"""Generador de XML limpio: conserva sólo la lógica funcional.

Reconstruye un XML mínimo desde el modelo interno, eliminando toda la
información del diseñador (propiedades AFP/PDF/PCL, posiciones, seguridad,
etiquetas, GUIDs, etc.).
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from xml.dom import minidom

from inspire.model.elements import Module
from inspire.model.workflow import Workflow


class CleanXmlGenerator:
    """Produce un XML funcional reducido del workflow."""

    def render(self, workflow: Workflow) -> str:
        root = ET.Element("Workflow")
        root.set("name", workflow.name)
        root.set("version", workflow.version)

        modules_el = ET.SubElement(root, "Modules")
        for module in workflow.modules:
            modules_el.append(self._module_element(module))

        conns_el = ET.SubElement(root, "Connections")
        for conn in workflow.connections:
            if conn.from_id and conn.to_id:
                ET.SubElement(
                    conns_el,
                    "Connection",
                    {"from": conn.from_id, "to": conn.to_id},
                )

        rough = ET.tostring(root, encoding="unicode")
        return minidom.parseString(rough).toprettyxml(indent="  ")

    def _module_element(self, module: Module) -> ET.Element:
        el = ET.Element(
            "Module",
            {
                "id": module.id,
                "name": module.name,
                "kind": module.kind,
                "category": module.category.value,
            },
        )
        for t in module.transformations:
            t_el = ET.SubElement(
                el,
                "Transformation",
                {"target": t.dot_name, "fcv": t.fcv_type, "kind": t.kind},
            )
            if t.expression:
                t_el.set("expression", t.expression)
            if t.script:
                ET.SubElement(t_el, "Script").text = t.script
        if module.filter is not None:
            f_el = ET.SubElement(el, "Filter")
            for c in module.filter.conditions:
                ET.SubElement(
                    f_el,
                    "Condition",
                    {
                        "field": c.search_name,
                        "operator": c.operator,
                        "value": c.value,
                        "invert": str(c.invert),
                    },
                )
        for k in module.join_keys:
            ET.SubElement(
                el,
                "Join",
                {"type": module.join_type, "left": k.left, "right": k.right},
            )
        for p in module.parameters:
            ET.SubElement(
                el,
                "Parameter",
                {"name": p.name, "type": p.type, "default": p.default},
            )
        for old, new in module.renames:
            ET.SubElement(el, "Rename", {"from": old, "to": new})
        for g in module.group_by:
            ET.SubElement(el, "GroupBy", {"field": g})
        for s in module.scripts:
            s_el = ET.SubElement(el, "Script", {"language": s.language})
            s_el.text = s.code
        if module.location:
            ET.SubElement(el, "Location").text = module.location
        return el

    def write(self, workflow: Workflow, path: str | Path) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(self.render(workflow), encoding="utf-8")
        return out
