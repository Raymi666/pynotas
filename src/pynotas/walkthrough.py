"""Source-linked reading steps. AST and tokens only; no execution or object lookup."""
import ast
import io
import tokenize
from dataclasses import replace
from .model import ReadingStep, CaseContext
from .teaching import short, recipe
from .teacher import explain as teacher_explanation


DEFAULTS = {'os': 'os', 'scipy': 'scipy', 'np': 'numpy', 'numpy': 'numpy'}


def qualified(node, bindings):
    if isinstance(node, ast.Name):
        return bindings.get(node.id, '')
    if isinstance(node, ast.Attribute):
        base = qualified(node.value, bindings)
        return base + '.' + node.attr if base else ''
    return ''


def condition(node, bindings):
    if isinstance(node, ast.Call):
        q = qualified(node.func, bindings)
        arg = short(node.args[0]) if node.args else 'la ruta indicada'
        if q == 'os.path.exists':
            return f'Comprueba si existe la ruta {arg}.'
        if q == 'os.path.isdir':
            return f'Comprueba si {arg} es una carpeta.'
        if isinstance(node.func, ast.Attribute) and node.args:
            who = short(node.func.value)
            if node.func.attr == 'endswith':
                return f'Conserva los nombres de {who} que terminan en {arg}.'
            if node.func.attr == 'startswith':
                return f'Comprueba si {who} comienza por {arg}.'
    if (isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not)
            and isinstance(node.operand, ast.Call) and isinstance(node.operand.func, ast.Attribute)
            and node.operand.func.attr == 'startswith' and node.operand.args):
        return f'Excluye las claves de {short(node.operand.func.value)} que comienzan por {short(node.operand.args[0])}.'
    return f'Comprueba {short(node)}; el resultado decide si continúa por este camino.'


def expression_steps(node, bindings):
    """Short, concrete actions for an expression, including its actual operands."""
    if isinstance(node, ast.IfExp):
        yes = ' '.join(expression_steps(node.body, bindings))
        no = ' '.join(expression_steps(node.orelse, bindings))
        return [condition(node.test, bindings), 'Si se cumple: ' + yes, 'Si no: ' + no]
    if isinstance(node, (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)):
        result = []
        for g in node.generators:
            if (isinstance(g.iter, ast.Call) and qualified(g.iter.func, bindings) == 'os.listdir'
                    and g.iter.args):
                result.append(f'Lista los nombres de {short(g.iter.args[0])} y llama {short(g.target)} a cada nombre.')
            elif isinstance(g.iter, ast.Call) and isinstance(g.iter.func, ast.Attribute) and g.iter.func.attr == 'items':
                result.append(f'Recorre los pares nombre y valor de {short(g.iter.func.value)} como {short(g.target)}.')
            else:
                result.append(f'Recorre {short(g.iter)} usando {short(g.target)} para cada elemento.')
            result.extend(condition(c, bindings) for c in g.ifs)
        if isinstance(node, ast.DictComp):
            value = node.value
            if isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id == 'type' and value.args:
                result.append(f'Asocia cada clave {short(node.key)} con el tipo de {short(value.args[0])}, usando type().')
            else:
                result.append(f'Asocia {short(node.key)} con {short(node.value)} en un diccionario.')
        elif isinstance(node, ast.GeneratorExp):
            result.append(f'Prepara {short(node.elt)} para obtenerlo al recorrer el generador; aún no crea una lista.')
        else:
            result.append(f'Reúne {short(node.elt)} en ' + ('una lista.' if isinstance(node, ast.ListComp) else 'un conjunto sin repetidos.'))
        return result
    if isinstance(node, ast.Call):
        q = qualified(node.func, bindings)
        args = [short(a) for a in node.args]
        numeric = {'numpy.sqrt':('sqrt','Obtiene la raíz cuadrada de'),
                   'numpy.mean':('mean','Calcula el promedio de'),
                   'numpy.square':('square','Eleva al cuadrado los valores de'),
                   'numpy.abs':('abs','Obtiene el valor absoluto de'),
                   'numpy.absolute':('absolute','Obtiene el valor absoluto de'),
                   'numpy.max':('max','Selecciona el valor máximo de'),
                   'numpy.amax':('amax','Selecciona el valor máximo de')}
        if q in numeric and args:
            name,verb=numeric[q]
            nested = expression_steps(node.args[0],bindings) if isinstance(node.args[0],(ast.BinOp,ast.Call)) else []
            return nested+[f'{verb} '+('ese resultado' if nested else args[0])+f' con {name}().']
        if q in {'numpy.array','numpy.asarray'} and args:
            return [f'Organiza {args[0]} como un arreglo de NumPy para operar con sus valores.']
        if q == 'numpy.arange':
            return ['Crea una secuencia numérica con los límites y el paso escritos; el límite final queda fuera.']
        if q == 'os.path.join':
            return ['Une los componentes ' + ', '.join(args) + ' para formar una ruta.'] + [
                f'{short(a)} elige el primer elemento: en Python la posición inicial es 0.'
                for a in node.args if isinstance(a, ast.Subscript) and isinstance(a.slice, ast.Constant) and a.slice.value == 0]
        if q == 'scipy.io.loadmat' and args:
            return [f'Lee el archivo MATLAB de {args[0]}.', 'Devuelve un diccionario: cada nombre permite acceder a una variable del archivo.']
        if q == 'os.listdir' and args:
            return [f'Lista los nombres que contiene la carpeta {args[0]}; no carga su contenido.']
        if q in {'os.path.exists', 'os.path.isdir'}:
            return [condition(node, bindings)]
        if isinstance(node.func, ast.Name) and node.func.id in {'print', 'display'}:
            formats = [a for a in node.args if isinstance(a, ast.JoinedStr)]
            fields = [short(v.value) for a in formats for v in a.values if isinstance(v, ast.FormattedValue)]
            if fields:
                result = ['Construye el mensaje insertando ' + ', '.join(fields) + ' en las llaves {…}.', 'Muestra el mensaje debajo de la celda.']
                for a in formats:
                    for v in a.values:
                        if isinstance(v,ast.FormattedValue) and v.format_spec:
                            spec=''.join(n.value for n in v.format_spec.values if isinstance(n,ast.Constant) and isinstance(n.value,str))
                            if spec.startswith('.') and spec.endswith('f') and spec[1:-1].isdigit():
                                result.append(f'{spec} presenta {short(v.value)} con {int(spec[1:-1])} decimales; no cambia el valor guardado.')
                for a in node.args:
                    for n in ast.walk(a):
                        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'getattr'
                                and len(n.args) == 3 and isinstance(n.args[1], ast.Constant) and n.args[1].value == 'shape'):
                            result.append(f'getattr consulta las dimensiones de {short(n.args[0])}; usa {short(n.args[2])} si no tiene shape.')
                return result
            return ['Muestra ' + (', '.join(args) if args else 'una línea vacía') + ' debajo de la celda.']
        if isinstance(node.func, ast.Name) and node.func.id in {'sum', 'len', 'type'} and args:
            return [{'sum':f'Suma los valores de {args[0]}.', 'len':f'Cuenta los elementos de {args[0]}.',
                     'type':f'Consulta el tipo de objeto de {args[0]}.'}[node.func.id]]
        title, detail = recipe(node)
        if title == 'Usar una función':
            params = args + [(k.arg + '=' if k.arg else '**') + short(k.value) for k in node.keywords]
            return [f'Llama a {short(node.func)} con ' + (', '.join(params) if params else 'ningún argumento') + '.',
                    'Su tarea concreta depende de cómo esté definida esa función.']
        return [detail]
    if isinstance(node, ast.BinOp):
        left, right = short(node.left), short(node.right)
        if isinstance(node.op,ast.Pow) and isinstance(node.right,ast.Constant) and node.right.value==2:
            return [f'Eleva {left} al cuadrado (potencia 2).']
        verbs = {ast.Div:f'Divide {left} entre {right}. El divisor debe ser distinto de cero.',
                 ast.Mult:f'Multiplica {left} por {right}.', ast.Sub:f'Resta {right} de {left}.',
                 ast.Pow:f'Eleva {left} a la potencia {right}.', ast.Add:f'Combina {left} y {right} mediante +, según su tipo.',
                 ast.Mod:f'Calcula el resto de dividir {left} entre {right}.', ast.FloorDiv:f'Divide {left} entre {right} y redondea hacia abajo.'}
        return [verbs.get(type(node.op), recipe(node)[1])]
    if isinstance(node, ast.Constant):
        return [f'Usa el valor {short(node)}.']
    if isinstance(node, (ast.List, ast.Tuple, ast.Set, ast.Dict)):
        if isinstance(node, ast.List) and not node.elts:
            return ['Crea una lista vacía: [].']
        return [recipe(node)[1]]
    if isinstance(node, ast.Name):
        return [f'Usa el objeto llamado {node.id}; no crea una copia.']
    if isinstance(node, ast.Subscript):
        if isinstance(node.slice, ast.Constant) and node.slice.value == 0:
            return [f'Toma el primer elemento de {short(node.value)}: la posición inicial es 0.']
        return [f'Selecciona en {short(node.value)} la parte indicada por [{short(node.slice)}].']
    return [recipe(node)[1]]


def describe(node, block, bindings):
    title = block.title if block else 'Leer esta instrucción'
    fallback = list(block.summaries) if block else []
    if block and block.kind == 'setup':
        return title, fallback
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        return title, [r.purpose + ' Nombre de uso: ' + (r.access_name or r.binding) + '.' for r in block.resources]
    if isinstance(node, ast.If):
        test = short(node.test)
        detail = (f'Comprueba si {test} tiene un valor verdadero. Una lista vacía cuenta como falso.'
                  if isinstance(node.test, ast.Name) else condition(node.test, bindings))
        alternate = 'Si es falso, pasa a la alternativa escrita abajo.' if node.orelse else 'Si es falso, omite esas líneas y continúa fuera del if.'
        return 'Elegir qué camino seguir', [detail, 'Si es verdadero, entra en las líneas indentadas. '+alternate]
    if isinstance(node, (ast.For, ast.AsyncFor)):
        return 'Repetir para cada elemento', [f'Recorre {short(node.iter)} y asigna cada elemento a {short(node.target)}.',
                    'Repite las líneas indentadas para cada elemento; si no hay elementos, no entra.']
    if isinstance(node, ast.While):
        return title, [condition(node.test, bindings), 'Repite las líneas indentadas mientras se cumpla; revisa la condición antes de cada vuelta.']
    value = getattr(node, 'value', None)
    if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Expr, ast.Return)) and value is not None:
        parts = expression_steps(value, bindings)
        numeric_q=qualified(value.func,bindings) if isinstance(value,ast.Call) else ''
        precise_numeric=numeric_q in {'numpy.sqrt','numpy.mean','numpy.square','numpy.abs','numpy.absolute','numpy.max','numpy.amax'}
        if block and block.topics and block.summaries and not precise_numeric and not isinstance(value, (ast.IfExp, ast.ListComp, ast.DictComp, ast.SetComp)):
            parts = list(block.summaries)
        if isinstance(node, ast.AugAssign):
            parts = fallback
        if isinstance(value, ast.IfExp) and isinstance(value.body, ast.ListComp):
            title = 'Buscar y filtrar nombres'
        elif isinstance(value, ast.DictComp):
            title = 'Organizar nombres y tipos' if any(isinstance(n, ast.Call) and short(n.func) == 'type' for n in ast.walk(value.value)) else 'Construir un diccionario'
        elif isinstance(value, ast.Call):
            q = qualified(value.func, bindings)
            title = {'numpy.array':'Organizar datos numéricos','numpy.asarray':'Organizar datos numéricos',
                     'numpy.arange':'Crear una secuencia numérica',
                     'numpy.sqrt':'Obtener la raíz cuadrada','numpy.mean':'Calcular el promedio',
                     'os.path.join':'Construir la ruta del archivo', 'scipy.io.loadmat':'Cargar las variables de MATLAB',
                     'os.listdir':'Listar los nombres de una carpeta'}.get(q, title)
            if title == 'Usar una función':
                title = 'Llamar a ' + short(value.func)
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            target = ', '.join(short(t) for t in targets)
            if not any('Guarda el resultado en ' + target in p for p in parts):
                parts.append('Guarda el resultado en ' + target + '.')
        if isinstance(node, ast.Return):
            parts.append('Entrega ese valor y termina esta llamada a la función.')
        return title, parts
    return title, fallback or [block.explanation if block else 'Lee esta instrucción según la sintaxis escrita.']


def brief_reading(node,parts,bindings):
    """Short parallel reading for Letter; the full explanations remain in the model."""
    value=getattr(node,'value',None)
    if isinstance(node,ast.If):
        if parts and parts[0].startswith('Comprueba si la lista '):
            return parts[0]+' Si tiene elementos, sigue las líneas indentadas; si no, toma la alternativa.' if node.orelse else parts[0]+' Si tiene elementos, sigue las líneas indentadas.'
        return f'Si {short(node.test)} es verdadero, entra en el bloque.'+(' Si es falso, usa la alternativa.' if node.orelse else ' Si es falso, lo omite.')
    if isinstance(node,(ast.For,ast.AsyncFor)):
        return f'Recorre {short(node.iter)}: cada elemento pasa a {short(node.target)}. Repite las líneas indentadas.'
    if isinstance(value,ast.IfExp) and isinstance(value.body,ast.ListComp) and len(value.body.generators)==1:
        g=value.body.generators[0]
        if (isinstance(value.test,ast.Call) and qualified(value.test.func,bindings)=='os.path.exists'
                and isinstance(g.iter,ast.Call) and qualified(g.iter.func,bindings)=='os.listdir'
                and value.test.args and g.iter.args and isinstance(value.body.elt,ast.Name)
                and isinstance(g.target,ast.Name) and value.body.elt.id==g.target.id
                and len(g.ifs)==1 and isinstance(g.ifs[0],ast.Call)
                and isinstance(g.ifs[0].func,ast.Attribute) and g.ifs[0].func.attr=='endswith'
                and isinstance(g.ifs[0].func.value,ast.Name) and g.ifs[0].func.value.id==g.target.id
                and len(g.ifs[0].args)==1 and isinstance(value.orelse,ast.List) and not value.orelse.elts):
            return (f'Si existe {short(value.test.args[0])}, lista los nombres de {short(g.iter.args[0])} '
                    f'y conserva los que terminan en {short(g.ifs[0].args[0])}. Si la ruta no existe, crea una lista vacía [].')
        return (f'Si {short(value.test)} es verdadero, recorre {short(g.iter)} como {short(g.target)}'
                + (' y conserva lo que cumple '+', '.join(short(c) for c in g.ifs) if g.ifs else '')
                + f'. Si no, usa {short(value.orelse)}.')
    if isinstance(value,ast.DictComp) and len(value.generators)==1:
        g=value.generators[0]
        if (isinstance(g.target,ast.Tuple) and len(g.target.elts)==2
                and all(isinstance(a,ast.Name) for a in g.target.elts)
                and isinstance(value.key,ast.Name) and value.key.id==g.target.elts[0].id
                and isinstance(value.value,ast.Call) and isinstance(value.value.func,ast.Name)
                and value.value.func.id=='type' and len(value.value.args)==1
                and isinstance(value.value.args[0],ast.Name) and value.value.args[0].id==g.target.elts[1].id):
            return (f'Recorre las parejas de {short(g.iter)} y asocia cada clave con el tipo de su valor. '
                    +' '.join(condition(c,bindings) for c in g.ifs))
        return (f'Recorre {short(g.iter)} como {short(g.target)}; '
                + ('filtra con '+', '.join(short(c) for c in g.ifs)+'; ' if g.ifs else '')
                + f'asocia {short(value.key)} con {short(value.value)}.')
    if isinstance(value,ast.Call):
        q=qualified(value.func,bindings)
        if q=='scipy.io.loadmat' and value.args:return f'Lee {short(value.args[0])}: devuelve las variables del archivo en un diccionario.'
        if q=='os.path.join':return 'Construye la ruta uniendo '+', '.join(short(a) for a in value.args)+'. [0] selecciona el primer elemento.' if any(isinstance(a,ast.Subscript) and isinstance(a.slice,ast.Constant) and a.slice.value==0 for a in value.args) else ' '.join(parts)
        if isinstance(value.func,ast.Name) and value.func.id=='print':
            fields=[v for a in value.args if isinstance(a,ast.JoinedStr) for v in a.values if isinstance(v,ast.FormattedValue)]
            shape=next((n for a in value.args for n in ast.walk(a) if isinstance(n,ast.Call) and short(n.func)=='getattr' and len(n.args)==3 and isinstance(n.args[1],ast.Constant) and n.args[1].value=='shape'),None)
            if shape:return f'Muestra el mensaje con los valores indicados; getattr consulta las dimensiones (shape) y usa {short(shape.args[2])} si ese atributo no existe.'
            if fields:
                formats=[]
                for v in fields:
                    if v.format_spec:
                        spec=''.join(n.value for n in v.format_spec.values if isinstance(n,ast.Constant) and isinstance(n.value,str))
                        if spec.startswith('.') and spec.endswith('f') and spec[1:-1].isdigit():formats.append(f'{spec}: {int(spec[1:-1])} decimales')
                return 'Inserta '+', '.join(short(v.value) for v in fields)+' en el texto y lo muestra.'+(' '+'; '.join(formats)+'.' if formats else '')
            if all(isinstance(a,ast.Constant) and isinstance(a.value,str) for a in value.args):return 'Muestra el texto entre comillas en la salida de la celda.'
    compact=[p for p in parts if not p.startswith('Guarda el resultado en ')]
    return ' '.join(compact or parts)


def enrich_reading(model, tree, initial=None):
    from .analyzer import walk_details
    from .ml import update_bindings
    blocks = {(b.line, b.end_line, b.column, b.end_column): b for b in walk_details(model.blocks)}
    lines = model.source.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    tokens = list(tokenize.generate_tokens(io.StringIO(model.source).readline))
    candidates = []
    matlab_calls = []

    def position(line, bytecol):
        return offsets[line - 1] + len(lines[line - 1].encode('utf-8')[:bytecol].decode('utf-8'))

    def marker(keyword, after, before, scope, label, detail, kind='clause'):
        matches = [t for t in tokens if t.type == tokenize.NAME and t.string == keyword
                   and after < t.start[0] <= before]
        if not matches:
            return
        t = matches[0]
        candidates.append((offsets[t.start[0]-1]+t.start[1],t.start[0],label,(detail,),scope,kind))

    def visit(statements, bindings, scope=(), known_lists=()):
        aliases = dict(bindings)
        lists=set(known_lists)
        for node in statements:
            b = blocks.get((node.lineno, node.end_lineno, node.col_offset, node.end_col_offset))
            title, parts = describe(node, b, aliases)
            if isinstance(node,ast.If) and isinstance(node.test,ast.Name) and node.test.id in lists:
                title='Comprobar si hay elementos'
                parts[0]=f'Comprueba si la lista {node.test.id} contiene algún elemento. Una lista vacía cuenta como falso.'
            start = position(node.lineno, node.col_offset)
            if getattr(node, 'decorator_list', ()):
                start = position(node.decorator_list[0].lineno, max(0,node.decorator_list[0].col_offset-1))
            title, brief, aside = teacher_explanation(node,title,brief_reading(node,parts,aliases),aliases,qualified,b)
            candidates.append((start,node.lineno,title,tuple(parts),scope,'decision' if isinstance(node, ast.If) else 'instruction',brief,aside))
            expr = getattr(node,'value',None)
            if isinstance(expr,ast.Call) and qualified(expr.func,aliases)=='scipy.io.loadmat':
                matlab_calls.append(node.lineno)
            if isinstance(node, ast.If):
                tag = f'L{node.lineno}: {short(node.test)}'
                visit(node.body, aliases, scope + ('Si es verdadero · '+tag,),lists)
                if node.orelse:
                    last = node.body[-1].end_lineno
                    is_elif = isinstance(node.orelse[0],ast.If) and lines[node.orelse[0].lineno-1].lstrip().startswith('elif ')
                    if not is_elif:
                        marker('else',last,node.orelse[0].lineno,scope,'Tomar el camino alternativo','Solo entra aquí si la condición anterior es falsa.')
                    visit(node.orelse,aliases,scope+('Si es falso · '+tag,),lists)
            elif isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
                local = dict(aliases)
                # Function locals shadow imports throughout the function body.
                if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                    for arg in ast.walk(node.args):
                        if isinstance(arg,ast.arg):local[arg.arg]=''
                    for stmt in node.body:
                        for child in ast.walk(stmt):
                            if isinstance(child,ast.Name) and isinstance(child.ctx,ast.Store):local[child.id]=''
                visit(node.body,local,scope+(('Dentro de la clase ' if isinstance(node,ast.ClassDef) else 'Dentro de la función ')+node.name+' · lectura del cuerpo',))
            elif isinstance(node,(ast.For,ast.AsyncFor,ast.While,ast.With,ast.AsyncWith)):
                local = dict(aliases)
                for n in ast.walk(getattr(node,'target',ast.Pass())):
                    if isinstance(n,ast.Name):local[n.id]=''
                visit(node.body,local,scope+(('En cada vuelta' if isinstance(node,(ast.For,ast.AsyncFor,ast.While)) else 'Dentro del contexto')+f' · L{node.lineno}',))
                if getattr(node,'orelse',()):
                    marker('else',node.body[-1].end_lineno,node.orelse[0].lineno,scope,'Al terminar sin break','Se usa si la repetición termina sin ejecutar break.')
                    visit(node.orelse,local,scope+('Al terminar sin break',))
            elif isinstance(node,(ast.Try,getattr(ast,'TryStar',ast.Try))):
                visit(node.body,aliases,scope+('Intento dentro de try',))
                last=node.body[-1].end_lineno
                for handler in node.handlers:
                    name=short(handler.type) if handler.type else 'cualquier excepción'
                    marker('except',last,handler.body[0].lineno,scope,'Responder a un error','Maneja '+name+' si se produce en el intento.')
                    local=dict(aliases)
                    if handler.name:local[handler.name]=''
                    visit(handler.body,local,scope+('Si ocurre '+name,));last=handler.end_lineno
                for key,label in [('orelse','Sin excepción'),('finalbody','Al salir del intento')]:
                    body=getattr(node,key)
                    if body:
                        marker('else' if key=='orelse' else 'finally',last,body[0].lineno,scope,label,
                               'Se usa si try termina sin excepción.' if key=='orelse' else 'Se ejecuta al salir del intento, incluso si hubo un error.')
                        visit(body,aliases,scope+(label,));last=body[-1].end_lineno
            elif isinstance(node,ast.Match):
                last=node.lineno
                for case in node.cases:
                    pattern=short(case.pattern)
                    marker('case',last,case.body[0].lineno,scope,'Comparar un patrón','Prueba '+pattern+(' y la condición '+short(case.guard) if case.guard else '')+'.')
                    local=dict(aliases)
                    for n in ast.walk(case.pattern):
                        if isinstance(n,(ast.MatchAs,ast.MatchStar)) and n.name:local[n.name]=''
                    visit(case.body,local,scope+('Caso '+pattern,));last=case.body[-1].end_lineno
            def list_expression(value):
                return isinstance(value,(ast.List,ast.ListComp)) or (isinstance(value,ast.IfExp) and list_expression(value.body) and list_expression(value.orelse))
            if isinstance(node,(ast.Assign,ast.AnnAssign)):
                targets=node.targets if isinstance(node,ast.Assign) else [node.target]
                for target in targets:
                    if isinstance(target,ast.Name):
                        lists.discard(target.id)
                        if list_expression(node.value):lists.add(target.id)
                    else:lists.clear()
            elif not isinstance(node,(ast.Import,ast.ImportFrom,ast.Pass)):
                lists.clear()
            aliases = update_bindings(node, aliases)
        return aliases

    aliases=dict(DEFAULTS);aliases.update(initial or {})
    visit(tree.body,aliases)
    candidates.sort(key=lambda c:c[0])
    # A leading comment belongs beside the following instruction, not the previous one.
    for i,candidate in enumerate(candidates):
        start=candidate[0]
        line_index=model.source.count('\n',0,start)
        prefix=model.source[offsets[line_index]:start]
        if prefix.strip():continue
        first=line_index
        while first>0 and (not lines[first-1].strip() or lines[first-1].lstrip().startswith('#')):
            if i and offsets[first-1] <= candidates[i-1][0]:break
            first-=1
        # Skip blank separator lines; include comments exactly as written.
        while first<line_index and not lines[first].strip():first+=1
        if first<line_index:
            candidates[i]=(offsets[first],)+candidate[1:]
    steps=[]
    asides=0
    for i,candidate in enumerate(candidates):
        start,line,title,parts,scope,kind=candidate[:6]
        brief=candidate[6] if len(candidate)>6 else ' '.join(parts)
        aside=candidate[7] if len(candidate)>7 and asides<2 else ''
        if aside:asides+=1
        # Partition the original source, including comments and clause headers.
        # It appears once beside the corresponding explanation, never as a second full copy.
        if i==0:start=0
        end=candidates[i+1][0] if i+1<len(candidates) else len(model.source)
        raw=model.source[start:end].rstrip()
        # Preserve indentation when starting at an AST token inside a physical line.
        line_index=model.source.count('\n',0,start)+1
        col=start-offsets[line_index-1]
        prefix=model.source[offsets[line_index-1]:start]
        if prefix.isspace():raw=' '*col+raw
        raw=raw.rstrip('; \t\r\n')
        end_line=line_index+raw.count('\n')
        steps.append(ReadingStep(title,raw,line_index,end_line,parts,scope,kind,brief,aside))
    case=None
    if matlab_calls:
        case=CaseContext('Abrir un archivo MATLAB y reconocer sus datos',
            'La carga de un archivo .mat permite usar en Python variables guardadas desde MATLAB. Sigue cada instrucción para entender cómo prepara estos datos.',
            ('Un archivo .mat guarda variables de MATLAB; pueden ser señales, matrices u otros datos.',
             'loadmat devuelve un diccionario. Las claves __header__, __version__ y __globals__ son metadatos del archivo.',
             'El tipo dice qué clase de objeto es cada valor; shape indica sus dimensiones. Conocer su estructura ayuda a elegir qué datos analizar.'),
            ('Archivo .mat','Cargar variables','Diccionario en Python'),
            ('https://docs.scipy.org/doc/scipy/reference/generated/scipy.io.loadmat.html',))
        if 'os.listdir' in model.source and '[0]' in model.source:
            case=replace(case,facts=case.facts+('listdir no garantiza un orden: [0] elige el primer nombre de esa lista, no necesariamente el más reciente. exists comprueba existencia, no que la ruta sea una carpeta.',),
                         sources=case.sources+('https://docs.python.org/3/library/os.html#os.listdir',))
    return replace(model,steps=tuple(steps),case=case)
