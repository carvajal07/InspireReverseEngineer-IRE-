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


def test_mermaid_escapes_special_chars():
    from inspire.model.elements import Module
    from inspire.model.enums import ModuleCategory
    from inspire.model.workflow import Workflow

    wf = Workflow(name="t")
    wf.modules = [
        Module(
            id="DT1",
            name="AsignaEmail&Politicas",
            kind="DataTransformer",
            category=ModuleCategory.TRANSFORM,
        )
    ]
    mmd = MermaidGenerator().render(wf)
    # El '&' debe ir escapado como entidad para no romper Mermaid.
    assert "AsignaEmail&amp;Politicas" in mmd
    assert "AsignaEmail&Politicas" not in mmd
    # Ya no usamos <small> (lo sanitiza Mermaid en modo estricto).
    assert "<small>" not in mmd


def test_html_raises_mermaid_edge_limit(workflow):
    # El portal debe elevar maxEdges para workflows con >500 conexiones.
    html = HtmlGenerator().render(workflow)
    assert "maxEdges" in html


def test_html_has_design_column_and_lineage(workflow):
    html = HtmlGenerator().render(workflow)
    # Columna de diseño y modal/funciones de linaje de variable.
    assert "Diseño" in html
    assert "used_in_layout" in html
    assert "buildLineageMermaid" in html
    assert "lineageOverlay" in html


def test_html_variable_state_filters(workflow):
    html = HtmlGenerator().render(workflow)
    # Filtros de estado en la barra de Variables.
    assert 'id="filterUnused"' in html
    assert 'id="filterCritical"' in html
    assert 'id="filterOrphan"' in html
    # La celda de diseño incluye el número de hojas.
    assert "Sí · " in html
    # Tooltip explicativo de "crítica".
    assert "alto impacto" in html


def test_html_lineage_relevant_only_and_panzoom(workflow):
    html = HtmlGenerator().render(workflow)
    # El linaje ya no dibuja nodos de tránsito.
    assert "transito" not in html
    assert "Tránsito" not in html
    # Visor con zoom + paneo para grafos grandes.
    assert "mountPanZoom" in html
    assert "graphview" in html
    assert "rueda para zoom" in html
    # Modo enfoque (vecindario de un módulo) para flujos grandes.
    assert "buildFlowSubgraph" in html
    assert "focusModule" in html
    # Integración del diagrama SVG: helper para montar con nodos clicables.
    assert "mountSvgInto" in html
    assert "flow_svg" in html


def test_html_uses_python_layout_when_graphviz_missing(workflow, monkeypatch):
    # Simula que el binario 'dot' no está disponible (caso sin permisos admin).
    import inspire.generators.graphviz_gen as gv

    monkeypatch.setattr(gv.shutil, "which", lambda name: None)
    html = HtmlGenerator().render(workflow)
    assert "Layout jerárquico (Python)" in html
    # El diagrama sigue incrustado como SVG (no depende de Mermaid).
    assert '"flow_svg"' in html or "flow_svg" in html
    # Columna de diseño: "Sí" abre un cuadro con las hojas.
    assert "openPages" in html
    assert "pagesOverlay" in html
    # El badge de estadísticas usa "Cruces" (no "Joins").
    assert "'Cruces'" in html
    assert "'Joins'" not in html


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
