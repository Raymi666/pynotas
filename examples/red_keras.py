# Ejemplo de lectura estática: las variables de entrada se aportan en el notebook.
from tensorflow import keras as k
red = k.Sequential([k.layers.Dense(64, activation="relu"), k.layers.Dropout(0.2), k.layers.Dense(1)])
red.compile(optimizer="adam", loss="mse", metrics=["mae"])
historia = red.fit(X_train, y_train, epochs=20, batch_size=32, validation_split=0.2)
salidas = red.predict(X_test)
error = red.evaluate(X_test, y_test)
