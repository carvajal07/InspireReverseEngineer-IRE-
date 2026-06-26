"""Enumeraciones del modelo interno."""

from __future__ import annotations

from enum import Enum


class ModuleCategory(str, Enum):
    """Categoría funcional de un módulo del workflow."""

    INPUT = "input"
    TRANSFORM = "transform"
    CONTROL = "control"
    INTEGRATION = "integration"
    SCRIPT = "script"
    OUTPUT = "output"
    OTHER = "other"


class ModuleKind(str, Enum):
    """Tipos de módulo soportados de Quadient Inspire."""

    # Entradas
    DATA_INPUT = "DataInput"
    PARAM_INPUT = "ParamInput"
    SCRIPT_DATA_INPUT = "ScriptDataInput"

    # Transformación
    DATA_TRANSFORMER = "DataTransformer"
    DATA_REMAPPER = "DataRemapper"
    RENAMER = "Renamer"
    DATA_CONCATENATOR = "DataConcatenator"

    # Control
    DATA_FILTER = "DataFilter"

    # Integración
    CUST_CODE = "CustCode"
    DATA_MERGER = "DataMerger"
    DATA_SORTER = "DataSorter"
    DATA_GROUP_BY = "DataGroupBy"
    DATA_UNGROUP = "DataUnGroup"
    DATA_ADD = "DataAdd"
    DATA_CACHER = "DataCacher"
    DATA_REPEATER = "DataRepeater"

    # Scripts
    SCRIPTED_SHEETER = "ScriptedSheeter"

    # Salidas
    DATA_OUTPUT = "DataOutput"
    ADV_DATA_OUTPUT = "AdvDataOutput"

    # Otros
    WORD_TABULATOR = "WordTabulatorGroupSepar"
    TNG_NATIVE = "TNGNative"
    STATISTIC_DATA = "StatisticData"

    UNKNOWN = "Unknown"


#: Mapeo de tag XML -> categoría funcional.
KIND_TO_CATEGORY: dict[str, ModuleCategory] = {
    ModuleKind.DATA_INPUT.value: ModuleCategory.INPUT,
    ModuleKind.PARAM_INPUT.value: ModuleCategory.INPUT,
    ModuleKind.SCRIPT_DATA_INPUT.value: ModuleCategory.INPUT,
    ModuleKind.DATA_TRANSFORMER.value: ModuleCategory.TRANSFORM,
    ModuleKind.DATA_REMAPPER.value: ModuleCategory.TRANSFORM,
    ModuleKind.RENAMER.value: ModuleCategory.TRANSFORM,
    ModuleKind.DATA_CONCATENATOR.value: ModuleCategory.TRANSFORM,
    ModuleKind.DATA_FILTER.value: ModuleCategory.CONTROL,
    ModuleKind.CUST_CODE.value: ModuleCategory.INTEGRATION,
    ModuleKind.DATA_MERGER.value: ModuleCategory.INTEGRATION,
    ModuleKind.DATA_SORTER.value: ModuleCategory.INTEGRATION,
    ModuleKind.DATA_GROUP_BY.value: ModuleCategory.INTEGRATION,
    ModuleKind.DATA_UNGROUP.value: ModuleCategory.INTEGRATION,
    ModuleKind.DATA_ADD.value: ModuleCategory.INTEGRATION,
    ModuleKind.DATA_CACHER.value: ModuleCategory.INTEGRATION,
    ModuleKind.DATA_REPEATER.value: ModuleCategory.INTEGRATION,
    ModuleKind.SCRIPTED_SHEETER.value: ModuleCategory.SCRIPT,
    ModuleKind.DATA_OUTPUT.value: ModuleCategory.OUTPUT,
    ModuleKind.ADV_DATA_OUTPUT.value: ModuleCategory.OUTPUT,
    ModuleKind.WORD_TABULATOR.value: ModuleCategory.OTHER,
    ModuleKind.TNG_NATIVE.value: ModuleCategory.OTHER,
    ModuleKind.STATISTIC_DATA.value: ModuleCategory.OTHER,
}

#: Tags que pertenecen al diseñador (no son módulos de negocio).
DESIGNER_TAGS: frozenset[str] = frozenset(
    {
        "Property",
        "SecurityDescriptorManager",
        "SecurityDescriptorWorkFlow",
        "SecurityDescriptor",
        "Label",
        "FieldReordering",
    }
)


def category_for(kind: str) -> ModuleCategory:
    """Devuelve la categoría funcional para un tag de módulo dado."""

    return KIND_TO_CATEGORY.get(kind, ModuleCategory.OTHER)
