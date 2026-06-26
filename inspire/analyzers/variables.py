"""Variable Analyzer: detecta variables sin uso, huérfanas, duplicadas, críticas."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from inspire.model.elements import Variable
from inspire.model.workflow import Workflow


@dataclass(slots=True)
class VariableReport:
    """Resultado del análisis de variables."""

    total: int = 0
    unused: list[str] = field(default_factory=list)
    orphan: list[str] = field(default_factory=list)
    duplicated: list[str] = field(default_factory=list)
    critical: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "total": self.total,
            "unused": self.unused,
            "orphan": self.orphan,
            "duplicated": self.duplicated,
            "critical": self.critical,
        }


class VariableAnalyzer:
    """Clasifica las variables según su uso a lo largo del workflow.

    * **Sin uso**: declarada pero nunca consumida ni modificada.
    * **Huérfana**: usada pero nunca declarada en ningún módulo.
    * **Duplicada**: declarada con el mismo nombre en varios módulos.
    * **Crítica**: usada/modificada en muchos módulos (alta centralidad).
    """

    def __init__(self, critical_threshold: int = 3) -> None:
        self.critical_threshold = critical_threshold

    def analyze(self, workflow: Workflow) -> VariableReport:
        report = VariableReport(total=len(workflow.variables))
        name_counts: Counter[str] = Counter()

        for variable in workflow.variables:
            name_counts[variable.name] += len(variable.created_in)
            if variable.is_unused:
                report.unused.append(variable.name)
            if variable.is_orphan:
                report.orphan.append(variable.name)
            if self._impact(variable) >= self.critical_threshold:
                report.critical.append(variable.name)

        report.duplicated = sorted(
            name for name, count in name_counts.items() if count > 1
        )
        report.unused.sort()
        report.orphan.sort()
        report.critical.sort()
        return report

    @staticmethod
    def _impact(variable: Variable) -> int:
        return len(variable.created_in | variable.modified_in | variable.used_in)
