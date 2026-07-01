"""Pruebas del layout jerárquico en Python puro (sin dependencias)."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from inspire.generators.flow_layout import FlowLayoutGenerator
from inspire.generators.graphviz_gen import node_dom_id

_NS = "{http://www.w3.org/2000/svg}"


def _svg_nodes(svg: str):
    root = ET.fromstring(svg)
    return [g for g in root.iter(f"{_NS}g") if g.get("class") == "node"]


def test_svg_has_all_nodes_and_edges(workflow):
    svg = FlowLayoutGenerator().build_svg(workflow)
    assert svg.startswith("<svg")
    assert len(_svg_nodes(svg)) == len(workflow.modules)
    edges = [
        p
        for p in ET.fromstring(svg).iter(f"{_NS}path")
        if p.get("class") == "edge"
    ]
    drawable = sum(1 for c in workflow.connections if c.from_id and c.to_id)
    assert len(edges) == drawable


def test_node_ids_match_graphviz_convention(workflow):
    svg = FlowLayoutGenerator().build_svg(workflow)
    ids = {g.get("id") for g in _svg_nodes(svg)}
    for m in workflow.modules:
        assert node_dom_id(m.id) in ids


def test_layering_places_input_before_output(workflow):
    """El nodo de entrada debe quedar a la izquierda del de salida."""

    gen = FlowLayoutGenerator()
    svg = gen.build_svg(workflow)
    root = ET.fromstring(svg)
    x = {}
    for g in _svg_nodes(svg):
        rect = g.find(f"{_NS}rect")
        x[g.get("id")] = float(rect.get("x"))
    # BasePortal (input) -> ... -> Salida (output) en el fixture.
    assert x[node_dom_id("DataInput1")] < x[node_dom_id("AdvDataOutput1")]


def test_handles_cycles_without_hanging():
    from inspire.model.elements import Connection, Module
    from inspire.model.enums import ModuleCategory
    from inspire.model.workflow import Workflow

    wf = Workflow(name="cyc")
    wf.modules = [
        Module(id=f"M{i}", name=f"M{i}", kind="DataTransformer",
               category=ModuleCategory.TRANSFORM)
        for i in range(3)
    ]
    # Ciclo M0 -> M1 -> M2 -> M0
    wf.connections = [
        Connection(from_id="M0", to_id="M1"),
        Connection(from_id="M1", to_id="M2"),
        Connection(from_id="M2", to_id="M0"),
    ]
    svg = FlowLayoutGenerator().build_svg(wf)
    assert len(_svg_nodes(svg)) == 3


def test_escapes_special_chars():
    from inspire.model.elements import Module
    from inspire.model.enums import ModuleCategory
    from inspire.model.workflow import Workflow

    wf = Workflow(name="t")
    wf.modules = [
        Module(id="DT1", name='A & B <x>', kind="DataTransformer",
               category=ModuleCategory.TRANSFORM)
    ]
    svg = FlowLayoutGenerator().build_svg(wf)
    assert "&amp;" in svg
    assert "&lt;x&gt;" in svg
    # Debe seguir siendo XML válido.
    ET.fromstring(svg)
