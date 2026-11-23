# PyNotas

**Tu código, explicado paso a paso.** Biblioteca pedagógica abierta en español.

PyNotas convierte código Python en apuntes visuales en español para acompañar el
aprendizaje. Puedes usarla con código escrito por ti o generado con ayuda de un LLM.
Identifica operaciones conocidas, explica sus pasos y parámetros y organiza las
notas en láminas descargables. Funciona mediante análisis estático y plantillas:
no necesita un LLM ni una API, y no vuelve a ejecutar tu código.

![Ejemplo de notas de PyNotas](https://raw.githubusercontent.com/Raymi666/pynotas/main/docs/ejemplo.png)

## Novedades de 0.13.1

Mejora `print(df[col].unique())`: explica los valores distintos de las columnas
recorridas en `cols`, en lugar de repetir el código. Conserva las explicaciones
de redes neuronales y SHAP de 0.13.0. El ejemplo `examples/valores_unicos.py`
permite probar el cambio con datos sencillos.

## Novedades de 0.13.0

**PyNotas 0.13.0** incorpora explicaciones más concretas para SHAP, Keras,
PyTorch y modelos de scikit-learn: qué datos entran, qué hace cada operación
y qué significan sus parámetros reconocidos. Conserva la ejecución única,
las notas plegadas y las descargas en PDF y JPG.

Por ejemplo, `model.fit(X, y)` explica que `X` contiene las entradas y `y` las
respuestas que el modelo aprende a estimar. `shap.utils.sample(X, 100)` explica
que selecciona filas para una muestra, y que eso aún no calcula valores SHAP.
Consulta la [cobertura y límites](https://github.com/Raymi666/pynotas/blob/main/docs/EXPLICACIONES.md).

## En Google Colab o Jupyter

```python
%pip install pynotas
```

En una nueva celda:

```python
import pynotas
```

Si ya la tenías instalada, actualiza con `%pip install --upgrade pynotas`.
Para usar exactamente esta versión en una clase:

```python
%pip install --upgrade "pynotas==0.13.1"
```

Después reinicia la sesión de Colab o el kernel de Jupyter, vuelve a ejecutar
`import pynotas` y comprueba `pynotas.__version__`. Ejecuta nuevamente las celdas
que quieras explicar: las láminas guardadas antes de actualizar no se regeneran solas.

Ejecuta después una celda de Python. La salida original permanece visible y las
notas aparecen plegadas en **Ver explicación de PyNotas**. Puedes abrirlas,
descargarlas como PDF o JPG y volver a ocultarlas. Se pliegan las notas, no la
celda completa ni sus resultados. Si actualizas una biblioteca ya importada,
reinicia la sesión antes de volver a importarla.

## Opciones

```python
pynotas.activar(oculto=True)           # Notas plegadas al terminar cada celda.
pynotas.activar(capturar_graficos=False)
pynotas.desactivar()
pynotas.activar()
print(pynotas.__version__)
```

No hace falta indicar un contexto para comenzar. `contexto="vibraciones"` y otras
opciones del motor se conservan. Para omitir una celda, incluye `# pynotas: omitir`.
`PYNOTAS_AUTOACTIVAR=0` desactiva el inicio automático antes del primer import.

Fuera de un notebook puedes generar apuntes sin ejecutar el código:

```python
import pynotas
pynotas.guardar("temperaturas = [60, 65, 70, 75]\npromedio = sum(temperaturas) / len(temperaturas)", "apuntes.html")
```

También existe `python -m pynotas archivo.py`.

## Alcance pedagógico

La explicación es una lectura de la sintaxis y de patrones reconocidos; no es
una validación de la corrección del programa ni de sus resultados. Las funciones
desconocidas reciben una explicación general. El objetivo es apoyar el estudio,
la práctica y las preguntas al docente, no sustituirlos ni garantizar aprendizaje.

Los gráficos PNG/JPEG ya publicados por la celda pueden incorporarse sin repetir
los cálculos. No se capturan tablas HTML ni gráficos interactivos que solo emitan
HTML. Las hojas son tamaño carta; los códigos extensos pueden ocupar varias hojas.
Los límites del motor y de captura se mantienen respecto de SURF IA 0.11.0.

## Transición desde SURF IA

La biblioteca antes se distribuía como `surfia-pedagogia` y se importaba con
`import surfia`. El nuevo nombre es `pynotas` en ambos casos. El paquete de
compatibilidad `surfia-pedagogia==0.13.1` depende de PyNotas 0.13.1 y conserva
los imports anteriores. No contiene una segunda copia del motor.

Para actualizar una clase que todavía usa `import surfia`:

```python
%pip install --upgrade "surfia-pedagogia==0.13.1"
```

Reinicia la sesión. Los notebooks anteriores pueden seguir usando `import surfia`.
Para nuevos materiales, usa `import pynotas`.

## Licencia

[MIT](https://github.com/Raymi666/pynotas/blob/main/LICENSE): puedes usar, estudiar, modificar y redistribuir PyNotas, también
con fines comerciales, conservando los avisos de licencia y autoría.
Las fuentes tipográficas incluidas conservan [su propia licencia](https://github.com/Raymi666/pynotas/blob/main/src/pynotas/fonts/LICENSE_DEJAVU).

## Mejorarlo en comunidad

Puedes proponer reglas, mejorar las explicaciones, informar errores y aportar
ejemplos. Consulta [cómo contribuir](https://github.com/Raymi666/pynotas/blob/main/CONTRIBUTING.md). No hace falta implementar
una función para ayudar: una celda mínima y una explicación de por qué la nota
no se entiende son aportes valiosos.

Para probar esta rama desde una copia local:

```sh
python -m pip install -e '.[dev]' -e ./compat
python -m unittest discover -s tests -v
```

El directorio `compat/` conserva el puente para los imports antiguos; el motor
vive únicamente en `src/pynotas/`.
