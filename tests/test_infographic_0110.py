import base64
import io
import json
import unittest
from dataclasses import replace
from unittest.mock import patch
from PIL import Image
import pynotas
from pynotas.capture import DisplayCapture, raster
from pynotas.layout import build, fonts
from pynotas.infographic import plan, draw_card, source_rows


def png(color='blue'):
    stream=io.BytesIO()
    Image.new('RGB',(60,30),color).save(stream,format='PNG')
    return base64.b64encode(stream.getvalue()).decode()


class Publisher:
    def __init__(self):self.calls=[]
    def publish(self,*args,**kw):self.calls.append((args,kw));return 'original'
    def clear_output(self,*args,**kw):self.calls.append(('clear',args,kw))


class InfographicTests(unittest.TestCase):
    def test_stages_preserve_source_steps_once_and_serializable(self):
        source='import matplotlib.pyplot as plt\nimport seaborn as sns\nx = df.groupby("motor")["ciclos"].max().reset_index()\nplt.title("Motores")\nplt.show()'
        model=pynotas.analizar(source)
        self.assertEqual([s.kind for s in model.stages],['tools','group','style'])
        self.assertEqual(tuple(s for stage in model.stages for s in stage.steps),model.steps)
        text=' '.join(model.stages[1].details)
        for part in ['groupby','max()','reset_index','ciclos']:self.assertIn(part,text)
        self.assertIn('Si trabajamos con pandas',model.stages[1].summary)
        json.dumps(model.to_dict())

    def test_explicit_parameter_meanings_and_descending(self):
        m=pynotas.analizar('x=df.sort_values(by="ciclos",ascending=False)')
        self.assertIn('de mayor a menor',' '.join(m.stages[0].details))
        m=pynotas.analizar('x=df.sort_values(by="ciclos",ascending=True)')
        self.assertNotIn('de mayor a menor',' '.join(m.stages[0].details))
        m=pynotas.analizar('import seaborn as s\ns.barplot(data=df,x="motor",y="ciclos",estimator="max")')
        for token in ['data:','x:','y:','estimator:']:self.assertIn(token,' '.join(m.stages[-1].details))

    def test_unknown_plot_and_rebound_alias_do_not_claim_matplotlib(self):
        for source in ['otra.plot(x,y)','import otra as plt\nplt.plot(x,y)','import matplotlib.pyplot as plt\nplt=otra\nplt.plot(x,y)']:
            stage=pynotas.analizar(source).stages[-1]
            self.assertEqual(stage.kind,'code')
            self.assertIn('depende',stage.summary)

    def test_no_merge_across_control_scope(self):
        m=pynotas.analizar('import matplotlib.pyplot as plt\nif ok:\n    plt.title("A")\nelse:\n    plt.title("B")')
        self.assertEqual(len(m.steps),sum(len(s.steps) for s in m.stages))
        self.assertTrue(m.stages[2].steps[0].scope)
        self.assertTrue(m.stages[-1].steps[0].scope)

    def test_same_line_statements_keep_their_own_meaning(self):
        m=pynotas.analizar('import numpy as np\nx=np.mean(datos); y=np.std(datos)')
        self.assertIn('sumamos y dividimos',m.stages[1].summary)
        self.assertNotEqual(m.stages[1].summary,m.stages[2].summary)

    def test_dynamic_plot_label_explains_numeric_format(self):
        m=pynotas.analizar('import matplotlib.pyplot as plt\nplt.title(f"Valor: {x:.2f}")')
        self.assertIn('x con 2 decimales',' '.join(m.stages[-1].details))

    def test_card_height_source_and_text_bounds(self):
        m=pynotas.analizar('import matplotlib.pyplot as plt\nimport numpy as np\nx=np.array([1,2,3])\np=np.mean(x)\nplt.plot(x,linewidth=2,marker="o")\nplt.show()')
        from pynotas.layout import Page
        for i,s in enumerate(m.stages,1):
            design=plan(s,276);page=Page('test',width=612,height=792)
            bottom=draw_card(page,24,112,276,s,i,design)
            self.assertLessEqual(bottom,112+design['height'])
            for op in page.ops:
                if op[0]=='text':self.assertLessEqual(op[1]+fonts().stringWidth(op[3],op[6],op[4]),300)
            self.assertEqual(''.join(r[1] for r in source_rows(s,256)),''.join(line for step in s.steps for line in step.code.splitlines() if line.strip()))

    def test_static_sheet_never_claims_real_result(self):
        m=pynotas.analizar('import matplotlib.pyplot as plt\nplt.plot(datos)')
        with patch('builtins.eval',side_effect=AssertionError('execution')):
            doc=build(m,pynotas.seleccionar(m))
        self.assertFalse(any(op[0]=='image' for p in doc.pages for op in p.ops))
        self.assertNotIn('RESULTADO REAL',' '.join(op[3] for p in doc.pages for op in p.ops if op[0]=='text'))

    def test_images_shared_by_svg_pdf_and_jpg(self):
        from pynotas.exports import pdf_bytes,jpg_pages
        m=replace(pynotas.analizar('x=1'),figures=(raster('image/png',png()),))
        doc=build(m,pynotas.seleccionar(m))
        self.assertIn('<image ',' '.join(p.svg('p'+str(i)) for i,p in enumerate(doc.pages)))
        pdf=pdf_bytes(doc)
        self.assertIn(b'/Subtype /Image',pdf)
        for blob in jpg_pages(pdf):
            with Image.open(io.BytesIO(blob)) as im:self.assertEqual(im.size,(2550,3300))


class CaptureTests(unittest.TestCase):
    def test_forward_unchanged_and_restore_instance_state(self):
        pub=Publisher();capture=DisplayCapture(pub);capture.install()
        data={'image/png':png(),'text/plain':'fig'}
        self.assertEqual(pub.publish(data,metadata={'a':1}),'original')
        self.assertIs(pub.calls[0][0][0],data)
        self.assertEqual(len(capture.figures),1)
        capture.restore();self.assertNotIn('publish',vars(pub));self.assertNotIn('clear_output',vars(pub))

    def test_bad_and_huge_payload_never_breaks_original_output(self):
        pub=Publisher();cap=DisplayCapture(pub);cap.install()
        for payload in ['not base64','x'*11_000_000]:pub.publish({'image/png':payload})
        self.assertEqual(len(pub.calls),2);self.assertFalse(cap.figures);self.assertTrue(cap.notes)
        pub.publish({'text/html':'<svg>interactive</svg>'});self.assertFalse(cap.figures)
        cap.restore()

    def test_update_clear_limits_and_no_replacement_of_later_hook(self):
        pub=Publisher();cap=DisplayCapture(pub);cap.install()
        pub.publish({'image/png':png()},transient={'display_id':'a'})
        pub.publish({'image/png':png('red')},transient={'display_id':'a'},update=True)
        self.assertEqual(len(cap.figures),1);self.assertEqual(cap.figures[0].data,png('red'))
        pub.clear_output();self.assertFalse(cap.figures)
        for _ in range(6):pub.publish({'image/png':png()})
        self.assertEqual(len(cap.figures),4);self.assertTrue(cap.notes)
        replacement=lambda *a,**k:None
        pub.publish=replacement;cap.restore();self.assertIs(pub.publish,replacement)

    def test_deferred_clear_waits_for_a_new_display(self):
        pub=Publisher();cap=DisplayCapture(pub);cap.install()
        pub.publish({'image/png':png()});pub.clear_output(wait=True)
        self.assertEqual(len(cap.figures),1)
        pub.publish({'text/plain':'next'})
        self.assertFalse(cap.figures);cap.restore()

    def test_real_ipython_runs_once_and_resets_between_cells(self):
        from IPython.core.interactiveshell import InteractiveShell
        from IPython.utils.capture import capture_output
        from pynotas.notebook import SLOT
        shell=InteractiveShell.instance();pynotas.activar(shell=shell,descargas=False)
        observer=getattr(shell,SLOT)
        shell.user_ns.update(_test_png=png(),_counter=0)
        source='from IPython.display import display\n_counter += 1\ndisplay({"image/png": _test_png}, raw=True)\nprint(_counter)'
        with capture_output() as out:r=shell.run_cell(source,store_history=True)
        self.assertIsNone(r.error_in_exec);self.assertEqual(out.stdout,'1\n')
        self.assertEqual(len(out.outputs),2);self.assertEqual(len(observer.last_model.figures),1)
        self.assertIsNone(observer.capture)
        with capture_output():shell.run_cell('x=3',store_history=True)
        self.assertFalse(observer.last_model.figures)
        with capture_output():shell.run_cell('raise ValueError("intentional")',store_history=True)
        self.assertIsNone(observer.capture)
        with capture_output():shell.run_cell('# pynotas: omitir\nprint("omitido")',store_history=True)
        self.assertIsNone(observer.capture)
        pynotas.activar(shell=shell,descargas=False,capturar_graficos=False)
        with capture_output():shell.run_cell(source,store_history=True)
        self.assertFalse(observer.last_model.figures)
        pynotas.desactivar(shell=shell)


if __name__=='__main__':unittest.main()
