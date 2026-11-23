# Cómo se construyen las explicaciones

PyNotas lee el árbol sintáctico (AST), sigue importaciones y asignaciones conocidas,
crea un modelo pedagógico y lo convierte en láminas HTML/SVG, PDF y JPG.
El código del alumno no se vuelve a ejecutar. Las explicaciones son reglas
locales, no respuestas de un LLM. Los resultados del programa siguen perteneciendo
a la ejecución original del notebook.

## Valores únicos y contexto del recorrido (0.13.1)

`for col in cols: print(df[col].unique())` se explica como una consulta de los
valores distintos de cada columna de `df` recorrida en `cols`. La nota conecta
la selección de columna con `unique()`, en vez de repetir la expresión de Python.
`len(df[col].unique())` cuenta esos valores distintos; no muestra los valores.
También se reconocen asignaciones, mensajes con varios argumentos, f-strings y
`display` importado desde IPython. El destino de `print(file=...)` se conserva.

Se sigue el origen de `pandas.DataFrame`, `pandas.Series`, `pandas.read_csv` y
`pandas.read_table`, incluidos alias y celdas anteriores observadas. Las lecturas
CSV por bloques no se tratan como tablas. Si no se conoce el origen de `df`, la
explicación comienza con «Si df es una tabla de pandas…». Si el nombre se ha
reasignado a un objeto desconocido, se conserva la explicación general.
No se comprueban los tipos reales, las etiquetas duplicadas, las columnas
jerárquicas ni los valores; la selección debe identificar una sola columna.

El contexto del recorrido se limita al cuerpo correspondiente. Una reasignación
de sus nombres lo invalida; no se traslada a una función definida dentro del bucle
ni a instrucciones posteriores al mismo. Las comprensiones y otras cadenas de
métodos todavía usan las explicaciones anteriores.

## Cobertura de redes neuronales y SHAP (desde 0.13.0)

Las reglas de `learning.py` explican entradas, acciones y opciones concretas para:

- SHAP: `datasets.california`, `utils.sample`/`sample`, `Explainer`,
  `TreeExplainer`, `LinearExplainer`, `DeepExplainer`, `GradientExplainer`,
  `KernelExplainer`, llamadas al explicador, `shap_values`, `beeswarm`, `bar`,
  `waterfall`, `summary_plot`, `dependence_plot` y `force_plot`.
- Keras: `Sequential`, `Model`, `Input`, `Dense`, `Dropout`, `Flatten`, `Adam`,
  `EarlyStopping`, `add`, `compile`, `fit`, `predict` y `evaluate`.
- PyTorch: `Sequential`, `Linear`, `ReLU`, `Sigmoid`, `Softmax`, `Dropout`,
  `Flatten`, `MSELoss`, `CrossEntropyLoss`, `BCEWithLogitsLoss`, `Adam`, `SGD`,
  paso por la red, pérdida, `backward`, `zero_grad`, `step`, `train` y `eval`.
- scikit-learn: mejora de `LinearRegression`, `MLPClassifier`, `MLPRegressor`,
  `fit` y `predict`, sobre modelos cuyo origen puede seguirse en el código.

Se reconocen alias explícitos y objetos construidos por llamadas conocidas,
incluso entre celdas observadas. Una reasignación o un origen ambiguo descarta esa
identidad. Las clases personalizadas, callbacks propios, modelos cargados de un
archivo y muchas otras operaciones todavía reciben una explicación general.
No se garantiza cobertura de cualquier red ni de todos los parámetros.

El constructor de un explicador y el cálculo de contribuciones son pasos distintos.
Una referencia para SHAP tampoco es lo mismo que el conjunto que se quiere explicar.
No se inventan predicciones, unidades, tamaños de tensores, causas ni mejoras de
desempeño. `sample` documenta la diferencia de comportamiento desde SHAP 0.42.

## Referencias primarias de revisión

- [Valores únicos de una serie de pandas](https://pandas.pydata.org/docs/reference/api/pandas.Series.unique.html)
- [Lectura CSV y lectores por bloques](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html)
- [California Housing en SHAP](https://shap.readthedocs.io/en/latest/generated/shap.datasets.california.html)
- [Muestreo de SHAP](https://shap.readthedocs.io/en/latest/generated/shap.utils.sample.html)
- [Explainer](https://shap.readthedocs.io/en/latest/generated/shap.Explainer.html)
- [TreeExplainer](https://shap.readthedocs.io/en/latest/generated/shap.TreeExplainer.html)
- [DeepExplainer](https://shap.readthedocs.io/en/latest/generated/shap.DeepExplainer.html)
- [Beeswarm](https://shap.readthedocs.io/en/latest/generated/shap.plots.beeswarm.html)
- [Waterfall](https://shap.readthedocs.io/en/latest/generated/shap.plots.waterfall.html)
- [Dense](https://keras.io/api/layers/core_layers/dense/)
- [Dropout](https://keras.io/api/layers/regularization_layers/dropout/)
- [Entrenamiento en Keras](https://keras.io/api/models/model_training_apis/)
- [Linear en PyTorch](https://docs.pytorch.org/docs/stable/generated/torch.nn.Linear.html)
- [Adam en PyTorch](https://docs.pytorch.org/docs/stable/generated/torch.optim.Adam.html)
- [LinearRegression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LinearRegression.html)

Las pruebas validan las explicaciones y sus límites sin entrenar redes, instalar
SHAP ni descargar datasets. No sustituyen las pruebas de integración de cada
framework ni la revisión pedagógica de un docente.
