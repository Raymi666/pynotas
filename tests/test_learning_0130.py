"""Regression cases: concrete meaning, cautious identity and readable exports."""
import ast
import builtins
import unittest
from unittest.mock import patch
import pynotas
from pynotas.theory import import_bindings
from pynotas.layout import build, fonts

REPORT = '''import sklearn
import pynotas
import shap

# a classic housing price dataset
X, y = shap.datasets.california(n_points=1000)

X100 = shap.utils.sample(X, 100)  # 100 instances for use as the background distribution

# a simple linear model
model = sklearn.linear_model.LinearRegression()
model.fit(X, y)
'''
KERAS = '''from tensorflow import keras as k
red = k.Sequential([k.layers.Dense(64, activation="relu"), k.layers.Dropout(0.2), k.layers.Dense(1)])
red.compile(optimizer="adam", loss="mse", metrics=["mae"])
historia = red.fit(X_train, y_train, epochs=20, batch_size=32, validation_split=0.2)
salidas = red.predict(X_test)
error = red.evaluate(X_test, y_test)
'''
TORCH = '''import torch
from torch import nn
red = nn.Sequential(nn.Linear(8, 16), nn.ReLU(), nn.Linear(16, 1))
criterio = nn.MSELoss()
opt = torch.optim.Adam(red.parameters(), lr=0.001)
opt.zero_grad()
pred = red(X)
error = criterio(pred, y)
error.backward()
opt.step()
red.eval()
'''
SHAP = '''import shap as sh
exp = sh.Explainer(model.predict, X_ref)
valores = exp(X_test)
sh.plots.beeswarm(valores, max_display=8, show=False)
sh.plots.waterfall(valores[0], max_display=6)
'''


class LearningTests(unittest.TestCase):
    def stages(self, source, **kwargs):
        return pynotas.analizar(source, **kwargs).stages

    def test_report_explains_all_five_tasks_and_self_import(self):
        stages = self.stages(REPORT)
        self.assertEqual(len(stages), 5)
        all_text = ' '.join(s.summary + ' '.join(s.details) for s in stages)
        for part in ('viviendas de California', '1000 registros', '100 filas de X', 'X100', 'X como entradas', 'y como respuestas', 'apuntes visuales'):
            self.assertIn(part, all_text)
        self.assertNotIn('depende de cómo', all_text)
        self.assertIn('todavía no', stages[1].tip)

    def test_sample_keyword_args_and_version_caveat(self):
        s=self.stages('from shap.utils import sample as muestra\nx=muestra(X=tabla,nsamples=12,random_state=3)')[-1]
        self.assertIn('12 filas de tabla',s.summary)
        self.assertIn('SHAP 0.42',s.summary)
        self.assertIn('random_state=3',' '.join(s.details))
        self.assertNotIn('opción adicional',' '.join(s.details))

    def test_keras_nested_layers_and_parameters(self):
        stages=self.stages(KERAS)
        architecture=' '.join(stages[1].details)
        for item in ('64 salidas','ReLU','0.2','1 salidas'):
            self.assertIn(item,architecture)
        compile_details=' '.join(stages[2].details)
        for item in ('optimizer=', 'pesos', 'loss=', 'error', 'metrics='):
            self.assertIn(item,compile_details)
        fit=' '.join(stages[3].details)
        for item in ('epochs=20', 'batch_size=32', 'validation_split=0.2', 'no se usa para ajustar pesos'):
            self.assertIn(item,fit)
        self.assertIn('X_train',stages[3].summary)
        self.assertIn('y_train',stages[3].summary)
        self.assertIn('historia',stages[3].summary)

    def test_keras_add_and_functional_model(self):
        s=self.stages('from keras import Sequential, Model\nfrom keras.layers import Dense\nr=Sequential()\nr.add(Dense(7,activation="sigmoid"))\nm=Model(inputs=x,outputs=y)\nm.compile(loss="mse",optimizer="adam")')
        self.assertIn('7 salidas',' '.join(s[3].details))
        self.assertIn('conecta x con y',s[4].summary)
        self.assertIn('Configuramos m',s[5].summary)

    def test_mlp_parameters(self):
        s=self.stages('from sklearn.neural_network import MLPRegressor\nm=MLPRegressor(hidden_layer_sizes=(32,16),max_iter=200)')[-1]
        self.assertIn('estimar cantidades',s.summary)
        self.assertIn('neuronas',' '.join(s.details))

    def test_torch_separates_forward_backward_step_and_eval(self):
        s=self.stages(TORCH)
        text=' '.join(x.summary+' '.join(x.details) for x in s)
        for item in ('8 valores','16','lr=0.001','no borramos los pesos','pred y y','backward calcula gradientes','ajusta los pesos','ni desactiva por sí solo'):
            self.assertIn(item,text)
        self.assertNotIn('depende de cómo',text)

    def test_shap_reference_differs_from_data_to_explain(self):
        s=self.stages(SHAP)
        self.assertIn('model.predict',s[1].summary)
        self.assertIn('X_ref',' '.join(s[1].details))
        self.assertIn('todavía no son las filas',' '.join(s[1].details))
        self.assertIn('X_test',s[2].summary)
        self.assertIn('aportes',s[4].summary)
        self.assertIn('una sola predicción',s[4].summary)
        self.assertIn('max_display=8',' '.join(s[3].details))
        self.assertIn('no prueban causas',s[1].tip)

    def test_deep_and_tree_shap(self):
        for cls in ('DeepExplainer','TreeExplainer','GradientExplainer','KernelExplainer','LinearExplainer'):
            s=self.stages(f'import shap\ne=shap.{cls}(modelo,referencia)\nv=e.shap_values(muestras)')
            self.assertIn('referencia',' '.join(s[1].details))
            self.assertIn('muestras',s[2].summary)
            self.assertNotIn('probabilidad',s[2].summary)

    def test_cross_cell_identity_and_reassignment(self):
        names=import_bindings(ast.parse('from shap import Explainer as E\ne=E(m,ref)'))
        s=self.stages('valores=e(X)',bindings=names)[0]
        self.assertIn('contribuciones SHAP',s.summary)
        names=import_bindings(ast.parse('e=otra_funcion'),names)
        self.assertIn('depende',self.stages('valores=e(X)',bindings=names)[0].summary)

    def test_custom_names_shadowing_and_control_flow_are_not_frameworks(self):
        for code in ('import otro as shap\ne=shap.Explainer(m,X)',
                     'from otro import Dense\ncapa=Dense(4)',
                     'import shap\nshap=otro\nx=shap.utils.sample(X,100)',
                     'import shap\ndef f(shap):\n    e=shap.Explainer(m,X)',
                     'import shap\nif ok:\n    e=shap.Explainer(m,X)\nv=e(X)',
                     'error=desconocida(X)\nerror.backward()'):
            last=self.stages(code)[-1]
            self.assertIn('depende',last.summary,code)

    def test_scoped_code_keeps_parameters_and_source(self):
        m=pynotas.analizar('from keras import Sequential\nr=Sequential()\nif ok:\n    r.fit(X,y,epochs=3,batch_size=8)')
        s=m.stages[-1]
        self.assertIn('epochs=3',s.summary)
        self.assertIn('lote',s.summary)
        self.assertTrue(s.steps[0].scope)

    def test_unknown_parameters_are_not_given_invented_meanings(self):
        s=self.stages('from keras.layers import Dense\ncapa=Dense(8,opcion_futura=42)')[-1]
        self.assertIn('opcion_futura=42',' '.join(s.details))
        self.assertIn('no está descrito',' '.join(s.details))

    def test_analysis_does_not_import_or_execute_frameworks(self):
        original=builtins.__import__
        def no_framework(name,*args,**kwargs):
            if name.split('.')[0] in {'torch','keras','tensorflow','sklearn','shap'}:
                raise AssertionError('Framework imported during analysis')
            return original(name,*args,**kwargs)
        with patch('builtins.__import__',side_effect=no_framework), patch('builtins.eval',side_effect=AssertionError('eval')):
            for source in (REPORT,KERAS,TORCH,SHAP):
                self.assertTrue(pynotas.analizar(source).stages)

    def test_report_stays_on_one_letter_page_without_orphan_practice(self):
        m=pynotas.analizar(REPORT);doc=build(m,pynotas.seleccionar(m))
        self.assertEqual(len(doc.pages),1)
        self.assertTrue(any(op[0]=='text' and op[3]=='AHORA TE TOCA A TI' for op in doc.pages[0].ops))

    def test_readable_layout_bounds_and_complete_source(self):
        for source in (REPORT,KERAS,TORCH,SHAP):
            m=pynotas.analizar(source);doc=build(m,pynotas.seleccionar(m))
            for page in doc.pages:
                self.assertEqual((page.width,page.height),(612,792))
                for op in page.ops:
                    if op[0]=='text':
                        self.assertLessEqual(op[1]+fonts().stringWidth(op[3],op[6],op[4]),589,(source,op))
                        self.assertTrue(0<op[2]<792,(source,op))
            self.assertEqual(sum(len(s.steps) for s in m.stages),len(m.steps))


if __name__ == '__main__':unittest.main()
