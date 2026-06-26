"""WorkflowParser: orquesta loader + extractores hacia el modelo interno."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from inspire.extractors.fields import iter_fields
from inspire.extractors.registry import build_module
from inspire.model.elements import Connection, Module, Variable
from inspire.model.enums import DESIGNER_TAGS, ModuleCategory, category_for
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

        workflow.variables = self._collect_variables(
            workflow.modules, workflow.connections
        )
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

    @classmethod
    def _collect_variables(
        cls, modules: list[Module], connections: list[Connection]
    ) -> list[Variable]:
        """Reúne las variables distinguiendo creación, modificación y uso.

        Punto clave: el ``WorkFlowDefinition`` de un módulo contiene el árbol de
        datos COMPLETO tal como existe en ese punto del flujo, por lo que cada
        módulo aguas abajo re-declara todas las variables que ya existen. Por eso
        la declaración NO equivale a creación.

        La creación real se detecta con señales explícitas:

        * Módulos de entrada: declaran los datos fuente (sus campos y parámetros).
        * ``DataTransformer``: los ``CreatedNodes`` que introduce.
        * ``Renamer``: el nuevo nombre que produce.

        Para variables creadas por módulos sin metadatos de creación (p.ej.
        scripts de imposición) se usa como respaldo la primera aparición en el
        orden topológico del flujo, garantizando un único módulo creador.
        """

        index: dict[str, Variable] = {}
        # leaf -> ids de módulos cuyo árbol de datos declara la variable.
        declared_in: dict[str, set[str]] = {}

        def ensure(name: str, type_hint: str = "") -> Variable:
            var = index.get(name)
            if var is None:
                var = Variable(name=name, type=type_hint)
                index[name] = var
            elif not var.type and type_hint:
                var.type = type_hint
            return var

        # 1) Catálogo de variables y tipos a partir de todos los árboles de datos.
        for module in modules:
            for field in iter_fields(module.fields):
                if field.is_subtree:
                    continue
                ensure(field.name, field.type)
                declared_in.setdefault(field.name, set()).add(module.id)

        # 2) Creación explícita.
        for module in modules:
            if module.category is ModuleCategory.INPUT:
                for field in iter_fields(module.fields):
                    if field.is_subtree:
                        continue
                    ensure(field.name, field.type).created_in.add(module.name)
                for param in module.parameters:
                    ensure(param.name, param.type).created_in.add(module.name)
            for dot in module.created_nodes:
                leaf = dot.split(".")[-1]
                if leaf:
                    ensure(leaf).created_in.add(module.name)
            for old, new in module.renames:
                new_leaf = new.split(".")[-1]
                old_leaf = old.split(".")[-1]
                if new_leaf:
                    ensure(new_leaf).created_in.add(module.name)
                if old_leaf:
                    ensure(old_leaf).used_in.add(module.name)

        # 3) Modificación (transformaciones/scripts) y uso (filtros/joins/scripts).
        for module in modules:
            for transformation in module.transformations:
                leaf = transformation.dot_name.split(".")[-1]
                if not leaf:
                    continue
                var = ensure(leaf, transformation.node_type)
                var.modified_in.add(module.name)
            for script in module.scripts:
                for name in script.reads:
                    ensure(name.split(".")[-1]).used_in.add(module.name)
                for name in script.writes:
                    ensure(name.split(".")[-1]).modified_in.add(module.name)
            if module.filter is not None:
                for cond in module.filter.conditions:
                    leaf = cond.search_name.split(".")[-1]
                    if leaf:
                        ensure(leaf).used_in.add(module.name)
            for key in module.join_keys:
                for side in (key.left, key.right):
                    leaf = side.split(".")[-1]
                    if leaf:
                        ensure(leaf).used_in.add(module.name)

        # 4) Respaldo: atribuir las variables sin creador a su primera aparición
        #    en el orden de flujo (un único módulo creador).
        order = cls._flow_order(modules, connections)
        position = {module_id: i for i, module_id in enumerate(order)}
        name_by_id = {m.id: m.name for m in modules}
        for name, var in index.items():
            if var.created_in:
                continue
            candidates = declared_in.get(name)
            if not candidates:
                continue
            first = min(candidates, key=lambda mid: position.get(mid, len(order)))
            var.created_in.add(name_by_id.get(first, first))

        return sorted(index.values(), key=lambda v: v.name.lower())

    @staticmethod
    def _flow_order(
        modules: list[Module], connections: list[Connection]
    ) -> list[str]:
        """Orden topológico (Kahn) de los módulos según las conexiones.

        Los ciclos o nodos sin orden definido se añaden al final en el orden
        original, de modo que siempre se devuelven todos los módulos.
        """

        from collections import deque

        ids = [m.id for m in modules]
        id_set = set(ids)
        indegree = {i: 0 for i in ids}
        adjacency: dict[str, list[str]] = {i: [] for i in ids}
        for conn in connections:
            if conn.from_id in id_set and conn.to_id in id_set:
                adjacency[conn.from_id].append(conn.to_id)
                indegree[conn.to_id] += 1

        queue = deque(i for i in ids if indegree[i] == 0)
        order: list[str] = []
        seen: set[str] = set()
        while queue:
            node = queue.popleft()
            if node in seen:
                continue
            seen.add(node)
            order.append(node)
            for nxt in adjacency[node]:
                indegree[nxt] -= 1
                if indegree[nxt] == 0:
                    queue.append(nxt)
        for i in ids:  # nodos restantes (ciclos)
            if i not in seen:
                order.append(i)
        return order


def parse_workflow(path: str | Path):
    """Atajo funcional para parsear un workflow desde un archivo."""

    return WorkflowParser().parse_file(path)
