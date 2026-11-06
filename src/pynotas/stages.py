"""Turn a faithful source reading into teaching tasks. No runtime data access."""
import ast
from dataclasses import replace
from .model import TeachingStage
from .walkthrough import qualified, DEFAULTS
from .ml import update_bindings


def code(node):
    return ast.unparse(node)


PARAMETERS = {
    'figsize': 'ancho y alto de la figura, en pulgadas',
    'fontsize': 'tamaño de las letras, en puntos',
    'rotation': 'giro de las etiquetas, en grados',
    'color': 'color del dibujo', 'label': 'nombre de la serie para la leyenda',
    'linewidth': 'grosor de la línea', 'alpha': 'transparencia: 0 invisible, 1 opaco',
    'marker': 'símbolo que marca cada dato', 'linestyle': 'estilo del trazo',
    'bins': 'cantidad o límites de los intervalos del histograma',
    'density': 'elige si se normaliza el área del histograma',
    'x': 'dato o columna para el eje horizontal',
    'y': 'dato o columna para el eje vertical',
    'data': 'tabla que contiene las columnas',
    'order': 'orden de las categorías', 'palette': 'paleta de colores',
    'hue': 'variable que separa los grupos por color',
    'legend': 'controla la leyenda', 'errorbar': 'tipo de intervalo de incertidumbre',
    'estimator': 'cálculo que resume cada grupo', 'ax': 'eje donde se dibuja',
    'by': 'columna o columnas usadas para ordenar',
    'axis': 'eje sobre el que se opera', 'ddof': 'resta este número a N en el divisor',
    'inplace': 'True cambia el objeto original y devuelve None',
    'drop': 'True descarta el índice anterior; False lo conserva como columnas',
}


def parameters(call):
    result=[]
    for kw in call.keywords:
        value=code(kw.value)
        if kw.arg=='ascending' and isinstance(kw.value,ast.Constant) and isinstance(kw.value.value,bool):
            meaning='de menor a mayor' if kw.value.value else 'de mayor a menor'
        else:meaning=PARAMETERS.get(kw.arg,'opción que se entrega a la función; consulta su definición')
        # Values remain visible in the adjacent code; avoid printing them twice.
        label=f'{kw.arg}={value}' if kw.arg in {'ascending','ddof'} else (kw.arg or '**')
        result.append(f'{label}: {meaning}.')
    return result


def chain_parts(value):
    """Only follow the receiver chain, not calls inside unrelated arguments."""
    if isinstance(value,ast.Call) and isinstance(value.func,ast.Attribute):
        return chain_parts(value.func.value)+[value]
    if isinstance(value,ast.Subscript):return chain_parts(value.value)+[value]
    return []


def describe(step,node,names):
    base=TeachingStage(step.title,'code',(step,),summary=step.brief or ' '.join(step.explanations),tip=step.aside)
    if step.scope or not node:return base
    if isinstance(node,(ast.Import,ast.ImportFrom)):
        parts=[]
        entries=[(a.name,a.asname or a.name) for a in node.names] if isinstance(node,ast.Import) else [(f'{node.module}.{a.name}',a.asname or a.name) for a in node.names]
        purposes={'matplotlib.pyplot':'dibujar y personalizar gráficos','seaborn':'Facilita crear gráficos estadísticos',
                  'numpy':'calcular con números y grupos de datos','pandas':'trabajar con tablas de filas y columnas',
                  'scipy.io':'leer y guardar archivos, como los de MATLAB','os':'trabajar con carpetas y rutas'}
        purposes.update({'sklearn':'preparar datos y ajustar modelos predictivos',
                         'pynotas':'crear apuntes visuales del código sin volver a ejecutarlo',
                         'shap':'estimar el aporte de cada variable a la salida de un modelo',
                         'torch':'calcular con tensores y construir redes neuronales',
                         'torch.nn':'preparar capas y pérdidas para redes neuronales',
                         'keras':'construir y entrenar redes neuronales por capas',
                         'tensorflow':'calcular con tensores y construir modelos de aprendizaje'})
        for original,alias in entries:
            if original not in purposes:return replace(base,kind='tools')
            parts.append(f'{alias}'+(f' (apodo de {original})' if alias!=original else '')+f': {purposes[original]}.')
        return TeachingStage('Preparar las herramientas','tools',(step,),tuple(parts),'Importar deja las herramientas listas para usarlas.')
    value=getattr(node,'value',None)
    if not isinstance(value,ast.Call):return base
    q=qualified(value.func,names)
    target=''
    if isinstance(node,(ast.Assign,ast.AnnAssign)):
        targets=node.targets if isinstance(node,ast.Assign) else [node.target]
        target='Guardamos en '+', '.join(code(t) for t in targets)+'.'
    from .learning import explain as learning_explanation
    lesson = learning_explanation(value, names)
    if lesson:
        from .teacher import destination
        assigned = isinstance(node, (ast.Assign, ast.AnnAssign))
        return TeachingStage(lesson.title, lesson.kind, (step,), lesson.details,
                             lesson.summary + (' ' + destination(node) if assigned else ''), lesson.tip)
    if q.startswith('matplotlib.pyplot.') or q.startswith('seaborn.'):
        op=q.rsplit('.',1)[-1]
        args=[code(a) for a in value.args]
        parts=parameters(value)
        if op in {'figure','subplots'}:
            return TeachingStage('Preparar el lienzo','canvas',(step,),tuple(parts),base.summary.split(' Opciones:')[0])
        labels={'title':'título del gráfico','xlabel':'nombre del eje horizontal','ylabel':'nombre del eje vertical',
                'xticks':'posiciones o etiquetas del eje horizontal','yticks':'posiciones o etiquetas del eje vertical',
                'tight_layout':'ajusta los espacios entre los elementos','show':'muestra las figuras preparadas',
                'legend':'identifica las series con una leyenda','grid':'configura la cuadrícula'}
        if op in labels:
            text=f'{op}(): {labels[op]}.'
            formats=[]
            for arg in value.args:
                if isinstance(arg,ast.JoinedStr):
                    for item in arg.values:
                        if isinstance(item,ast.FormattedValue):
                            spec=''.join(v.value for v in item.format_spec.values if isinstance(v,ast.Constant) and isinstance(v.value,str)) if item.format_spec else ''
                            import re
                            match=re.fullmatch(r'\.(\d+)f',spec)
                            formats.append('El texto inserta '+code(item.value)+(f' con {match[1]} decimales' if match else ' usando el formato escrito')+'.')
            return TeachingStage('Dar claridad al gráfico','style',(step,),tuple([text]+formats+parts),'Añadimos las pistas que ayudan a leer el gráfico.')
        if op=='barplot' and q.startswith('seaborn.'):
            details=['barplot resume el valor de cada categoría; por defecto calcula su promedio.']+parts
            return TeachingStage('Dibujar las barras','plot',(step,),tuple(details),'Cada barra permite comparar una categoría con las demás. '+target,
                                 'Con una fila por categoría, la barra representa ese valor.')
        if op in {'plot','bar','barh','hist','scatter','axhline','axvline','fill_between'}:
            meanings={'bar':'Dibujamos barras con las posiciones y alturas indicadas.',
                      'barh':'Dibujamos barras horizontales con las posiciones y longitudes indicadas.',
                      'hist':'Reunimos los datos en intervalos; sus alturas dependen de los conteos, pesos y normalización indicados.',
                      'scatter':'Dibujamos un punto por cada pareja de datos.',
                      'axhline':'Trazamos una línea horizontal de referencia.',
                      'axvline':'Trazamos una línea vertical de referencia.',
                      'fill_between':'Coloreamos la zona entre las curvas indicadas.'}
            summary=meanings.get(op,base.summary.split(' Opciones:')[0])
            return TeachingStage('Dibujar los datos','plot',(step,),tuple(parts),summary)
    if q=='numpy.std':
        first=code(value.args[0]) if value.args else next((code(k.value) for k in value.keywords if k.arg=='a'),'los datos indicados')
        return TeachingStage('Medir cuánto varían los datos','measure',(step,),tuple(parameters(value)),
            f'std calcula la desviación estándar de {first}: una medida de su dispersión respecto del promedio. '+target,
            'Con ddof=0 divide por N; con ddof=1 divide por N−1. No son el mismo cálculo.')
    chain=chain_parts(value)
    methods=[n.func.attr for n in chain if isinstance(n,ast.Call)]
    # A bare variable may have any type. Explain pandas semantics conditionally.
    if methods and set(methods)<= {'groupby','max','min','mean','sum','reset_index','sort_values'} and ('groupby' in methods or methods==['sort_values']):
        parts=[]
        for n in chain:
            if isinstance(n,ast.Subscript):parts.append('['+code(n.slice)+']: elige la columna o columnas que vamos a calcular.');continue
            op=n.func.attr
            if op=='groupby':
                by=code(n.args[0]) if n.args else next((code(k.value) for k in n.keywords if k.arg=='by'),'la clave indicada')
                parts.append(f'groupby({by}): reúne las filas que comparten esa clave.')
            elif op in {'max','min','mean','sum'}:
                parts.append(op+'(): '+{'max':'elige el mayor valor','min':'elige el menor valor','mean':'calcula el promedio','sum':'suma los valores'}[op]+' de cada grupo.')
            elif op=='reset_index':
                drop=any(k.arg=='drop' and isinstance(k.value,ast.Constant) and k.value.value is True for k in n.keywords)
                parts.append('reset_index(): '+('descarta el índice anterior y crea uno nuevo.' if drop else 'convierte el índice en columnas y crea un índice nuevo.'))
            elif op=='sort_values':
                parts.append('sort_values(): cambia el orden según los valores indicados.')
                if n.args:parts.append('by='+code(n.args[0])+': columna o columnas usadas para ordenar.')
            parts.extend(parameters(n))
        return TeachingStage('Resumir cada grupo' if 'groupby' in methods else 'Ordenar los resultados',
                             'group' if 'groupby' in methods else 'sort',(step,),tuple(parts),
                             'Si trabajamos con pandas, seguimos estos pasos. '+target,
                             'max elige el mayor registro; no suma los registros.' if 'max' in methods else '')
    return base


def enrich_stages(model,tree,initial=None):
    names=dict(DEFAULTS);names.update(initial or {})
    by_line={}
    for node in tree.body:
        by_line[node.lineno]=(None,{}) if node.lineno in by_line else (node,dict(names))
        names=update_bindings(node,names)
    stages=[]
    for step in model.steps:
        match=next((v for line,v in by_line.items() if step.line<=line<=step.end_line),None)
        stage=describe(step,*(match if match else (None,{})))
        # Only adjacent import and presentation calls share a card. Never cross a scope.
        if stages and stage.kind in {'tools','style'} and stages[-1].kind==stage.kind and not step.scope:
            prev=stages[-1]
            # Generic imports retain their own explanation instead of losing it.
            if not prev.details or not stage.details:
                stages.append(stage);continue
            stages[-1]=replace(prev,steps=prev.steps+stage.steps,details=prev.details+stage.details)
        else:stages.append(stage)
    return replace(model,stages=tuple(stages))
