"""Generador GraphML: exporta el workflow para Gephi / yEd / Cytoscape."""

from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from inspire.model.workflow import Workflow


class GraphMLGenerator:
    """Genera un documento GraphML con nodos (módulos) y aristas (conexiones)."""

    def render(self, workflow: Workflow) -> str:
        lines: list[str] = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
            '  <key id="name" for="node" attr.name="name" attr.type="string"/>',
            '  <key id="kind" for="node" attr.name="kind" attr.type="string"/>',
            '  <key id="category" for="node" attr.name="category" attr.type="string"/>',
            '  <graph edgedefault="directed">',
        ]
        for module in workflow.modules:
            node_id = escape(module.id)
            lines.append(f'    <node id="{node_id}">')
            lines.append(f'      <data key="name">{escape(module.name)}</data>')
            lines.append(f'      <data key="kind">{escape(module.kind)}</data>')
            lines.append(
                f'      <data key="category">{escape(module.category.value)}</data>'
            )
            lines.append("    </node>")
        for i, conn in enumerate(workflow.connections):
            if conn.from_id and conn.to_id:
                lines.append(
                    f'    <edge id="e{i}" source="{escape(conn.from_id)}" '
                    f'target="{escape(conn.to_id)}"/>'
                )
        lines.append("  </graph>")
        lines.append("</graphml>")
        return "\n".join(lines) + "\n"

    def write(self, workflow: Workflow, path: str | Path) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(self.render(workflow), encoding="utf-8")
        return out
