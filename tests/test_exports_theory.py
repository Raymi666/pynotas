import ast
import base64
import io
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

import pynotas
from pynotas.layout import build, fonts, WIDTH, HEIGHT
from pynotas.theory import import_bindings
from pynotas.exports import pdf_bytes, jpg_pages
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output
from pynotas.notebook import SLOT

class TheoryTests(unittest.TestCase):
    def keys(self,code,**kw):
        return [t.key for t in pynotas.analizar(code,**kw).theories]

    def test_rms_equivalent_expressions(self):
        for code in ['r=np.sqrt(np.mean(x**2))',
                     'import numpy as numeros\nr=numeros.sqrt(numeros.mean(numeros.square(x)))',
                     'from numpy import sqrt, mean\nr=sqrt(mean(x**2))',
                     'cuadrados=x**2\nm=np.mean(cuadrados)\nr=np.sqrt(m)']:
            self.assertIn('rms',self.keys(code),code)

    def test_wrong_formula_shadowing_and_deferred_calls(self):
        for code in ['r=np.sqrt(np.mean(x))','r=np.mean(x)**2',
                     'np=otro\nr=np.sqrt(np.mean(x**2))',
                     'def np():\n    pass\nr=np.std(x)',
                     'r=lambda: np.fft.rfft(x)',
                     'cuadrados=x**2\ncuadrados=otros\nr=np.sqrt(np.mean(cuadrados))']:
            self.assertEqual(self.keys(code),[],code)

    def test_crest_requires_same_input(self):
        same='p=np.max(np.abs(x))\nr=np.sqrt(np.mean(x**2))\nc=p/r'
        self.assertIn('crest',self.keys(same))
        self.assertNotIn('crest',self.keys(same.replace('x**2','y**2')))

    def test_fft_and_kurtosis_sources_and_cautions(self):
        model=pynotas.analizar('f=np.fft.rfftfreq(N,1/fs)\nX=np.fft.rfft(x)\nk=stats.kurtosis(x)')
        self.assertEqual({t.key for t in model.theories},{'frequency_axis','fft','kurtosis'})
        self.assertTrue(all(t.source.startswith('https://') for t in model.theories))
        self.assertIn('fisher=True',model.theories[-1].meaning)

    def test_alias_bindings_from_prior_cell_and_invalidated_alias(self):
        aliases=import_bindings(ast.parse('import numpy as numeros'))
        self.assertEqual(self.keys('r=numeros.std(x)',bindings=aliases),['std'])
        aliases=import_bindings(ast.parse('numeros=otro'),aliases)
        self.assertEqual(self.keys('r=numeros.std(x)',bindings=aliases),[])

    def test_std_distinguishes_sample_correction(self):
        t=pynotas.analizar('s=np.std(x,ddof=1)').theories[0]
        self.assertIn('ddof=0',t.meaning)
        self.assertIn('N-1',t.meaning)

    def test_update_slice_describes_operation(self):
        b=pynotas.analizar('amplitud[1:-1] *= 2').blocks[0]
        self.assertIn('Multiplica',b.summaries[0])
        self.assertIn('corchetes',b.summaries[0])

    def test_no_fabricated_domain_for_unknown_code(self):
        model=pynotas.analizar('resultado=mi_funcion(datos)',context='vibraciones')
        self.assertEqual(model.theories,())

class ExportTests(unittest.TestCase):
    source='rms = np.sqrt(np.mean(vibracion**2))'
    def document(self,source=None):
        m=pynotas.analizar(source or self.source)
        return build(m,pynotas.seleccionar(m))

    def test_download_payloads_and_one_disclosure(self):
        from PIL import Image
        html=pynotas.generar(self.source,oculto=True)
        tag=re.search(r'<details[^>]*>',html).group()
        self.assertNotIn(' open',tag)
        self.assertEqual(html.count('<details '),1)
        pdf=base64.b64decode(re.search(r'data:application/pdf;base64,([^"]+)',html)[1])
        self.assertTrue(pdf.startswith(b'%PDF-'))
        jpg=base64.b64decode(re.search(r'data:image/jpeg;base64,([^"]+)',html)[1])
        image=Image.open(io.BytesIO(jpg))
        self.assertGreaterEqual(image.width,2480)
        self.assertGreaterEqual(image.height,1700)
        self.assertEqual(image.info['dpi'],(300,300))
        self.assertNotIn('<script',html)
        self.assertNotIn('data:application/pdf',pynotas.generar(self.source,descargas=False))

    def test_export_does_not_execute_and_protects_existing_file(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/'sheet.pdf'
            with patch('builtins.eval',side_effect=AssertionError):
                result=pynotas.exportar('x=must_not_run()',p)
            self.assertEqual(result,p)
            original=p.read_bytes()
            with self.assertRaises(FileExistsError):pynotas.exportar('x=2',p)
            self.assertEqual(p.read_bytes(),original)

    def test_letter_pages_retain_last_instruction(self):
        import pypdfium2 as pdfium
        source='\n'.join(f'dato_{i} = {i}' for i in range(25))
        doc=self.document(source)
        self.assertGreater(len(doc.pages),1)
        self.assertTrue(all((p.width,p.height)==(612,792) for p in doc.pages))
        with pdfium.PdfDocument(pdf_bytes(doc)) as pdf:
            text=''
            for page in pdf:
                tp=page.get_textpage();text+=tp.get_text_range();tp.close()
                page.close()
        self.assertIn('dato_24',text)
        self.assertIn('L25',text)
        self.assertNotIn('adicional(es)',text)

    def test_layout_text_inside_page(self):
        cases=[self.source,'if temperatura > 80:\n    estado="ALERTA"\nelse:\n    estado="NORMAL"',
               'promedio=suma/cantidad','import '+'modulo_'+'x'*120,
               'def ejemplo(x):\n    return x*2']
        for source in cases:
            for page in self.document(source).pages:
                for op in page.ops:
                    if op[0]=='text':
                        _,x,y,s,size,color,font=op
                        self.assertLessEqual(x+fonts().stringWidth(s,font,size),page.width+1,(source,s))
                        self.assertTrue(0<y<page.height,(source,s))

    def test_letter_jpg_files_and_no_partial_overwrite(self):
        source='\n'.join(f'x{i}={i}' for i in range(15))
        with tempfile.TemporaryDirectory() as root:
            paths=pynotas.exportar(source,Path(root)/'page.jpg',dpi=96)
            self.assertGreater(len(paths),1)
            self.assertTrue(all(p.read_bytes().startswith(b'\xff\xd8') for p in paths))
            first=paths[0].read_bytes()
            with self.assertRaises(FileExistsError):pynotas.exportar(source,Path(root)/'page.jpg',dpi=96)
            self.assertEqual(paths[0].read_bytes(),first)
            paths[0].unlink()
            with self.assertRaises(FileExistsError):pynotas.exportar(source,Path(root)/'page.jpg',dpi=96)
            self.assertFalse(paths[0].exists())

    def test_observer_single_execution_collapsed_and_last_export(self):
        shell=InteractiveShell.instance()
        pynotas.desactivar(shell=shell)
        pynotas.activar(shell=shell,descargas=False)
        shell.user_ns['veces_pynotas']=0
        try:
            with capture_output() as cap:
                result=shell.run_cell('veces_pynotas += 1\nprint(veces_pynotas)',store_history=True)
            self.assertIsNone(result.error_in_exec)
            self.assertEqual(cap.stdout,'1\n')
            html=cap.outputs[0].data['text/html']
            self.assertNotIn(' open',re.search(r'<details[^>]*>',html).group())
            with tempfile.TemporaryDirectory() as root,patch('pynotas.notebook.current_shell',return_value=shell):
                pynotas.exportar(None,Path(root)/'ultima.pdf')
            self.assertEqual(shell.user_ns['veces_pynotas'],1)
        finally:pynotas.desactivar(shell=shell)

if __name__=='__main__':unittest.main()
