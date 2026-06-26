"""Registro de extractores por tipo de módulo.

Cada extractor recibe el elemento XML del módulo y el :class:`Module` base
(con id/name/posición/campos ya rellenados) y le añade la lógica funcional
específica de su tipo. El diseño es extensible: registrar un nuevo tipo es
añadir una función decorada con :func:`ExtractorRegistry.register`.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import Callable

from inspire.extractors.fcv import parse_transformation
from inspire.extractors.fields import extract_definition
from inspire.extractors.scripts import build_script
from inspire.model.elements import (
    Filter,
    FilterCondition,
    JoinKey,
    Module,
    Parameter,
)
from inspire.model.enums import ModuleKind, category_for

Extractor = Callable[[ET.Element, Module], None]


class ExtractorRegistry:
    """Mapa de ``tag XML -> función extractora``."""

    _registry: dict[str, Extractor] = {}

    @classmethod
    def register(cls, *kinds: str) -> Callable[[Extractor], Extractor]:
        def decorator(func: Extractor) -> Extractor:
            for kind in kinds:
                cls._registry[kind] = func
            return func

        return decorator

    @classmethod
    def get(cls, kind: str) -> Extractor | None:
        return cls._registry.get(kind)


def _pos(element: ET.Element) -> tuple[int, int]:
    pos = element.find("ModulePos")
    if pos is None:
        return (0, 0)
    try:
        return (int(pos.get("X", "0")), int(pos.get("Y", "0")))
    except ValueError:
        return (0, 0)


def build_module(element: ET.Element) -> Module:
    """Construye un :class:`Module` completo a partir de su elemento XML."""

    kind = element.tag
    module = Module(
        id=element.findtext("Id", element.findtext("Name", kind)) or kind,
        name=element.findtext("Name", element.findtext("Id", kind)) or kind,
        kind=kind,
        category=category_for(kind),
        position=_pos(element),
        fields=extract_definition(element),
    )
    extractor = ExtractorRegistry.get(kind)
    if extractor is not None:
        extractor(element, module)
    return module


# --------------------------------------------------------------------------
# Extractores específicos
# --------------------------------------------------------------------------


@ExtractorRegistry.register(ModuleKind.DATA_TRANSFORMER.value)
def _extract_transformer(element: ET.Element, module: Module) -> None:
    container = element.find("Transformations")
    if container is None:
        return
    for raw in container.findall("Transformation"):
        transformation = parse_transformation(raw)
        # Solo conservamos las que tienen lógica funcional real.
        if transformation.has_logic:
            module.transformations.append(transformation)


@ExtractorRegistry.register(ModuleKind.DATA_FILTER.value)
def _extract_filter(element: ET.Element, module: Module) -> None:
    flt = Filter(has_else_output=element.findtext("HasElseOutput", "False") == "True")
    container = element.find("Conditions")
    if container is not None:
        for cond in container.findall("Condition"):
            flt.conditions.append(
                FilterCondition(
                    search_name=cond.get("SearchName", ""),
                    operator=cond.get("ConditionType", "Equalto"),
                    value=cond.get("Value", ""),
                    value_type=cond.get("ValueType", "String"),
                    invert=cond.get("InvertCondition", "False") == "True",
                )
            )
    module.filter = flt


def _extract_searcher_join(element: ET.Element, module: Module) -> None:
    module.join_type = element.findtext("SearcherClassName", "")
    left = element.findtext("SelectedNodeA", "") or ""
    right = element.findtext("SelectedNodeB", "") or ""
    if left.strip() or right.strip():
        module.join_keys.append(JoinKey(left=left.strip(), right=right.strip()))
    ignore = element.findtext("IgnoreUnmatched", "")
    if ignore:
        module.extra["IgnoreUnmatched"] = ignore


ExtractorRegistry.register(ModuleKind.CUST_CODE.value)(_extract_searcher_join)
ExtractorRegistry.register(ModuleKind.DATA_MERGER.value)(_extract_searcher_join)


@ExtractorRegistry.register(ModuleKind.PARAM_INPUT.value)
def _extract_params(element: ET.Element, module: Module) -> None:
    for param in element.findall("Param"):
        module.parameters.append(
            Parameter(
                name=param.get("FieldName", ""),
                label=param.get("ParamLabel", ""),
                type=param.get("ParamType", "String"),
                default=param.get("Default", ""),
                command_line=param.get("CommandLine", ""),
                struct=param.findtext("StructName", ""),
            )
        )


@ExtractorRegistry.register(ModuleKind.DATA_INPUT.value)
def _extract_data_input(element: ET.Element, module: Module) -> None:
    module.location = element.findtext("Location", "")
    module.reader = element.findtext("Reader", "")
    codec = element.findtext("TextCodec", "")
    if codec:
        module.extra["TextCodec"] = codec


@ExtractorRegistry.register(ModuleKind.SCRIPT_DATA_INPUT.value)
def _extract_script_input(element: ET.Element, module: Module) -> None:
    module.location = element.findtext("Location", "")
    code = element.findtext("Script", "")
    if code:
        module.scripts.append(build_script(code))


@ExtractorRegistry.register(ModuleKind.SCRIPTED_SHEETER.value)
def _extract_scripted_sheeter(element: ET.Element, module: Module) -> None:
    code = element.findtext("Script", "")
    if code:
        module.scripts.append(build_script(code))


@ExtractorRegistry.register(ModuleKind.RENAMER.value)
def _extract_renamer(element: ET.Element, module: Module) -> None:
    container = element.find("RenameNodes")
    if container is None:
        return
    for node in container.findall("RenameNode"):
        old = node.findtext("Path", "")
        new = node.findtext("NewName", "")
        if old or new:
            module.renames.append((old, new))


@ExtractorRegistry.register(ModuleKind.DATA_GROUP_BY.value)
def _extract_group_by(element: ET.Element, module: Module) -> None:
    for tag in ("FieldName", "GroupName", "FieldsName"):
        value = element.findtext(tag, "")
        if value:
            module.extra[tag] = value
    field = element.findtext("FieldName", "")
    if field:
        module.group_by.append(field)


@ExtractorRegistry.register(
    ModuleKind.DATA_OUTPUT.value, ModuleKind.ADV_DATA_OUTPUT.value
)
def _extract_output(element: ET.Element, module: Module) -> None:
    location = element.findtext("Location", "")
    if location:
        module.location = location
