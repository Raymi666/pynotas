"""Output meaning, loop scope, source fidelity, and no runtime evaluation."""
import ast
import builtins
import unittest
from unittest.mock import patch
import pynotas
from pynotas.theory import import_bindings
from pynotas.layout import build, fonts


TABLE = 'import pandas as pd\ndf = pd.DataFrame(datos)\n'


class DataReadingTests(unittest.TestCase):
    def last(self, source, **kwargs):
        return pynotas.analizar(source, **kwargs).steps[-1]

    def test_loop_explains_data_operation_and_source_collection(self):
        source = TABLE + 'for col in cols:\n    print(df[col].unique())'
        step = self.last(source)
        for text in ('Mostramos los valores distintos', 'cada columna de df',
                     'recorremos en cols', 'sin repetirlos', 'no cambia la tabla original'):
            self.assertIn(text, step.brief)
        self.assertNotIn('Mostramos df[col].unique()', step.brief)
        self.assertNotIn('Si df', step.brief)
        self.assertTrue(step.scope)

    def test_unknown_notebook_table_is_qualified_once_not_asserted(self):
        step = self.last('for nombre in columnas:\n    print(tabla[nombre].unique())')
        self.assertTrue(step.brief.startswith('Si tabla es una tabla de pandas, mostramos'))
        self.assertIn('recorremos en columnas', step.brief)

    def test_explicit_alias_and_previous_cell_preserve_table_origin(self):
        names = import_bindings(ast.parse('from pandas import read_csv as leer\ntabla=leer("datos.csv")'))
        step = self.last('for campo in campos:\n    print(tabla[campo].unique())', bindings=names)
        self.assertIn('cada columna de tabla', step.brief)
        self.assertNotIn('Si tabla', step.brief)
        names = import_bindings(ast.parse('tabla=otro_objeto'), names)
        self.assertNotIn('valores distintos', self.last('print(tabla[campo].unique())', bindings=names).brief)

    def test_print_arguments_and_fstrings_explain_nested_unique(self):
        for expression in ('print(col, df[col].unique())',
                           'print(f"Columna {col}: {df[col].unique()}")',
                           'print("Valores:", df[col].unique(), sep=" | ", end="!")'):
            step = self.last(TABLE + 'for col in cols:\n    ' + expression)
            self.assertIn('valores distintos de cada columna', step.brief)
            self.assertIn('cols', step.brief)
        self.assertIn('sep=', step.brief)
        self.assertIn('end=', step.brief)

    def test_len_counts_and_assignment_keeps_destination(self):
        for expr in ('print(len(df[col].unique()))', 'cantidad=len(df[col].unique())'):
            step = self.last(TABLE + 'for col in cols:\n    ' + expr)
            self.assertIn('valores distintos', step.brief)
            self.assertIn('cantidad' if expr.startswith('print') else 'Contamos', step.brief)
        self.assertIn('Guardamos el resultado en cantidad', step.brief)
        step = self.last(TABLE + 'valores=df["estado"].unique()')
        self.assertIn("columna 'estado'", step.brief)
        self.assertIn('Guardamos el resultado en valores', step.brief)

    def test_file_output_does_not_claim_normal_cell_output(self):
        step = self.last(TABLE + 'for col in cols:\n    print(df[col].unique(), file=archivo)')
        self.assertIn('Enviamos los valores distintos', step.brief)
        self.assertIn('file=archivo', step.brief)
        self.assertNotIn('Mostramos', step.brief)
        self.assertIn('Mostramos', self.last(TABLE + 'print(df["x"].unique(), file=None)').brief)

    def test_display_with_explicit_import_and_series_constructor(self):
        source = 'from pandas import Series as S\nfrom IPython.display import display as ver\ns=S(datos)\nver(s.unique())'
        self.assertIn('Mostramos los valores distintos de s', self.last(source).brief)
        self.assertNotIn('valores distintos', self.last('objeto.unique()').brief)

    def test_custom_objects_shadowed_print_and_unsupported_selection(self):
        for source in ('df=otro_objeto\nprint(df[col].unique())',
                       'import otro as pd\ndf=pd.DataFrame(datos)\nprint(df[col].unique())',
                       TABLE + 'print=mi_funcion\nprint(df[col].unique())',
                       TABLE + 'len=mi_funcion\nprint(len(df[col].unique()))',
                       TABLE + 'df.unique=otra\nprint(df[col].unique())',
                       TABLE + 'print(df[["x", "y"]].unique())',
                       TABLE + 'print(df[1:3].unique())',
                       TABLE + 'print(df[col].unique(opcion=True))',
                       TABLE + 'print(df[col].unique(), **opciones)',
                       TABLE + 'print((col:="otra"),df[col].unique())'):
            self.assertNotIn('valores distintos', self.last(source).brief, source)

    def test_chunked_csv_read_is_not_misidentified_as_table(self):
        for options in ('chunksize=100', 'iterator=True', '**opciones', 'chunksize=tamano'):
            source=f'import pandas as pd\ndf=pd.read_csv("x.csv",{options})\nprint(df[col].unique())'
            self.assertNotIn('valores distintos', self.last(source).brief)
        source='import pandas as pd\ndf=pd.read_csv("x.csv",iterator=False,chunksize=None)\nprint(df[col].unique())'
        self.assertNotIn('Si df', self.last(source).brief)
        self.assertIn('valores distintos', self.last(source).brief)

    def test_loop_relation_does_not_leak_or_survive_reassignment(self):
        for tail in ('col="otra"\n    print(df[col].unique())',
                     'cols=otras\n    print(df[col].unique())',
                     'if cambiar:\n        col="otra"\n    print(df[col].unique())'):
            step=self.last(TABLE+'for col in cols:\n    '+tail)
            self.assertNotIn('recorremos en cols',step.brief)
        step=self.last(TABLE+'for col in cols:\n    print(df[col].unique())\nprint(df[col].unique())')
        self.assertNotIn('recorremos en cols',step.brief)
        step=self.last(TABLE+'for col in cols:\n    def tarea():\n        print(df[col].unique())')
        self.assertNotIn('recorremos en cols',step.brief)

    def test_nested_and_conditional_scopes_use_the_nearest_loop(self):
        source=TABLE+'for col in cols:\n    for col in otras:\n        if revisar:\n            print(df[col].unique())'
        step=self.last(source)
        self.assertIn('recorremos en otras',step.brief)
        self.assertNotIn('recorremos en cols',step.brief)
        self.assertTrue(any('Si es verdadero' in s for s in step.scope))

    def test_analysis_and_export_do_not_import_or_run_student_code(self):
        original=builtins.__import__
        def guarded(name,*args,**kwargs):
            if name=='pandas':raise AssertionError('No pandas import during static analysis')
            return original(name,*args,**kwargs)
        with patch('builtins.eval',side_effect=AssertionError('No eval')), patch('builtins.__import__',side_effect=guarded):
            model=pynotas.analizar(TABLE+'for col in cols:\n    print(df[col].unique())')
            self.assertIn('valores distintos',model.steps[-1].brief)

    def test_source_lines_and_exported_card_remain_legible(self):
        source=TABLE+'cols=["estado", "equipo"]\nfor col in cols:\n    print(df[col].unique())'
        model=pynotas.analizar(source)
        self.assertEqual('\n'.join(s.code for s in model.steps),source)
        self.assertEqual(model.steps[-1].line,5)
        self.assertIn('valores distintos',model.stages[-1].summary)
        doc=build(model,pynotas.seleccionar(model))
        self.assertEqual(len(doc.pages),1)
        texts=[op for p in doc.pages for op in p.ops if op[0]=='text']
        self.assertTrue(any('valores distintos' in op[3] for op in texts))
        for _,x,y,text,size,_,font in texts:
            self.assertLessEqual(x+fonts().stringWidth(text,font,size),588)
            self.assertTrue(0<y<792)


if __name__=='__main__':
    unittest.main()
