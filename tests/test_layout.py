"""Pruebas del análisis del diseño (módulo Layout) y su integración."""

from __future__ import annotations

import pytest

from inspire.analyzers import analyze
from inspire.analyzers.layout import LayoutAnalyzer
from inspire.parser import WorkflowParser

# Layout sintético: ejercita cadena ParentId con nodo "Value", tabla
# (RowSet/SubRow), código de barras (VariableId) y condición.
LAYOUT_XML = """<Layout>
  <Id>1000</Id>
  <Name>Extracto</Name>
  <Layout>
    <Variable><Id>10</Id><Name>NumCrediRotativo</Name><ParentId>11</ParentId><IndexInParent>0</IndexInParent></Variable>
    <SubTree><Id>11</Id><Name>Records</Name><ParentId>12</ParentId><IndexInParent>0</IndexInParent></SubTree>
    <SubTree><Id>12</Id><Name>Sodim_Ord</Name><ParentId>Def.Data</ParentId><IndexInParent>0</IndexInParent></SubTree>
    <Variable><Id>20</Id><Name>NombreCliente</Name><ParentId>21</ParentId><IndexInParent>1</IndexInParent></Variable>
    <SubTree><Id>21</Id><Name>Value</Name><ParentId>11</ParentId><IndexInParent>1</IndexInParent></SubTree>
    <Variable><Id>30</Id><Name>Saldo</Name><ParentId>11</ParentId><IndexInParent>2</IndexInParent></Variable>
    <Variable><Id>40</Id><Name>CodigoBarras</Name><ParentId>11</ParentId><IndexInParent>3</IndexInParent></Variable>
    <Page><Id>100</Id><Name>Hoja1</Name><ParentId>1</ParentId><IndexInParent>0</IndexInParent></Page>
    <FlowArea><Id>110</Id><Name>FA1</Name><ParentId>100</ParentId><IndexInParent>0</IndexInParent></FlowArea>
    <FlowArea><Id>110</Id><FlowId>200</FlowId></FlowArea>
    <Flow><Id>200</Id><FlowContent><O Id="10"/><O Id="300"/><Barcode><VariableId>40</VariableId></Barcode><InlCond><Condition Value="if(DATA.Sodim_Ord.Current.Records.Saldo>0)">410</Condition><Default>200</Default></InlCond></FlowContent></Flow>
    <Table><Id>300</Id><RowSetId>310</RowSetId></Table>
    <RowSet><Id>310</Id><SubRowId>320</SubRowId></RowSet>
    <Row><Id>320</Id><O Id="20"/></Row>
    <Flow><Id>410</Id><FlowContent><O Id="30"/></FlowContent></Flow>
  </Layout>
</Layout>
"""

# WorkFlow que embebe el Layout y declara variables de datos que coinciden.
WF_WITH_LAYOUT = """<?xml version="1.0" encoding="UTF-8"?>
<WorkFlow version="12.0.0.0">
  <DataInput>
    <Id>DataInput1</Id><Name>BasePortal</Name>
    <WorkFlowDefinition><Node Name="" Type="SubTree">
      <Node Name="Records" Type="SubTree" Optionality="Array">
        <Node Name="NumCrediRotativo" Type="String"/>
        <Node Name="Saldo" Type="String"/>
        <Node Name="NoEnDiseno" Type="String"/>
      </Node></Node></WorkFlowDefinition>
  </DataInput>
  <DataTransformer>
    <Id>DataTransformer1</Id><Name>Calcula</Name>
    <CreatedNodes><CreatedNode FieldDotName="Records.Saldo"/></CreatedNodes>
    <Transformations>
      <Transformation DotName="Records.Saldo" NodeType="String">
        <FCVClassName>ScriptFCV</FCVClassName>
        <FCVProps><Script>return Input;</Script></FCVProps>
      </Transformation>
    </Transformations>
  </DataTransformer>
  __LAYOUT__
  <Connect><From>DataInput1</From><To>DataTransformer1</To></Connect>
</WorkFlow>
""".replace("__LAYOUT__", LAYOUT_XML)


@pytest.fixture()
def layout_file(tmp_path):
    path = tmp_path / "layout.xml"
    path.write_text(LAYOUT_XML, encoding="utf-8")
    return path


@pytest.fixture()
def wf_layout_path(tmp_path):
    path = tmp_path / "wf.xml"
    path.write_text(WF_WITH_LAYOUT, encoding="utf-8")
    return path


# --------------------------------------------------------------------------
# Analizador de Layout (algoritmo)
# --------------------------------------------------------------------------


def test_layout_finds_all_variables(layout_file):
    report = LayoutAnalyzer().analyze_file(layout_file)
    assert report.found_layout
    assert report.modules == ["Extracto"]
    assert ("Extracto", "Hoja1") in report.pages
    paths = report.paths_used()
    assert "Sodim_Ord.Records.NumCrediRotativo" in paths  # vía <O>
    assert "Sodim_Ord.Records.NombreCliente" in paths  # tabla, "Value" omitido
    assert "Sodim_Ord.Records.CodigoBarras" in paths  # VariableId (barcode)
    assert "Sodim_Ord.Records.Saldo" in paths  # condición / flujo


def test_layout_origin_classification(layout_file):
    report = LayoutAnalyzer().analyze_file(layout_file)
    origins = {u.path: u.origin for u in report.usages}
    assert origins["Sodim_Ord.Records.NumCrediRotativo"] == "DATA"


def test_layout_value_node_dropped(layout_file):
    report = LayoutAnalyzer().analyze_file(layout_file)
    # El nodo contenedor "Value" no debe aparecer en ninguna ruta.
    assert all(".Value." not in p and not p.endswith(".Value") for p in report.paths_used())


def test_layout_leaves(layout_file):
    leaves = LayoutAnalyzer().analyze_file(layout_file).leaves_used()
    assert {"NumCrediRotativo", "NombreCliente", "Saldo", "CodigoBarras"} <= leaves


# --------------------------------------------------------------------------
# Integración con el flujo
# --------------------------------------------------------------------------


def test_workflow_marks_design_variables(wf_layout_path):
    wf = WorkflowParser().parse_file(wf_layout_path)
    analyze(wf)
    index = {v.name: v for v in wf.variables}
    assert index["NumCrediRotativo"].used_in_layout is True
    assert index["Saldo"].used_in_layout is True
    assert index["NoEnDiseno"].used_in_layout is False
    assert "Extracto / Hoja1" in index["Saldo"].layout_pages
    assert "Sodim_Ord.Records.Saldo" in index["Saldo"].layout_paths


def test_workflow_layout_statistics(wf_layout_path):
    wf = WorkflowParser().parse_file(wf_layout_path)
    analyze(wf)
    assert wf.statistics.variables_in_layout == 2
    assert wf.statistics.layout_pages == 1


def test_separate_layout_file(tmp_path):
    # XML principal sin Layout + archivo de layout aparte.
    main = tmp_path / "main.xml"
    main.write_text(
        WF_WITH_LAYOUT.replace(LAYOUT_XML, ""), encoding="utf-8"
    )
    layout = tmp_path / "layout.xml"
    layout.write_text(LAYOUT_XML, encoding="utf-8")
    wf = WorkflowParser().parse_file(main, layout_path=layout)
    index = {v.name: v for v in wf.variables}
    assert index["NumCrediRotativo"].used_in_layout is True


def test_workflow_without_layout(sample_xml_path):
    wf = WorkflowParser().parse_file(sample_xml_path)
    assert wf.layout is not None
    assert wf.layout.found_layout is False
    assert all(not v.used_in_layout for v in wf.variables)
