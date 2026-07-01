"""Diagrama de flujo con layout jerárquico en Python puro (sin dependencias).

Cuando Graphviz (el binario ``dot``) no está disponible —p.ej. en equipos
corporativos sin permisos de administrador— este generador produce el mismo
tipo de diagrama por capas directamente en SVG, usando sólo la librería
estándar.

Algoritmo (estilo Sugiyama):

1. Se rompen los ciclos (aristas de retroceso) para poder estratificar.
2. Estratificación por camino más largo: cada nodo va a la capa
   ``max(capa(predecesores)) + 1``.
3. Ordenación dentro de cada capa por baricentro (varias pasadas) para reducir
   cruces.
4. Asignación de coordenadas: columnas por capa (izquierda→derecha); dentro de
   cada capa, la ``y`` se acerca al baricentro de los vecinos resolviendo
   solapes.
5. Emisión del SVG: nodos como rectángulos redondeados coloreados por
   categoría; aristas como curvas Bézier con punta de flecha.

El SVG resultante usa la misma convención de ids (``fn<id>``) que el generador
de Graphviz, por lo que el portal HTML lo incrusta y hace clicables los nodos
sin cambios adicionales.
"""

from __future__ import annotations

from collections import deque
from pathlib import Path
from xml.sax.saxutils import escape

from inspire.generators.graphviz_gen import CATEGORY_COLORS, node_dom_id
from inspire.model.workflow import Workflow

_NODE_H = 44
_VGAP = 16
_HGAP = 90
_MARGIN = 30
_CHAR_W = 6.6


def _node_width(name: str, kind: str) -> float:
    longest = max(len(name), len(kind) + 2)
    return min(250.0, max(120.0, longest * _CHAR_W + 24))


def _truncate(text: str, width: float) -> str:
    max_chars = int((width - 14) / _CHAR_W)
    if len(text) <= max_chars:
        return text
    return text[: max(1, max_chars - 1)] + "…"


class FlowLayoutGenerator:
    """Genera el diagrama de flujo como SVG con layout jerárquico propio."""

    def __init__(self, *, order_passes: int = 6, coord_passes: int = 12) -> None:
        self.order_passes = order_passes
        self.coord_passes = coord_passes

    # ------------------------------------------------------------------

    def build_svg(self, workflow: Workflow) -> str:
        nodes = [m.id for m in workflow.modules]
        by_id = {m.id: m for m in workflow.modules}
        node_set = set(nodes)
        edges = [
            (c.from_id, c.to_id)
            for c in workflow.connections
            if c.from_id in node_set and c.to_id in node_set
        ]

        forward = self._forward_edges(nodes, edges)
        layer = self._layering(nodes, forward)
        layers = self._group_by_layer(nodes, layer)
        self._order_layers(layers, forward)
        neighbors = self._neighbors(nodes, edges)

        width = {n: _node_width(by_id[n].name, by_id[n].kind) for n in nodes}
        xpos = self._assign_x(layers, width)
        ypos = self._assign_y(layers, neighbors)

        return self._emit_svg(workflow, by_id, edges, xpos, ypos, width)

    def write(self, workflow: Workflow, path: str | Path) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(self.build_svg(workflow), encoding="utf-8")
        return out

    # ------------------------------------------------------------------
    # Estructura del grafo
    # ------------------------------------------------------------------

    @staticmethod
    def _forward_edges(
        nodes: list[str], edges: list[tuple[str, str]]
    ) -> list[tuple[str, str]]:
        """Devuelve las aristas sin las de retroceso (rompe ciclos con DFS)."""

        adj: dict[str, list[str]] = {n: [] for n in nodes}
        for a, b in edges:
            adj[a].append(b)
        color = {n: 0 for n in nodes}  # 0 blanco, 1 gris, 2 negro
        back: set[tuple[str, str]] = set()
        for start in nodes:
            if color[start] != 0:
                continue
            color[start] = 1
            stack: list[tuple[str, object]] = [(start, iter(adj[start]))]
            while stack:
                node, it = stack[-1]
                advanced = False
                for nxt in it:  # type: ignore[assignment]
                    if color[nxt] == 0:
                        color[nxt] = 1
                        stack.append((nxt, iter(adj[nxt])))
                        advanced = True
                        break
                    if color[nxt] == 1:
                        back.add((node, nxt))
                if not advanced:
                    color[node] = 2
                    stack.pop()
        return [(a, b) for (a, b) in edges if (a, b) not in back and a != b]

    @staticmethod
    def _layering(
        nodes: list[str], forward: list[tuple[str, str]]
    ) -> dict[str, int]:
        """Estratificación por camino más largo (DAG ya sin ciclos)."""

        adj: dict[str, list[str]] = {n: [] for n in nodes}
        indeg = {n: 0 for n in nodes}
        for a, b in forward:
            adj[a].append(b)
            indeg[b] += 1
        layer = {n: 0 for n in nodes}
        queue = deque(n for n in nodes if indeg[n] == 0)
        while queue:
            node = queue.popleft()
            for nxt in adj[node]:
                if layer[node] + 1 > layer[nxt]:
                    layer[nxt] = layer[node] + 1
                indeg[nxt] -= 1
                if indeg[nxt] == 0:
                    queue.append(nxt)
        return layer

    @staticmethod
    def _group_by_layer(
        nodes: list[str], layer: dict[str, int]
    ) -> dict[int, list[str]]:
        layers: dict[int, list[str]] = {}
        for node in nodes:  # orden de inserción -> orden inicial estable
            layers.setdefault(layer[node], []).append(node)
        return layers

    @staticmethod
    def _neighbors(
        nodes: list[str], edges: list[tuple[str, str]]
    ) -> dict[str, list[str]]:
        neigh: dict[str, list[str]] = {n: [] for n in nodes}
        for a, b in edges:
            neigh[a].append(b)
            neigh[b].append(a)
        return neigh

    # ------------------------------------------------------------------
    # Ordenación y coordenadas
    # ------------------------------------------------------------------

    def _order_layers(
        self, layers: dict[int, list[str]], forward: list[tuple[str, str]]
    ) -> None:
        """Reduce cruces ordenando por baricentro (pasadas arriba/abajo)."""

        preds: dict[str, list[str]] = {}
        succs: dict[str, list[str]] = {}
        for a, b in forward:
            succs.setdefault(a, []).append(b)
            preds.setdefault(b, []).append(a)
        max_layer = max(layers) if layers else 0

        for pass_i in range(self.order_passes):
            downward = pass_i % 2 == 0
            layer_range = range(1, max_layer + 1) if downward else range(max_layer - 1, -1, -1)
            for lyr in layer_range:
                ids = layers.get(lyr, [])
                ref = layers.get(lyr - 1 if downward else lyr + 1, [])
                index = {nid: i for i, nid in enumerate(ref)}
                rel = preds if downward else succs

                def bary(nid: str) -> float:
                    positions = [index[x] for x in rel.get(nid, []) if x in index]
                    if not positions:
                        return float(ids.index(nid))
                    return sum(positions) / len(positions)

                layers[lyr] = sorted(ids, key=bary)

    def _assign_x(
        self, layers: dict[int, list[str]], width: dict[str, float]
    ) -> dict[str, float]:
        xpos: dict[str, float] = {}
        x = float(_MARGIN)
        for lyr in sorted(layers):
            ids = layers[lyr]
            col_w = max((width[n] for n in ids), default=120.0)
            for nid in ids:
                xpos[nid] = x
            x += col_w + _HGAP
        return xpos

    def _assign_y(
        self, layers: dict[int, list[str]], neighbors: dict[str, list[str]]
    ) -> dict[str, float]:
        # Posición inicial: apilado por orden dentro de la capa.
        ypos: dict[str, float] = {}
        layer_of: dict[str, int] = {}
        for lyr, ids in layers.items():
            y = 0.0
            for nid in ids:
                ypos[nid] = y
                layer_of[nid] = lyr
                y += _NODE_H + _VGAP

        max_layer = max(layers) if layers else 0
        for pass_i in range(self.coord_passes):
            layer_range = (
                range(0, max_layer + 1)
                if pass_i % 2 == 0
                else range(max_layer, -1, -1)
            )
            for lyr in layer_range:
                ids = layers.get(lyr, [])
                desired = []
                for nid in ids:
                    centers = [
                        ypos[x] + _NODE_H / 2
                        for x in neighbors[nid]
                        if layer_of.get(x) != lyr
                    ]
                    d = sum(centers) / len(centers) if centers else ypos[nid] + _NODE_H / 2
                    desired.append((d, nid))
                desired.sort(key=lambda t: t[0])
                prev = None
                for d, nid in desired:
                    target = d - _NODE_H / 2
                    if prev is not None and target < prev + _NODE_H + _VGAP:
                        target = prev + _NODE_H + _VGAP
                    ypos[nid] = target
                    prev = target
                layers[lyr] = [nid for _, nid in desired]

        # Normalizar para que la y mínima sea el margen.
        if ypos:
            min_y = min(ypos.values())
            for nid in ypos:
                ypos[nid] += _MARGIN - min_y
        return ypos

    # ------------------------------------------------------------------
    # Emisión del SVG
    # ------------------------------------------------------------------

    def _emit_svg(
        self,
        workflow: Workflow,
        by_id: dict,
        edges: list[tuple[str, str]],
        xpos: dict[str, float],
        ypos: dict[str, float],
        width: dict[str, float],
    ) -> str:
        canvas_w = (
            max((xpos[n] + width[n] for n in xpos), default=0) + _MARGIN
        )
        canvas_h = max((ypos[n] + _NODE_H for n in ypos), default=0) + _MARGIN

        parts: list[str] = [
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{canvas_w:.0f}pt" height="{canvas_h:.0f}pt" '
            f'viewBox="0 0 {canvas_w:.0f} {canvas_h:.0f}">',
            '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" '
            'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            '<path d="M0,0 L10,5 L0,10 z" fill="#94a3b8"/></marker></defs>',
        ]

        # Aristas primero (debajo de los nodos).
        for a, b in edges:
            if a not in xpos or b not in xpos:
                continue
            x1 = xpos[a] + width[a]
            y1 = ypos[a] + _NODE_H / 2
            x2 = xpos[b]
            y2 = ypos[b] + _NODE_H / 2
            dx = max(30.0, abs(x2 - x1) / 2)
            parts.append(
                f'<path class="edge" d="M{x1:.1f},{y1:.1f} '
                f'C{x1 + dx:.1f},{y1:.1f} {x2 - dx:.1f},{y2:.1f} {x2:.1f},{y2:.1f}" '
                f'fill="none" stroke="#94a3b8" stroke-opacity="0.55" '
                f'marker-end="url(#arrow)"/>'
            )

        # Nodos.
        for node_id, module in by_id.items():
            if node_id not in xpos:
                continue
            x = xpos[node_id]
            y = ypos[node_id]
            w = width[node_id]
            fill = CATEGORY_COLORS.get(module.category.value, "#cbd5e1")
            name = _truncate(module.name, w)
            kind = _truncate(f"({module.kind})", w)
            dom = node_dom_id(node_id)
            parts.append(
                f'<g class="node" id="{dom}">'
                f"<title>{escape(module.name)} [{escape(module.kind)}]</title>"
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{_NODE_H}" '
                f'rx="8" fill="{fill}" stroke="#1e293b" stroke-width="1"/>'
                f'<text x="{x + w / 2:.1f}" y="{y + 18:.1f}" text-anchor="middle" '
                f'font-family="Helvetica" font-size="11" font-weight="600" '
                f'fill="#0f172a">{escape(name)}</text>'
                f'<text x="{x + w / 2:.1f}" y="{y + 33:.1f}" text-anchor="middle" '
                f'font-family="Helvetica" font-size="9" fill="#334155">'
                f"{escape(kind)}</text>"
                f"</g>"
            )

        parts.append("</svg>")
        return "".join(parts)
