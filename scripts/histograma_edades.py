"""
Funciones para generar histogramas a partir de una columna numerica
de una tabla de la base de datos del proyecto.

Este script NO ejecuta nada al importarlo: solo define funciones.
"""
import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "proyecto.db"


def histograma(
    columna: str,
    tabla: str = "seguros",
    db_path: Path = DB_PATH,
    ancho_banda: float = 5,
    titulo: str | None = None,
):
    """
    Genera un histograma de una columna numerica de una tabla.

    Parametros:
        columna: nombre de la columna a graficar (ej. "age", "bmi").
        tabla: nombre de la tabla de donde leer los datos.
        db_path: ruta a la base de datos.
        ancho_banda: ancho de cada barra del histograma.
        titulo: titulo del grafico. Si no se indica, se genera uno automatico.

    Devuelve:
        (fig, ax): la figura y los ejes de matplotlib, para que el notebook
        decida si mostrarlos (fig.show / plt.show), guardarlos
        (fig.savefig(...)) o seguir modificandolos.
    """
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(f"SELECT {columna} FROM {tabla}", conn)
    conn.close()

    valor_min = (df[columna].min() // ancho_banda) * ancho_banda
    valor_max = ((df[columna].max() // ancho_banda) + 1) * ancho_banda
    bins = np.arange(valor_min, valor_max + ancho_banda, ancho_banda)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(df[columna], bins=bins, edgecolor="white", color="#4C72B0")
    ax.set_title(titulo or f"Distribucion de {columna} (ancho de banda = {ancho_banda})")
    ax.set_xlabel(columna)
    ax.set_ylabel("Frecuencia")
    ax.set_xticks(bins)
    fig.tight_layout()

    return fig, ax
