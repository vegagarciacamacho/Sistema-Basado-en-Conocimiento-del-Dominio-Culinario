import os
import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from sbc.motor import cargar, ejecutar_consulta, añadir_hecho, revocar_hecho, descubrir, razona
from sbc.clases import Tripleta


SMALL_KB = """\
# --------------------------------------------------
# HECHOS BÁSICOS
# --------------------------------------------------

tomate es ingrediente.
tomate color rojo.
tomate hay 500.

cebolla es ingrediente.
cebolla color morado.
cebolla hay 100.

queso_cheddar es ingrediente.
queso_cheddar contiene lacteos.
queso_cheddar hay 0.

pollo es ingrediente.
pollo hay 200.

# --------------------------------------------------
# REGLAS SIMPLES
# --------------------------------------------------

# Disponible si hay cantidad > 0
X disponible_si true <- X es ingrediente, X hay Y. [Y > 0]
X disponible_si false <- X es ingrediente, X hay Y. [Y = 0]

# Lista de compra si no está disponible
X lista_compra si <- X es ingrediente, X disponible_si false.

# --------------------------------------------------
# RECETAS
# --------------------------------------------------

ensalada_simple es receta.
ensalada_simple contiene ingrediente001.
ingrediente001 es tomate.

ensalada_simple contiene ingrediente002.
ingrediente002 es cebolla.

ensalada_simple contiene ingrediente003.
ingrediente003 es queso_cheddar.
"""

def _capture(func, *args, **kwargs) -> str:
    """Captura la salida por pantalla de una función."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        func(*args, **kwargs)
    return buf.getvalue()

class TestMotor(unittest.TestCase):

    def setUp(self):
        """Carga hechos y reglas para cada test."""
        #Comprobar variable de entorno para usar KB completa o pequeña
        self.use_full = os.getenv("TEST_USE_FULL_KB") == "1"
        if self.use_full:
            # Si la variable de entorno TEST_USE_FULL_KB está configurada a "1", se usa la base de datos completa
            archivo_bc = Path(__file__).parent.parent / 'kb' / 'bc.txt'  # Construye la ruta completa al archivo bc.txt en la carpeta "kb"
            self.hechos, self.reglas = cargar(archivo_bc)  # Llama a la función cargar para cargar hechos y reglas desde el archivo bc.txt
        else:
            # crear un archivo temporal dentro de tests/
            temp_path = Path(__file__).parent / "temp_bc_small.txt"  # Construye la ruta del archivo temporal en el directorio de tests
            temp_path.write_text(SMALL_KB, encoding="utf-8")  # Escribe la base de datos pequeña en el archivo temporal
            self.hechos, self.reglas = cargar(temp_path)  # Carga los hechos y reglas desde este archivo temporal


    # --------------------------------------------------

    def test_consultas_y_modificaciones(self):

        # consulta con variable
        out = _capture(ejecutar_consulta, "tomate color X?", self.hechos, [])
        self.assertIn("X = rojo", out)

        # consulta afirmativa
        out = _capture(ejecutar_consulta, "tomate color rojo?", self.hechos, [])
        self.assertTrue("Sí" in out)

        # añadir y consultar
        out = _capture(añadir_hecho, "pepino color verde.", self.hechos)
        self.assertIn("Hecho añadido", out)

        out = _capture(ejecutar_consulta, "pepino color X?", self.hechos, [])
        self.assertIn("X = verde", out)

        # revocar y comprobar ausencia
        ok = revocar_hecho("no pepino color verde.", self.hechos)
        self.assertIs(ok, True)

        out = _capture(ejecutar_consulta, "pepino color X?", self.hechos, [])
        self.assertTrue(
            ("No se encontraron coincidencias" in out)
            or ("No, no está" in out)
        )

    # --------------------------------------------------

    def test_descubrir_y_razona(self):

        hechos_deducidos = descubrir(self.hechos, self.reglas)
        self.assertIsInstance(hechos_deducidos, list)

        consulta = Tripleta("tomate", "es_vegetal", "verdadero")

        resultado, grado = razona(consulta, self.hechos, self.reglas)
        self.assertIsInstance(resultado, bool)
        self.assertIsInstance(grado, float)


    # --------------------------------------------------

    def test_ingredientes_y_recetas(self):
        if not self.use_full:
            self.skipTest("Test de ingredientes y recetas solo se ejecuta con la base de datos completa.")
        
        # Verifica si la receta de bica_blanca_laza es disponible
        out = _capture(razona, "razona si bica_blanca_laza receta_totalmente_disponible true?", self.hechos, [])
        self.assertIn("Sí, se puede deducir: bica_blanca_laza receta_totalmente_disponible true con certeza 0.95", out)

        # Verifica si una receta es apta para celiacos (contiene gluten)
        out = _capture(ejecutar_consulta, "bica_blanca_laza no_apta_celiacos X?", self.hechos, [])
        self.assertIn("X = true", out)

        # Verifica si una receta no es apta para personas con intolerancia a la lactosa
        out = _capture(ejecutar_consulta, "bica_blanca_laza no_apta_lactosa X?", self.hechos, [])
        self.assertIn("X = true", out)

    # --------------------------------------------------

    def test_maridajes(self):
        if not self.use_full:
            self.skipTest("Test de maridajes solo se ejecuta con la base de datos completa.")

        # Verifica si el vino tinto marida con carne
        out = _capture(ejecutar_consulta, "vino_tinto marida carne?", self.hechos, [])
        self.assertTrue("Sí, está en la base." in out)

        # Verifica si la cerveza suave marida con ensalada
        out = _capture(ejecutar_consulta, "cerveza_suave marida ensalada?", self.hechos, [])
        self.assertTrue("Sí" in out)

        # Verifica si el café marida con postre
        out = _capture(razona, "razona si vino_blanco acompaña_receta quiche_de_salmon?", self.hechos, [])
        self.assertTrue("Sí, se puede deducir: vino_blanco acompaña_receta quiche_de_salmon con certeza 0.85" in out)


# Permite ejecutar este archivo como script
if __name__ == "__main__":
    unittest.main(verbosity=2)