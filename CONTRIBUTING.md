# Contribuir a PyNotas

Gracias por ayudar a que más personas comprendan su código. Se reciben mejoras
de explicaciones, reglas, diseño, documentación y pruebas.

## Informar una explicación vaga o incorrecta

Abre un issue con un ejemplo pequeño, la versión de PyNotas, la explicación que
aparece y una propuesta en palabras sencillas. Usa datos inventados. No adjuntes
tokens, datos de estudiantes, archivos privados ni salidas completas del notebook.

## Preparar el entorno

Python 3.10 o posterior. Desde la raíz de tu copia del repositorio:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]' -e ./compat
python -m unittest discover -s tests -v
```

En Windows, activa el entorno con `.venv\Scripts\activate`.

## Añadir una explicación

1. Escribe un caso mínimo y consulta la documentación oficial de esa operación.
2. Si se trata de ML, redes o SHAP, añade una regla en `src/pynotas/learning.py`.
   Las identidades reconocidas se siguen en `src/pynotas/ml.py`.
3. Explica la acción con los nombres y parámetros del código: qué entra, qué se
   hace y qué se obtiene. Separa la idea principal de los detalles. Evita repetir
   «usa los parámetros indicados» cuando puedas explicar qué controlan.
4. Añade pruebas con alias, argumentos por nombre, reasignaciones y funciones
   desconocidas. Nunca deduzcas que algo es Keras solo porque se llama `fit`.
5. Revisa la lámina exportada: letra legible, código completo, líneas trazables,
   sin superposiciones ni datos o resultados inventados.
6. Envía un pull request describiendo el problema, el cambio y las pruebas.

El motor no debe ejecutar otra vez el código, importar los frameworks del alumno,
inspeccionar objetos del usuario ni llamar a servicios externos. Una operación no
reconocida debe admitir su límite. Se prefieren reglas pequeñas y comprobables a
explicaciones extensas que prometan comprender cualquier programa.

## Licencia y convivencia

Las contribuciones se distribuyen bajo la misma licencia MIT del proyecto.
Conserva los avisos de autoría y las licencias de las dependencias y fuentes.
Comenta el código y las ideas con respeto; no publiques información personal.
