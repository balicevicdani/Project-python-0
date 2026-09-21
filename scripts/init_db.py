"""
Script de inicializacion de la base de datos del proyecto.

Uso:
    python scripts/init_db.py

Crea (si no existe) el fichero data/proyecto.db con una tabla de ejemplo,
para que puedas empezar a practicar consultas SQL desde Python.
"""
import sqlite3
from pathlib import Path

# Carpeta y fichero de la base de datos
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "proyecto.db"


def crear_base_de_datos():
    DATA_DIR.mkdir(exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alumnos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            asignatura TEXT,
            nota REAL
        )
    """)

    # Datos de ejemplo, solo se insertan si la tabla esta vacia
    cursor.execute("SELECT COUNT(*) FROM alumnos")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO alumnos (nombre, asignatura, nota) VALUES (?, ?, ?)",
            [
                ("Daniel", "Estadistica Actuarial", 8.5),
                ("Laura", "Matematica Financiera", 9.1),
                ("Marcos", "Probabilidad", 7.3),
            ],
        )

    conn.commit()
    conn.close()
    print(f"Base de datos creada/actualizada en: {DB_PATH}")


if __name__ == "__main__":
    crear_base_de_datos()
