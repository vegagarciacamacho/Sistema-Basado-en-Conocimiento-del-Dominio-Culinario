import unittest
from pyparsing import ParseException
from sbc.parserSBC import ParserSBC

def parse_ext(text):
    parser = ParserSBC()
    resultado = parser.extension.parseString(text, parseAll=True)
    return parser._parsear_extension(resultado)

class TestParserSBCCompleto(unittest.TestCase):

    # ---------------------------------------------------------------
    # TRIPLETAS
    # ---------------------------------------------------------------
    def test_tripleta_basica(self):
        p = ParserSBC()
        t = p.parsear_tripleta("juan es_alumno pedro")
        self.assertEqual((t.sujeto, t.predicado, t.objeto), ("juan", "es_alumno", "pedro"))

    def test_tripleta_con_mayusculas_y_numeros(self):
        p = ParserSBC()
        t = p.parsear_tripleta("x1 hermanoDe Y2")
        self.assertEqual((t.sujeto, t.predicado, t.objeto), ("x1", "hermanoDe", "Y2"))

    # ---------------------------------------------------------------
    # CONSULTAS
    # ---------------------------------------------------------------
    def test_consulta_simple(self):
        p = ParserSBC()
        trip, razonamiento = p.parsear_consulta("juan amigo pedro?")
        self.assertFalse(razonamiento)
        self.assertEqual(trip.objeto, "pedro")

    def test_consulta_razona(self):
        p = ParserSBC()
        trip, razonamiento = p.parsear_consulta("razona si juan ama maria?")
        self.assertTrue(razonamiento)
        self.assertEqual(trip.predicado, "ama")

    def test_consulta_espacios_random(self):
        p = ParserSBC()
        trip, razonamiento = p.parsear_consulta("  juan   es   maria ? ")
        self.assertEqual(trip.predicado, "es")

    # ---------------------------------------------------------------
    # EXTENSIONES
    # ---------------------------------------------------------------

    def test_ext_difusa(self):
        ext = parse_ext("[0.7]")
        self.assertEqual(ext.difusa.valor, 0.7)

    def test_ext_precedencia(self):
        ext = parse_ext("[123]")
        self.assertEqual(ext.precedencia, 123)

    def test_ext_restricciones(self):
        ext = parse_ext("[A < 2; B >= 5]")
        self.assertEqual(len(ext.restricciones), 2)

    def test_ext_combinada(self):
        ext = parse_ext("[0.5; 321; A = 3]")
        self.assertEqual(ext.difusa.valor, 0.5)
        self.assertEqual(ext.precedencia, 321)
        self.assertIn(("A", "=", 3), ext.restricciones)

    def test_ext_multiple_difusa_queda_ultima(self):
        ext = parse_ext("[0.2; 0.9]")
        self.assertEqual(ext.difusa.valor, 0.9)

    def test_ext_multiple_precedencia_queda_ultima(self):
        ext = parse_ext("[001; 999]")
        self.assertEqual(ext.precedencia, 999)

    def test_ext_invalida_valor_no_numerico(self):
        with self.assertRaises(ParseException):
            parse_ext("[A = xyz]")

    def test_ext_vacia_error(self):
        with self.assertRaises(ParseException):
            parse_ext("[]")

    def test_ext_mal_formada_falta_cierre(self):
        with self.assertRaises(ParseException):
            parse_ext("[0.3")

    def test_ext_operadores_varios(self):
        ext = parse_ext("[X <= 5; Y > 3; Z >= 10]")
        self.assertEqual(len(ext.restricciones), 3)

    # ---------------------------------------------------------------
    # AFIRMACIONES
    # ---------------------------------------------------------------
    def test_afirmacion_simple(self):
        p = ParserSBC()
        trip, ext = p.parsear_afirmacion("juan sabe maria.")
        self.assertEqual(trip.predicado, "sabe")
        self.assertIsNone(ext)

    def test_afirmacion_con_extension(self):
        p = ParserSBC()
        trip, ext = p.parsear_afirmacion("juan sabe maria. [0.8; 120]")
        self.assertEqual(ext.precedencia, 120)

    def test_afirmacion_con_restricciones(self):
        p = ParserSBC()
        trip, ext = p.parsear_afirmacion("a b c. [A = 1]")
        self.assertEqual(ext.restricciones, [("A", "=", 1)])

    # ---------------------------------------------------------------
    # NEGACIONES
    # ---------------------------------------------------------------
    def test_negacion_basica(self):
        p = ParserSBC()
        trip = p.parsear_negacion("no juan ama maria.")
        self.assertEqual(trip.predicado, "ama")

    # ---------------------------------------------------------------
    # REGLAS
    # ---------------------------------------------------------------
    def test_regla_simple(self):
        p = ParserSBC()
        tipo, regla = p.parsear_linea_archivo("juan feliz maria <- pedro ayuda maria.")
        self.assertEqual(tipo, "regla")
        self.assertEqual(len(regla.antecedentes), 1)

    def test_regla_multiple(self):
        p = ParserSBC()
        tipo, regla = p.parsear_linea_archivo("x r y <- a b c, d e f, g h i.")
        self.assertEqual(len(regla.antecedentes), 3)

    def test_regla_con_extension(self):
        p = ParserSBC()
        tipo, regla = p.parsear_linea_archivo("x r y <- a b c. [0.5; 111]")
        self.assertEqual(regla.extension.precedencia, 111)

    # ---------------------------------------------------------------
    # PARSEAR LÍNEAS COMPLETAS DEL ARCHIVO
    # ---------------------------------------------------------------
    def test_linea_hecho(self):
        p = ParserSBC()
        tipo, (hecho, ext) = p.parsear_linea_archivo("juan ama maria. [0.7]")
        self.assertEqual(tipo, "hecho")
        self.assertEqual(hecho.predicado, "ama")
        self.assertEqual(ext.difusa.valor, 0.7)

    def test_linea_tripleta_sola(self):
        p = ParserSBC()
        tipo, (trip, ext) = p.parsear_linea_archivo("a b c")
        self.assertEqual(tipo, "tripleta")
        self.assertIsNone(ext)

    def test_linea_comentario_final(self):
        p = ParserSBC()
        tipo, (hecho, _) = p.parsear_linea_archivo("a b c. # comentario")
        self.assertEqual(tipo, "hecho")

    # ---------------------------------------------------------------
    # ERRORES GENERALES
    # ---------------------------------------------------------------
    def test_error_tripleta_invalida(self):
        p = ParserSBC()
        with self.assertRaises(ParseException):
            p.parsear_tripleta("solo_dos_palabras")

    def test_error_sintaxis_regla_mal_formada(self):
        p = ParserSBC()
        with self.assertRaises(ParseException):
            p.parsear_linea_archivo("a b c <- a b.")

    def test_error_consulta_mal_formada(self):
        p = ParserSBC()
        with self.assertRaises(ParseException):
            p.parsear_consulta("juan ama maria??")


if __name__ == "__main__":
    unittest.main()
