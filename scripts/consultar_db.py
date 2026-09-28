"""
Funciones de consulta genericas sobre la base de datos del proyecto.

Este script NO ejecuta nada al importarlo: solo define funciones.
"""
import sqlite3
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "proyecto.db"


def consultar_tabla(tabla: str = "alumnos", db_path: Path = DB_PATH) -> pd.DataFrame:
    """
    Lee una tabla completa de la base de datos y la devuelve como DataFrame.

    Parametros:
        tabla: nombre de la tabla a consultar. Por defecto, "alumnos".
        db_path: ruta a la base de datos. Por defecto, data/proyecto.db.

    Devuelve:
        un DataFrame de pandas con todas las filas de la tabla.
    """
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(f"SELECT * FROM {tabla}", conn)
    conn.close()
    return df
