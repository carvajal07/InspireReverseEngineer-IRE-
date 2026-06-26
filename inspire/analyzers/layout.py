"""Layout Analyzer: variables de datos usadas en el diseño (módulo Layout).

Porta la lógica de ``extraer_variables_layout.py`` al modelo de IRE. Por cada
página/hoja de un módulo ``<Layout>`` determina qué variables de datos se usan
en su generación, siguiendo la cadena de referencias (no el anidamiento físico):

    Page --(ParentId)--> FlowArea --(FlowId)--> Flow
    Flow.FlowContent --> <O Id="n"/>            (objetos en línea)
    <O Id="n"> --> Variable | Table | Cell | Flow | FlowObject | Image/Barcode
    Flow (InlCond) --> <Condition>destino</Condition> / <Default>flowId</Default>

La ruta de cada variable se reconstruye subiendo por ``<ParentId>``, omitiendo
los nodos contenedor ``Value`` (repeticiones de Inspire), hasta una raíz no
numérica (``Def.Data`` -> DATA, ``Def.SystemVariables`` -> SYS).

El análisis usa la librería estándar (ElementTree). Para archivos de Layout
sueltos y potencialmente malformados (varios ``<Layout>`` concatenados, o con el
``<`` de apertura perdido) usa ``lxml`` con recuperación si está disponible, y
si no, repara los defectos conocidos y parsea con ElementTree.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

# Tags cuyo TEXTO es el Id de otro contenedor que hay que seguir.
TAGS_FOLLOW_TEXT = {
    "FlowId",
    "SubRowId",
    "RowSetId",
    "NextFlowAreaId",
    "Condition",
    "Default",
    "EnableById",
}

# Tags cuyo TEXTO es el Id de una variable (códigos de barras, imágenes, etc.).
TAGS_VARIABLE_TEXT = {"VariableId"}

# Raíces de definición conocidas, para clasificar el origen de cada variable.
ORIGIN_BY_ROOT = {
    "Def.Data": "DATA",
    "Def.SystemVariables": "SYS",
}

_RE_COND_PATH = re.compile(r"\bDATA\.((?:[A-Za-z_]\w*)(?:\.[A-Za-z_]\w*)*)")
_COND_DROP = {"Current", "Index", "Count", "Value"}


@dataclass(slots=True)
class LayoutUsage:
    """Uso de una variable de datos en una página de diseño."""

    module: str
    page: str
    path: str
    origin: str
    variable_id: str = ""

    @property
    def leaf(self) -> str:
        return self.path.split(".")[-1] if self.path else ""


@dataclass(slots=True)
class _LayoutModule:
    """Índices de un módulo ``<Layout>`` ya parseado."""

    name: str
    module_id: str
    # id -> (tag, name, parent_id) de la sección de definición.
    defs: dict[str, tuple[str, str, str]] = field(default_factory=dict)
    # id -> Element de la sección de contenido (último gana).
    content: dict[str, ET.Element] = field(default_factory=dict)


@dataclass(slots=True)
class LayoutReport:
    """Resultado del análisis del diseño."""

    usages: list[LayoutUsage] = field(default_factory=list)
    pages: list[tuple[str, str]] = field(default_factory=list)
    modules: list[str] = field(default_factory=list)

    @property
    def found_layout(self) -> bool:
        return bool(self.modules)

    def leaves_used(self) -> set[str]:
        return {u.leaf for u in self.usages if u.leaf}

    def paths_used(self) -> set[str]:
        return {u.path for u in self.usages if u.path}

    def pages_for_leaf(self, leaf: str) -> set[str]:
        return {
            f"{u.module} / {u.page}" for u in self.usages if u.leaf == leaf
        }

    def paths_for_leaf(self, leaf: str) -> set[str]:
        return {u.path for u in self.usages if u.leaf == leaf}


class LayoutAnalyzer:
    """Extrae, por página, las variables de datos usadas en el diseño."""

    def __init__(self, *, include_conditions: bool = True) -> None:
        self.include_conditions = include_conditions

    # ------------------------------------------------------------------
    # Entradas
    # ------------------------------------------------------------------

    def analyze_root(self, root: ET.Element | None) -> LayoutReport:
        """Analiza los ``<Layout>`` contenidos en un árbol ya parseado."""

        report = LayoutReport()
        if root is None:
            return report
        modules = self._modules_from_root(root)
        self._run(modules, report)
        return report

    def analyze_file(self, path: str | Path) -> LayoutReport:
        """Analiza un archivo de Layout (tolerante a export concatenado)."""

        report = LayoutReport()
        modules = self._modules_from_file(Path(path))
        self._run(modules, report)
        return report

    # ------------------------------------------------------------------
    # Construcción de módulos
    # ------------------------------------------------------------------

    def _modules_from_root(self, root: ET.Element) -> list[_LayoutModule]:
        modules: list[_LayoutModule] = []
        for node in root.iter("Layout"):
            inner = node.find("Layout")
            if inner is None:
                continue
            mod = _LayoutModule(
                name=node.findtext("Name") or "(sin nombre)",
                module_id=node.findtext("Id") or "?",
            )
            self._index(inner, mod)
            modules.append(mod)
        return modules

    def _modules_from_file(self, path: Path) -> list[_LayoutModule]:
        text = path.read_text(encoding="utf-8", errors="replace")
        # Reparar módulos cuyo '<' de apertura se perdió: "  Layout>" -> "<Layout>".
        text = re.sub(r"(?m)^(\s*)Layout>", r"\1<Layout>", text)
        wrapped = f"<__root__>{text}</__root__>"
        root = self._tolerant_parse(wrapped)
        return self._modules_from_root(root) if root is not None else []

    @staticmethod
    def _tolerant_parse(wrapped: str) -> ET.Element | None:
        try:  # lxml recupera mejor exportaciones imperfectas.
            from lxml import etree  # type: ignore

            parser = etree.XMLParser(recover=True, huge_tree=True)
            lroot = etree.fromstring(wrapped.encode("utf-8"), parser)
            # Convertir a ElementTree para una interfaz homogénea.
            return ET.fromstring(etree.tostring(lroot))
        except ImportError:
            pass
        except Exception:
            return None
        try:
            return ET.fromstring(wrapped)
        except ET.ParseError:
            return None

    @staticmethod
    def _index(inner: ET.Element, mod: _LayoutModule) -> None:
        """Separa nodos de definición (Name+ParentId+IndexInParent) de contenido."""

        for el in inner:
            eid = el.findtext("Id")
            if eid is None:
                continue
            is_definition = (
                el.find("Name") is not None
                and el.find("ParentId") is not None
                and el.find("IndexInParent") is not None
            )
            if is_definition:
                mod.defs.setdefault(
                    eid,
                    (el.tag, el.findtext("Name") or "", el.findtext("ParentId") or ""),
                )
            else:
                mod.content[eid] = el  # el contenido aparece después; último gana

    # ------------------------------------------------------------------
    # Recorrido
    # ------------------------------------------------------------------

    def _run(self, modules: list[_LayoutModule], report: LayoutReport) -> None:
        for mod in modules:
            report.modules.append(mod.name)
            for page_id, page_name in self._pages(mod):
                report.pages.append((mod.name, page_name))
                var_ids: set[str] = set()
                flow_areas = self._flow_areas(mod, page_id)
                for fa in flow_areas:
                    self._collect(mod, fa, var_ids)

                seen_paths: set[str] = set()
                for vid in var_ids:
                    path, origin = self._var_path(mod, vid)
                    if path and path not in seen_paths:
                        seen_paths.add(path)
                        report.usages.append(
                            LayoutUsage(mod.name, page_name, path, origin, vid)
                        )

                if self.include_conditions:
                    for fa in flow_areas:
                        for path in self._condition_paths(mod, fa):
                            if path not in seen_paths:
                                seen_paths.add(path)
                                report.usages.append(
                                    LayoutUsage(mod.name, page_name, path, "COND")
                                )

    @staticmethod
    def _pages(mod: _LayoutModule) -> list[tuple[str, str]]:
        return [
            (i, name)
            for i, (tag, name, _p) in mod.defs.items()
            if tag == "Page"
        ]

    @staticmethod
    def _flow_areas(mod: _LayoutModule, page_id: str) -> list[str]:
        return [
            i
            for i, (tag, _n, parent) in mod.defs.items()
            if tag == "FlowArea" and parent == page_id
        ]

    def _collect(
        self, mod: _LayoutModule, start_id: str, var_ids: set[str]
    ) -> None:
        """DFS iterativo sobre referencias, acumulando Ids de variable."""

        visited: set[str] = set()
        stack: list[str] = [start_id]
        while stack:
            cid = stack.pop()
            if cid in visited:
                continue
            visited.add(cid)

            info = mod.defs.get(cid)
            if info and info[0] == "Variable":
                var_ids.add(cid)
                continue

            node = mod.content.get(cid)
            if node is None:
                continue

            for sub in node.iter():
                if sub.tag == "O":
                    ref = sub.get("Id")
                    if ref:
                        stack.append(ref)
                elif sub.tag in TAGS_FOLLOW_TEXT or sub.tag in TAGS_VARIABLE_TEXT:
                    txt = (sub.text or "").strip()
                    if txt.isdigit():
                        stack.append(txt)

    def _var_path(self, mod: _LayoutModule, vid: str) -> tuple[str, str]:
        """Devuelve (ruta_punteada, origen) para la variable con Id ``vid``."""

        parts: list[str] = []
        seen: set[str] = set()
        origin = "GLOBAL"
        current = vid
        while current in mod.defs and current not in seen:
            seen.add(current)
            _tag, name, parent = mod.defs[current]
            parts.append(name)
            if not parent.isdigit():
                origin = ORIGIN_BY_ROOT.get(parent, "GLOBAL")
                break
            current = parent
        clean = [p for p in reversed(parts) if p != "Value"]
        return ".".join(clean), origin

    def _condition_paths(self, mod: _LayoutModule, start_id: str) -> set[str]:
        """Extrae rutas tipo ``DATA.X.Y`` de las expresiones de condición."""

        paths: set[str] = set()
        visited: set[str] = set()
        stack: list[str] = [start_id]
        while stack:
            cid = stack.pop()
            if cid in visited:
                continue
            visited.add(cid)
            node = mod.content.get(cid)
            if node is None:
                continue
            for sub in node.iter():
                if sub.tag == "O" and sub.get("Id"):
                    stack.append(sub.get("Id"))
                elif sub.tag in TAGS_FOLLOW_TEXT:
                    txt = (sub.text or "").strip()
                    if txt.isdigit():
                        stack.append(txt)
                    expr = sub.get("Value") or (sub.text or "")
                    for match in _RE_COND_PATH.finditer(expr):
                        paths.add(self._clean_expr_path(match.group(1)))
        return paths

    @staticmethod
    def _clean_expr_path(path: str) -> str:
        segments = [s for s in path.split(".") if s not in _COND_DROP]
        return ".".join(segments)
