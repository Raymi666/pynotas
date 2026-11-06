"""Code-native SVG sheets: a small concept, a process and the actual instructions."""
from html import escape
import textwrap
from .model import is_preparation

NAVY, TEAL, MUTED = '#112f42', '#00796f', '#4b6371'

class Canvas:
    def __init__(self):
        self.items = []
    def rect(self,x,y,w,h,fill,stroke='none',r=16):
        self.items.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}"/>')
    def text(self,x,y,s,size=22,color=NAVY,bold=False,mono=False):
        font='monospace' if mono else 'Arial, sans-serif'
        self.items.append(f'<text x="{x}" y="{y}" xml:space="preserve" font-family="{font}" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color}">{escape(str(s))}</text>')
    def paragraph(self,x,y,s,width=88,size=22,color=MUTED,step=30):
        rows=textwrap.wrap(s,width,break_long_words=True,break_on_hyphens=False) or ['']
        for i,row in enumerate(rows): self.text(x,y+i*step,row,size,color)
        return y + len(rows)*step
    def arrow(self,x,y,prefix):
        self.items.append(f'<path d="M{x},{y} h34" stroke="{TEAL}" stroke-width="3" fill="none" marker-end="url(#{prefix}-arrow)"/>')
    def svg(self,height,title,prefix):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 {height}" role="img" aria-labelledby="{prefix}-title">'
                f'<title id="{prefix}-title">{escape(title)}</title>'
                '<desc>Explicación del código. No muestra valores calculados ni una rama observada.</desc>'
                f'<defs><marker id="{prefix}-arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="{TEAL}"/></marker></defs>'
                + f'<rect width="1200" height="{height}" fill="#f4f7f6"/>' + ''.join(self.items) + '</svg>')

def line_label(block):
    return f'L{block.line}' if block.line == block.end_line else f'L{block.line}–{block.end_line}'

def focus_blocks(model, lesson):
    # Show a bounded reading; retain all statements in the source and full graph.
    blocks=[b for b in model.blocks if b.kind != 'import']
    if lesson.key in {'scale','scale_fit'}:
        focused=[b for b in blocks if set(b.topics) & {'scale','scale_fit'}]
        remaining=[b for b in blocks if b not in focused]
        blocks=focused + remaining[-1:]
    return blocks[:4]

def sheet_svg(model, lesson, prefix):
    c=Canvas()
    header_height=170 if len(textwrap.wrap(lesson.title,43)) == 1 else 220
    c.rect(0,0,1200,header_height,NAVY,r=0)
    c.text(48,44,'PyNotas  /  PYTHON PASO A PASO',17,'#85ded0',True)
    y=c.paragraph(48,100,lesson.title,43,42,'white',49)
    c.text(48,header_height-22,'Una explicación del código y de la idea que hay detrás.',21,'#cfe0e6')
    c.text(48,header_height+45,'La idea, en simple',27,NAVY,True)
    y=c.paragraph(48,header_height+86,lesson.idea,91)+24
    if is_preparation(model):
        resources=[(r,b) for b in model.blocks for r in b.resources]
        for start in range(0,len(resources),2):
            row=resources[start:start+2]
            height=max(102+29*len(textwrap.wrap(r.qualified_name,35))+28*len(textwrap.wrap(r.purpose,42))+25*len(textwrap.wrap('Nombre de uso: '+(r.access_name or r.binding),43)) for r,b in row)
            for i,(r,b) in enumerate(row):
                x=48+i*565
                c.rect(x,y,539,height,'white','#d7e4e1')
                yy=c.paragraph(x+24,y+37,r.qualified_name,35,24,TEAL,29)
                yy=c.paragraph(x+24,yy+12,r.purpose,42,21,NAVY,28)
                yy=c.paragraph(x+24,yy+14,'Nombre de uso: '+(r.access_name or r.binding),43,18,MUTED,25)
                c.text(x+455,y+height-15,line_label(b),15,MUTED)
            y+=height+18
        for b in model.blocks:
            if b.kind=='setup':
                c.text(48,y+25,b.title,25,NAVY,True)
                y=c.paragraph(48,y+62,' '.join(b.summaries),90)+18
    else:
        if model.blocks:
            c.text(48,y+16,'Datos que se usan',23,NAVY,True)
            c.text(426,y+16,'Lo que hace Python',23,NAVY,True)
            c.text(804,y+16,'Lo que se obtiene',23,NAVY,True)
            y+=40
            for x,body,fill in [(48,lesson.incoming,'white'),(426,lesson.action,'#e2f0ec'),(804,lesson.outgoing,'#fff0dd')]:
                c.rect(x,y,348,154,fill,'#d7e4e1')
                c.paragraph(x+24,y+43,body,25,25,NAVY,34)
            c.arrow(394,y+77,prefix); c.arrow(772,y+77,prefix)
            y+=184
        else:
            y=c.paragraph(48,y+10,'No hay instrucciones Python para representar.')+15
        if lesson.key != 'decision' and model.blocks:
            c.text(48,y+17,'Así se lo pedimos a Python',27,NAVY,True)
            y+=43
            for b in focus_blocks(model,lesson):
                title_rows=textwrap.wrap(b.title,35)
                summary=' '.join(b.summaries) or b.explanation
                summary_rows=textwrap.wrap(summary,46)
                # Exact source prefix, never reformulate semantics in the code column.
                full_rows=[part for line in b.code.splitlines() for part in (textwrap.wrap(line,47,replace_whitespace=False) or [''])]
                code_rows=full_rows[:3]
                if len(full_rows)>3:code_rows[-1]=code_rows[-1][:43]+' …'
                height=max(64+len(title_rows)*29+len(summary_rows)*25,58+len(code_rows)*25)
                c.rect(48,y,1104,height,'white','#d7e4e1')
                yy=y+34
                for t in title_rows:c.text(70,yy,t,23,NAVY,True);yy+=29
                for t in summary_rows:c.text(70,yy+4,t,20,MUTED);yy+=25
                for i,t in enumerate(code_rows):c.text(636,y+38+i*25,t,17,TEAL,mono=True)
                c.text(1060,y+height-14,line_label(b),15,MUTED)
                y+=height+12
            omitted=len([b for b in model.blocks if b.kind!='import'])-len(focus_blocks(model,lesson))
            if omitted>0:
                y=c.paragraph(48,y+18,f'{omitted} paso(s) adicional(es) en «Ver todos los pasos y su código».',93,18)+8
    y+=12
    meaning_rows=textwrap.wrap(lesson.meaning,87)
    c.rect(48,y,1104,92+len(meaning_rows)*30,NAVY)
    c.text(72,y+39,'¿Cómo entenderlo?',27,'white',True)
    c.paragraph(72,y+78,lesson.meaning,87,23,'white')
    y+=117+len(meaning_rows)*30
    c.text(48,y,'Los valores calculados se consultan en la salida original de la celda.',18,MUTED)
    return c.svg(y+30,lesson.title,prefix)
