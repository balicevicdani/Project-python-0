# Python Project — Intro Course (Master in Actuarial Sciences, UC3M)

Personal project for the intro programming course ("curso 0") of the Master in Actuarial Sciences at UC3M. It works through a complete practical case: setting up a reproducible environment, downloading a public dataset from GitHub, storing it in a SQLite database and running a first statistical analysis relevant to actuarial work.

## Project structure

The project is **modular**: generic, reusable functions live in `scripts/`, and the analysis itself is developed and documented in the notebooks inside `notebooks/`.

```
Proyecto python/
├── requirements.txt          # Environment dependencies (exact versions)
├── data/
│   ├── seguros.csv           # Dataset (downloaded from GitHub; local copy as fallback)
│   ├── proyecto.db           # SQLite database (generated, not tracked in git)
│   └── graficos.pdf          # All charts in one PDF (generated, not tracked in git)
├── scripts/
│   ├── __init__.py
│   └── funciones.py          # All reusable functions, organised in sections
└── notebooks/
    ├── analisis.ipynb        # Main analysis: imports the functions and runs everything
    └── practica.ipynb        # Quick check that the database/environment work
```

`scripts/funciones.py` only **defines** functions: importing it doesn't run anything or print anything. Every function receives its data, paths and table/column names as parameters, so it can be reused with other databases, variables or future projects. For a project of this size a single script with well-separated sections is enough; it can be split into several scripts as it grows.

| Section | Function | What it does |
|---|---|---|
| 1. Data | `descargar_csv(url, ruta_destino)` | Downloads a CSV from a URL (e.g. GitHub) and saves it locally |
| | `cargar_csv_en_db(ruta_csv, ruta_db, nombre_tabla)` | Stores a CSV as a table in a SQLite database |
| | `leer_tabla(ruta_db, nombre_tabla, columnas=None)` | Reads a table (or some columns) as a DataFrame |
| 2. Visualisation | `histograma(datos, ancho_banda=None, titulo=None, ...)` | Histogram of any numeric column; returns `(fig, ax)` |
| | `guardar_figuras_pdf(figuras, ruta_pdf)` | Saves a list of figures into a single PDF, one per page |
| 3. Statistics | `tabla_contingencia(df, var_filas, var_columnas)` | Contingency table of two categorical variables (`pd.crosstab`) |
| | `test_asociacion(df, var1, var2)` | Chi-square test of independence + phi coefficient for 2×2 tables |
| | `resumen_asociacion(resultado)` | One-row summary of a test, to compare several groups |

## How to reproduce it

Requirements: **Python 3.11 or newer** (developed and tested with Python 3.14).

```
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
```

Open the **project folder** in your editor (in VS Code: *File → Open Folder*), select the `.venv` kernel and run `notebooks/analisis.ipynb` top to bottom. It will:

1. Download the dataset from GitHub (or use the local copy if there is no connection) and load it into `data/proyecto.db`.
2. Explore the data.
3. Plot histograms of age, BMI and insurance cost.
4. Study the association between being a smoker and having no children (contingency table, chi-square test and phi coefficient), overall and by sex.
5. Save all charts into `data/graficos.pdf`.

## Dataset

Public "Medical Cost Personal Datasets" (1,338 insured individuals), from [stedy/Machine-Learning-with-R-datasets](https://github.com/stedy/Machine-Learning-with-R-datasets).

| Column     | Description                          |
|------------|--------------------------------------|
| `age`      | Age of the insured person            |
| `sex`      | Sex (male / female)                  |
| `bmi`      | Body mass index                      |
| `children` | Number of dependent children         |
| `smoker`   | Whether the person smokes (yes / no) |
| `region`   | Residential region in the US         |
| `charges`  | Medical insurance cost               |

## Notes

This project was developed as a personal exercise, with help from Claude to work through Python, SQL and basic statistics questions along the way.

## Author

Daniel Balicevic Celdrán — Master in Actuarial Sciences, UC3M
