# Ejemplo de lectura estática: las variables de entrada se aportan en el notebook.
import shap as sh
exp = sh.Explainer(model.predict, X_ref)
valores = exp(X_test)
sh.plots.beeswarm(valores, max_display=8, show=False)
sh.plots.waterfall(valores[0], max_display=6)
