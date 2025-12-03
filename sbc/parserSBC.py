# sbc/parserSBC.py
# Descripción: Implementación de parsers para el sistema basado en la sintaxis EBNF.
#              Utiliza la librería pyparsing para definir los parsers de:
#              - Tripletas
#              - Consultas (simples y de razonamiento)
#              - Afirmaciones
#              - Negaciones
#              - Reglas
#              - Líneas completas del archivo de base de conocimiento
#              Cada parser convierte cadenas de texto en instancias de las clases
#              definidas en sbc.clases.py, facilitando la interacción con el motor

from sbc.clases import Tripleta, Regla, Extension, Hecho, LogicaDifusa
from pyparsing import (
    Word,
    Suppress,
    restOfLine,
    Literal,
    Group,
    Optional,
    ZeroOrMore,
    Regex,
    nums,
    oneOf,
)


class ParserSBC:
    """
    Clase singleton que contiene todos los parsers necesarios para el sistema.
    Se inicializa una sola vez y se reutiliza en todas las funciones.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._inicializar_parsers()
        return cls._instance

    def _inicializar_parsers(self):
        """Crea todos los parsers necesarios según la sintaxis EBNF."""

        # Definición básica de caracteres según EBNF
        minus = "abcdefghijklmnopqrstuvwxyz" + "ñáéíóúü"
        mayus = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" + "ÑÁÉÍÓÚÜ"
        digito = "0123456789"

        # Términos básicos
        self.literal = Word(minus + digito, minus + mayus + digito + "_")
        self.variable = Word(mayus, minus + mayus + digito + "_")
        self.termino = self.variable | self.literal

        # Comentario
        self.comentario = Suppress("#" + restOfLine)

        # Tripleta: termino termino termino
        self.tripleta = Group(
            self.termino("sujeto") + self.termino("predicado") + self.termino("objeto")
        )

        # Extensiones opcionales
        difusa = Regex(r"0\.\d+|1\.0+")("difusa")  # Valor entre 0 y 1
        precedencia = Word(nums, exact=3)(
            "precedencia"
        )  # Entero de 3 dígitos [000-999]
        operador = oneOf("< <= = >= >")
        restriccion = Group(
            self.variable("var") + operador("op") + Word(nums)("valor")
        )("restriccion*")  # Puede haber múltiples restricciones

        # difusa y precedencia mantienen solo la última ocurrencia si aparecieran repetidos
        opcional = difusa | precedencia | restriccion
        punto_coma = Suppress(Optional(" ") + Literal(";") + Optional(" "))

        self.extension = Group(
            Suppress("[") + opcional + ZeroOrMore(punto_coma + opcional) + Suppress("]")
        )("extension")

        # Separadores
        flecha = Suppress(Optional(" ") + Literal("<-") + Optional(" "))
        coma = Suppress(Optional(" ") + Literal(",") + Optional(" "))
        punto = Suppress(".")
        interrogacion = Suppress("?")

        # Consulta: tripleta "?" | "razona si " tripleta "?"
        self.consulta_simple = self.tripleta + interrogacion
        self.consulta_razona = (
            Suppress("razona") + Suppress("si") + self.tripleta + interrogacion
        )
        self.consulta = self.consulta_razona | self.consulta_simple

        # Afirmación: tripleta "." [ extension ]
        self.afirmacion = (
            Group(self.tripleta)("tripleta") + punto + Optional(self.extension)
        )

        # Negación: "no " tripleta "."
        self.negacion = Suppress("no") + Group(self.tripleta)("tripleta") + punto

        # Regla: tripleta "<-" tripleta { ", " tripleta } "." [ extension ]
        lista_antecedentes = Group(self.tripleta) + ZeroOrMore(
            coma + Group(self.tripleta)
        )

        self.regla = (
            Group(self.tripleta)("consecuente")
            + flecha
            + lista_antecedentes("antecedentes")
            + punto
            + Optional(self.extension)
        )

        # Parser completo para líneas de archivo (regla, afirmación o tripleta sola)
        self.linea_archivo = (self.regla | self.afirmacion | self.tripleta) + Optional(
            self.comentario
        )

    def parsear_tripleta(self, texto: str) -> Tripleta:
        """Parsea una tripleta."""
        resultado = self.tripleta.parseString(texto, parseAll=True)
        trip = resultado[0]
        return Tripleta(trip["sujeto"], trip["predicado"], trip["objeto"])

    def parsear_consulta(self, texto: str) -> tuple[Tripleta, bool]:
        """Parsea una consulta (con o sin razonamiento)."""
        resultado = self.consulta.parseString(texto, parseAll=True)

        # Detectar si es razonamiento o consulta simple
        es_razonamiento = "razona si" in texto.lower()

        # La tripleta está siempre en el primer grupo
        trip = resultado[0]
        return Tripleta(
            trip["sujeto"], trip["predicado"], trip["objeto"]
        ), es_razonamiento

    def parsear_afirmacion(self, texto: str) -> tuple[Tripleta, Extension | None]:
        """Parsea una afirmación con posible extensión."""
        resultado = self.afirmacion.parseString(texto, parseAll=True)
        trip = resultado["tripleta"][0]
        tripleta = Tripleta(trip["sujeto"], trip["predicado"], trip["objeto"])
        extension = self._parsear_extension(resultado)
        return tripleta, extension

    def parsear_negacion(self, texto: str) -> Tripleta:
        """Parsea una negación."""
        resultado = self.negacion.parseString(texto, parseAll=True)
        trip = resultado["tripleta"][0]
        return Tripleta(trip["sujeto"], trip["predicado"], trip["objeto"])

    def parsear_linea_archivo(self, texto: str) -> tuple[str, any]:
        """
        Parsea una línea del archivo de base de conocimiento.

        Args:
            texto: Línea del archivo

        Returns:
            Tupla (tipo, contenido) donde tipo es 'regla', 'hecho' o 'tripleta'

        Raises:
            ParseException: Si el formato no es válido
        """
        resultado = self.linea_archivo.parseString(texto, parseAll=True)

        # Detectar tipo
        if "consecuente" in resultado and "antecedentes" in resultado:
            # Es una regla
            cons = resultado["consecuente"][0]
            consecuente = Tripleta(cons["sujeto"], cons["predicado"], cons["objeto"])

            antecedentes = []
            for ant in resultado["antecedentes"]:
                ant = ant[0]
                antecedentes.append(
                    Tripleta(ant["sujeto"], ant["predicado"], ant["objeto"])
                )

            extension = self._parsear_extension(resultado)
            regla = Regla(consecuente, antecedentes, extension)
            return "regla", regla

        elif "tripleta" in resultado:
            # Es una afirmación con punto y puede tener extensión
            trip = resultado["tripleta"][0]
            extension = self._parsear_extension(resultado)
            hecho = Tripleta(trip["sujeto"], trip["predicado"], trip["objeto"])
            return "hecho", (hecho, extension)

        else:
            # Tripleta simple (retrocompatibilidad)
            trip = resultado[0]
            hecho = Tripleta(trip["sujeto"], trip["predicado"], trip["objeto"])
            return "tripleta", (hecho, None)

    def _parsear_extension(self, resultado) -> Extension | None:
        """Extrae los datos de extensión del resultado del parser."""
        if "extension" not in resultado:
            return None

        ext_data = resultado["extension"]
        if not ext_data:
            return None

        extension = Extension()

        # Buscar difusa
        if "difusa" in ext_data:
            try:
                valor_difuso = float(ext_data["difusa"])
                extension.difusa = LogicaDifusa(valor_difuso)
            except (ValueError, TypeError):
                pass

        # Buscar precedencia
        if "precedencia" in ext_data:
            try:
                prec = int(ext_data["precedencia"])
                extension.precedencia = prec
            except (ValueError, TypeError):
                pass

        # Restricciones (lista)
        if "restriccion" in ext_data:
            for r in ext_data["restriccion"]:
                try:
                    var = r["var"]
                    op = r["op"]
                    valor = int(r["valor"])
                    extension.restricciones.append((var, op, valor))
                except (ValueError, KeyError, TypeError):
                    pass

        return (
            extension
            if (extension.difusa or extension.precedencia or extension.restricciones)
            else None
        )


# Instancia global del parser (singleton)
_parser = ParserSBC()
