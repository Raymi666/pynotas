"""Glosario local de recursos conocidos. No importa ni inspecciona módulos."""
import ast
from dataclasses import replace
from .model import Resource

GLOSSARY = {
    "sklearn.preprocessing.StandardScaler": "Prepara una transformación que resta la media y divide por la escala de cada variable.",
    "matplotlib": "Permite crear gráficos y figuras.",
    "matplotlib.pyplot": "Permite dibujar y personalizar gráficos.",
    "seaborn": "Facilita crear gráficos estadísticos.",
    "scipy.io": "Permite leer y guardar datos, incluidos archivos .mat.",
    "scipy.io.loadmat": "Lee los datos de un archivo .mat de MATLAB.",
    "google.colab.drive": "Permite conectar Google Drive con Colab.",
    "google.colab.files": "Permite subir y descargar archivos en Colab.",
    "os": "Permite trabajar con rutas, carpetas y el sistema operativo.",
    "os.path": "Permite construir y consultar rutas de archivos.",
    "numpy": "Permite calcular con arreglos de datos numéricos.",
    "pandas": "Permite organizar y analizar datos en tablas.",
    "scipy.fft": "Ofrece herramientas para analizar frecuencias con Fourier.",
    "scipy.fft.fft": "Calcula la transformada de Fourier de una señal.",
    "scipy.fft.fftfreq": "Genera las frecuencias asociadas a la transformada.",
    "scipy.stats.skew": "Mide la asimetría de una distribución de datos.",
    "scipy.stats.kurtosis": "Calcula la curtosis de una distribución de datos.",
    "matplotlib.backends.backend_pdf.PdfPages": "Permite guardar varias figuras en un mismo PDF.",
}


from .ml import CONSTRUCTORS as _ML_CONSTRUCTORS, FUNCTIONS as _ML_FUNCTIONS, CATALOG as _ML_CATALOG
for _name,_key in {**_ML_CONSTRUCTORS,**_ML_FUNCTIONS}.items():
    GLOSSARY.setdefault(_name,_ML_CATALOG[_key][1])
    if _name.startswith('keras.'):
        GLOSSARY.setdefault('tensorflow.'+_name,_ML_CATALOG[_key][1])
GLOSSARY.update({
    'pynotas':'Genera apuntes visuales del código y permite descargarlos, sin volver a ejecutar sus instrucciones.',
    'shap':'Ayuda a estimar el aporte de cada variable a la salida de un modelo, respecto de una referencia.',
    'torch':'Permite calcular con tensores y construir redes neuronales.',
    'torch.nn':'Reúne capas y funciones de pérdida para redes neuronales.',
    'tensorflow':'Ofrece herramientas para calcular con tensores y construir modelos de aprendizaje.',
    'sklearn':'Ofrece herramientas para preparar datos, entrenar modelos y evaluar predicciones.',
    'keras':'Permite construir y entrenar redes neuronales por capas.',
    'tensorflow.keras':'Ofrece la interfaz Keras para construir y entrenar redes neuronales.',
    'keras.layers':'Reúne las capas que se conectan para construir una red neuronal.',
    'tensorflow.keras.layers':'Reúne las capas para construir una red neuronal con Keras.',
})

def describe_import(node):
    names, summaries, details, resources = [], [], [], []
    for alias in node.names:
        if isinstance(node, ast.Import):
            qualified = alias.name
            binding = alias.asname or alias.name.split('.')[0]
            fallback = "Recurso importado; su función no está en el glosario local."
        else:
            module = '.' * node.level + (node.module or '')
            qualified = module + '.' + alias.name
            binding = alias.asname or alias.name
            fallback = ("Importa los nombres públicos disponibles; no se enumeran aquí."
                        if alias.name == '*' else "Nombre importado; su función no está en el glosario local.")
        purpose = GLOSSARY.get(qualified, fallback)
        access = (alias.asname or qualified) if isinstance(node, ast.Import) else binding
        resources.append(Resource(qualified, binding, alias.asname, purpose, access))
        display = alias.name
        if alias.asname:
            display += " · " + alias.asname
        names.append(display)
        summaries.append((alias.name + ": " if len(node.names) > 1 else "") + purpose)
        alias_note = (f" En el código se usa el alias {alias.asname}." if alias.asname else
                      f" El nombre disponible es {binding}." if alias.name != '*' else "")
        details.append(f"{qualified}: {purpose}{alias_note} Importar prepara el recurso; no implica que sus funciones ya se hayan utilizado.")
    return ', '.join(names), tuple(summaries), ' '.join(details), tuple(resources)


def enrich_setup(blocks, statements, source):
    """Resolve only an uninterrupted prefix of explicit imports and Drive mounts.

    Stop on other statements or wildcard imports: no guesses across assignments,
    branches, arbitrary calls or scopes. No imports or calls are evaluated here.
    """
    bindings = {}
    result = []

    def dotted(expr):
        if isinstance(expr, ast.Name):
            return expr.id
        if isinstance(expr, ast.Attribute):
            root = dotted(expr.value)
            return root + '.' + expr.attr if root else None
        return None

    active = True
    for b, stmt in zip(blocks, statements):
        if active and isinstance(stmt, (ast.Import, ast.ImportFrom)):
            for r in b.resources:
                if r.binding == '*':
                    active = False
                    break
                # Re-imports under the same bound name replace earlier resolution.
                local = (r.alias or r.qualified_name) if isinstance(stmt, ast.Import) else r.binding
                for name in list(bindings):
                    if name.split('.')[0] == r.binding:
                        del bindings[name]
                bindings[local] = r.qualified_name
        elif active and isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            call = stmt.value
            name = dotted(call.func)
            resolved = None
            for local in sorted(bindings, key=len, reverse=True):
                if name == local or (name and name.startswith(local + '.')):
                    resolved = bindings[local] + name[len(local):]
                    break
            if resolved == 'google.colab.drive.mount':
                messages = ['Solicita conectar Drive para acceder a sus archivos desde Colab.']
                for kw in call.keywords:
                    if kw.arg == 'force_remount' and isinstance(kw.value, ast.Constant):
                        if kw.value.value is True:
                            messages.append('force_remount=True solicita montar Drive de nuevo, aunque ya estuviera montado.')
                        elif kw.value.value is False:
                            messages.append('force_remount=False no solicita forzar un nuevo montaje.')
                b = replace(b, kind='setup', title='Conectar Google Drive',
                            summaries=tuple(messages), explanation=' '.join(messages) +
                            ' La lámina no comprueba si se concedió acceso ni si los archivos están disponibles.')
            else:
                active = False
        else:
            active = False
        result.append(b)
    return tuple(result)
