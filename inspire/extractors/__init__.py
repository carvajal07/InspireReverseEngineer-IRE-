"""Extractores: convierten cada tipo de módulo XML en el modelo interno."""

from inspire.extractors.registry import ExtractorRegistry, build_module

__all__ = ["ExtractorRegistry", "build_module"]
