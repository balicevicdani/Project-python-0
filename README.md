# Proyecto Python — Curso 0 (Máster en Ciencias Actuariales, UC3M)

Proyecto personal para el curso 0 de programación del Máster en Ciencias Actuariales de la UC3M. Recorre un caso práctico completo: montar un entorno reproducible, descargar un dataset público desde GitHub, guardarlo en una base de datos SQLite, consultarlo con SQL y hacer un primer análisis estadístico con interés actuarial.

## Estructura

El proyecto es **modular**: las funciones genéricas y reutilizables están en `scripts/`, y el análisis se desarrolla y documenta en los notebooks de `notebooks/`.

```
Project-python-0/
├── requirements.txt          # Dependencias del entorno (versiones exactas)
├── data/
│   ├── seguros.csv           # Dataset (copia exacta del original de GitHub)
│   ├── proyecto.db           # Base de datos SQLite (se genera, no se versiona)
│   └── graficos.pdf          # Todos los gráficos en un PDF (se genera, no se versiona)
├── scripts/
│   ├── __init__.py
│   └── funciones.py          # Todas las funciones reutilizables, organizadas por secciones
├── notebooks/
│   ├── analisis.ipynb        # Análisis principal: importa las funciones y lo ejecuta todo
│   └── practica.ipynb        # Comprobación rápida de que la base de datos y el entorno funcionan
└── tests/
    └── test_funciones.py     # Pruebas automáticas de las funciones
```

`scripts/funciones.py` solo **define** funciones: importarlo no ejecuta ni imprime nada. Todas reciben los datos, las rutas y los nombres de tablas o columnas como parámetros, así que sirven para otras bases de datos, variables o proyectos.

| Sección | Función | Qué hace |
|---|---|---|
| 1. Datos | `descargar_csv(url, ruta_destino)` | Descarga un CSV de una URL (p. ej. GitHub) y guarda una copia exacta; si la descarga falla, no toca la copia local |
| | `cargar_csv_en_db(ruta_csv, ruta_db, nombre_tabla)` | Guarda un CSV como tabla de una base de datos SQLite |
| | `listar_tablas(ruta_db)` | Nombres de las tablas de la base de datos |
| | `leer_tabla(ruta_db, nombre_tabla, columnas=None)` | Lee una tabla (o algunas columnas) como DataFrame |
| 2. SQL | `consultar(ruta_db, sql, parametros)` | Ejecuta cualquier consulta SQL y devuelve un DataFrame |
| | `media_por_grupo(ruta_db, tabla, var_numerica, var_grupo)` | `GROUP BY`: n, media, mínimo y máximo por grupo |
| 3. Visualización | `histograma(datos, ancho_banda=None, titulo=None, ...)` | Histograma de cualquier columna numérica; devuelve `(fig, ax)` |
| | `boxplot_por_grupo(df, var_numerica, var_grupo)` | Diagrama de cajas por grupos; devuelve `(fig, ax)` |
| | `guardar_figuras_pdf(figuras, ruta_pdf)` | Guarda una lista de figuras en un único PDF, una por página |
| 4. Estadística | `tabla_contingencia(df, var_filas, var_columnas)` | Tabla de contingencia de dos variables categóricas (`pd.crosstab`) |
| | `test_asociacion(df, var1, var2)` | Test chi-cuadrado de independencia + V de Cramér + phi (tablas 2×2) |
| | `resumen_asociacion(resultado)` | Resumen en una fila de un test, para comparar varios grupos |

## Cómo reproducirlo

Requisitos: **Python 3.12 o superior** (desarrollado y probado con Python 3.14).

```
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
```

Abre la **carpeta del proyecto** en el editor (en VS Code: *File → Open Folder*), selecciona el kernel `.venv` y ejecuta `notebooks/analisis.ipynb` de principio a fin (*Run All*). El notebook:

1. Descarga el dataset de GitHub (o usa la copia local si no hay conexión) y lo carga en `data/proyecto.db`.
2. Explora los datos y comprueba su calidad (valores que faltan y filas duplicadas).
3. Dibuja los histogramas de edad, BMI y coste médico.
4. Compara el coste médico según las características del asegurado con consultas SQL (`GROUP BY`).
5. Estudia la asociación entre ser fumador y no tener hijos (tabla de contingencia, test chi-cuadrado, phi y V de Cramér), en total y por sexo.
6. Guarda todos los gráficos en `data/graficos.pdf`.

Para ejecutar las pruebas automáticas (no necesitan nada más que lo de `requirements.txt`), desde la carpeta raíz:

```
python -m unittest discover -s tests -v
```

Para abrir los notebooks fuera de VS Code hace falta instalar además Jupyter: `pip install jupyterlab`.

## Dataset

*Medical Cost Personal Datasets* (1.338 asegurados), del libro *Machine Learning with R* de Brett Lantz, publicado en [stedy/Machine-Learning-with-R-datasets](https://github.com/stedy/Machine-Learning-with-R-datasets).

| Columna    | Descripción |
|------------|-------------|
| `age`      | Edad del asegurado |
| `sex`      | Sexo (female / male) |
| `bmi`      | Índice de masa corporal |
| `children` | Número de hijos a cargo |
| `smoker`   | Si fuma (yes / no) |
| `region`   | Región de residencia en EE. UU. |
| `charges`  | Coste médico anual facturado al seguro (USD); no es la prima |

No tiene valores que falten. Tiene una fila duplicada (filas 195 y 581), que se mantiene en el análisis porque sin un identificador de cliente no se puede saber si es un error.

## Notas

Proyecto desarrollado como ejercicio personal, con ayuda de Claude para resolver dudas de Python, SQL y estadística básica.

## Autor

Daniel Balicevic Celdrán — Máster en Ciencias Actuariales, UC3M
