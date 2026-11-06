"""Local file export. Read code as text; never import or run the supplied file."""
from pathlib import Path
from html import escape
import tokenize


def guardar(codigo, destino, *, sobrescribir=False, **opciones):
    """Save a standalone HTML sheet and return its Path. Existing files are protected."""
    from . import generar
    path = Path(destino)
    markup = generar(codigo, **opciones)
    document = ('<!doctype html><html lang="es"><meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width,initial-scale=1">'
                '<title>PyNotas · Explicación de código Python</title>'
                '<body style="margin:0;padding:12px;background:#e7eeeb">'
                + markup + '</body></html>')
    with path.open('w' if sobrescribir else 'x', encoding='utf-8') as stream:
        stream.write(document)
    return path


def explicar_archivo(origen, destino=None, *, sobrescribir=False, **opciones):
    """Read a .py file (honoring its encoding declaration) and export HTML without running it."""
    source = Path(origen)
    if source.suffix.lower() != '.py':
        raise ValueError('El archivo de entrada debe tener extensión .py.')
    target = Path(destino) if destino is not None else source.with_suffix('.pynotas.html')
    if source.resolve() == target.resolve():
        raise ValueError('El destino no puede ser el archivo de código original.')
    with tokenize.open(source) as stream:
        code = stream.read(60001)
    return guardar(code, target, sobrescribir=sobrescribir, **opciones)
