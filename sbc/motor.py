# sbc/motor.py
# =============================================================================
# Módulo: motor
#
# Descripción:
#   Este módulo proporciona utilidades para gestionar una base de conocimiento
#   representada mediante tripletas (sujeto, predicado, objeto).
#
#   Incluye:
#     - leer_base_conocimiento(ruta):
#         Generador que lee un archivo de base de conocimiento y emite cada
#         hecho o regla como instancia de Tripleta.
#
#     - consultar(base, sujeto, predicado, objeto):
#         Generador que busca coincidencias en la base de conocimiento y devuelve
#         objetos Sustitucion con las asignaciones de variables (términos cuyo
#         nombre comienza con mayúscula).
#
#   Formato esperado de entrada:
#     Cada línea debe contener palabras separadas por espacios.
#     Las líneas pueden representar:
#       • Hechos: una tripleta simple (sujeto, predicado, objeto).
#       • Reglas: dos tripletas unidas mediante el operador "<-".
#     Las líneas vacías o que comienzan con '#' se consideran comentarios y se
#     ignoran durante el procesamiento.
# =============================================================================

import warnings
from pathlib import Path
from typing import Iterator, Iterable
from sbc.clases import Tripleta, Sustitucion
from pyparsing import Word, alphanums, Suppress, restOfLine, Combine, Literal, Group, Optional

def leer_base_conocimiento(ruta_archivo: str | Path) -> Iterator[Tripleta]:
    """
    Generador que lee una base de conocimiento desde un archivo de texto.

    Cada línea puede representar:
      - Un hecho: formado por tres palabras (sujeto, predicado, objeto).
      - Una regla: formada por dos tripletas unidas mediante "<-".

    Se admiten sujetos compuestos por dos palabras.

    Ignora líneas vacías y comentarios (precedidos por '#').

    Args:
        ruta_archivo (str | Path): Ruta del archivo de base de conocimiento.

    Yields:
        Tripleta: Instancia que representa un hecho o parte de una regla.
    """

    # Definimos el formato esperado usando pyparsing
    palabra = Word(alphanums + "áéíóúñüÁÉÍÓÚÑÜ_-")
    comentario = Suppress("#" + restOfLine)

    # Definimos tripleta
    tripleta3 = Group(palabra("sujeto")                           + palabra("predicado") + palabra("objeto"))
    tripleta4 = Group(Combine(palabra + " " + palabra)("sujeto")  + palabra("predicado") + palabra("objeto")) # Suponemos sujeto de 2 palabras

    tripleta = tripleta4 | tripleta3

    # Definimos regla
    flecha = Suppress(Optional(" ") + Literal("<-") + Optional(" "))
    regla = Group(tripleta)("causa") + flecha + Group(tripleta)("efecto")

    # Definimos el parser completo
    parser_linea = regla | tripleta

    with Path(ruta_archivo).open('r') as archivo:
        for linea in archivo:
            linea = linea.strip()
            
            if not linea or linea.startswith("#"):
                continue  # Saltamos líneas vacías y comentarios

            try:
                resultado = parser_linea.parseString(linea)

                if 'causa' in resultado and 'efecto' in resultado:
                    # Es una regla
                    causa = resultado['causa'][0]
                    efecto = resultado['efecto'][0]

                    yield Tripleta(causa['sujeto'], causa['predicado'], causa['objeto'])
                    yield Tripleta(efecto['sujeto'], efecto['predicado'], efecto['objeto'])
                else:
                    # Es un hecho
                    hecho = resultado[0]
                    yield Tripleta(hecho['sujeto'], hecho['predicado'], hecho['objeto'])
            except Exception as e:
                warnings.warn(f"No se pudo analizar la línea: '{linea}'. Motivo: {e}", RuntimeWarning)
                continue

def consultar(
        base_conocimiento: Iterable[Tripleta | tuple[str, str, str]],
        sujeto: str,
        predicado: str,
        objeto: str
) -> Iterator[Sustitucion]:
    """
    Generador que produce resultados de consulta.
    Devuelve instancias de Sustitucion con las sustituciones de variables.
    Acepta como base elementos Tripleta o tuplas/listas de 3 elementos.
    """
    for entrada in base_conocimiento:
        # soportar Tripleta y tuplas/listas
        if isinstance(entrada, Tripleta):
            s, p, o = entrada.sujeto, entrada.predicado, entrada.objeto
        else:
            s, p, o = entrada

        if ((sujeto == s or sujeto[0].isupper()) and
            (predicado == p or predicado[0].isupper()) and
            (objeto == o or objeto[0].isupper())):

            sustitucion = Sustitucion()
            if sujeto[0].isupper():
                sustitucion[sujeto] = s
            if predicado[0].isupper():
                sustitucion[predicado] = p
            if objeto[0].isupper():
                sustitucion[objeto] = o

            yield sustitucion

# Comando debug. Falta integrarlo en cli o no se donde para poder usarlo. Tampoco sé si hay que darle la bc por parámetro.
def debug():
    """Muestra toda la base de conocimiento cargada en memoria."""
    if not base_conocimiento:
        print("La base de conocimiento está vacía.")
    else:
        print("\nBase de conocimiento cargada en memoria:")
        for tripleta in base_conocimiento:
            print(tripleta)

# Comando razona. Pseudocódigo, falta completarlo y aplicarlo.
def razona():
    # Obtener todas las reglas de la base de conocimiento
    reglas = obtener_reglas_de_base_conocimiento()  # Devuelve las reglas como tripletas

    # Para cada regla (cada regla tiene un antecedente y un consecuente)
    for regla in reglas:
        antecedente, consecuente = regla  # Descomponer la regla en antecedente y consecuente / parsear

        # Verificar si el antecedente se cumple en la base de conocimiento
        if consultar(antecedente):
            # Si el antecedente se cumple, aplicar el consecuente

            # Agregar el consecuente a la base de conocimiento
            agregar_hecho_a_base_conocimiento(consecuente)  # Añadir el consecuente (nuevo hecho) a la base de conocimiento

            print(f"Se aplicó la regla: {antecedente} -> {consecuente}")
        else:
            print(f"No se cumple el antecedente: {antecedente}")