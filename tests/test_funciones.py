"""
Pruebas automáticas de scripts/funciones.py.

Usan solo la librería estándar (unittest), así que no hace falta instalar nada más.
Desde la carpeta raíz del proyecto:

    python -m unittest discover -s tests -v
"""
import functools
import http.server
import tempfile
import threading
import unittest
from pathlib import Path

import matplotlib
matplotlib.use("Agg")                     # dibujar sin abrir ventanas
import matplotlib.pyplot as plt
import pandas as pd

from scripts.funciones import (
    boxplot_por_grupo, cargar_csv_en_db, consultar, descargar_csv, guardar_figuras_pdf,
    histograma, leer_tabla, listar_tablas, media_por_grupo, resumen_asociacion,
    test_asociacion,
)

CSV_EJEMPLO = (
    "grupo,fuma,hijos,coste\n"
    "a,1,0,10.0\n"
    "a,1,1,20\n"
    "b,0,0,30.5\n"
    "b,0,1,40\n"
    "b,1,0,50\n"
)


class TestDatosYSQL(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.csv = self.dir / "ejemplo.csv"
        self.csv.write_text(CSV_EJEMPLO, encoding="utf-8")
        self.db = self.dir / "prueba.db"

    def tearDown(self):
        self.tmp.cleanup()                 # en Windows falla si queda una conexión abierta

    def test_cargar_y_leer(self):
        self.assertEqual(cargar_csv_en_db(self.csv, self.db, "t"), 5)
        self.assertEqual(listar_tablas(self.db), ["t"])
        self.assertEqual(leer_tabla(self.db, "t").shape, (5, 4))
        self.assertEqual(list(leer_tabla(self.db, "t", ["coste"]).columns), ["coste"])

    def test_reemplazar_y_anadir(self):
        cargar_csv_en_db(self.csv, self.db, "t")
        cargar_csv_en_db(self.csv, self.db, "t")
        self.assertEqual(len(leer_tabla(self.db, "t")), 5)
        cargar_csv_en_db(self.csv, self.db, "t", reemplazar=False)
        self.assertEqual(len(leer_tabla(self.db, "t")), 10)

    def test_errores_claros(self):
        with self.assertRaises(FileNotFoundError):
            leer_tabla(self.dir / "no_existe.db", "t")
        cargar_csv_en_db(self.csv, self.db, "t")
        with self.assertRaises(ValueError):
            leer_tabla(self.db, "otra")

    def test_consultas_sql(self):
        cargar_csv_en_db(self.csv, self.db, "t")
        self.assertEqual(len(consultar(self.db, "SELECT * FROM t WHERE coste > ?", (25,))), 3)
        medias = media_por_grupo(self.db, "t", "coste", "grupo")
        self.assertAlmostEqual(medias.loc["a", "media"], 15.0)
        self.assertEqual(medias.loc["b", "n"], 3)
        self.assertEqual(list(medias.index), ["b", "a"])      # ordenado de mayor a menor media


class _ServidorSilencioso(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):         # no llenar la salida de las pruebas con el log del servidor
        pass


class TestDescarga(unittest.TestCase):
    """Levanta un pequeño servidor web local para probar la descarga sin depender de internet."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        (self.dir / "origen.csv").write_bytes(CSV_EJEMPLO.encode("utf-8"))
        (self.dir / "vacio.csv").write_bytes(b"a,b\n")
        manejador = functools.partial(_ServidorSilencioso, directory=str(self.dir))
        self.servidor = http.server.ThreadingHTTPServer(("127.0.0.1", 0), manejador)
        threading.Thread(target=self.servidor.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.servidor.server_address[1]}"

    def tearDown(self):
        self.servidor.shutdown()
        self.servidor.server_close()
        self.tmp.cleanup()

    def test_copia_exacta(self):
        destino = descargar_csv(f"{self.url}/origen.csv", self.dir / "sub" / "copia.csv")
        # mismos bytes: "10.0" y "20" no se reescriben como "10.0" y "20.0"
        self.assertEqual(destino.read_bytes(), CSV_EJEMPLO.encode("utf-8"))

    def test_no_sobrescribe_si_falla(self):
        destino = self.dir / "local.csv"
        destino.write_text("copia buena", encoding="utf-8")
        with self.assertRaises(Exception):
            descargar_csv(f"{self.url}/no_existe.csv", destino)
        with self.assertRaises(ValueError):
            descargar_csv(f"{self.url}/vacio.csv", destino)
        self.assertEqual(destino.read_text(encoding="utf-8"), "copia buena")


class TestGraficos(unittest.TestCase):
    def tearDown(self):
        plt.close("all")

    def test_bordes_histograma(self):
        _, ax = histograma(pd.Series([18, 19, 64], name="edad"), ancho_banda=5)
        bordes = [p.get_x() for p in ax.patches] + [ax.patches[-1].get_x() + ax.patches[-1].get_width()]
        self.assertEqual(bordes[0], 15)
        self.assertEqual(bordes[-1], 65)
        self.assertEqual(sum(p.get_height() for p in ax.patches), 3)   # no se pierde ningún dato

    def test_histograma_valida_entrada(self):
        with self.assertRaises(ValueError):
            histograma(pd.Series([], dtype=float))
        with self.assertRaises(ValueError):
            histograma(pd.Series([1, 2, 3]), ancho_banda=0)

    def test_pdf(self):
        figuras = [histograma(pd.Series([1, 2, 3], name="x"))[0],
                   boxplot_por_grupo(pd.DataFrame({"v": [1, 2, 3, 4], "g": ["a", "a", "b", "b"]}), "v", "g")[0]]
        with tempfile.TemporaryDirectory() as tmp:
            ruta = guardar_figuras_pdf(figuras, Path(tmp) / "g.pdf")
            self.assertTrue(ruta.read_bytes().startswith(b"%PDF"))


class TestAsociacion(unittest.TestCase):
    def test_phi_y_chi2(self):
        df = pd.DataFrame({"x": [0] * 30 + [1] * 30, "y": [0] * 25 + [1] * 5 + [0] * 10 + [1] * 20})
        r = test_asociacion(df, "x", "y")
        self.assertAlmostEqual(r["phi"], df["x"].corr(df["y"]))           # phi = Pearson
        self.assertAlmostEqual(r["chi2"], r["n"] * r["phi"] ** 2)          # chi2 = n * phi^2
        self.assertAlmostEqual(r["v_cramer"], abs(r["phi"]))
        self.assertLess(r["p_valor"], 0.05)
        self.assertTrue(resumen_asociacion(r)["asociacion_significativa"])

    def test_tabla_mayor_que_2x2(self):
        df = pd.DataFrame({"x": list("aabbcc") * 5, "y": list("uvuvuv") * 5})
        r = test_asociacion(df, "x", "y")
        self.assertIsNone(r["phi"])
        self.assertEqual(r["grados_libertad"], 2)

    def test_una_sola_categoria(self):
        with self.assertRaises(ValueError):
            test_asociacion(pd.DataFrame({"x": [1, 1, 1], "y": [0, 1, 0]}), "x", "y")


if __name__ == "__main__":
    unittest.main()
