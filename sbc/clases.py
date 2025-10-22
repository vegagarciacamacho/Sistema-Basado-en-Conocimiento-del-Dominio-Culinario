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
class Tripleta:
    """
    Representa una tripleta (sujeto, predicado, objeto).
    """
    sujeto: str
    predicado: str
    objeto: str

    def __iter__(self) -> Iterator[str]:
        yield self.sujeto
        yield self.predicado
        yield self.objeto

    def __repr__(self) -> str:
        return f"Tripleta({self.sujeto!r}, {self.predicado!r}, {self.objeto!r})"

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

