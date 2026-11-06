"""Letter print geometry and analytical context that survives pagination."""
from dataclasses import replace
import unittest
import pynotas
from pynotas.layout import build, fonts
from pynotas.analysis_context import for_model
from pynotas.letter_layout import code_rows
from test_reading_090 import MATLAB


def document(code):
    m=pynotas.analizar(code)
    return build(m,pynotas.seleccionar(m))


def visible(doc):
    return ' '.join(op[3] for page in doc.pages for op in page.ops if op[0]=='text')


class LetterTests(unittest.TestCase):
    def test_code_explanation_takes_priority_over_domain_theory(self):
        doc=document('rms=np.sqrt(np.mean(x**2))')
        text=visible(doc)
        self.assertEqual(len(doc.pages),1)
        self.assertNotIn('POR QUÉ FUNCIONA',text)
        self.assertNotIn('RMS = √',text)
        for phrase in ('al cuadrado','promedio','raíz cuadrada','Guardamos el resultado en rms'):
            self.assertIn(phrase,text)

    def test_matlab_explains_preparation_without_claiming_signal_analysis(self):
        m=pynotas.analizar(MATLAB)
        context=for_model(m,pynotas.seleccionar(m))
        self.assertIn('Si los datos son vibraciones',context.interpretation)
        self.assertIn('todavía no calcula RMS ni FFT',context.interpretation)
        self.assertIn('diccionario',context.principle)
        self.assertIn('frecuencia de muestreo',context.interpretation)

    def test_rms_plus_fft_keeps_both_theories(self):
        model=pynotas.analizar('rms=np.sqrt(np.mean(x**2))\nX=np.fft.rfft(x)')
        self.assertTrue({'rms','fft'} <= {t.key for t in model.theories})
        text=visible(build(model,pynotas.seleccionar(model)))
        self.assertIn('raíz cuadrada',text)
        self.assertIn('rfft',text)
        self.assertNotIn('RMS = √',text)

    def test_matlab_plus_other_theory_keeps_extra_concept(self):
        m=pynotas.analizar('x=scipy.io.loadmat(ruta)\ns=np.std(datos)')
        self.assertIsNotNone(m.case)
        self.assertTrue(m.theories)
        text=visible(build(m,pynotas.seleccionar(m)))
        self.assertIn('archivo MATLAB',text)
        self.assertIn('std',text)

    def test_long_code_preserves_font_size_numbering_and_last_line(self):
        doc=document('\n'.join(f'dato_{i}={i}' for i in range(40)))
        self.assertGreater(len(doc.pages),1)
        self.assertIn('L40',visible(doc))
        for i,page in enumerate(doc.pages,1):
            self.assertEqual((page.width,page.height),(612,792))
            self.assertIn(f'{i} / {len(doc.pages)}',[op[3] for op in page.ops if op[0]=='text'])
            for op in page.ops:
                if op[0]=='text':
                    _,x,y,text,size,color,font=op
                    self.assertLessEqual(x+fonts().stringWidth(text,font,size),612)
                    self.assertTrue(0<y<792)
                    if font=='PyNotasMono' and size>7 and text!='{ }':self.assertGreaterEqual(size,8.4)

    def test_single_long_instruction_continues_without_clipping(self):
        source='texto = "'+'dato_'*1800+'"'
        doc=document(source)
        self.assertGreater(len(doc.pages),1)
        self.assertIn('continuación',visible(doc))
        for page in doc.pages:
            for op in page.ops:
                if op[0]=='text' and op[6]=='PyNotasMono':self.assertLess(op[2],742)

    def test_code_wrapping_preserves_comments_and_multiline_string(self):
        source='# comentario\ntexto = """primera\n# texto, no comentario\núltima"""'
        m=pynotas.analizar(source)
        step=m.steps[0]
        rows=code_rows(step)
        self.assertEqual(''.join(r[1] for r in rows),''.join(source.splitlines()))
        self.assertIn('# comentario',visible(build(m,pynotas.seleccionar(m))))

    def test_compact_explanations_remain_concrete_and_simple(self):
        m=pynotas.analizar(MATLAB)
        self.assertIn('lista vacía',m.steps[0].brief)
        self.assertIn('contiene algún elemento',m.steps[1].brief)
        self.assertIn('Excluimos los nombres',m.steps[5].brief)
        # A shape lookup does not imply the unrelated code prints a name or type.
        s=pynotas.analizar('print(getattr(objeto,"shape",None))').steps[0]
        self.assertNotIn('con nombre, tipo',s.brief)

    def test_unknown_operation_does_not_invent_theory(self):
        m=pynotas.analizar('r=operacion_propia(x)',context='vibraciones')
        text=visible(build(m,pynotas.seleccionar(m)))
        self.assertNotIn('RMS =',text)
        self.assertNotIn('frecuencia de muestreo',text)


if __name__=='__main__':unittest.main()
