"""Letter pages that give the teacher's explanation priority over code and theory."""
from .layout import Page,wrap,fonts,NAVY,INK,MUTED,LINE
from .reading_layout import ReadingDocument
from .artwork import theme_for
from ._version import __version__

WIDTH,HEIGHT=612,792
MARGIN,END,BOTTOM=26,586,742
CODE_X,CODE_WIDTH=51,535
TEXT_X,TEXT_WIDTH=51,529
PAPER='#FCFBF7'


def code_rows(step):
    rows=[]
    for number,(line,colors) in enumerate(colored_lines(step.code),step.line):
        if not line.strip():continue
        offset=0;rest=line
        while rest:
            part=wrap(rest,CODE_WIDTH-37,8.7,'PyNotasMono')[0]
            end=len(part)
            if end<len(rest):
                positions=[i+1 for i,c in enumerate(part) if c.isspace() and i>len(part)//2]
                if not positions:positions=[i+1 for i,c in enumerate(part) if c in ',.()[]{}:+-*/=' and i>len(part)//3]
                if positions:end=positions[-1]
            rows.append((str(number) if offset==0 else '↳',rest[:end],colors[offset:offset+end]))
            rest=rest[end:];offset+=end
    return rows


from .syntax import colored_lines


class LetterBuilder:
    def __init__(self,title,theme):
        self.title=title;self.theme=theme;self.pages=[];self.y=0
        self.new_page()

    @property
    def page(self):return self.pages[-1]

    def new_page(self):
        if len(self.pages)>=24:raise ValueError('La explicación necesita más de 24 hojas carta. Divide la celda en tareas.')
        p=Page(self.title,width=WIDTH,height=HEIGHT);self.pages.append(p)
        p.rect(0,0,WIDTH,HEIGHT,PAPER,0);p.rect(0,0,5,HEIGHT,self.theme.accent,0)
        p.text(MARGIN,29,'PyNotas',13,NAVY,'PyNotasBold')
        p.text(119,29,'PYTHON PASO A PASO',8,self.theme.accent,'PyNotasBold')
        p.text(459,29,'CARTA · v'+__version__,8,MUTED)
        p.line(MARGIN,39,END,39,LINE)
        size=18 if len(self.pages)==1 else 12
        self.y=p.paragraph(MARGIN,61,self.title,560,size,NAVY,'PyNotasBold',size*1.2)+5

    def ensure(self,height):
        if self.y+height>BOTTOM:self.new_page()

    def paragraph(self,text,size=9,color=INK):
        for row in wrap(text,560,size):
            self.ensure(size*1.35)
            self.page.text(MARGIN,self.y+size,row,size,color);self.y+=size*1.35
        self.y+=5

    def headings(self):
        self.ensure(23)
        self.page.text(MARGIN,self.y+9,'VAMOS LÍNEA A LÍNEA',8.5,self.theme.accent,'PyNotasBold')
        self.page.text(170,self.y+9,'Qué hacemos · con qué datos · dónde queda',8,MUTED)
        self.y+=23

    def step(self,step,index):
        code=code_rows(step)
        # Content is a single ordered stream. Pagination never shrinks type or
        # lets a second column run ahead of the matching explanation.
        content=[('detail',row) for row in wrap(step.brief or ' '.join(step.explanations),TEXT_WIDTH,11)]
        content += [('aside',row) for row in wrap(step.aside,TEXT_WIDTH-15,9.5)] if step.aside else []
        content += [('code',row) for row in code]
        spacing={'detail':14.5,'aside':13,'code':11}
        scope=' / '.join(step.scope).replace('Si es verdadero · ','Si se cumple: ').replace('Si es falso · ','Si no se cumple: ')
        scope_lines=wrap(scope,TEXT_WIDTH,8,'PyNotasBold') if scope else []
        trace=f'L{step.line}' if step.line==step.end_line else f'L{step.line}-{step.end_line}'
        heading=wrap(step.title+' · '+trace,TEXT_WIDTH,10,'PyNotasBold')
        header_h=14*len(heading)+10*len(scope_lines)+5
        if header_h>550:raise ValueError('Esta instrucción tiene demasiados niveles o un nombre demasiado largo. Divide la celda en tareas.')
        while content:
            full_h=header_h+sum(spacing[k] for k,_ in content)+25
            if self.y+full_h>BOTTOM and full_h<BOTTOM-125:
                self.new_page();self.headings()
            if self.y+header_h+45>BOTTOM:
                self.new_page();self.headings()
            capacity=BOTTOM-self.y-header_h-25
            count=0;used=0
            for kind,_ in content:
                if used+spacing[kind]>capacity:break
                count+=1;used+=spacing[kind]
            part,content=content[:count],content[count:]
            p=self.page;y=self.y
            p.circle(34,y+5,8,self.theme.accent)
            label=f'{index:02d}';p.text(34-fonts().stringWidth(label,'PyNotasBold',7)/2,y+7.5,label,7,'#FFFFFF','PyNotasBold')
            for row in heading:p.text(TEXT_X,y+8,row,10,NAVY,'PyNotasBold');y+=14
            for row in scope_lines:p.text(TEXT_X,y+4,row,8,self.theme.accent,'PyNotasBold');y+=10
            y=self.y+header_h
            cr=[row for kind,row in part if kind=='code']
            for kind,row in part:
                if kind=='detail':p.text(TEXT_X,y+11,row,11,INK);y+=14.5
                elif kind=='aside':
                    p.text(TEXT_X+9,y+10,row,9.5,self.theme.accent);y+=13
            if cr:
                y+=5
                p.rect(CODE_X,y,CODE_WIDTH,len(cr)*11+8,NAVY,3)
                for j,(number,row,colors) in enumerate(cr):
                    yy=y+12+j*11;p.text(CODE_X+6,yy,number,7,'#AFC6CE','PyNotasMono')
                    start=0
                    while start<len(row):
                        color=colors[start] if start<len(colors) else '#EFF5F8';end=start+1
                        while end<len(row) and end<len(colors) and colors[end]==color:end+=1
                        x=CODE_X+26+fonts().stringWidth(row[:start],'PyNotasMono',8.7)
                        p.text(x,yy,row[start:end],8.7,color,'PyNotasMono');start=end
                y+=len(cr)*11+8
            self.y=y+10
            p.line(CODE_X,self.y-2,END,self.y-2,LINE,.5)
            if content:
                self.new_page();self.headings()
                heading=wrap(step.title+' · '+trace+' · continuación',TEXT_WIDTH,10,'PyNotasBold')
                header_h=14*len(heading)+10*len(scope_lines)+5

    def finish(self):
        for i,p in enumerate(self.pages,1):
            p.line(MARGIN,756,END,756,LINE)
            p.text(MARGIN,769,'PyNotas · CARTA 21,59 × 27,94 cm',7.3,self.theme.accent,'PyNotasBold')
            p.text(522,769,f'{i} / {len(self.pages)}',7.5,MUTED)
            p.text(MARGIN,782,'Leemos el código sin ejecutarlo otra vez. El resultado real está en la salida original de tu celda.',7,MUTED)
        return ReadingDocument(self.title,self.theme,self.pages)


def build(model,representation):
    title=model.case.title if model.case else 'Entendamos tu código, paso a paso'
    b=LetterBuilder(title,theme_for(model,representation))
    b.headings()
    for i,step in enumerate(model.steps,1):b.step(step,i)
    if not model.steps:b.paragraph('No hay instrucciones Python para explicar. '+model.source)
    if model.objective!='Comprender cómo los datos se transforman en un resultado':
        b.paragraph('Objetivo: '+model.objective,9)
    # Domain catalogs remain in the model for other consumers. The student sheet
    # concentrates on learning to program; no speculative theory is inserted.
    return b.finish()
