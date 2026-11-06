"""Lecturas pedagógicas locales. Solo sintaxis: sin ejecutar ni consultar objetos.

Los métodos se describen según su uso habitual en Python/pandas/scikit-learn.
No se resuelven tipos ni se atribuyen resultados observados.
"""
import ast
from dataclasses import replace


def short(node):
    return ast.unparse(node) if node is not None else ''


def names(node):
    if isinstance(node, (ast.Tuple, ast.List)):
        return ', '.join(names(n) for n in node.elts)
    return short(node)


def method(call):
    if isinstance(call, ast.Call):
        if isinstance(call.func, ast.Attribute):
            return call.func.attr
        if isinstance(call.func, ast.Name):
            return call.func.id
    return ''


def keyword(call, key, default=None):
    for k in call.keywords:
        if k.arg == key and isinstance(k.value, ast.Constant):
            return k.value.value
    return default


def recipe(value):
    """Return a title and a short reading, never an inferred runtime value."""
    if isinstance(value, ast.Call):
        op = method(value)
        recipes = {
            'to_frame': ('Organizar como tabla', 'Convierte la serie seleccionada en una tabla.'),
            'append': ('Añadir un elemento', 'Añade el elemento indicado al final, según el objeto utilizado.'),
            'split': ('Separar un texto', 'Divide un texto en partes usando el separador indicado.'),
            'strip': ('Limpiar los extremos del texto', 'Quita los espacios o caracteres indicados de los extremos.'),
            'sorted': ('Ordenar elementos', 'Construye una lista ordenada a partir de los elementos indicados.'),
            'range': ('Preparar una secuencia de números', 'Describe una secuencia de enteros; el límite final no se incluye.'),
            'read_csv': ('Abrir los datos', 'Lee un archivo CSV y organiza su contenido en una tabla.'),
            'DataFrame': ('Organizar una tabla', 'Reúne los datos indicados en filas y columnas.'),
            'head': ('Ver las primeras filas', 'Muestra el inicio de la tabla para revisar cómo están organizados los datos.'),
            'copy': ('Trabajar con una copia', 'Crea una copia para trabajar sin reemplazar la tabla de origen.'),
            'groupby': ('Reunir registros por grupo', 'Agrupa los registros que comparten el criterio indicado.'),
            'agg': ('Calcular un resumen', 'Calcula los resúmenes indicados, como cantidades, mínimos o máximos.'),
            'sort_values': ('Ordenar los registros', 'Ordena según las columnas indicadas para facilitar la lectura.'),
            'drop_duplicates': ('Quitar repeticiones', 'Conserva una aparición según las columnas y opciones indicadas.'),
            'isna': ('Encontrar datos vacíos', 'Marca dónde falta un valor para poder contarlo o revisarlo.'),
            'isnull': ('Encontrar datos vacíos', 'Marca dónde falta un valor para poder contarlo o revisarlo.'),
            'isin': ('Elegir valores de una lista', 'Marca los elementos que están en la lista indicada.'),
            'mean': ('Calcular un promedio', 'Resume los valores mediante su promedio.'),
            'sum': ('Sumar los valores', 'Suma los elementos; si son marcas de verdadero/falso, cuenta los verdaderos.'),
            'len': ('Contar elementos', 'Cuenta cuántos elementos contiene el objeto indicado.'),
            'std': ('Medir cuánto varían', 'Calcula cuánto se dispersan los valores respecto del promedio.'),
            'corr': ('Comparar cómo varían', 'Calcula asociaciones entre columnas numéricas; no demuestra causas.'),
            'describe': ('Resumir los datos', 'Reúne medidas para conocer la distribución de los datos.'),
            'nunique': ('Contar valores diferentes', 'Cuenta cuántos valores distintos aparecen.'),
            'unique': ('Reconocer valores diferentes', 'Reúne los valores distintos que aparecen.'),
            'eq': ('Buscar coincidencias', 'Compara con el valor indicado y marca verdadero o falso.'),
            'diff': ('Comparar con el dato anterior', 'Calcula la diferencia respecto de otro registro de la secuencia.'),
            'rename': ('Cambiar los nombres', 'Asigna las etiquetas indicadas para facilitar la lectura.'),
            'to_csv': ('Guardar una tabla en CSV', 'Escribe la tabla en el archivo indicado para poder usarla después.'),
            'print': ('Mostrar un mensaje', 'Presenta el mensaje o los valores indicados en la salida de la celda.'),
            'display': ('Ver el resultado', 'Presenta el objeto indicado en la salida de la celda.'),
            'StandardScaler': ('Preparar el cambio de escala', 'Crea una herramienta para expresar los sensores en escalas comparables.'),
            'fit': ('Aprender los parámetros', 'Ajusta la herramienta con los datos indicados. Su función depende de cómo se creó.'),
            'transform': ('Aplicar la transformación', 'Usa los parámetros de la herramienta para transformar los datos indicados.'),
            'fit_transform': ('Ajustar y transformar', 'Aprende los parámetros con estos datos y después los transforma.'),
            'assign': ('Añadir datos a una tabla', 'Construye una tabla con las columnas indicadas añadidas o actualizadas.'),
            'tolist': ('Crear una lista', 'Convierte los valores seleccionados en una lista de Python.'),
            'round': ('Redondear para leer mejor', 'Redondea los valores con la precisión indicada.'),
        }
        if op in {'print', 'display'} and len(value.args) == 1 and isinstance(value.args[0], ast.Name):
            return 'Ver el resultado', f'Muestra el contenido de {value.args[0].id} debajo de la celda.'
        if op == 'display' and len(value.args) == 1 and method(value.args[0]) == 'head':
            return recipe(value.args[0])
        if op == 'mean' and isinstance(value.func, ast.Attribute) and isinstance(value.func.value, ast.Subscript):
            col = value.func.value.slice
            if isinstance(col, ast.Constant) and isinstance(col.value, str):
                return 'Calcular un promedio', f'Calcula el promedio de {col.value} en {short(value.func.value.value)}.'
        if op == 'drop_duplicates' and keyword(value, 'keep') is False:
            return 'Quitar grupos repetidos', 'Retira todas las filas que repiten los criterios indicados.'
        if op == 'duplicated':
            all_members = keyword(value, 'keep') is False
            return ('Detectar registros repetidos',
                    'Marca todas las apariciones de cada repetición.' if all_members else
                    'Marca repeticiones según las columnas y opciones indicadas.')
        # Explain the combined operation, rather than only the last call in a chain.
        if op == 'agg' and isinstance(value.func, ast.Attribute) and method(value.func.value) == 'groupby':
            group = value.func.value
            key = group.args[0] if group.args else None
            if isinstance(key, ast.Constant) and key.value == 'ID':
                return 'Resumir por ID', 'Reúne las filas con el mismo ID y calcula un resumen para cada grupo.'
            return 'Resumir cada grupo', 'Reúne registros por el criterio indicado y calcula sus resúmenes.'
        if op in {'copy', 'sort_values'} and isinstance(value.func, ast.Attribute):
            receiver = value.func.value
            chain = receiver
            while isinstance(chain, ast.Call) and isinstance(chain.func, ast.Attribute):
                chain = chain.func.value
            if isinstance(chain, ast.Subscript) and isinstance(chain.value, ast.Attribute) and chain.value.attr in {'loc','iloc'}:
                condition = chain.slice
                if isinstance(condition, ast.Compare) and len(condition.ops) == 1 and isinstance(condition.ops[0], ast.Eq) and isinstance(condition.left, ast.Subscript) and isinstance(condition.left.slice, ast.Constant) and isinstance(condition.comparators[0], ast.Constant):
                    col, val = condition.left.slice.value, condition.comparators[0].value
                    if isinstance(col, str) and len(str(val)) < 30:
                        return 'Elegir las filas que coinciden', f'Elige las filas donde {col} es {val} y ' + ('crea una copia.' if op == 'copy' else 'las ordena.')
                return ('Elegir filas y columnas',
                        'Selecciona la parte indicada de la tabla y ' + ('crea una copia para trabajar.' if op == 'copy' else 'ordena los registros.'))
        if op in recipes:
            return recipes[op]
        return 'Usar una función', 'Solicita la operación indicada. Consulta el código para identificar la función y sus datos.'
    if isinstance(value, ast.Subscript):
        if isinstance(value.value, ast.Attribute) and value.value.attr in {'loc','iloc'}:
            return 'Elegir filas y columnas', 'Selecciona la parte de la tabla indicada entre los corchetes.'
        return 'Elegir una parte de los datos', 'Usa lo escrito entre corchetes para seleccionar elementos.'
    if isinstance(value, ast.Attribute) and value.attr == 'shape':
        return 'Consultar el tamaño', 'Consulta las dimensiones de los datos.'
    if isinstance(value, ast.Compare):
        return 'Marcar los datos que cumplen', 'Compara los valores y obtiene verdadero o falso para cada comparación.'
    if isinstance(value, ast.GeneratorExp):
        return 'Preparar un generador', 'Prepara valores que se irán obteniendo al recorrer el generador; aquí no materializa una lista.'
    if isinstance(value, ast.Lambda):
        return 'Preparar una función breve', 'Define una función de una expresión; su cuerpo se usa al llamarla.'
    if isinstance(value, ast.JoinedStr):
        return 'Construir un mensaje', 'Inserta los valores indicados entre llaves dentro del texto.'
    if isinstance(value, ast.IfExp):
        return 'Elegir entre dos valores', 'La condición decide cuál de las dos expresiones proporciona el valor.'
    if isinstance(value, (ast.ListComp, ast.SetComp, ast.DictComp)):
        return 'Reunir elementos', 'Recorre los elementos indicados y construye el resultado; aplica los filtros que aparezcan.'
    if isinstance(value, ast.BinOp):
        if isinstance(value.op, ast.Add) and any(isinstance(n, ast.List) for n in (value.left, value.right)):
            return 'Unir listas', 'Reúne los elementos de las listas en el orden escrito.'
        if isinstance(value.op, ast.Add) and all(isinstance(n, ast.Constant) and isinstance(n.value, str) for n in (value.left, value.right)):
            return 'Unir textos', 'Coloca un texto a continuación del otro.'
        if isinstance(value.op, ast.Add) and not all(isinstance(n, ast.Constant) and isinstance(n.value, (int, float, complex)) for n in (value.left, value.right)):
            return 'Combinar valores', 'Usa el signo + para combinar los datos según su tipo.'
        titles = {ast.Add:'Sumar', ast.Sub:'Calcular una diferencia', ast.Mult:'Multiplicar',
                  ast.Div:'Calcular una razón', ast.Mod:'Calcular el resto', ast.Pow:'Elevar a una potencia'}
        if isinstance(value.op, ast.Div):
            return 'Calcular una razón', 'Divide la expresión de la izquierda entre la de la derecha y guarda el resultado. El divisor no debe ser cero.'
        return titles.get(type(value.op), 'Hacer un cálculo'), 'Combina los datos de la expresión y guarda el resultado.'
    if isinstance(value, (ast.List, ast.Tuple, ast.Dict, ast.Set)):
        return 'Preparar los datos', 'Reúne los elementos escritos en el código para utilizarlos después.'
    if isinstance(value, ast.Constant):
        return 'Guardar un dato', 'Guarda el valor ' + (short(value) if len(short(value)) < 55 else 'escrito en el código') + ' con un nombre.'
    if isinstance(value, ast.Name):
        return 'Guardar una referencia', 'Usa otro nombre para referirse al mismo objeto; no crea una copia.'
    return 'Guardar un resultado', 'Obtiene lo indicado a la derecha y lo guarda con el nombre de destino.'


def topics_for(node):
    """Only inspect immediate expressions, never bodies with deferred execution."""
    structures = {ast.FunctionDef:'function', ast.AsyncFunctionDef:'async_function', ast.For:'loop',
                  ast.AsyncFor:'loop', ast.While:'loop', ast.Try:'errors', ast.With:'context',
                  ast.AsyncWith:'context', ast.Match:'patterns', ast.ClassDef:'class'}
    if type(node) in structures:
        return (structures[type(node)],)
    if not isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Expr)):
        return ()
    value = node.value
    if value is None:
        return ()
    found = set()
    mappings = {'read_csv':'read', 'duplicated':'duplicates', 'isna':'quality',
                'isnull':'quality', 'std':'spread',
                'mean':'mean', 'to_csv':'export', 'isin':'selection'}
    def visit(n):
        if isinstance(n, (ast.Lambda, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            return
        if isinstance(n, ast.Call):
            op = method(n)
            if op in mappings:
                found.add(mappings[op])
            if op == 'agg' and isinstance(n.func, ast.Attribute) and method(n.func.value) == 'groupby':
                found.add('group')
            if op == 'corr' and not n.args and all(k.arg in {'method','min_periods','numeric_only'} for k in n.keywords):
                opts = [k.value for k in n.keywords if k.arg == 'method']
                if not opts or all(isinstance(v, ast.Constant) and v.value == 'pearson' for v in opts):
                    found.add('correlation')
        if isinstance(n, ast.Subscript) and isinstance(n.value, ast.Attribute) and n.value.attr in {'loc','iloc'}:
            found.add('selection')
        for child in ast.iter_child_nodes(n):
            visit(child)
    visit(value)
    return tuple(sorted(found))


def explain(block, node):
    """Enrich the model without changing control flow or dependency semantics."""
    title, text, result = block.title, '', ''
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        return block
    if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
        if node.value is None:
            return replace(block, title='Indicar un tipo de dato', summaries=('Anota el tipo esperado, sin guardar todavía un valor.',))
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        result = ', '.join(names(t) for t in targets)
        title, text = recipe(node.value)
        if isinstance(node, ast.AugAssign):
            title='Actualizar la parte elegida' if isinstance(node.target,ast.Subscript) else 'Actualizar un valor'
            text='Aplica el operador al valor anterior y al de la derecha; guarda el cambio en el mismo destino.'
            if isinstance(node.op, ast.Mult):text='Multiplica el valor anterior por lo indicado a la derecha y guarda el cambio en el mismo destino.'
            if isinstance(node.target,ast.Subscript):text+=' Los corchetes indican qué parte se actualiza.'
        elif any(isinstance(t, ast.Subscript) for t in targets):
            title, text = 'Guardar en la parte elegida', 'Coloca el resultado en la selección indicada entre corchetes.'
        elif any(isinstance(t, ast.Attribute) for t in targets):
            title, text = 'Actualizar una propiedad', 'Guarda el resultado en la propiedad indicada del objeto.'
        elif isinstance(node.value, ast.Attribute) and node.value.attr == 'shape' and any(isinstance(t, (ast.Tuple, ast.List)) for t in targets):
            title, text = 'Contar filas y columnas', 'Consulta las dimensiones y guarda cada una con su nombre.'
    elif isinstance(node, ast.Expr):
        if isinstance(node.value, ast.Call):
            title, text = recipe(node.value)
        else:
            title, text = 'Consultar una expresión', 'Evalúa lo indicado sin guardarlo en un nombre nuevo.'
    elif isinstance(node, ast.Assert):
        title, text = 'Comprobar antes de seguir', 'Si la condición no se cumple, esta comprobación comunica un error.'
        if isinstance(node.test, ast.UnaryOp) and isinstance(node.test.op, ast.Not) and method(node.test.operand) == 'any' and isinstance(node.test.operand.func, ast.Attribute) and method(node.test.operand.func.value) == 'duplicated':
            title, text = 'Comprobar que no se repitan', 'Comprueba que no queden filas repetidas según los criterios indicados.'
        elif method(node.test) == 'all' and isinstance(node.test.func, ast.Attribute) and method(node.test.func.value) == 'isfinite':
            title, text = 'Comprobar los valores numéricos', 'Comprueba que no haya valores vacíos ni infinitos.'
        elif isinstance(node.test, ast.Compare) and len(node.test.ops) == 1 and isinstance(node.test.ops[0], ast.Eq):
            left, right = node.test.left, node.test.comparators[0]
            if method(left) == 'set' and method(right) == 'set':
                title, text = 'Comprobar los valores conservados', 'Comprueba que ambos conjuntos contengan los mismos valores.'
            elif isinstance(left, ast.BinOp) and isinstance(left.op, ast.Add) and method(left.left) == method(left.right) == method(right) == 'len':
                title, text = 'Comprobar el total', 'Comprueba que los dos recuentos sumen el total esperado.'
    elif isinstance(node, ast.If):
        title, text = '¿Se cumple la condición?', 'La respuesta decide qué camino sigue el programa.'
    elif isinstance(node, (ast.For, ast.AsyncFor)):
        title, text = 'Repetir para cada elemento', 'Recorre los elementos indicados y aplica las instrucciones del interior.'
    elif isinstance(node, ast.While):
        title, text = 'Repetir mientras se cumpla', 'Repite las instrucciones mientras la condición sea verdadera.'
    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        title, text = 'Preparar una función', 'Define instrucciones con un nombre para poder llamarlas después; aquí no ejecuta su cuerpo.'
        result = node.name
    elif isinstance(node, ast.ClassDef):
        title, text = 'Definir un tipo de objeto', 'Agrupa datos y operaciones bajo el nombre de la clase.'
        result = node.name
    elif isinstance(node, ast.Raise):
        title, text = 'Avisar de un problema', 'Lanza el error indicado e interrumpe este camino.'
    elif isinstance(node, (ast.With, ast.AsyncWith)):
        title, text = 'Trabajar dentro de un contexto', 'Prepara un contexto para realizar las instrucciones de su interior.'
    elif isinstance(node, ast.Try):
        title, text = 'Preparar una respuesta a errores', 'Intenta las instrucciones y define cómo responder a ciertos errores.'
    elif isinstance(node, ast.Return):
        title, text = 'Devolver un resultado', 'Termina esta llamada a la función y entrega el valor indicado, o None si no hay valor.'
    elif isinstance(node, ast.Break):
        title, text = 'Salir de la repetición', 'Termina el bucle más cercano; no continúa con sus siguientes elementos.'
    elif isinstance(node, ast.Continue):
        title, text = 'Pasar a la siguiente vuelta', 'Omite el resto de esta vuelta y continúa con la siguiente iteración.'
    elif isinstance(node, ast.Match):
        title, text = 'Elegir un caso por su patrón', 'Compara con los casos escritos y utiliza el primero que coincida y cumpla su condición.'
    elif isinstance(node, ast.Delete):
        title, text = 'Eliminar una referencia o elemento', 'Elimina los destinos indicados; no implica borrar un archivo del disco.'
    elif isinstance(node, (ast.Global, ast.Nonlocal)):
        title, text = 'Indicar dónde se usa un nombre', 'Indica que el nombre corresponde a otro ámbito del programa.'
    elif isinstance(node, ast.Pass):
        title, text = 'Dejar este paso vacío', 'No realiza ninguna acción en este lugar.'
    else:
        title, text = 'Revisar esta instrucción', 'Esta regla no explica su función todavía. Abre el código para revisarla.'
    # Longer evidence is retained in the foldout; the diagram leads with purpose.
    return replace(block, title=title, summaries=(text,), result=result,
                   explanation=text + ' ' + block.explanation, topics=topics_for(node))


def enrich_sequence(blocks, statements):
    """Resolve StandardScaler only within straight-line local code.

    Stop at compound constructs; reassignments and calls invalidate known objects.
    Unknown .fit() calls keep a generic, honest description.
    """
    constructor_names = set()
    scaler_names = set()
    result = []
    for b, stmt in zip(blocks, statements):
        if isinstance(stmt, ast.ImportFrom) and stmt.module == 'sklearn.preprocessing' and stmt.level == 0:
            for alias in stmt.names:
                constructor_names.add(alias.asname or alias.name) if alias.name == 'StandardScaler' else None
        elif isinstance(stmt, ast.Import):
            for a in stmt.names:
                constructor_names.discard(a.asname or a.name.split('.')[0])
                scaler_names.discard(a.asname or a.name.split('.')[0])
        elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            call = stmt.value
            if isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name) and call.func.value.id in scaler_names:
                if call.func.attr == 'fit':
                    b = replace(b, title='Calcular la media y la escala', summaries=('Aprende el promedio y la dispersión de cada variable con los datos indicados.',), topics=('scale_fit',))
                elif call.func.attr not in {'transform','fit_transform'}:
                    scaler_names.clear()
            else:
                scaler_names.clear()
        elif isinstance(stmt, ast.Assign):
            call = stmt.value
            if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name) and call.func.value.id in scaler_names:
                if call.func.attr == 'transform':
                    b = replace(b, title='Poner los datos en otra escala', summaries=('Resta el promedio y divide por la dispersión aprendida para cada variable.',), topics=('scale',))
            target_names = {n.id for t in stmt.targets for n in ast.walk(t) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
            new_scaler = (isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id in constructor_names and not call.args and
                          all(k.arg in {'copy', 'with_mean', 'with_std'} and isinstance(k.value, ast.Constant) and (k.arg == 'copy' or k.value.value is True) for k in call.keywords))
            scaler_names -= target_names
            constructor_names -= target_names
            if new_scaler and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                scaler_names.add(stmt.targets[0].id)
            elif any(isinstance(n, ast.Call) for n in ast.walk(stmt.value)) and not (isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name) and call.func.value.id in scaler_names and call.func.attr == 'transform'):
                scaler_names.clear()
            if any(isinstance(t, (ast.Attribute,ast.Subscript)) for t in stmt.targets):
                scaler_names.clear()
        else:
            constructor_names.clear()
            scaler_names.clear()
        result.append(b)
    return tuple(result)
