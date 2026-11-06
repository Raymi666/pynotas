"""An adaptive Letter infographic, shared by the notebook, PDF and JPG."""
from .layout import Page,wrap,fonts
from .reading_layout import ReadingDocument
from .artwork import theme_for
from .syntax import colored_lines
from ._version import __version__

W,H,M,GAP,BOTTOM=612,792,24,12,746
INK='#12324F';MUTED='#52667D';NAVY='#103B65'
PALETTES=[('#E5F2FF','#1C65A1'),('#E6F5EA','#247552'),('#FFF4CF','#936515'),
          ('#FBE7EE','#A83E65'),('#EEE9FC','#6850A2'),('#DDF5F1','#16796E')]
CODE_SIZE=8.4


def icon(p,x,y,kind,c):
    """Small vector signs that explain the task, never fake measured values."""
    if kind in {'plot','measure','sort'}:
        p.line(x,y+19,x+25,y+19,c,1)
        for i,h in enumerate((8,17,12) if kind!='sort' else (17,12,8)):
            p.rect(x+3+i*8,y+18-h,5,h,c,1)
    elif kind=='group':
        for row in range(3):
            for col in range(2):p.circle(x+3+col*6,y+4+row*6,1.8,c)
        p.arrow(x+13,y+10,x+23,y+10,c);p.rect(x+25,y+2,5,17,c,1)
    elif kind in {'canvas','style'}:
        p.path([('M',x,y+2),('L',x+26,y+2),('L',x+26,y+20),('L',x,y+20),('Z',)],c,None,1.2)
        p.line(x+5,y+15,x+10,y+9,c,1.2);p.line(x+10,y+9,x+18,y+12,c,1.2)
    else:
        p.text(x,y+17,'{ }',16,c,'PyNotasMono')


def source_rows(stage,width):
    rows=[]
    for step in stage.steps:
        for i,(line,colors) in enumerate(colored_lines(step.code),step.line):
            if not line.strip():continue
            offset=0;rest=line
            while rest:
                row=wrap(rest,width-43,CODE_SIZE,'PyNotasMono')[0]
                if len(row)<len(rest):
                    boundaries=[j+1 for j,c in enumerate(row) if c in ' ,.(=[]):' and j>len(row)//3]
                    if boundaries:row=row[:boundaries[-1]]
                rows.append((str(i) if offset==0 else '↳',row,colors[offset:offset+len(row)]))
                offset+=len(row);rest=rest[len(row):]
    return rows


def plan(stage,width):
    title=wrap(stage.title,width-92,11,'PyNotasBold')
    summary=wrap(stage.summary,width-24,10)
    scope_text=' / '.join(stage.steps[0].scope).replace('Si es verdadero · ','Si se cumple: ').replace('Si es falso · ','Si no se cumple: ')
    scope=wrap(scope_text,width-24,8.5,'PyNotasBold') if scope_text else []
    rows=source_rows(stage,width-20)
    details=[wrap(detail,width-35,9.2) for detail in stage.details]
    tip=wrap(stage.tip,width-36,9) if stage.tip else []
    height=36+len(title)*13+len(summary)*13+len(scope)*11+12+len(rows)*10.5+12
    if details:height+=19+sum(len(d)*12+4 for d in details)
    if tip:height+=len(tip)*12+12
    return dict(title=title,summary=summary,scope=scope,code=rows,details=details,tip=tip,height=height)


def draw_card(p,x,y,w,stage,index,design):
    pale,accent=PALETTES[(index-1)%len(PALETTES)]
    p.rect(x,y,w,design['height'],pale,9)
    p.circle(x+21,y+23,12,accent)
    label=str(index);p.text(x+21-fonts().stringWidth(label,'PyNotasBold',13)/2,y+27.5,label,13,'#FFFFFF','PyNotasBold')
    icon(p,x+w-39,y+19,stage.kind,accent)
    yy=y+22
    for row in design['title']:p.text(x+40,yy,row,11,INK,'PyNotasBold');yy+=13
    trace=f'L{stage.steps[0].line}'
    if stage.steps[-1].end_line!=stage.steps[0].line:trace+='–'+str(stage.steps[-1].end_line)
    p.text(x+w-12-fonts().stringWidth(trace,'PyNotas',7.2),y+10,trace,7.2,accent)
    yy=max(y+50,yy+15)
    for row in design['scope']:p.text(x+12,yy,row,8.5,accent,'PyNotasBold');yy+=11
    for row in design['summary']:p.text(x+12,yy,row,10,INK);yy+=13
    yy+=3
    p.rect(x+10,yy,w-20,len(design['code'])*10.5+12,'#FFFFFF',4)
    yy+=12
    # Remap the dark-editor palette to ink on paper without losing syntax detail.
    colors={'#CDBFF9':'#7543B2','#B5E7CA':'#23734B','#F8CF88':'#8A570C','#ACBEC7':'#52667D'}
    for number,row,tones in design['code']:
        p.text(x+14,yy,number,6.8,MUTED,'PyNotasMono')
        start=0
        while start<len(row):
            tone=tones[start] if start<len(tones) else ''
            end=start+1
            while end<len(row) and end<len(tones) and tones[end]==tone:end+=1
            p.text(x+31+fonts().stringWidth(row[:start],'PyNotasMono',CODE_SIZE),yy,row[start:end],CODE_SIZE,colors.get(tone,INK),'PyNotasMono')
            start=end
        yy+=10.5
    yy+=8
    if design['details']:
        p.text(x+12,yy+4,'QUÉ SIGNIFICA CADA PARTE',7.5,accent,'PyNotasBold');yy+=19
        for lines in design['details']:
            p.circle(x+14,yy-3,1.6,accent)
            for line in lines:p.text(x+22,yy,line,9.2,INK);yy+=12
            yy+=4
    if design['tip']:
        p.line(x+12,yy-2,x+w-12,yy-2,accent,.4);yy+=10
        for line in design['tip']:p.text(x+18,yy,line,9,accent);yy+=12
    return yy


class Builder:
    def __init__(self,model,rep):
        self.model=model;self.rep=rep;self.pages=[];self.theme=theme_for(model,rep)
        self.practice_slot=None
        self.title=model.case.title if model.case else 'Entiende lo que hace tu código'
        if any(s.kind=='group' for s in model.stages):self.title='De una tabla a un resumen visual' if any(s.kind=='plot' for s in model.stages) else 'Agrupar, calcular y ordenar datos'
        self.new_page()

    @property
    def page(self):return self.pages[-1]

    def new_page(self):
        if len(self.pages)>=24:raise ValueError('La lámina supera 24 páginas. Divide la celda en tareas.')
        p=Page(self.title,width=W,height=H);self.pages.append(p)
        p.rect(0,0,W,H,'#FFFFFF',0)
        p.rect(M,18,W-2*M,67,NAVY,10)
        p.text(M+16,43,'PyNotas',21,'#FFFFFF','PyNotasBold')
        p.text(M+125,43,'Python CheatSheet',18,'#FFCF55','PyNotasBold')
        title_lines=wrap(self.title,500,11,'PyNotasBold')
        yy=63
        for row in title_lines:p.text(M+16,yy,row,11,'#E7F2FC','PyNotasBold');yy+=13
        self.y=max(95,yy+15)
        p.text(M,self.y,'VAMOS LÍNEA A LÍNEA · PASO A PASO',8.5,NAVY,'PyNotasBold')
        p.text(438,self.y,'CARTA / v'+__version__,8,MUTED)
        self.y+=17

    def ensure(self,height):
        if self.y+height>BOTTOM:self.new_page()

    def cards(self):
        stages=self.model.stages;i=0;half=(W-2*M-GAP)/2
        while i<len(stages):
            a=plan(stages[i],half)
            b=plan(stages[i+1],half) if i+1<len(stages) else None
            if a['height']>470 or (b and b['height']>470):
                a=plan(stages[i],W-2*M)
                self.ensure(a['height'])
                draw_card(self.page,M,self.y,W-2*M,stages[i],i+1,a)
                self.y+=a['height']+GAP;i+=1
            else:
                height=max(a['height'],b['height'] if b else 0)
                beside_practice = b is None and not self.model.figures and not self.model.capture_notes
                if beside_practice:
                    height=max(height,112)
                self.ensure(height)
                draw_card(self.page,M,self.y,half,stages[i],i+1,a)
                if b:draw_card(self.page,M+half+GAP,self.y,half,stages[i+1],i+2,b)
                if beside_practice:
                    self.practice_slot=(self.page,M+half+GAP,self.y,half)
                self.y+=height+GAP;i+=2 if b else 1

    def results(self):
        for i,figure in enumerate(self.model.figures,1):
            remaining=BOTTOM-self.y-56-70
            max_height=min(210,remaining) if remaining>=110 else 210
            scale=min((W-2*M-24)/figure.width,max_height/figure.height)
            w,h=figure.width*scale,figure.height*scale
            self.ensure(h+56)
            p=self.page;y=self.y
            p.rect(M,y,W-2*M,h+48,'#EDF4FB',9)
            p.text(M+12,y+18,'RESULTADO REAL DE TU CELDA'+(f' · {i}' if len(self.model.figures)>1 else ''),9,NAVY,'PyNotasBold')
            p.image((W-w)/2,y+26,w,h,figure)
            p.text(M+12,y+h+40,'Imagen ya mostrada por Python; incorporada sin repetir el cálculo.',7.8,MUTED)
            self.y+=h+60
        for note in self.model.capture_notes:
            lines=wrap(note,W-2*M,8.5);self.ensure(len(lines)*12+8)
            for line in lines:self.page.text(M,self.y+9,line,8.5,MUTED);self.y+=12

    def practice(self):
        text='Cambia una opción o un dato. Predice qué cambiará y ejecuta de nuevo para comprobarlo.'
        if any(s.kind=='sort' and any('ascending=False' in d for d in s.details) for s in self.model.stages):text='Cambia ascending=False por True. ¿Qué categoría debería aparecer primero? Compruébalo.'
        if self.practice_slot:
            p,x,y,width=self.practice_slot
        else:
            self.ensure(65)
            p,x,y,width=self.page,M,self.y,W-2*M
        lines=wrap(text,width-68,9.5)
        height=max(60,42+len(lines)*12)
        p.rect(x,y,width,height,'#FFF5D8',8)
        icon(p,x+12,y+17,'tools','#997117')
        p.text(x+52,y+18,'AHORA TE TOCA A TI',9,INK,'PyNotasBold')
        for j,line in enumerate(lines):p.text(x+52,y+34+j*12,line,9.5,INK)
        if not self.practice_slot:self.y+=height+10

    def finish(self):
        for i,p in enumerate(self.pages,1):
            p.line(M,759,W-M,759,'#D7E5EE')
            p.text(M,773,'PyNotas · Aprende Python leyendo tus propios pasos',7.6,NAVY,'PyNotasBold')
            p.text(528,773,f'{i} / {len(self.pages)}',8,MUTED)
            p.text(M,785,'Lectura sin repetir cálculos. Conserva la salida original. Carta 21,59 × 27,94 cm.',7,MUTED)
        return ReadingDocument(self.title,self.theme,self.pages)


def build(model,representation):
    # Very long individual tasks keep the proven line-by-line paginator, at full
    # width. Never truncate source or shrink it to squeeze into a small card.
    if not model.stages or any(plan(s,W-2*M)['height']>610 for s in model.stages):
        from dataclasses import replace
        from .letter_layout import build as long_build
        steps=[]
        for stage in model.stages:
            first=replace(stage.steps[0],brief=' '.join((stage.summary,)+stage.details),aside=stage.tip)
            steps.extend((first,)+stage.steps[1:])
        doc=long_build(replace(model,steps=tuple(steps) or model.steps),representation)
        if not model.figures and not model.capture_notes:return doc
        b=Builder(model,representation);b.results();b.practice()
        extra=b.finish();doc.pages.extend(extra.pages)
        # Consistent total pagination also on the original long-source pages.
        for i,p in enumerate(doc.pages,1):
            p.rect(514,760,74,16,'#FFFFFF',0);p.text(528,773,f'{i} / {len(doc.pages)}',8,MUTED)
        return doc
    b=Builder(model,representation);b.cards();b.results();b.practice()
    if model.objective!='Comprender cómo los datos se transforman en un resultado':
        lines=wrap('Objetivo: '+model.objective,W-2*M,9)
        for line in lines:b.ensure(13);b.page.text(M,b.y+9,line,9,INK);b.y+=13
    return b.finish()
