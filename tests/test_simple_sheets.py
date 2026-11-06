import json,re,unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET
import pynotas
from pynotas.lessons import choose_lesson

class SimpleSheetsTests(unittest.TestCase):
    def lesson(self,code):
        m=pynotas.analizar(code)
        return choose_lesson(m,pynotas.seleccionar(m)).key

    def test_sag_topics_from_nested_calls(self):
        examples={
            'df = pd.read_csv(ruta)':'read',
            'calidad = pd.DataFrame({"nulos": df.isna().sum()})':'quality',
            'm = df.duplicated(["ID", "Cycle"], keep=False)':'duplicates',
            'r = df.groupby("ID").agg(n=("Cycle", "size"))':'group',
            'v = pd.DataFrame({"media": df.mean(), "dispersion": df.std()})':'spread',
            'datos = df.loc[mascara].copy()':'selection',
            'r = df.corr()':'correlation',
            'df.to_csv(destino)':'export',
        }
        for code,key in examples.items():self.assertEqual(self.lesson(code),key,code)

    def test_selector_carries_lesson_and_group_only_is_not_a_summary(self):
        model=pynotas.analizar('df = pd.read_csv(ruta)')
        self.assertEqual(pynotas.seleccionar(model).lesson_key,'read')
        self.assertNotEqual(self.lesson('g = df.groupby("ID")'),'group')

    def test_fit_alone_does_not_claim_transformed_output(self):
        self.assertEqual(self.lesson('from sklearn.preprocessing import StandardScaler\ne = StandardScaler()\ne.fit(datos)'), 'scale_fit')

    def test_non_pearson_and_deferred_calls_get_no_pearson_claim(self):
        for code in ['r = df.corr(method="spearman")','r = df.corr(method=personalizado)',
                     'def calcular():\n    return df.corr()', 'funcion = lambda: df.corr()']:
            self.assertNotEqual(self.lesson(code),'correlation',code)

    def test_scaling_only_with_evidence_in_same_cell(self):
        source='from sklearn.preprocessing import StandardScaler\ne = StandardScaler()\ne.fit(datos)\nz = e.transform(otros)'
        self.assertEqual(self.lesson(source),'scale')
        for other in ['e.fit(datos)',source.replace('StandardScaler()','StandardScaler(with_mean=False)'),
                      source.replace('e.fit(datos)','e = desconocido\ne.fit(datos)')]:
            self.assertNotEqual(self.lesson(other),'scale')

    def test_unknown_or_opaque_code_has_no_invented_sensor_theory(self):
        for code,expected in [('misterio(datos)','generic'),('def analizar():\n    df = pd.read_csv(ruta)','function'),
                              ('for x in cosas:\n    e.fit(x)','loop')]:
            self.assertEqual(self.lesson(code),expected)

    def test_apa_removed_and_all_source_retained_for_long_cells(self):
        code='\n'.join('dato_'+str(i)+' = '+str(i) for i in range(10))
        markup=pynotas.generar(code)
        for token in ['APRENDER','PRACTICAR','APLICAR','Comprobar la idea de práctica']:
            self.assertNotIn(token,markup)
        for line in code.splitlines():self.assertIn(line,markup)
        self.assertEqual(markup.count('<details '),1)
        self.assertIn('L10',markup)

    def test_topics_serializable_and_do_not_import_or_execute(self):
        code='x = pd.read_csv("no-existe.csv")'
        with patch('builtins.eval',side_effect=AssertionError),patch('builtins.open',side_effect=AssertionError):
            m=pynotas.analizar(code);html=pynotas.renderizar(m,pynotas.seleccionar(m))
        self.assertEqual(json.loads(json.dumps(m.to_dict()))['blocks'][0]['topics'],['read'])
        self.assertIn('sin ejecutarlo',html)

    def test_text_positions_within_svg_for_unicode_and_long_names(self):
        cases=['import paquete_muy_largo_'+'x'*100+' as '+'a'*100,
               'resultado = '+ 'variable_'+'ñ'*120,
               'if listo:\n    resultado = 1\nelse:\n    resultado = 2']
        for code in cases:
            markup=pynotas.generar(code)
            for svg in re.findall(r'<svg.*?</svg>',markup,re.S):
                elem=ET.fromstring(svg)
                _,_,width,height=map(float,elem.attrib['viewBox'].split())
                for node in elem.iter('{http://www.w3.org/2000/svg}text'):
                    self.assertLess(float(node.attrib['y']),height)
                    self.assertGreaterEqual(float(node.attrib['y']),0)
                    self.assertLess(float(node.attrib['x']),width)

    def test_no_observed_values_or_calls_in_scale_sheet(self):
        code='from sklearn.preprocessing import StandardScaler\ne = StandardScaler()\ne.fit(datos)\nz = e.transform(otros)'
        html=pynotas.generar(code)
        visible=' '.join(''.join(ET.fromstring(svg).itertext()) for svg in re.findall(r'<svg.*?</svg>',html,re.S))
        self.assertNotIn('1355',visible)
        self.assertIn('salida original',html)
        self.assertNotIn('<script',html)

if __name__=='__main__':unittest.main()
