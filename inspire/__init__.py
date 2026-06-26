"""Inspire Reverse Engineer (IRE).

Herramienta de análisis e ingeniería inversa de workflows de Quadient
Inspire Designer. Carga un XML exportado, reconstruye un modelo interno
independiente del diseñador y genera documentación, análisis y artefactos
de migración.
"""

from inspire.parser import parse_workflow
from inspire.analyzers import analyze

__version__ = "0.1.0"

__all__ = ["parse_workflow", "analyze", "__version__"]
