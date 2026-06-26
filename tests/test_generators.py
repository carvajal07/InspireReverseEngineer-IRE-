"""Pruebas de los generadores de artefactos."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET

import pytest

from inspire.generators import (
    CleanXmlGenerator,
    ExcelGenerator,
    GraphMLGenerator,
    HtmlGenerator,
    JsonGenerator,
    MarkdownGenerator,
    MermaidGenerator,
    PdfGenerator,
)


def test_json_is_valid_and_complete(workflow):
    data = json.loads(JsonGenerator().render(workflow))
    assert data["version"] == "12.0.0.0"
    assert len(data["modules"]) == 8
    assert "statistics" in data
    calc = next(m for m in data["modules"] if m["name"] == "Calcula")
    assert len(calc["transformations"]) == 2


def test_markdown_has_sections(workflow):
    md = MarkdownGenerator().render(workflow)
    assert "## Estadísticas" in md
    assert "## Variables" in md
    assert "```mermaid" in md
    assert "Calcula" in md


def test_mermaid_flowchart(workflow):
    mmd = MermaidGenerator().render(workflow)
    assert mmd.startswith("flowchart LR")
    assert "-->" in mmd
    assert "DataInput1" in mmd


def test_graphml_is_valid_xml(workflow):
    xml = GraphMLGenerator().render(workflow)
    root = ET.fromstring(xml)
    assert root.tag.endswith("graphml")
    nodes = root.findall(".//{http://graphml.graphdrawing.org/xmlns}node")
    assert len(nodes) == 8


def test_clean_xml_strips_designer(workflow):
    xml = CleanXmlGenerator().render(workflow)
    root = ET.fromstring(xml)
    assert root.tag == "Workflow"
    assert root.find("Modules") is not None
    # No debe contener propiedades del diseñador.
    assert "AFPApplyMediumOrientation" not in xml


def test_excel_writes_files(workflow, tmp_path):
    gen = ExcelGenerator()
    result = gen.write(workflow, tmp_path / "out.xlsx")
    if gen.uses_excel:
        assert result.exists()
    else:
        # En modo CSV se generan varios archivos.
        assert list(tmp_path.glob("out_*.csv"))


def test_html_is_self_contained(workflow):
    html = HtmlGenerator().render(workflow)
    assert html.startswith("<!DOCTYPE html>")
    # Datos embebidos (sin servidor) y app de búsqueda.
    assert 'id="ire-data"' in html
    assert "Calcula" in html
    # No debe requerir recursos locales externos.
    assert 'src="http' not in html or "mermaid" in html


def test_html_embeds_valid_json(workflow):
    import json
    import re

    html = HtmlGenerator().render(workflow)
    match = re.search(
        r'<script type="application/json" id="ire-data">(.*?)</script>',
        html,
        re.S,
    )
    assert match is not None
    payload = json.loads(match.group(1).replace("<\\/", "</"))
    assert len(payload["modules"]) == len(workflow.modules)
    assert "rules" in payload and "variable_report" in payload


def test_pdf_generation(workflow, tmp_path):
    gen = PdfGenerator()
    if not gen.available:
        pytest.skip("reportlab no instalado")
    out = gen.write(workflow, tmp_path / "wf.pdf")
    assert out.exists()
    assert out.read_bytes().startswith(b"%PDF-")


def test_all_generators_write(workflow, tmp_path):
    for gen, name in [
        (JsonGenerator(), "wf.json"),
        (MarkdownGenerator(), "wf.md"),
        (MermaidGenerator(), "wf.mmd"),
        (GraphMLGenerator(), "wf.graphml"),
        (CleanXmlGenerator(), "wf.xml"),
    ]:
        out = gen.write(workflow, tmp_path / name)
        assert out.exists()
        assert out.stat().st_size > 0
