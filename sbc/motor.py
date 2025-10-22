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

def leer_base_conocimiento(ruta_archivo):
    """
    Generador que lee tripletas de la base de conocimiento.
    Devuelve una instancia de Tripleta por cada línea válida.
    """
    with ruta_archivo.open('r') as archivo:
        for linea in archivo:
            palabras = linea.strip().split()
            if len(palabras) < 3:
                print(f"Línea no válida (menos de 3 palabras): {linea.strip()}")
                continue

            mitad = len(palabras) // 2
            predicado = palabras[mitad]
            sujeto = " ".join(palabras[:mitad])
            objeto = " ".join(palabras[mitad + 1:])
            yield Tripleta(sujeto, predicado, objeto)


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


