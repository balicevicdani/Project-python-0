"""
Funciones reutilizables del proyecto.

Este script SOLO define funciones: no ejecuta nada ni muestra resultados al
importarlo. Todas reciben sus datos, rutas y nombres de tablas o columnas como
parámetros, de modo que sirven para cualquier base de datos, tabla o variable,
no solo para el dataset de seguros de este proyecto.

Los resultados (tablas, gráficos, estadísticos) se generan y se comentan en los
notebooks de la carpeta notebooks/.

Secciones:
    1. Obtención y carga de datos
    2. Consultas SQL
    3. Visualización
    4. Estadística: asociación entre dos variables categóricas
"""
import sqlite3
import urllib.request
from contextlib import closing
from io import BytesIO
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
from scipy.stats import chi2_contingency


# =============================================================================
# 1. OBTENCIÓN Y CARGA DE DATOS
# =============================================================================

def descargar_csv(url: str, ruta_destino: str | Path, timeout: float = 15) -> Path:
    """
    Descarga un fichero CSV desde una URL (por ejemplo, un fichero "raw" de
    GitHub) y guarda una copia EXACTA en local (los mismos bytes que en origen,
    sin reformatear los números ni los saltos de línea).

    Antes de guardarlo comprueba que el contenido se puede leer como CSV, para
    no sustituir una copia local buena por una página de error.

    Parámetros:
        url: dirección web del CSV.
        ruta_destino: ruta donde guardar el fichero (se crean las carpetas
            que falten).
        timeout: segundos máximos de espera antes de abandonar la descarga.

    Devuelve:
        la ruta del fichero guardado.
    """
    ruta_destino = Path(ruta_destino)
    with urllib.request.urlopen(url, timeout=timeout) as respuesta:
        contenido = respuesta.read()

    if pd.read_csv(BytesIO(contenido)).empty:   # falla si no es un CSV válido
        raise ValueError(f"El fichero descargado de {url} no contiene datos")

    ruta_destino.parent.mkdir(parents=True, exist_ok=True)
    ruta_destino.write_bytes(contenido)
    return ruta_destino


def _conectar(ruta_db: str | Path):
    """Abre la base de datos y garantiza que la conexión se CIERRA al salir del with.
    (El 'with' de sqlite3 por sí solo hace commit, pero no cierra la conexión.)"""
    return closing(sqlite3.connect(ruta_db))


def _nombre_sql(nombre: str) -> str:
    """Escribe un nombre de tabla o columna entre comillas dobles, escapando las
    comillas que pudiera contener, para usarlo con seguridad dentro de una consulta."""
    return '"' + str(nombre).replace('"', '""') + '"'


def cargar_csv_en_db(ruta_csv: str | Path, ruta_db: str | Path, nombre_tabla: str,
                     reemplazar: bool = True) -> int:
    """
    Guarda el contenido de un CSV como tabla de una base de datos SQLite.
    Si la base de datos no existe, SQLite la crea.

    Parámetros:
        ruta_csv: fichero CSV de origen.
        ruta_db: fichero .db de destino.
        nombre_tabla: nombre que tendrá la tabla dentro de la base de datos.
        reemplazar: si True, sustituye la tabla si ya existía; si False,
            añade las filas al final.

    Devuelve:
        el número de filas cargadas.
    """
    ruta_db = Path(ruta_db)
    ruta_db.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(ruta_csv)
    with _conectar(ruta_db) as conn, conn:          # el segundo 'conn' hace commit
        df.to_sql(nombre_tabla, conn, if_exists="replace" if reemplazar else "append",
                  index=False)
    return len(df)


def listar_tablas(ruta_db: str | Path) -> list[str]:
    """Devuelve los nombres de las tablas que hay en una base de datos SQLite."""
    ruta_db = Path(ruta_db)
    if not ruta_db.exists():
        raise FileNotFoundError(f"No existe la base de datos {ruta_db}")
    with _conectar(ruta_db) as conn:
        filas = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    return [nombre for (nombre,) in filas]


def leer_tabla(ruta_db: str | Path, nombre_tabla: str,
               columnas: list[str] | None = None) -> pd.DataFrame:
    """
    Lee una tabla de una base de datos SQLite y la devuelve como DataFrame.

    Parámetros:
        ruta_db: fichero .db.
        nombre_tabla: tabla a leer.
        columnas: lista de columnas a leer. Si es None, se leen todas.

    Devuelve:
        un DataFrame de pandas.
    """
    tablas = listar_tablas(ruta_db)
    if nombre_tabla not in tablas:
        raise ValueError(f"La tabla '{nombre_tabla}' no existe. Tablas disponibles: {tablas}")

    cols = "*" if columnas is None else ", ".join(_nombre_sql(c) for c in columnas)
    return consultar(ruta_db, f"SELECT {cols} FROM {_nombre_sql(nombre_tabla)}")


# =============================================================================
# 2. CONSULTAS SQL
# =============================================================================

def consultar(ruta_db: str | Path, sql: str, parametros: tuple | dict = ()) -> pd.DataFrame:
    """
    Ejecuta cualquier consulta SQL (SELECT) sobre la base de datos y devuelve
    el resultado como DataFrame.

    Parámetros:
        ruta_db: fichero .db.
        sql: texto de la consulta. Los VALORES variables se escriben como "?"
            y se pasan en 'parametros' (nunca pegados en el texto de la consulta).
        parametros: valores que sustituyen a los "?" de la consulta.

    Ejemplo:
        consultar(ruta_db, "SELECT * FROM seguros WHERE age > ?", (60,))
    """
    ruta_db = Path(ruta_db)
    if not ruta_db.exists():
        raise FileNotFoundError(f"No existe la base de datos {ruta_db}")
    with _conectar(ruta_db) as conn:
        return pd.read_sql_query(sql, conn, params=parametros)


def media_por_grupo(ruta_db: str | Path, nombre_tabla: str, var_numerica: str,
                    var_grupo: str) -> pd.DataFrame:
    """
    Calcula con SQL (GROUP BY) el número de observaciones, la media, el mínimo
    y el máximo de una variable numérica para cada categoría de otra variable.

    Parámetros:
        ruta_db: fichero .db.
        nombre_tabla: tabla sobre la que se calcula.
        var_numerica: columna numérica a resumir (por ejemplo, el coste).
        var_grupo: columna categórica que define los grupos.

    Devuelve:
        un DataFrame con una fila por grupo, ordenado de mayor a menor media.
    """
    num, grupo, tabla = _nombre_sql(var_numerica), _nombre_sql(var_grupo), _nombre_sql(nombre_tabla)
    sql = f"""
        SELECT {grupo}       AS grupo,
               COUNT(*)      AS n,
               AVG({num})    AS media,
               MIN({num})    AS minimo,
               MAX({num})    AS maximo
        FROM {tabla}
        GROUP BY {grupo}
        ORDER BY media DESC
    """
    return consultar(ruta_db, sql).set_index("grupo")


# =============================================================================
# 3. VISUALIZACIÓN
# =============================================================================

def histograma(datos: pd.Series, ancho_banda: float | None = None,
               titulo: str | None = None, etiqueta_x: str | None = None,
               color: str = "#4C72B0"):
    """
    Dibuja el histograma de una variable numérica.

    Parámetros:
        datos: la variable a representar (una columna de un DataFrame).
        ancho_banda: anchura de cada barra. Si es None, matplotlib elige
            automáticamente el número de barras.
        titulo: título del gráfico. Si es None, se genera uno automático.
        etiqueta_x: texto del eje X. Si es None, se usa el nombre de la columna.
        color: color de las barras.

    Devuelve:
        (fig, ax): la figura y los ejes de matplotlib. La función NO muestra
        ni guarda el gráfico; eso se decide en el notebook.
    """
    datos = pd.to_numeric(datos, errors="raise").dropna()
    if datos.empty:
        raise ValueError("No hay datos numéricos que representar")
    if ancho_banda is not None and ancho_banda <= 0:
        raise ValueError("ancho_banda tiene que ser un número positivo")
    nombre = datos.name or "variable"

    if ancho_banda is None:
        bins = "auto"
    else:
        # Bordes alineados con múltiplos del ancho de banda. Se calcula primero
        # el NÚMERO de barras (entero) para evitar errores de redondeo de np.arange.
        inicio = np.floor(datos.min() / ancho_banda) * ancho_banda
        n_barras = int(np.floor((datos.max() - inicio) / ancho_banda)) + 1
        bins = inicio + ancho_banda * np.arange(n_barras + 1)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(datos, bins=bins, edgecolor="white", color=color)
    ax.set_title(titulo or f"Distribución de {nombre}")
    ax.set_xlabel(etiqueta_x or nombre)
    ax.set_ylabel("Frecuencia")
    if ancho_banda is not None and len(bins) <= 25:
        ax.set_xticks(bins)
    fig.tight_layout()
    return fig, ax


def boxplot_por_grupo(df: pd.DataFrame, var_numerica: str, var_grupo: str,
                      titulo: str | None = None, etiqueta_y: str | None = None):
    """
    Diagrama de cajas de una variable numérica para cada categoría de otra
    variable: permite comparar de un vistazo la distribución entre grupos.

    Devuelve:
        (fig, ax), igual que histograma().
    """
    grupos = sorted(df[var_grupo].dropna().unique())
    valores = [df.loc[df[var_grupo] == g, var_numerica].dropna() for g in grupos]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.boxplot(valores, tick_labels=[str(g) for g in grupos])
    ax.set_title(titulo or f"{var_numerica} según {var_grupo}")
    ax.set_xlabel(var_grupo)
    ax.set_ylabel(etiqueta_y or var_numerica)
    fig.tight_layout()
    return fig, ax


def guardar_figuras_pdf(figuras: list, ruta_pdf: str | Path) -> Path:
    """
    Guarda una lista de figuras de matplotlib en un único PDF,
    una figura por página.

    Parámetros:
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
# 4. ESTADÍSTICA: ASOCIACIÓN ENTRE DOS VARIABLES CATEGÓRICAS
# =============================================================================

def tabla_contingencia(df: pd.DataFrame, var_filas: str, var_columnas: str) -> pd.DataFrame:
    """
    Tabla de contingencia (frecuencias cruzadas) de dos variables categóricas:
    cuenta cuántas observaciones hay en cada combinación de categorías.

    Parámetros:
        df: DataFrame con los datos.
        var_filas: variable que irá en las filas.
        var_columnas: variable que irá en las columnas.

    Devuelve:
        un DataFrame con los recuentos (pd.crosstab).
    """
    return pd.crosstab(df[var_filas], df[var_columnas])


def test_asociacion(df: pd.DataFrame, var1: str, var2: str,
                    correccion_yates: bool = False) -> dict:
    """
    Estudia si dos variables categóricas están asociadas.

    1) Construye la tabla de contingencia con tabla_contingencia().
    2) Aplica el test chi-cuadrado de independencia sobre esa tabla
       (H0: las variables son independientes).
    3) Mide la FUERZA de la asociación:
       - V de Cramér, para tablas de cualquier tamaño (de 0 a 1).
       - Coeficiente phi, solo si ambas variables son binarias (tabla 2x2). Es la
         correlación de Pearson entre dos variables 0/1 y tiene signo (de -1 a 1):
         phi = (a*d - b*c) / sqrt((a+b)(c+d)(a+c)(b+d)).
       Sin corrección de Yates se cumple chi2 = n * phi^2 (y = n * V^2 en 2x2).

    Parámetros:
        df: DataFrame con los datos.
        var1, var2: nombres de las dos columnas a relacionar.
        correccion_yates: aplicar la corrección de continuidad de Yates en tablas
            2x2. Hace el test más conservador, pero entonces chi2 ya no es n*phi^2.
            Solo es relevante con muestras pequeñas; por defecto no se aplica.

    Devuelve un diccionario con:
        n, tabla (contingencia), chi2, p_valor, grados_libertad,
        esperadas (frecuencias esperadas si hubiera independencia),
        esperada_min (el test solo es fiable si todas son >= 5),
        v_cramer y phi (None si la tabla no es 2x2).
    """
    tabla = tabla_contingencia(df, var1, var2)
    if min(tabla.shape) < 2:
        raise ValueError(
            f"Cada variable necesita al menos 2 categorías con datos; la tabla es {tabla.shape[0]}x{tabla.shape[1]}"
        )

    chi2, p_valor, gl, esperadas = chi2_contingency(tabla, correction=correccion_yates)
    n = int(tabla.to_numpy().sum())

    chi2_sin_correccion = chi2_contingency(tabla, correction=False)[0]
    v_cramer = float(np.sqrt(chi2_sin_correccion / (n * (min(tabla.shape) - 1))))

    phi = None
    if tabla.shape == (2, 2):
        (a, b), (c, d) = tabla.to_numpy().astype(float)
        denominador = np.sqrt((a + b) * (c + d) * (a + c) * (b + d))
        phi = float((a * d - b * c) / denominador)

    return {
        "n": n,
        "tabla": tabla,
        "chi2": float(chi2),
        "p_valor": float(p_valor),
        "grados_libertad": int(gl),
        "esperadas": pd.DataFrame(esperadas, index=tabla.index, columns=tabla.columns),
        "esperada_min": float(esperadas.min()),
        "v_cramer": v_cramer,
        "phi": phi,
    }


def resumen_asociacion(resultado: dict, alfa: float = 0.05) -> pd.Series:
    """
    Resume en una fila los números clave devueltos por test_asociacion(),
    para poder comparar varios casos en una misma tabla desde el notebook.

    Parámetros:
        resultado: diccionario devuelto por test_asociacion().
        alfa: nivel de significación para decidir si hay asociación.
    """
    return pd.Series({
        "n": resultado["n"],
        "phi": resultado["phi"],
        "v_cramer": resultado["v_cramer"],
        "chi2": resultado["chi2"],
        "p_valor": resultado["p_valor"],
        "esperada_min": resultado["esperada_min"],
        "asociacion_significativa": resultado["p_valor"] < alfa,
    })
