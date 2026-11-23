"""Explain selected data inside output calls, using syntax and lexical context.

No runtime inspection: an unknown table is described conditionally, and a name
explicitly rebound to an unknown object is not assumed to be pandas.
"""
import ast
from dataclasses import dataclass
from .ml import instance, qualified
from .teaching import short


@dataclass(frozen=True)
class DataMeaning:
    phrase: str
    condition: str = ''
    context: str = ''
    counted: bool = False


def unique_meaning(value, bindings, loops):
    if not isinstance(value, ast.Call) or value.keywords:
        return None
    if (isinstance(value.func, ast.Name) and value.func.id == 'len'
            and 'len' not in bindings and len(value.args) == 1):
        child = unique_meaning(value.args[0], bindings, loops)
        if child and not child.counted:
            return DataMeaning('la cantidad de ' + child.phrase.removeprefix('los '),
                               child.condition, child.context, True)
        return None
    if (not isinstance(value.func, ast.Attribute) or value.func.attr != 'unique'
            or value.args):
        return None
    receiver = value.func.value
    condition, context = '', ''
    if isinstance(receiver, ast.Subscript) and isinstance(receiver.value, ast.Name):
        table, key = receiver.value, receiver.slice
        # A list or slice selects multiple columns/rows, not one Series.
        if not (isinstance(key, ast.Name) or
                isinstance(key, ast.Constant) and type(key.value) in {str, int}):
            return None
        identity = bindings.get(table.id)
        if identity not in {None, '@pandas.DataFrame'}:
            return None
        if identity is None:
            condition = f'Si {table.id} es una tabla de pandas, '
        if isinstance(key, ast.Name) and key.id in loops:
            iterable = short(loops[key.id])
            phrase = f'los valores distintos de cada columna de {table.id} que recorremos en {iterable}, sin repetirlos'
        else:
            label = short(key)
            phrase = f'los valores distintos de la columna {label} de {table.id}, sin repetirlos'
            if isinstance(key, ast.Name):
                context = f'{key.id} indica qué columna seleccionamos.'
    elif instance(receiver, bindings) == '@pandas.Series':
        phrase = f'los valores distintos de {short(receiver)}, sin repetirlos'
    else:
        return None
    return DataMeaning(phrase, condition, context)


def explain(node, bindings, loops):
    """Return a teacher explanation only for supported, immediate operations."""
    if not isinstance(node, (ast.Expr, ast.Assign, ast.AnnAssign)):
        return None
    value = node.value
    if not isinstance(value, ast.Call):
        return None
    if any(isinstance(n, ast.NamedExpr) for n in ast.walk(value)):
        # Assignment expressions can change the meaning of later arguments.
        return None
    assigned = isinstance(node, (ast.Assign, ast.AnnAssign))
    builtin_print = (isinstance(value.func, ast.Name) and value.func.id == 'print'
                     and 'print' not in bindings)
    display = qualified(value.func, bindings) == 'IPython.display.display'
    if not builtin_print and not display:
        meaning = unique_meaning(value, bindings, loops)
        if not meaning:
            return None
        action = 'Contamos ' if meaning.counted else 'Obtenemos '
        phrase = 'los ' + meaning.phrase.removeprefix('la cantidad de ') if meaning.counted else meaning.phrase
        summary = meaning.condition + (action.lower() if meaning.condition else action) + phrase + '.'
        if assigned:
            from .teacher import destination
            summary += ' ' + destination(node)
        title = 'Contar los valores distintos' if meaning.counted else 'Obtener los valores sin repetir'
        return title, summary + (' ' + meaning.context if meaning.context else ''), ''

    # Keep file destinations and print/display options visible; do not claim
    # that every output call prints to the notebook's usual output.
    allowed = {'sep', 'end', 'file', 'flush'} if builtin_print else set()
    if any(k.arg not in allowed for k in value.keywords):
        return None
    meanings, pieces = [], []
    for arg in value.args:
        meaning = unique_meaning(arg, bindings, loops)
        if meaning:
            meanings.append(meaning)
            pieces.append(meaning.phrase)
        elif isinstance(arg, ast.JoinedStr):
            fields = [v for v in arg.values if isinstance(v, ast.FormattedValue)]
            inner = [unique_meaning(f.value, bindings, loops) for f in fields]
            if not any(inner):
                pieces.append('el mensaje ' + short(arg))
                continue
            meanings.extend(m for m in inner if m)
            descriptions = []
            for field, child in zip(fields, inner):
                descriptions.append(child.phrase if child else short(field.value))
                if field.format_spec or field.conversion != -1:
                    descriptions[-1] += ' con la presentación indicada entre llaves'
            pieces.append('el mensaje con ' + ' y '.join(descriptions))
        elif isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            pieces.append('el texto ' + short(arg))
        elif isinstance(arg, ast.Name) and arg.id in loops:
            pieces.append(f'el valor de {arg.id}')
        else:
            pieces.append(short(arg))
    if not meanings:
        return None
    conditions = list(dict.fromkeys(m.condition for m in meanings if m.condition))
    # Multiple unknown tables would need separate qualifications.
    if len(conditions) > 1:
        return None
    condition = conditions[0] if conditions else ''
    file_arg = next((k.value for k in value.keywords if k.arg == 'file'), None)
    redirected = file_arg is not None and not (isinstance(file_arg, ast.Constant) and file_arg.value is None)
    action = 'Enviamos ' if redirected else 'Mostramos '
    summary = condition + (action.lower() if condition else action) + ' y '.join(pieces) + '.'
    if redirected:
        summary += f' El destino lo indica file={short(file_arg)}.'
    for option in value.keywords:
        meaning = {'sep': 'separa los elementos', 'end': 'se añade al final',
                   'flush': 'controla si se fuerza el envío inmediato de la salida'}.get(option.arg)
        if meaning:
            summary += f' {option.arg}={short(option.value)}: {meaning}.'
    contexts = list(dict.fromkeys(m.context for m in meanings if m.context))
    summary += (' ' + ' '.join(contexts)) if contexts else ''
    summary += ' Consultar estos valores no cambia la tabla original.'
    title = 'Enviar los valores sin repetir' if redirected else 'Mostrar los valores sin repetir'
    if all(m.counted for m in meanings):
        title = 'Mostrar cuántos valores distintos hay' if not redirected else 'Enviar la cantidad de valores distintos'
    return title, summary, ''


def invalidate_loops(loops, node):
    """Never reuse a loop relation after its names can have been replaced."""
    changed = {n.id for n in ast.walk(node) if isinstance(n, ast.Name)
               and isinstance(n.ctx, (ast.Store, ast.Del))}
    changed.update(n.name for n in ast.walk(node)
                   if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)))
    for n in ast.walk(node):
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            if any(a.name == '*' for a in n.names):
                return {}
            changed.update(a.asname or a.name.split('.')[0] for a in n.names)
    return {target: iterable for target, iterable in loops.items()
            if target not in changed and not any(isinstance(n, ast.Name) and n.id in changed
                                                 for n in ast.walk(iterable))}
