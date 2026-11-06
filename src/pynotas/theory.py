"""Reviewed theory, selected from syntax. No evaluation or runtime-object access."""
import ast
from dataclasses import dataclass, replace

CONTEXTS = ('auto', 'general', 'vibraciones', 'machine_learning', 'redes_neuronales')

@dataclass(frozen=True)
class Theory:
    key: str
    title: str
    idea: str
    meaning: str
    steps: tuple[str, ...]
    source: str
    line: int

NUMPY = 'https://numpy.org/doc/stable/reference/'
CATALOG = {
 'rms': ('Valor eficaz (RMS)',
  'Para datos reales, RMS = raíz del promedio de los cuadrados. El cuadrado evita la cancelación entre signos.',
  'Conserva las unidades de entrada. Describe magnitud global; no identifica por sí solo una falla.',
  ('Datos reales', 'Elevar al cuadrado', 'Promediar', 'Obtener la raíz'),
  'https://www.ifm.com/ca/en/shared/technologies/real-time-maintenance/technology/time-domain'),
 'fft': ('Del tiempo a la frecuencia',
  'La FFT descompone una señal muestreada en componentes de frecuencia. Sus coeficientes son números complejos.',
  'El módulo de la FFT no es por sí solo una amplitud física: hay que revisar N, el escalado y la ventana. Un pico no identifica por sí solo una falla.',
  ('Señal muestreada', 'Calcular FFT', 'Coeficientes complejos'), NUMPY+'routines.fft.html'),
 'frequency_axis': ('El eje de frecuencias',
  'rfftfreq/fftfreq construyen las frecuencias de cada coeficiente. Si d está en segundos, el eje queda en Hz.',
  'El espaciado es fs/N y Nyquist es fs/2. Sin conocer fs y N no se deben inventar sus valores.',
  ('N y paso temporal d', 'Construir el eje', 'Frecuencias por muestra'), NUMPY+'generated/numpy.fft.rfftfreq.html'),
 'std': ('Dispersión alrededor del promedio',
  'La desviación estándar describe cuánto varían los valores respecto de su promedio; conserva sus unidades.',
  'El divisor depende de ddof: N con ddof=0 y N-1 con ddof=1. Para datos reales y ddof=0, desviación estándar y RMS coinciden si la media es cero.',
  ('Valores', 'Distancias al promedio', 'Medida de dispersión'), NUMPY+'generated/numpy.std.html'),
 'variance': ('Variación al cuadrado',
  'La varianza resume las desviaciones al cuadrado respecto del promedio.',
  'Sus unidades quedan al cuadrado. Revisa ddof para saber qué divisor utiliza el cálculo.',
  ('Valores', 'Desviaciones cuadradas', 'Varianza'), NUMPY+'generated/numpy.var.html'),
 'peak': ('Pico absoluto',
  'El máximo del valor absoluto identifica la mayor magnitud de las muestras, sin importar su signo.',
  'Es sensible a un único valor extremo. En vibraciones se interpreta junto con otras medidas y con las condiciones de medición.',
  ('Señal', 'Valor absoluto', 'Máximo'), NUMPY+'generated/numpy.absolute.html'),
 'crest': ('Factor de cresta',
  'El factor de cresta divide el pico absoluto por el RMS de la misma señal real.',
  'No tiene unidades. Puede resaltar impulsos, pero no confirma una falla. Si el RMS es cero, la razón no está definida.',
  ('Misma señal', 'Pico absoluto y RMS', 'Pico / RMS'),
  'https://www.bksv.com/downloads/svpockethandbook/index.html'),
 'ptp': ('Rango pico a pico',
  'La diferencia entre el máximo y el mínimo describe el recorrido total de los valores.',
  'Conserva las unidades de entrada; no es lo mismo que el pico absoluto ni que el RMS.',
  ('Valores', 'Máximo y mínimo', 'Restar extremos'), NUMPY+'generated/numpy.ptp.html'),
 'kurtosis': ('Curtosis: sensibilidad a valores extremos',
  'La curtosis se basa en el cuarto momento central, normalizado por la varianza al cuadrado.',
  'En scipy.stats.kurtosis, fisher=True usa exceso de curtosis (normal: 0); fisher=False usa Pearson (normal: 3). Revisa también bias y nan_policy.',
  ('Valores', 'Cuarto momento central', 'Normalizar'),
  'https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.kurtosis.html'),
 'sine': ('Una oscilación descrita con seno',
  'Para una señal A·sin(2·π·f·t), A es amplitud pico y f indica ciclos por segundo cuando t está en segundos.',
  'np.sin recibe ángulos en radianes. Una suma de senos puede representar varias componentes; no toda llamada a sin es una señal de vibración.',
  ('Ángulo en radianes', 'Aplicar seno', 'Valores entre -1 y 1'), NUMPY+'generated/numpy.sin.html'),
}
DEFAULT_ALIASES = {'np':'numpy', 'numpy':'numpy', 'scipy':'scipy', 'stats':'scipy.stats'}
OPERATIONS = {
 'rms': 'Python eleva cada muestra al cuadrado, calcula el promedio con mean y obtiene la raíz con sqrt.',
 'fft': 'fft o rfft reciben las muestras y devuelven los coeficientes de la transformada. rfft se usa con señales reales.',
 'frequency_axis': 'fftfreq o rfftfreq reciben el número de muestras y su separación temporal d para construir el eje.',
 'std': 'std calcula la dispersión de los valores. axis permite elegir la dirección del cálculo en una matriz.',
 'variance': 'var calcula la varianza de los valores, usando los parámetros indicados en la llamada.',
 'peak': 'abs convierte las muestras en magnitudes; max selecciona la mayor.',
 'crest': 'Python divide el pico absoluto por el RMS calculado sobre la misma entrada.',
 'ptp': 'ptp resta el mínimo al máximo de los valores.',
 'kurtosis': 'kurtosis calcula este indicador con la convención y las opciones de la llamada.',
 'sine': 'sin calcula el seno de cada ángulo. Las multiplicaciones y sumas del código ajustan la señal.',
}


def import_bindings(tree, initial=None):
    """Track syntax identities across successful cells; never inspect user objects."""
    from .ml import update_bindings
    names = dict(initial or {})
    for node in tree.body:
        names = update_bindings(node, names)
    return names


def enrich(blocks, statements, context='auto', bindings=None):
    if context not in CONTEXTS:raise ValueError('Contexto válido: '+', '.join(CONTEXTS))
    from . import ml
    catalog = {**CATALOG, **ml.CATALOG}
    operations = {**OPERATIONS, **ml.OPERATIONS}
    aliases = dict(DEFAULT_ALIASES); aliases.update(bindings or {})
    values, theories = {}, []
    def qualified(node):
        if isinstance(node,ast.Name):return aliases.get(node.id,'')
        if isinstance(node,ast.Attribute):
            base=qualified(node.value)
            return base+'.'+node.attr if base else ''
        return ''
    def resolve(n, depth=0):
        if isinstance(n,ast.Name) and n.id in values and depth<8:return resolve(values[n.id],depth+1)
        return n
    def call(n, endings):
        n=resolve(n)
        return isinstance(n,ast.Call) and qualified(n.func) in endings and bool(n.args)
    def rms_input(n):
        n=resolve(n)
        if not call(n,{'numpy.sqrt'}):return None
        avg=resolve(n.args[0])
        if not call(avg,{'numpy.mean'}):return None
        square=resolve(avg.args[0])
        if isinstance(square,ast.BinOp) and isinstance(square.op,ast.Pow) and isinstance(square.right,ast.Constant) and square.right.value==2:return square.left
        if call(square,{'numpy.square'}):return square.args[0]
        return None
    def peak_input(n):
        n=resolve(n)
        if not call(n,{'numpy.max','numpy.amax'}):return None
        inner=resolve(n.args[0])
        return inner.args[0] if call(inner,{'numpy.abs','numpy.absolute'}) else None
    def keys_for(n):
        if n is None:return []
        n=resolve(n)
        if rms_input(n) is not None:return ['rms']
        if isinstance(n,ast.BinOp) and isinstance(n.op,ast.Div):
            a,b=peak_input(n.left),rms_input(n.right)
            if a is not None and b is not None and ast.dump(resolve(a))==ast.dump(resolve(b)):return ['crest']
        if peak_input(n) is not None:return ['peak']
        keys=[]
        for invocation in ml.immediate_calls(n):
            key=ml.operation(invocation,aliases)
            if key:
                keys.append(key)
                q=ml.canonical(ml.qualified(invocation.func,aliases))
                if q.startswith('@'):
                    ctor=q[1:].rpartition('.')[0]
                    if key in {'train','nn_train','predict','probability'}:
                        model_key=ml.CONSTRUCTORS.get(ctor)
                        if model_key:keys.append(model_key)
        # Do not interpret deferred lambda/comprehension bodies as the immediate computation.
        def visit(v):
            if isinstance(v,(ast.Lambda,ast.GeneratorExp,ast.ListComp,ast.SetComp,ast.DictComp)):return
            if isinstance(v,ast.Call):
                q=qualified(v.func)
                if q in {'numpy.fft.rfft','numpy.fft.fft','scipy.fft.rfft','scipy.fft.fft'}:keys.append('fft')
                elif q in {'numpy.fft.rfftfreq','numpy.fft.fftfreq','scipy.fft.rfftfreq','scipy.fft.fftfreq'}:keys.append('frequency_axis')
                elif q=='numpy.std':keys.append('std')
                elif q=='numpy.var':keys.append('variance')
                elif q=='numpy.ptp':keys.append('ptp')
                elif q=='scipy.stats.kurtosis':keys.append('kurtosis')
                elif q=='numpy.sin':keys.append('sine')
            for child in ast.iter_child_nodes(v):visit(child)
        visit(n)
        return list(dict.fromkeys(keys))
    result=[]
    for b,node in zip(blocks,statements):
        expression=node.value if isinstance(node,(ast.Assign,ast.AnnAssign,ast.AugAssign,ast.Expr,ast.Return)) else None
        keys=keys_for(expression)
        for key in keys:
            item=catalog[key]
            meaning=item[2]
            if context=='vibraciones' and key=='rms':meaning='En vibraciones, resume la magnitud de la señal medida. '+meaning
            theories.append(Theory(key,item[0],item[1],meaning,item[3],item[4],node.lineno))
        if keys:
            first=catalog[keys[0]]
            summary=operations[keys[0]]
            # A transformer method must not be described as constructor creation.
            for invocation in ml.immediate_calls(expression):
                q=ml.canonical(ml.qualified(invocation.func,aliases))
                if ml.operation(invocation,aliases)==keys[0] and q.startswith('@'):
                    method=q.rpartition('.')[2]
                    if keys[0] in {'scaling','pca','kmeans'}:
                        action={'fit':'Aprende los parámetros con los datos indicados.',
                                'transform':'Aplica la transformación aprendida a los datos indicados.',
                                'fit_transform':'Aprende los parámetros y transforma esos mismos datos.',
                                'fit_predict':'Aprende los grupos y devuelve sus asignaciones.',
                                'predict':'Asigna los datos a los centros aprendidos.'}.get(method)
                        if action:summary=method+': '+action
                    break
            if b.writes: summary+=' Guarda el resultado en '+', '.join(b.writes)+'.'
            if not (keys[0]=='scaling' and b.topics in {('scale',),('scale_fit',)}):
                b=replace(b,title=first[0],summaries=(summary,),topics=tuple(dict.fromkeys(b.topics+tuple(keys))))
        result.append(b)
        if isinstance(node,(ast.Import,ast.ImportFrom)):
            aliases.update(import_bindings(ast.Module(body=[node],type_ignores=[])))
        elif isinstance(node,(ast.Assign,ast.AnnAssign)):
            targets=node.targets if isinstance(node,ast.Assign) else [node.target]
            # Drop substituted expressions when their input is reassigned (avoids stale chains).
            stored={n.id for target in targets for n in ast.walk(target) if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Store)}
            for name in list(values):
                if name in stored or any(isinstance(n,ast.Name) and n.id in stored for n in ast.walk(values[name])):values.pop(name,None)
            for target in targets:
                if isinstance(target,ast.Name):
                    if node.value is not None and not any(isinstance(n,ast.Name) and n.id==target.id for n in ast.walk(node.value)):values[target.id]=node.value
        else:
            aliases.update(import_bindings(ast.Module(body=[node],type_ignores=[])))
            values.clear()
        aliases = ml.update_bindings(node, aliases)
    unique={}
    for t in theories:unique.setdefault(t.key,t)
    return tuple(result),tuple(unique.values())
