# sbc/clases.py
# Descripción: Definición de las clases de dominio usadas por el motor y la CLI.
#              - Tripleta: dataclass que representa una tripleta (sujeto, predicado, objeto).
#                Proporciona iteración, comparación y representación legible.
#              - Sustitucion: diccionario especializado para representar sustituciones
#                de variables (por ejemplo {'X': 'tomate'}). Incluye un método `add`
#                para añadir asociaciones y una representación personalizada.
#              Estas clases son utilizadas por sbc.motor y sbc.cli para leer la
#              base de conocimiento, realizar consultas y devolver resultados.

from dataclasses import dataclass
from typing import Iterator, Any

@dataclass
class LogicaDifusa:
    """Representa una lógica difusa con su valor de pertenencia."""
    valor: float

    def __init__(self, valor: float):
        if not (0.0 <= valor <= 1.0):
            raise ValueError("El valor de pertenencia debe estar entre 0.0 y 1.0")
        self.valor = valor

    def minimo(self, otro: 'LogicaDifusa') -> 'LogicaDifusa':
        """Devuelve el mínimo de los dos valores difusos."""
        return LogicaDifusa(min(self.valor, otro.valor))

    def maximo(self, otro: 'LogicaDifusa') -> 'LogicaDifusa':
        """Devuelve el máximo de los dos valores difusos."""
        return LogicaDifusa(max(self.valor, otro.valor))

    def producto(self, otro: 'LogicaDifusa') -> 'LogicaDifusa':
        """Devuelve el producto de los dos valores difusos."""
        return LogicaDifusa(self.valor * otro.valor)

    def suma(self, otro: 'LogicaDifusa') -> 'LogicaDifusa':
        """Devuelve la suma de los dos valores difusos, limitada a 1.0."""
        return LogicaDifusa(min(self.valor + otro.valor, 1.0))

    def __repr__(self) -> str:
        return f"LogicaDifusa({self.valor})"

@dataclass
class Extension:
    """Representa las extensiones opcionales de una regla o afirmación."""
    difusa: LogicaDifusa | None = None # Usamos LogicaDifusa en lugar de un valor float (es opcional)
    precedencia: int | None = None
    restricciones: list[tuple[str, str, int]] = None
    
    def __post_init__(self):
        if self.restricciones is None:
            self.restricciones = []

@dataclass
class Tripleta:
    """
    Representa una tripleta (sujeto, predicado, objeto).
    """
    sujeto: str
    predicado: str
    objeto: str
    extension: Extension | None = None #La extensión es opcional

    def __iter__(self) -> Iterator[str]:
        yield self.sujeto
        yield self.predicado
        yield self.objeto

    def __repr__(self) -> str:
        return f"{self.sujeto} {self.predicado} {self.objeto}"

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Tripleta):
            return (self.sujeto, self.predicado, self.objeto) == (other.sujeto, other.predicado, other.objeto)
        if isinstance(other, (tuple, list)) and len(other) == 3:
            return (self.sujeto, self.predicado, self.objeto) == tuple(other)
        return NotImplemented


class Sustitucion(dict):
    """
    Diccionario especializado para representar sustituciones de variables.
    """
    def add(self, var: str, valor: str) -> None:
        self[var] = valor

    def __repr__(self) -> str:
        return f"Sustitucion({dict(self)!r})"

@dataclass
class Regla:
    """Representa una regla de producción con sus extensiones."""
    consecuente: Tripleta
    antecedentes: list[Tripleta]
    extension: Extension | None = None