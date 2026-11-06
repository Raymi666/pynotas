# Cómo se construyen las explicaciones

PyNotas lee el árbol sintáctico (AST), sigue importaciones y asignaciones conocidas,
crea un modelo pedagógico y lo convierte en láminas HTML/SVG, PDF y JPG.
El código del alumno no se vuelve a ejecutar. Las explicaciones son reglas
locales, no respuestas de un LLM. Los resultados del programa siguen perteneciendo
a la ejecución original del notebook.

## Desarrollo 0.13

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
