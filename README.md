# Inspire Reverse Engineer (IRE)

**IRE** es una herramienta en Python para hacer ingeniería inversa de proyectos
exportados desde **Quadient Inspire Designer**. Carga un XML del *Workflow*,
separa la información del diseñador de la lógica de negocio, reconstruye un
**modelo interno independiente** y genera documentación, análisis y artefactos
de migración.

> El objetivo no es limpiar un XML, sino construir un motor de análisis capaz de
> interpretar la lógica del Workflow.

---

## Características

- **Parser tolerante** de XML de Inspire (probado con proyectos de >8 MB).
- **Modelo interno** (AST) tipado que es la única fuente de verdad: ningún
  generador vuelve a leer el XML.
- **Extracción de lógica funcional**:
  - Transformaciones (FCV: `ScriptFCV`, `ConcatStrFCV`, `StackFCV`, `BT2BTFCV`,
    `ConvNumFCV`, `IntIncrFCV`).
  - Filtros y condiciones.
  - Cruces (Join) y Lookups.
  - Scripts embebidos (con detección de variables leídas/escritas).
  - Parámetros, renombrados y agrupaciones.
  - **Uso en el diseño** (módulo Layout): por cada hoja/página detecta qué
    variables de datos se usan, marcando cada variable como usada o no en el
    diseño (incluye variables citadas en condiciones de las hojas).
- **Grafo de linaje por variable**: en el portal HTML, al seleccionar una
  variable se muestran los módulos donde se crea, se modifica y se usa (y si
  llega al diseño).
- **Diagrama de flujo con layout jerárquico** incrustado en el portal, con
  nodos clicables que abren el módulo. Usa **Graphviz** (`dot`) si está
  instalado (mejor calidad, `-f graphviz`); si no —p.ej. en equipos sin
  permisos de administrador— usa un **layout jerárquico propio en Python puro,
  sin dependencias** (`-f flow`). Sólo como último recurso cae a Mermaid.
- **Visor de grafos con zoom y paneo** y, para flujos grandes, un **modo
  enfoque** que muestra el vecindario de un módulo (aguas arriba/abajo a la
  profundidad elegida) en lugar del grafo completo ilegible.
- **Analizadores semánticos**: dependencias, estadísticas, reglas y variables
  (sin uso, huérfanas, duplicadas, críticas).
- **Generadores**: JSON, Markdown, Mermaid, GraphML, Excel/CSV, XML limpio,
  **HTML** (portal navegable con búsqueda y filtros) y **PDF**.
- **Sin dependencias obligatorias** (sólo librería estándar). `openpyxl` es
  opcional para `.xlsx` (si falta, el Excel se degrada a CSV) y `reportlab`
  para `.pdf` (si falta, ese formato se omite con un aviso).

---

## Instalación

```bash
# Sólo núcleo (sin dependencias)
pip install -e .

# Con soporte de Excel y herramientas de desarrollo
pip install -e ".[dev]"
```

Requiere Python 3.10+.

---

## Uso

### Línea de comandos

```bash
# Genera todos los artefactos en ./output
ire proyecto.xml

# Sólo estadísticas
ire proyecto.xml --stats-only

# Formatos concretos y directorio de salida
ire proyecto.xml -o salida -f json -f markdown -f mermaid

# Diseño en un archivo de Layout aparte (si no está en el XML principal)
ire proyecto.xml --layout Layout.xml
```

Formatos disponibles: `json`, `markdown`, `mermaid`, `graphml`, `graphviz`,
`flow`, `cleanxml`, `excel`, `html`, `pdf`, `all`.

El **portal HTML** es un único archivo autocontenido: ábrelo en el navegador
para buscar y filtrar módulos, variables y reglas, navegar entre módulos
conectados y ver el diagrama de flujo. No necesita servidor.

### Como librería

```python
from inspire import parse_workflow, analyze
from inspire.generators import JsonGenerator, MarkdownGenerator

workflow = parse_workflow("proyecto.xml")
result = analyze(workflow)            # estadísticas, dependencias, reglas, variables

print(workflow.statistics.as_dict())
JsonGenerator().write(workflow, "salida/proyecto.json")
MarkdownGenerator().write(workflow, "salida/proyecto.md")

# Variables sin uso detectadas por el análisis
print(result.variables.unused)
```

---

## Arquitectura

```
XML Inspire → XML Loader → XML Parser → AST (Modelo Interno)
                                          │
                              Semantic Analyzers
                                          │
                    ┌───────────┬─────────┴────────┬──────────┐
                  JSON      Markdown            Mermaid     GraphML
                  Excel    XML limpio
```

### Estructura del código

```
inspire/
    parser/       Carga y parseo del XML hacia el modelo
    model/        Modelo interno (Workflow, Module, Variable, ...)
    extractors/   Extracción de lógica por tipo de módulo (+ FCV, scripts)
    analyzers/    Dependencias, estadísticas, reglas, variables
    generators/   JSON, Markdown, Mermaid, GraphML, Excel, XML limpio
    cli/          Interfaz de línea de comandos
tests/            Suite de pruebas (cobertura > 90%)
docs/             Documentación de arquitectura
examples/         Ejemplos de uso
```

---

## Tipos de módulo soportados

| Categoría     | Módulos |
| ------------- | ------- |
| Entradas      | `DataInput`, `ParamInput`, `ScriptDataInput` |
| Transformación| `DataTransformer`, `DataRemapper`, `Renamer`, `DataConcatenator` |
| Control       | `DataFilter` |
| Integración   | `CustCode` (Join/Lookup), `DataMerger`, `DataSorter`, `DataGroupBy`, `DataUnGroup`, `DataAdd`, `DataCacher`, `DataRepeater` |
| Scripts       | `ScriptedSheeter` |
| Salidas       | `DataOutput`, `AdvDataOutput` |

Añadir un nuevo tipo es registrar una función con
`@ExtractorRegistry.register("MiTag")` en `inspire/extractors/registry.py`.

---

## Desarrollo

```bash
pytest                              # ejecutar pruebas
pytest --cov=inspire --cov-report=term-missing   # con cobertura
```

---

## Hoja de ruta

- Comparador de versiones de Workflow (reglas/variables nuevas, eliminadas, cambios).
- Exportadores parciales a Python / Java.
- API REST para procesar XML por HTTP.

> El **buscador** ya está disponible dentro del portal HTML. El **visualizador
> web** (HTML navegable) y la **exportación a PDF** ya están implementados.

---

## Licencia

MIT.
