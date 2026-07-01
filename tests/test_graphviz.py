"""Pruebas del generador Graphviz."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from inspire.generators import GraphvizGenerator
from inspire.generators.graphviz_gen import node_dom_id


def test_dot_source_has_nodes_and_edges(workflow):
    dot = GraphvizGenerator().build_dot(workflow)
    assert dot.startswith("digraph workflow {")
    assert 'rankdir="LR"' in dot
    # Un nodo por módulo y una arista por conexión.
    assert dot.count("[label=") == len(workflow.modules)
    assert dot.count(" -> ") == sum(
        1 for c in workflow.connections if c.from_id and c.to_id
    )


def test_dot_escapes_special_chars():
    from inspire.model.elements import Module
    from inspire.model.enums import ModuleCategory
    from inspire.model.workflow import Workflow

    wf = Workflow(name="t")
    wf.modules = [
        Module(id="DT1", name='Raro"&<>', kind="DataTransformer",
               category=ModuleCategory.TRANSFORM)
    ]
    dot = GraphvizGenerator().build_dot(wf)
    # Las comillas del nombre deben ir escapadas para no romper el DOT.
    assert '\\"' in dot
    assert node_dom_id("DT1") == "fnDT1"


def test_node_dom_id_stable():
    assert node_dom_id("CustCode1") == "fnCustCode1"
    assert node_dom_id("a b&c") == "fna_b_c"


def test_render_svg_when_available(workflow):
    gen = GraphvizGenerator()
    if not gen.available:
        pytest.skip("binario 'dot' no instalado")
    svg = gen.render_svg(workflow)
    root = ET.fromstring(svg)
    assert root.tag.endswith("svg")
    # Un grupo de nodo por módulo.
    ns = "{http://www.w3.org/2000/svg}"
    nodes = [g for g in root.iter(f"{ns}g") if g.get("class") == "node"]
    assert len(nodes) == len(workflow.modules)


def test_write_svg_or_dot(workflow, tmp_path):
    gen = GraphvizGenerator()
    out = gen.write(workflow, tmp_path / "flow.svg")
    assert out.exists()
    text = out.read_text()
    if gen.available:
        assert out.suffix == ".svg" and "<svg" in text
    else:
        assert out.suffix == ".dot" and text.startswith("digraph")
