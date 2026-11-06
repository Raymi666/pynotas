"""Concrete, syntax-only teaching for recognized ML, neural-network and SHAP calls.

No imports of the student's libraries, data inspection, evaluation or network.
Rules are reviewed against the references in docs/EXPLICACIONES.md.
"""
import ast
from dataclasses import dataclass
from .ml import (canonical, qualified, SHAP_EXPLAINERS, KERAS_MODELS,
                 TORCH_LAYERS, TORCH_LOSSES, TORCH_OPTIMIZERS, CONSTRUCTORS)


@dataclass(frozen=True)
class Lesson:
    title: str
    summary: str
    details: tuple[str, ...] = ()
    tip: str = ''
    kind: str = 'code'


def text(node):
    return ast.unparse(node)


def explain(call, names):
    if not isinstance(call, ast.Call):
        return None
    q = canonical(qualified(call.func, names))
    opts = {kw.arg: kw.value for kw in call.keywords if kw.arg is not None}
    used = set()

    def arg(index, key, default='lo indicado en el código'):
        if key in opts:
            used.add(key)
            return text(opts[key])
        return text(call.args[index]) if len(call.args) > index else default

    def option(key, meaning, details):
        if key in opts:
            used.add(key)
            details.append(f'{key}={text(opts[key])}: {meaning}.')

    def result(title, summary, details=(), tip='', kind='code'):
        details = list(details)
        for kw in call.keywords:
            if kw.arg not in used:
                label = (kw.arg + '=') if kw.arg else '**'
                details.append(f'{label}{text(kw.value)}: opción adicional; su significado no está descrito por esta regla.')
        return Lesson(title, summary, tuple(details), tip, kind)

    if q == 'shap.datasets.california':
        count = arg(0, 'n_points', 'None')
        request = f' Pedimos una muestra de {count} registros.' if count != 'None' else ''
        return result('Preparar un ejemplo de viviendas',
            'Cargamos el conjunto de viviendas de California.' + request,
            ('El primer resultado contiene las características de cada zona; el segundo, el valor mediano de sus viviendas.',),
            'Aquí preparamos datos; todavía no entrenamos ni calculamos explicaciones SHAP.')
    if q in {'shap.utils.sample', 'shap.sample'}:
        data, count = arg(0, 'X'), arg(1, 'nsamples', '100')
        details = []
        option('random_state', 'semilla para repetir la selección con la misma versión', details)
        return result('Elegir una muestra de los datos',
            f'Tomamos al azar hasta {count} filas de {data}, sin reemplazo en SHAP 0.42 o posterior.', details,
            'Esta muestra puede servir de referencia para SHAP; elegirla todavía no explica el modelo.')
    if q == 'sklearn.linear_model.LinearRegression':
        details = []
        option('fit_intercept', 'controla si el modelo incluye un término independiente', details)
        return result('Preparar una regresión lineal',
            'Creamos un modelo que combina las variables con pesos para estimar un número. Los pesos se aprenderán con fit.', details)
    if q in {'sklearn.neural_network.MLPClassifier', 'sklearn.neural_network.MLPRegressor'}:
        details = []
        for key, meaning in [('hidden_layer_sizes', 'neuronas de cada capa oculta, en el orden escrito'), ('activation', 'transformación usada en las capas ocultas'), ('max_iter', 'límite de iteraciones del entrenamiento; puede detenerse antes'), ('random_state', 'semilla para repetir las operaciones aleatorias con la misma configuración')]:
            option(key, meaning, details)
        task = 'distinguir clases' if q.endswith('Classifier') else 'estimar cantidades'
        return result('Preparar una red de varias capas', f'Creamos una red para {task}. Cada capa transforma los datos y entrega su salida a la siguiente; fit aprenderá los pesos.', details)

    if q in KERAS_MODELS or q == 'torch.nn.Sequential':
        details = []
        if q.endswith('Sequential'):
            if q.startswith('keras.'):
                nodes = call.args[:1] or ([opts['layers']] if 'layers' in opts else [])
                if 'layers' in opts: used.add('layers')
                layers = nodes[0].elts if nodes and isinstance(nodes[0], (ast.List, ast.Tuple)) else nodes
            else:
                layers = call.args
            for i, layer in enumerate(layers, 1):
                child = explain(layer, names)
                detail = child.summary + (' ' + ' '.join(child.details) if child.details else '') if child else f'Usamos {text(layer)}; revisa su definición para conocer esa capa.'
                details.append(f'Paso {i}: {detail}')
            return result('Conectar las capas de la red',
                'Organizamos las capas en orden: cada una recibe la salida de la anterior. Construir la red todavía no la entrena.', details)
        inputs, outputs = arg(0, 'inputs'), arg(1, 'outputs')
        return result('Unir entradas y salidas de la red', f'Construimos el modelo que conecta {inputs} con {outputs}. Las capas intermedias ya definen ese recorrido.')
    if q == 'keras.layers.Dense':
        units = arg(0, 'units')
        activation = arg(1, 'activation', 'None')
        meanings = {"'relu'": 'ReLU deja pasar los valores positivos y convierte los negativos en cero.',
                    "'sigmoid'": 'Sigmoid lleva cada salida a un valor entre 0 y 1.',
                    "'softmax'": 'Softmax convierte las salidas en proporciones que suman 1 en el eje aplicado.',
                    'None': 'Sin activación adicional, la salida es una suma con pesos y, por defecto, un sesgo.',
                    "'linear'": 'La activación lineal deja la combinación tal como está.'}
        details = [meanings.get(activation, f'activation={activation}: función que transforma la combinación de entradas.')]
        for key, meaning in [('input_shape', 'forma esperada de una muestra, sin contar el lote'), ('use_bias', 'controla si se añade un término independiente')]:
            option(key, meaning, details)
        return result('Crear una capa de neuronas', f'Creamos una capa con {units} salidas. Cada una combina las entradas mediante pesos.', details)
    if q in {'keras.Input', 'keras.layers.Input'}:
        return result('Indicar la forma de entrada', f'Declaramos una entrada con forma {arg(0, "shape")}, sin incluir el tamaño del lote. No estamos creando ejemplos de entrenamiento.')
    if q in {'keras.layers.Dropout', 'torch.nn.Dropout'}:
        rate = arg(0, 'rate' if q.startswith('keras.') else 'p', '0.5')
        return result('Desactivar algunas entradas al entrenar',
            f'Dropout pone entradas a cero al azar con proporción {rate} durante el entrenamiento y reescala las restantes.',
            tip='Durante la inferencia normal, Dropout deja pasar las entradas. No elimina neuronas de forma permanente.')
    if q in {'keras.layers.Flatten', 'torch.nn.Flatten'}:
        details = []
        option('start_dim', 'primera dimensión que se combina', details)
        option('end_dim', 'última dimensión que se combina', details)
        return result('Reordenar los datos en una fila', 'Flatten junta dimensiones para preparar la entrada de otra capa. Cambia la forma, no aprende pesos.', details)
    if q == 'torch.nn.Linear':
        inputs, outputs = arg(0, 'in_features'), arg(1, 'out_features')
        details = []
        option('bias', 'controla si se añade un término independiente', details)
        return result('Conectar entradas con salidas', f'Creamos una capa que recibe {inputs} valores por posición y produce {outputs}. Combina las entradas con pesos; no añade una activación.', details)
    if q in {'torch.nn.ReLU', 'torch.nn.Sigmoid', 'torch.nn.Softmax'}:
        op = q.rsplit('.', 1)[-1]
        summary = {'ReLU': 'Preparamos ReLU: deja pasar los valores positivos y convierte los negativos en cero.',
                   'Sigmoid': 'Preparamos Sigmoid: transforma cada valor a un número entre 0 y 1.',
                   'Softmax': 'Preparamos Softmax: convierte valores en proporciones que suman 1 en el eje indicado.'}[op]
        details = []
        option('dim', 'eje en el que se normalizan las proporciones', details)
        return result('Preparar una activación', summary, details)
    if q in TORCH_LOSSES:
        summaries = {'MSELoss': 'Preparamos una medida del error: eleva al cuadrado la diferencia entre predicción y objetivo; por defecto promedia.',
                     'CrossEntropyLoss': 'Preparamos una pérdida de clasificación que compara las puntuaciones sin normalizar con los objetivos. No se aplica softmax antes para el caso habitual.',
                     'BCEWithLogitsLoss': 'Preparamos una pérdida binaria que combina sigmoid y comparación con los objetivos en un cálculo estable.'}
        details = []
        option('reduction', 'cómo se reúnen los errores: media, suma o sin reducción', details)
        return result('Elegir cómo medir el error', summaries[q.rsplit('.', 1)[-1]], details)
    if q in TORCH_OPTIMIZERS or q == 'keras.optimizers.Adam':
        details = []
        if q.startswith('torch.'):
            details.append(f'params={arg(0, "params")}: pesos que podrá actualizar el optimizador.')
        for key in ('lr', 'learning_rate'):
            option(key, 'controla la escala de los ajustes de los pesos', details)
        return result('Preparar el ajuste de los pesos', f'Creamos el optimizador {q.rsplit(".", 1)[-1]}. Crear esta herramienta todavía no cambia los pesos.', details)
    if q == 'keras.callbacks.EarlyStopping':
        details = []
        for key, meaning in [('monitor', 'medida cuyo progreso se observa'), ('patience', 'épocas sin mejora que se toleran antes de detenerse'), ('restore_best_weights', 'si es True, recupera los pesos del mejor valor observado'), ('mode', 'indica si mejorar significa subir o bajar la medida')]:
            option(key, meaning, details)
        return result('Preparar una parada del entrenamiento', 'Creamos una regla que puede detener fit cuando la medida observada deja de mejorar. Hay que pasarla a callbacks en fit.', details)

    if q in SHAP_EXPLAINERS:
        model = arg(0, 'model')
        key = 'masker' if q == 'shap.Explainer' else 'data'
        reference = arg(1, key, '')
        types = {'Explainer': 'un explicador SHAP', 'TreeExplainer': 'un explicador SHAP para árboles',
                 'DeepExplainer': 'un explicador Deep SHAP para redes compatibles',
                 'GradientExplainer': 'un explicador de gradientes esperados para redes compatibles',
                 'KernelExplainer': 'un explicador Kernel SHAP para una función de predicción',
                 'LinearExplainer': 'un explicador SHAP para modelos lineales'}
        summary = f'Preparamos {types[q.split(".")[-1]]} para {model}.'
        details = ([f'{key}={reference}: referencia usada para comparar u ocultar variables; todavía no son las filas que vamos a explicar.'] if reference else [])
        for key, meaning in [('algorithm', 'método para calcular las contribuciones'), ('model_output', 'salida del modelo que se quiere explicar'), ('feature_perturbation', 'cómo se trata la dependencia entre variables'), ('feature_names', 'nombres usados para identificar las variables'), ('seed', 'semilla para las operaciones aleatorias')]:
            option(key, meaning, details)
        return result('Preparar la explicación del modelo', summary, details,
                      'Las contribuciones describen la salida del modelo respecto de una referencia; no prueban causas.')
    is_explainer = q in {'@' + n for n in SHAP_EXPLAINERS}
    is_shap_values = q in {'@' + n + '.shap_values' for n in SHAP_EXPLAINERS}
    if is_explainer or is_shap_values:
        data = arg(0, 'X')
        details = []
        for key, meaning in [('nsamples', 'cantidad de evaluaciones o muestras usadas por el método'), ('max_evals', 'límite de evaluaciones para la explicación'), ('check_additivity', 'controla la comprobación de la suma de contribuciones')]:
            option(key, meaning, details)
        return result('Calcular el aporte de las variables',
            f'Pedimos contribuciones SHAP para las filas de {data}. Indican cuánto aporta cada variable a la salida respecto de la referencia.', details,
            'Un aporte positivo sube la salida explicada y uno negativo la baja; las unidades dependen de esa salida.')
    if q in {'shap.plots.beeswarm', 'shap.plots.bar', 'shap.plots.waterfall', 'shap.summary_plot', 'shap.dependence_plot', 'shap.force_plot'}:
        data = arg(0, 'shap_values')
        op = q.rsplit('.', 1)[-1]
        summaries = {
            'beeswarm': f'Dibujamos las contribuciones de {data}. Cada punto representa una muestra para una variable; su posición indica el aporte.',
            'bar': f'Dibujamos barras con las contribuciones de {data}. Para varias muestras resume la magnitud media; con una explicación muestra sus aportes individuales.',
            'waterfall': f'Dibujamos cómo los aportes de {data} llevan desde la referencia hasta la salida explicada. Se necesita una sola predicción y una salida seleccionada.',
            'summary_plot': f'Resumimos visualmente las contribuciones de {data}; el tipo de gráfico depende de plot_type y de los datos.',
            'dependence_plot': f'Dibujamos la variable {data} frente a su contribución SHAP para observar cómo varía su aporte.',
            'force_plot': f'Preparamos un gráfico de fuerzas desde la referencia {data}: muestra aportes que suben o bajan la salida.'}
        details = []
        for key, meaning in [('max_display', 'máximo de entradas visibles en el resumen'), ('show', 'controla si la función muestra el gráfico al terminar'), ('plot_type', 'tipo de representación'), ('interaction_index', 'variable usada para colorear posibles interacciones')]:
            option(key, meaning, details)
        return result('Dibujar la explicación SHAP', summaries[op], details, 'El gráfico explica al modelo; no demuestra que una variable sea la causa del resultado.', 'plot')

    if not q.startswith('@'):
        return None
    ctor, _, method = q[1:].rpartition('.')
    receiver = text(call.func.value) if isinstance(call.func, ast.Attribute) else text(call.func)
    if q in {'@' + n for n in TORCH_LOSSES}:
        return result('Comparar predicciones y objetivos', f'Calculamos el error entre {arg(0, "input")} y {arg(1, "target")}, usando la pérdida preparada. Todavía no actualizamos pesos.')
    if q == '@torch.loss_value.backward':
        return result('Calcular cómo cambia el error', 'backward calcula gradientes: cuánto influye cada parámetro en el error. Los acumula; el optimizador usará esa información para ajustar pesos.')
    if ctor in TORCH_OPTIMIZERS and method in {'zero_grad', 'step'}:
        return result('Limpiar los gradientes' if method == 'zero_grad' else 'Actualizar los pesos',
            'Limpiamos los gradientes anteriores antes de calcular los del siguiente paso; no borramos los pesos.' if method == 'zero_grad' else 'El optimizador ajusta los pesos con los gradientes disponibles y su configuración.')
    if ctor in TORCH_LAYERS and method in {'train', 'eval'}:
        return result('Cambiar el modo de la red',
            f'{receiver}.eval() activa el modo de evaluación. No calcula métricas ni desactiva por sí solo los gradientes.' if method == 'eval' else
            f'{receiver}.train configura el modo con {arg(0, "mode", "True")}. Cambia el comportamiento de capas como Dropout; esta llamada no entrena pesos.')
    if q in {'@' + n for n in TORCH_LAYERS | KERAS_MODELS}:
        return result('Pasar los datos por la red', f'Entregamos {arg(0, "inputs")} a {receiver} y calculamos su salida con los pesos actuales. Esta llamada no realiza por sí sola un paso de optimización.')
    if ctor in KERAS_MODELS and method == 'add':
        layer = call.args[0] if call.args else opts.get('layer')
        child = explain(layer, names) if layer is not None else None
        if 'layer' in opts:used.add('layer')
        return result('Añadir una capa a la red', f'Añadimos {text(layer) if layer is not None else "la capa indicada"} al final de {receiver}.',
                      (child.summary, *child.details) if child else ())
    if ctor in KERAS_MODELS and method == 'compile':
        details = []
        for key, meaning in [('optimizer', 'herramienta que actualiza los pesos'), ('loss', 'error que el entrenamiento intentará reducir'), ('metrics', 'medidas que se mostrarán para observar el desempeño')]:
            option(key, meaning, details)
        return result('Elegir cómo aprenderá la red', f'Configuramos {receiver} antes de entrenar. Elegimos cómo medir el error y cómo ajustar sus pesos.', details, 'compile prepara; fit entrena.')
    if (ctor in KERAS_MODELS or ctor in CONSTRUCTORS) and method in {'fit', 'predict', 'evaluate'}:
        x = arg(0, 'x' if ctor in KERAS_MODELS else 'X')
        if method == 'predict':
            return result('Obtener predicciones', f'Pasamos {x} a {receiver} para obtener sus estimaciones con los parámetros actuales. No volvemos a entrenarlo.')
        y = arg(1, 'y', 'los objetivos suministrados')
        if method == 'evaluate':
            return result('Medir el desempeño de la red', f'Comparamos la salida de {receiver} para {x} con {y}. Recibimos la pérdida y las métricas configuradas, sin ajustar pesos.')
        details = []
        for key, meaning in [('epochs', 'límite de épocas; cada época recorre el entrenamiento y una parada temprana puede reducirlo'), ('batch_size', 'cantidad de ejemplos por lote'), ('validation_split', 'fracción reservada para validación; no se usa para ajustar pesos'), ('validation_data', 'datos y objetivos usados para comprobar el progreso'), ('callbacks', 'acciones ejecutadas durante el entrenamiento, como una parada temprana'), ('verbose', 'cantidad o estilo de mensajes de progreso')]:
            option(key, meaning, details)
        if ctor in KERAS_MODELS:
            summary = f'Entrenamos {receiver}: recibe {x}, compara sus respuestas con {y} y ajusta los pesos para reducir el error.'
        elif CONSTRUCTORS.get(ctor) in {'scaling', 'pca', 'kmeans'}:
            return None
        else:
            summary = f'Ajustamos {receiver} con {x} como entradas y {y} como respuestas que debe aprender a estimar.'
        return result('Aprender con entradas y respuestas', summary, details, 'Entrenar no mide cómo responderá con datos nuevos; eso se comprueba por separado.')
    return None
