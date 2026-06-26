"""Análisis ligero de scripts embebidos para inferir variables."""

from __future__ import annotations

import re

from inspire.model.elements import Script

# Patrones de acceso a campos/variables comunes en scripts de Inspire.
_READ_PATTERNS = [
    re.compile(r'Get(?:String|Int|Double|Bool|Value)\s*\(\s*"([^"]+)"', re.I),
    re.compile(r'\bInput\b'),
]
_WRITE_PATTERNS = [
    re.compile(r'Set(?:String|Int|Double|Bool|Value)\s*\(\s*"([^"]+)"', re.I),
    re.compile(r'\breturn\b'),
]
_QUOTED = re.compile(r'"([A-Za-z_][\w.]*)"')


def _detect_language(code: str) -> str:
    lowered = code.lower()
    if "function" in lowered or "var " in lowered or "===" in lowered:
        return "JavaScript"
    if "dim " in lowered or "end sub" in lowered or "end function" in lowered:
        return "VB"
    if "using " in lowered or "namespace" in lowered:
        return "C#"
    return "Script"


def build_script(code: str, language: str | None = None) -> Script:
    """Construye un :class:`Script` detectando lecturas/escrituras aproximadas."""

    code = code or ""
    reads: set[str] = set()
    writes: set[str] = set()
    for pattern in _READ_PATTERNS:
        for match in pattern.finditer(code):
            if match.groups():
                reads.add(match.group(1))
    for pattern in _WRITE_PATTERNS:
        for match in pattern.finditer(code):
            if match.groups():
                writes.add(match.group(1))
    return Script(
        language=language or _detect_language(code),
        code=code,
        reads=sorted(reads),
        writes=sorted(writes),
    )
