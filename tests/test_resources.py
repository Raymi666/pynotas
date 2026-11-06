import re
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output
import pynotas
from pynotas.notebook import SLOT


class ResourceTests(unittest.TestCase):
    def test_alias_uses_resource_not_alias_for_meaning(self):
        b = pynotas.analizar('import matplotlib.pyplot as dibujo').blocks[0]
        self.assertIn('personalizar gráficos', b.summaries[0])
        self.assertIn('dibujo', b.title)
        self.assertIn('alias dibujo', b.explanation)

    def test_class_resources_have_visible_explanation(self):
        for source in ['import matplotlib.pyplot as plt','import seaborn as sns',
                       'import scipy.io','from google.colab import drive','import os',
                       'import numpy as np','import pandas as pd',
                       'from matplotlib.backends.backend_pdf import PdfPages']:
            with self.subTest(source=source):
                b=pynotas.analizar(source).blocks[0]
                html=pynotas.generar(source)
                svg=re.search(r'<svg.*?</svg>',html,re.S).group()
                text=' '.join(ET.fromstring(svg).itertext())
                # Visible SVG text, not only a tooltip or collapsed explanation.
                visible=' '.join(t.text or '' for t in ET.fromstring(svg).iter('{http://www.w3.org/2000/svg}text'))
                expected={'matplotlib.pyplot':'dibujar y personalizar gráficos', 'scipy.io':'leer y guardar', 'os':'carpetas y rutas', 'numpy':'calcular con números', 'pandas':'tablas de filas y columnas'}.get(b.resources[0].qualified_name,b.summaries[0])
                self.assertIn(expected, visible)
                self.assertNotIn('no está en',text)
                self.assertNotIn('Importar recursos', html)

    def test_multiple_resources_each_described(self):
        b=pynotas.analizar('from scipy.fft import fft, fftfreq as frecuencias').blocks[0]
        self.assertEqual(len(b.summaries),2)
        self.assertIn('Calcula',b.summaries[0])
        self.assertIn('Genera',b.summaries[1])
        self.assertEqual((b.line,b.end_line),(1,1))

    def test_unknown_and_relative_do_not_guess(self):
        for source in ['import paquete_desconocido as np','from numpy import no_existe',
                       'from . import numpy']:
            self.assertIn('no está en',pynotas.analizar(source).blocks[0].summaries[0])

    def test_wildcard_is_explicit(self):
        b=pynotas.analizar('from paquete import *').blocks[0]
        self.assertIn('no se enumeran',b.summaries[0])

    def test_static_analysis_does_not_load_resources(self):
        import builtins
        original = builtins.__import__
        def guarded(name, *args, **kwargs):
            if name == 'seaborn':
                raise AssertionError('Do not import the analyzed resource')
            return original(name, *args, **kwargs)
        with patch('builtins.__import__', side_effect=guarded):
            b=pynotas.analizar('import seaborn').blocks[0]
        self.assertIn('estadísticos',b.summaries[0])

    def test_import_only_cell_is_displayed_once(self):
        shell=InteractiveShell.instance()
        pynotas.activar(shell=shell)
        observer=getattr(shell,SLOT)
        before=observer.generated
        try:
            with capture_output() as capture:
                result=shell.run_cell('import os',store_history=True)
            self.assertIsNone(result.error_in_exec)
            self.assertEqual(observer.generated,before+1)
            self.assertEqual(len(capture.outputs),1)
        finally:
            pynotas.desactivar(shell=shell)

    def test_pynotas_only_import_stays_quiet(self):
        shell=InteractiveShell.instance()
        pynotas.activar(shell=shell)
        observer=getattr(shell,SLOT)
        before=observer.generated
        try:
            with capture_output():
                shell.run_cell('import pynotas',store_history=True)
            self.assertEqual(observer.generated,before)
        finally:
            pynotas.desactivar(shell=shell)

    def test_drive_mount_is_not_repeated_by_observer(self):
        import types
        from unittest.mock import Mock
        google = types.ModuleType('google')
        colab = types.ModuleType('google.colab')
        mount = Mock()
        colab.drive = types.SimpleNamespace(mount=mount)
        google.colab = colab
        shell = InteractiveShell.instance()
        pynotas.activar(shell=shell)
        observer = getattr(shell, SLOT)
        before = observer.generated
        try:
            with patch.dict('sys.modules', {'google': google, 'google.colab': colab}):
                with capture_output() as capture:
                    result = shell.run_cell("from google.colab import drive\ndrive.mount('/content/drive', force_remount=True)", store_history=True)
            self.assertIsNone(result.error_in_exec)
            mount.assert_called_once_with('/content/drive', force_remount=True)
            self.assertEqual(observer.generated, before+1)
            self.assertEqual(len(capture.outputs), 1)
        finally:
            pynotas.desactivar(shell=shell)
