"""Copy bounded PNG/JPEG display messages, forwarding the original unchanged."""
import base64
import io
from .model import CapturedFigure

MAX_BYTES=8_000_000
MAX_PIXELS=20_000_000
MAX_FIGURES=4


def raster(mime,payload):
    from PIL import Image
    if mime not in {'image/png','image/jpeg'}:raise ValueError('Formato no admitido')
    if not isinstance(payload,(str,bytes)) or len(payload)>MAX_BYTES*4//3+8:raise ValueError('Imagen demasiado grande')
    raw=base64.b64decode(payload,validate=True) if isinstance(payload,str) else payload
    if len(raw)>MAX_BYTES:raise ValueError('Imagen demasiado grande')
    with Image.open(io.BytesIO(raw)) as im:
        w,h=im.size
        if w*h>MAX_PIXELS or im.format!=({'image/png':'PNG','image/jpeg':'JPEG'}[mime]):raise ValueError('Imagen no admitida')
        im.verify()
    return CapturedFigure(mime,base64.b64encode(raw).decode('ascii'),w,h)


class DisplayCapture:
    def __init__(self,publisher):
        self.publisher=publisher;self.saved=[];self.images=[];self.notes=[];self.clear_pending=False

    def note(self):
        message='Alguna imagen no se incorporó por su formato, tamaño o límite de 4 imágenes. Consulta la salida original.'
        if message not in self.notes:self.notes.append(message)

    def receive(self,data,transient=None,update=False):
        if not isinstance(data,dict):return
        if self.clear_pending:self.images.clear();self.clear_pending=False
        key=(transient or {}).get('display_id')
        for mime in ('image/png','image/jpeg'):
            if mime not in data:continue
            try:
                fig=raster(mime,data[mime])
                index=next((i for i,(old,_) in enumerate(self.images) if key and old==key),None)
                if update and index is None:return
                candidates=list(self.images)
                if index is not None:candidates[index]=(key,fig)
                else:candidates.append((key,fig))
                if len(candidates)>MAX_FIGURES or sum(len(f.data)*3//4 for _,f in candidates)>MAX_BYTES:raise ValueError('Límite')
                self.images=candidates
            except Exception:self.note()
            return

    def install(self):
        original=self.publisher.publish
        def publish(*args,**kwargs):
            result=original(*args,**kwargs)
            try:self.receive(kwargs.get('data',args[0] if args else None),kwargs.get('transient'),kwargs.get('update',False))
            except Exception:self.note()
            return result
        self.wrap('publish',publish)
        original_clear=getattr(self.publisher,'clear_output',None)
        if original_clear:
            def clear(*args,**kwargs):
                result=original_clear(*args,**kwargs)
                wait=kwargs.get('wait',args[0] if args else False)
                if wait:self.clear_pending=True
                else:self.images.clear();self.clear_pending=False
                return result
            self.wrap('clear_output',clear)

    def wrap(self,name,wrapper):
        namespace=vars(self.publisher)
        self.saved.append((name,name in namespace,namespace.get(name),wrapper))
        setattr(self.publisher,name,wrapper)

    def restore(self):
        for name,existed,old,wrapper in reversed(self.saved):
            if getattr(self.publisher,name,None) is wrapper:
                if existed:setattr(self.publisher,name,old)
                else:delattr(self.publisher,name)
        self.saved.clear()

    @property
    def figures(self):return tuple(f for _,f in self.images)
