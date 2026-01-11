import unittest

from sbc.clases import Tripleta, Extension, LogicaDifusa, Regla
from sbc.motor import aplicar, descubrir, consultar


class TestOpcionales(unittest.TestCase):

    # --------------------------------------------------
    # LÓGICA DIFUSA
    # --------------------------------------------------

    def test_difusa_hecho_y_regla_minimo(self):
        """
        Hecho con 0.6 + regla con 0.8
        → min(0.6, 0.8) = 0.6
        """
        hechos = [
            (Tripleta("vino", "marida", "carne"), Extension(difusa=LogicaDifusa(0.6)))
        ]

        regla = Regla(
            consecuente=Tripleta("vino", "acompaña", "plato"),
            antecedentes=[Tripleta("vino", "marida", "carne")],
            extension=Extension(difusa=LogicaDifusa(0.8)),
        )

        resultados = list(aplicar(regla, hechos))
        self.assertEqual(len(resultados), 1)

        _, grado, _ = resultados[0]
        self.assertAlmostEqual(grado, 0.6)

    def test_difusa_varios_antecedentes(self):
        """
        Dos antecedentes con 0.9 y 0.4
        → min = 0.4
        """
        hechos = [
            (Tripleta("a", "es", "x"), Extension(difusa=LogicaDifusa(0.9))),
            (Tripleta("b", "es", "y"), Extension(difusa=LogicaDifusa(0.4))),
        ]

        regla = Regla(
            consecuente=Tripleta("z", "es", "ok"),
            antecedentes=[
                Tripleta("a", "es", "x"),
                Tripleta("b", "es", "y"),
            ],
            extension=None,
        )

        resultados = list(aplicar(regla, hechos))
        self.assertEqual(len(resultados), 1)

        _, grado, _ = resultados[0]
        self.assertAlmostEqual(grado, 0.4)

    # --------------------------------------------------
    # PRECEDENCIA DE REGLAS
    # --------------------------------------------------

    def test_precedencia_regla_mayor_gana(self):
        """
        Dos reglas con mismo antecedente.
        Debe quedarse la de mayor precedencia.
        """
        hechos = [
            (Tripleta("juan", "es", "persona"), None)
        ]

        regla_baja = Regla(
            consecuente=Tripleta("juan", "estado", "feliz"),
            antecedentes=[Tripleta("juan", "es", "persona")],
            extension=Extension(precedencia=100),
        )

        regla_alta = Regla(
            consecuente=Tripleta("juan", "estado", "contento"),
            antecedentes=[Tripleta("juan", "es", "persona")],
            extension=Extension(precedencia=900),
        )

        nuevos = descubrir(hechos, [regla_baja, regla_alta])

        self.assertEqual(len(nuevos), 1)
        hecho, _ = nuevos[0]
        self.assertEqual(hecho, Tripleta("juan", "estado", "contento"))

    # --------------------------------------------------
    # RESTRICCIONES
    # --------------------------------------------------

    def test_restriccion_cumple(self):
        """
        X = 3 cumple X < 5 → debe unificar
        """
        hechos = [
            (Tripleta("3", "es", "numero"), None)
        ]

        patron = Tripleta("X", "es", "numero")
        ext = Extension(restricciones=[("X", "<", 5)])

        resultados = list(consultar(patron, hechos, ext))
        self.assertEqual(len(resultados), 1)

    def test_restriccion_no_cumple(self):
        """
        X = 7 no cumple X < 5 → no debe unificar
        """
        hechos = [
            (Tripleta("7", "es", "numero"), None)
        ]

        patron = Tripleta("X", "es", "numero")
        ext = Extension(restricciones=[("X", "<", 5)])

        resultados = list(consultar(patron, hechos, ext))
        self.assertEqual(len(resultados), 0)

    def test_restriccion_variable_no_instanciada(self):
        """
        Restricción sobre variable no presente
        → no debe fallar
        """
        hechos = [
            (Tripleta("juan", "es", "persona"), None)
        ]

        patron = Tripleta("juan", "es", "persona")
        ext = Extension(restricciones=[("X", ">", 10)])

        resultados = list(consultar(patron, hechos, ext))
        self.assertEqual(len(resultados), 1)


if __name__ == "__main__":
    unittest.main()
