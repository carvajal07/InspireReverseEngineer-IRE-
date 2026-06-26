"""Modelo raíz: Workflow, dependencias y estadísticas."""

from __future__ import annotations

from dataclasses import dataclass, field

from inspire.model.elements import Connection, Module, Variable
from inspire.model.enums import ModuleCategory


@dataclass(slots=True)
class Dependency:
    """Dependencia de una variable entre módulos."""

    variable: str
    source_module: str
    target_module: str


@dataclass(slots=True)
class Statistics:
    """Métricas agregadas del workflow."""

    modules: int = 0
    variables: int = 0
    rules: int = 0
    filters: int = 0
    joins: int = 0
    scripts: int = 0
    lookups: int = 0
    connections: int = 0
    inputs: int = 0
    outputs: int = 0
    by_kind: dict[str, int] = field(default_factory=dict)
    by_category: dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict[str, object]:
        return {
            "modules": self.modules,
            "variables": self.variables,
            "rules": self.rules,
            "filters": self.filters,
            "joins": self.joins,
            "scripts": self.scripts,
            "lookups": self.lookups,
            "connections": self.connections,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "by_kind": dict(self.by_kind),
            "by_category": dict(self.by_category),
        }


@dataclass(slots=True)
class Workflow:
    """Modelo interno completo de un workflow de Inspire.

    Es la única fuente de verdad para todos los generadores y analizadores.
    """

    name: str = ""
    version: str = ""
    source_file: str = ""

    modules: list[Module] = field(default_factory=list)
    connections: list[Connection] = field(default_factory=list)
    variables: list[Variable] = field(default_factory=list)
    dependencies: list[Dependency] = field(default_factory=list)
    statistics: Statistics = field(default_factory=Statistics)

    # ----- Índices y accesos de conveniencia -----

    def module_by_id(self, module_id: str) -> Module | None:
        for module in self.modules:
            if module.id == module_id:
                return module
        return None

    def modules_by_category(self, category: ModuleCategory) -> list[Module]:
        return [m for m in self.modules if m.category == category]

    @property
    def inputs(self) -> list[Module]:
        return self.modules_by_category(ModuleCategory.INPUT)

    @property
    def outputs(self) -> list[Module]:
        return self.modules_by_category(ModuleCategory.OUTPUT)

    @property
    def variable_index(self) -> dict[str, Variable]:
        return {v.name: v for v in self.variables}
