"""Behavioral migration checks: identical state, single execution, new branding."""
import base64
import io
import os
import re
import subprocess
import sys
import unittest

import pynotas


class RenameTests(unittest.TestCase):
    def run_program(self, code, **options):
        env = dict(os.environ)
        env.pop('PYNOTAS_AUTOACTIVAR', None)
        env.pop('SURFIA_AUTOACTIVAR', None)
        env.update(options)
        result = subprocess.run([sys.executable, '-c', code], env=env,
                                capture_output=True, text=True, timeout=45)
        self.assertEqual(result.returncode, 0, result.stdout+'\n'+result.stderr)

    def test_visible_identity_and_exports(self):
        html = pynotas.generar('temperatura = 85\nestado = "ALERTA" if temperatura > 80 else "NORMAL"', oculto=True)
        self.assertIn('Ver explicación de PyNotas', html)
        self.assertIn('Ocultar explicación de PyNotas', html)
        self.assertIn('download="PyNotas.pdf"', html)
        self.assertIn('download="PyNotas.jpg"', html)
        self.assertNotIn('SURF IA', html)
        self.assertNotRegex(html, r'<details[^>]* open')
        from pypdf import PdfReader
        encoded = re.search(r'data:application/pdf;base64,([^\"]+)', html).group(1)
        reader = PdfReader(io.BytesIO(base64.b64decode(encoded)))
        self.assertIn('PyNotas', reader.pages[0].extract_text())
        self.assertEqual(tuple(float(x) for x in reader.pages[0].mediabox[2:]), (612,792))

    def test_old_and_new_import_orders_share_one_observer(self):
        for imports in ('import surfia\nimport pynotas', 'import pynotas\nimport surfia'):
            with self.subTest(imports=imports):
                self.run_program('''
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output
shell=InteractiveShell.instance()
'''+imports+'''
from pynotas.notebook import SLOT
from surfia.notebook import Observer as OldObserver
from pynotas.notebook import Observer
assert OldObserver is Observer
assert surfia.activar is pynotas.activar
assert surfia.__version__ == pynotas.__version__
o=getattr(shell,SLOT)
assert shell.events.callbacks['post_run_cell'].count(o.after_cell)==1
shell.user_ns['contador']=0
with capture_output() as output:
    shell.run_cell('contador += 1\\nprint(contador)',store_history=True)
assert shell.user_ns['contador']==1
assert output.stdout=='1\\n'
assert len(output.outputs)==1
assert 'Ver explicación de PyNotas' in output.outputs[0].data['text/html']
surfia.desactivar()
assert not o.active
pynotas.activar()
assert o.active
''')

    def test_legacy_opt_out_and_appearance(self):
        self.run_program('''
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output
shell=InteractiveShell.instance()
import pynotas
from pynotas.notebook import SLOT
assert getattr(shell,SLOT,None) is None
pynotas.activar(apariencia='surfia')
with capture_output() as output:
    shell.run_cell('# surfia: omitir\\nx=1',store_history=True)
assert output.outputs==[]
with capture_output() as output:
    shell.run_cell('# pynotas: omitir\\nx=2',store_history=True)
assert output.outputs==[]
assert pynotas.diagnostico()['version_surfia']==pynotas.__version__
''', SURFIA_AUTOACTIVAR='0')

    def test_cli_brand(self):
        for name in ('pynotas', 'surfia'):
            p = subprocess.run([sys.executable, '-m', name, '--version'], capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(p.stdout.strip(), 'PyNotas '+pynotas.__version__)


if __name__ == '__main__':
    unittest.main()
