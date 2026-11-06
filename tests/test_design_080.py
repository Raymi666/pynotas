"""Visual-routing and export regressions, independent of user-code execution."""
from dataclasses import replace
import unittest
from xml.etree import ElementTree

import pynotas
from pynotas.artwork import theme_for
from pynotas.exports import pdf_bytes
from pynotas.layout import build, WIDTH, HEIGHT, fonts
from pynotas.theory import Theory, CATALOG
from pynotas.ml import CATALOG as ML_CATALOG


class EditorialDesignTests(unittest.TestCase):
    def document(self, source):
        model=pynotas.analizar(source)
        return build(model,pynotas.seleccionar(model))

    def test_automatic_visual_family_matches_operation(self):
        cases={
            'rms=np.sqrt(np.mean(x**2))':'signal',
            'from sklearn.neural_network import MLPClassifier\nm=MLPClassifier()':'network',
            'from sklearn.model_selection import train_test_split\na,b=train_test_split(X)':'learning',
            'if temperatura>80:\n    estado="ALERTA"':'decision',
            'import numpy as np\nimport matplotlib.pyplot as plt':'resources',
            'promedio=suma/cantidad':'expression',
            'desconocida(datos)':'code',
        }
        for source,expected in cases.items():
            model=pynotas.analizar(source)
            self.assertEqual(theme_for(model,pynotas.seleccionar(model)).kind,expected,source)

    def test_signal_diagram_contains_reviewed_transformation(self):
        doc=self.document('rms=np.sqrt(np.mean(x**2))')
        texts=' '.join(o[3] for p in doc.pages for o in p.ops if o[0]=='text')
        for label in ['al cuadrado','promedio','raíz cuadrada','Guardamos el resultado en rms']:
            self.assertIn(label,texts)
        self.assertEqual(len(doc.pages),1)

    def test_unknown_code_keeps_generic_artwork_even_with_context(self):
        m=pynotas.analizar('r=mi_funcion(x)',context='redes_neuronales')
        self.assertNotEqual(theme_for(m,pynotas.seleccionar(m)).kind,'network')

    def test_short_decision_keeps_both_branches_on_one_page(self):
        doc=self.document('temperatura = 85\nif temperatura > 80:\n    estado = "ALERTA"\nelse:\n    estado = "NORMAL"\nprint(estado)')
        self.assertEqual(len(doc.pages),1)
        text=' '.join(o[3] for p in doc.pages for o in p.ops if o[0]=='text')
        for word in ('temperatura > 80','Si se cumple','Si no se cumple','ALERTA','NORMAL','VAMOS LÍNEA A LÍNEA'):
            self.assertIn(word,text)

    def test_forced_flow_keeps_condition_diagram(self):
        m=pynotas.analizar('if temperatura>80:\n    estado="ALERTA"')
        doc=build(m,pynotas.seleccionar(m,'flujo'))
        text=' '.join(o[3] for p in doc.pages for o in p.ops if o[0]=='text')
        self.assertIn('Si se cumple',text)

    def test_all_reviewed_theories_fit_visual_bounds(self):
        base=pynotas.analizar('x=1')
        for key,entry in {**CATALOG,**ML_CATALOG}.items():
            title,idea,meaning,steps,source=entry
            model=replace(base,theories=(Theory(key,title,idea,meaning,steps,source,1),))
            for page in build(model,pynotas.seleccionar(model)).pages:
                for op in page.ops:
                    if op[0]=='text':
                        _,x,y,s,size,color,font=op
                        self.assertGreaterEqual(x,0,(key,s))
                        self.assertLessEqual(x+fonts().stringWidth(s,font,size),page.width+1,(key,s))
                        self.assertTrue(0<y<page.height,(key,s))

    def test_curve_geometry_is_valid_in_both_export_formats(self):
        doc=self.document('from sklearn.neural_network import MLPClassifier\nm=MLPClassifier()')
        # The shared path primitive remains exportable even though the reading
        # layout no longer inserts a decorative neural-network diagram.
        doc.pages[0].path([('M',30,100),('C',50,100,70,120,90,120)],'#007B74')
        paths=[o for o in doc.pages[0].ops if o[0]=='path']
        self.assertTrue(paths)
        for _,commands,stroke,fill,width in paths:
            for command in commands:
                for i,coordinate in enumerate(command[1:]):
                    self.assertTrue(0<=coordinate<= (WIDTH if i%2==0 else HEIGHT))
        svg=ElementTree.fromstring(doc.pages[0].svg('test'))
        self.assertTrue(list(svg.iter('{http://www.w3.org/2000/svg}path')))
        self.assertTrue(pdf_bytes(doc).startswith(b'%PDF-'))


if __name__=='__main__':unittest.main()
