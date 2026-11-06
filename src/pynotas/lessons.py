"""Small reviewed local lessons. The renderer never evaluates or imports user code."""
from dataclasses import dataclass
from .model import is_preparation

@dataclass(frozen=True)
class Lesson:
    key: str
    title: str
    idea: str
    incoming: str
    action: str
    outgoing: str
    meaning: str
    glossary: tuple[tuple[str, str], ...] = ()
    source: str = ''

PANDAS = 'https://pandas.pydata.org/docs/'
LESSONS = {
 'scale': Lesson('scale', '¿Cómo cambia Python la escala de los datos?',
    'Los números pueden tener tamaños muy distintos. Estandarizar expresa cada lectura según cuánto se aleja del promedio de su propia columna.',
    'Lecturas de cada variable', 'Restar su promedio y dividir por su dispersión', 'Lecturas en una escala común',
    'Cero corresponde al promedio de referencia. Un valor negativo queda por debajo y uno positivo, por encima. Esto no indica por sí solo una falla.',
    (('Promedio', 'El centro de referencia de los datos.'), ('Dispersión', 'Cuánto varían los datos; aquí se usa la desviación estándar.'),
     ('fit', 'Aprende la referencia con los datos indicados.'), ('transform', 'Usa esa referencia para cambiar la escala.')),
    'https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html'),
 'read': Lesson('read', 'Del archivo a una tabla de Python',
    'Para trabajar con un archivo CSV, Python organiza sus datos en filas y columnas. Cada columna tiene un nombre que permite seleccionarla después.',
    'Archivo CSV', 'Leer y organizar su contenido', 'Tabla para trabajar en Python',
    'Abrir los datos es el primer paso. Mirar las primeras filas ayuda a reconocer su estructura, pero no comprueba todo el archivo.',
    (('Tabla / DataFrame', 'Datos organizados en filas y columnas.'), ('head', 'Muestra las primeras filas.')),
    'https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html'),
 'duplicates': Lesson('duplicates', '¿Qué registros se repiten?',
    'Una repetición depende de qué columnas compares. Dos filas pueden compartir una identificación y contener mediciones diferentes.',
    'Filas de la tabla', 'Comparar las columnas elegidas', 'Marcas para reconocer repeticiones',
    'True significa que la fila queda marcada según la regla elegida; False, que no. Detectar una repetición no la elimina.',
    (('duplicated', 'Marca las repeticiones según las opciones del código.'), ('keep=False', 'Marca todos los miembros de cada repetición.')),
    'https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.duplicated.html'),
 'quality': Lesson('quality', 'Conocer los datos antes de usarlos',
    'Un dato vacío significa que falta información. Revisarlo permite decidir qué hacer antes de calcular o comparar.',
    'Tabla por revisar', 'Buscar valores vacíos y resumirlos', 'Información sobre los datos disponibles',
    'Encontrar datos vacíos no los rellena ni los elimina. Su tratamiento requiere una decisión posterior.',
    (('isna', 'Marca los lugares donde falta un valor.'), ('sum', 'Al sumar marcas True/False, cuenta las verdaderas.')), PANDAS),
 'correlation': Lesson('correlation', '¿Cómo cambian juntas las variables?',
    'La correlación de Pearson resume cómo dos variables aumentan o disminuyen juntas de forma lineal.',
    'Columnas numéricas', 'Comparar cómo cambian juntas', 'Correlaciones entre −1 y 1',
    'Cerca de 1 cambian en el mismo sentido; cerca de −1, en sentidos opuestos. Cerca de 0 hay poca asociación lineal. Correlación no demuestra causa.',
    (('corr', 'Calcula las correlaciones.'), ('abs', 'Obtiene la magnitud sin el signo; no cambia la relación original.')),
    'https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.corr.html'),
 'group': Lesson('group', 'De muchas filas a un resumen por grupo',
    'Agrupar reúne las filas que comparten una característica. Después puedes contar o resumir los datos de cada grupo.',
    'Registros de distintos grupos', 'Reunir por criterio y calcular resúmenes', 'Un resumen para cada grupo',
    'El resumen ayuda a comparar grupos. Para entender cada medida, hay que mirar qué columna y qué cálculo se eligieron.',
    (('groupby', 'Reúne los registros por el criterio indicado.'), ('agg', 'Indica qué resúmenes calcular.')), PANDAS),
 'selection': Lesson('selection', 'Elegir los datos que necesitamos',
    'Una selección permite trabajar con una parte de la tabla. Puede elegir filas que cumplan una condición y columnas concretas.',
    'Tabla disponible', 'Elegir filas o columnas', 'Parte seleccionada de los datos',
    'El criterio determina qué datos quedan en la selección. Seleccionar no significa que el resto de los datos sea incorrecto.',
    (('loc', 'Selecciona por etiquetas o condiciones.'), ('isin', 'Comprueba qué valores están en una lista.'), ('copy', 'Crea una copia para trabajar.')), PANDAS),
 'spread': Lesson('spread', '¿Cuánto cambian los valores?',
    'El promedio resume el centro de los datos. La desviación estándar describe cuánto se dispersan alrededor de ese centro.',
    'Valores numéricos', 'Resumir su centro y su variación', 'Medidas para describir los datos',
    'Una dispersión grande indica mayor variación en la escala de esos datos. Por sí sola no significa que el sensor esté fallando.',
    (('mean', 'Calcula el promedio.'), ('std', 'Calcula la desviación estándar.')), PANDAS),
 'mean': Lesson('mean', 'De varios valores a un promedio',
    'El promedio aritmético reparte la suma total entre la cantidad de valores. Resume el conjunto con un número.',
    'Valores que queremos resumir', 'Sumar y dividir por la cantidad', 'Un valor de resumen',
    'El promedio ayuda a describir el centro del conjunto. No muestra cuánto cambia cada medición.',
    (('sum', 'Suma valores.'), ('len', 'Cuenta elementos.'), ('/', 'Divide el valor de la izquierda por el de la derecha.'))),
 'export': Lesson('export', 'Guardar los datos para usarlos después',
    'Exportar una tabla a CSV permite abrir sus datos en otro momento o en otra herramienta.',
    'Tabla en Python', 'Escribir filas y columnas en un archivo', 'Archivo CSV',
    'La tabla guardada depende de las filas y columnas seleccionadas. El código indica la ubicación y las opciones de exportación.',
    (('to_csv', 'Guarda la tabla en formato CSV.'), ('index=False', 'Evita añadir el índice como una columna del archivo.')), PANDAS),
 'decision': Lesson('decision', 'Una pregunta cambia el camino del código',
    'Python comprueba una condición. Si se cumple, sigue un camino; si no, puede seguir otro.',
    'Datos para comparar', 'Preguntar si se cumple una condición', 'Una de las alternativas del código',
    'El diagrama muestra caminos posibles. Para conocer el resultado de esta ejecución, mira la salida original de la celda.',
    (('if', 'Introduce la condición.'), ('else', 'Indica qué hacer si no se cumple.'), ('True / False', 'Verdadero / falso.'))),
 'generic': Lesson('generic', '¿Qué hace este código?',
    'Cada instrucción indica una acción. Sigue los nombres para reconocer qué datos usa y dónde guarda o muestra el resultado.',
    'Datos escritos o preparados antes', 'Seguir las instrucciones del código', 'Datos, mensajes o cambios indicados',
    'Los nombres permiten volver a usar los datos. El detalle de cada paso conserva el código completo.',
    (('=', 'Guarda un resultado con el nombre de la izquierda.'), ('Paréntesis', 'En una llamada, contienen los datos que recibe la función.'))),
 'preparation': Lesson('preparation', 'Las herramientas que usará tu código',
    'Importar hace disponibles herramientas para trabajar. Cada nombre permite acceder después a sus funciones.',
    '', '', '', 'Importar una herramienta no realiza todavía todo el análisis.',
    (('import', 'Hace disponible un recurso de Python.'), ('as', 'Le asigna un nombre corto para escribirlo después.'))),
}

LESSONS['scale_fit'] = Lesson('scale_fit', 'Preparar la referencia para cambiar la escala',
    'Antes de transformar los datos, la herramienta necesita conocer el promedio y la dispersión de cada columna de referencia.',
    'Datos elegidos como referencia', 'Aprender el promedio y la dispersión', 'Parámetros guardados en la herramienta',
    'fit prepara la referencia. Para obtener valores transformados se necesita usar transform después.',
    LESSONS['scale'].glossary, LESSONS['scale'].source)

LESSONS.update({
 'function': Lesson('function', 'Dar un nombre a una tarea para reutilizarla',
    'Una función reúne instrucciones. Definirla prepara la tarea; una llamada permite usarla con los datos que recibe.',
    'Datos que recibirá la función', 'Seguir las instrucciones definidas', 'Un valor devuelto o los efectos de la tarea',
    'Los parámetros dan nombre a los datos que recibe la función. El detalle permite seguir sus instrucciones y reconocer qué entrega return.',
    (('def', 'Define una función con un nombre.'), ('Parámetros', 'Nombres de los datos que puede recibir.'), ('return', 'Entrega un resultado y termina esa llamada.'))),
 'loop': Lesson('loop', 'Repetir una tarea sin escribirla muchas veces',
    'Un bucle repite instrucciones: for recorre elementos y while comprueba una condición antes de cada vuelta.',
    'Elementos o una condición', 'Repetir las instrucciones del interior', 'Los efectos de las vueltas realizadas',
    'Puede haber cero, una o muchas vueltas. La lámina explica la estructura; no observa el número de repeticiones.',
    (('for', 'Recorre los elementos de un objeto.'), ('while', 'Repite mientras su condición sea verdadera.'), ('break', 'Sale del bucle.'), ('continue', 'Pasa a la siguiente vuelta.'))),
 'errors': Lesson('errors', 'Preparar una respuesta cuando algo falla',
    'try agrupa instrucciones que pueden fallar. except indica cómo responder a ciertos errores.',
    'Instrucciones por intentar', 'Realizarlas y responder a errores previstos', 'Continuación o propagación de un error',
    'El detalle distingue intento, respuestas, else y finally. La lámina no afirma que haya ocurrido una excepción.',
    (('try', 'Contiene las instrucciones del intento.'), ('except', 'Responde al tipo de error indicado.'), ('finally', 'Se ejecuta al salir del intento, incluso si hay un error.'))),
 'context': Lesson('context', 'Trabajar con un recurso y gestionar su cierre',
    'with utiliza un gestor de contexto. Por ejemplo, puede abrir un archivo y encargarse de cerrarlo al salir del bloque.',
    'Un recurso o contexto', 'Realizar las instrucciones del bloque', 'Salida del contexto según sus reglas',
    'El comportamiento concreto depende del gestor utilizado. Leer esta explicación no abre el archivo ni ejecuta el bloque.',
    (('with', 'Entra y sale de un contexto.'), ('as', 'Asigna un nombre al recurso entregado por el contexto.'))),
 'patterns': Lesson('patterns', 'Elegir una acción según la forma del dato',
    'match compara un dato con patrones. Los casos se revisan en orden y se utiliza el primero que coincida y cumpla su condición.',
    'Dato para comparar', 'Revisar los patrones case', 'El primer caso coincidente, si existe',
    'El detalle presenta todos los casos posibles. No señala ninguno como ejecutado.',
    (('match', 'Introduce el dato que se compara.'), ('case', 'Describe un patrón.'), ('_', 'Puede actuar como patrón que acepta cualquier valor.'))),
 'class': Lesson('class', 'Organizar datos y operaciones en un tipo de objeto',
    'Una clase permite definir cómo serán ciertos objetos y qué operaciones tendrán disponibles.',
    'Una definición de clase', 'Preparar sus atributos y métodos', 'Un tipo para crear objetos',
    'El cuerpo de la clase se evalúa al definirla; los cuerpos de sus métodos no se ejecutan solo por aparecer en esa definición.',
    (('class', 'Define un tipo de objeto.'), ('Método', 'Una función definida dentro de la clase.'))),
})

LESSONS['async_function'] = Lesson('async_function', 'Preparar una tarea asíncrona',
    'async def define una función asíncrona. Su llamada prepara una tarea que necesita await u otro mecanismo compatible para ejecutarse.',
    'Datos de la llamada', 'Preparar y esperar la tarea', 'Resultado cuando la tarea termina',
    'Definir o llamar la función no equivale por sí solo a completar su cuerpo. El detalle permite leer sus instrucciones.',
    (('async def', 'Define una función asíncrona.'), ('await', 'Espera el resultado de una operación compatible.')))

def choose_lesson(model, representation):
    if is_preparation(model):
        return LESSONS['preparation']
    if representation.format == 'decisiones':
        return LESSONS['decision']
    # No lessons from bodies of functions, branches or loops not expanded here.
    topics = {t for b in model.blocks for t in b.topics}
    for key in ('scale','scale_fit','read','export','duplicates','quality','correlation','group','spread','selection','mean','function','async_function','loop','errors','context','patterns','class'):
        if key in topics:
            return LESSONS[key]
    return LESSONS['generic']
