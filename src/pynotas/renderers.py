"""Tres renderizadores sobre el contrato pedagógico, sin acceder al AST."""
from dataclasses import dataclass
from html import escape
import textwrap
import uuid
from .analyzer import walk_blocks
from .model import is_preparation
from ._version import __version__
from .preparation import preparation_svg


@dataclass
class Node:
    id: str
    title: str
    code: str = ""
    line: int = 0
    end_line: int = 0
    kind: str = "transform"
    summaries: tuple[str, ...] = ()
    result: str = ""


@dataclass
class Edge:
    source: str
    target: str
    label: str = ""


def from_block(b):
    return Node(b.id, b.title, b.code, b.line, b.end_line, b.kind, b.summaries, b.result)


def control_graph(model):
    nodes, edges = [], []

    def sequence(blocks, incoming):
        for b in blocks:
            nodes.append(from_block(b))
            for origin, label in incoming:
                edges.append(Edge(origin, b.id, label))
            if b.kind == "decision":
                yes = sequence(b.body, [(b.id, "Verdadero")])
                no = sequence(b.alternative, [(b.id, "Falso")])
                if yes or no:
                    join = b.id + "_join"
                    nodes.append(Node(join, "Continuar", kind="join"))
                    for origin, label in yes + no:
                        edges.append(Edge(origin, join, label))
                    incoming = [(join, "")]
                else:
                    incoming = []
                    break
            elif b.kind == "stop":
                incoming = []
                # Following statements in this sequence are statically unreachable.
                break
            else:
                incoming = [(b.id, "")]
        return incoming

    sequence(model.blocks, [])
    return nodes, edges


def dependency_graph(model):
    nodes, edges, definitions = [], [], {}
    for b in model.blocks:
        nodes.append(from_block(b))
        grouped = {}
        for name in b.reads:
            if name in definitions:
                grouped.setdefault(definitions[name], []).append(name)
        for origin, names in grouped.items():
            edges.append(Edge(origin, b.id, ", ".join(names)))
        for name in b.writes:
            definitions[name] = b.id
    return nodes, edges


def expression_graph(expression):
    nodes, edges = [], []

    def visit(e):
        ident = f"e{len(nodes)}"
        nodes.append(Node(ident, e.label, e.code, e.line, e.end_line, "operation"))
        for i, child in enumerate(e.children):
            child_id = visit(child)
            edges.append(Edge(ident, child_id, "Izquierda" if i == 0 else "Derecha"))
        return ident

    visit(expression)
    return nodes, edges


def code_lines(code):
    lines = []
    for line in code.expandtabs(4).splitlines():
        lines.extend(textwrap.wrap(line, 35, replace_whitespace=False,
                                   drop_whitespace=True) or [""])
    if len(lines) > 4:
        lines = lines[:3] + [lines[3][:32] + "…"]
    return lines


def summary_lines(node):
    return [line for summary in node.summaries for line in textwrap.wrap(summary, 36)]


def main_lines(node):
    # The primary surface explains purpose. Full code is in the foldout.
    rows = [('title', line) for line in textwrap.wrap(node.title, 31)]
    rows += [('purpose', line) for line in summary_lines(node)]
    if not node.summaries or node.kind == 'decision':
        rows += [('code', line) for line in code_lines(node.code)]
    if node.result:
        label = node.result if len(node.result) <= 72 else node.result[:69] + '…'
        rows += [('result', line) for line in textwrap.wrap('Guarda en: ' + label, 35)]
    return rows


def svg_graph(nodes, edges, label, prefix):
    if not nodes:
        return '<p>No hay instrucciones Python para representar.</p>'
    # Longest-path ranks on a DAG. Both branches join after their longest path.
    ranks = {n.id: 0 for n in nodes}
    for _ in nodes:
        changed = False
        for e in edges:
            if ranks[e.target] <= ranks[e.source]:
                ranks[e.target] = ranks[e.source] + 1
                changed = True
        if not changed:
            break
    layers = {}
    for n in nodes:
        layers.setdefault(ranks[n.id], []).append(n)
    width = max(700, max(len(layer) for layer in layers.values()) * 340 + 80)
    pos, heights = {}, {}
    y = 24
    for rank in sorted(layers):
        layer = layers[rank]
        for i, n in enumerate(layer):
            h = 30 if n.kind == "join" else max(106, 52 + 21 * len(main_lines(n)))
            heights[n.id] = h
            pos[n.id] = (width / 2 + (i - (len(layer)-1)/2) * 340, y)
        y += max(heights[n.id] for n in layer) + 56
    height = y - 48
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="{prefix}-title" '
           f'viewBox="0 0 {width} {height}" font-family="system-ui,sans-serif" style="width:100%;min-width:{min(width, 700)}px;display:block">',
           f'<title id="{prefix}-title">{escape(label)}</title>',
           '<desc>Diagrama estático. Las etiquetas de línea corresponden al código fuente detallado.</desc>',
           f'<defs><marker id="{prefix}-arrow" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto"><path d="M0,0 L9,4.5 L0,9" fill="#557d91"/></marker></defs>']
    for i, e in enumerate(edges):
        x1, y1 = pos[e.source]
        x2, y2 = pos[e.target]
        y1 += heights[e.source]
        mid = (y1 + y2) / 2
        if ranks[e.target] - ranks[e.source] > 1:
            # Route long dependencies in an outer gutter, outside intermediate blocks.
            gutter = 16 + (i % 3) * 9
            path = f"M{x1},{y1} V{y1+22} H{gutter} V{y2-25} H{x2} V{y2-3}"
            lx, ly = (x1 + gutter)/2, y1+14
        else:
            path = f"M{x1},{y1} V{mid} H{x2} V{y2-3}"
            lx, ly = (x1 + x2)/2, mid-9
        out.append(f'<path d="{path}" fill="none" stroke="#557d91" stroke-width="2" marker-end="url(#{prefix}-arrow)"/>')
        if e.label:
            label_text = e.label if len(e.label) < 27 else e.label[:24] + "…"
            out.append(f'<text x="{lx}" y="{ly}" text-anchor="middle" font-size="12" font-weight="700" fill="#315269" stroke="#f7fafc" stroke-width="5" paint-order="stroke">{escape(label_text)}<title>{escape(e.label)}</title></text>')
    colors = {"data": ("#e4f5ef", "#12755e"), "operation": ("#e8efff", "#3558ad"),
              "decision": ("#fff1d7", "#96611e"), "opaque": ("#f0edf5", "#716182"),
              "stop": ("#ffe8e5", "#a64231"), "import": ("#eef3ff", "#3558ad")}
    for n in nodes:
        x, y = pos[n.id]
        h = heights[n.id]
        fill, accent = colors.get(n.kind, ("#ffffff", "#386478"))
        if n.kind == "join":
            out.append(f'<circle cx="{x}" cy="{y+15}" r="9" fill="#557d91"><title>Reunión de caminos</title></circle>')
            continue
        out.append(f'<g><title>{escape(n.title + chr(10) + n.code)}</title>')
        if n.kind == "decision":
            out.append(f'<path d="M{x-132},{y} H{x+132} L{x+155},{y+h/2} L{x+132},{y+h} H{x-132} L{x-155},{y+h/2} Z" fill="{fill}" stroke="{accent}" stroke-width="1.6"/>')
        else:
            out.append(f'<rect x="{x-155}" y="{y}" width="310" height="{h}" rx="13" fill="{fill}" stroke="#c9d9e3"/>')
            out.append(f'<rect x="{x-155}" y="{y+16}" width="4" height="{h-32}" rx="2" fill="{accent}"/>')
        cursor = y + 26
        previous = None
        for category, line in main_lines(n):
            if previous is not None and category != previous:
                cursor += 7
            color = accent if category == 'title' else '#526978' if category == 'result' else '#183247'
            size = 14 if category == 'title' else 12
            weight = '700' if category == 'title' else '400'
            font = 'monospace' if category in {'code', 'result'} else 'system-ui,sans-serif'
            out.append(f'<text x="{x-133}" y="{cursor}" font-family="{font}" font-size="{size}" font-weight="{weight}" fill="{color}">{escape(line)}</text>')
            cursor += 19
            previous = category
        trace = f"L{n.line}" if n.line == n.end_line else f"L{n.line}–{n.end_line}"
        out.append(f'<text x="{x+132}" y="{y+h-12}" text-anchor="end" font-size="10" fill="#526978">{trace}</text></g>')
    out.append('</svg>')
    return ''.join(out)


def render_despiece(model, prefix):
    nodes, edges = dependency_graph(model)
    result = '<p class="legend">Las flechas conectan un dato con los pasos de esta celda que usan su nombre.</p>'
    result += svg_graph(nodes, edges, "Dependencias entre datos, operaciones y salida", prefix)
    focus = next((b.expression for b in reversed(model.blocks) if b.expression), None)
    if focus:
        result += '<h3>Acercamiento · partes de la expresión</h3><p class="legend">Flechas = se compone de. No representan orden de evaluación.</p>'
        result += svg_graph(*expression_graph(focus), "Operandos de la expresión", prefix + "-expr")
    return result


def render_flujo(model, prefix):
    return '<p class="legend">Sigue las flechas para leer los pasos. Cada flecha continúa si el paso anterior termina sin interrumpirse.</p>' + svg_graph(
        *control_graph(model), "Secuencia estructural del código", prefix)


def render_decisiones(model, prefix):
    return '<p class="legend">Verdadero significa «sí»; falso significa «no». Se muestran los dos caminos posibles.</p>' + svg_graph(
        *control_graph(model), "Condiciones y caminos posibles", prefix)


RENDERERS = {"despiece": render_despiece, "flujo": render_flujo, "decisiones": render_decisiones}


def render(model, representation, executed=False, *, collapsed=False, downloads=True):
    from .presentation import render as present
    return present(model, representation, executed, collapsed=collapsed, downloads=downloads)
