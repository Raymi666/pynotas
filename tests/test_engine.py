import ast
import json
import unittest
from unittest.mock import patch
from xml.etree import ElementTree
import re

import pynotas
from pynotas.renderers import control_graph, dependency_graph
from pynotas.notebook import SLOT
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output

AVERAGE = '''# Temperaturas registradas durante cuatro mediciones
temperaturas = [60, 65, 70, 75]

# Calculamos la suma de todas las temperaturas
suma = sum(temperaturas)

# Calculamos cuántas mediciones existen
cantidad = len(temperaturas)

# Calculamos la temperatura promedio
promedio = suma / cantidad

# Mostramos el resultado
print(f"Temperatura promedio: {promedio:.1f} °C")'''

DECISION = '''temperatura = 85

if temperatura > 80:
    estado = "ALERTA"
else:
    estado = "NORMAL"

print(f"Estado del equipo: {estado}")'''


class StaticTests(unittest.TestCase):
    def test_auto_formats(self):
        for source, expected in [(AVERAGE, "despiece"), (DECISION, "decisiones"),
                                 ('x = 1\nprint(x)', "flujo")]:
            with self.subTest(expected=expected):
                self.assertEqual(pynotas.seleccionar(pynotas.analizar(source)).format, expected)

    def test_line_trace_and_source(self):
        model = pynotas.analizar(AVERAGE)
        self.assertEqual([b.line for b in model.blocks], [2, 5, 8, 11, 14])
        self.assertEqual(model.source, AVERAGE)
        self.assertEqual(model.blocks[3].expression.children[1].code, 'cantidad')

    def test_dependency_edges(self):
        nodes, edges = dependency_graph(pynotas.analizar(AVERAGE))
        self.assertEqual([(e.source, e.target) for e in edges],
                         [('b1', 'b2'), ('b1', 'b3'), ('b3', 'b4'), ('b2', 'b4'), ('b4', 'b5')])

    def test_reassignment(self):
        _, edges = dependency_graph(pynotas.analizar('x = 1\nx = x + 1\ny = x * 2'))
        self.assertEqual([(e.source,e.target) for e in edges], [('b1','b2'),('b2','b3')])

    def test_augassign_reads_old_target(self):
        _, edges = dependency_graph(pynotas.analizar('x = 1\nx += 2'))
        self.assertEqual(len(edges), 1)

    def test_decision_branches_and_merge(self):
        _, edges = control_graph(pynotas.analizar(DECISION))
        triples = {(e.source, e.target, e.label) for e in edges}
        self.assertIn(('b2', 'b3', 'Verdadero'), triples)
        self.assertIn(('b2', 'b4', 'Falso'), triples)
        self.assertIn(('b3', 'b2_join', ''), triples)
        self.assertIn(('b4', 'b2_join', ''), triples)
        self.assertIn(('b2_join', 'b5', ''), triples)

    def test_no_else_false_reaches_join(self):
        _, edges = control_graph(pynotas.analizar('if x:\n    y = 1\nprint(x)'))
        self.assertTrue(any(e.label == 'Falso' and e.target == 'b1_join' for e in edges))

    def test_elif_and_nested(self):
        source = 'if x:\n    if y:\n        z = 1\nelif w:\n    z = 2\nelse:\n    z = 3'
        nodes, edges = control_graph(pynotas.analizar(source))
        self.assertEqual(sum(n.kind == 'decision' for n in nodes), 3)
        self.assertEqual(sum(e.label == 'Falso' for e in edges), 3)

    def test_raise_does_not_join(self):
        nodes, edges = control_graph(pynotas.analizar('if x:\n    raise ValueError()\nelse:\n    y = 1\nprint(y)'))
        self.assertFalse(any(e.source == 'b2' for e in edges))

    def test_both_branches_stop(self):
        nodes, edges = control_graph(pynotas.analizar('if x:\n    raise A\nelse:\n    raise B\nprint(1)'))
        self.assertEqual(len(nodes), 3)

    def test_serializable_no_ast(self):
        data = json.loads(json.dumps(pynotas.analizar(DECISION).to_dict()))
        self.assertEqual(data['schema_version'], '0.11')

    def test_no_evaluation(self):
        with patch('builtins.eval', side_effect=AssertionError('eval forbidden')):
            html = pynotas.generar('x = forbidden_side_effect() / 0')
        self.assertIn('forbidden_side_effect', html)

    def test_unicode_multiline(self):
        model = pynotas.analizar('área = (\n    2 + 3\n)\nprint(área)')
        self.assertEqual(model.blocks[0].end_line, 3)
        self.assertEqual(model.blocks[0].expression.code, '2 + 3')

    def test_escaping(self):
        html = pynotas.generar('x = "<script>alert(1)</script>"', objetivo='<img onerror="bad">')
        self.assertNotIn('<script>', html)
        self.assertNotIn('<img ', html)
        self.assertIn('&lt;script&gt;', html)

    def test_svg_valid_and_unique(self):
        first, second = pynotas.generar(AVERAGE), pynotas.generar(AVERAGE)
        ids = re.findall(r'id="([^"]+)"', first + second)
        self.assertEqual(len(ids), len(set(ids)))
        for source in (AVERAGE, DECISION, 'x=1\nprint(x)'):
            for svg in re.findall(r'<svg.*?</svg>', pynotas.generar(source), re.S):
                ElementTree.fromstring(svg)

    def test_all_renderers_use_simple_sheet(self):
        for source, fmt in [(AVERAGE,'despiece'),(AVERAGE,'flujo'),(DECISION,'decisiones')]:
            html = pynotas.generar(source, formato=fmt)
            for token in ('<svg', '<line ', 'VAMOS LÍNEA A LÍNEA', 'PASO A PASO', '<details id='):
                self.assertIn(token, html)

    def test_opaque_scopes_are_not_execution(self):
        for source in ['def f():\n    if x:\n        print(x)', 'for x in xs:\n    print(x)',
                       'x: int', 'xs[0] = 3', 'x = [i*i for i in xs]']:
            model = pynotas.analizar(source)
            self.assertEqual(pynotas.seleccionar(model).format, 'flujo')
            self.assertTrue(model.notes)
            self.assertFalse(model.blocks[0].body)

    def test_format_validation(self):
        for source, fmt in [(AVERAGE,'wrong'), (AVERAGE,'decisiones'), (DECISION,'despiece')]:
            with self.assertRaises(ValueError):
                pynotas.generar(source, formato=fmt)

    def test_invalid_and_limits(self):
        with self.assertRaises(SyntaxError):
            pynotas.generar('if :')
        with self.assertRaises(ValueError):
            pynotas.generar('#' * 60001)
        with self.assertRaises(ValueError):
            pynotas.generar('\n'.join(f'x{i} = {i}' for i in range(61)))

    def test_empty(self):
        self.assertIn('No hay instrucciones', pynotas.generar('# comentario'))


class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shell = InteractiveShell.instance()

    def setUp(self):
        pynotas.desactivar(shell=self.shell)
        pynotas.activar(shell=self.shell)
        self.observer = getattr(self.shell, SLOT)
        self.before = self.observer.generated

    def tearDown(self):
        pynotas.desactivar(shell=self.shell)

    def run_cell(self, source):
        with capture_output() as capture:
            result = self.shell.run_cell(source, store_history=True)
        return result, capture

    def test_single_execution_and_display(self):
        self.shell.user_ns['pynotas_counter'] = 0
        result, captured = self.run_cell('pynotas_counter += 1\nprint(pynotas_counter)')
        self.assertIsNone(result.error_in_exec)
        self.assertEqual(self.shell.user_ns['pynotas_counter'], 1)
        self.assertEqual(captured.stdout, '1\n')
        self.assertEqual(self.observer.generated, self.before + 1)
        self.assertEqual(len(captured.outputs), 1)

    def test_repeated_activation_and_deactivation(self):
        pynotas.activar(shell=self.shell)
        pynotas.activar(shell=self.shell)
        self.run_cell('x = 2')
        self.assertEqual(self.observer.generated, self.before + 1)
        pynotas.desactivar(shell=self.shell)
        pynotas.desactivar(shell=self.shell)
        self.run_cell('x = 3')
        self.assertEqual(self.observer.generated, self.before + 1)

    def test_original_average_output(self):
        result, captured = self.run_cell(AVERAGE)
        self.assertEqual(captured.stdout, 'Temperatura promedio: 67.5 °C\n')
        self.assertEqual(self.shell.user_ns['promedio'], 67.5)
        self.assertIsNone(result.error_in_exec)

    def test_decision_boundary(self):
        for value, expected in [(75, 'NORMAL'), (80, 'NORMAL'), (85, 'ALERTA'), (95,'ALERTA')]:
            result, captured = self.run_cell(DECISION.replace('= 85', f'= {value}'))
            self.assertEqual(captured.stdout, f'Estado del equipo: {expected}\n')
            self.assertEqual(self.shell.user_ns['estado'], expected)

    def test_error_preserved_and_next_cell_works(self):
        result, captured = self.run_cell('1 / 0')
        self.assertIsInstance(result.error_in_exec, ZeroDivisionError)
        self.assertEqual(self.observer.generated, self.before)
        self.run_cell('x = 1')
        self.assertEqual(self.observer.generated, self.before + 1)

    def test_syntax_error(self):
        result, captured = self.run_cell('if :')
        self.assertIsNotNone(result.error_before_exec)
        self.assertEqual(self.observer.generated, self.before)

    def test_render_failure_does_not_change_cell(self):
        with patch('pynotas.notebook.render', side_effect=RuntimeError('test failure')):
            result, captured = self.run_cell('print("intacto")')
        self.assertEqual(captured.stdout, 'intacto\n')
        self.assertIsNone(result.error_in_exec)
        self.assertIn('test failure', self.observer.last_error)

    def test_magic_skipped(self):
        result, captured = self.run_cell('%pwd')
        self.assertIsNone(result.error_in_exec)
        self.assertEqual(self.observer.generated, self.before)

    def test_skip_directive(self):
        self.run_cell('# pynotas: omitir\nx = 1')
        self.assertEqual(self.observer.generated, self.before)

    def test_management_cell_skipped(self):
        self.run_cell('import pynotas\npynotas.diagnostico()')
        self.assertEqual(self.observer.generated, self.before)


if __name__ == '__main__':
    unittest.main(verbosity=2)
