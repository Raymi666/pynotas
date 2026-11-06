import ast
import unittest
from unittest.mock import patch
import pynotas
from pynotas.theory import import_bindings
from pynotas.layout import build,fonts,WIDTH,HEIGHT
from pynotas.exports import pdf_bytes

class MLTests(unittest.TestCase):
    def keys(self,code,**kwargs):return [t.key for t in pynotas.analizar(code,**kwargs).theories]
    def test_split_is_only_recognized_with_identity(self):
        self.assertEqual(self.keys('train_test_split(X,y)'),[])
        self.assertEqual(self.keys('from sklearn.model_selection import train_test_split as dividir\na=dividir(X,y)'),['split'])
    def test_across_cells_tracks_models(self):
        names={}
        for code in ['from sklearn.neural_network import MLPClassifier as Red','modelo=Red(hidden_layer_sizes=(8,))']:
            names=import_bindings(ast.parse(code),names)
        self.assertEqual(self.keys('modelo.fit(X,y)',bindings=names),['train','mlp'])
        self.assertEqual(self.keys('pred=modelo.predict(X)',bindings=names),['predict','mlp'])
    def test_pipeline_and_nested_models(self):
        code='from sklearn.pipeline import make_pipeline\nfrom sklearn.preprocessing import StandardScaler\nfrom sklearn.linear_model import LogisticRegression\nmodelo=make_pipeline(StandardScaler(),LogisticRegression())\nmodelo.fit(X,y)'
        self.assertEqual(set(self.keys(code)),{'pipeline','scaling','logistic','train'})
    def test_transform_methods_describe_action(self):
        m=pynotas.analizar('from sklearn.decomposition import PCA\np=PCA(2)\nz=p.fit_transform(X)')
        self.assertIn('Aprende los parámetros y transforma',m.blocks[-1].summaries[0])
    def test_keras_alias_and_methods(self):
        code='from tensorflow import keras as k\nred=k.Sequential([k.layers.Dense(4,activation="relu"),k.layers.Dense(1)])\nred.compile(optimizer="adam",loss="mse")\nhistoria=red.fit(X,y,epochs=4)\nerror=red.evaluate(X_test,y_test)'
        self.assertEqual(self.keys(code),['sequential','dense','compile','nn_train','evaluate'])
        names=import_bindings(ast.parse(code))
        self.assertEqual(names['red'],'@keras.Sequential')
        self.assertEqual(names['historia'],'')
    def test_shadowing_and_scopes_remove_expertise(self):
        prefix='from sklearn.linear_model import LinearRegression\nmodelo=LinearRegression()\n'
        for change in ['modelo=otro','modelo.fit=otra','del modelo','if condicion:\n    modelo=otro']:
            names=import_bindings(ast.parse(prefix+change))
            self.assertEqual(self.keys('modelo.fit(X,y)',bindings=names),[],change)
        for code in ['modelo.fit(X,y)', 'def preparar():\n    from sklearn.neural_network import MLPClassifier\n    return MLPClassifier()',
                     'from otro import Dense\ncapa=Dense(8)']:
            self.assertEqual(self.keys(code),[],code)
    def test_no_deferred_or_comprehension_theory(self):
        prefix='from sklearn.linear_model import LinearRegression\n'
        for code in ['f=lambda: LinearRegression()', 'a=[LinearRegression() for LinearRegression in cosas]']:
            self.assertEqual(self.keys(prefix+code),[])
    def test_context_does_not_invent_theory(self):
        self.assertEqual(self.keys('x=desconocida(datos)',context='redes_neuronales'),[])
    def test_fit_return_types(self):
        code='from sklearn.linear_model import LinearRegression\nm=LinearRegression().fit(X,y)'
        bindings=import_bindings(ast.parse(code))
        self.assertIn('linear',self.keys('m.predict(X)',bindings=bindings))
    def test_metrics_reference_real_vs_predicted(self):
        code='from sklearn.metrics import accuracy_score,confusion_matrix,mean_squared_error\na=accuracy_score(y,p)\nc=confusion_matrix(y,p)\ne=mean_squared_error(y,p)'
        self.assertEqual(self.keys(code),['accuracy','confusion','mse'])
    def test_never_calls_user_code(self):
        with patch('builtins.eval',side_effect=AssertionError):
            m=pynotas.analizar('from keras import Sequential\nred=Sequential()\nred.fit(destructive(),y)')
        self.assertIn('nn_train',[t.key for t in m.theories])

class VisualTests(unittest.TestCase):
    def test_new_illustrations_and_bounds(self):
        cases=['rms=np.sqrt(np.mean(x**2))',
               'from sklearn.model_selection import train_test_split\na,b=train_test_split(X)',
               'from keras import Sequential\nfrom keras.layers import Dense\nred=Sequential([Dense(8),Dense(1)])',
               'x=1\ny=2\nz=x+y',
               'if temperatura>80:\n    estado="ALERTA"\nelse:\n    estado="NORMAL"']
        for source in cases:
            m=pynotas.analizar(source);doc=build(m,pynotas.seleccionar(m))
            for page in doc.pages:
                for op in page.ops:
                    if op[0]=='text':
                        _,x,y,s,size,color,font=op
                        self.assertLessEqual(x+fonts().stringWidth(s,font,size),page.width+1,(source,s))
                        self.assertTrue(0<y<page.height,(source,s))
            self.assertTrue(pdf_bytes(doc).startswith(b'%PDF'))
    def test_rms_fits_one_page_and_source_preserved(self):
        source='rms=np.sqrt(np.mean(x**2))\nprint(rms)'
        m=pynotas.analizar(source);d=build(m,pynotas.seleccionar(m))
        self.assertEqual(len(d.pages),1)
        h=pynotas.generar(source,descargas=False,oculto=True)
        self.assertIn(source,h)
        self.assertEqual(h.count('<details '),1)
        self.assertIn('VAMOS LÍNEA A LÍNEA',h)
    def test_syntax_colors_preserve_full_text(self):
        from pynotas.syntax import colored_lines
        code='texto = "ñ < hola"\n\t# comentario'
        lines=list(colored_lines(code))
        self.assertEqual('\n'.join(a for a,b in lines),code.expandtabs(4))
        for a,b in lines:self.assertEqual(len(a),len(b))
    def test_long_cell_uses_readable_letter_pages(self):
        code='\n'.join(f'variable_{i} = {i}' for i in range(30))
        m=pynotas.analizar(code);d=build(m,pynotas.seleccionar(m))
        self.assertGreater(len(d.pages),1)
        self.assertTrue(all((p.width,p.height)==(612,792) for p in d.pages))
        self.assertIn('L30',' '.join(o[3] for p in d.pages for o in p.ops if o[0]=='text'))
