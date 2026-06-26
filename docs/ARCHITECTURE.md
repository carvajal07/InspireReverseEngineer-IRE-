# Arquitectura de IRE

Este documento describe cómo fluye la información dentro de Inspire Reverse
Engineer, desde el XML de Quadient Inspire hasta los artefactos generados.

## Pipeline

```
XML Inspire
    │  (inspire.parser.loader.XmlLoader)
    ▼
Elemento raíz <WorkFlow>
    │  (inspire.parser.parser.WorkflowParser)
    ▼
Modelo Interno (inspire.model.Workflow)
    │  (inspire.analyzers.analyze)
    ▼
Workflow anotado (estadísticas, dependencias, reglas, variables)
    │  (inspire.generators.*)
    ▼
JSON · Markdown · Mermaid · GraphML · Excel/CSV · XML limpio
```

## Principio fundamental

El **modelo interno** (`inspire/model`) es la única fuente de verdad. Una vez
parseado el XML, ningún analizador ni generador vuelve a leerlo. Esto:

- desacopla el formato de Inspire de la lógica de la herramienta,
- permite versionar/serializar el modelo,
- facilita comparar versiones y migrar a otras tecnologías.

## Capas

### 1. Parser (`inspire/parser`)

- `loader.py`: lee el archivo, valida que la raíz sea `WorkFlow` y,
  opcionalmente, elimina nodos del diseñador.
- `parser.py`: recorre los hijos del `WorkFlow`, ignora los tags del diseñador,
  delega cada módulo al extractor adecuado y reúne conexiones y variables.

### 2. Modelo (`inspire/model`)

Dataclasses tipadas con `slots`:

- `Workflow`: módulos, conexiones, variables, dependencias y estadísticas.
- `Module`: id, nombre, tipo, categoría y la lógica funcional extraída.
- `Transformation`, `Filter`, `JoinKey`, `Parameter`, `Script`, `Variable`, ...

### 3. Extractores (`inspire/extractors`)

Patrón **registry**: cada tipo de módulo registra una función que añade su
lógica específica al `Module`. `fcv.py` interpreta los *Field Computed Values*
(la unidad de lógica de las transformaciones de Inspire) y `scripts.py` analiza
los scripts embebidos.

### 4. Analizadores (`inspire/analyzers`)

- `statistics.py`: métricas agregadas.
- `dependency.py`: árbol de dependencias de variables (por uso o por flujo).
- `rules.py`: clasifica cada pieza de lógica como regla de negocio.
- `variables.py`: detecta variables sin uso, huérfanas, duplicadas y críticas.

### 5. Generadores (`inspire/generators`)

Cada generador consume el `Workflow` y produce un artefacto. `serialize.py`
ofrece la conversión común a `dict` que reutilizan JSON y otros.

## Extensibilidad

- **Nuevo módulo**: registrar un extractor con
  `@ExtractorRegistry.register("Tag")`.
- **Nuevo FCV**: añadir el caso en `inspire/extractors/fcv.py`.
- **Nuevo generador**: crear una clase con métodos `render(workflow)` y
  `write(workflow, path)` y registrarla en la CLI.
