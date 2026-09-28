"""
Funciones para cargar el dataset publico "Medical Cost Personal"
(costes de seguros medicos) en una tabla de la base de datos del proyecto.

Fuente original: stedy/Machine-Learning-with-R-datasets (GitHub), 1338 registros.
Columnas: age, sex, bmi, children, smoker, region, charges

Este script NO ejecuta nada al importarlo: solo define funciones.
"""
import sqlite3
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "proyecto.db"
CSV_PATH = DATA_DIR / "seguros.csv"


def cargar_seguros(csv_path: Path = CSV_PATH, db_path: Path = DB_PATH, tabla: str = "seguros") -> int:
    """
    Carga un CSV con la misma estructura que seguros.csv en una tabla
    de la base de datos indicada.

    Parametros:
        csv_path: ruta al CSV de origen. Por defecto, data/seguros.csv.
        db_path: ruta a la base de datos destino. Por defecto, data/proyecto.db.
        tabla: nombre de la tabla a crear/reemplazar. Por defecto, "seguros".

    Devuelve:
        numero de filas cargadas.
    """
    csv_path = Path(csv_path)
    db_path = Path(db_path)
    db_path.parent.mkdir(exist_ok=True, parents=True)

    df = pd.read_csv(csv_path)

    conn = sqlite3.connect(db_path)
    df.to_sql(tabla, conn, if_exists="replace", index=False)
    conn.close()

    print(f"Tabla '{tabla}' cargada con {len(df)} filas en {db_path}")
    return len(df)
