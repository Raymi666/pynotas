"""In-memory local PDF/JPG export of the shared layout, never of executed code."""
import io
import math
import threading
from pathlib import Path
from .layout import HEIGHT, WIDTH, fonts

_RENDER_LOCK = threading.RLock()  # PDFium must not run simultaneously across threads.


def pdf_bytes(document):
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.lib.colors import HexColor
    fonts()
    stream=io.BytesIO()
    c=Canvas(stream,pagesize=(WIDTH,HEIGHT),pageCompression=1,invariant=1)
    c.setTitle('PyNotas · '+document.title);c.setAuthor('PyNotas')
    for page in document.pages:
        height = page.height
        c.setPageSize((page.width, height))
        for op in page.ops:
            if op[0]=='rect':
                _,x,y,w,h,col,r=op;c.setFillColor(HexColor(col));c.roundRect(x,height-y-h,w,h,r,fill=1,stroke=0)
            elif op[0]=='circle':
                _,x,y,r,col=op;c.setFillColor(HexColor(col));c.circle(x,height-y,r,fill=1,stroke=0)
            elif op[0]=='line':
                _,x,y,x2,y2,col,w=op;c.setStrokeColor(HexColor(col));c.setLineWidth(w);c.line(x,height-y,x2,height-y2)
            elif op[0]=='path':
                _,commands,stroke,fill,width=op
                path=c.beginPath()
                for command in commands:
                    kind,*v=command
                    if kind=='M':path.moveTo(v[0],height-v[1])
                    elif kind=='L':path.lineTo(v[0],height-v[1])
                    elif kind=='C':path.curveTo(v[0],height-v[1],v[2],height-v[3],v[4],height-v[5])
                    elif kind=='Z':path.close()
                if stroke:c.setStrokeColor(HexColor(stroke))
                if fill:c.setFillColor(HexColor(fill))
                c.setLineWidth(width)
                c.drawPath(path,stroke=int(bool(stroke)),fill=int(bool(fill)))
            elif op[0]=='image':
                import base64
                from reportlab.lib.utils import ImageReader
                from .capture import raster
                _,x,y,w,h,fig=op
                fig=raster(fig.mime,fig.data)
                c.drawImage(ImageReader(io.BytesIO(base64.b64decode(fig.data))),x,height-y-h,w,h,mask='auto')
            else:
                _,x,y,s,size,col,font=op;c.setFillColor(HexColor(col));c.setFont(font,size);c.drawString(x,height-y,s)
        c.showPage()
    c.save();return stream.getvalue()


def jpg_pages(pdf,dpi=300):
    if not isinstance(dpi,int) or isinstance(dpi,bool) or not 96<=dpi<=400:
        raise ValueError('La resolución debe ser un entero entre 96 y 400 ppp.')
    import pypdfium2 as pdfium
    result=[]
    with _RENDER_LOCK, pdfium.PdfDocument(pdf) as doc:
        for index in range(len(doc)):
            page=doc[index]
            scale=dpi/72
            width,height=page.get_size()
            if width*height*scale*scale>80_000_000 or max(width,height)*scale>65000:
                raise ValueError("La imagen sería demasiado grande. Reduce dpi al exportar o divide la celda; no se corta la lámina.")
            # Avoid a spurious extra row when an exact physical page size lands
            # just above an integer due to floating-point multiplication.
            bitmap=page.render(scale=math.nextafter(scale,0.0))
            image=bitmap.to_pil()
            stream=io.BytesIO()
            image.convert('RGB').save(stream,format='JPEG',quality=95,subsampling=0,dpi=(dpi,dpi))
            result.append(stream.getvalue())
            image.close();bitmap.close();page.close()
    return result


def exportar(codigo,destino,*,formato=None,sobrescribir=False,dpi=300,**opciones):
    """Export source text or the last successful sheet with codigo=None.

    PDF returns one Path; JPG returns one Path per Letter page. Never executes codigo.
    """
    from .analyzer import analyze
    from .selector import select
    from .layout import build
    from .notebook import current_shell,SLOT
    target=Path(destino)
    kind=(formato or target.suffix.lstrip('.')).lower()
    if kind not in {'pdf','jpg','jpeg'}:raise ValueError('El formato de descarga debe ser pdf o jpg.')
    if not isinstance(sobrescribir,bool):raise TypeError('sobrescribir debe ser booleano.')
    if codigo is None:
        obs=getattr(current_shell(),SLOT,None)
        if not obs or obs.last_model is None:raise RuntimeError('Todavía no hay una lámina para exportar. Ejecuta una celda o proporciona código.')
        if opciones:raise ValueError('Para exportar la última lámina no se aceptan opciones que cambien su contenido.')
        model=obs.last_model;representation=obs.last_representation
    else:
        fmt=opciones.pop('representacion','auto')
        model=analyze(codigo,opciones.pop('objetivo','Comprender cómo los datos se transforman en un resultado'),opciones.pop('nivel','inicial'),context=opciones.pop('contexto','auto'))
        if opciones:raise TypeError('Opciones desconocidas: '+', '.join(opciones))
        representation=select(model,fmt)
    document=build(model,representation);pdf=pdf_bytes(document)
    blobs=[pdf] if kind=='pdf' else jpg_pages(pdf,dpi)
    if len(blobs)==1:paths=[target]
    else:paths=[target.with_name(target.stem+f'-{i:02d}'+target.suffix) for i in range(1,len(blobs)+1)]
    if not sobrescribir:
        for p in paths:
            if p.exists():raise FileExistsError(str(p))
    for p,data in zip(paths,blobs):
        with p.open('wb' if sobrescribir else 'xb') as f:f.write(data)
    return paths[0] if kind=='pdf' else paths
