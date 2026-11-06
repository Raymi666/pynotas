# 0.13.0.dev0 — en desarrollo

- Explicaciones de entradas, acciones y parámetros para SHAP, Keras, PyTorch y MLP.
- Reconocimiento de los imports de PyNotas y SHAP.
- Muestra de referencia separada de los datos que se explican.
- Práctica junto a la última tarjeta cuando hay espacio; evita una hoja casi vacía.
- Guía de contribuciones, plantilla de issues y pruebas automáticas para GitHub.
- Sin ejecución adicional del código ni dependencias nuevas de frameworks.

# Changelog

## 0.12.0 — PyNotas

- SURF IA changes its library name to PyNotas: `pip install pynotas`, `import pynotas`.
- Updated visible branding, PDF/JPG filenames, HTML titles and CLI.
- Preserved the AST analysis, teaching explanations and single-execution notebook integration.
- Legacy opt-out comments, environment variable and appearance option remain accepted.
- A separate surfia-pedagogia compatibility package forwards old imports to PyNotas.

# 0.11.0 · Infografías por tareas y gráficos de la celda

- Modelo intermedio ampliado con etapas pedagógicas e imágenes ya publicadas; esquema 0.11.
- Nuevo render adaptable en carta: tarjetas numeradas, paleta por tarea, iconos vectoriales, sintaxis resaltada y actividad de práctica.
- Se explican cadenas de agrupación, cálculo, ordenación y parámetros de gráficos. Se conservan todos los fragmentos y alcances.
- Copia opcional de PNG/JPEG publicados por la celda mediante el publicador IPython. Sin reevaluar el código ni inspeccionar variables; límites de memoria, restauración de métodos y respeto de la salida original.
- Imágenes reales integradas en SVG, PDF y JPG; lectura estática sin resultados inventados.
- Notebook reproducible con motores, desviación estándar y decisiones; datos sintéticos y comprobaciones numéricas.
- Sin nuevas dependencias obligatorias, sin LLM ni API. La interacción en Colab debe verificarse después de publicar.

# 0.10.0 · Explicar como un profesor cercano

- Nueva lectura pedagógica: datos, acción y destino, con nombres concretos y lenguaje para principiantes.
- Analogías y humor breve separados de la explicación, con un máximo de dos por celda.
- Explicación de 11 puntos, seguida por el código de ancho completo; hojas carta con continuidad de líneas y alcances.
- Se retiran los paneles de teoría del dominio de la lámina. El catálogo sigue en el modelo, sin integrar un LLM ni servicios externos.
- Se conservan la salida plegada, la ejecución única y las exportaciones PDF/JPG.
- El borrador 0.9.2 de estabilidad de Colab se archivó, sin incorporarlo a esta versión.

# 0.9.1 · Carta y fundamento del análisis

- Hojas carta verticales reales (612 × 792 puntos) en PDF, SVG y JPG. Una página si cabe; varias páginas cuando el código lo necesita.
- Teoría al comienzo: objetivo del análisis, fundamento e interpretación. Explicaciones específicas de RMS, FFT y preparación de archivos MATLAB; se conservan los demás conceptos detectados.
- Código y explicación juntos, con lectura compacta, comentarios, líneas originales y continuidad de pasos y alcances entre páginas.
- JPG a 300 ppp (2550 × 3300 píxeles) por página; descargas con nombres distintos para evitar confusión.
- Sin nuevas dependencias, API ni reevaluación del código. Continúa oculto por defecto.

# 0.9.0 · Código y explicación juntos

- Una lámina continua por celda en HTML/SVG, PDF y JPG, sin paginación automática.
- Pasos en orden de lectura, cada fragmento de código junto a su explicación; comentarios y líneas originales conservados.
- Alcances explícitos para condiciones, bucles, funciones y manejo de errores.
- Explicaciones de búsqueda y carga de archivos MATLAB, filtros de diccionario y mensajes con formato.
- Contexto local sobre archivos .mat, diccionarios, tipos y dimensiones.
- Cálculos repartidos entre líneas explicados por su operación inmediata, sin atribuir el cálculo completo a la última línea.
- PDF vectorial con altura variable y JPG de una sola imagen. Se conservan el desplegable exterior y la ejecución única.

# 0.8.0 · 2026-10-09

- Rediseño del generador compartido por HTML/SVG, PDF y JPG. La selección de familia visual es automática y no requiere nueva configuración del estudiante.
- Mapa visual central para señales, redes, aprendizaje, decisiones, recursos y código general; curvas vectoriales, paletas por tema y anotaciones editoriales.
- La condición del código aparece en la primera bifurcación conceptual. Se conservan las explicaciones de ramas y estructuras anidadas.
- Menos repetición de texto cuando el propósito de una importación coincide exactamente con la teoría ya presentada.
- Maquetación y paginación revisadas, con código completo y resultados nativos intactos.

# 0.7.0 · 2026-10-09

- Nuevo diseño vectorial compartido por SVG, PDF y JPG: ilustraciones conceptuales, código con colores, secciones numeradas, tarjetas en columnas y continuidad de páginas.
- 21 conceptos revisados de machine learning/redes neuronales con fuentes oficiales, seleccionados por sintaxis e identidad explícita de importaciones.
- Identificación conservadora de constructores y métodos de scikit-learn y Keras, entre celdas exitosas. Se invalidan identidades ante errores, reasignaciones y mutaciones explícitas.
- Se mantienen importación automática, salida inicialmente oculta, ejecución única y descargas sin servicios externos.
- Ejemplos reproducibles de vibraciones, clasificación y perceptrón multicapa.

# Cambios

## 0.6.0 — 2026-10-08

- Explicación automática plegada por defecto; resultados originales visibles.
- Una única apertura, con código y detalle pedagógico completos en su interior.
- Diseño paginado común para SVG, PDF vectorial y JPG a 300 ppp.
- Botones de descarga autocontenidos y API `exportar`, sin reejecutar código.
- Teoría local revisada para operaciones de NumPy/SciPy y vibraciones.
- Fuentes DejaVu incluidas para exportaciones portátiles.
- Nuevas dependencias locales: ReportLab, PDFium y Pillow.
- Modelo 0.4 con contexto y teoría; compatibilidad con la API de 0.5.
- Límite adicional de 24 páginas por lámina para evitar salidas excesivas.

## 0.5.0 — 2026-10-06

- Base general de código abierto MIT, publicada en PyPI.
- Conserva las láminas simples de 0.4.0 y elimina la dependencia del caso SAG.
- Núcleo sin dependencias externas; IPython es opcional para integración con notebooks.
- API `guardar` / `explicar_archivo` y comando `surfia` para exportar HTML sin ejecutar el archivo.
- Explicaciones internas desplegables de funciones, bucles, clases, contextos, errores y patrones.
- Modelo pedagógico 0.3: cuerpos internos separados del diagrama exterior.
- Lecturas específicas para generadores, funciones lambda, mensajes formateados y control de bucles.
- Protección de archivos existentes y comprobaciones de sintaxis antes de escribir una lámina.

## 0.4.0

- Diseño datos → proceso → resultado, teoría breve y código desplegable.
- Validación del caso SAG sin modificar sus resultados numéricos.
