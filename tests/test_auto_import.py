import os
import subprocess
import sys
import unittest

class AutomaticImportTests(unittest.TestCase):
    def run_program(self, code, auto='1'):
        env = dict(os.environ, PYNOTAS_AUTOACTIVAR=auto)
        p = subprocess.run([sys.executable, '-c', code], env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(p.returncode, 0, p.stdout+'\n'+p.stderr)
        return p

    def test_plain_python_import_does_not_create_shell(self):
        p=self.run_program('''
import pynotas
from IPython.core.interactiveshell import InteractiveShell
assert not InteractiveShell.initialized()
assert '<svg' in pynotas.generar('x=1')
''')
        self.assertEqual(p.stdout,'')

    def test_import_is_enough_and_user_code_runs_once(self):
        self.run_program('''
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output
shell=InteractiveShell.instance()
with capture_output() as c:
    r=shell.run_cell('import pynotas',store_history=True)
assert r.error_in_exec is None
import pynotas
from pynotas.notebook import SLOT
observer=getattr(shell,SLOT)
assert observer.active and observer.generated==0
shell.user_ns['contador']=0
with capture_output() as c:
    r=shell.run_cell('contador += 1\\nprint(contador)',store_history=True)
assert r.error_in_exec is None
assert shell.user_ns['contador']==1
assert c.stdout=='1\\n'
assert len(c.outputs)==1
assert observer.generated==1
''')

    def test_reimport_and_reload_keep_single_observer_and_options(self):
        self.run_program('''
from IPython.core.interactiveshell import InteractiveShell
shell=InteractiveShell.instance()
import pynotas,importlib
from pynotas.notebook import SLOT
pynotas.activar(objetivo='Mi objetivo',shell=shell)
o=getattr(shell,SLOT)
import pynotas
importlib.reload(pynotas)
assert getattr(shell,SLOT) is o
assert o.options['objetivo']=='Mi objetivo'
assert shell.events.callbacks['post_run_cell'].count(o.after_cell)==1
pynotas.desactivar(shell=shell)
importlib.reload(pynotas)
assert not o.active
''')

    def test_environment_opt_out(self):
        self.run_program('''
from IPython.core.interactiveshell import InteractiveShell
shell=InteractiveShell.instance()
import pynotas
from pynotas.notebook import SLOT
assert getattr(shell,SLOT,None) is None
pynotas.activar(shell=shell)
assert getattr(shell,SLOT).active
''',auto='0')

    def test_registration_failure_does_not_break_import(self):
        self.run_program('''
from IPython.core.interactiveshell import InteractiveShell
shell=InteractiveShell.instance()
from unittest.mock import patch
with patch.object(shell.events,'register',side_effect=RuntimeError('unavailable')):
    import pynotas
assert 'RuntimeError' in pynotas.diagnostico()['ultimo_aviso']
assert '<svg' in pynotas.generar('x=1')
''')

if __name__=='__main__':unittest.main()
