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
        use_full = os.getenv("TEST_USE_FULL_KB") == "1"
        if use_full:
            repo_root = Path(__file__).resolve().parents[2]
            kb_path = repo_root / "kb" / "bc.txt"
            self.hechos, self.reglas = cargar(kb_path)
        else:
            # crear un archivo temporal dentro de tests/
            temp_path = Path(__file__).parent / "temp_bc_small.txt"
            temp_path.write_text(SMALL_KB, encoding="utf-8")
            self.hechos, self.reglas = cargar(temp_path)

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

        resultado = razona(consulta, self.hechos, self.reglas)
        self.assertIsInstance(resultado, bool)


# Permite ejecutar este archivo como script
if __name__ == "__main__":
    unittest.main(verbosity=2)