"""Generadores: producen artefactos desde el modelo interno.

Ningún generador lee el XML original; todos consumen el :class:`Workflow`.
"""

from inspire.generators.json_gen import JsonGenerator
from inspire.generators.markdown_gen import MarkdownGenerator
from inspire.generators.mermaid_gen import MermaidGenerator
from inspire.generators.graphml_gen import GraphMLGenerator
from inspire.generators.cleanxml_gen import CleanXmlGenerator
from inspire.generators.excel_gen import ExcelGenerator

__all__ = [
    "JsonGenerator",
    "MarkdownGenerator",
    "MermaidGenerator",
    "GraphMLGenerator",
    "CleanXmlGenerator",
    "ExcelGenerator",
]
