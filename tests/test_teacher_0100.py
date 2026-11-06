"""Meaning, source fidelity and readability of the beginner-first explanation."""
import unittest
from unittest.mock import patch
import pynotas
from pynotas.layout import build, fonts


class TeacherTests(unittest.TestCase):
    def steps(self, source):
        return pynotas.analizar(source).steps

    def test_mean_names_input_operation_and_destination(self):
        step=self.steps('promedio=np.mean(cuadrados)')[0]
        for text in ('cuadrados','sumamos','dividimos','cantidad de datos','en promedio'):
            self.assertIn(text,step.brief)
        self.assertIn('partes iguales',step.aside)

    def test_mean_with_axis_does_not_claim_overall_mean(self):
        text=self.steps('medias=np.mean(matriz,axis=0,where=mascara)')[0].brief
        self.assertNotIn('cantidad de datos',text)
        self.assertIn('axis=0',text)
        self.assertIn('where=mascara',text)
        self.assertIn('en medias',text)

    def test_aliases_resolve_but_reassignment_and_custom_module_do_not(self):
        text=self.steps('from numpy import mean as media\nx=media(datos)')[-1].brief
        self.assertIn('sumamos',text)
        for code in ('np=otro\nx=np.mean(datos)', 'import mi_modulo as np\nx=np.mean(datos)',
                     'def f(np):\n    return_value=np.mean(datos)', 'sum=otra\nx=sum(datos)'):
            text=self.steps(code)[-1].brief
            self.assertNotIn('sumamos',text.lower())
            self.assertIn('depende',text)

    def test_unknown_call_retains_inputs_and_destination(self):
        text=self.steps('salida=mi_funcion(datos,nivel=2)')[0].brief
        for token in ('mi_funcion','datos','nivel=2','salida','depende'):self.assertIn(token,text)

    def test_analogy_budget_is_bounded_and_deterministic(self):
        source='import numpy as np\np=np.mean(x)\nq=np.mean(y)\nprint(p)'
        first=self.steps(source)
        self.assertEqual(first,self.steps(source))
        self.assertEqual(sum(bool(s.aside) for s in first),2)
        self.assertTrue(all(s.brief for s in first))

    def test_addition_and_multiplication_allow_non_numeric_types(self):
        self.assertIn('textos o listas',self.steps('x=a+b')[0].brief)
        self.assertIn('se repite',self.steps('x=a*3')[0].brief)

    def test_print_format_does_not_change_stored_value(self):
        text=self.steps('print(f"RMS: {rms:.3f}")')[0].brief
        for part in ('rms','3 decimales','no el valor guardado'):self.assertIn(part,text)
        other=self.steps('print(x,file=archivo)')[0]
        self.assertNotEqual(other.title,'Mostrar en pantalla')
        self.assertIn('file',other.brief)

    def test_condition_explains_comparison_without_predicting_a_branch(self):
        steps=self.steps('if temperatura>80:\n    estado="ALERTA"\nelse:\n    estado="NORMAL"')
        self.assertIn('temperatura es mayor que 80',steps[0].brief)
        self.assertIn('Si la respuesta es sí',steps[0].brief)
        self.assertIn('Si es no',steps[0].brief)
        self.assertTrue(steps[1].scope and steps[-1].scope)

    def test_no_evaluation_and_no_value_inspection(self):
        with patch('builtins.eval',side_effect=AssertionError('no execution')):
            steps=self.steps('resultado=funcion_con_efectos()')
        self.assertIn('depende',steps[0].brief)

    def test_unpacking_and_annotation_do_not_invent_assignment(self):
        self.assertIn('Repartimos',self.steps('a,b=datos')[0].brief)
        self.assertIn('no le asigna',self.steps('x:int')[0].brief)

    def test_explanations_are_larger_than_code_and_complete(self):
        source='import numpy as np\nx=np.array([1,2,3])\nm=np.mean(x)\nprint(m)'
        model=pynotas.analizar(source)
        doc=build(model,pynotas.seleccionar(model))
        self.assertEqual(len(doc.pages),1)
        ops=[op for p in doc.pages for op in p.ops if op[0]=='text']
        self.assertTrue(any(o[4]>=10 and 'sumamos' in o[3] for o in ops))
        self.assertTrue(any(o[4]>=8.4 and o[6]=='PyNotasMono' for o in ops))
        self.assertEqual('\n'.join(s.code for s in model.steps),source)
        for _,x,y,text,size,_,font in ops:
            self.assertLessEqual(x+fonts().stringWidth(text,font,size),588)
            self.assertTrue(0<y<792)

    def test_function_definition_is_a_recipe_not_a_call(self):
        step=self.steps('def calcular(x):\n    return x+1')[0]
        self.assertIn('no ejecuta ahora ese cuerpo',step.brief)

    def test_plot_explains_axes_and_show_with_explicit_import(self):
        steps=self.steps('import matplotlib.pyplot as dibujo\ndibujo.plot(t,x)\ndibujo.show()')
        self.assertIn('t para el eje horizontal',steps[1].brief)
        self.assertIn('x para el vertical',steps[1].brief)
        self.assertIn('Mostramos las figuras',steps[2].brief)
        self.assertIn('depende',self.steps('otra.plot(t,x)')[0].brief)

    def test_arange_respects_keyword_step_and_stop(self):
        step=self.steps('t=np.arange(0,1,1/fs)')[0]
        for text in ('desde 0','hacia 1','paso de 1 / fs','límite final queda fuera','en t'):self.assertIn(text,step.brief)
        self.assertIn('paso de 2',self.steps('x=np.arange(10,step=2)')[0].brief)
        self.assertIn('desde 2 hacia 10',self.steps('x=np.arange(2,stop=10)')[0].brief)

    def test_fft_explains_call_without_inventing_peaks_or_units(self):
        steps=self.steps('X=np.fft.rfft(x)\nf=np.fft.rfftfreq(n,0.01)')
        self.assertIn('muestras de x',steps[0].brief)
        self.assertIn('todavía no las dibuja',steps[0].brief)
        self.assertIn('0.01 como separación',steps[1].brief)
        self.assertNotIn('Hz',steps[1].brief)

    def test_literal_legend_and_axis_label_are_visible(self):
        steps=self.steps('import matplotlib.pyplot as plt\nplt.xlabel("Tiempo (s)")\nplt.legend()')
        self.assertIn('Tiempo (s)',steps[1].brief)
        self.assertIn('horizontal',steps[1].brief)
        self.assertIn('leyenda',steps[2].brief)


if __name__=='__main__':unittest.main()
