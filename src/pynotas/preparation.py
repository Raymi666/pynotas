"""Lámina SVG de preparación: recursos agrupados, acciones y práctica concreta.

Consume exclusivamente el modelo, no el AST ni los objetos del notebook.
"""
from html import escape
import textwrap


def wrap(text, width):
    return textwrap.wrap(text, width, break_long_words=True, break_on_hyphens=False) or ['']


def preparation_svg(model, representation, prefix):
    parts = []
    ink, muted, green, blue = '#18384b', '#526f7e', '#10785f', '#4266b0'

    def rect(x, y, w, h, fill, r=15, stroke='none'):
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}"/>')

    def text(x, y, value, size=15, color=ink, weight=400, mono=False):
        font = 'monospace' if mono else 'Arial,sans-serif'
        parts.append(f'<text xml:space="preserve" x="{x}" y="{y}" font-family="{font}" font-size="{size}" fill="{color}" font-weight="{weight}">{escape(str(value))}</text>')

    def paragraph(x, y, value, chars=54, size=15, color=ink, mono=False, limit=None):
        lines = wrap(value, chars)
        if limit and len(lines) > limit:
            lines = lines[:limit]
            lines[-1] = lines[-1][:-1] + '…'
        for i, line in enumerate(lines):
            text(x, y + i * 21, line, size, color, mono=mono)
        return y + len(lines) * 21

    def label(x, y, number, title, color=green):
        rect(x, y, 32, 30, '#e4f3ed' if color == green else '#e8edfa', 8)
        text(x + 6, y + 21, number, 15, color, 700)
        text(x + 44, y + 22, title, 18, color, 700)

    def icon(x, y, qualified):
        # Consistent, small line icons; category is determined by exact names.
        rect(x, y, 32, 32, '#eaf0fa', 9)
        if qualified in {'matplotlib', 'matplotlib.pyplot', 'seaborn'}:
            d = f'M{x+7},{y+7} V{y+25} H{x+26} M{x+10},{y+20} L{x+15},{y+15} L{x+20},{y+18} L{x+25},{y+10}'
        elif qualified in {'google.colab.drive', 'google.colab.files', 'os', 'os.path', 'scipy.io', 'scipy.io.loadmat'}:
            d = f'M{x+7},{y+11} H{x+14} L{x+17},{y+14} H{x+26} V{y+25} H{x+7} Z'
        else:
            d = f'M{x+12},{y+9} L{x+6},{y+16} L{x+12},{y+23} M{x+21},{y+9} L{x+27},{y+16} L{x+21},{y+23}'
        parts.append(f'<path d="{d}" stroke="#4266b0" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')

    # Cards retain source order for lookup, but have no inter-resource arrows.
    rect(0, 0, 1000, 117, '#163c50', 0)
    text(30, 28, 'PyNotas  /  PYTHON PASO A PASO', 12, '#a4e4d3', 700)
    text(30, 68, representation.title, 30, '#ffffff', 700)
    text(30, 98, 'Reconoce las herramientas. Después, úsalas en tu programa.', 15, '#d1e3ec')
    label(30, 139, '01', 'APRENDER')
    text(30, 196, 'Herramientas que prepara esta celda', 19, ink, 700)
    text(30, 221, 'Cada tarjeta responde: ¿para qué sirve y con qué nombre la usaré?', 15, muted)

    cards = [(b, r) for b in model.blocks for r in b.resources]
    aliased = next((r for _, r in cards if r.alias), None)
    primer = ('as ' + aliased.alias + ' define un nombre corto para usar el recurso.' if aliased else
              'Cada importación hace disponible un recurso en tu programa.')
    y = 242
    for start in range(0, len(cards), 2):
        row = cards[start:start+2]
        specs = []
        for b, r in row:
            title_lines = wrap(r.qualified_name, 32)
            purpose_lines = wrap(r.purpose, 48)
            code_lines = wrap(' '.join(b.code.split()), 49)[:3]
            height = 100 + len(title_lines)*22 + len(purpose_lines)*21 + len(code_lines)*18
            specs.append((b, r, title_lines, purpose_lines, code_lines, height))
        row_height = max(s[-1] for s in specs)
        if len(row) == 1:
            row_height = max(row_height, 101 + len(wrap(primer, 44))*21)
        for col, (b, r, title_lines, purpose_lines, code_lines, _) in enumerate(specs):
            x = 30 + col * 478
            rect(x, y, 462, row_height, '#ffffff', 15, '#d8e4eb')
            icon(x+17, y+17, r.qualified_name)
            ty = y+39
            for title_line in title_lines:
                text(x+60, ty, title_line, 17, ink, 700)
                ty += 22
            sy = ty + 9
            for line in purpose_lines:
                text(x+19, sy, line, 15, muted)
                sy += 21
            sy += 4
            rect(x+15, sy-14, 432, len(code_lines)*18+14, '#f1f5f8', 8)
            # Original code is also preserved unabridged in the HTML details.
            all_code_lines = wrap(' '.join(b.code.split()), 49)
            if len(all_code_lines) > 3:
                code_lines[-1] = code_lines[-1][:-1] + '…'
            for line in code_lines:
                text(x+24, sy+3, line, 12, blue, mono=True)
                sy += 18
            access = r.access_name if len(r.access_name) < 36 else r.access_name[:33]+'…'
            text(x+19, y+row_height-17, 'Nombre de uso: ' + access, 12, green)
            trace = f'L{b.line}' if b.line == b.end_line else f'L{b.line}–{b.end_line}'
            text(x+405, y+row_height-17, trace, 11, muted)
        if len(row) == 1:
            rect(508, y, 462, row_height, '#e9f5ef', 15)
            text(527, y+34, 'CLAVE PARA LEER EL CÓDIGO', 13, green, 700)
            paragraph(527, y+69, primer, 44, 17)
            text(527, y+row_height-23, 'Preparar una herramienta es el primer paso.', 14, muted)
        y += row_height + 14

    if len(cards) % 2 == 0:
        primer_height = 62 + len(wrap(primer, 100))*21
        rect(30, y+1, 940, primer_height, '#e9f5ef', 13)
        text(48, y+28, 'CLAVE PARA LEER EL CÓDIGO', 12, green, 700)
        paragraph(48, y+55, primer, 100, 16)
        y += primer_height + 27
    else:
        y += 10

    actions = [b for b in model.blocks if b.kind == 'setup']
    if actions:
        text(30, y+4, 'Ahora sí: una llamada que solicita una acción', 19, ink, 700)
        y += 23
        for b in actions:
            code_lines = wrap(' '.join(b.code.split()), 92)
            summary_lines = [line for s in b.summaries for line in wrap(s, 105)]
            height = 81 + len(code_lines)*22 + len(summary_lines)*21
            rect(30, y, 940, height, '#fff6e6', 15, '#eddfc1')
            text(50, y+30, 'Conectar Google Drive', 18, '#855d1f', 700)
            text(920, y+30, f'L{b.line}', 11, muted)
            sy = y+61
            for line in code_lines:
                text(50, sy, line, 14, ink, mono=True)
                sy += 22
            sy += 8
            for line in summary_lines:
                text(50, sy, line, 15, '#655943')
                sy += 21
            y += height+14
    else:
        y = paragraph(30, y+3, 'Siguiente paso: usa una de estas herramientas mediante una llamada a una función.', 106, 15, muted)+14

    text(30, y+9, 'Idea clave: importar un recurso y llamar a una función son instrucciones diferentes.', 16, ink, 700)
    y += 42
    practice = wrap(representation.practice, 49)
    apply = wrap(representation.apply, 49)
    height = max(len(practice), len(apply))*23 + 93
    for x, number, title, lines, color, fill in [(30,'02','PRACTICAR',practice,blue,'#edf2fd'),
                                               (508,'03','APLICAR',apply,green,'#e9f5ef')]:
        rect(x, y, 462, height, fill, 15)
        label(x+18, y+16, number, title, color)
        for i, line in enumerate(lines):
            text(x+18, y+76+i*23, line, 16)
    y += height + 36
    text(30, y, 'Las etiquetas L indican líneas de tu celda. Recursos agrupados; no hay dependencias dibujadas entre ellos.', 12, muted)
    y += 24
    return (f'<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="{prefix}-title" '
            f'viewBox="0 0 1000 {y}" style="width:100%;min-width:720px;display:block" font-family="Arial,sans-serif">'
            f'<title id="{prefix}-title">{escape(representation.title)} · Aprender, Practicar y Aplicar</title>'
            '<desc>Herramientas de la celda, nombres de uso, código original y acciones de preparación. No se muestran valores observados.</desc>'
            f'<rect width="1000" height="{y}" fill="#f7fafc"/>' + ''.join(parts) + '</svg>')
