"""Automatic vector compositions selected from the pedagogical model.

All diagrams are conceptual. This module never evaluates code, reads notebook
variables, or reconstructs results. SVG and PDF consume the same primitives.
"""
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    kind: str
    label: str
    accent: str
    light: str
    bright: str
    secondary: str = '#FAAA72'


THEMES = {
    'signal': Theme('signal', 'SEÑALES Y MAGNITUDES', '#007B74', '#E2F2E9', '#78E8CB'),
    'network': Theme('network', 'REDES NEURONALES', '#6451BF', '#EEE9FB', '#C9B3FF'),
    'learning': Theme('learning', 'APRENDIZAJE CON DATOS', '#2857AB', '#E8EEFB', '#94C5FF'),
    'decision': Theme('decision', 'DECISIONES EN PYTHON', '#A94825', '#FBEBDC', '#FFBE8B'),
    'expression': Theme('expression', 'DATOS Y OPERACIONES', '#18787B', '#E3F2EF', '#79DDD7'),
    'resources': Theme('resources', 'HERRAMIENTAS DE PYTHON', '#476199', '#E9EEFA', '#AAC4FF'),
    'code': Theme('code', 'LEER Y COMPRENDER PYTHON', '#18787B', '#E3F2EF', '#79DDD7'),
}


def theme_for(model, representation):
    from .illustrations import kind_for
    from .model import is_preparation
    if representation.format == 'decisiones':
        return THEMES['decision']
    if is_preparation(model):
        return THEMES['resources']
    kind = kind_for(tuple(t.key for t in model.theories))
    if kind == 'code' and representation.format == 'despiece':
        kind = 'expression'
    return THEMES[kind]


def wave(p, x, y, w, h, color, squared=False):
    """A schematic oscillation, with no measured coordinates or values."""
    points = []
    for i in range(81):
        value = math.sin(i / 80 * math.pi * 4)
        if squared:
            value = value * value
        points.append((x + i * w / 80, y - h * value))
    p.line(x, y, x+w, y, '#47606A', .6)
    for a, b in zip(points, points[1:]):
        p.line(*a, *b, color, 1.65)
    for i in (7, 29, 49, 72):
        p.circle(*points[i], 2.1, '#FAAA72')


def connector(p, x, y, x2, y2, color):
    dx = (x2-x) * .52
    p.path([('M', x, y), ('C', x+dx, y, x2-dx, y2, x2, y2)], stroke=color, width=1)


def icon(p, cx, cy, kind, color, size=19):
    if kind == 'table':
        for row in range(3):
            for col in range(3):
                p.rect(cx-size+col*14, cy-size+row*13, 10, 9,
                       color if row != 2 else '#FAAA72', 2)
    elif kind == 'braces':
        p.text(cx-23, cy+9, '{ }', 24, color, 'PyNotasMono')
    elif kind == 'bars':
        for i, height in enumerate((14, 30, 21, 39, 17)):
            p.rect(cx-27+i*12, cy+20-height, 7, height, color if i != 3 else '#FAAA72', 2)
    elif kind == 'dots':
        for i, (dx, dy) in enumerate(((-16,-12),(-5,4),(9,-17),(20,10),(-20,18),(4,21))):
            p.circle(cx+dx, cy+dy, 4, color if i < 4 else '#FAAA72')
    else:
        p.circle(cx, cy, 18, color)
        p.circle(cx, cy, 8, '#153944')


def _label(p, x, y, text, width, color, size=8.1):
    # Page.paragraph preserves every label, wrapping inside its allocated space.
    p.paragraph(x, y, text, width, size, color, step=max(11,size*1.3))


def draw(p, x, y, w, theme, keys=(), steps=(), resources=(), decision=None):
    """Full-width teaching canvas. Returns height for the pagination engine."""
    kind = theme.kind
    h = 140 if kind == 'decision' else 156
    p.rect(x, y, w, h, '#102F3B', 12)
    # Small dotted construction grid gives the diagram a drawing-board texture.
    for xx in range(16, int(w)-8, 22):
        for yy in range(16, h-8, 22):
            p.circle(x+xx, y+yy, .55, '#28434D')
    p.rect(x+14, y+13, 3, 10, theme.bright, 1)
    p.text(x+24, y+21, 'MAPA VISUAL', 7.4, theme.bright, 'PyNotasBold')
    p.text(x+w-202, y+21, 'Esquema conceptual · sin resultados', 7, '#C3D4D8')

    if kind == 'network':
        layers = [[(x+72,y+q) for q in (56,83,110)],
                  [(x+208,y+q) for q in (46,70,94,118)],
                  [(x+337,y+q) for q in (69,99)]]
        for a, b in zip(layers, layers[1:]):
            for ax, ay in a:
                for bx, by in b:
                    connector(p, ax+6, ay, bx-6, by, '#58647F')
        for i, layer in enumerate(layers):
            for xx, yy in layer:
                p.circle(xx, yy, 12, '#3B465E')
                p.circle(xx, yy, 7.2, (theme.bright, '#82DDC5', theme.secondary)[i])
                p.circle(xx, yy, 2.3, '#FFFFFF')
        for xx, label in [(x+40,'Entradas'),(x+172,'Capas conectadas'),(x+317,'Salidas')]:
            p.text(xx, y+143, label, 8, '#EDF7F6')
        p.line(x+385,y+45,x+385,y+124,'#45616A',.8)
        _label(p,x+399,y+61,'Cada conexión participa en el cálculo.',w-414,'#E2EAF0',9)
        _label(p,x+399,y+107,'La cantidad de nodos es ilustrativa.',w-414,'#B5C8D0',7.4)

    elif kind == 'signal':
        is_rms = 'rms' in keys
        labels = ('Datos reales','Elevar al cuadrado','Promediar','Obtener la raíz') if is_rms else tuple(steps)
        if not labels:
            labels = ('Muestras','Operación','Representación')
        count = min(len(labels), 4)
        span = (w-30)/count
        for i, label in enumerate(labels[:count]):
            xx=x+15+i*span; cx=xx+span/2
            p.text(xx+8,y+43,f'{i+1:02d}',7,theme.bright,'PyNotasBold')
            if i==0 or (is_rms and i==1):
                wave(p,xx+12,y+86,span-27,19,theme.bright,squared=(i==1))
            elif is_rms and i==2:
                for j,height in enumerate((23,11,33,18,26)):
                    p.rect(cx-31+j*13,y+105-height,8,height,'#557E80',2)
                p.line(cx-37,y+81,cx+37,y+81,theme.secondary,2)
                p.text(cx-19,y+62,'media',8.5,theme.secondary)
            elif is_rms:
                p.circle(cx,y+80,26,'#2B534F')
                p.text(cx-17,y+91,'√',32,theme.bright,'PyNotasBold')
            elif i==1 and 'fft' in keys:
                p.text(cx-27,y+88,'FFT',22,theme.bright,'PyNotasBold')
            else:
                icon(p,cx,y+82,'bars' if 'fft' in keys else 'braces',theme.bright)
            _label(p,xx+7,y+127,label,span-15,'#F4F7F7')
            if i<count-1:
                p.arrow(xx+span-10,y+83,xx+span+4,y+83,theme.secondary)

    elif kind == 'learning':
        split = 'split' in keys
        icon(p,x+67,y+81,'table',theme.bright)
        if split:
            connector(p,x+104,y+81,x+221,y+57,theme.bright)
            connector(p,x+104,y+81,x+221,y+107,theme.secondary)
            p.rect(x+223,y+39,154,35,'#244A65',7)
            p.rect(x+223,y+90,154,35,'#60463C',7)
            p.text(x+237,y+61,'Entrenamiento',10,theme.bright,'PyNotasBold')
            p.text(x+237,y+112,'Prueba',10,theme.secondary,'PyNotasBold')
            _label(p,x+393,y+57,'Aprender con una parte.',w-407,'#D8E7F1',8.5)
            _label(p,x+393,y+108,'Evaluar con otra.',w-407,'#F5DAC4',8.5)
            p.text(x+38,y+139,'Conjunto de datos',8,'#E6EFF3')
        else:
            centers=(x+67,x+267,x+462)
            p.arrow(centers[0]+41,y+82,centers[1]-39,y+82,theme.bright)
            p.arrow(centers[1]+40,y+82,centers[2]-41,y+82,theme.secondary)
            p.circle(centers[1],y+82,30,'#28465E')
            icon(p,centers[1],y+82,'braces',theme.bright)
            icon(p,centers[2],y+82,'dots',theme.secondary)
            labels=tuple(steps) if len(steps)==3 else ('Datos','Operación reconocida','Salida conceptual')
            for cx,label in zip(centers,labels):_label(p,cx-58,y+135,label,118,'#E6EFF3')

    elif kind == 'decision':
        cx=x+249;cy=y+72
        p.path([('M',cx,cy-37),('L',cx+61,cy),('L',cx,cy+37),('L',cx-61,cy),('Z',)],
               fill='#624936',stroke=theme.bright,width=1.4)
        if decision:
            from .layout import wrap
            condition=decision.code.removeprefix('if ').removeprefix('elif ').rstrip(':').strip()
            rows=wrap(condition,92,8,'PyNotasMono')
            if len(rows)>2:rows=[rows[0],rows[1][:-1]+'…']
            for i,row in enumerate(rows):p.text(cx-46,cy+3+(i-(len(rows)-1)/2)*12,row,8,theme.bright,'PyNotasMono')
            p.text(cx-28,cy-43,f'CONDICIÓN · L{decision.line}',6.8,theme.bright,'PyNotasBold')
        else:p.text(cx-11,cy+10,'?',30,theme.bright,'PyNotasBold')
        p.text(x+22,y+68,'Evaluar',11,'#F6EEE6','PyNotasBold')
        p.text(x+22,y+83,'la condición',9,'#C7D6D9')
        p.arrow(x+121,cy,cx-67,cy,theme.bright)
        connector(p,cx+63,cy,x+389,y+49,'#90DBBA')
        connector(p,cx+63,cy,x+389,y+101,theme.secondary)
        for yy,label,col in ((49,'Verdadero','#90DBBA'),(101,'Falso',theme.secondary)):
            p.circle(x+399,y+yy,6,col);p.text(x+414,y+yy+4,label,10,col,'PyNotasBold')
        p.text(x+157,y+131,'Se muestran alternativas; no una rama observada.',8,'#C7D6D9')

    elif kind == 'resources':
        names=list(dict.fromkeys(resources))[:5]
        if not names:names=[('','Recursos')]
        span=(w-28)/len(names)
        from .layout import wrap,fonts
        for i,(qualified,name) in enumerate(names):
            cx=x+90 if len(names)==1 else x+14+(i+.5)*span
            p.circle(cx,y+78,28,'#2C4661')
            shape='bars' if 'matplotlib' in qualified or 'seaborn' in qualified else 'table' if qualified.split('.')[0] in {'pandas','numpy'} else 'braces'
            icon(p,cx,y+77,shape,theme.bright)
            if len(name)>24:name=name[:23]+'…'
            if len(names)==1:
                headline=qualified or name
                if len(headline)>35:headline=headline[:34]+'…'
                _label(p,x+160,y+66,headline,w-181,theme.bright,14)
                p.text(x+160,y+96,'Nombre de uso: '+name,10,'#ECF1F8')
                p.text(x+160,y+123,'Disponible para tus próximas instrucciones.',8,'#B9CED9')
            else:
                for j,row in enumerate(wrap(name,span-18,8.4)):
                    p.text(cx-fonts().stringWidth(row,'PyNotas',8.4)/2,y+125+j*11,row,8.4,'#ECF1F8')
        # Imports are grouped tools, not a sequence or a data dependency graph.

    else:
        centers=(x+73,x+266,x+459)
        icon(p,centers[0],y+82,'table',theme.bright)
        p.circle(centers[1],y+82,32,'#255054')
        icon(p,centers[1],y+82,'braces',theme.bright)
        icon(p,centers[2],y+82,'dots',theme.secondary)
        for a,b in zip(centers,centers[1:]):p.arrow(a+43,y+82,b-45,y+82,theme.bright)
        for cx,label in zip(centers,('Datos de entrada','Instrucciones','Salida conceptual')):
            p.text(cx-44,y+137,label,8.2,'#EEF5F5')
    return h
