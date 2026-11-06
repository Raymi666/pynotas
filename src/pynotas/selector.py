from .analyzer import walk_blocks
from .model import Representation, is_preparation

FORMATS = ("auto", "despiece", "flujo", "decisiones")


def _select(model, requested="auto"):
    if requested not in FORMATS:
        raise ValueError("Formato válido: " + ", ".join(FORMATS))
    decision = any(b.kind == "decision" for b in walk_blocks(model.blocks))
    simple = all(b.kind in {"data", "transform", "operation", "call"} for b in model.blocks)
    compound = any(b.expression for b in model.blocks)
    if requested == "despiece" and not simple:
        raise ValueError("Despiece requiere asignaciones simples y expresiones sin control compuesto. Usa auto o flujo.")
    if requested == "decisiones" and not decision:
        raise ValueError("No se detectó una condición if para representar decisiones.")
    fmt = requested
    if fmt == "auto":
        fmt = "decisiones" if decision else "despiece" if simple and compound else "flujo"
    if fmt == "flujo" and is_preparation(model):
        aliased = next((r for b in model.blocks for r in b.resources if r.alias), None)
        practice = (f"Si cambias el alias {aliased.alias}, ¿qué nombres debes actualizar al usar ese recurso?"
                    if aliased else "Elige una importación: identifica el recurso y el nombre con el que lo usarás.")
        check = (f"El alias {aliased.alias} es un nombre local. Si lo cambias en el import, cambia también las referencias posteriores a ese alias."
                 if aliased else "import prepara un recurso. Una llamada posterior, con paréntesis, solicita una operación concreta.")
        return Representation(fmt, "Prepara tu entorno en Python",
            "Esta celda prepara herramientas y, si aparece, solicita conectar Drive. Las tarjetas agrupan recursos; no representan dependencias entre ellos.",
            "Reconoce qué herramienta aporta cada importación y cómo la usarás en el código.",
            practice,
            "Escribe las importaciones para una tarea de tu clase. Justifica qué aporta cada recurso que elegiste.",
            check)
    if fmt == "decisiones":
        return Representation(fmt, "Comprender las alternativas",
            "Hay condiciones if: se muestran sus caminos posibles.",
            "Una condición abre caminos alternativos que pueden volver a reunirse.",
            "Predice un caso verdadero, uno falso y un caso en el límite. Justifica cada salida.",
            "Adapta la condición a un problema de tu especialidad con datos ficticios.")
    if fmt == "despiece":
        return Representation(fmt, "De los datos a la expresión",
            "Se conectan nombres definidos en esta celda y se descompone una operación.",
            "Relaciona cada nombre con su definición anterior y reconoce qué datos participan en el cálculo.",
            "Cambia un dato y predice qué expresiones podrían verse afectadas antes de ejecutar.",
            "Reutiliza esta estructura de cálculo con datos ficticios de tu especialidad.")
    titles = {b.title for b in model.blocks}
    practice = "Elige una caja y explica con tus palabras qué datos necesita y qué produce."
    apply = "Repite estos pasos con un ejemplo pequeño de tu clase. Explica qué cambiaste."
    if 'Detectar registros repetidos' in titles:
        practice = "Imagina dos filas con el mismo ID y Cycle. ¿Qué debería marcar la búsqueda de repeticiones?"
        apply = "Crea una tabla de tres filas, repite una clave y comprueba qué filas quedan marcadas."
    elif 'Calcular la media y la escala' in titles or 'Poner los datos en otra escala' in titles:
        practice = "¿Qué datos se usan para aprender la media y la escala? Localízalos en el código."
        apply = "Transforma otra campaña con la misma referencia y compara sus valores."
    elif 'Elegir filas y columnas' in titles:
        practice = "Predice qué parte de la tabla quedará después de la selección."
        apply = "Cambia un criterio de selección y comprueba qué filas o columnas aparecen."
    elif 'Resumir por ID' in titles:
        practice = "¿Cuántos grupos esperas? Comprueba cuántos ID diferentes aparecen."
        apply = "Añade un resumen que te ayude a comparar las campañas y explica qué calcula."
    elif 'Guardar una tabla en CSV' in titles:
        practice = "Localiza el nombre del archivo y la tabla que se guardará en él."
        apply = "Abre el archivo guardado y comprueba sus filas y columnas."
    return Representation(fmt, "Así trabaja tu código",
        "Las cajas resumen las acciones que reconoce el analizador local.",
        "Cada caja explica una acción. El código completo conserva sus líneas originales.",
        practice, apply)


def select(model, requested="auto"):
    """Select both the representation and its reviewed local lesson."""
    from dataclasses import replace
    from .lessons import choose_lesson
    representation = _select(model, requested)
    return replace(representation, lesson_key=choose_lesson(model, representation).key)
