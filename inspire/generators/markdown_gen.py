"""Generador Markdown: documentación técnica del workflow."""

from __future__ import annotations

from pathlib import Path

from inspire.generators.mermaid_gen import MermaidGenerator
from inspire.model.enums import ModuleCategory
from inspire.model.workflow import Workflow


class MarkdownGenerator:
    """Produce documentación técnica completa en Markdown."""

    def render(self, workflow: Workflow) -> str:
        lines: list[str] = []
        out = lines.append

        out(f"# Workflow: {workflow.name or 'Inspire Workflow'}\n")
        out(f"- **Versión Inspire:** {workflow.version or 'desconocida'}")
        out(f"- **Archivo origen:** `{workflow.source_file or 'n/d'}`\n")

        self._statistics(workflow, out)
        self._diagram(workflow, out)
        self._inputs_outputs(workflow, out)
        self._variables(workflow, out)
        self._rules(workflow, out)
        self._dependencies(workflow, out)

        return "\n".join(lines) + "\n"

    # ------------------------------------------------------------------

    def _statistics(self, workflow: Workflow, out) -> None:
        s = workflow.statistics
        out("## Estadísticas\n")
        out("| Métrica | Valor |")
        out("| --- | --- |")
        out(f"| Módulos | {s.modules} |")
        out(f"| Variables | {s.variables} |")
        out(f"| Reglas | {s.rules} |")
        out(f"| Filtros | {s.filters} |")
        out(f"| Cruces | {s.joins} |")
        out(f"| Scripts | {s.scripts} |")
        out(f"| Lookups | {s.lookups} |")
        out(f"| Conexiones | {s.connections} |")
        out(f"| Entradas | {s.inputs} |")
        out(f"| Salidas | {s.outputs} |\n")

        if s.by_kind:
            out("### Módulos por tipo\n")
            out("| Tipo | Cantidad |")
            out("| --- | --- |")
            for kind, count in s.by_kind.items():
                out(f"| {kind} | {count} |")
            out("")

    def _diagram(self, workflow: Workflow, out) -> None:
        out("## Diagrama de flujo\n")
        out("```mermaid")
        out(MermaidGenerator().render(workflow).strip())
        out("```\n")

    def _inputs_outputs(self, workflow: Workflow, out) -> None:
        inputs = workflow.modules_by_category(ModuleCategory.INPUT)
        outputs = workflow.modules_by_category(ModuleCategory.OUTPUT)
        if inputs:
            out("## Entradas\n")
            for m in inputs:
                loc = f" — `{m.location}`" if m.location else ""
                out(f"- **{m.name}** ({m.kind}){loc}")
            out("")
        if outputs:
            out("## Salidas\n")
            for m in outputs:
                loc = f" — `{m.location}`" if m.location else ""
                out(f"- **{m.name}** ({m.kind}){loc}")
            out("")

    def _variables(self, workflow: Workflow, out) -> None:
        if not workflow.variables:
            return
        has_layout = workflow.layout is not None and workflow.layout.found_layout
        out("## Variables\n")
        if has_layout:
            out("| Variable | Tipo | Creada en | Modificada en | Usada en | En diseño |")
            out("| --- | --- | --- | --- | --- | --- |")
            for v in workflow.variables:
                design = "Sí" if v.used_in_layout else "No"
                out(
                    f"| {v.name} | {v.type or '-'} | {len(v.created_in)} | "
                    f"{len(v.modified_in)} | {len(v.used_in)} | {design} |"
                )
        else:
            out("| Variable | Tipo | Creada en | Modificada en | Usada en |")
            out("| --- | --- | --- | --- | --- |")
            for v in workflow.variables:
                out(
                    f"| {v.name} | {v.type or '-'} | "
                    f"{len(v.created_in)} | {len(v.modified_in)} | {len(v.used_in)} |"
                )
        out("")

    def _rules(self, workflow: Workflow, out) -> None:
        modules_with_logic = [m for m in workflow.modules if m.has_logic]
        if not modules_with_logic:
            return
        out("## Reglas y transformaciones\n")
        for m in modules_with_logic:
            out(f"### {m.name} ({m.kind})\n")
            for t in m.transformations:
                out(f"- `{t.dot_name}` → {t.expression or t.fcv_type}")
                if t.script:
                    out("  ```")
                    for line in t.script.splitlines():
                        out(f"  {line}")
                    out("  ```")
            if m.filter is not None:
                out(f"- **Filtro:** `{m.filter.as_expression()}`")
            for k in m.join_keys:
                out(f"- **Join** ({m.join_type}): `{k.left}` = `{k.right}`")
            for old, new in m.renames:
                out(f"- **Renombra:** `{old}` → `{new}`")
            for g in m.group_by:
                out(f"- **Group by:** `{g}`")
            for s in m.scripts:
                out(f"- **Script** {s.language} ({s.line_count} líneas)")
            for p in m.parameters:
                out(f"- **Parámetro:** `{p.name}` ({p.type}) = `{p.default}`")
            out("")

    def _dependencies(self, workflow: Workflow, out) -> None:
        if not workflow.dependencies:
            return
        out("## Dependencias\n")
        out("| Variable | Módulo origen | Módulo destino |")
        out("| --- | --- | --- |")
        for d in workflow.dependencies[:500]:
            out(f"| {d.variable} | {d.source_module} | {d.target_module} |")
        if len(workflow.dependencies) > 500:
            out(f"| ... | ({len(workflow.dependencies) - 500} más) | ... |")
        out("")

    def write(self, workflow: Workflow, path: str | Path) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(self.render(workflow), encoding="utf-8")
        return out
