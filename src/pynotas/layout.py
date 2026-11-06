"""One paginated drawing model shared by SVG, PDF and JPG. Coordinates in points."""
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from html import escape
from ._version import __version__

WIDTH, HEIGHT = 595.28, 841.89
NAVY, TEAL, INK, MUTED = '#102F3D', '#007F83', '#203E4E', '#526671'
PALE, PAPER, LINE = '#E8F4F0', '#F2F5F7', '#D5E2E4'
BLUE, GOLD = '#4C63CB', '#C06B35'

@lru_cache(maxsize=1)
def fonts():
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    root=Path(__file__).with_name('fonts')
    for name,file in [('PyNotas','DejaVuSans.ttf'),('PyNotasBold','DejaVuSans-Bold.ttf'),('PyNotasMono','DejaVuSansMono.ttf')]:
        if name not in pdfmetrics.getRegisteredFontNames():pdfmetrics.registerFont(TTFont(name,str(root/file)))
    return pdfmetrics

def wrap(text,width,size=10,font='PyNotas'):
    metrics=fonts()
    rows=[]
    for original in str(text).split('\n'):
        if not original:rows.append('');continue
        rest=original
        while metrics.stringWidth(rest,font,size)>width:
            end=1
            while end<len(rest) and metrics.stringWidth(rest[:end+1],font,size)<=width:end+=1
            if font!='PyNotasMono':
                space=rest.rfind(' ',0,end+1)
                if space>0:end=space
            rows.append(rest[:end]);rest=rest[end:]
            if font!='PyNotasMono':rest=rest.lstrip()
        rows.append(rest)
    return rows

@dataclass
class Page:
    title: str
    ops: list = field(default_factory=list)
    width: float = WIDTH
    height: float = HEIGHT
    def rect(self,x,y,w,h,fill=PAPER,r=6):self.ops.append(('rect',x,y,w,h,fill,r))
    def text(self,x,y,s,size=10,color=INK,font='PyNotas'):self.ops.append(('text',x,y,str(s),size,color,font))
    def circle(self,x,y,r,fill=TEAL):self.ops.append(('circle',x,y,r,fill))
    def line(self,x,y,x2,y2,color=LINE,width=.8):self.ops.append(('line',x,y,x2,y2,color,width))
    def path(self,commands,stroke=None,fill=None,width=1):
        self.ops.append(('path',commands,stroke,fill,width))
    def image(self,x,y,w,h,figure):self.ops.append(('image',x,y,w,h,figure))
    def arrow(self,x,y,x2,y2,color=TEAL):
        import math
        self.line(x,y,x2,y2,color,1.2)
        angle=math.atan2(y2-y,x2-x)
        for offset in (-.55,.55):
            self.line(x2-5*math.cos(angle+offset),y2-5*math.sin(angle+offset),x2,y2,color,1.2)
    def paragraph(self,x,y,s,width=531,size=10.5,color=INK,font='PyNotas',step=None):
        step=step or size*1.4
        rows=wrap(s,width,size,font)
        for row in rows:self.text(x,y,row,size,color,font);y+=step
        return y
    def svg(self,prefix):
        out=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.width} {self.height}" role="img" aria-labelledby="{prefix}-title">',f'<title id="{prefix}-title">{escape(self.title)}</title>', '<rect width="100%" height="100%" fill="white"/>']
        for op in self.ops:
            if op[0]=='rect':
                _,x,y,w,h,col,r=op;out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{col}"/>')
            elif op[0]=='circle':
                _,x,y,r,col=op;out.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{col}"/>')
            elif op[0]=='line':
                _,x,y,x2,y2,col,w=op;out.append(f'<line x1="{x}" y1="{y}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="{w}"/>')
            elif op[0]=='path':
                _,commands,stroke,fill,width=op
                data=' '.join(' '.join(map(str,command)) for command in commands)
                out.append(f'<path d="{data}" stroke="{stroke or "none"}" fill="{fill or "none"}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>')
            elif op[0]=='image':
                _,x,y,w,h,fig=op
                from .capture import raster
                fig=raster(fig.mime,fig.data)
                out.append(f'<image x="{x}" y="{y}" width="{w}" height="{h}" href="data:{fig.mime};base64,{fig.data}"/>')
            else:
                _,x,y,s,size,col,font=op
                family='DejaVu Sans Mono, monospace' if font=='PyNotasMono' else 'DejaVu Sans, Arial, sans-serif'
                weight='700' if font=='PyNotasBold' else '400'
                out.append(f'<text x="{x}" y="{y}" font-family="{family}" font-weight="{weight}" font-size="{size}" fill="{col}" xml:space="preserve">{escape(s)}</text>')
        return ''.join(out)+'</svg>'

class Document:
    def __init__(self,title,theme=None):
        from .artwork import THEMES
        self.theme=theme or THEMES['code']
        self.title=title;self.pages=[];self.y=0;self.section_number=0;self.section_anchor=None;self.new_page()
    @property
    def page(self):return self.pages[-1]
    def new_page(self):
        if len(self.pages)>=24:raise ValueError("La explicación necesita más de 24 páginas; divide la celda en pasos más pequeños.")
        p=Page(self.title);self.pages.append(p)
        first=len(self.pages)==1
        p.rect(0,0,WIDTH,HEIGHT,'#FBFAF6',0)
        p.rect(0,0,7,HEIGHT,self.theme.accent,0)
        p.text(32,28,'PyNotas',13,NAVY,'PyNotasBold')
        p.text(109,28,'/  CÓDIGO QUE SE ENTIENDE',7.3,MUTED,'PyNotasBold')
        p.text(494,28,'v'+__version__,8.5,self.theme.accent,'PyNotasBold')
        p.line(32,39,563,39,LINE,.8)
        if first:
            p.text(32,57,self.theme.label,8,self.theme.accent,'PyNotasBold')
            size=23;yy=84
            if len(wrap(self.title,531,size,'PyNotasBold'))>1 and fonts().stringWidth(self.title,'PyNotasBold',20)<=531:
                size=20
        else:
            size=14;yy=62
        for row in wrap(self.title,531,size,'PyNotasBold'):
            p.text(32,yy,row,size,NAVY,'PyNotasBold');yy+=size*1.2
        self.y=yy-5
    def hero(self,idea,keys,steps=(),resources=(),decision=None):
        from .artwork import draw
        rows=wrap(idea,503,10.4)
        height=len(rows)*14+20
        self.ensure(height+172)
        self.page.rect(32,self.y,3,height-6,self.theme.accent,1)
        for i,row in enumerate(rows):self.page.text(44,self.y+11+i*14,row,10.4,INK)
        self.y+=height+2
        self.y+=draw(self.page,32,self.y,531,self.theme,keys,steps,resources,decision)+13
    def ensure(self,h):
        if self.y+h>778:
            anchor=self.section_anchor
            carry=anchor and anchor[0]==len(self.pages) and abs(self.y-anchor[1])<.001
            if carry:
                _,_,start,title=anchor
                del self.page.ops[start:]
            self.section_anchor=None
            self.new_page()
            if carry:
                self.section_number-=1
                self.section(title)
    def section(self,title):
        self.ensure(70);self.section_number+=1
        start=len(self.page.ops)
        self.page.text(32,self.y+13,str(self.section_number).zfill(2),17,self.theme.accent,'PyNotasBold')
        self.page.text(63,self.y+12,title,10.5,NAVY,'PyNotasBold')
        end=63+fonts().stringWidth(title,'PyNotasBold',10.5)
        if end<543:self.page.line(end+12,self.y+9,563,self.y+9,LINE,.7)
        self.y+=24
        self.section_anchor=(len(self.pages),self.y,start,title)
    def paragraphs(self,text,size=10.5,color=INK):
        for row in wrap(text,531,size):
            self.ensure(size*1.4);self.page.text(32,self.y,row,size,color);self.y+=size*1.4
        self.y+=6
    def card(self,label,text,accent=False):
        rows=[(r,'PyNotasBold',self.theme.accent) for r in wrap(label,503,10,'PyNotasBold')]
        rows += [(r,'PyNotas',INK) for r in wrap(text,503,10)]
        while rows:
            self.ensure(66)
            count=max(1,int((778-self.y-24)/14))
            part,rows=rows[:count],rows[count:]
            h=24+len(part)*14
            self.page.rect(32,self.y,531,h,self.theme.light if accent else '#FFFFFF')
            for i,(row,font,color) in enumerate(part):self.page.text(46,self.y+19+i*14,row,10,color,font)
            self.y+=h+10
            if rows:self.new_page()
    def code(self,source):
        from .syntax import colored_lines
        self.section('El código que estás leyendo')
        items=[]
        for number,(line,colors) in enumerate(colored_lines(source),1):
            offset=0
            for i,row in enumerate(wrap(line,479,9.1,'PyNotasMono')):
                items.append((str(number) if i==0 else '↳',row,colors[offset:offset+len(row)]))
                offset+=len(row)
        if not items:self.paragraphs('No hay instrucciones Python para representar.');return
        while items:
            self.ensure(66)
            count=min(len(items),max(1,int((778-self.y-24)/14)))
            part,items=items[:count],items[count:]
            self.page.rect(32,self.y,531,len(part)*14+24,NAVY,9)
            self.page.rect(32,self.y,3,len(part)*14+24,self.theme.accent,1)
            for i,(n,row,colors) in enumerate(part):
                baseline=self.y+17+i*14
                self.page.text(42,baseline,n,8,'#AFC6CE','PyNotasMono')
                # Coalesce equally colored characters into positioned text runs.
                offset=0
                while offset<len(row):
                    color=colors[offset] if offset<len(colors) else '#F0F5F8'
                    end=offset+1
                    while end<len(row) and colors[end]==color:end+=1
                    x=76+fonts().stringWidth(row[:offset],'PyNotasMono',9.1)
                    self.page.text(x,baseline,row[offset:end],9.1,color,'PyNotasMono')
                    offset=end
            self.y+=len(part)*14+39
            if items:self.new_page();self.section('El código · continuación')

    def tiles(self,items,accent=False):
        """Editorial annotations, with full-width pagination for long content."""
        for offset in range(0,len(items),2):
            pair=items[offset:offset+2]
            width=531 if len(pair)==1 else 258
            inset=15 if accent else 20
            prepared=[(wrap(label,width-inset-10,9.3,'PyNotasBold'),wrap(text,width-inset-10,9.3)) for label,text in pair]
            heights=[(34 if accent else 20)+len(a)*12.5+len(b)*12.5 for a,b in prepared]
            if max(heights)>480:
                for label,text in pair:self.card(label,text,accent)
                continue
            h=max(heights)
            self.ensure(h+12)
            for i,(labels,rows) in enumerate(prepared):
                x=32+i*273
                if accent:
                    self.page.rect(x,self.y,width,h,self.theme.light,8)
                    self.page.rect(x+inset,self.y+11,25,2,self.theme.accent,1)
                    yy=self.y+26
                else:
                    self.page.circle(x+5,self.y+10,4,self.theme.accent)
                    self.page.line(x+5,self.y+20,x+5,self.y+h-5,LINE,1)
                    yy=self.y+13
                for row in labels:self.page.text(x+inset,yy,row,9.3,self.theme.accent,'PyNotasBold');yy+=12.5
                yy+=4
                for row in rows:self.page.text(x+inset,yy,row,9.3,INK);yy+=12.5
                if not accent:self.page.line(x+inset,self.y+h-1,x+width,self.y+h-1,LINE,.6)
            self.y+=h+9

    def flow(self,steps):
        if not steps:return
        self.section('El recorrido de los datos')
        for offset in range(0,len(steps),4):
            row=steps[offset:offset+4];w=(531-15*(len(row)-1))/len(row)
            wrapped=[wrap(s,w-18,9.5) for s in row];h=37+max(map(len,wrapped))*13
            self.ensure(h+16)
            for i,lines in enumerate(wrapped):
                x=32+i*(w+15);self.page.rect(x,self.y,w,h,PALE)
                self.page.text(x+9,self.y+14,f'{offset+i+1:02d}',7.5,TEAL,'PyNotasBold')
                for j,s in enumerate(lines):self.page.text(x+9,self.y+30+j*13,s,9.5,TEAL)
                if i<len(row)-1:self.page.arrow(x+w+2,self.y+h/2,x+w+13,self.y+h/2)
            self.y+=h+14
    def branch(self,condition):
        rows=wrap(condition,483,9.5,'PyNotasMono')
        h=50+len(rows)*14
        self.ensure(h+80)
        p=self.page;y=self.y
        p.rect(46,y,503,h,'#fff3e9')
        p.text(60,y+19,'CONDICIÓN · dos caminos posibles',10,'#95481f','PyNotasBold')
        for i,row in enumerate(rows):p.text(60,y+39+i*14,row,9.5,INK,'PyNotasMono')
        p.line(297,y+h,297,y+h+15,TEAL)
        p.line(162,y+h+15,430,y+h+15,TEAL)
        for x,label in [(162,'Verdadero: seguir rama sí'),(430,'Falso: seguir rama no')]:
            p.line(x,y+h+15,x,y+h+26,TEAL)
            p.rect(x-119,y+h+26,238,30,PALE)
            p.text(x-107,y+h+45,label,9.5,TEAL)
        self.y+=h+70

    def expression(self,expression):
        """Show operands feeding an operation, never as a sequence of operations."""
        self.section('Despiece · las partes de la expresión')
        children=expression.children
        if len(children)!=2:
            self.card(expression.label,expression.code);return
        rows=[wrap(c.code,220,9,'PyNotasMono') for c in children]
        bottom=wrap(expression.code,483,9,'PyNotasMono')
        h=28+max(map(len,rows))*13
        total=h+len(bottom)*13+75
        if total>550:
            self.card(expression.label,expression.code);return
        self.ensure(total)
        p=self.page;y=self.y
        for x,lines,label in zip((32,307),rows,('Parte izquierda','Parte derecha')):
            p.rect(x,y,256,h,PAPER);p.text(x+12,y+16,label,9,MUTED)
            for i,row in enumerate(lines):p.text(x+12,y+33+i*13,row,9,INK,'PyNotasMono')
            p.line(x+128,y+h,x+128,y+h+12,TEAL)
        p.line(160,y+h+12,435,y+h+12,TEAL)
        p.line(297,y+h+12,297,y+h+24,TEAL)
        p.line(294,y+h+20,297,y+h+24,TEAL);p.line(300,y+h+20,297,y+h+24,TEAL)
        p.rect(46,y+h+24,503,30+len(bottom)*13,PALE)
        p.text(60,y+h+40,expression.label,9,TEAL,'PyNotasBold')
        for i,row in enumerate(bottom):p.text(60,y+h+55+i*13,row,9,INK,'PyNotasMono')
        self.y+=total

    def footer(self):
        for i,p in enumerate(self.pages,1):
            p.line(32,799,563,799)
            p.text(32,815,'PyNotas '+__version__+'  /  APUNTES VISUALES DE PYTHON',7.6,self.theme.accent,'PyNotasBold')
            p.text(515,815,f'{i:02d} / {len(self.pages):02d}',8,self.theme.accent,'PyNotasBold')
            p.text(32,829,'Lectura local, sin volver a ejecutar. Resultados en la salida original de la celda.',7.2,MUTED)


def build_paginated(model,representation):
    from .lessons import LESSONS
    lesson=LESSONS.get(representation.lesson_key,LESSONS['generic'])
    theories=list(model.theories)
    title=theories[0].title if theories else lesson.title
    from .artwork import theme_for
    d=Document(title,theme_for(model,representation))
    from .analyzer import walk_blocks
    hero_decision=next((b for b in walk_blocks(model.blocks) if b.kind=='decision'),None) if d.theme.kind=='decision' else None
    d.hero(theories[0].idea if theories else lesson.idea,[t.key for t in theories],
           theories[0].steps if theories else (),
           [(r.qualified_name,r.access_name or r.binding) for b in model.blocks for r in b.resources],
           hero_decision)
    d.code(model.source)
    if not model.blocks:d.paragraphs('No hay instrucciones Python para representar.')
    if representation.format=='despiece' and not theories:
        focus=next((b.expression for b in reversed(model.blocks) if b.expression),None)
        if focus:d.expression(focus)
    elif theories:
        # Signals place the complete short route inside the illustration.
        # Other families keep the reviewed route as one typographic annotation.
        if d.theme.kind!='signal':
            d.paragraphs('Recorrido conceptual: '+' → '.join(theories[0].steps),8.8,d.theme.accent)
    elif model.blocks and lesson.incoming and d.theme.kind not in {'resources','decision'}:
        d.paragraphs('Recorrido conceptual: '+' → '.join((lesson.incoming,lesson.action,lesson.outgoing)),8.8,d.theme.accent)
    d.section('Paso a paso · qué hace Python')
    def explain(blocks,path='',pending=None):
        owns_pending=pending is None
        if pending is None:pending=[]
        def flush():
            if pending:d.tiles(pending);pending.clear()
        for b in blocks:
            trace=f'L{b.line}' if b.line==b.end_line else f'L{b.line}-{b.end_line}'
            body=' '.join(b.summaries) or b.explanation
            if b.resources:
                def resource_text(r):
                    # The opening already teaches this exact idea. Avoid printing
                    # the same paragraph twice, while retaining resource identity.
                    purpose=theories[0].title+'.' if theories and r.purpose==theories[0].idea else r.purpose
                    return r.qualified_name+': '+purpose+' Nombre de uso: '+(r.access_name or r.binding)+'.'
                body=' '.join(resource_text(r) for r in b.resources)
            pending.append(((path+' · ' if path else '')+trace+' · '+b.title,body))
            if b.kind=='decision':
                if b is not hero_decision:
                    flush();d.branch(b.code)
                explain(b.body,'Si es verdadero',pending);explain(b.alternative,'Si es falso',pending)
            for sec in b.sections:
                flush();d.section('Dentro de la estructura')
                d.paragraphs(sec.label,10,MUTED);explain(sec.blocks,pending=pending)
        if owns_pending:flush()
    explain(model.blocks)
    d.section('La teoría que da sentido al código')
    if theories:
        d.tiles([(t.title+' · L'+str(t.line), t.meaning if i==0 else t.idea+' '+t.meaning) for i,t in enumerate(theories)],True)
        d.paragraphs('Para profundizar · documentación de las operaciones:',8,MUTED)
        for t in theories:d.paragraphs(t.source,7.4,MUTED)
    else:
        d.tiles([('La idea, en simple',lesson.meaning)],True)
        if lesson.glossary:d.paragraphs(' · '.join(term+': '+meaning for term,meaning in lesson.glossary),9)
        if lesson.source:d.paragraphs('Referencia: '+lesson.source,7.4,MUTED)
    if model.objective!='Comprender cómo los datos se transforman en un resultado':d.card('Objetivo',model.objective)
    for note in model.notes:d.paragraphs(note,9,MUTED)
    d.paragraphs('Lectura estática: reconoce operaciones por su sintaxis; no verifica tipos, unidades, resultados ni caminos ejecutados.',8,MUTED)
    d.footer()
    return d


def build(model,representation):
    """US Letter pages, preserving legible type and every source instruction."""
    from .infographic import build as reading_build
    return reading_build(model,representation)
