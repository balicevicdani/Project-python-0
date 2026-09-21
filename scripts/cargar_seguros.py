"""
Carga el dataset publico "Medical Cost Personal" (costes de seguros medicos)
en una tabla nueva de la base de datos del proyecto.

Fuente original: stedy/Machine-Learning-with-R-datasets (GitHub), 1338 registros.
Columnas: age, sex, bmi, children, smoker, region, charges

Uso:
    python scripts/cargar_seguros.py
"""
import sqlite3
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "proyecto.db"
CSV_PATH = DATA_DIR / "seguros.csv"


def cargar_seguros():
    DATA_DIR.mkdir(exist_ok=True)

    df = pd.read_csv(CSV_PATH)

    conn = sqlite3.connect(DB_PATH)
    df.to_sql("seguros", conn, if_exists="replace", index=False)
    conn.close()

    print(f"Tabla 'seguros' cargada con {len(df)} filas en {DB_PATH}")


if __name__ == "__main__":
    cargar_seguros()
