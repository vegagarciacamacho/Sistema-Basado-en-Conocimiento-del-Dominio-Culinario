# sbc/clases.py
# Descripción: Clases de dominio simplificadas y funcionales

from dataclasses import dataclass
from typing import Iterator, Any

@dataclass
class Tripleta:
    """Representa una tripleta (sujeto, predicado, objeto)."""
    sujeto: str
    predicado: str
    objeto: str

    def __iter__(self) -> Iterator[str]:
        """Permite iterar sobre los componentes de la tripleta."""
        yield self.sujeto
        yield self.predicado
        yield self.objeto

    def __repr__(self) -> str:
        return f"{self.sujeto} {self.predicado} {self.objeto}"

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Tripleta):
            return (self.sujeto, self.predicado, self.objeto) == \
                   (other.sujeto, other.predicado, other.objeto)
        if isinstance(other, (tuple, list)) and len(other) == 3:
            return (self.sujeto, self.predicado, self.objeto) == tuple(other)
        return NotImplemented
    
    def es_variable(self, componente: str) -> bool:
        """Verifica si un componente es una variable (empieza con mayúscula)."""
        return componente and componente[0].isupper()
    
    def tiene_variables(self) -> bool:
        """Verifica si la tripleta contiene alguna variable."""
        return any(self.es_variable(c) for c in self)
    
    def aplicar(self, sustitucion: 'Sustitucion') -> 'Tripleta':
        """
        Aplica una sustitución a la tripleta, reemplazando variables por valores.
        
        Args:
            sustitucion: Diccionario de sustituciones {variable: valor}
            
        Returns:
            Nueva tripleta con las variables sustituidas
        """
        return Tripleta(
            sustitucion.get(self.sujeto, self.sujeto),
            sustitucion.get(self.predicado, self.predicado),
            sustitucion.get(self.objeto, self.objeto)
        )


class Sustitucion(dict):
    """
    Diccionario especializado para sustituciones de variables.
    Facilita la composición y verificación de compatibilidad.
    """
    
    def es_compatible_con(self, var: str, valor: str) -> bool:
        """
        Verifica si una nueva asignación es compatible con las existentes.
        
        Args:
            var: Variable a asignar
            valor: Valor a asignar
            
        Returns:
            True si es compatible (no hay conflicto), False en caso contrario
        """
        return var not in self or self[var] == valor
    
    def agregar(self, var: str, valor: str) -> bool:
        """
        Intenta agregar una nueva asignación si es compatible.
        
        Args:
            var: Variable a asignar
            valor: Valor a asignar
            
        Returns:
            True si se agregó exitosamente, False si hay conflicto
        """
        if not self.es_compatible_con(var, valor):
            return False
        self[var] = valor
        return True
    
    def componer(self, otra: 'Sustitucion') -> 'Sustitucion | None':
        """
        Compone esta sustitución con otra, verificando compatibilidad.
        
        Args:
            otra: Otra sustitución a componer
            
        Returns:
            Nueva sustitución combinada, o None si hay conflicto
        """
        resultado = Sustitucion(self)
        for var, valor in otra.items():
            if not resultado.agregar(var, valor):
                return None
        return resultado
    
    def __repr__(self) -> str:
        if not self:
            return "Sustitucion({})"
        items = ", ".join(f"{k} = {v}" for k, v in self.items())
        return f"{items}"

# Clases para extensiones (para implementar después)
@dataclass
class LogicaDifusa:
    """Representa lógica difusa"""
    valor: float

    def __init__(self, valor: float):
        if not (0.0 <= valor <= 1.0):
            raise ValueError("El valor debe estar entre 0.0 y 1.0")
        self.valor = valor

    def __repr__(self) -> str:
        return f"{self.valor}"
    
    # T-NORMAS (operadores AND difusos)
    @staticmethod
    def t_min(a: float, b: float) -> float:
        """T-norma mínimo (Zadeh)"""
        return min(a, b)
    
    @staticmethod
    def t_producto(a: float, b: float) -> float:
        """T-norma producto (Larsen)"""
        return a * b
    
    @staticmethod
    def t_lukasiewicz(a: float, b: float) -> float:
        """T-norma de Lukasiewicz"""
        return max(0, a + b - 1)
    
    # S-NORMAS (operadores OR difusos)
    @staticmethod
    def s_max(a: float, b: float) -> float:
        """S-norma máximo (Zadeh)"""
        return max(a, b)
    
    @staticmethod
    def s_suma_probabilistica(a: float, b: float) -> float:
        """S-norma suma probabilística"""
        return a + b - a * b
    
    @staticmethod
    def s_lukasiewicz(a: float, b: float) -> float:
        """S-norma de Lukasiewicz"""
        return min(1, a + b)
    
    # IMPLICACIONES DIFUSAS
    @staticmethod
    def impl_mamdani(antecedente: float, consecuente: float) -> float:
        """Implicación de Mamdani (mínimo)"""
        return min(antecedente, consecuente)
    
    @staticmethod
    def impl_larsen(antecedente: float, consecuente: float) -> float:
        """Implicación de Larsen (producto)"""
        return antecedente * consecuente
    
    @staticmethod
    def impl_zadeh(antecedente: float, consecuente: float) -> float:
        """Implicación de Zadeh"""
        return max(1 - antecedente, min(antecedente, consecuente))
    
    # AGREGACIÓN
    @staticmethod
    def agregacion_max(valores: list[float]) -> float:
        """Agregación por máximo"""
        return max(valores) if valores else 0.0
    
    @staticmethod
    def agregacion_suma(valores: list[float]) -> float:
        """Agregación por suma acotada"""
        return min(1.0, sum(valores))


@dataclass
class Extension:
    """Extensiones opcionales"""
    difusa: LogicaDifusa | None = None
    precedencia: int | None = None
    restricciones: list[tuple[str, str, int]] = None
    
    def __post_init__(self):
        if self.restricciones is None:
            self.restricciones = []
    
    def __repr__(self):
        partes = []
        if self.difusa is not None:
            partes.append(f"{self.difusa}")
        if self.precedencia is not None:
            partes.append(f"{self.precedencia}")
        if self.restricciones:
            partes.append(
                "; ".join(f"{a} {op} {b}" for a, op, b in self.restricciones)
            )
        return "[" + "; ".join(partes) + "]"

@dataclass
class Hecho:
    """Representa un hecho en la base de conocimiento."""
    tripleta: Tripleta
    extension: Extension | None = None
    
    def __repr__(self) -> str:
        return f"{self.tripleta}".strip()

@dataclass
class Regla:
    """Representa una regla de producción: consecuente <- antecedentes."""
    consecuente: Tripleta
    antecedentes: list[Tripleta]
    extension: Extension | None = None
    
    def __repr__(self) -> str:
        ants = ", ".join(str(a) for a in self.antecedentes)
        return f"{self.consecuente} <- {ants}"