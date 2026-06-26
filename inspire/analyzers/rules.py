"""Rule Analyzer: clasifica automáticamente las reglas de negocio."""

from __future__ import annotations

from dataclasses import dataclass, field

from inspire.model.workflow import Workflow


@dataclass(slots=True)
class BusinessRule:
    """Una regla de negocio clasificada extraída del workflow."""

    module: str
    category: str  # transformation | filter | join | script | rename | group
    target: str
    rule_type: str  # script | concat | convert | format_number | counter | ...
    expression: str
    detail: str = ""


@dataclass(slots=True)
class RuleReport:
    rules: list[BusinessRule] = field(default_factory=list)

    def by_type(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for rule in self.rules:
            counts[rule.rule_type] = counts.get(rule.rule_type, 0) + 1
        return counts


class RuleAnalyzer:
    """Recorre los módulos y clasifica cada pieza de lógica como regla."""

    def analyze(self, workflow: Workflow) -> RuleReport:
        report = RuleReport()

        for module in workflow.modules:
            for transformation in module.transformations:
                report.rules.append(
                    BusinessRule(
                        module=module.name,
                        category="transformation",
                        target=transformation.dot_name,
                        rule_type=transformation.kind or "transformation",
                        expression=transformation.expression,
                        detail=transformation.script[:200],
                    )
                )
            if module.filter is not None:
                report.rules.append(
                    BusinessRule(
                        module=module.name,
                        category="filter",
                        target=module.name,
                        rule_type="filter",
                        expression=module.filter.as_expression(),
                        detail="else-output" if module.filter.has_else_output else "",
                    )
                )
            for key in module.join_keys:
                report.rules.append(
                    BusinessRule(
                        module=module.name,
                        category="join",
                        target=f"{key.left} = {key.right}",
                        rule_type="join",
                        expression=f"{module.join_type}",
                    )
                )
            for script in module.scripts:
                report.rules.append(
                    BusinessRule(
                        module=module.name,
                        category="script",
                        target=module.name,
                        rule_type="script",
                        expression=f"{script.language} ({script.line_count} líneas)",
                        detail=script.code[:200],
                    )
                )
            for old, new in module.renames:
                report.rules.append(
                    BusinessRule(
                        module=module.name,
                        category="rename",
                        target=f"{old} -> {new}",
                        rule_type="rename",
                        expression=f"{old} -> {new}",
                    )
                )
            for group in module.group_by:
                report.rules.append(
                    BusinessRule(
                        module=module.name,
                        category="group",
                        target=group,
                        rule_type="group_by",
                        expression=f"GROUP BY {group}",
                    )
                )

        return report
