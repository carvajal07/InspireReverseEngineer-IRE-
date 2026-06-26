"""Extracción de la estructura de datos (WorkFlowDefinition -> DataField)."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import Iterator

from inspire.model.elements import DataField


def parse_nodes(parent: ET.Element | None, prefix: str = "") -> list[DataField]:
    """Convierte recursivamente los ``<Node>`` en una lista de :class:`DataField`."""

    if parent is None:
        return []

    fields: list[DataField] = []
    for node in parent.findall("Node"):
        name = node.get("Name", "")
        if not name:
            # Nodo raíz anónimo: aplanar sus hijos en el mismo nivel.
            fields.extend(parse_nodes(node, prefix))
            continue
        path = f"{prefix}.{name}" if prefix else name
        field = DataField(
            name=name,
            type=node.get("Type", ""),
            optionality=node.get("Optionality", "MustExist"),
            path=path,
            children=parse_nodes(node, path),
        )
        fields.append(field)
    return fields


def iter_fields(fields: list[DataField]) -> Iterator[DataField]:
    """Recorre en profundidad todos los campos (incluyendo anidados)."""

    for field in fields:
        yield field
        yield from iter_fields(field.children)


def extract_definition(element: ET.Element) -> list[DataField]:
    """Extrae la estructura de ``<WorkFlowDefinition>`` de un módulo."""

    return parse_nodes(element.find("WorkFlowDefinition"))
