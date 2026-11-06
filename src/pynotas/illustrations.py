"""Vector teaching illustrations. Conceptual, never presented as observed data."""
import math

TEAL, BLUE, GOLD, PALE, INK = '#007F83', '#4C63CB', '#CB703C', '#E9F4F1', '#193844'

def kind_for(keys):
    if set(keys)&{'mlp','sequential','dense','compile','nn_train','evaluate'}:return 'network'
    if set(keys)&{'rms','fft','frequency_axis','sine','peak','crest','std','variance','ptp','kurtosis'}:return 'signal'
    if set(keys)&{'split','train','scaling','pipeline','predict','linear','logistic','forest','pca','kmeans','accuracy','confusion','probability','mse','mae'}:return 'learning'
    return 'code'

def draw(p,x,y,w,h,kind):
    """Use existing drawing primitives so notebook and PDF are identical."""
    p.rect(x,y,w,h,'#EDF3F4',10)
    if kind=='network':
        layers=[[(x+27,y+v) for v in (32,52,72)],
                [(x+w/2,y+v) for v in (22,42,62,82)],
                [(x+w-27,y+v) for v in (40,64)]]
        for first,second in zip(layers,layers[1:]):
            for ax,ay in first:
                for bx,by in second:p.line(ax,ay,bx,by,'#C3D5D9',.7)
        for i,layer in enumerate(layers):
            for ax,ay in layer:
                p.circle(ax,ay,7,[TEAL,BLUE,GOLD][i]);p.circle(ax,ay,2,'#FFFFFF')
        for dx,label in [(10,'Entradas'),(w/2-15,'Capas'),(w-44,'Salidas')]:p.text(x+dx,y+h-9,label,7,INK)
    elif kind=='signal':
        p.line(x+13,y+46,x+w-12,y+46,'#CADCDD',.6)
        pts=[]
        for i in range(101):
            px=x+14+(w-28)*i/100
            py=y+44-18*math.sin(i/100*math.pi*6)
            pts.append((px,py))
        for a,b in zip(pts,pts[1:]):p.line(*a,*b,TEAL,1.8)
        for i in (13,46,79):p.circle(*pts[i],3.2,GOLD)
        p.text(x+13,y+17,'MUESTRAS DE UNA SEÑAL',7.5,TEAL,'PyNotasBold')
        for i,label in enumerate(['Datos','Cálculo','Indicador']):
            xx=x+10+i*(w-20)/3
            p.rect(xx,y+76,(w-28)/3,20,'#FFFFFF',4)
            p.text(xx+4,y+89,label,7.2,INK)
        # Decorative waveform illustrates the domain, not the user's sampled signal.
    elif kind=='learning':
        for j in range(4):
            for i in range(3):p.rect(x+13+i*11,y+29+j*11,8,8,TEAL if j<3 else GOLD,2)
        p.line(x+52,y+49,x+71,y+49,TEAL,1.2)
        p.line(x+71,y+32,x+71,y+78,TEAL,1.2)
        p.arrow(x+71,y+32,x+86,y+32)
        p.arrow(x+71,y+78,x+86,y+78)
        p.rect(x+88,y+19,w-98,27,'#DDE6F7',5)
        p.rect(x+88,y+65,w-98,27,'#F8E9DC',5)
        p.text(x+94,y+36,'Aprender',8,BLUE,'PyNotasBold')
        p.text(x+94,y+82,'Comprobar',8,'#8D491E','PyNotasBold')
        p.text(x+13,y+16,'EJEMPLOS',7,TEAL,'PyNotasBold')
    else:
        for i in range(3):
            p.rect(x+13,y+23+i*14,36,9,'#AFD4D1',3)
        p.arrow(x+55,y+46,x+77,y+46)
        p.rect(x+82,y+22,42,49,TEAL,7)
        p.text(x+89,y+51,'{ }',15,'#FFFFFF','PyNotasMono')
        p.arrow(x+128,y+46,x+w-24,y+46)
        p.circle(x+w-16,y+46,7,GOLD)
        p.text(x+13,y+h-14,'Datos → instrucciones → salida',7.2,INK)
