"""WorkflowParser: orquesta loader + extractores hacia el modelo interno."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from inspire.extractors.fields import iter_fields
from inspire.extractors.registry import build_module
from inspire.model.elements import Connection, Module, Variable
from inspire.model.enums import DESIGNER_TAGS, category_for
from inspire.parser.loader import XmlLoader


class WorkflowParser:
    """Convierte el XML de un workflow de Inspire en un :class:`Workflow`."""

    def __init__(self, *, loader: XmlLoader | None = None) -> None:
        self.loader = loader or XmlLoader()

    def parse_file(self, path: str | Path):
        from inspire.model.workflow import Workflow  # import diferido

        root = self.loader.load(path)
        workflow = self._build(root)
        workflow.source_file = str(path)
        workflow.name = Path(path).stem
        return workflow

    def parse_root(self, root: ET.Element):
        return self._build(root)

    # ------------------------------------------------------------------

    def _build(self, root: ET.Element):
        from inspire.model.workflow import Workflow

        workflow = Workflow(version=root.get("version", ""))

        for child in root:
            tag = child.tag
            if tag == "Connect":
                workflow.connections.append(self._connection(child))
            elif tag in DESIGNER_TAGS:
                continue
            elif category_for(tag).value != "other" or self._looks_like_module(child):
                workflow.modules.append(build_module(child))

        workflow.variables = self._collect_variables(workflow.modules)
        return workflow

    @staticmethod
    def _looks_like_module(element: ET.Element) -> bool:
        """Heurística: un módulo tiene Id o Name."""

        return element.find("Id") is not None or element.find("Name") is not None

    @staticmethod
    def _connection(element: ET.Element) -> Connection:
        def _int(tag: str) -> int:
            try:
                return int(element.findtext(tag, "0") or "0")
            except ValueError:
                return 0

        return Connection(
            from_id=element.findtext("From", ""),
            to_id=element.findtext("To", ""),
            from_index=_int("FromIndex"),
            to_index=_int("ToIndex"),
        )

    @staticmethod
    def _collect_variables(modules: list[Module]) -> list[Variable]:
        """Reúne todas las variables a partir de campos y transformaciones.

        Una variable se identifica por su nombre (último segmento del path).
        Se registra dónde se declara (campos del módulo) y dónde se modifica
        (transformaciones con lógica que la tienen como destino).
        """

        index: dict[str, Variable] = {}

        def ensure(name: str) -> Variable:
            var = index.get(name)
            if var is None:
                var = Variable(name=name)
                index[name] = var
            return var

        for module in modules:
            # Campos declarados -> variable creada en este módulo.
            for field in iter_fields(module.fields):
                if field.is_subtree:
                    continue
                var = ensure(field.name)
                var.created_in.add(module.name)
                if not var.type:
                    var.type = field.type
            # Transformaciones -> variable modificada.
            for transformation in module.transformations:
                leaf = transformation.dot_name.split(".")[-1]
                if not leaf:
                    continue
                var = ensure(leaf)
                var.modified_in.add(module.name)
                if not var.type and transformation.node_type:
                    var.type = transformation.node_type
            # Scripts -> lecturas/escrituras.
            for script in module.scripts:
                for name in script.reads:
                    ensure(name.split(".")[-1]).used_in.add(module.name)
                for name in script.writes:
                    ensure(name.split(".")[-1]).modified_in.add(module.name)
            # Filtros -> variables consumidas.
            if module.filter is not None:
                for cond in module.filter.conditions:
                    leaf = cond.search_name.split(".")[-1]
                    if leaf:
                        ensure(leaf).used_in.add(module.name)

        return sorted(index.values(), key=lambda v: v.name.lower())


def parse_workflow(path: str | Path):
    """Atajo funcional para parsear un workflow desde un archivo."""

    return WorkflowParser().parse_file(path)
