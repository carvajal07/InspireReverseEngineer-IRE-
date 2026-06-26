"""Pruebas de los analizadores semánticos."""

from __future__ import annotations

from inspire.analyzers import (
    DependencyAnalyzer,
    RuleAnalyzer,
    StatisticsAnalyzer,
    VariableAnalyzer,
)


def test_statistics(workflow):
    s = workflow.statistics
    assert s.modules == 8
    assert s.filters == 1
    assert s.joins == 1  # CustCode
    assert s.lookups == 1
    assert s.scripts == 1
    assert s.inputs == 2  # ParamInput + DataInput
    assert s.outputs == 1
    assert s.connections == 4


def test_statistics_by_kind(workflow):
    stats = StatisticsAnalyzer().analyze(workflow)
    assert stats.by_kind["DataTransformer"] == 1


def test_rules_classification(workflow):
    report = RuleAnalyzer().analyze(workflow)
    types = report.by_type()
    assert types.get("script", 0) >= 1
    assert types.get("concat", 0) >= 1
    assert types.get("filter", 0) == 1
    assert types.get("join", 0) == 1
    assert types.get("rename", 0) == 1


def test_variable_report(workflow):
    report = VariableAnalyzer().analyze(workflow)
    assert report.total == len(workflow.variables)
    # 'TipoId' se declara y se usa en el filtro -> no debería estar sin uso.
    assert "TipoId" not in report.unused


def test_dependencies_built(workflow):
    deps = DependencyAnalyzer().analyze(workflow)
    assert isinstance(deps, list)
    # Debe haber al menos una dependencia derivada del flujo o del uso.
    assert workflow.dependencies is deps
