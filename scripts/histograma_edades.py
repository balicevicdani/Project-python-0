"""
Histograma de la edad de los asegurados (tabla 'seguros'), con bins de ancho 5.

Uso:
    python scripts/histograma_edades.py
"""
import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "proyecto.db"
OUT_PATH = BASE_DIR / "data" / "histograma_edades.png"

ANCHO_BANDA = 5


def main():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT age FROM seguros", conn)
    conn.close()

    edad_min = (df["age"].min() // ANCHO_BANDA) * ANCHO_BANDA
    edad_max = ((df["age"].max() // ANCHO_BANDA) + 1) * ANCHO_BANDA
    bins = np.arange(edad_min, edad_max + ANCHO_BANDA, ANCHO_BANDA)

    plt.figure(figsize=(8, 5))
    plt.hist(df["age"], bins=bins, edgecolor="white", color="#4C72B0")
    plt.title(f"Distribucion de edades (ancho de banda = {ANCHO_BANDA})")
    plt.xlabel("Edad")
    plt.ylabel("Frecuencia")
    plt.xticks(bins)
    plt.tight_layout()

    plt.savefig(OUT_PATH, dpi=150)
    print(f"Histograma guardado en: {OUT_PATH}")

    plt.show()


if __name__ == "__main__":
    main()
