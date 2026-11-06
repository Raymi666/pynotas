"""Compatibility imports: SURF IA is now PyNotas."""
import importlib as _importlib
import sys as _sys
import pynotas as _pynotas
from pynotas import *
from pynotas import __version__, __all__, load_ipython_extension, unload_ipython_extension

# Both names share the exact same submodules, observer and capture state.
for _name in ['_version', 'analysis_context', 'analyzer', 'artwork', 'capture', 'cli', 'exports', 'files', 'illustrations', 'infographic', 'layout', 'lessons', 'letter_layout', 'ml', 'model', 'notebook', 'preparation', 'presentation', 'reading_layout', 'renderers', 'resources', 'selector', 'sheets', 'stages', 'syntax', 'teacher', 'teaching', 'theory', 'walkthrough']:
    _module = _importlib.import_module('pynotas.' + _name)
    _sys.modules[__name__ + '.' + _name] = _module
    globals()[_name] = _module

def __getattr__(name):
    return getattr(_pynotas, name)
