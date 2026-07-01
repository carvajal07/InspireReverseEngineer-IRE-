"""Generador Graphviz: diagrama de flujo con layout jerárquico (dot).

El workflow es un flujo dirigido, por lo que un layout por capas (Graphviz
``dot``) es mucho más legible que un diagrama de fuerza o el de Mermaid,
incluso con cientos de módulos.

Genera el código DOT sin dependencias (sólo texto) y, si el binario ``dot``
está disponible, produce el SVG ya diagramado. El SVG se incrusta en el portal
HTML y también puede exportarse como archivo suelto.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from inspire.model.enums import ModuleCategory
from inspire.model.workflow import Workflow

#: Color de relleno por categoría (coherente con el portal HTML).
CATEGORY_COLORS: dict[str, str] = {
    ModuleCategory.INPUT.value: "#5eead4",
    ModuleCategory.TRANSFORM.value: "#fbbf24",
    ModuleCategory.CONTROL.value: "#f87171",
    ModuleCategory.INTEGRATION.value: "#c084fc",
    ModuleCategory.SCRIPT.value: "#4ade80",
    ModuleCategory.OUTPUT.value: "#fb923c",
    ModuleCategory.OTHER.value: "#cbd5e1",
}


def node_dom_id(module_id: str) -> str:
    """Id estable para el nodo (coherente con el JS del portal)."""

    return "fn" + "".join(c if c.isalnum() else "_" for c in module_id)


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


class GraphvizGenerator:
    """Produce el diagrama de flujo con Graphviz ``dot``."""

    def __init__(self, direction: str = "LR") -> None:
        self.direction = direction

    @property
    def available(self) -> bool:
        """True si el binario ``dot`` está instalado."""

        return shutil.which("dot") is not None

    # ------------------------------------------------------------------

    def build_dot(self, workflow: Workflow) -> str:
        """Genera el código DOT del workflow (no requiere el binario)."""

        lines: list[str] = ["digraph workflow {"]
        lines.append(f'  rankdir="{self.direction}";')
        lines.append('  bgcolor="transparent";')
        lines.append('  nodesep=0.25; ranksep=0.6; splines=true;')
        lines.append(
            '  node [shape=box style="filled,rounded" fontname="Helvetica" '
            'fontsize=10 color="#1e293b"];'
        )
        lines.append('  edge [color="#94a3b8" arrowsize=0.7];')

        for module in workflow.modules:
            fill = CATEGORY_COLORS.get(module.category.value, "#cbd5e1")
            label = _escape(f"{module.name}\n({module.kind})")
            lines.append(
                f'  "{node_dom_id(module.id)}" '
                f'[label="{label}" fillcolor="{fill}" '
                f'id="{node_dom_id(module.id)}" '
                f'tooltip="{_escape(module.name)} [{_escape(module.kind)}]"];'
            )

        for conn in workflow.connections:
            if conn.from_id and conn.to_id:
                lines.append(
                    f'  "{node_dom_id(conn.from_id)}" -> '
                    f'"{node_dom_id(conn.to_id)}";'
                )

        lines.append("}")
        return "\n".join(lines) + "\n"

    def render_svg(self, workflow: Workflow) -> str:
        """Renderiza el SVG invocando ``dot`` (requiere el binario)."""

        dot_source = self.build_dot(workflow)
        try:
            proc = subprocess.run(
                ["dot", "-Tsvg"],
                input=dot_source.encode("utf-8"),
                capture_output=True,
                check=True,
            )
        except FileNotFoundError as exc:  # pragma: no cover - depende del entorno
            raise RuntimeError(
                "El binario 'dot' de Graphviz no está instalado. "
                "Instálalo con: apt-get install graphviz (o brew install graphviz)."
            ) from exc
        return proc.stdout.decode("utf-8")

    def write(self, workflow: Workflow, path: str | Path) -> Path:
        """Escribe el SVG si ``dot`` está disponible; si no, el código DOT."""

        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        if self.available:
            out.write_text(self.render_svg(workflow), encoding="utf-8")
            return out
        dot_path = out.with_suffix(".dot")
        dot_path.write_text(self.build_dot(workflow), encoding="utf-8")
        return dot_path
