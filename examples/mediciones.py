import numpy as np
import matplotlib.pyplot as plt

mediciones = np.array([8, 9, 10, 11, 12])
promedio = np.mean(mediciones)
desviacion = np.std(mediciones)

plt.plot(mediciones, marker="o", label="Mediciones")
plt.axhline(promedio, color="orange", label="Promedio")
plt.title(f"Desviación estándar: {desviacion:.2f}")
plt.xlabel("Índice de la medición")
plt.ylabel("Valor")
plt.legend()
plt.show()
