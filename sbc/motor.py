# sbc/motor.py
# Descripción: Módulo 'motor' que proporciona utilidades para manejar una base
#              de conocimiento representada como tripletas (sujeto, predicado, objeto).
#              Contiene:
#                - leer_base_conocimiento(ruta): generador que lee un archivo de
#                  base de conocimiento y emite cada tripleta como una tupla.
#                - consultar(base, sujeto, predicado, objeto): generador que
#                  busca coincidencias en la base y devuelve diccionarios con
#                  sustituciones para variables (nombres que empiezan por mayúscula).
#              El formato esperado por línea es: palabras separadas por espacios;
#              el predicado se toma como la palabra central de la línea.

from pathlib import Path
from sbc.clases import Tripleta, Sustitucion
from pyparsing import Word, alphanums, Suppress, restOfLine, Combine, MatchFirst, Literal, Group, Optional

def leer_base_conocimiento(ruta_archivo):
    """
    Generador que lee hechos y reglas de la base del conocimient.
    Devuelve un diccionario de hechos y reglas como lista de tripletas.
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

            print(linea)
            
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
                print(f"Error al parsear la línea: {linea}\n{e}")
                continue

def consultar(base_conocimiento, sujeto, predicado, objeto):
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


