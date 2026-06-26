#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extraer_variables_layout.py
============================
Analiza un XML de Quadient Inspire Designer (módulo Layout) y, por cada
página/hoja, lista las variables de datos que se usan en su generación.

Modelo de datos recorrido (cadena de referencias, NO de anidamiento físico):

    Page  --(ParentId)-->  FlowArea  --(FlowId)-->  Flow
    Flow.FlowContent  -->  <O Id="n"/>            (objetos en línea)
    <O Id="n">  -->  Variable      (se reconstruye la ruta completa)
                     Table         (RowSetId -> RowSet -> SubRowId -> ... -> Cell)
                     Cell          (FlowId -> Flow)
                     Flow          (FlowContent -> más <O Id>)
                     FlowObject    (Barcode / Image con VariableId)
                     Image/Barcode (VariableId)
    Flow (InlCond)  -->  <Condition>flowDestino</Condition> / <Default>flowId</Default>

La ruta de cada variable se arma siguiendo la cadena <ParentId> en la sección
de definición, omitiendo los nodos contenedor llamado "Value" (nodos de
repetición de Inspire). Resultado, p.ej.:  Sodim_Ord.Records.NumCrediRotativo

Notas sobre el formato del archivo:
- El export puede contener VARIOS módulos <Layout> concatenados a nivel raíz
  (no es un único documento XML válido).
- Algún módulo puede venir con el '<' de apertura faltante ("Layout>" en vez
  de "<Layout>"). Ambos defectos se reparan antes de parsear.

Uso:
    python extraer_variables_layout.py Layout.xml
    python extraer_variables_layout.py Layout.xml -o salida.csv
    python extraer_variables_layout.py Layout.xml --modulo Extracto
    python extraer_variables_layout.py Layout.xml --incluir-condiciones

Requisitos:  lxml   (pip install lxml)
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import OrderedDict
from dataclasses import dataclass, field

from lxml import etree


# --------------------------------------------------------------------------- #
# Configuración del recorrido
# --------------------------------------------------------------------------- #

# Tags cuyo TEXTO es el Id de otro contenedor que hay que seguir (flujos,
# filas de tabla, celdas, áreas encadenadas).
TAGS_SEGUIR_TEXTO = {
    "FlowId", "SubRowId", "RowSetId", "NextFlowAreaId",
    "Condition", "Default", "EnableById",
}

# Tags cuyo TEXTO es el Id de una variable (objetos visuales que muestran datos:
# códigos de barras, imágenes variables, etc.).
TAGS_VARIABLE_TEXTO = {"VariableId"}

# Raíces de definición conocidas, para clasificar el origen de cada variable.
ORIGEN_POR_RAIZ = {
    "Def.Data": "DATA",
    "Def.SystemVariables": "SYS",
}


# --------------------------------------------------------------------------- #
# Estructuras de datos
# --------------------------------------------------------------------------- #

@dataclass
class UsoVariable:
    modulo: str
    pagina: str
    ruta: str
    origen: str
    id_variable: str


@dataclass
class Modulo:
    """Índices de un módulo <Layout> ya parseado."""
    nombre: str
    id_modulo: str
    # id -> (tag, name, parent_id)  de la sección de definición
    defs: dict = field(default_factory=dict)
    # id -> Element  de la sección de contenido (último gana)
    content: dict = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Carga y parseo tolerante a fallos
# --------------------------------------------------------------------------- #

def cargar_modulos(ruta_xml: str) -> list[Modulo]:
    """Lee el XML, repara defectos conocidos y devuelve los módulos Layout."""
    with open(ruta_xml, "r", encoding="utf-8") as fh:
        texto = fh.read()

    # Reparar módulos cuyo '<' de apertura se perdió: "  Layout>" -> "  <Layout>"
    texto = re.sub(r"(?m)^(\s*)Layout>", r"\1<Layout>", texto)

    # Envolver en un root sintético para tolerar múltiples elementos de nivel raíz.
    envuelto = f"<__root__>{texto}</__root__>".encode("utf-8")
    parser = etree.XMLParser(recover=True, huge_tree=True)
    root = etree.fromstring(envuelto, parser)

    modulos: list[Modulo] = []
    for nodo_layout in root.iter("Layout"):
        # Sólo los <Layout> de nivel módulo (tienen Id + Name + un <Layout> interno).
        interno = nodo_layout.find("Layout")
        if interno is None:
            continue
        mod = Modulo(
            nombre=nodo_layout.findtext("Name") or "(sin nombre)",
            id_modulo=nodo_layout.findtext("Id") or "?",
        )
        _indexar(interno, mod)
        modulos.append(mod)
    return modulos


def _indexar(interno: etree._Element, mod: Modulo) -> None:
    """Separa nodos de definición (con Name+ParentId) de nodos de contenido."""
    for el in interno:
        eid = el.findtext("Id")
        if eid is None:
            continue
        es_definicion = (
            el.find("Name") is not None
            and el.find("ParentId") is not None
            and el.find("IndexInParent") is not None
        )
        if es_definicion:
            mod.defs.setdefault(
                eid, (el.tag, el.findtext("Name"), el.findtext("ParentId"))
            )
        else:
            mod.content[eid] = el  # el contenido aparece después; último gana


# --------------------------------------------------------------------------- #
# Reconstrucción de la ruta de una variable
# --------------------------------------------------------------------------- #

def ruta_variable(mod: Modulo, vid: str) -> tuple[str, str]:
    """Devuelve (ruta_punteada, origen) para la variable con Id `vid`."""
    partes: list[str] = []
    visto: set[str] = set()
    origen = "GLOBAL"
    actual = vid
    while actual in mod.defs and actual not in visto:
        visto.add(actual)
        _tag, nombre, parent = mod.defs[actual]
        partes.append(nombre)
        if not parent.isdigit():
            origen = ORIGEN_POR_RAIZ.get(parent, "GLOBAL")
            break
        actual = parent
    # Omitir los nodos contenedor "Value" (repeticiones de Inspire) y armar ruta.
    limpio = [p for p in reversed(partes) if p != "Value"]
    return ".".join(limpio), origen


# --------------------------------------------------------------------------- #
# Recorrido recursivo de una página
# --------------------------------------------------------------------------- #

def recolectar_variables(mod: Modulo, id_inicio: str,
                         ids_variable: set[str]) -> None:
    """DFS iterativo sobre referencias, acumulando Ids de variable encontrados."""
    visitados: set[str] = set()
    pila: list[str] = [id_inicio]
    while pila:
        cid = pila.pop()
        if cid in visitados:
            continue
        visitados.add(cid)

        # ¿Es una variable de datos? -> hoja, registrar y no profundizar.
        info = mod.defs.get(cid)
        if info and info[0] == "Variable":
            ids_variable.add(cid)
            continue

        nodo = mod.content.get(cid)
        if nodo is None:
            continue

        for sub in nodo.iter():
            if sub.tag == "O":
                ref = sub.get("Id")
                if ref:
                    pila.append(ref)
            elif sub.tag in TAGS_SEGUIR_TEXTO:
                txt = (sub.text or "").strip()
                if txt.isdigit():
                    pila.append(txt)
            elif sub.tag in TAGS_VARIABLE_TEXTO:
                txt = (sub.text or "").strip()
                if txt.isdigit():
                    pila.append(txt)


def flowareas_de_pagina(mod: Modulo, page_id: str) -> list[str]:
    """FlowAreas cuyo ParentId (en la definición) es la página dada."""
    return [
        i for i, (tag, _n, parent) in mod.defs.items()
        if tag == "FlowArea" and parent == page_id
    ]


def paginas_del_modulo(mod: Modulo) -> "OrderedDict[str, str]":
    """OrderedDict id_pagina -> nombre_pagina, en orden de definición."""
    paginas: "OrderedDict[str, str]" = OrderedDict()
    for i, (tag, nombre, _p) in mod.defs.items():
        if tag == "Page":
            paginas[i] = nombre
    return paginas


# --------------------------------------------------------------------------- #
# Variables mencionadas dentro de expresiones de condición (opcional)
# --------------------------------------------------------------------------- #

_RE_RUTA_COND = re.compile(r"\bDATA\.((?:[A-Za-z_]\w*)(?:\.[A-Za-z_]\w*)*)")


def rutas_en_condiciones(mod: Modulo, id_inicio: str) -> set[str]:
    """Extrae rutas tipo DATA.X.Y de las expresiones de condición alcanzables."""
    rutas: set[str] = set()
    visitados: set[str] = set()
    pila: list[str] = [id_inicio]
    while pila:
        cid = pila.pop()
        if cid in visitados:
            continue
        visitados.add(cid)
        nodo = mod.content.get(cid)
        if nodo is None:
            continue
        for sub in nodo.iter():
            if sub.tag == "O" and sub.get("Id"):
                pila.append(sub.get("Id"))
            elif sub.tag in TAGS_SEGUIR_TEXTO:
                txt = (sub.text or "").strip()
                if txt.isdigit():
                    pila.append(txt)
                # El atributo Value o el texto pueden traer la expresión.
                expr = sub.get("Value") or (sub.text or "")
                for m in _RE_RUTA_COND.finditer(expr):
                    rutas.add(_limpiar_ruta_expr(m.group(1)))
    return rutas


def _limpiar_ruta_expr(ruta: str) -> str:
    """DATA.Sodim_Ord.Current.Records.NombreCliente -> Sodim_Ord.Records.NombreCliente"""
    descartar = {"Current", "Index", "Count", "Value"}
    segmentos = [s for s in ruta.split(".") if s not in descartar]
    return ".".join(segmentos)


# --------------------------------------------------------------------------- #
# Orquestación
# --------------------------------------------------------------------------- #

def analizar(modulos: list[Modulo], filtro_modulo: str | None,
             incluir_condiciones: bool) -> list[UsoVariable]:
    resultados: list[UsoVariable] = []
    for mod in modulos:
        if filtro_modulo and mod.nombre != filtro_modulo:
            continue
        for page_id, page_name in paginas_del_modulo(mod).items():
            ids_var: set[str] = set()
            for fa in flowareas_de_pagina(mod, page_id):
                recolectar_variables(mod, fa, ids_var)

            usos: dict[str, UsoVariable] = {}
            for vid in ids_var:
                ruta, origen = ruta_variable(mod, vid)
                if ruta:
                    usos[ruta] = UsoVariable(
                        mod.nombre, page_name, ruta, origen, vid
                    )

            if incluir_condiciones:
                for fa in flowareas_de_pagina(mod, page_id):
                    for ruta in rutas_en_condiciones(mod, fa):
                        usos.setdefault(
                            ruta,
                            UsoVariable(mod.nombre, page_name, ruta, "COND", ""),
                        )

            for uso in sorted(usos.values(), key=lambda u: u.ruta.lower()):
                resultados.append(uso)
    return resultados


def imprimir(resultados: list[UsoVariable]) -> None:
    pagina_actual = None
    for uso in resultados:
        clave = (uso.modulo, uso.pagina)
        if clave != pagina_actual:
            pagina_actual = clave
            print(f"\n=== [{uso.modulo}]  {uso.pagina} ===")
        marca = "" if uso.origen == "DATA" else f"  ({uso.origen})"
        print(f"   {uso.ruta}{marca}")


def exportar_csv(resultados: list[UsoVariable], ruta_csv: str) -> None:
    with open(ruta_csv, "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh, delimiter=";")
        writer.writerow(["Modulo", "Pagina", "RutaVariable", "Origen", "IdVariable"])
        for u in resultados:
            writer.writerow([u.modulo, u.pagina, u.ruta, u.origen, u.id_variable])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Extrae, por página/hoja, las variables usadas en un XML "
                    "de Layout de Quadient Inspire Designer."
    )
    ap.add_argument("xml", help="Ruta al archivo Layout XML")
    ap.add_argument("-o", "--output", help="Ruta del CSV de salida (delimitador ';')")
    ap.add_argument("--modulo", help="Procesar sólo el módulo Layout con este Name")
    ap.add_argument("--incluir-condiciones", action="store_true",
                    help="Añadir también variables citadas en expresiones de condición")
    ap.add_argument("--listar-modulos", action="store_true",
                    help="Sólo listar los módulos Layout encontrados y salir")
    args = ap.parse_args(argv)

    modulos = cargar_modulos(args.xml)
    if not modulos:
        print("No se encontró ningún módulo <Layout> en el archivo.", file=sys.stderr)
        return 1

    if args.listar_modulos:
        for m in modulos:
            n_pag = len(paginas_del_modulo(m))
            print(f"{m.id_modulo:10}  {m.nombre:30}  páginas={n_pag}")
        return 0

    resultados = analizar(modulos, args.modulo, args.incluir_condiciones)

    if args.output:
        exportar_csv(resultados, args.output)
        print(f"CSV generado: {args.output}  ({len(resultados)} filas)")
    else:
        imprimir(resultados)
        print(f"\nTotal de usos de variable: {len(resultados)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
