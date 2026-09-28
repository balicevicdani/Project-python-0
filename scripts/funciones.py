"""
Funciones reutilizables del proyecto.

Este script SOLO define funciones: no ejecuta nada ni muestra resultados al
importarlo. Todas reciben sus datos y rutas como parametros, de modo que
sirven para cualquier base de datos, tabla o variable, no solo para el
dataset de seguros de este proyecto.

Los resultados (tablas, graficos, estadisticos) se generan y se comentan
en los notebooks de la carpeta notebooks/.

Secciones:
    1. Obtencion y carga de datos
    2. Visualizacion
    3. Estadistica: asociacion entre dos variables categoricas
"""
import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
from scipy.stats import chi2_contingency


# =============================================================================
# 1. OBTENCION Y CARGA DE DATOS
# =============================================================================

def descargar_csv(url: str, ruta_destino: str | Path) -> Path:
    """
    Descarga un fichero CSV desde una URL (por ejemplo, un fichero "raw" de
    GitHub) y lo guarda en local.

    Parametros:
        url: direccion web del CSV.
        ruta_destino: ruta donde guardar el fichero (se crean las carpetas
            que falten).

    Devuelve:
        la ruta del fichero guardado.
    """
    ruta_destino = Path(ruta_destino)
    ruta_destino.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(url)          # pandas lee directamente desde una URL
    df.to_csv(ruta_destino, index=False)
    return ruta_destino


def cargar_csv_en_db(ruta_csv: str | Path, ruta_db: str | Path, nombre_tabla: str,
                     reemplazar: bool = True) -> int:
    """
    Guarda el contenido de un CSV como tabla de una base de datos SQLite.
    Si la base de datos no existe, SQLite la crea.

    Parametros:
        ruta_csv: fichero CSV de origen.
        ruta_db: fichero .db de destino.
        nombre_tabla: nombre que tendra la tabla dentro de la base de datos.
        reemplazar: si True, sustituye la tabla si ya existia; si False,
            anade las filas al final.

    Devuelve:
        el numero de filas cargadas.
    """
    ruta_db = Path(ruta_db)
    ruta_db.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(ruta_csv)
    with sqlite3.connect(ruta_db) as conn:
        df.to_sql(nombre_tabla, conn, if_exists="replace" if reemplazar else "append",
                  index=False)
    return len(df)


def leer_tabla(ruta_db: str | Path, nombre_tabla: str,
               columnas: list[str] | None = None) -> pd.DataFrame:
    """
    Lee una tabla de una base de datos SQLite y la devuelve como DataFrame.

    Parametros:
        ruta_db: fichero .db.
        nombre_tabla: tabla a leer.
        columnas: lista de columnas a leer. Si es None, se leen todas.

    Devuelve:
        un DataFrame de pandas.
    """
    ruta_db = Path(ruta_db)
    if not ruta_db.exists():
        raise FileNotFoundError(f"No existe la base de datos {ruta_db}")

    with sqlite3.connect(ruta_db) as conn:
        tablas = pd.read_sql_query(
            "SELECT name FROM sqlite_master WHERE type = 'table'", conn
        )["name"].tolist()
        if nombre_tabla not in tablas:
            raise ValueError(f"La tabla '{nombre_tabla}' no existe. Tablas disponibles: {tablas}")

        cols = "*" if columnas is None else ", ".join(f'"{c}"' for c in columnas)
        return pd.read_sql_query(f'SELECT {cols} FROM "{nombre_tabla}"', conn)


# =============================================================================
# 2. VISUALIZACION
# =============================================================================

def histograma(datos: pd.Series, ancho_banda: float | None = None,
               titulo: str | None = None, etiqueta_x: str | None = None,
               color: str = "#4C72B0"):
    """
    Dibuja el histograma de una variable numerica.

    Parametros:
        datos: la variable a representar (una columna de un DataFrame).
        ancho_banda: anchura de cada barra. Si es None, matplotlib elige
            automaticamente el numero de barras.
        titulo: titulo del grafico. Si es None, se genera uno automatico.
        etiqueta_x: texto del eje X. Si es None, se usa el nombre de la columna.
        color: color de las barras.

    Devuelve:
        (fig, ax): la figura y los ejes de matplotlib. La funcion NO muestra
        ni guarda el grafico; eso se decide en el notebook.
    """
    datos = datos.dropna()
    nombre = datos.name or "variable"

    if ancho_banda is None:
        bins = "auto"
    else:
        # Bordes de las barras alineados con multiplos del ancho de banda
        inicio = np.floor(datos.min() / ancho_banda) * ancho_banda
        fin = np.floor(datos.max() / ancho_banda) * ancho_banda + ancho_banda
        bins = np.arange(inicio, fin + ancho_banda, ancho_banda)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(datos, bins=bins, edgecolor="white", color=color)
    ax.set_title(titulo or f"Distribucion de {nombre}")
    ax.set_xlabel(etiqueta_x or nombre)
    ax.set_ylabel("Frecuencia")
    if ancho_banda is not None and len(bins) <= 25:
        ax.set_xticks(bins)
    fig.tight_layout()
    return fig, ax


def guardar_figuras_pdf(figuras: list, ruta_pdf: str | Path) -> Path:
    """
    Guarda una lista de figuras de matplotlib en un unico PDF,
    una figura por pagina.

    Parametros:
        figuras: lista de figuras (por ejemplo, las devueltas por histograma()).
        ruta_pdf: ruta del PDF de salida (se crean las carpetas que falten).

    Devuelve:
        la ruta del PDF generado.
    """
    ruta_pdf = Path(ruta_pdf)
    ruta_pdf.parent.mkdir(parents=True, exist_ok=True)
    with PdfPages(ruta_pdf) as pdf:
        for fig in figuras:
            pdf.savefig(fig)
    return ruta_pdf


# =============================================================================
# 3. ESTADISTICA: ASOCIACION ENTRE DOS VARIABLES CATEGORICAS
# =============================================================================

def tabla_contingencia(df: pd.DataFrame, var_filas: str, var_columnas: str) -> pd.DataFrame:
    """
    Tabla de contingencia (frecuencias cruzadas) de dos variables categoricas:
    cuenta cuantas observaciones hay en cada combinacion de categorias.

    Parametros:
        df: DataFrame con los datos.
        var_filas: variable que ira en las filas.
        var_columnas: variable que ira en las columnas.

    Devuelve:
        un DataFrame con los recuentos (pd.crosstab).
    """
    return pd.crosstab(df[var_filas], df[var_columnas])


def test_asociacion(df: pd.DataFrame, var1: str, var2: str,
                    correccion_yates: bool = True) -> dict:
    """
    Estudia si dos variables categoricas estan asociadas.

    1) Construye la tabla de contingencia con tabla_contingencia().
    2) Aplica el test chi-cuadrado de independencia sobre esa tabla
       (H0: las variables son independientes).
    3) Si ambas variables son binarias (tabla 2x2), calcula ademas el
       coeficiente phi, que es la correlacion de Pearson entre dos
       variables 0/1: phi = (a*d - b*c) / sqrt((a+b)(c+d)(a+c)(b+d)).

    Parametros:
        df: DataFrame con los datos.
        var1, var2: nombres de las dos columnas a relacionar.
        correccion_yates: aplicar la correccion de continuidad de Yates en
            tablas 2x2 (hace el test algo mas conservador).

    Devuelve un diccionario con:
        n, tabla (contingencia), chi2, p_valor, grados_libertad,
        esperadas (frecuencias esperadas si hubiera independencia)
        y phi (None si la tabla no es 2x2).
    """
    tabla = tabla_contingencia(df, var1, var2)
    chi2, p_valor, gl, esperadas = chi2_contingency(tabla, correction=correccion_yates)

    phi = None
    if tabla.shape == (2, 2):
        (a, b), (c, d) = tabla.to_numpy()
        denominador = np.sqrt((a + b) * (c + d) * (a + c) * (b + d))
        phi = float((a * d - b * c) / denominador) if denominador > 0 else np.nan

    return {
        "n": int(tabla.to_numpy().sum()),
        "tabla": tabla,
        "chi2": float(chi2),
        "p_valor": float(p_valor),
        "grados_libertad": int(gl),
        "esperadas": pd.DataFrame(esperadas, index=tabla.index, columns=tabla.columns),
        "phi": phi,
    }


def resumen_asociacion(resultado: dict, alfa: float = 0.05) -> pd.Series:
    """
    Resume en una fila los numeros clave devueltos por test_asociacion(),
    para poder comparar varios casos en una misma tabla desde el notebook.

    Parametros:
        resultado: diccionario devuelto por test_asociacion().
        alfa: nivel de significacion para decidir si hay asociacion.
    """
    return pd.Series({
        "n": resultado["n"],
        "phi": resultado["phi"],
        "chi2": resultado["chi2"],
        "p_valor": resultado["p_valor"],
        "asociacion_significativa": resultado["p_valor"] < alfa,
    })
