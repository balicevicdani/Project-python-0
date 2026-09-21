"""
Estudia si existe correlacion entre ser fumador y no tener hijos,
usando los datos de la tabla 'seguros'. Permite filtrar por sexo
(por ejemplo, estudiar la correlacion solo entre las mujeres).

Uso:
    python scripts/correlacion_fumador_hijos.py
"""
import sqlite3
from pathlib import Path

import pandas as pd
from scipy.stats import chi2_contingency

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "proyecto.db"


def calcular_correlacion(db_path: Path = DB_PATH, sexo: str | None = None) -> dict:
    """
    Calcula la correlacion entre 'ser fumador' y 'no tener hijos'.

    Parametros:
        db_path: ruta a la base de datos.
        sexo: si se indica ("female" o "male"), filtra la tabla 'seguros'
              a ese sexo antes de calcular la correlacion. Si es None,
              usa todos los registros.

    Convierte ambas variables a binario:
        fumador   -> 1 si smoker == 'yes', 0 si 'no'
        sin_hijos -> 1 si children == 0, 0 si tiene 1 o mas

    Devuelve un diccionario con:
        - n: numero de registros usados
        - tabla_contingencia: cruce de frecuencias entre ambas variables
        - correlacion: coeficiente de correlacion de Pearson (equivalente
          al coeficiente phi, al ser ambas variables binarias 0/1)
        - chi2, p_valor: resultado del test de independencia chi-cuadrado
    """
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT sex, smoker, children FROM seguros", conn)
    conn.close()

    if sexo is not None:
        df = df[df["sex"] == sexo]

    df["fumador"] = (df["smoker"] == "yes").astype(int)
    df["sin_hijos"] = (df["children"] == 0).astype(int)

    tabla_contingencia = pd.crosstab(df["fumador"], df["sin_hijos"])

    correlacion = df["fumador"].corr(df["sin_hijos"])

    chi2, p_valor, _, _ = chi2_contingency(tabla_contingencia)

    return {
        "n": len(df),
        "tabla_contingencia": tabla_contingencia,
        "correlacion": correlacion,
        "chi2": chi2,
        "p_valor": p_valor,
    }


def imprimir_resultado(titulo: str, resultado: dict):
    print(f"--- {titulo} (n = {resultado['n']}) ---")
    print("Tabla de contingencia (filas=fumador, columnas=sin_hijos):")
    print(resultado["tabla_contingencia"])
    print()
    print(f"Coeficiente de correlacion (fumador vs sin_hijos): {resultado['correlacion']:.4f}")
    print(f"Test chi-cuadrado: chi2 = {resultado['chi2']:.4f}, p-valor = {resultado['p_valor']:.4f}")

    if resultado["p_valor"] < 0.05:
        print("=> Existe una asociacion estadisticamente significativa (p < 0.05).")
    else:
        print("=> No hay evidencia suficiente de asociacion (p >= 0.05).")
    print()


def main():
    # Con todos los registros
    imprimir_resultado("Todos los registros", calcular_correlacion())

    # Solo mujeres
    imprimir_resultado("Solo mujeres", calcular_correlacion(sexo="female"))

    # Solo hombres (para comparar)
    imprimir_resultado("Solo hombres", calcular_correlacion(sexo="male"))


if __name__ == "__main__":
    main()
