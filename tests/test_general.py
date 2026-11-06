import json,os,re,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
import pynotas
from pynotas.analyzer import walk_details
from pynotas.renderers import control_graph

CASES = {
 'variables': 'nombre = "SAG"\nactivo = True\nvalor = None',
 'arithmetic': 'a = 12\nb = 3\nr = (a + b) / b',
 'unpacking': 'primero, segundo = (1, 2)',
 'selection': 'xs = [1,2,3]\nparte = xs[1:]',
 'dictionary': 'opciones = {"umbral": 80}\nx = opciones["umbral"]',
 'list_comprehension': 'dobles = [x*2 for x in range(4) if x > 0]',
 'generator': 'g = (x*2 for x in range(4))',
 'lambda': 'f = lambda x: x+1\nr = f(3)',
 'f_string': 'valor = 4\ntexto = f"Lectura: {valor:.1f}"',
 'condition': 'if dato > 80:\n    salida = "alto"\nelse:\n    salida = "bajo"',
 'for': 'total = 0\nfor x in [1,2,3]:\n    total += x\nprint(total)',
 'while': 'n = 3\nwhile n > 0:\n    n -= 1\nelse:\n    print("fin")',
 'function': 'def promedio(xs):\n    return sum(xs)/len(xs)\nx = promedio([60,65,70,75])',
 'nested': 'def f(xs):\n    for x in xs:\n        if x > 0:\n            return x\n    return None',
 'control': 'for x in xs:\n    if x == 0:\n        continue\n    if x < 0:\n        break',
 'try': 'try:\n    x = float(texto)\nexcept ValueError:\n    x = None\nelse:\n    print(x)\nfinally:\n    print("fin")',
 'context': 'with open("archivo.csv") as f:\n    texto = f.read()',
 'class': 'class Sensor:\n    def __init__(self, valor):\n        self.valor = valor\n    def leer(self):\n        return self.valor',
 'match': 'match valor:\n    case 0:\n        salida = "cero"\n    case _ if valor > 0:\n        salida = "positivo"',
 'async': 'async def leer():\n    resultado = await obtener()\n    return resultado',
 'imports': 'import math as m\nfrom collections import Counter\nc = Counter([1,1,2])',
 'unknown': 'import biblioteca_que_no_existe\nx = biblioteca_que_no_existe.misterio(datos)',
 'annotation': 'x: int\nx = 2',
 'delete': 'x = [1,2]\ndel x[0]',
 'pandas': 'tabla = pd.read_csv(ruta)\nresumen = tabla.groupby("ID").agg(n=("Cycle","size"))',
 'numpy': 'x = np.array([1,2,3])\npromedio = np.mean(x)',
 'matplotlib': 'plt.plot(tiempo, senal)\nplt.show()',
 'sklearn': 'from sklearn.preprocessing import StandardScaler\ns = StandardScaler()\ns.fit(X)\nZ = s.transform(X)',
}

class GeneralTests(unittest.TestCase):
 def test_syntax_matrix_is_static_serializable_and_valid_svg(self):
  for name,source in CASES.items():
   with self.subTest(name=name), patch('builtins.eval',side_effect=AssertionError('eval forbidden')):
    m=pynotas.analizar(source);json.dumps(m.to_dict());markup=pynotas.generar(source)
    self.assertNotIn('PRACTICAR',markup)
    self.assertNotIn('APLICAR',markup)
    for svg in re.findall(r'<svg.*?</svg>',markup,re.S):ET.fromstring(svg)
    for b in walk_details(m.blocks):
     self.assertGreaterEqual(b.line,1);self.assertLessEqual(b.end_line,len(source.splitlines()))

 def test_function_body_explained_but_not_a_top_level_branch(self):
  m=pynotas.analizar(CASES['nested'])
  self.assertEqual(pynotas.seleccionar(m).format,'flujo')
  nodes,_=control_graph(m);self.assertEqual(len(nodes),1)
  self.assertTrue(m.blocks[0].sections)
  markup=pynotas.generar(CASES['nested'])
  self.assertIn('Entregar la respuesta',markup);self.assertIn('Dentro de la función',markup)

 def test_loop_else_and_error_sections_preserve_distinct_meaning(self):
  m=pynotas.analizar(CASES['while']);self.assertEqual(m.blocks[1].sections[1].label,'Al terminar sin break')
  m=pynotas.analizar(CASES['try']);self.assertEqual(len(m.blocks[0].sections),4)
  self.assertIn('ValueError',m.blocks[0].sections[1].label)

 def test_nested_instructions_count_towards_limit(self):
  source='def f():\n'+'\n'.join('    x'+str(i)+' = 1' for i in range(60))
  with self.assertRaisesRegex(ValueError,'60 instrucciones'):pynotas.generar(source)

 def test_generator_does_not_claim_list_materialized(self):
  b=pynotas.analizar(CASES['generator']).blocks[0]
  self.assertEqual(b.title,'Preparar un generador')
  self.assertIn('no materializa',b.summaries[0])

 def test_file_export_never_executes_and_preserves_files(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'prueba.py';flag=Path(td)/'efecto.txt'
   p.write_text(f'from pathlib import Path\nPath({str(flag)!r}).write_text("no ejecutar")')
   result=pynotas.explicar_archivo(p)
   self.assertFalse(flag.exists());self.assertTrue(result.read_text().startswith('<!doctype html>'))
   with self.assertRaises(FileExistsError):pynotas.explicar_archivo(p)
   with self.assertRaises(ValueError):pynotas.explicar_archivo(p,p,sobrescribir=True)
   result.write_text('anterior')
   with self.assertRaises(SyntaxError):pynotas.guardar('if :',result,sobrescribir=True)
   self.assertEqual(result.read_text(),'anterior')

 def test_encoding_and_cli(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'acentos.py';p.write_bytes('# coding: latin-1\naño = 2026'.encode('latin-1'))
   r=subprocess.run([sys.executable,'-m','pynotas',str(p)],capture_output=True,text=True)
   self.assertEqual(r.returncode,0,r.stderr)
   self.assertIn('año',p.with_suffix('.pynotas.html').read_text())
   r=subprocess.run([sys.executable,'-m','pynotas',str(p)],capture_output=True,text=True)
   self.assertEqual(r.returncode,2)

 def test_async_has_own_lesson_and_code_preserves_spaces(self):
  m=pynotas.analizar(CASES['async'])
  self.assertEqual(pynotas.seleccionar(m).lesson_key,'async_function')
  self.assertIn('xml:space="preserve"',pynotas.generar(CASES['function']))

 def test_options_validated_at_api(self):
  with self.assertRaises(TypeError):pynotas.generar('x=1',objetivo=1)
  with self.assertRaises(ValueError):pynotas.generar('x=1',nivel='desconocido')

if __name__=='__main__':unittest.main()
