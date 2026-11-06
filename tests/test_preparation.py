import json
import re
import unittest
from xml.etree import ElementTree as ET
import pynotas
from pynotas.model import is_preparation

SOURCE = '''import matplotlib.pyplot as plt
import seaborn as sns
import scipy.io
from google.colab import drive
import os
drive.mount('/content/drive', force_remount=True)'''


class PreparationTests(unittest.TestCase):
    def test_preparation_has_own_pedagogy(self):
        model = pynotas.analizar(SOURCE)
        rep = pynotas.seleccionar(model)
        self.assertTrue(is_preparation(model))
        self.assertEqual(rep.format, 'flujo')
        self.assertEqual(rep.title, 'Prepara tu entorno en Python')
        self.assertIn('plt', rep.practice)
        self.assertIn('referencias posteriores', rep.check)

    def test_resources_grouped_without_dependency_arrows(self):
        html = pynotas.generar(SOURCE)
        pages = re.findall(r'<svg.*?</svg>', html, re.S)
        for page in pages:ET.fromstring(page)
        svg = ' '.join(pages)
        self.assertNotIn('marker-end', svg)
        for phrase in ['Preparar las herramientas', 'apodo',
                       'Conectar Google Drive', 'montar Drive de nuevo']:
            visible = ' '.join(' '.join(ET.fromstring(p).itertext()) for p in pages)
            self.assertIn(phrase,visible)
        self.assertNotIn('PRACTICAR', html)
        self.assertNotIn('APLICAR', html)

    def test_original_lines_and_full_code_preserved(self):
        source = '# comentario\n\n' + SOURCE
        m = pynotas.analizar(source)
        self.assertEqual(m.source, source)
        self.assertEqual(m.blocks[0].line, 3)
        self.assertEqual(m.blocks[-1].line, 8)
        self.assertIn('source', json.loads(json.dumps(m.to_dict())))

    def test_access_names_match_python_import_forms(self):
        model = pynotas.analizar('import scipy.io\nfrom scipy.io import loadmat as leer')
        self.assertEqual(model.blocks[0].resources[0].access_name, 'scipy.io')
        self.assertEqual(model.blocks[1].resources[0].access_name, 'leer')

    def test_drive_aliases_resolved_without_importing(self):
        for source in ["from google.colab import drive as d\nd.mount('/content/drive')",
                       "import google.colab.drive as d\nd.mount('/content/drive')",
                       "import google.colab.drive\ngoogle.colab.drive.mount('/content/drive')",
                       "from google.colab.drive import mount as conectar\nconectar('/content/drive')"]:
            with self.subTest(source=source):
                self.assertEqual(pynotas.analizar(source).blocks[-1].kind, 'setup')

    def test_rebound_or_unknown_drive_not_identified(self):
        for source in ["drive.mount('/x')", "from otra import drive\ndrive.mount('/x')",
                       "from google.colab import drive\ndrive = custom\ndrive.mount('/x')",
                       "from google.colab import drive\nimport otra as drive\ndrive.mount('/x')",
                       "from google.colab import drive\nfrom otra import *\ndrive.mount('/x')",
                       "from google.colab import drive\nmutar()\ndrive.mount('/x')"]:
            with self.subTest(source=source):
                model = pynotas.analizar(source)
                self.assertNotEqual(model.blocks[-1].kind, 'setup')
                self.assertFalse(is_preparation(model))

    def test_mount_option_explanations_are_literal_only(self):
        base = 'from google.colab import drive\ndrive.mount("/x", force_remount={})'
        for expr in ['True', 'False', 'configurar()']:
            b = pynotas.analizar(base.format(expr)).blocks[-1]
            if expr == 'True':
                self.assertIn('montar Drive de nuevo', ' '.join(b.summaries))
            elif expr == 'False':
                self.assertIn('no solicita forzar', ' '.join(b.summaries))
            else:
                self.assertEqual(len(b.summaries), 1)

    def test_mixed_code_still_has_control_flow(self):
        for code in ['import os\nx = 1', 'import os\nif listo:\n    print(1)',
                     'def funcion():\n    import os']:
            self.assertFalse(is_preparation(pynotas.analizar(code)))
            self.assertIn('<svg', pynotas.generar(code))

    def test_large_import_cell_falls_back_without_losing_code(self):
        source = 'import ' + ', '.join('paquete'+str(i) for i in range(13))
        model = pynotas.analizar(source)
        self.assertFalse(is_preparation(model))
        self.assertEqual(len(model.blocks[0].resources), 13)
        self.assertIn(source, pynotas.generar(source))

    def test_duplicate_alias_and_unknown_module_are_not_guessed(self):
        model = pynotas.analizar('import matplotlib.pyplot as dibujo\nimport desconocido as np')
        self.assertIn('dibujo', pynotas.seleccionar(model).practice)
        self.assertIn('no está en', model.blocks[1].resources[0].purpose)

    def test_escaping_and_unique_ids_in_preparation(self):
        html = pynotas.generar(SOURCE, objetivo='<script>alert(1)</script>')
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)
        ids = re.findall(r'id="([^"]+)"', html + pynotas.generar(SOURCE))
        self.assertEqual(len(ids), len(set(ids)))

    def test_long_alias_multiline_and_unicode(self):
        source = 'from scipy.io import (\n    loadmat as lectura_de_datos_muy_larga_ñ,\n)'
        model = pynotas.analizar(source)
        self.assertEqual(model.blocks[0].end_line, 3)
        for svg in re.findall(r'<svg.*?</svg>', pynotas.generar(source), re.S):
            ET.fromstring(svg)
