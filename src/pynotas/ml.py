"""Reviewed ML vocabulary and conservative, syntax-only identity tracking.

No framework import, object inspection, evaluation, or network calls.
The '@' prefix denotes an instance constructed by a recognized callable.
"""
import ast

SK = 'https://scikit-learn.org/stable/'
KE = 'https://keras.io/api/'
# title, idea, interpretation, conceptual steps, primary reference
CATALOG = {
 'split': ('Separar para aprender y comprobar',
  'Entrenamiento sirve para ajustar el modelo. Prueba reserva ejemplos para evaluar cómo responde ante datos que no usó al aprender.',
  'train_test_split reparte los datos. random_state hace repetible la división; stratify puede conservar proporciones de clases. En series temporales, revisa si corresponde separar por tiempo.',
  ('Datos y etiquetas', 'Separar conjuntos', 'Entrenar / evaluar'), SK+'modules/generated/sklearn.model_selection.train_test_split.html'),
 'scaling': ('Dar una escala comparable a los datos',
  'StandardScaler centra y escala cada variable según sus opciones. Con los valores predeterminados resta la media y divide por la desviación estándar.',
  'Ajusta el escalador con entrenamiento y reutilízalo en prueba. Una escala comparable no significa que los datos sean normales ni elimina valores extremos.',
  ('Datos de entrenamiento', 'Aprender media y escala', 'Transformar otros datos'), SK+'modules/generated/sklearn.preprocessing.StandardScaler.html'),
 'linear': ('Predecir una cantidad',
  'La regresión lineal combina las variables con pesos y un término independiente para estimar un valor numérico.',
  'LinearRegression ajusta los coeficientes minimizando la suma de errores al cuadrado. Evalúa con datos reservados: una relación predictiva no demuestra causalidad.',
  ('Variables de entrada', 'Suma con pesos', 'Cantidad estimada'), SK+'modules/generated/sklearn.linear_model.LinearRegression.html'),
 'logistic': ('Aprender a distinguir categorías',
  'La regresión logística es un modelo de clasificación: relaciona variables de entrada con probabilidades de clase.',
  'predict devuelve clases; predict_proba devuelve probabilidades según el orden de classes_. Una probabilidad estimada no es certeza.',
  ('Variables de entrada', 'Modelo de clasificación', 'Clases o probabilidades'), SK+'modules/generated/sklearn.linear_model.LogisticRegression.html'),
 'forest': ('Combinar varios árboles',
  'Un bosque aleatorio combina árboles de decisión. El conjunto puede capturar relaciones que un único árbol no representa bien.',
  'El clasificador combina probabilidades de los árboles; el regresor promedia predicciones. n_estimators controla cuántos árboles se construyen. Más árboles no garantizan mejor generalización.',
  ('Variables de entrada', 'Varios árboles', 'Combinar predicciones'), SK+'modules/ensemble.html#forest'),
 'pca': ('Resumir variables con componentes',
  'PCA encuentra direcciones de mayor variación y proyecta los datos sobre ellas. Puede reducir la cantidad de variables conservando parte de la información.',
  'PCA centra los datos, pero no los escala por defecto. Ajusta con entrenamiento y revisa la varianza explicada. Las componentes no son las variables originales.',
  ('Variables', 'Aprender direcciones', 'Proyectar en componentes'), SK+'modules/generated/sklearn.decomposition.PCA.html'),
 'kmeans': ('Agrupar por semejanza',
  'KMeans busca grupos alrededor de centros: asigna cada muestra a un centro cercano y reajusta los centros para reducir distancias al cuadrado.',
  'n_clusters fija la cantidad de grupos. Sus números son identificadores, no etiquetas de fallas conocidas. La escala y la inicialización influyen en el resultado.',
  ('Muestras', 'Centros y distancias', 'Grupos'), SK+'modules/generated/sklearn.cluster.KMeans.html'),
 'pipeline': ('Unir los pasos del aprendizaje',
  'Un Pipeline conecta transformaciones con un paso final. Permite repetir la misma preparación al entrenar y al predecir.',
  'Si la preparación está dentro del Pipeline y se ajusta solo con entrenamiento, ayuda a evitar que información de prueba entre en el ajuste.',
  ('Datos', 'Transformaciones', 'Modelo final'), SK+'modules/compose.html#pipeline'),
 'train': ('Aprender a partir de ejemplos',
  'fit ajusta los parámetros de un modelo utilizando los datos suministrados. Aprender es cambiar esos parámetros para responder mejor a los ejemplos.',
  'Entrenar no demuestra que el modelo funcione con datos nuevos. Reserva datos para evaluar y evita ajustar con el conjunto de prueba.',
  ('Ejemplos de entrenamiento', 'Ajustar parámetros', 'Modelo ajustado'), SK+'getting_started.html#fitting-and-predicting-estimator-basics'),
 'predict': ('Usar lo que el modelo aprendió',
  'predict aplica un modelo ajustado a las entradas para producir estimaciones. En esta operación no se vuelven a ajustar sus parámetros.',
  'Mantén las mismas variables, orden y preparación usados al entrenar. El tipo de salida depende del modelo: cantidades, clases u otros valores.',
  ('Nuevas entradas', 'Modelo ajustado', 'Predicciones'), SK+'getting_started.html#fitting-and-predicting-estimator-basics'),
 'probability': ('Consultar probabilidades de clase',
  'predict_proba estima una probabilidad para cada clase y cada muestra, cuando el modelo ofrece ese método.',
  'Consulta classes_ para interpretar las columnas. Una confianza alta puede estar mal calibrada y no garantiza una respuesta correcta.',
  ('Entradas', 'Modelo clasificador', 'Probabilidades'), SK+'modules/calibration.html'),
 'accuracy': ('Medir cuántas clases acertó',
  'La exactitud compara clases reales con clases predichas. Por defecto, accuracy_score entrega la proporción de coincidencias.',
  'Un conjunto con clases muy desiguales puede dar alta exactitud aunque se detecte mal la clase minoritaria. Examina también los errores por clase.',
  ('Clases reales + predichas', 'Comparar', 'Proporción de aciertos'), SK+'modules/generated/sklearn.metrics.accuracy_score.html'),
 'confusion': ('Ver en qué clases se equivoca',
  'La matriz de confusión cuenta o normaliza coincidencias y errores entre categorías. En scikit-learn las filas son clases reales y las columnas, predichas.',
  'Revisa el orden de labels y la opción normalize. La diagonal representa coincidencias; fuera de ella aparecen confusiones entre clases.',
  ('Clases reales + predichas', 'Cruzar categorías', 'Matriz de confusión'), SK+'modules/generated/sklearn.metrics.confusion_matrix.html'),
 'mse': ('Medir el error al cuadrado',
  'El error cuadrático medio compara valores reales y predichos, eleva cada diferencia al cuadrado y las promedia.',
  'MSE queda en unidades al cuadrado y penaliza más los errores grandes. Compáralo con una referencia sencilla sobre los mismos datos de prueba.',
  ('Valores reales + predichos', 'Diferencias al cuadrado', 'Promedio de errores'), SK+'modules/generated/sklearn.metrics.mean_squared_error.html'),
 'mae': ('Medir el tamaño habitual del error',
  'El error absoluto medio promedia la magnitud de las diferencias entre valores reales y predichos.',
  'MAE conserva las unidades del objetivo. Menor error es mejor en la misma tarea y conjunto de evaluación.',
  ('Valores reales + predichos', 'Diferencias absolutas', 'Promediar'), SK+'modules/generated/sklearn.metrics.mean_absolute_error.html'),
 'mlp': ('Una red que aprende conexiones',
  'Un perceptrón multicapa conecta entradas, capas ocultas y salidas. Cada neurona combina entradas con pesos y aplica una activación.',
  'hidden_layer_sizes indica las neuronas de las capas ocultas. MLPClassifier aprende clases; MLPRegressor estima cantidades. Escala las entradas y comprueba el desempeño fuera del entrenamiento.',
  ('Variables de entrada', 'Capas ocultas', 'Salida de la red'), SK+'modules/neural_networks_supervised.html'),
 'sequential': ('Construir una red por capas',
  'Sequential organiza capas en una secuencia: la salida de una alimenta la siguiente. Crear la arquitectura todavía no entrena sus pesos.',
  'La salida debe ser compatible con el objetivo y la función de pérdida. Este esquema conceptual no muestra los tamaños reales de tu red.',
  ('Entradas', 'Capas conectadas', 'Salidas'), KE+'models/sequential/'),
 'dense': ('Conectar entradas con neuronas',
  'Dense combina entradas con pesos, añade un sesgo si está habilitado y aplica la activación configurada. units indica cuántas salidas tiene la capa.',
  'ReLU conserva valores positivos y lleva los negativos a cero. Sin activación, Dense usa una transformación lineal. Más neuronas no garantizan mejor aprendizaje.',
  ('Entradas', 'Pesos + sesgo', 'Activación y salidas'), KE+'layers/core_layers/dense/'),
 'compile': ('Elegir cómo aprenderá la red',
  'compile configura el optimizador, la pérdida y las métricas. La pérdida expresa qué error se intentará reducir; el optimizador define cómo actualizar los pesos.',
  'Compilar no entrena. Selecciona una pérdida compatible con las etiquetas y la salida. fit es el paso que inicia el entrenamiento.',
  ('Arquitectura', 'Pérdida y optimizador', 'Configuración de entrenamiento'), KE+'models/model_training_apis/#compile-method'),
 'nn_train': ('Entrenar los pesos de una red',
  'fit recorre ejemplos y ajusta pesos para reducir la pérdida. Una época es un recorrido del conjunto de entrenamiento; batch_size define el tamaño de los grupos.',
  'La pérdida de entrenamiento puede bajar mientras empeora la validación: es una señal de sobreajuste. La validación ayuda a elegir; la prueba se reserva para la evaluación final.',
  ('Ejemplos por lotes', 'Error y gradientes', 'Actualizar pesos'), KE+'models/model_training_apis/#fit-method'),
 'evaluate': ('Comprobar la red con otros datos',
  'evaluate calcula la pérdida y las métricas configuradas para los datos suministrados, sin realizar un entrenamiento.',
  'Usa datos reservados y la misma preparación del entrenamiento. El valor obtenido depende de las métricas elegidas; no siempre es exactitud.',
  ('Datos reservados', 'Red entrenada', 'Pérdida y métricas'), KE+'models/model_training_apis/#evaluate-method'),
}
CONSTRUCTORS = {
 'sklearn.preprocessing.StandardScaler': 'scaling',
 'sklearn.linear_model.LinearRegression': 'linear',
 'sklearn.linear_model.LogisticRegression': 'logistic',
 'sklearn.ensemble.RandomForestClassifier': 'forest',
 'sklearn.ensemble.RandomForestRegressor': 'forest',
 'sklearn.decomposition.PCA': 'pca',
 'sklearn.cluster.KMeans': 'kmeans',
 'sklearn.pipeline.Pipeline': 'pipeline',
 'sklearn.pipeline.make_pipeline': 'pipeline',
 'sklearn.neural_network.MLPClassifier': 'mlp',
 'sklearn.neural_network.MLPRegressor': 'mlp',
 'keras.Sequential': 'sequential', 'keras.models.Sequential': 'sequential',
 'keras.layers.Dense': 'dense',
}
FUNCTIONS = {
 'sklearn.model_selection.train_test_split': 'split',
 **{'sklearn.metrics.'+name:key for name,key in (
  ('accuracy_score','accuracy'),('confusion_matrix','confusion'),
  ('mean_squared_error','mse'),('mean_absolute_error','mae'))},
}
# Identity tracking is separate from theory selection: a recognized constructor
# need not have a generic theory card. Concrete explanations live in learning.py.
SHAP_EXPLAINERS = {'shap.' + n for n in (
    'Explainer', 'TreeExplainer', 'DeepExplainer', 'GradientExplainer',
    'KernelExplainer', 'LinearExplainer')}
KERAS_MODELS = {'keras.Sequential', 'keras.models.Sequential', 'keras.Model', 'keras.models.Model'}
TORCH_LAYERS = {'torch.nn.' + n for n in (
    'Sequential', 'Linear', 'ReLU', 'Sigmoid', 'Softmax', 'Dropout', 'Flatten')}
TORCH_LOSSES = {'torch.nn.MSELoss', 'torch.nn.CrossEntropyLoss', 'torch.nn.BCEWithLogitsLoss'}
TORCH_OPTIMIZERS = {'torch.optim.Adam', 'torch.optim.SGD'}
TRACKED_CONSTRUCTORS = (set(CONSTRUCTORS) | SHAP_EXPLAINERS | KERAS_MODELS |
    TORCH_LAYERS | TORCH_LOSSES | TORCH_OPTIMIZERS |
    {'keras.layers.' + n for n in ('Input', 'Dropout', 'Flatten', 'LSTM', 'Conv1D')} |
    {'keras.callbacks.EarlyStopping', 'keras.optimizers.Adam'})
OPERATIONS = {
 'split':'Reparte las entradas y, si se entregan, sus etiquetas en conjuntos de entrenamiento y prueba.',
 'scaling':'Prepara un escalador. fit aprende la referencia; transform aplica la referencia aprendida.',
 'train':'Llama a fit con los datos indicados para ajustar el modelo reconocido.',
 'predict':'Aplica predict a los datos indicados y obtiene las predicciones del modelo.',
 'probability':'Llama a predict_proba para obtener probabilidades por clase.',
 'accuracy':'Compara etiquetas reales y predichas mediante accuracy_score.',
 'confusion':'Construye una matriz que cruza las clases reales y las predichas.',
 'mse':'Calcula mean_squared_error entre los valores reales y las predicciones.',
 'mae':'Calcula mean_absolute_error entre los valores reales y las predicciones.',
 'compile':'Configura la forma de entrenamiento con los argumentos de compile; todavía no entrena.',
 'nn_train':'Entrena la red mediante fit con los ejemplos y las opciones indicadas.',
 'evaluate':'Calcula la pérdida y las métricas de la red para los datos indicados.',
 'dense':'Crea una capa Dense con la cantidad de salidas y activación indicadas.',
 'sequential':'Construye una red Sequential con las capas que se indican.',
 'mlp':'Prepara un perceptrón multicapa. El entrenamiento ocurre al llamar a fit.',
 'linear':'Crea un modelo de regresión lineal; sus coeficientes se ajustan al llamar a fit.',
 'logistic':'Crea un clasificador de regresión logística; se ajusta al llamar a fit.',
 'forest':'Crea un bosque aleatorio con los parámetros indicados; se entrena con fit.',
 'pca':'Prepara una proyección PCA; sus componentes se aprenden con fit.',
 'kmeans':'Prepara KMeans con los parámetros indicados; fit aprende sus centros.',
 'pipeline':'Conecta las transformaciones y el paso final en una secuencia reutilizable.',
}

def canonical(name):
    return name.replace('tensorflow.keras.', 'keras.', 1) if name.startswith('tensorflow.keras.') else name

def qualified(node, names):
    if isinstance(node, ast.Name):return names.get(node.id, '')
    if isinstance(node, ast.Attribute):
        base=qualified(node.value,names)
        return base+'.'+node.attr if base else ''
    if isinstance(node, ast.Call):return instance(node,names)
    return ''

def instance(node, names):
    if isinstance(node,ast.Name):
        value=names.get(node.id,'')
        return value if value.startswith('@') else ''
    if isinstance(node,ast.Call):
        q=canonical(qualified(node.func,names))
        if q in TRACKED_CONSTRUCTORS:return '@'+q
        if q in {'@'+n for n in TORCH_LOSSES}:return '@torch.loss_value'
        if q in {'@shap.Explainer', '@shap.TreeExplainer', '@shap.LinearExplainer'}:
            return '@shap.Explanation'
        if q in {'@'+n+suffix for n in TORCH_LAYERS for suffix in ('.train', '.eval', '.to')}:
            return q.rsplit('.', 1)[0]
        if q.startswith('@') and q.endswith('.fit') and q[1:-4].startswith('sklearn.'):
            return q[:-4]
    return ''

def operation(call,names):
    q=canonical(qualified(call.func,names))
    if q in CONSTRUCTORS:return CONSTRUCTORS[q]
    if q in FUNCTIONS:return FUNCTIONS[q]
    if q.startswith('@'):
        ctor,_,method=q[1:].rpartition('.')
        key=CONSTRUCTORS.get(ctor)
        if not key or key=='dense':return None
        if key in {'scaling','pca','kmeans'}:
            allowed={'fit','transform','fit_transform'} | ({'fit_predict','predict'} if key=='kmeans' else set())
            if method in allowed:return key
            return None
        if method=='fit':return 'nn_train' if key=='sequential' else 'train'
        if method=='predict':return 'predict'
        if method=='predict_proba' and (key in {'logistic','pipeline'} or ctor.endswith('Classifier')):return 'probability'
        if key=='sequential' and method in {'compile','evaluate'}:return method
    return None

def immediate_calls(node):
    """Prune deferred code and local comprehension scopes to avoid false identity."""
    if isinstance(node,(ast.Lambda,ast.GeneratorExp,ast.ListComp,ast.SetComp,ast.DictComp)):
        return
    if isinstance(node,ast.Call):yield node
    for child in ast.iter_child_nodes(node):yield from immediate_calls(child)

def update_bindings(node,names):
    """Update a copy using only immediate imports/assignments; invalidate ambiguity."""
    result=dict(names)
    if isinstance(node,ast.Import):
        for a in node.names:result[a.asname or a.name.split('.')[0]]=a.name if a.asname else a.name.split('.')[0]
    elif isinstance(node,ast.ImportFrom) and node.module:
        if any(a.name=='*' for a in node.names):
            # Unknown imports may shadow any binding.
            result={k:'' for k in result}
        for a in node.names:
            if a.name!='*':result[a.asname or a.name]=(node.module+'.'+a.name if node.level==0 else '')
    elif isinstance(node,(ast.Assign,ast.AnnAssign)):
        targets=node.targets if isinstance(node,ast.Assign) else [node.target]
        value=instance(node.value,names) if node.value is not None else ''
        for target in targets:
            for n in ast.walk(target):
                if isinstance(n,ast.Name) and isinstance(n.ctx,(ast.Store,ast.Del)):
                    result[n.id]=value if isinstance(target,ast.Name) else ''
    else:
        for n in ast.walk(node):
            if isinstance(n,ast.Name) and isinstance(n.ctx,(ast.Store,ast.Del)):result[n.id]=''
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):result[node.name]=''
    for n in ast.walk(node):
        if isinstance(n,ast.NamedExpr) and isinstance(n.target,ast.Name):result[n.target.id]=''
    # Explicit assignments to qualified attributes invalidate that namespace/instance.
    for n in ast.walk(node):
        if isinstance(n,ast.Attribute) and isinstance(n.ctx,(ast.Store,ast.Del)):
            root=n.value
            while isinstance(root,ast.Attribute):root=root.value
            if isinstance(root,ast.Name):result[root.id]=''
    return result
