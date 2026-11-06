"""A teacher's reading of syntax. Never imports, evaluates or inspects user data.

Return a plain explanation and an optional analogy separately, so the renderer
can give the explanation priority and limit jokes without dropping information.
"""
import ast
from .teaching import short


def name(node):
    text = short(node)
    return text if len(text) <= 100 else 'la expresión escrita en el código'


def question(node):
    if isinstance(node, ast.Compare) and len(node.ops) == 1:
        words = {ast.Gt: 'es mayor que', ast.GtE: 'es mayor o igual que',
                 ast.Lt: 'es menor que', ast.LtE: 'es menor o igual que',
                 ast.Eq: 'es igual a', ast.NotEq: 'es distinto de',
                 ast.In: 'está en', ast.NotIn: 'no está en',
                 ast.Is: 'es el mismo objeto que', ast.IsNot: 'es otro objeto distinto de'}
        if type(node.ops[0]) in words:
            return f'{name(node.left)} {words[type(node.ops[0])]} {name(node.comparators[0])}'
    return f'{name(node)} cuenta como verdadero'


def destination(node):
    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    if len(targets) == 1 and isinstance(targets[0], (ast.Tuple, ast.List)):
        return f'Repartimos lo recibido entre {name(targets[0])}, en ese orden.'
    return 'Guardamos el resultado en ' + ', '.join(name(t) for t in targets) + '.'


def explain(node, title, fallback, bindings, resolve, block=None):
    """Prefer specific, qualified operations over guesses based on method names."""
    if isinstance(node, (ast.Import, ast.ImportFrom)) and block:
        parts = []
        friendly = {
            'numpy': 'Traemos NumPy, una caja de herramientas para calcular con números y grupos de datos.',
            'matplotlib.pyplot': 'Traemos pyplot, la herramienta de Matplotlib para dibujar y personalizar gráficos.',
            'pandas': 'Traemos pandas para trabajar con tablas de filas y columnas.',
            'os': 'Traemos os para trabajar con carpetas y rutas de archivos.',
            'scipy.io': 'Traemos scipy.io para leer y guardar archivos de datos, como los .mat de MATLAB.',
        }
        for r in block.resources:
            if r.binding == '*':
                parts.append('Traemos los nombres públicos del módulo. El * no muestra cuáles son en esta línea.')
                continue
            parts.append(friendly.get(r.qualified_name, f'Traemos {r.qualified_name}. {r.purpose}'))
            parts.append(f'Le ponemos el apodo {r.alias} para usarlo en el código.' if r.alias
                         else f'Lo usamos como {r.access_name or r.binding}.')
        joke = '¡Ya tenemos ayudante para las cuentas!' if any(r.qualified_name == 'numpy' for r in block.resources) else ''
        return 'Preparar las herramientas', ' '.join(parts), joke
    if block and block.kind == 'setup':
        return title, fallback, ''
    if isinstance(node, ast.If):
        if fallback.startswith('Comprueba si la lista '):
            detail = fallback.split('. ')[0] + '. Si tiene elementos, seguimos las líneas desplazadas a la derecha.'
        else:
            detail = f'Preguntamos si {question(node.test)}. Si la respuesta es sí, seguimos las líneas desplazadas a la derecha.'
        detail += ' Si es no, vamos a la alternativa.' if node.orelse else ' Si es no, saltamos esas líneas.'
        return 'Elegir un camino', detail, 'Un cruce de caminos: la condición pone el semáforo.'
    if isinstance(node, (ast.For, ast.AsyncFor)):
        if (isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Attribute)
                and node.iter.func.attr == 'items' and isinstance(node.target, ast.Tuple)
                and len(node.target.elts) == 2):
            a, b = (name(n) for n in node.target.elts)
            return 'Revisar cada pareja', (f'Recorremos las parejas de {name(node.iter.func.value)} con items(). '
                    f'En cada vuelta, el nombre pasa a {a} y el valor a {b}. Repetimos las líneas desplazadas a la derecha.'), ''
        return 'Repetir, uno por uno', (f'Tomamos cada elemento de {name(node.iter)} y lo llamamos {name(node.target)}. '
                'Con cada uno repetimos las líneas desplazadas a la derecha. Si no hay elementos, no entramos.'), 'Python hace las vueltas; tú te ahorras copiar y pegar.'
    if isinstance(node, ast.While):
        return 'Repetir mientras se cumpla', (f'Comprobamos si {question(node.test)} antes de cada vuelta. '
                'Mientras se cumpla, repetimos las líneas desplazadas a la derecha. Cuando no, salimos.'), ''
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        prefix = 'Preparamos una función asíncrona' if isinstance(node, ast.AsyncFunctionDef) else 'Preparamos una función'
        return f'Preparar {node.name}', (f'{prefix} llamada {node.name}. Las líneas desplazadas a la derecha son su receta; '
                'def la define, no ejecuta ahora ese cuerpo.'), 'Escribimos la receta antes de ponernos a cocinar.'
    if isinstance(node, ast.Return):
        detail = ('Devolvemos ' + name(node.value) if node.value else 'Devolvemos None (ningún valor explícito)')
        return 'Entregar la respuesta', detail + ' y terminamos esta llamada a la función.', ''
    if isinstance(node, ast.AugAssign):
        verbs = {ast.Add: 'aplicamos +', ast.Sub: 'restamos', ast.Mult: 'multiplicamos por', ast.Div: 'dividimos entre'}
        if type(node.op) in verbs:
            return 'Actualizar un valor', f'Tomamos {name(node.target)}, {verbs[type(node.op)]} {name(node.value)} y guardamos el resultado de nuevo en {name(node.target)}.', ''
    if isinstance(node, ast.AnnAssign) and node.value is None:
        return 'Indicar el tipo esperado', f'Anotamos {name(node.annotation)} como tipo esperado para {name(node.target)}. Esta línea no le asigna un valor.', ''
    value = getattr(node, 'value', None)
    if not isinstance(node, (ast.Assign, ast.AnnAssign, ast.Expr)) or value is None:
        return title, fallback, ''
    detail, aside = '', ''
    assigned = isinstance(node, (ast.Assign, ast.AnnAssign))
    if isinstance(value, ast.Constant):
        title = 'Ponerle nombre a un dato'
        detail = f'Tomamos {name(value)}.'
    elif isinstance(value, ast.List):
        title = 'Reunir los datos'
        detail = ('Creamos una lista vacía [], lista para guardar elementos.' if not value.elts
                  else 'Reunimos los elementos entre [ ] en una lista. Conservan el orden escrito.')
    elif isinstance(value, ast.DictComp) and len(value.generators) == 1 and 'type' not in bindings:
        g = value.generators[0]
        if (isinstance(value.value, ast.Call) and isinstance(value.value.func, ast.Name)
                and value.value.func.id == 'type' and len(value.value.args) == 1):
            detail = (f'Recorremos {name(g.iter)}. Para cada {name(value.key)}, consultamos con type qué clase de dato es '
                      f'{name(value.value.args[0])}. Armamos un diccionario de nombres y tipos.')
            # Preserve every filter, rather than assuming that all dictionaries
            # omit MATLAB metadata.
            for cond in g.ifs:
                if isinstance(cond, ast.UnaryOp) and isinstance(cond.op, ast.Not) and isinstance(cond.operand, ast.Call) and isinstance(cond.operand.func, ast.Attribute) and cond.operand.func.attr == 'startswith' and cond.operand.args:
                    detail += f' Excluimos los nombres que comienzan por {name(cond.operand.args[0])}.'
                else:detail += f' Solo guardamos las parejas que cumplen {name(cond)}.'
    elif isinstance(value, ast.Name):
        title = 'Usar un dato que ya tenemos'
        detail = f'Usamos lo que tiene el nombre {value.id}. El nuevo nombre apunta al mismo objeto; no hacemos una copia.'
    elif isinstance(value, ast.BinOp):
        a, b = name(value.left), name(value.right)
        if isinstance(value.op, ast.Pow) and isinstance(value.right, ast.Constant) and value.right.value == 2:
            title, detail = 'Elevar al cuadrado', f'Elevamos {a} al cuadrado: **2 significa multiplicar por sí mismo. Con un arreglo de NumPy se hace en cada elemento.'
        elif isinstance(value.op, ast.Div):
            title, detail = 'Dividir', f'Dividimos {a} entre {b}. El divisor debe ser distinto de cero.'
        elif isinstance(value.op, ast.Add):
            title, detail = 'Combinar con +', f'Aplicamos + a {a} y {b}. Con números suma; con textos o listas los une. Depende de los datos.'
        elif isinstance(value.op, ast.Sub):
            title, detail = 'Restar', f'A {a} le restamos {b}.'
        elif isinstance(value.op, ast.Mult):
            title, detail = 'Multiplicar con *', f'Aplicamos * a {a} y {b}. Con números multiplica; un texto o una lista por un entero se repite.'
    elif isinstance(value, ast.Compare):
        title, detail = 'Comparar', f'Comprobamos si {question(value)}. La comparación indica verdadero o falso; con arreglos puede producir varias respuestas.'
    elif isinstance(value, ast.Subscript):
        title = 'Elegir una parte'
        if isinstance(value.slice, ast.Constant) and value.slice.value == 0:
            detail = f'Tomamos el elemento de {name(value.value)} que corresponde a [0]. En listas y arreglos es el primero: Python empieza a contar en cero.'
        else:
            detail = f'Buscamos en {name(value.value)} la parte indicada entre [{name(value.slice)}].'
    elif isinstance(value, ast.Call):
        from .learning import explain as learning_explanation
        lesson = learning_explanation(value, bindings)
        if lesson:
            detail = ' '.join((lesson.summary,) + lesson.details)
            if assigned:
                detail += ' ' + destination(node)
            return lesson.title, detail, lesson.tip
        q = resolve(value.func, bindings)
        builtin = isinstance(value.func, ast.Name) and value.func.id not in bindings
        arg = name(value.args[0]) if value.args else ''
        nested = bool(value.args and isinstance(value.args[0], (ast.Call, ast.BinOp)))
        if q in {'numpy.mean', 'numpy.sqrt', 'numpy.square', 'numpy.array', 'numpy.asarray'} and arg and not nested:
            if q == 'numpy.mean':
                title = 'Calcular el promedio'
                if not value.keywords and len(value.args) == 1:
                    detail = f'Tomamos los números de {arg}, los sumamos y dividimos entre la cantidad de datos.'
                    aside = 'Como repartir la cuenta en partes iguales.'
                else:
                    detail = f'Calculamos el promedio de {arg} siguiendo las opciones escritas en la llamada.'
            elif q == 'numpy.sqrt':
                title, detail = 'Obtener la raíz cuadrada', f'Pedimos a sqrt la raíz cuadrada de {arg}. Por ejemplo, la raíz de 9 es 3, porque 3 × 3 = 9.'
            elif q == 'numpy.square':
                title, detail = 'Elevar al cuadrado', f'Multiplicamos cada valor de {arg} por sí mismo con square.'
            else:
                title, detail = 'Preparar números para calcular', f'Organizamos {arg} en un arreglo de NumPy: un grupo de datos con el que podemos hacer cálculos.'
        elif q == 'scipy.io.loadmat' and arg:
            title, detail = 'Abrir el archivo MATLAB', f'Abrimos el archivo indicado por {arg}. Recibimos sus variables en un diccionario: cada nombre sirve para encontrar su dato.'
            aside = 'Como un archivador: buscas la etiqueta y encuentras el contenido.'
        elif q == 'os.path.join':
            title, detail = 'Armar la dirección del archivo', 'Unimos ' + ', '.join(name(a) for a in value.args) + ' para construir una ruta.'
            if any(isinstance(a, ast.Subscript) and isinstance(a.slice, ast.Constant) and a.slice.value == 0 for a in value.args):
                detail += ' [0] elige el primer elemento de la lista, no necesariamente el archivo más reciente.'
        elif q == 'numpy.arange' and value.args:
            title = 'Crear una secuencia de números'
            args = value.args
            opts = {k.arg:name(k.value) for k in value.keywords}
            start = arg if len(args)>1 or 'stop' in opts else '0'
            stop = name(args[1]) if len(args)>1 else opts.get('stop',arg)
            step = name(args[2]) if len(args)>2 else opts.get('step','1')
            detail = f'Creamos números desde {start} hacia {stop}, con un paso de {step}. El límite final queda fuera.'
        elif q == 'numpy.sin' and arg:
            title, detail = 'Calcular el seno', f'Pasamos {arg} a sin. Calcula el seno de esos ángulos, que deben estar en radianes. Con varios ángulos, devuelve un valor para cada uno.'
        elif q in {'numpy.fft.fft', 'numpy.fft.rfft', 'scipy.fft.fft', 'scipy.fft.rfft'} and arg:
            title, detail = 'Transformar las muestras', f'Entregamos las muestras de {arg} a {name(value.func)}. Devuelve números que representan sus componentes de frecuencia; esta llamada todavía no las dibuja.'
        elif q in {'numpy.fft.fftfreq', 'numpy.fft.rfftfreq', 'scipy.fft.fftfreq', 'scipy.fft.rfftfreq'} and arg:
            distance = next((name(k.value) for k in value.keywords if k.arg=='d'),name(value.args[1]) if len(value.args)>1 else '1 (el valor predeterminado)')
            title, detail = 'Preparar el eje de frecuencias', f'Usamos {arg} como cantidad de muestras y {distance} como separación entre ellas. Con eso calculamos las frecuencias del eje.'
        elif q.startswith('matplotlib.pyplot.'):
            op = q.rsplit('.', 1)[-1]
            if op == 'plot':
                title = 'Dibujar los datos'
                if len(value.args) == 1:
                    detail = f'Dibujamos los valores de {arg} en el eje vertical. Su posición 0, 1, 2… se usa en el horizontal.'
                elif len(value.args) == 2 and not isinstance(value.args[1], ast.Constant):
                    detail = f'Usamos {arg} para el eje horizontal y {name(value.args[1])} para el vertical. plot une los puntos según el orden de los datos.'
                else:detail = 'Dibujamos las series indicadas entre paréntesis, siguiendo los estilos y opciones escritos.'
            elif op in {'xlabel', 'ylabel', 'title'} and arg:
                where = {'xlabel':'al eje horizontal','ylabel':'al eje vertical','title':'al título del gráfico'}[op]
                title, detail = 'Poner una etiqueta', f'Ponemos el texto {arg} {where}. Así sabemos qué estamos mirando.'
            elif op == 'show':title, detail = 'Mostrar el gráfico', 'Mostramos las figuras que hemos preparado. Los cálculos y el dibujo se hicieron en las llamadas anteriores.'
            elif op == 'legend':title, detail = 'Identificar las series', 'Añadimos la leyenda al gráfico con las etiquetas indicadas, o con las que ya tienen las series.'
            elif op in {'figure','subplots'}:title, detail = 'Preparar dónde dibujar', 'Preparamos una figura para los gráficos.' + (' subplots devuelve la figura y sus ejes: las zonas donde dibujaremos.' if op=='subplots' else '')
        elif builtin and value.func.id == 'range' and value.args:
            title, detail = 'Preparar las vueltas', f'range prepara una secuencia de enteros con los límites de {name(value)}. El límite final no se incluye.'
        elif builtin and value.func.id == 'print':
            title = 'Mostrar en pantalla'
            # Preserve format specifications and shape lookups from the precise reader.
            if any(isinstance(a, ast.JoinedStr) for a in value.args):
                detail = fallback.replace('Inserta ', 'Ponemos ').replace(' en el texto y lo muestra.', ' dentro del mensaje y lo mostramos en pantalla.')
                import re
                detail = re.sub(r'(\.\d+f): (\d+) decimales', r'El formato \1 muestra \2 decimales', detail)
                if 'decimales' in detail:detail += ' Cambia cómo se ve, no el valor guardado.'
                shape = next((n for a in value.args for n in ast.walk(a) if isinstance(n,ast.Call)
                              and isinstance(n.func,ast.Name) and n.func.id=='getattr' and 'getattr' not in bindings
                              and len(n.args)==3 and isinstance(n.args[1],ast.Constant) and n.args[1].value=='shape'),None)
                if shape:
                    detail = ('Mostramos el mensaje con los valores entre llaves. getattr busca shape: la forma de los datos, '
                              f'por ejemplo filas y columnas. Si no encuentra ese atributo, usa {name(shape.args[2])}.')
            else:
                detail = 'Mostramos ' + (', '.join(name(a) for a in value.args) if value.args else 'una línea vacía') + ' en la salida de la celda.'
            if any(k.arg == 'file' for k in value.keywords):
                title = 'Enviar un mensaje';detail = 'Enviamos el texto al destino indicado por file, en lugar de la salida habitual.'
            elif len(value.args) == 1 and isinstance(value.args[0], ast.Name):
                aside = 'Ya tenemos el dato; ahora le damos voz.'
        elif builtin and value.func.id in {'sum', 'len', 'type'} and arg:
            title, detail = {
                'sum': ('Sumar los datos', f'Sumamos los elementos de {arg}.'),
                'len': ('Contar los elementos', f'Contamos cuántos elementos tiene {arg}. No sumamos sus valores.'),
                'type': ('Reconocer el tipo', f'Consultamos qué tipo de objeto es {arg}, por ejemplo una lista o un número.'),
            }[value.func.id]
            if value.func.id == 'sum' and len(value.args) > 1:detail += f' Empezamos la suma en {name(value.args[1])}.'
        elif not q or not q.startswith(('numpy.', 'scipy.', 'os.', 'matplotlib.', 'pandas.', 'seaborn.', 'sklearn.', '@sklearn.', 'keras.', '@keras.', 'tensorflow.', '@tensorflow.', 'google.colab.')):
            # A method called mean/loadmat/fit is not necessarily NumPy/SciPy/ML.
            title = 'Pedir una tarea a ' + name(value.func)
            inputs = ', '.join(name(a) for a in value.args) or 'ningún dato posicional'
            detail = f'Llamamos a {name(value.func)} con {inputs}. Su tarea depende de cómo se haya definido.'
        if detail and value.keywords and not (builtin and value.func.id == 'print'):
            detail += ' Opciones: ' + ', '.join((k.arg + '=' if k.arg else '**') + name(k.value) for k in value.keywords) + '.'
    if not detail:
        detail = fallback.replace('líneas indentadas', 'líneas desplazadas a la derecha')
        # Remove the old destination sentence before adding a consistent one below.
        if assigned and 'Guarda el resultado en ' in detail:
            detail = detail.split('Guarda el resultado en ')[0].rstrip()
    if assigned:
        detail += ' ' + destination(node)
    return title, detail, aside
