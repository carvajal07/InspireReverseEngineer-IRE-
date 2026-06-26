"""Pruebas del loader y el parser."""

from __future__ import annotations

import pytest

from inspire.model.enums import ModuleCategory
from inspire.parser import WorkflowParser
from inspire.parser.loader import XmlLoader, XmlLoadError


def test_loader_rejects_non_workflow():
    with pytest.raises(XmlLoadError):
        XmlLoader().loads("<NotWorkFlow/>")


def test_loader_strips_designer_nodes():
    root = XmlLoader(strip_designer=True).loads(
        "<WorkFlow><Property><Name>x</Name></Property>"
        "<DataFilter><Id>a</Id><Name>a</Name></DataFilter></WorkFlow>"
    )
    tags = [c.tag for c in root]
    assert "Property" not in tags
    assert "DataFilter" in tags


def test_parser_ignores_designer_tags(workflow):
    kinds = {m.kind for m in workflow.modules}
    assert "Property" not in kinds
    assert "Label" not in kinds


def test_parser_collects_modules(workflow):
    names = {m.name for m in workflow.modules}
    assert {"Parametros", "BasePortal", "Calcula", "Cruce"} <= names
    assert len(workflow.modules) == 8


def test_parser_categories(workflow):
    by_name = {m.name: m for m in workflow.modules}
    assert by_name["BasePortal"].category is ModuleCategory.INPUT
    assert by_name["Calcula"].category is ModuleCategory.TRANSFORM
    assert by_name["FiltraVariables"].category is ModuleCategory.CONTROL
    assert by_name["Cruce"].category is ModuleCategory.INTEGRATION
    assert by_name["Hoja"].category is ModuleCategory.SCRIPT
    assert by_name["Salida"].category is ModuleCategory.OUTPUT


def test_parser_connections(workflow):
    assert len(workflow.connections) == 4
    first = workflow.connections[0]
    assert first.from_id == "DataInput1"
    assert first.to_id == "DataTransformer1"


def test_parse_file_sets_metadata(sample_xml_path):
    wf = WorkflowParser().parse_file(sample_xml_path)
    assert wf.version == "12.0.0.0"
    assert wf.name == "sample"
    assert wf.source_file.endswith("sample.xml")
