"""Pruebas unitarias del parseo de FCV (todos los tipos soportados)."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from inspire.extractors.fcv import parse_transformation


def _parse(xml: str):
    return parse_transformation(ET.fromstring(xml))


def test_int_incr_counter():
    t = _parse(
        '<Transformation DotName="R.C" NodeType="Int">'
        "<FCVClassName>IntIncrFCV</FCVClassName>"
        "<FCVProps><InputType>Int</InputType><OutputType>Int</OutputType></FCVProps>"
        "</Transformation>"
    )
    assert t.kind == "counter"
    assert t.expression == "counter++"


def test_bt2bt_convert():
    t = _parse(
        '<Transformation DotName="R.N" NodeType="String">'
        "<FCVClassName>BT2BTFCV</FCVClassName>"
        "<FCVProps><InputType>String</InputType><OutputType>Int</OutputType>"
        "<EmptyResult>0</EmptyResult></FCVProps></Transformation>"
    )
    assert t.kind == "convert"
    assert "String -> Int" in t.expression
    assert t.props.get("EmptyResult") == "0"


def test_convnum_format():
    t = _parse(
        '<Transformation DotName="P.M" NodeType="Double">'
        "<FCVClassName>ConvNumFCV</FCVClassName>"
        "<FCVProps><InputType>Double</InputType><OutputType>String</OutputType>"
        "<OutDigitsAfterDecimal>2</OutDigitsAfterDecimal>"
        "<OutDecimalSeparator>,</OutDecimalSeparator></FCVProps></Transformation>"
    )
    assert t.kind == "format_number"
    assert "decimals=2" in t.expression
    assert "sep=','" in t.expression


def test_stack_fcv_chains_operations():
    xml = (
        '<Transformation DotName="R.S" NodeType="String">'
        "<FCVClassName>StackFCV</FCVClassName>"
        "<FCVProps>"
        "<InputType>String</InputType><OutputType>String</OutputType>"
        "<FCVClassName>ConcatStrFCV</FCVClassName>"
        "<FCVProps><InputType>String</InputType><OutputType>String</OutputType>"
        "<PreString>A-</PreString><PostString /><Type>TrimWhiteSpaces</Type></FCVProps>"
        "<FCVClassName>ScriptFCV</FCVClassName>"
        "<FCVProps><InputType>String</InputType><OutputType>String</OutputType>"
        "<Script>return Input;</Script></FCVProps>"
        "</FCVProps></Transformation>"
    )
    t = _parse(xml)
    assert t.kind == "stack"
    assert len(t.stack) == 2
    assert t.stack[0].fcv_type == "ConcatStrFCV"
    assert t.stack[1].fcv_type == "ScriptFCV"
    assert "|" in t.expression


def test_transformation_without_logic():
    t = _parse('<Transformation DotName="R.X" NodeType="String" />')
    assert not t.has_logic
    assert t.dot_name == "R.X"
