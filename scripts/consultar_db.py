"""
Ejemplo de lectura de la base de datos con pandas.

Uso:
    python scripts/consultar_db.py
"""
import sqlite3
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "proyecto.db"

conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query("SELECT * FROM alumnos", conn)
conn.close()

print(df)
