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

def leer_base_conocimiento(ruta_archivo):
    """
    Generador que lee tripletas de la base de conocimiento.
    Devuelve una tripleta (sujeto, predicado, objeto) por cada línea válida.
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
            yield (sujeto, predicado, objeto)


def consultar(base_conocimiento, sujeto, predicado, objeto):
    """
    Generador que produce resultados de consulta.
    Devuelve diccionarios con las sustituciones de variables.
    """
    for (s, p, o) in base_conocimiento:
        if ((sujeto == s or sujeto[0].isupper()) and
            (predicado == p or predicado[0].isupper()) and
            (objeto == o or objeto[0].isupper())):

            sustitucion = {}
            if sujeto[0].isupper():
                sustitucion[sujeto] = s
            if predicado[0].isupper():
                sustitucion[predicado] = p
            if objeto[0].isupper():
                sustitucion[objeto] = o

            yield sustitucion
