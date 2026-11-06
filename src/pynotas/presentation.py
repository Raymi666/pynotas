"""Accessible notebook shell: one outer disclosure and self-contained downloads."""
import base64
from html import escape
import uuid
from .layout import build
from .exports import pdf_bytes,jpg_pages



def render(model,representation,executed=False,*,collapsed=False,downloads=True):
    if not isinstance(collapsed,bool) or not isinstance(downloads,bool):raise TypeError('oculto y descargas deben ser booleanos.')
    ident='pynotas-'+uuid.uuid4().hex
    doc=build(model,representation)
    css=f'''<style>
#{ident}{{max-width:1000px;margin:12px 0;font:15px/1.5 Arial,sans-serif;color:#203e4e;text-align:left;color-scheme:light}}
#{ident}>summary{{cursor:pointer;background:#fbfaf6;color:#102f3b;border:1px solid #d4e0df;border-left:4px solid {doc.theme.accent};border-radius:8px;padding:13px 18px;font-weight:bold;list-style:none}}
#{ident}>summary::-webkit-details-marker{{display:none}}
#{ident}>summary::before{{content:'▶ ';}} #{ident}[open]>summary::before{{content:'▼ ';}}
#{ident} .close-label{{display:none}} #{ident}[open] .open-label{{display:none}} #{ident}[open] .close-label{{display:inline}}
#{ident} .sheet-page{{background:#fbfaf6;margin:16px 0;border:1px solid #dbe5e9;border-radius:8px;overflow-x:auto;box-shadow:0 6px 20px #102f3b12}}
#{ident} svg{{display:block;width:100%;min-width:480px;height:auto}}
#{ident} .downloads{{display:flex;gap:8px;flex-wrap:wrap;padding:12px 0}}
#{ident} .downloads a{{padding:9px 14px;border-radius:6px;background:#123447;color:white;text-decoration:none}}
#{ident} a:focus-visible,#{ident} summary:focus-visible{{outline:3px solid #ac4e23;outline-offset:3px}}
#{ident} .plain-source{{white-space:pre-wrap;overflow-wrap:anywhere;background:#f5f8fa;padding:14px;font:12px/1.5 monospace}}
#{ident} .sr-only{{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}}
@media print{{#{ident} .downloads,#{ident}>summary{{display:none}} #{ident} .sheet-page{{break-after:page;border:0}} #{ident} svg{{min-width:0}}}}
</style>'''
    pages=''.join('<div class="sheet-page">'+p.svg(ident+f'-p{i}')+'</div>' for i,p in enumerate(doc.pages,1))
    links=''
    if downloads:
        pdf=pdf_bytes(doc)
        links='<a download="PyNotas.pdf" href="data:application/pdf;base64,'+base64.b64encode(pdf).decode()+'">Descargar PDF</a>'
        for i,data in enumerate(jpg_pages(pdf),1):
            label='Descargar JPG' if len(doc.pages)==1 else f'JPG · página {i}'
            name='PyNotas.jpg' if len(doc.pages)==1 else f'PyNotas_{i:02d}.jpg'
            links+=f'<a download="{name}" href="data:image/jpeg;base64,{base64.b64encode(data).decode()}">{label}</a>'
    # Preserve exact source for copy/paste/accessibility, including blank lines/Unicode.
    source='<pre class="sr-only" aria-label="Código fuente completo">'+escape(model.source)+'</pre>'
    status='La celda terminó; sus resultados están en la salida original.' if executed else 'Lámina generada leyendo el código, sin ejecutarlo.'
    content=pages+f'<nav class="downloads" aria-label="Descargar la lámina">{links}</nav><p>{escape(status)}</p>'+source
    return css+f'<details id="{ident}" data-topic="{representation.lesson_key}"'+('' if collapsed else ' open')+'><summary><span class="open-label">Ver explicación de PyNotas</span><span class="close-label">Ocultar explicación de PyNotas</span></summary>'+content+'</details>'
