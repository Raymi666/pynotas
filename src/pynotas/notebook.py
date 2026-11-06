"""Observador posterior a la ejecución. Nunca invoca run_cell/exec/eval."""
import ast
import os
from dataclasses import replace
from .analyzer import analyze
from .selector import select, FORMATS
from .renderers import render

# Keep the shared slot during migration so an already imported SURF IA observer
# can be replaced without registering a second pair of cell hooks.
SLOT = "_surfia_pedagogia_v02"


def current_shell():
    try:
        from IPython import get_ipython
    except ImportError:
        return None
    return get_ipython()


class Observer:
    def __init__(self, shell, options):
        self.shell = shell
        self.options = options
        self.active = False
        self.busy = False
        self.generated = 0
        self.last_error = None
        self.last_model = None
        self.last_representation = None
        self.bindings = {}
        self.capture = None

    def start(self):
        if not self.active:
            self.shell.events.register("post_run_cell", self.after_cell)
            try:
                self.shell.events.register("pre_run_cell", self.before_cell)
            except Exception:
                self.shell.events.unregister("post_run_cell", self.after_cell)
                raise
            self.active = True

    def stop(self):
        if self.active:
            self.shell.events.unregister("post_run_cell", self.after_cell)
            self.shell.events.unregister("pre_run_cell", self.before_cell)
            self.active = False
        self.finish_capture()

    def finish_capture(self):
        capture=self.capture
        self.capture=None
        if capture:capture.restore()
        return capture

    def before_cell(self, info=None):
        self.finish_capture()
        if self.busy or not self.active or not self.options.get('capturar_graficos',True):return
        from .capture import DisplayCapture
        publisher=getattr(self.shell,'display_pub',None)
        if publisher is None:return
        self.capture=DisplayCapture(publisher)
        try:self.capture.install()
        except Exception:self.finish_capture()

    def after_cell(self, result):
        capture=self.finish_capture()
        if self.busy or not self.active or result is None:
            return
        if getattr(result, "error_before_exec", None) is not None or getattr(result, "error_in_exec", None) is not None:
            from .theory import DEFAULT_ALIASES
            self.bindings = {name: '' for name in {**DEFAULT_ALIASES, **self.bindings}}
            # A failing cell may have partially rebound names, including np.
            self.last_error = "Celda con error: se conserva la salida original y se omite la lámina."
            return
        source = getattr(getattr(result, "info", None), "raw_cell", "")
        if not source.strip() or any(marker in source for marker in ("# pynotas: omitir", "# surfia: omitir")):
            return
        self.busy = True
        try:
            tree = ast.parse(source)
            if not tree.body:
                return
            # Management cells are not learning examples. Aliased calls remain harmless.
            if any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                   and isinstance(n.func.value, ast.Name) and n.func.value.id in {"pynotas", "surfia"}
                   for n in ast.walk(tree)):
                return
            if all((isinstance(n, ast.Import) and all(a.name in {"pynotas", "surfia"} for a in n.names))
                   or (isinstance(n, ast.ImportFrom) and n.module in {"pynotas", "surfia"}) for n in tree.body):
                return
            from .theory import import_bindings
            previous_bindings = dict(self.bindings)
            self.bindings = import_bindings(tree, self.bindings)
            model = analyze(source, self.options["objetivo"], self.options["nivel"], context=self.options["contexto"], bindings=previous_bindings)
            if capture:model=replace(model,figures=capture.figures,capture_notes=tuple(capture.notes))
            representation = select(model, self.options["formato"])
            html = render(model, representation, executed=True, collapsed=self.options["oculto"], downloads=self.options["descargas"])
            from IPython.display import HTML, display
            display(HTML(html))
            self.generated += 1
            self.last_model = model
            self.last_representation = representation
            self.last_error = None
        except (SyntaxError, ValueError, RecursionError) as error:
            self.last_error = f"Lámina omitida: {type(error).__name__}: {error}"
        except Exception as error:
            # Rendering must not change the outcome of the user's cell.
            self.last_error = f"No se pudo generar la lámina: {type(error).__name__}: {error}"
        finally:
            self.busy = False


def activate(formato="auto", apariencia="pynotas", nivel="inicial",
             objetivo="Comprender cómo los datos se transforman en un resultado", shell=None,
             oculto=True, descargas=True, contexto="auto", capturar_graficos=True):
    from .theory import CONTEXTS
    if not isinstance(oculto,bool) or not isinstance(descargas,bool):
        raise TypeError("oculto y descargas deben ser booleanos.")
    if not isinstance(capturar_graficos,bool):raise TypeError('capturar_graficos debe ser booleano.')
    if contexto not in CONTEXTS:
        raise ValueError("Contexto válido: " + ", ".join(CONTEXTS))
    if formato not in FORMATS:
        raise ValueError("Formato válido: " + ", ".join(FORMATS))
    if apariencia not in {"pynotas", "surfia"}:
        raise ValueError("La apariencia disponible es pynotas.")
    if nivel not in {"inicial", "intermedio", "avanzado"}:
        raise ValueError("Nivel válido: inicial, intermedio, avanzado.")
    if not isinstance(objetivo, str):
        raise TypeError("El objetivo debe ser texto.")
    shell = shell if shell is not None else current_shell()
    if shell is None:
        raise RuntimeError("activar() requiere Colab/Jupyter/IPython; usa generar() para HTML independiente.")
    options = dict(formato=formato, apariencia=apariencia, nivel=nivel, objetivo=objetivo, oculto=oculto, descargas=descargas, contexto=contexto, capturar_graficos=capturar_graficos)
    observer = getattr(shell, SLOT, None)
    if observer is not None and not isinstance(observer, Observer):
        observer.stop()
        bindings = dict(getattr(observer, "bindings", {}))
        observer = Observer(shell, options)
        observer.bindings = bindings
        setattr(shell, SLOT, observer)
    elif observer is None:
        observer = Observer(shell, options)
        setattr(shell, SLOT, observer)
    else:
        observer.options = options
    observer.start()
    return None


def deactivate(shell=None):
    shell = shell if shell is not None else current_shell()
    observer = getattr(shell, SLOT, None)
    if observer:
        observer.stop()


def diagnostics():
    import platform
    from ._version import __version__
    try:
        import IPython
        ipython_version = IPython.__version__
    except ImportError:
        ipython_version = None
    shell = current_shell()
    observer = getattr(shell, SLOT, None)
    return dict(version_pynotas=__version__, version_surfia=__version__, python=platform.python_version(), ipython=ipython_version,
                sesion_ipython=shell is not None, motor_estatico="OK",
                modo_automatico_activo=bool(observer and observer.active), servicios_externos=False,
                laminas_generadas=observer.generated if observer else 0,
                explicacion_oculta=observer.options["oculto"] if observer else True,
                contexto=observer.options["contexto"] if observer else "auto",
                imagenes_en_ultima_lamina=len(observer.last_model.figures) if observer and observer.last_model else 0,
                ultimo_aviso=(observer.last_error if observer else None) or _startup_error)


_startup_error = None


def auto_activate():
    """Activate once when imported in IPython; preserve explicit user settings.

    Ordinary Python imports stay usable for static HTML generation. Import must
    not fail merely because the interactive display integration is unavailable.
    """
    global _startup_error
    if os.environ.get("PYNOTAS_AUTOACTIVAR", os.environ.get("SURFIA_AUTOACTIVAR", "1")).lower() in {"0", "false", "no"}:
        return False
    try:
        shell = current_shell()
        if shell is None:
            return False
        existing = getattr(shell, SLOT, None)
        if isinstance(existing, Observer):
            return False
        if existing is not None:
            was_active = bool(existing.active)
            options = dict(existing.options)
            activate(shell=shell, **options)
            if not was_active:
                deactivate(shell=shell)
            _startup_error = None
            return was_active
        activate(shell=shell)
        _startup_error = None
        return True
    except ImportError:
        return False
    except Exception as error:
        _startup_error = f"No se pudo activar automáticamente: {type(error).__name__}: {error}"
        return False
