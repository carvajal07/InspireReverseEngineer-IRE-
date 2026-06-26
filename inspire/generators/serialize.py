"""Serialización del modelo interno a estructuras de datos planas (dict)."""

from __future__ import annotations

from inspire.model.elements import DataField, Module, Transformation, Variable
from inspire.model.workflow import Workflow


def field_to_dict(field: DataField) -> dict[str, object]:
    return {
        "name": field.name,
        "type": field.type,
        "optionality": field.optionality,
        "path": field.path,
        "children": [field_to_dict(c) for c in field.children],
    }


def transformation_to_dict(t: Transformation) -> dict[str, object]:
    data: dict[str, object] = {
        "target": t.dot_name,
        "node_type": t.node_type,
        "fcv": t.fcv_type,
        "kind": t.kind,
        "input_type": t.input_type,
        "output_type": t.output_type,
        "expression": t.expression,
    }
    if t.script:
        data["script"] = t.script
    if t.stack:
        data["stack"] = [transformation_to_dict(s) for s in t.stack]
    if t.props:
        data["props"] = t.props
    return data


def module_to_dict(module: Module) -> dict[str, object]:
    data: dict[str, object] = {
        "id": module.id,
        "name": module.name,
        "kind": module.kind,
        "category": module.category.value,
        "position": {"x": module.position[0], "y": module.position[1]},
    }
    if module.fields:
        data["fields"] = [field_to_dict(f) for f in module.fields]
    if module.transformations:
        data["transformations"] = [
            transformation_to_dict(t) for t in module.transformations
        ]
    if module.filter is not None:
        data["filter"] = {
            "expression": module.filter.as_expression(),
            "has_else_output": module.filter.has_else_output,
            "conditions": [
                {
                    "field": c.search_name,
                    "operator": c.operator,
                    "value": c.value,
                    "value_type": c.value_type,
                    "invert": c.invert,
                }
                for c in module.filter.conditions
            ],
        }
    if module.join_keys:
        data["join"] = {
            "type": module.join_type,
            "keys": [{"left": k.left, "right": k.right} for k in module.join_keys],
        }
    if module.parameters:
        data["parameters"] = [
            {
                "name": p.name,
                "type": p.type,
                "default": p.default,
                "command_line": p.command_line,
            }
            for p in module.parameters
        ]
    if module.scripts:
        data["scripts"] = [
            {
                "language": s.language,
                "lines": s.line_count,
                "reads": s.reads,
                "writes": s.writes,
                "code": s.code,
            }
            for s in module.scripts
        ]
    if module.renames:
        data["renames"] = [{"from": o, "to": n} for o, n in module.renames]
    if module.group_by:
        data["group_by"] = module.group_by
    if module.location:
        data["location"] = module.location
    if module.reader:
        data["reader"] = module.reader
    if module.extra:
        data["extra"] = module.extra
    return data


def variable_to_dict(v: Variable) -> dict[str, object]:
    return {
        "name": v.name,
        "type": v.type,
        "initial_value": v.initial_value,
        "created_in": sorted(v.created_in),
        "modified_in": sorted(v.modified_in),
        "used_in": sorted(v.used_in),
        "is_unused": v.is_unused,
        "is_orphan": v.is_orphan,
    }


def workflow_to_dict(workflow: Workflow) -> dict[str, object]:
    return {
        "name": workflow.name,
        "version": workflow.version,
        "source_file": workflow.source_file,
        "statistics": workflow.statistics.as_dict(),
        "modules": [module_to_dict(m) for m in workflow.modules],
        "connections": [
            {
                "from": c.from_id,
                "to": c.to_id,
                "from_index": c.from_index,
                "to_index": c.to_index,
            }
            for c in workflow.connections
        ],
        "variables": [variable_to_dict(v) for v in workflow.variables],
        "dependencies": [
            {
                "variable": d.variable,
                "source": d.source_module,
                "target": d.target_module,
            }
            for d in workflow.dependencies
        ],
    }
