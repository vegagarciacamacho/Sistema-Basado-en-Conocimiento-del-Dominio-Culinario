import unittest
from sbc.parserSBC import ParserSBC


def parse_ext(text):
    """Pequeño helper para usar en varios tests."""
    parser = ParserSBC()
    resultado = parser.extension.parseString(text, parseAll=True)

    return parser._parsear_extension(resultado)


class TestParserExtension(unittest.TestCase):

    def test_parse_difusa(self):
        ext = parse_ext("[0.7]")
        self.assertEqual(ext.difusa.valor, 0.7)

    def test_parse_precedencia(self):
        ext = parse_ext("[123]")
        self.assertEqual(ext.precedencia, 123)

    def test_parse_restricciones(self):
        ext = parse_ext("[A < 2; B >= 5]")
        self.assertEqual(len(ext.restricciones), 2)
        self.assertIn(("A", "<", 2), ext.restricciones)

    def test_parse_todo(self):
        ext = parse_ext("[0.5; 321; A = 3]")
        self.assertEqual(ext.difusa.valor, 0.5)
        self.assertEqual(ext.precedencia, 321)
        self.assertIn(("A", "=", 3), ext.restricciones)


if __name__ == "__main__":
    unittest.main()