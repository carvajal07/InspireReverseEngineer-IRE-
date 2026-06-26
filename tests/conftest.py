"""Fixtures compartidos para las pruebas de IRE."""

from __future__ import annotations

import pytest

#: Workflow sintético mínimo que ejercita los principales tipos de módulo.
SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<WorkFlow version="12.0.0.0">
  <Property><Name>Guid</Name><Value>ABC</Value></Property>
  <Label><Text>solo diseñador</Text></Label>

  <ParamInput>
    <Id>ParamInput1</Id>
    <Name>Parametros</Name>
    <ModulePos X="10" Y="20" />
    <Param FieldName="Cliente" ParamLabel="Cliente" ParamType="String"
           CommandLine="Cliente" Default="ITAU">
      <StructName>Params</StructName>
    </Param>
  </ParamInput>

  <DataInput>
    <Id>DataInput1</Id>
    <Name>BasePortal</Name>
    <ModulePos X="30" Y="40" />
    <WorkFlowDefinition>
      <Node Name="" Type="SubTree" Optionality="MustExist">
        <Node Name="Records" Type="SubTree" Optionality="Array">
          <Node Name="TipoId" Type="String" Optionality="MustExist" />
          <Node Name="NumId" Type="String" Optionality="MustExist" />
        </Node>
      </Node>
    </WorkFlowDefinition>
    <Location>DiskLocation,//srv/base.txt</Location>
    <Reader>CSVSimpleDataReader</Reader>
    <TextCodec>ISO-8859-1</TextCodec>
  </DataInput>

  <DataTransformer>
    <Id>DataTransformer1</Id>
    <Name>Calcula</Name>
    <ModulePos X="50" Y="60" />
    <WorkFlowDefinition>
      <Node Name="" Type="SubTree" Optionality="MustExist">
        <Node Name="Contador" Type="Int" Optionality="MustExist" />
      </Node>
    </WorkFlowDefinition>
    <Transformations>
      <Transformation DotName="Records.Contador" Propagate="True" NodeType="Int">
        <FCVClassName>ScriptFCV</FCVClassName>
        <FCVProps>
          <InputType>Int</InputType>
          <OutputType>Bool</OutputType>
          <Script>if(Input&gt;0){return true;}else{return false;}</Script>
        </FCVProps>
      </Transformation>
      <Transformation DotName="Records.TipoId" Propagate="True" NodeType="String">
        <FCVClassName>ConcatStrFCV</FCVClassName>
        <FCVProps>
          <InputType>String</InputType>
          <OutputType>String</OutputType>
          <PreString>X-</PreString>
          <PostString />
          <Type>TrimWhiteSpaces</Type>
        </FCVProps>
      </Transformation>
      <Transformation DotName="Records.SinLogica" Propagate="False" NodeType="String" />
    </Transformations>
  </DataTransformer>

  <DataFilter>
    <Id>DataFilter1</Id>
    <Name>FiltraVariables</Name>
    <ModulePos X="70" Y="80" />
    <Conditions>
      <Condition SearchName="Records.TipoId" ValueType="String"
                 InvertCondition="False" ConditionType="Equalto" Value="Variables" />
    </Conditions>
    <HasElseOutput>True</HasElseOutput>
  </DataFilter>

  <CustCode>
    <Id>CustCode1</Id>
    <Name>Cruce</Name>
    <ModulePos X="90" Y="100" />
    <SelectedNodeA>Records.NumId</SelectedNodeA>
    <SelectedNodeB>Base.NumId</SelectedNodeB>
    <SearcherClassName>StringSortAndSearcher</SearcherClassName>
    <IgnoreUnmatched>False</IgnoreUnmatched>
  </CustCode>

  <ScriptedSheeter>
    <Id>ScriptedSheeter1</Id>
    <Name>Hoja</Name>
    <ModulePos X="110" Y="120" />
    <Script>var x = GetString("Records.NumId"); SetString("Out", x); return x;</Script>
  </ScriptedSheeter>

  <Renamer>
    <Id>Renamer1</Id>
    <Name>Renombra</Name>
    <ModulePos X="130" Y="140" />
    <RenameNodes>
      <RenameNode>
        <Path>Records.TipoId</Path>
        <NewName>Tipo</NewName>
      </RenameNode>
    </RenameNodes>
  </Renamer>

  <AdvDataOutput>
    <Id>AdvDataOutput1</Id>
    <Name>Salida</Name>
    <ModulePos X="150" Y="160" />
  </AdvDataOutput>

  <Connect><From>DataInput1</From><FromIndex>0</FromIndex><To>DataTransformer1</To><ToIndex>0</ToIndex></Connect>
  <Connect><From>DataTransformer1</From><FromIndex>0</FromIndex><To>DataFilter1</To><ToIndex>0</ToIndex></Connect>
  <Connect><From>DataFilter1</From><FromIndex>0</FromIndex><To>CustCode1</To><ToIndex>0</ToIndex></Connect>
  <Connect><From>CustCode1</From><FromIndex>0</FromIndex><To>AdvDataOutput1</To><ToIndex>0</ToIndex></Connect>
</WorkFlow>
"""


@pytest.fixture()
def sample_xml_path(tmp_path):
    path = tmp_path / "sample.xml"
    path.write_text(SAMPLE_XML, encoding="utf-8")
    return path


@pytest.fixture()
def workflow(sample_xml_path):
    from inspire.analyzers import analyze
    from inspire.parser import WorkflowParser

    wf = WorkflowParser().parse_file(sample_xml_path)
    analyze(wf)
    return wf
