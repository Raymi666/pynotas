"""A single continuous source/explanation sheet, shared by HTML, PDF and JPG."""
from dataclasses import dataclass
from .layout import Page, wrap, fonts, NAVY, INK, MUTED, LINE
from .artwork import theme_for
from .lessons import LESSONS
from .syntax import colored_lines
from ._version import __version__

SHEET_WIDTH = 840
LEFT, RIGHT = 36, 804
CODE_X, CODE_WIDTH = 76, 350
TEXT_X, TEXT_WIDTH = 451, 341
PAPER = '#FCFBF7'


@dataclass
class ReadingDocument:
    title: str
    theme: object
    pages: list


def wrap_code(line,width):
    """Prefer spaces or punctuation over splitting a Python identifier in two."""
    rest=line
    while rest:
        first=wrap(rest,width,10,'PyNotasMono')[0]
        end=len(first)
        if end<len(rest):
            spaces=[i+1 for i,c in enumerate(first) if c.isspace() and i>len(first)//2]
            boundaries=[i+1 for i,c in enumerate(first) if c in ',.()[]{}:+-*/=' and i>len(first)//3]
            if spaces or boundaries:end=(spaces or boundaries)[-1]
        yield rest[:end]
        rest=rest[end:]


def code_rows(step):
    result=[]
    for i,(line,colors) in enumerate(colored_lines(step.code),step.line):
        # A blank separator is spacing, not a separate Python action.
        if not line.strip():continue
        offset=0
        for j,row in enumerate(wrap_code(line,CODE_WIDTH-48)):
            result.append((str(i) if j==0 else '↳',row,colors[offset:offset+len(row)]))
            offset+=len(row)
    return result


def build(model,representation):
    theme=theme_for(model,representation)
    lesson=LESSONS.get(representation.lesson_key,LESSONS['generic'])
    case=model.case
    title=case.title if case else (model.theories[0].title if model.theories else lesson.title)
    p=Page(title,width=SHEET_WIDTH)
    p.rect(0,0,SHEET_WIDTH,1,PAPER,0)  # Height filled in after measuring the content.
    p.rect(0,0,8,1,theme.accent,0)
    p.text(LEFT,34,'PyNotas',16,NAVY,'PyNotasBold')
    p.text(142,34,'PYTHON · LÍNEA A LÍNEA',9,theme.accent,'PyNotasBold')
    p.text(744,34,'v'+__version__,9,MUTED)
    p.line(LEFT,48,RIGHT,48,LINE)
    y=p.paragraph(LEFT,82,title,768,25,NAVY,'PyNotasBold',31)+1
    intro=case.idea if case else (model.theories[0].idea if model.theories else lesson.idea)
    y=p.paragraph(LEFT,y,intro,768,11,INK,step=16)+10
    # Compact map: it describes the idea, never claims an observed execution path.
    route=case.route if case else (model.theories[0].steps if model.theories else ())
    if route:
        count=len(route);w=(768-20*(count-1))/count
        lines=[wrap(s,w-30,10,'PyNotasBold') for s in route]
        h=24+max(map(len,lines))*14
        for i,rows in enumerate(lines):
            x=LEFT+i*(w+20)
            p.rect(x,y,w,h,theme.light,5)
            p.text(x+10,y+15,str(i+1).zfill(2),8,theme.accent,'PyNotasBold')
            for j,row in enumerate(rows):p.text(x+10,y+29+j*14,row,10,NAVY,'PyNotasBold')
            if i<count-1:p.arrow(x+w+4,y+h/2,x+w+16,y+h/2,theme.accent)
        y+=h+19
    p.text(LEFT,y,'PASO A PASO',11,theme.accent,'PyNotasBold')
    p.text(168,y,'Orden de lectura; las condiciones indican qué pasos pueden ejecutarse.',9,MUTED)
    y+=24
    p.text(CODE_X,y,'TU CÓDIGO · LÍNEAS ORIGINALES',8.5,MUTED,'PyNotasBold')
    p.text(TEXT_X,y,'QUÉ HACE Y PARA QUÉ SIRVE',8.5,MUTED,'PyNotasBold')
    y+=15
    previous_scope=()
    for index,step in enumerate(model.steps,1):
        if step.scope != previous_scope and not (step.kind=='clause' and not step.scope):
            scope=' / '.join(step.scope) if step.scope else 'Continúa fuera de la estructura anterior'
            scope_rows=wrap(scope,728,9,'PyNotasBold')
            h=15+len(scope_rows)*13
            p.rect(LEFT,y,768,h,theme.light,3)
            for j,row in enumerate(scope_rows):p.text(LEFT+12,y+16+j*13,row,9,theme.accent,'PyNotasBold')
            y+=h+10
        previous_scope=step.scope
        trace=f'L{step.line}' if step.line==step.end_line else f'L{step.line}-{step.end_line}'
        heading=wrap(step.title+' · '+trace,720,12,'PyNotasBold')
        p.circle(LEFT+12,y+7,12,theme.accent)
        label=f'{index:02d}'
        p.text(LEFT+12-fonts().stringWidth(label,'PyNotasBold',9)/2,y+10,label,9,'#FFFFFF','PyNotasBold')
        for j,row in enumerate(heading):p.text(CODE_X,y+11+j*16,row,12,NAVY,'PyNotasBold')
        y+=len(heading)*16+8
        rows=code_rows(step)
        details=[wrap(text,TEXT_WIDTH-18,10.5) for text in step.explanations]
        code_h=20+max(1,len(rows))*14
        text_h=4+sum(len(lines)*15+8 for lines in details)
        h=max(code_h,text_h)
        p.rect(CODE_X,y,CODE_WIDTH,code_h,NAVY,6)
        for j,(number,row,colors) in enumerate(rows):
            baseline=y+17+j*14
            p.text(CODE_X+9,baseline,number,8,'#AFC6CE','PyNotasMono')
            start=0
            while start<len(row):
                color=colors[start] if start<len(colors) else '#F0F5F8'
                end=start+1
                while end<len(row) and end<len(colors) and colors[end]==color:end+=1
                x=CODE_X+34+fonts().stringWidth(row[:start],'PyNotasMono',10)
                p.text(x,baseline,row[start:end],10,color,'PyNotasMono');start=end
        yy=y+12
        for j,lines in enumerate(details):
            p.circle(TEXT_X+3,yy-3,2,theme.accent)
            for line in lines:
                p.text(TEXT_X+14,yy,line,10.5,INK);yy+=15
            yy+=8
        p.line(LEFT+12,y,LEFT+12,y+h,LINE,1)
        y+=h+14
        p.line(CODE_X,y,RIGHT,y,LINE,.6)
        y+=18
    if not model.steps:
        y=p.paragraph(LEFT,y,'No hay instrucciones Python para explicar. Los comentarios son notas para quien lee el código.',768,11)+10
        if model.source.strip():
            y=p.paragraph(LEFT,y,model.source,768,10,MUTED,'PyNotasMono')+10
    p.text(LEFT,y+5,'LA IDEA DEL CASO',11,theme.accent,'PyNotasBold');y+=23
    facts=[];sources=[]
    if case:
        facts.extend(case.facts);sources.extend(case.sources)
    if model.theories:
        for t in model.theories:
            facts.append(t.title+' · L'+str(t.line)+': '+(t.meaning if t==model.theories[0] and not case else t.idea+' '+t.meaning))
            sources.append(t.source)
    elif not case:
        facts.append(lesson.meaning)
        if lesson.glossary:facts.append(' · '.join(term+': '+meaning for term,meaning in lesson.glossary))
        if lesson.source:sources.append(lesson.source)
    for fact in facts:
        rows=wrap(fact,726,10.5)
        h=18+len(rows)*15
        p.rect(LEFT,y,768,h,theme.light,4)
        p.rect(LEFT,y,3,h,theme.accent,1)
        for j,row in enumerate(rows):p.text(LEFT+16,y+17+j*15,row,10.5,INK)
        y+=h+6
    if model.objective!='Comprender cómo los datos se transforman en un resultado':
        y=p.paragraph(LEFT,y+14,'Objetivo: '+model.objective,768,10)+10
    if sources:
        y+=12
        p.text(LEFT,y,'Referencia de las operaciones',8,MUTED,'PyNotasBold');y+=13
        for source in dict.fromkeys(sources):y=p.paragraph(LEFT,y,source,768,8,MUTED,step=11)
    y+=20
    p.line(LEFT,y,RIGHT,y,LINE)
    p.text(LEFT,y+17,'Una celda · una lámina · código y explicación juntos',9,theme.accent,'PyNotasBold')
    y=p.paragraph(LEFT,y+34,'Lectura del código, sin volver a ejecutarlo. No verifica valores ni caminos ejecutados. Resultados en la salida original.',768,8,MUTED,step=11)
    p.height=max(430,y+18)
    if p.height>12000:
        raise ValueError('La lámina es demasiado larga para descargarla con letra legible. Divide esta celda en tareas más pequeñas.')
    p.ops[0]=('rect',0,0,SHEET_WIDTH,p.height,PAPER,0)
    p.ops[1]=('rect',0,0,8,p.height,theme.accent,0)
    return ReadingDocument(title,theme,[p])
