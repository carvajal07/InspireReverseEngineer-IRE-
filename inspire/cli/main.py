"""Punto de entrada CLI de Inspire Reverse Engineer."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from inspire import __version__
from inspire.analyzers import analyze
from inspire.generators import (
    CleanXmlGenerator,
    ExcelGenerator,
    GraphMLGenerator,
    GraphvizGenerator,
    HtmlGenerator,
    JsonGenerator,
    MarkdownGenerator,
    MermaidGenerator,
    PdfGenerator,
)
from inspire.parser import WorkflowParser

#: Mapa de formato -> (extensión, factoría de generador).
_GENERATORS = {
    "json": (".json", JsonGenerator),
    "markdown": (".md", MarkdownGenerator),
    "mermaid": (".mmd", MermaidGenerator),
    "graphml": (".graphml", GraphMLGenerator),
    "graphviz": (".svg", GraphvizGenerator),
    "cleanxml": (".clean.xml", CleanXmlGenerator),
    "excel": (".xlsx", ExcelGenerator),
    "html": (".html", HtmlGenerator),
    "pdf": (".pdf", PdfGenerator),
}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ire",
        description="Inspire Reverse Engineer: analiza workflows de Quadient Inspire.",
    )
    parser.add_argument("xml", help="Ruta al XML exportado de Inspire Designer.")
    parser.add_argument(
        "-o",
        "--output",
        default="output",
        help="Directorio de salida (por defecto: ./output).",
    )
    parser.add_argument(
        "-f",
        "--format",
        action="append",
        choices=[*_GENERATORS.keys(), "all"],
        help="Formato(s) a generar. Repetible. Por defecto: all.",
    )
    parser.add_argument(
        "--stats-only",
        action="store_true",
        help="Sólo imprime las estadísticas, sin generar archivos.",
    )
    parser.add_argument(
        "--layout",
        metavar="LAYOUT_XML",
        help="Archivo de Layout aparte (si el diseño no está en el XML principal).",
    )
    parser.add_argument("--version", action="version", version=f"IRE {__version__}")
    return parser


def _print_stats(workflow) -> None:
    s = workflow.statistics
    print(f"\nWorkflow: {workflow.name}  (Inspire {workflow.version})")
    print("-" * 48)
    print(f"  Módulos       : {s.modules}")
    print(f"  Variables     : {s.variables}")
    print(f"  Reglas        : {s.rules}")
    print(f"  Filtros       : {s.filters}")
    print(f"  Cruces        : {s.joins}")
    print(f"  Scripts       : {s.scripts}")
    print(f"  Lookups       : {s.lookups}")
    print(f"  Conexiones    : {s.connections}")
    print(f"  Entradas      : {s.inputs}")
    print(f"  Salidas       : {s.outputs}")
    if s.layout_pages:
        print(f"  Vars en diseño: {s.variables_in_layout} (en {s.layout_pages} páginas)")
    print("-" * 48)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    xml_path = Path(args.xml)
    if not xml_path.exists():
        print(f"error: no existe el archivo {xml_path}", file=sys.stderr)
        return 2

    print(f"Cargando {xml_path} ...")
    workflow = WorkflowParser().parse_file(xml_path, layout_path=args.layout)
    analyze(workflow)
    _print_stats(workflow)

    if args.stats_only:
        return 0

    formats = args.format or ["all"]
    if "all" in formats:
        formats = list(_GENERATORS.keys())

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = workflow.name or xml_path.stem

    print(f"\nGenerando artefactos en {out_dir}/ ...")
    failures = 0
    for fmt in formats:
        ext, factory = _GENERATORS[fmt]
        target = out_dir / f"{stem}{ext}"
        try:
            result = factory().write(workflow, target)
        except Exception as exc:  # noqa: BLE001 - un generador no debe abortar el resto
            failures += 1
            print(f"  [{fmt:9}] OMITIDO: {exc}", file=sys.stderr)
            continue
        print(f"  [{fmt:9}] {result}")

    print("\nListo." if not failures else f"\nListo (con {failures} omitido(s)).")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
