"""Elementos del modelo interno: módulos, variables, reglas, etc."""

from __future__ import annotations

from dataclasses import dataclass, field

from inspire.model.enums import ModuleCategory


@dataclass(slots=True)
class DataField:
    """Un campo (Node) de la definición de datos de un módulo."""

    name: str
    type: str
    optionality: str = "MustExist"
    path: str = ""
    children: list["DataField"] = field(default_factory=list)

    @property
    def is_array(self) -> bool:
        return self.optionality == "Array"

    @property
    def is_subtree(self) -> bool:
        return self.type == "SubTree"


@dataclass(slots=True)
class Transformation:
    """Una transformación funcional aplicada a un campo.

    Representa la lógica de un FCV (Field Computed Value) de Inspire:
    scripts, concatenaciones, conversiones numéricas, incrementos, etc.
    """

    dot_name: str
    node_type: str = ""
    propagate: bool = False
    fcv_type: str = ""
    #: Lenguaje/tipo lógico inferido (script, concat, convert, ...).
    kind: str = ""
    input_type: str = ""
    output_type: str = ""
    #: Código del script cuando ``fcv_type == 'ScriptFCV'``.
    script: str = ""
    #: Resumen legible de la operación.
    expression: str = ""
    #: Pila de operaciones cuando es un ``StackFCV``.
    stack: list["Transformation"] = field(default_factory=list)
    #: Propiedades adicionales del FCV.
    props: dict[str, str] = field(default_factory=dict)

    @property
    def has_logic(self) -> bool:
        """True si la transformación contiene lógica real (no solo declarativa)."""

        return bool(self.fcv_type)


@dataclass(slots=True)
class FilterCondition:
    """Una condición individual dentro de un filtro."""

    search_name: str
    operator: str
    value: str = ""
    value_type: str = "String"
    invert: bool = False

    def as_expression(self) -> str:
        op = self.operator
        neg = "NOT " if self.invert else ""
        return f"{neg}{self.search_name} {op} '{self.value}'"


@dataclass(slots=True)
class Filter:
    """Lógica de un módulo de filtrado (DataFilter)."""

    conditions: list[FilterCondition] = field(default_factory=list)
    has_else_output: bool = False

    def as_expression(self) -> str:
        return " AND ".join(c.as_expression() for c in self.conditions)


@dataclass(slots=True)
class JoinKey:
    """Llave usada en un cruce (Join/Merge)."""

    left: str = ""
    right: str = ""


@dataclass(slots=True)
class Parameter:
    """Un parámetro de entrada del workflow (ParamInput)."""

    name: str
    label: str = ""
    type: str = "String"
    default: str = ""
    command_line: str = ""
    struct: str = ""


@dataclass(slots=True)
class Script:
    """Un bloque de código fuente embebido en un módulo."""

    language: str
    code: str
    #: Variables leídas dentro del código.
    reads: list[str] = field(default_factory=list)
    #: Variables escritas dentro del código.
    writes: list[str] = field(default_factory=list)

    @property
    def line_count(self) -> int:
        return self.code.count("\n") + 1 if self.code else 0


@dataclass(slots=True)
class Variable:
    """Una variable de negocio detectada en el workflow."""

    name: str
    type: str = ""
    initial_value: str = ""
    #: Módulos donde la variable se crea/declara.
    created_in: set[str] = field(default_factory=set)
    #: Módulos donde la variable se modifica (transformaciones).
    modified_in: set[str] = field(default_factory=set)
    #: Módulos donde la variable se consume/usa.
    used_in: set[str] = field(default_factory=set)

    @property
    def is_orphan(self) -> bool:
        """No se crea en ningún módulo pero se usa."""

        return not self.created_in and bool(self.used_in or self.modified_in)

    @property
    def is_unused(self) -> bool:
        """Se crea pero nunca se usa ni modifica posteriormente."""

        return bool(self.created_in) and not self.used_in and not self.modified_in


@dataclass(slots=True)
class Connection:
    """Una conexión dirigida entre dos módulos (Connect)."""

    from_id: str
    to_id: str
    from_index: int = 0
    to_index: int = 0


@dataclass(slots=True)
class Module:
    """Un módulo del workflow con su lógica de negocio extraída."""

    id: str
    name: str
    kind: str
    category: ModuleCategory
    position: tuple[int, int] = (0, 0)

    # Estructura de datos del módulo
    fields: list[DataField] = field(default_factory=list)

    # Lógica funcional específica (según el tipo de módulo)
    transformations: list[Transformation] = field(default_factory=list)
    filter: Filter | None = None
    join_keys: list[JoinKey] = field(default_factory=list)
    join_type: str = ""
    parameters: list[Parameter] = field(default_factory=list)
    scripts: list[Script] = field(default_factory=list)
    renames: list[tuple[str, str]] = field(default_factory=list)
    group_by: list[str] = field(default_factory=list)

    # Entradas / salidas (rutas de archivos, lectores, etc.)
    location: str = ""
    reader: str = ""

    #: Atributos sueltos relevantes que no encajan en lo anterior.
    extra: dict[str, str] = field(default_factory=dict)

    @property
    def display(self) -> str:
        return f"{self.name} ({self.kind})"

    @property
    def has_logic(self) -> bool:
        return bool(
            self.transformations
            or self.filter
            or self.join_keys
            or self.scripts
            or self.renames
            or self.group_by
            or self.parameters
        )
