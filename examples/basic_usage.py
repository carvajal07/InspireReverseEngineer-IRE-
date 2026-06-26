"""Ejemplo básico de uso de IRE como librería.

Ejecutar:
    python examples/basic_usage.py <ruta_al_xml>
"""

from __future__ import annotations

import sys
from pathlib import Path

from inspire import analyze, parse_workflow
from inspire.generators import (
    GraphMLGenerator,
    JsonGenerator,
    MarkdownGenerator,
    MermaidGenerator,
)


def main(xml_path: str) -> None:
    # 1. Parsear el XML al modelo interno.
    workflow = parse_workflow(xml_path)

    # 2. Ejecutar el análisis semántico completo.
    result = analyze(workflow)

    # 3. Mostrar un resumen.
    stats = workflow.statistics
    print(f"Workflow '{workflow.name}' (Inspire {workflow.version})")
    print(f"  Módulos   : {stats.modules}")
    print(f"  Variables : {stats.variables}")
    print(f"  Reglas    : {stats.rules}")
    print(f"  Joins     : {stats.joins}")
    print(f"  Scripts   : {stats.scripts}")
    print(f"  Variables sin uso: {len(result.variables.unused)}")

    # 4. Generar algunos artefactos.
    out = Path("output")
    JsonGenerator().write(workflow, out / f"{workflow.name}.json")
    MarkdownGenerator().write(workflow, out / f"{workflow.name}.md")
    MermaidGenerator().write(workflow, out / f"{workflow.name}.mmd")
    GraphMLGenerator().write(workflow, out / f"{workflow.name}.graphml")
    print(f"\nArtefactos generados en {out.resolve()}/")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("uso: python examples/basic_usage.py <ruta_al_xml>")
        raise SystemExit(1)
    main(sys.argv[1])
