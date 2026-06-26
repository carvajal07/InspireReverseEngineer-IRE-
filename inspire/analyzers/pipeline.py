"""Pipeline de análisis: ejecuta todos los analizadores sobre un workflow."""

from __future__ import annotations

from dataclasses import dataclass

from inspire.analyzers.dependency import DependencyAnalyzer
from inspire.analyzers.rules import RuleAnalyzer, RuleReport
from inspire.analyzers.statistics import StatisticsAnalyzer
from inspire.analyzers.variables import VariableAnalyzer, VariableReport
from inspire.model.workflow import Workflow


@dataclass(slots=True)
class AnalysisResult:
    """Agrupa los resultados de los analizadores semánticos."""

    workflow: Workflow
    rules: RuleReport
    variables: VariableReport


def analyze(workflow: Workflow) -> AnalysisResult:
    """Ejecuta el análisis semántico completo y anota el workflow in-place."""

    StatisticsAnalyzer().analyze(workflow)
    DependencyAnalyzer().analyze(workflow)
    rules = RuleAnalyzer().analyze(workflow)
    variables = VariableAnalyzer().analyze(workflow)
    # Reflejar el conteo de reglas reales en las estadísticas.
    workflow.statistics.rules = len(rules.rules)
    return AnalysisResult(workflow=workflow, rules=rules, variables=variables)
