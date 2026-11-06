"""PyNotas: código → modelo → representación → SVG/HTML."""
from .analyzer import analyze as analizar
from .selector import select as seleccionar
from .renderers import render as renderizar
from .notebook import activate as activar, deactivate as desactivar, diagnostics as diagnostico

from ._version import __version__
__all__ = ["analizar", "seleccionar", "renderizar", "generar", "mostrar", "activar", "desactivar", "diagnostico", "guardar", "explicar_archivo", "exportar"]


def generar(codigo, formato="auto", nivel="inicial",
            objetivo="Comprender cómo los datos se transforman en un resultado",
            contexto="auto", oculto=False, descargas=True):
    """Devuelve HTML autocontenido. No ejecuta codigo."""
    model = analizar(codigo, objetivo, nivel, context=contexto)
    return renderizar(model, seleccionar(model, formato), collapsed=oculto, downloads=descargas)


def mostrar(codigo, **opciones):
    """Muestra una lámina estática sin ejecutar codigo."""
    try:
        from IPython.display import HTML, display
    except ImportError as error:
        raise RuntimeError("mostrar() necesita IPython. Instala pynotas[notebook] o usa guardar().") from error
    display(HTML(generar(codigo, **opciones)))


def load_ipython_extension(ipython):
    activar(shell=ipython)


def unload_ipython_extension(ipython):
    desactivar(shell=ipython)


from .files import guardar, explicar_archivo
from .exports import exportar

# Importing in a notebook starts the existing post-run observer. No user code
# is executed here; normal Python imports do not create an interactive shell.
from .notebook import auto_activate as _auto_activate
_auto_activate()
