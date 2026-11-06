"""Lee sintaxis exclusivamente: no evalúa, ejecuta ni inspecciona variables."""
import ast
from .model import Block, Expression, PedagogicalModel, Section
from .resources import describe_import, enrich_setup
from .teaching import explain, enrich_sequence

OPS = {ast.Add: "Suma (+)", ast.Sub: "Resta (−)", ast.Mult: "Producto (×)",
       ast.Div: "División (/)", ast.FloorDiv: "División entera (//)",
       ast.Mod: "Resto (%)", ast.Pow: "Potencia (**)"}


def analyze(source, objective="Comprender cómo los datos se transforman en un resultado",
            level="inicial", context="auto", bindings=None):
    if not isinstance(source, str):
        raise TypeError("El código debe ser texto.")
    if not isinstance(objective, str):
        raise TypeError("El objetivo debe ser texto.")
    if level not in {"inicial", "intermedio", "avanzado"}:
        raise ValueError("Nivel válido: inicial, intermedio, avanzado.")
    if len(source) > 60000:
        raise ValueError("La lámina admite hasta 60 000 caracteres por celda.")
    tree = ast.parse(source)
    if sum(1 for _ in ast.walk(tree)) > 1500:
        raise ValueError("Celda demasiado extensa: divídela en pasos pedagógicos.")
    notes = []
    counter = 0

    def segment(node):
        return ast.get_source_segment(source, node) or ""

    def expr(node, depth=0):
        children = ()
        label = "Expresión"
        if isinstance(node, ast.BinOp):
            label = OPS.get(type(node.op), "Operación " + type(node.op).__name__)
            if isinstance(node.op, ast.Add):
                label = "Unir listas (+)" if any(isinstance(n, ast.List) for n in (node.left, node.right)) else "Combinar con +"
            if depth < 4:
                children = (expr(node.left, depth + 1), expr(node.right, depth + 1))
        elif isinstance(node, ast.Name):
            label = "Dato que usaremos"
        elif isinstance(node, ast.Constant):
            label = "Valor escrito"
        elif isinstance(node, ast.Call):
            label = "Resultado de una función"
        return Expression(segment(node), label, node.lineno, node.end_lineno, children)

    def block(node):
        nonlocal counter
        counter += 1
        if counter > 60:
            raise ValueError("La lámina admite hasta 60 instrucciones; divide el código.")
        ident = f"b{counter}"
        code = segment(node)
        kind, title = "opaque", "Bloque de código"
        explanation = "Estructura agrupada; sus pasos internos no se representan en esta versión."
        body, alternative, expression = (), (), None
        reads, writes = (), ()
        summaries = ()
        resources = ()
        sections = []
        if isinstance(node, ast.If):
            kind, title = "decision", "Evaluar condición"
            code = segment(node.test)
            explanation = "La condición selecciona una alternativa. No se observa qué rama se ejecutó."
            body = tuple(block(n) for n in node.body)
            alternative = tuple(block(n) for n in node.orelse)
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            value = node.value
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            simple = all(isinstance(t, ast.Name) for t in targets)
            if simple and value is not None:
                kind, title = "transform", "Obtener y asignar"
                if isinstance(value, (ast.Constant, ast.List, ast.Tuple, ast.Dict, ast.Set)):
                    kind, title = "data", "Definir datos"
                if isinstance(value, ast.BinOp):
                    kind, title, expression = "operation", "Combinar expresiones", expr(value)
                reads = tuple(sorted({n.id for n in ast.walk(value)
                                      if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}))
                writes = tuple(t.id for t in targets)
                if isinstance(node, ast.AugAssign):
                    reads = tuple(sorted(set(reads) | set(writes)))
                # Scope-changing expressions cannot support simple name dependencies.
                if any(isinstance(n, (ast.NamedExpr, ast.Lambda, ast.ListComp,
                                      ast.SetComp, ast.DictComp, ast.GeneratorExp))
                       for n in ast.walk(value)):
                    kind = "opaque"
                explanation = "Relaciona el destino con la expresión de la derecha; no se calcula su valor."
            elif isinstance(node, ast.AnnAssign) and value is None:
                kind, title = "opaque", "Anotar un nombre"
                explanation = "Declara una anotación de tipo sin asignar un valor."
        elif isinstance(node, ast.Expr):
            kind, title = "call", "Evaluar expresión"
            explanation = "Expresión tal como aparece en el código; no se vuelve a evaluar."
            if isinstance(node.value, ast.Call):
                title = "Llamar una operación"
                if isinstance(node.value.func, ast.Name) and node.value.func.id == "print":
                    title = "Mostrar información"
                    explanation = "Llama al nombre print. La salida original permanece en el notebook."
            reads = tuple(sorted({n.id for n in ast.walk(node)
                                  if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}))
            if any(isinstance(n, (ast.NamedExpr, ast.Lambda, ast.ListComp,
                                  ast.SetComp, ast.DictComp, ast.GeneratorExp)) for n in ast.walk(node)):
                kind = "opaque"
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            kind = "import"
            title, summaries, explanation, resources = describe_import(node)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            title = "Definir " + node.name
            explanation = "Definición agrupada. Su cuerpo no se presenta como si se hubiera ejecutado."
        elif isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
            title = "Repetición · bloque agrupado"
        elif isinstance(node, ast.Raise):
            kind, title = "stop", "Lanzar excepción"
            explanation = "Interrumpe este camino mediante una excepción."
        # Nested scopes are explained in foldouts, not attached as executed paths.
        def section(label, statements):
            if statements:
                sections.append(Section(label, enrich_sequence(tuple(block(n) for n in statements), statements)))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            section("Dentro de la función · se utiliza mediante una llamada", node.body)
        elif isinstance(node, ast.ClassDef):
            section("Dentro de la definición de clase", node.body)
        elif isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
            section("Dentro de la repetición", node.body)
            section("Al terminar sin break", node.orelse)
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            section("Dentro del contexto", node.body)
        elif isinstance(node, (ast.Try, getattr(ast, 'TryStar', ast.Try))):
            section("Instrucciones que se intentan", node.body)
            for handler in node.handlers:
                section("Respuesta al error: " + (ast.unparse(handler.type) if handler.type else "cualquier excepción"), handler.body)
            section("Si termina sin excepción", node.orelse)
            section("Al salir de este intento (finally)", node.finalbody)
        elif isinstance(node, ast.Match):
            for case in node.cases:
                label = "Caso: " + ast.unparse(case.pattern)
                if case.guard: label += " · si " + ast.unparse(case.guard)
                section(label, case.body)
        if kind == "opaque":
            notes.append(f"Línea {node.lineno}: ver el código para seguir todos sus pasos.")
        return explain(Block(ident, kind, title, code, node.lineno, node.end_lineno,
                     explanation, reads, writes, body, alternative, expression, summaries, resources, sections=tuple(sections),
                     column=node.col_offset,end_column=node.end_col_offset), node)

    blocks = tuple(block(node) for node in tree.body)
    blocks = enrich_sequence(blocks, tree.body)
    blocks = enrich_setup(blocks, tree.body, source)
    if len(list(walk_blocks(blocks))) > 60:
        raise ValueError("La lámina admite hasta 60 bloques; divide la celda.")
    from .theory import enrich
    blocks, theories = enrich(blocks, tree.body, context, bindings)
    model = PedagogicalModel(source, blocks, objective, level, tuple(notes), context=context, theories=theories)
    from .walkthrough import enrich_reading
    from .stages import enrich_stages
    return enrich_stages(enrich_reading(model, tree, bindings), tree, bindings)


def walk_blocks(blocks):
    for block in blocks:
        yield block
        yield from walk_blocks(block.body)
        yield from walk_blocks(block.alternative)


def walk_details(blocks):
    """Walk all source instructions, including deferred/compound scopes, for detail only."""
    for b in blocks:
        yield b
        yield from walk_details(b.body)
        yield from walk_details(b.alternative)
        for section in b.sections:
            yield from walk_details(section.blocks)
