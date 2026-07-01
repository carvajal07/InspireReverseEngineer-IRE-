"""Generadores: producen artefactos desde el modelo interno.

Ningún generador lee el XML original; todos consumen el :class:`Workflow`.
"""

from inspire.generators.json_gen import JsonGenerator
from inspire.generators.markdown_gen import MarkdownGenerator
from inspire.generators.mermaid_gen import MermaidGenerator
from inspire.generators.graphml_gen import GraphMLGenerator
from inspire.generators.graphviz_gen import GraphvizGenerator
from inspire.generators.cleanxml_gen import CleanXmlGenerator
from inspire.generators.excel_gen import ExcelGenerator
from inspire.generators.html_gen import HtmlGenerator
from inspire.generators.pdf_gen import PdfGenerator

__all__ = [
    "JsonGenerator",
    "MarkdownGenerator",
    "MermaidGenerator",
    "GraphMLGenerator",
    "GraphvizGenerator",
    "CleanXmlGenerator",
    "ExcelGenerator",
    "HtmlGenerator",
    "PdfGenerator",
]
