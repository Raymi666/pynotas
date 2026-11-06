"""Regression for the user's MATLAB cell: one sheet with local explanations."""
import base64
import io
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET
import pynotas
from pynotas.layout import build,fonts
from pynotas.exports import pdf_bytes

MATLAB = '''# Buscar el primer archivo .mat en el directorio y cargar su contenido
mat_files = [f for f in os.listdir(path) if f.endswith('.mat')] if os.path.exists(path) else []

if mat_files:
    file_to_load = os.path.join(path, mat_files[0])
    print(f"Cargando archivo: {file_to_load}")

    # Cargar el archivo .mat
    mat_data = scipy.io.loadmat(file_to_load)

    # Mostrar las variables que contiene el archivo (excluyendo los metadatos de MATLAB)
    variables = {key: type(val) for key, val in mat_data.items() if not key.startswith('__')}
    print("Variables dentro del archivo .mat:")
    for var_name, var_type in variables.items():
        print(f"- {var_name}: {var_type} (Forma/Tamaño: {getattr(mat_data[var_name], 'shape', 'N/A')})")
else:
    print("No se encontraron archivos .mat en la ruta especificada.")'''


class ReadingTests(unittest.TestCase):
    def test_one_source_instruction_per_step_and_letter_pages(self):
        m=pynotas.analizar(MATLAB)
        self.assertEqual(len(m.steps),11)
        self.assertEqual([s.line for s in m.steps],[1,4,5,6,8,11,13,14,15,16,17])
        self.assertTrue(all((p.width,p.height)==(612,792) for p in build(m,pynotas.seleccionar(m)).pages))
        # Comments lead their instruction. Every nonblank source line occurs once.
        visible=[line for s in m.steps for line in s.code.splitlines() if line.strip()]
        self.assertEqual(visible,[line for line in MATLAB.splitlines() if line.strip()])
        self.assertIn('scipy.io.loadmat',m.steps[4].code)
        self.assertNotIn('Usar una función',[s.title for s in m.steps])
        json.dumps(m.to_dict())

    def test_concrete_matlab_explanations_and_scopes(self):
        m=pynotas.analizar(MATLAB)
        text=' '.join(t for s in m.steps for t in s.explanations)
        for phrase in ('existe la ruta path','primer elemento','diccionario','__','type()', 'getattr','dimensiones'):
            self.assertIn(phrase,text)
        self.assertTrue(any('Si es verdadero' in p for p in m.steps[2].scope))
        self.assertTrue(any('En cada vuelta' in p for p in m.steps[8].scope))
        self.assertTrue(any('Si es falso' in p for p in m.steps[-1].scope))
        self.assertIn('no garantiza un orden',' '.join(m.case.facts))

    def test_letter_formats_and_payload_counts(self):
        import pypdfium2 as pdfium
        from PIL import Image
        with patch('builtins.eval',side_effect=AssertionError('Must not evaluate source')):
            pynotas.analizar(MATLAB)
        html=pynotas.generar(MATLAB,oculto=True)
        page_count=html.count('<svg ')
        self.assertGreater(page_count,1)
        self.assertEqual(html.count('<details '),1)
        self.assertNotIn(' open',re.search(r'<details[^>]*>',html)[0])
        self.assertEqual(html.count('data:image/jpeg;base64,'),page_count)
        self.assertIn('download="PyNotas_01.jpg"',html)
        self.assertIn('download="PyNotas_02.jpg"',html)
        jpg=base64.b64decode(re.search(r'data:image/jpeg;base64,([^"]+)',html)[1])
        image=Image.open(io.BytesIO(jpg))
        self.assertEqual(image.info['dpi'],(300,300))
        pdf=base64.b64decode(re.search(r'data:application/pdf;base64,([^"]+)',html)[1])
        with pdfium.PdfDocument(pdf) as doc:
            self.assertEqual(len(doc),page_count)
            self.assertEqual(image.size,(2550,3300))
            text=''
            for page in doc:
                self.assertEqual(page.get_size(),(612,792))
                tp=page.get_textpage();text+=tp.get_text_range();tp.close();page.close()
            self.assertIn('No se encontraron',text)
            self.assertIn('L17',text)

    def test_multiline_comments_unicode_and_same_line_statements(self):
        examples=['# inicio\nseñal = (\n    1 + 2\n)\n# fin', 'a=1; b=2',
                  '@decorador\ndef f(x):\n    return x+1',
                  'if x: a=1\nelse: a=2',
                  'try:\n    a()\nexcept ValueError as e:\n    b(e)\nelse:\n    c()\nfinally:\n    d()',
                  'match x:\n    case 1:\n        print(x)\n    case _:\n        pass']
        for source in examples:
            m=pynotas.analizar(source)
            self.assertTrue(m.steps)
            self.assertTrue(all(1<=s.line<=s.end_line<=len(source.splitlines()) for s in m.steps))
            for page in build(m,pynotas.seleccionar(m)).pages:
                ET.fromstring(page.svg('test'))
                for op in page.ops:
                    if op[0]=='text':
                        _,x,y,text,size,color,font=op
                        self.assertGreaterEqual(x,0)
                        self.assertLessEqual(x+fonts().stringWidth(text,font,size),page.width)
                        self.assertTrue(0<y<page.height)

    def test_unknown_calls_name_the_arguments_without_inventing_domain(self):
        m=pynotas.analizar('y=mi_funcion(datos, nivel=2)',context='vibraciones')
        self.assertIn('mi_funcion',m.steps[0].title)
        self.assertIn('datos, nivel=2',' '.join(m.steps[0].explanations))
        self.assertIsNone(m.case)
        self.assertFalse(m.theories)

    def test_aliases_and_shadowing_do_not_fabricate_matlab_case(self):
        self.assertIsNotNone(pynotas.analizar('from scipy.io import loadmat as leer\nx=leer(ruta)').case)
        self.assertIsNone(pynotas.analizar('scipy=otra_cosa\nx=scipy.io.loadmat(ruta)').case)
        self.assertIsNone(pynotas.analizar('def f(scipy):\n    x=scipy.io.loadmat(ruta)').case)
        self.assertIsNone(pynotas.analizar('x=otro.loadmat(ruta)').case)

    def test_rms_step_retains_expert_operations_and_exact_source(self):
        source='rms = np.sqrt(np.mean(vibracion**2))'
        m=pynotas.analizar(source)
        self.assertEqual(m.steps[0].code,source)
        text=' '.join(m.steps[0].explanations)
        for phrase in ('cuadrado','mean','sqrt','rms'):self.assertIn(phrase,text)
        self.assertIn('rms',[t.key for t in m.theories])

    def test_split_rms_explains_only_what_each_line_does(self):
        m=pynotas.analizar('cuadrados=x**2\npromedio=np.mean(cuadrados)\nrms=np.sqrt(promedio)')
        text=' '.join(m.steps[-1].explanations)
        self.assertIn('raíz cuadrada de promedio',text)
        self.assertNotIn('eleva',text.lower())
        self.assertNotIn('mean',text)

    def test_same_line_statements_keep_separate_explanations(self):
        m=pynotas.analizar('n=len(datos); media=np.mean(datos)')
        self.assertIn('Cuenta los elementos',' '.join(m.steps[0].explanations))
        self.assertIn('promedio',' '.join(m.steps[1].explanations))
        self.assertEqual(len(m.steps),2)

    def test_code_wrapping_keeps_identifiers_and_source(self):
        from pynotas.reading_layout import wrap_code
        line="mat_files = [f for f in os.listdir(path) if f.endswith('.mat')]"
        rows=list(wrap_code(line,302))
        self.assertEqual(''.join(rows),line)
        self.assertTrue(any('endswith' in row for row in rows))


if __name__=='__main__':unittest.main()
