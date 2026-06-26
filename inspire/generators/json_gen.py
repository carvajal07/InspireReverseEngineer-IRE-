"""Generador JSON: modelo estructurado para otros sistemas."""

from __future__ import annotations

import json
from pathlib import Path

from inspire.generators.serialize import workflow_to_dict
from inspire.model.workflow import Workflow


class JsonGenerator:
    """Serializa el workflow completo a JSON."""

    def __init__(self, *, indent: int = 2) -> None:
        self.indent = indent

    def render(self, workflow: Workflow) -> str:
        return json.dumps(
            workflow_to_dict(workflow),
            indent=self.indent,
            ensure_ascii=False,
        )

    def write(self, workflow: Workflow, path: str | Path) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(self.render(workflow), encoding="utf-8")
        return out
