import pandas as pd

df = pd.DataFrame({
    "estado": ["Normal", "Alerta", "Normal"],
    "equipo": ["Motor 1", "Motor 2", "Motor 1"],
})
cols = ["estado", "equipo"]

for col in cols:
    print(col, df[col].unique())
