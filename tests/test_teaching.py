import unittest
from unittest.mock import patch
import pynotas
from pynotas.renderers import from_block, main_lines

class TeachingTests(unittest.TestCase):
    def test_mutating_selection_gets_purpose_without_false_dependencies(self):
        block = pynotas.analizar('df_estandarizado[sensores] = valores_estandarizados').blocks[0]
        self.assertEqual(block.kind, 'opaque')
        self.assertEqual(block.title, 'Guardar en la parte elegida')
        self.assertEqual(block.result, 'df_estandarizado[sensores]')
        self.assertEqual(block.writes, ())

    def test_dimensions_and_asserts_are_actions(self):
        blocks = pynotas.analizar('filas, columnas = df.shape\nassert filas > 0').blocks
        self.assertEqual(blocks[0].title, 'Contar filas y columnas')
        self.assertEqual(blocks[0].result, 'filas, columnas')
        self.assertEqual(blocks[1].title, 'Comprobar antes de seguir')

    def test_duplicate_options_are_not_confused(self):
        a = pynotas.analizar('m = df.duplicated(["ID", "Cycle"], keep=False)').blocks[0]
        b = pynotas.analizar('d = df.drop_duplicates(keep=False)').blocks[0]
        self.assertIn('todas', a.summaries[0])
        self.assertIn('todas', b.summaries[0])
        self.assertNotIn('una aparición', b.summaries[0])

    def test_groupby_summary_includes_group(self):
        b = pynotas.analizar('resumen = df.groupby("ID").agg(n=("Cycle", "size"))').blocks[0]
        self.assertEqual(b.title, 'Resumir por ID')

    def test_plain_unknown_fit_is_not_scaler(self):
        b = pynotas.analizar('modelo.fit(X)').blocks[0]
        self.assertNotIn('media', b.title)
        self.assertNotIn('media', b.summaries[0])

    def test_known_default_scaler_in_same_cell(self):
        m = pynotas.analizar('from sklearn.preprocessing import StandardScaler as Escala\ne = Escala()\ne.fit(datos)\nz = e.transform(otros)')
        self.assertEqual(m.blocks[2].title, 'Calcular la media y la escala')
        self.assertEqual(m.blocks[3].title, 'Poner los datos en otra escala')

    def test_scaler_scope_guards(self):
        cases = ['e = otra_cosa()', 'desconocida(e)', 'if condicion:\n    e = otro',
                 'from otro_modulo import e', 'e.with_mean = False', 'e += otro']
        for edit in cases:
            m = pynotas.analizar('from sklearn.preprocessing import StandardScaler\ne = StandardScaler()\n'+edit+'\ne.fit(datos)')
            self.assertNotEqual(m.blocks[-1].title, 'Calcular la media y la escala', edit)

    def test_scaler_options_do_not_invent_centering(self):
        for options in ['with_mean=False','with_std=False','with_mean=opcion','opciones']:
            m = pynotas.analizar('from sklearn.preprocessing import StandardScaler\ne = StandardScaler('+options+')\ne.fit(datos)')
            self.assertNotEqual(m.blocks[-1].title, 'Calcular la media y la escala')

    def test_unknown_calls_and_definitions_do_not_claim_execution(self):
        b = pynotas.analizar('def leer():\n    borrar_datos()').blocks[0]
        self.assertIn('no ejecuta', b.summaries[0])
        b = pynotas.analizar('x = misterio(datos)').blocks[0]
        self.assertEqual(b.title, 'Usar una función')

    def test_primary_surface_leads_with_purpose_and_keeps_code_in_detail(self):
        source='df[sensores] = escalados'
        b=pynotas.analizar(source).blocks[0]
        rows=main_lines(from_block(b))
        self.assertTrue(any(kind=='purpose' for kind,text in rows))
        self.assertFalse(any(kind=='code' for kind,text in rows))
        html=pynotas.generar(source)
        self.assertIn(source,html)
        self.assertEqual(html.count('<details '),1)
        self.assertNotIn('Bloque de código',html)

    def test_lists_are_not_described_as_numeric_sums(self):
        b=pynotas.analizar('columnas = ["ID"] + sensores + ["RUL"]').blocks[0]
        self.assertEqual(b.title, 'Unir listas')

    def test_validation_purposes(self):
        examples = {
            'assert len(a) + len(b) == len(total)': 'Comprobar el total',
            'assert not df.duplicated(["ID", "Cycle"]).any()': 'Comprobar que no se repitan',
            'assert np.isfinite(df.to_numpy()).all()': 'Comprobar los valores numéricos',
            'assert set(a) == set(b)': 'Comprobar los valores conservados',
        }
        for source,title in examples.items():
            self.assertEqual(pynotas.analizar(source).blocks[0].title,title)

    def test_teaching_never_evaluates(self):
        with patch('builtins.eval', side_effect=AssertionError('evaluated')):
            pynotas.generar('df[sensores] = side_effect()')

if __name__=='__main__':unittest.main()
