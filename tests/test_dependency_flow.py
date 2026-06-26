"""Prueba del camino de dependencias derivadas del flujo de conexiones."""

from __future__ import annotations

from inspire.analyzers.dependency import DependencyAnalyzer
from inspire.model.elements import Connection, Module, Variable
from inspire.model.enums import ModuleCategory
from inspire.model.workflow import Workflow


def test_flow_variable_deps_used_when_no_explicit_usage():
    wf = Workflow(name="t")
    wf.modules = [
        Module(id="A", name="A", kind="DataTransformer", category=ModuleCategory.TRANSFORM),
        Module(id="B", name="B", kind="AdvDataOutput", category=ModuleCategory.OUTPUT),
    ]
    wf.connections = [Connection(from_id="A", to_id="B")]
    # Variable producida en A pero sin consumo explícito registrado.
    var = Variable(name="v")
    var.created_in.add("A")
    wf.variables = [var]

    deps = DependencyAnalyzer().analyze(wf)
    assert any(d.source_module == "A" and d.target_module == "B" for d in deps)
