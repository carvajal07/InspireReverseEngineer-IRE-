"""Generador Excel: libros de Variables, Reglas, Join y Dependencias.

Usa ``openpyxl`` si está disponible; de lo contrario degrada a archivos CSV
(un archivo por hoja) para no requerir dependencias pesadas.
"""

from __future__ import annotations

import csv
from pathlib import Path

from inspire.analyzers.rules import RuleAnalyzer
from inspire.model.workflow import Workflow

try:  # pragma: no cover - depende del entorno
    from openpyxl import Workbook

    _HAS_OPENPYXL = True
except ImportError:  # pragma: no cover
    _HAS_OPENPYXL = False


class ExcelGenerator:
    """Genera las hojas de cálculo de análisis del workflow."""

    def _sheets(self, workflow: Workflow) -> dict[str, tuple[list[str], list[list[str]]]]:
        rules = RuleAnalyzer().analyze(workflow).rules

        variables = (
            ["Variable", "Tipo", "Creada en", "Modificada en", "Usada en"],
            [
                [
                    v.name,
                    v.type,
                    "; ".join(sorted(v.created_in)),
                    "; ".join(sorted(v.modified_in)),
                    "; ".join(sorted(v.used_in)),
                ]
                for v in workflow.variables
            ],
        )
        reglas = (
            ["Módulo", "Categoría", "Tipo", "Destino", "Expresión"],
            [
                [r.module, r.category, r.rule_type, r.target, r.expression]
                for r in rules
            ],
        )
        joins = (
            ["Módulo", "Tipo", "Llave izquierda", "Llave derecha"],
            [
                [m.name, m.join_type, k.left, k.right]
                for m in workflow.modules
                for k in m.join_keys
            ],
        )
        deps = (
            ["Variable", "Módulo origen", "Módulo destino"],
            [
                [d.variable, d.source_module, d.target_module]
                for d in workflow.dependencies
            ],
        )
        return {
            "Variables": variables,
            "Reglas": reglas,
            "Join": joins,
            "Dependencias": deps,
        }

    def write(self, workflow: Workflow, path: str | Path) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        sheets = self._sheets(workflow)

        if _HAS_OPENPYXL:
            wb = Workbook()
            wb.remove(wb.active)
            for title, (header, rows) in sheets.items():
                ws = wb.create_sheet(title=title)
                ws.append(header)
                for row in rows:
                    ws.append(row)
            wb.save(out)
            return out

        # Fallback a CSV: un archivo por hoja.
        base = out.with_suffix("")
        for title, (header, rows) in sheets.items():
            csv_path = Path(f"{base}_{title}.csv")
            with csv_path.open("w", newline="", encoding="utf-8") as fh:
                writer = csv.writer(fh)
                writer.writerow(header)
                writer.writerows(rows)
        return base

    @property
    def uses_excel(self) -> bool:
        return _HAS_OPENPYXL
