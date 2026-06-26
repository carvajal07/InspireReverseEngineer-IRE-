"""XML Loader: lectura tolerante y eficiente de XML de Inspire.

Los proyectos de Inspire pueden ser muy grandes (varias decenas de MB), por lo
que el loader usa ``ElementTree`` y opcionalmente recorta el árbol del
diseñador para reducir el consumo de memoria.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from inspire.model.enums import DESIGNER_TAGS


class XmlLoadError(Exception):
    """Error al cargar o parsear el archivo XML."""


class XmlLoader:
    """Carga un XML de Inspire y devuelve su elemento raíz."""

    def __init__(self, *, strip_designer: bool = False) -> None:
        #: Si es True, elimina los nodos puramente del diseñador al cargar.
        self.strip_designer = strip_designer

    def load(self, path: str | Path) -> ET.Element:
        file_path = Path(path)
        if not file_path.exists():
            raise XmlLoadError(f"No existe el archivo: {file_path}")
        if not file_path.is_file():
            raise XmlLoadError(f"La ruta no es un archivo: {file_path}")

        try:
            tree = ET.parse(file_path)
        except ET.ParseError as exc:  # pragma: no cover - depende del XML
            raise XmlLoadError(f"XML malformado en {file_path}: {exc}") from exc

        root = tree.getroot()
        self._validate_root(root)
        if self.strip_designer:
            self._strip_designer_nodes(root)
        return root

    def loads(self, xml_text: str) -> ET.Element:
        """Carga desde una cadena de texto (útil en pruebas)."""

        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            raise XmlLoadError(f"XML malformado: {exc}") from exc
        self._validate_root(root)
        if self.strip_designer:
            self._strip_designer_nodes(root)
        return root

    @staticmethod
    def _validate_root(root: ET.Element) -> None:
        if root.tag != "WorkFlow":
            raise XmlLoadError(
                f"Raíz inesperada '{root.tag}'. Se esperaba 'WorkFlow'. "
                "¿Es un proyecto exportado de Inspire Designer?"
            )

    @staticmethod
    def _strip_designer_nodes(root: ET.Element) -> None:
        for child in list(root):
            if child.tag in DESIGNER_TAGS:
                root.remove(child)


def load_xml(path: str | Path, *, strip_designer: bool = False) -> ET.Element:
    """Atajo funcional para cargar un XML de Inspire."""

    return XmlLoader(strip_designer=strip_designer).load(path)
