"""Carga y parseo de XML de Inspire hacia el modelo interno."""

from inspire.parser.loader import XmlLoader, load_xml
from inspire.parser.parser import WorkflowParser, parse_workflow

__all__ = ["XmlLoader", "load_xml", "WorkflowParser", "parse_workflow"]
