"""Generador PDF: documentación completa del workflow.

Usa ``reportlab`` para construir un documento estructurado directamente desde
el modelo interno. Si ``reportlab`` no está instalado, lanza un error claro
indicando cómo habilitarlo.
"""

from __future__ import annotations

from pathlib import Path

from inspire.analyzers.rules import RuleAnalyzer
from inspire.analyzers.variables import VariableAnalyzer
from inspire.model.workflow import Workflow

try:  # pragma: no cover - depende del entorno
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    _HAS_REPORTLAB = True
except ImportError:  # pragma: no cover
    _HAS_REPORTLAB = False


class PdfGenerationError(RuntimeError):
    """Se lanza cuando no es posible generar el PDF."""


class PdfGenerator:
    """Genera la documentación del workflow en PDF."""

    #: Máximo de filas por tabla para mantener el PDF manejable.
    MAX_ROWS = 400
    #: Máximo de caracteres por celda (evita filas más altas que la página).
    MAX_CELL = 240

    @property
    def available(self) -> bool:
        return _HAS_REPORTLAB

    def write(self, workflow: Workflow, path: str | Path) -> Path:
        if not _HAS_REPORTLAB:
            raise PdfGenerationError(
                "La generación de PDF requiere 'reportlab'. "
                "Instálalo con: pip install reportlab"
            )
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)

        doc = SimpleDocTemplate(
            str(out),
            pagesize=A4,
            title=f"IRE · {workflow.name}",
            leftMargin=1.8 * cm,
            rightMargin=1.8 * cm,
            topMargin=1.8 * cm,
            bottomMargin=1.8 * cm,
        )
        styles = self._styles()
        story: list = []

        self._cover(workflow, story, styles)
        self._statistics(workflow, story, styles)
        self._inputs_outputs(workflow, story, styles)
        self._rules(workflow, story, styles)
        self._variables(workflow, story, styles)

        doc.build(story)
        return out

    # ------------------------------------------------------------------

    @staticmethod
    def _styles():
        styles = getSampleStyleSheet()
        styles.add(
            ParagraphStyle(
                "H1b", parent=styles["Heading1"], textColor=colors.HexColor("#0f766e")
            )
        )
        styles.add(
            ParagraphStyle(
                "H2b",
                parent=styles["Heading2"],
                textColor=colors.HexColor("#0369a1"),
                spaceBefore=14,
            )
        )
        styles.add(
            ParagraphStyle(
                "Small", parent=styles["Normal"], fontSize=8, alignment=TA_LEFT
            )
        )
        return styles

    def _cell(self, value: object, styles) -> "Paragraph":
        from xml.sax.saxutils import escape

        text = str(value)
        if len(text) > self.MAX_CELL:
            text = text[: self.MAX_CELL - 1] + "…"
        return Paragraph(escape(text), styles["Small"])

    def _table(self, header: list[str], rows: list[list[str]], styles) -> "Table":
        capped = rows[: self.MAX_ROWS]
        data = [header] + [[self._cell(c, styles) for c in row] for row in capped]
        table = Table(data, repeatRows=1, hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0369a1")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTSIZE", (0, 0), (-1, 0), 8),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        return table

    def _cover(self, workflow: Workflow, story, styles) -> None:
        story.append(Spacer(1, 4 * cm))
        story.append(Paragraph("Inspire Reverse Engineer", styles["H1b"]))
        story.append(Paragraph(f"Workflow: <b>{workflow.name}</b>", styles["Title"]))
        story.append(Spacer(1, 0.5 * cm))
        story.append(
            Paragraph(f"Versión Inspire: {workflow.version or 'desconocida'}", styles["Normal"])
        )
        story.append(
            Paragraph(f"Archivo origen: {workflow.source_file or 'n/d'}", styles["Normal"])
        )
        story.append(PageBreak())

    def _statistics(self, workflow: Workflow, story, styles) -> None:
        s = workflow.statistics
        story.append(Paragraph("Estadísticas", styles["H2b"]))
        rows = [
            ["Módulos", s.modules], ["Variables", s.variables], ["Reglas", s.rules],
            ["Filtros", s.filters], ["Joins", s.joins], ["Scripts", s.scripts],
            ["Lookups", s.lookups], ["Conexiones", s.connections],
            ["Entradas", s.inputs], ["Salidas", s.outputs],
        ]
        story.append(self._table(["Métrica", "Valor"], [[k, str(v)] for k, v in rows], styles))
        if s.by_kind:
            story.append(Spacer(1, 0.4 * cm))
            story.append(Paragraph("Módulos por tipo", styles["H2b"]))
            story.append(
                self._table(
                    ["Tipo", "Cantidad"],
                    [[k, str(v)] for k, v in s.by_kind.items()],
                    styles,
                )
            )

    def _inputs_outputs(self, workflow: Workflow, story, styles) -> None:
        from inspire.model.enums import ModuleCategory

        for title, cat in [("Entradas", ModuleCategory.INPUT), ("Salidas", ModuleCategory.OUTPUT)]:
            mods = workflow.modules_by_category(cat)
            if not mods:
                continue
            story.append(Paragraph(title, styles["H2b"]))
            story.append(
                self._table(
                    ["Nombre", "Tipo", "Ubicación"],
                    [[m.name, m.kind, m.location or "—"] for m in mods],
                    styles,
                )
            )

    def _rules(self, workflow: Workflow, story, styles) -> None:
        rules = RuleAnalyzer().analyze(workflow).rules
        if not rules:
            return
        story.append(PageBreak())
        story.append(Paragraph(f"Reglas de negocio ({len(rules)})", styles["H2b"]))
        story.append(
            self._table(
                ["Módulo", "Tipo", "Destino", "Expresión"],
                [[r.module, r.rule_type, r.target, r.expression] for r in rules],
                styles,
            )
        )

    def _variables(self, workflow: Workflow, story, styles) -> None:
        if not workflow.variables:
            return
        report = VariableAnalyzer().analyze(workflow)
        story.append(PageBreak())
        story.append(Paragraph(f"Variables ({len(workflow.variables)})", styles["H2b"]))
        story.append(
            Paragraph(
                f"Sin uso: {len(report.unused)} · Huérfanas: {len(report.orphan)} · "
                f"Críticas: {len(report.critical)} · Duplicadas: {len(report.duplicated)}",
                styles["Normal"],
            )
        )
        story.append(Spacer(1, 0.3 * cm))
        story.append(
            self._table(
                ["Variable", "Tipo", "Creada en", "Usada en"],
                [
                    [v.name, v.type, ", ".join(sorted(v.created_in)), ", ".join(sorted(v.used_in))]
                    for v in workflow.variables
                ],
                styles,
            )
        )
