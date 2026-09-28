"""
Funciones de inicializacion de la base de datos del proyecto.

Este script NO ejecuta nada al importarlo: solo define funciones.
Para usarlas, importalas desde un notebook, por ejemplo:

    from scripts.init_db import crear_base_de_datos
    crear_base_de_datos()
"""
import sqlite3
from pathlib import Path

# Carpeta y fichero de la base de datos por defecto
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "proyecto.db"


def crear_base_de_datos(db_path: Path = DB_PATH):
    """
    Crea (si no existe) la tabla 'alumnos' en la base de datos indicada,
    con datos de ejemplo.

    Parametros:
        db_path: ruta al fichero .db donde crear la tabla.
                 Por defecto, data/proyecto.db.
    """
    db_path = Path(db_path)
    db_path.parent.mkdir(exist_ok=True, parents=True)

    conn = sqlite3.connect(db_path)
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
    print(f"Base de datos creada/actualizada en: {db_path}")
