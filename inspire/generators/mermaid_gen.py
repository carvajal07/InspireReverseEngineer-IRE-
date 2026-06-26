"""Generador Mermaid: diagrama de flujo del workflow."""

from __future__ import annotations

import re
from pathlib import Path

from inspire.model.enums import ModuleCategory
from inspire.model.workflow import Workflow

#: Forma del nodo según la categoría funcional.
_SHAPE = {
    ModuleCategory.INPUT: ("([", "])"),
    ModuleCategory.OUTPUT: ("([", "])"),
    ModuleCategory.CONTROL: ("{", "}"),
    ModuleCategory.INTEGRATION: ("[/", "/]"),
    ModuleCategory.SCRIPT: ("[[", "]]"),
    ModuleCategory.TRANSFORM: ("[", "]"),
    ModuleCategory.OTHER: ("[", "]"),
}


def _safe_id(raw: str) -> str:
    return re.sub(r"\W", "_", raw) or "n"


def _label(text: str) -> str:
    return text.replace('"', "'").replace("\n", " ")


class MermaidGenerator:
    """Genera un ``flowchart`` de Mermaid a partir de módulos y conexiones."""

    def __init__(self, direction: str = "LR") -> None:
        self.direction = direction

    def render(self, workflow: Workflow) -> str:
        lines = [f"flowchart {self.direction}"]
        for module in workflow.modules:
            node_id = _safe_id(module.id)
            open_b, close_b = _SHAPE.get(module.category, ("[", "]"))
            lines.append(
                f'    {node_id}{open_b}"{_label(module.name)}<br/>'
                f'<small>{module.kind}</small>"{close_b}'
            )
        for conn in workflow.connections:
            if conn.from_id and conn.to_id:
                lines.append(f"    {_safe_id(conn.from_id)} --> {_safe_id(conn.to_id)}")
        return "\n".join(lines) + "\n"

    def write(self, workflow: Workflow, path: str | Path) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(self.render(workflow), encoding="utf-8")
        return out
