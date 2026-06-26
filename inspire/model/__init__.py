"""Modelo interno (AST) de Inspire Reverse Engineer.

Este paquete define la única fuente de verdad del workflow una vez parseado.
Ningún generador vuelve a leer el XML: todo se construye desde estas clases.
"""

from inspire.model.enums import ModuleCategory, ModuleKind
from inspire.model.elements import (
    Connection,
    DataField,
    Filter,
    FilterCondition,
    JoinKey,
    Module,
    Parameter,
    Script,
    Transformation,
    Variable,
)
from inspire.model.workflow import Dependency, Statistics, Workflow

__all__ = [
    "ModuleCategory",
    "ModuleKind",
    "Connection",
    "DataField",
    "Filter",
    "FilterCondition",
    "JoinKey",
    "Module",
    "Parameter",
    "Script",
    "Transformation",
    "Variable",
    "Dependency",
    "Statistics",
    "Workflow",
]
