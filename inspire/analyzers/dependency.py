"""Dependency Analyzer: árbol de dependencias entre módulos y variables."""

from __future__ import annotations

from inspire.model.workflow import Dependency, Workflow


class DependencyAnalyzer:
    """Construye las dependencias de flujo y de variables del workflow."""

    def analyze(self, workflow: Workflow) -> list[Dependency]:
        deps: list[Dependency] = []

        # Dependencias de variables: módulo que la crea/modifica -> módulo que la usa.
        module_by_name = {m.name: m for m in workflow.modules}
        for variable in workflow.variables:
            producers = variable.created_in | variable.modified_in
            for consumer in variable.used_in:
                for producer in producers:
                    if producer != consumer:
                        deps.append(
                            Dependency(
                                variable=variable.name,
                                source_module=producer,
                                target_module=consumer,
                            )
                        )

        # Si no hay uso explícito, derivar consumo por las conexiones de flujo.
        if not deps:
            deps = self._flow_variable_deps(workflow)

        workflow.dependencies = deps
        # Marcar módulos huérfanos / hojas no es necesario aquí.
        _ = module_by_name
        return deps

    @staticmethod
    def _flow_variable_deps(workflow: Workflow) -> list[Dependency]:
        """Aproxima dependencias siguiendo las conexiones del flujo.

        Si una variable se produce en un módulo, todo módulo aguas abajo que la
        declare/use se considera dependiente.
        """

        id_by_name = {m.name: m.id for m in workflow.modules}
        name_by_id = {m.id: m.name for m in workflow.modules}
        adj: dict[str, list[str]] = {}
        for conn in workflow.connections:
            adj.setdefault(conn.from_id, []).append(conn.to_id)

        deps: list[Dependency] = []
        for variable in workflow.variables:
            producers = variable.created_in | variable.modified_in
            for producer in producers:
                start = id_by_name.get(producer)
                if start is None:
                    continue
                for downstream_id in adj.get(start, []):
                    target = name_by_id.get(downstream_id, downstream_id)
                    deps.append(
                        Dependency(
                            variable=variable.name,
                            source_module=producer,
                            target_module=target,
                        )
                    )
        return deps
