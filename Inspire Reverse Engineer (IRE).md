# Inspire Reverse Engineer (IRE)

## Descripción

**Inspire Reverse Engineer (IRE)** es una herramienta desarrollada en Python cuyo objetivo es analizar proyectos exportados desde **Quadient Inspire Designer**, extraer toda la lógica de negocio y convertirla en un modelo independiente del diseñador.

La herramienta permitirá comprender, documentar, auditar y eventualmente migrar proyectos de Inspire hacia otras tecnologías como Python, Java o .NET.

El objetivo no es solamente limpiar un XML, sino construir un motor de análisis capaz de interpretar la lógica del Workflow.

---

# Objetivos

## Objetivo General

Extraer automáticamente toda la lógica de negocio contenida en un Workflow de Quadient Inspire.

## Objetivos específicos

* Analizar cualquier XML exportado desde Inspire.
* Reconstruir el Workflow completo.
* Detectar dependencias entre módulos.
* Identificar todas las variables utilizadas.
* Detectar reglas de negocio.
* Detectar filtros.
* Detectar cruces (Join).
* Detectar Lookups.
* Detectar Scripts.
* Detectar transformaciones.
* Detectar expresiones.
* Generar documentación técnica automáticamente.
* Servir como base para futuras migraciones del Workflow.

---

# Filosofía

El XML de Inspire contiene una enorme cantidad de información del diseñador que no representa reglas de negocio.

IRE debe separar completamente:

## Información técnica del diseñador

Ejemplos:

* Property
* SecurityDescriptorManager
* SecurityDescriptorWorkFlow
* ModulePos
* Label
* SecurityDescriptor
* FieldReordering
* GUID
* Posiciones gráficas
* Colores
* Configuración de interfaz
* Configuración AFP
* Configuración PDF
* Configuración PCL
* Datos del editor

Esta información podrá eliminarse.

---

## Información funcional

Esta información será preservada.

Ejemplos:

* Variables
* Transformaciones
* Expresiones
       Concat()
       Replace()
       Trim()
       Upper()
       Substring()
       IF()
       CASE()
* Filtros
* Join
       Join
       Left Key
       Right Key
       MatchType
* Lookup
* Scripts
* Entradas
* Salidas
* Dependencias

---

# Arquitectura

```
XML Inspire

        │

        ▼

 XML Loader

        │

        ▼

 XML Parser

        │

        ▼

 AST (Modelo Interno)

        │

        ▼

 Semantic Analyzer

        │

        ▼

 Generadores

        │

 ├──────────────┐
 ▼              ▼

JSON         Markdown

 ▼              ▼

Excel       Mermaid

 ▼              ▼

GraphML     XML limpio
```

---

# Modelo Interno

Toda la información será convertida en un modelo interno.

```
Workflow

├── Inputs

├── Outputs

├── Modules

├── Variables

├── Rules

├── Connections

├── Dependencies

└── Statistics
```

Este modelo será la única fuente de información.

Ningún generador volverá a leer el XML.

---

# Tipos de módulos soportados

## Entradas

* ParamInput
* DataInput
* XML Input
* CSV Input
* Database Input

---

## Transformación

* DataTransformer
* Expression
* Formula
* Variable Assignment

---

## Control

* Filter
* Condition
* Switch
* Loop

---

## Integración

* Join
* DataLookup
* Sort

---

## Scripts

* VB
* JavaScript
* C#
* Python (si existe)

---

## Salidas

* DataOutput
* XML Output
* Compose
* Export

---

# Información que será extraída

## Variables

* Nombre
* Tipo
* Valor inicial
* Módulo donde se crea
* Módulos donde se modifica
* Módulos donde se utiliza
* Dependencias

---

## Transformaciones

* Variable origen
* Variable destino
* Expresión
* Tipo de transformación

---

## Filtros

* Nombre
* Condición
* Variables utilizadas
* Destino verdadero
* Destino falso

---

## Join

* Fuente izquierda
* Fuente derecha
* Llaves
* Tipo de Join
* Campos recuperados

---

## Lookup

* Archivo
* Llave
* Campos obtenidos

---

## Scripts

* Lenguaje
* Código
* Variables utilizadas
* Variables modificadas

---

## Expresiones

* Fórmula
* Variables utilizadas
* Resultado

---

## Flujo

* Nodo origen
* Nodo destino
* Dependencias

---

# Analizadores

## Dependency Analyzer

Detectará:

* Variables creadas
* Variables modificadas
* Variables consumidas

Construirá un árbol de dependencias.

---

## Statistics Analyzer

Calculará:

* Número de módulos
* Número de variables
* Número de reglas
* Número de filtros
* Número de joins
* Número de scripts
* Número de lookups

---

## Rule Analyzer

Clasificará automáticamente las reglas de negocio.

---

## Variable Analyzer

Determinará:

* Variables sin uso
* Variables duplicadas
* Variables huérfanas
* Variables críticas

---

# Generadores

## XML limpio

Eliminará todo el contenido del diseñador.

Conservará únicamente lógica funcional.

---

## JSON

Modelo estructurado para otros sistemas.

Ejemplo:

* Variables
* Reglas
* Filtros
* Join
* Lookup
* Scripts
* Dependencias

---

## Markdown

Documentación técnica completa.

Contendrá:

* Descripción del Workflow
* Variables
* Reglas
* Transformaciones
* Dependencias
* Estadísticas

---

## Excel

Se generarán varios libros:

### Variables

* Variable
* Tipo
* Módulo
* Uso

### Reglas

* Tipo
* Expresión
* Variables

### Join

* Llaves
* Origen
* Destino

### Dependencias

* Variable
* Módulo origen
* Módulo destino

---

## Mermaid

Generará automáticamente diagramas de flujo.

Ejemplo:

```
flowchart LR

Input --> Transform

Transform --> Filter

Filter --> Join

Join --> Output
```

---

## GraphML

Permitirá abrir el Workflow en:

* Gephi
* yEd
* Cytoscape

---

## HTML

Portal navegable.

Con:

* búsqueda
* filtros
* navegación entre módulos

---

## PDF

Documentación completa del Workflow.

---

# Funcionalidades futuras

## Buscador

Buscar:

* Variable
* Regla
* Script
* Expresión
* Join

---

## Comparador

Comparar dos versiones del mismo Workflow.

Mostrar:

* reglas nuevas
* reglas eliminadas
* variables nuevas
* cambios

---

## Visualizador Web

Interfaz gráfica.

Permitirá navegar el Workflow.

---

## Exportador Python

Convertir parcialmente el Workflow a Python.

---

## Exportador Java

Convertir parcialmente el Workflow a Java.

---

## API REST

Procesar XML mediante HTTP.

---

# Estructura del proyecto

```
InspireReverseEngineer/

    inspire/

        parser/

        model/

        extractors/

        analyzers/

        generators/

        cli/

        tests/

    docs/

    examples/

    output/

    pyproject.toml

    requirements.txt

    README.md
```

---

# Principios del proyecto

* Arquitectura modular.
* Extensible mediante plugins.
* Sin dependencias del diseñador.
* Alto rendimiento para XML grandes.
* Bajo consumo de memoria.
* Código completamente tipado.
* Cobertura de pruebas superior al 90%.
* Compatible con proyectos grandes de Inspire.

---

# Objetivo final

Convertir Inspire Reverse Engineer en una herramienta capaz de interpretar un Workflow de Quadient Inspire con el mismo nivel de comprensión que tiene el propio diseñador, pero ofreciendo documentación, análisis, trazabilidad y capacidades de migración que Inspire no proporciona de forma nativa.
