"""Statistics Analyzer: métricas agregadas del workflow."""

from __future__ import annotations

from collections import Counter

from inspire.model.enums import ModuleCategory, ModuleKind
from inspire.model.workflow import Statistics, Workflow

#: Joins reales (cruces). DataMerger fusiona; CustCode cruza/lookup.
_JOIN_KINDS = {ModuleKind.CUST_CODE.value, ModuleKind.DATA_MERGER.value}


class StatisticsAnalyzer:
    """Calcula y adjunta las estadísticas al workflow."""

    def analyze(self, workflow: Workflow) -> Statistics:
        stats = Statistics()
        stats.modules = len(workflow.modules)
        stats.variables = len(workflow.variables)
        stats.connections = len(workflow.connections)

        by_kind: Counter[str] = Counter()
        by_category: Counter[str] = Counter()

        for module in workflow.modules:
            by_kind[module.kind] += 1
            by_category[module.category.value] += 1

            stats.rules += len(module.transformations)
            if module.filter is not None:
                stats.filters += 1
            if module.kind in _JOIN_KINDS:
                stats.joins += 1
            stats.scripts += len(module.scripts)

        stats.lookups = sum(
            1
            for m in workflow.modules
            if m.kind == ModuleKind.CUST_CODE.value
        )
        stats.inputs = by_category.get(ModuleCategory.INPUT.value, 0)
        stats.outputs = by_category.get(ModuleCategory.OUTPUT.value, 0)
        stats.variables_in_layout = sum(
            1 for v in workflow.variables if v.used_in_layout
        )
        if workflow.layout is not None:
            stats.layout_pages = len(workflow.layout.pages)
        stats.by_kind = dict(by_kind.most_common())
        stats.by_category = dict(by_category.most_common())

        workflow.statistics = stats
        return stats
