"""Parseo de FCV (Field Computed Value) de Inspire a :class:`Transformation`.

Un FCV es la unidad de lógica de una transformación. Inspire soporta varios:

* ``ScriptFCV``    -> código (JavaScript-like) que calcula el valor.
* ``ConcatStrFCV`` -> concatenación / trim de cadenas.
* ``StackFCV``     -> pila ordenada de varios FCV encadenados.
* ``BT2BTFCV``     -> conversión de tipo (base type a base type).
* ``ConvNumFCV``   -> formateo / conversión numérica.
* ``IntIncrFCV``   -> contador incremental.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from inspire.model.elements import Transformation

#: Clasificación lógica de cada FCV.
_KIND_BY_FCV = {
    "ScriptFCV": "script",
    "ConcatStrFCV": "concat",
    "StackFCV": "stack",
    "BT2BTFCV": "convert",
    "ConvNumFCV": "format_number",
    "IntIncrFCV": "counter",
}


def _text(element: ET.Element | None, tag: str, default: str = "") -> str:
    if element is None:
        return default
    found = element.find(tag)
    if found is None or found.text is None:
        return default
    return found.text


def _summary(fcv_type: str, props: ET.Element | None, script: str) -> str:
    """Genera un resumen humano de la operación del FCV."""

    if fcv_type == "ScriptFCV":
        first = script.strip().splitlines()[0] if script.strip() else ""
        return f"script: {first}" if first else "script"
    if fcv_type == "ConcatStrFCV":
        pre = _text(props, "PreString")
        post = _text(props, "PostString")
        ctype = _text(props, "Type")
        parts = []
        if pre:
            parts.append(f"pre='{pre}'")
        if post:
            parts.append(f"post='{post}'")
        if ctype:
            parts.append(ctype)
        return "concat(" + ", ".join(parts) + ")"
    if fcv_type == "BT2BTFCV":
        return f"convert {_text(props, 'InputType')} -> {_text(props, 'OutputType')}"
    if fcv_type == "ConvNumFCV":
        dec = _text(props, "OutDigitsAfterDecimal")
        sep = _text(props, "OutDecimalSeparator")
        return f"format_number(decimals={dec}, sep='{sep}')"
    if fcv_type == "IntIncrFCV":
        return "counter++"
    return fcv_type


def _parse_stack(props: ET.Element) -> list[Transformation]:
    """Parsea un StackFCV cuyos hijos alternan FCVClassName / FCVProps."""

    stack: list[Transformation] = []
    children = list(props)
    i = 0
    while i < len(children):
        child = children[i]
        if child.tag == "FCVClassName" and child.text:
            inner_props = children[i + 1] if i + 1 < len(children) else None
            if inner_props is not None and inner_props.tag == "FCVProps":
                stack.append(_build_from(child.text, inner_props))
                i += 2
                continue
        i += 1
    return stack


def _build_from(fcv_type: str, props: ET.Element | None) -> Transformation:
    script = _text(props, "Script")
    transformation = Transformation(
        dot_name="",
        fcv_type=fcv_type,
        kind=_KIND_BY_FCV.get(fcv_type, "other"),
        input_type=_text(props, "InputType"),
        output_type=_text(props, "OutputType"),
        script=script,
        expression=_summary(fcv_type, props, script),
    )
    if fcv_type == "StackFCV" and props is not None:
        transformation.stack = _parse_stack(props)
        transformation.expression = " | ".join(
            t.expression for t in transformation.stack
        )
    # Conservar props escalares útiles.
    if props is not None:
        for prop in props:
            if prop.tag in ("FCVClassName", "FCVProps", "Script"):
                continue
            if prop.text and prop.text.strip():
                transformation.props[prop.tag] = prop.text.strip()
    return transformation


def parse_transformation(element: ET.Element) -> Transformation:
    """Convierte un elemento ``<Transformation>`` en el modelo interno."""

    fcv_type = _text(element, "FCVClassName")
    props = element.find("FCVProps")
    transformation = _build_from(fcv_type, props) if fcv_type else Transformation(dot_name="")
    transformation.dot_name = element.get("DotName", "")
    transformation.node_type = element.get("NodeType", "")
    transformation.propagate = element.get("Propagate", "False") == "True"
    return transformation
