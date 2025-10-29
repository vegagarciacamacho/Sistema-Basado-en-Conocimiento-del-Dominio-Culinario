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

def cargar(ruta_archivo: str | Path) -> Iterator[Tripleta]:
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

    # Separar entre reglas y hechos
    hechos = []
    reglas = []

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

                    reglas.append((
                        Tripleta(causa['sujeto'], causa['predicado'], causa['objeto']),
                        Tripleta(efecto['sujeto'], efecto['predicado'], efecto['objeto'])
                    ))
                else:
                    # Es un hecho
                    hecho = resultado[0]
                    hechos.append(Tripleta(hecho['sujeto'], hecho['predicado'], hecho['objeto']))
            except Exception as e:
                warnings.warn(f"No se pudo analizar la línea: '{linea}'. Motivo: {e}", RuntimeWarning)
                continue
    return hechos, reglas

def consultar(consulta : Tripleta, base_conocimiento : list[Tripleta, Tripleta]) -> Iterator[Sustitucion]:
    """
    Realiza una consulta sobre la base de conocimiento.
    Devuelve una lista de Tripletas que coinciden con la consulta.
    La consulta puede contener variables (identificadas con mayúscula).
    """
    for hecho, _ in base_conocimiento:
        coincidencia = True
        sustitucion = {}
        
        for attr in ['sujeto', 'predicado', 'objeto']:
            valor_consulta = getattr(consulta, attr)
            valor_hecho = getattr(hecho, attr)
            
            if valor_consulta[0].isupper():  # Es una variable
                sustitucion[valor_consulta] = valor_hecho
            elif valor_consulta != valor_hecho:
                coincidencia = False
                break
        
        if coincidencia:
            yield Sustitucion(sustitucion)

def añadir(entrada : str , base_conocimiento : list[Tripleta, Tripleta]):
    """Añade un hecho a la base de conocimiento."""
    # Limpiar la entrada (eliminar el punto al final)
    hecho = entrada.strip().rstrip('.')
    
    # Dividir la entrada en sujeto, predicado y objeto
    try:
        sujeto, predicado, objeto = hecho.split()
        
        # Crear una nueva tripleta
        nuevo_hecho = Tripleta(sujeto, predicado, objeto)
        
        # Añadir el nuevo hecho a la base de conocimiento
        base_conocimiento.append(nuevo_hecho)
        
        print(f"Hecho añadido: {nuevo_hecho}")
    except ValueError:
        print("Error: El hecho debe estar en el formato 'sujeto predicado objeto'.")

def revocar(entrada: str, base_conocimiento: list[Tripleta]) -> bool:
    """
    Revoca (elimina) un hecho de la base de conocimiento.
    Args:
        entrada: texto en formato "no sujeto predicado objeto."
        base_conocimiento: lista de tripletas donde buscar y eliminar
    Returns:
        bool: True si se encontró y eliminó, False si no existía
    """
    # Limpiar entrada (quitar "no" inicial y punto final)
    hecho = entrada.strip()[3:-1].strip()
    
    try:
        # Dividir en sujeto predicado objeto
        palabras = hecho.split()
        if len(palabras) != 3:
            return False
            
        tripleta = Tripleta(palabras[0], palabras[1], palabras[2])
        
        # Buscar y eliminar si existe
        if tripleta in base_conocimiento:
            base_conocimiento.remove(tripleta)
            return True
            
        return False
        
    except ValueError:
        return False

def descubrir(hechos: list[Tripleta], reglas: list[tuple[Tripleta, Tripleta]]) -> list[Tripleta]:
    """
    Aplica las reglas sobre los hechos y devuelve los nuevos hechos deducidos sin modificar la base de conocimiento original.
    Repite hasta que no se infieran más hechos.
    """
    hechos_deducidos = []

    nuevos = True
    while nuevos:
        nuevos = False
        for consecuente, antecedente in reglas:
            # Si el antecedente está en los hechos, deducimos el consecuente
            if antecedente in hechos and consecuente not in hechos_deducidos:
                hechos_deducidos.append(consecuente)  # Añadimos el consecuente a los hechos deducidos
                nuevos = True  # Hay nuevos hechos que deducir
    return hechos_deducidos


# Comando debug. Falta integrarlo en cli o no se donde para poder usarlo. Tampoco sé si hay que darle la bc por parámetro.
def debug():
    """Muestra toda la base de conocimiento cargada en memoria."""
    if not base_conocimiento:
        print("La base de conocimiento está vacía.")
    else:
        print("\nBase de conocimiento cargada en memoria:")
        for tripleta in base_conocimiento:
            print(tripleta)

def consultar(entrada: str, base_conocimiento: list[Tripleta], hechos_deducidos: list[Tripleta]) -> None:
    """
    Procesa una consulta y muestra los resultados.
    Args:
        entrada: texto en formato "sujeto predicado objeto?"
        base_conocimiento: lista de hechos base
        hechos_deducidos: lista de hechos deducidos
    """
    # Quitar el ? final y dividir en palabras
    consulta_text = entrada[:-1].strip()
    palabras = consulta_text.split()
    
    if len(palabras) < 3:
        print("Error: la consulta debe tener al menos 3 palabras.\n")
        return
        
    if len(palabras) == 2:
        palabras.append("X")
        
    mitad = len(palabras) // 2
    predicado = palabras[mitad]
    sujeto = " ".join(palabras[:mitad])
    objeto = " ".join(palabras[mitad + 1:])

    consulta_tripleta = Tripleta(sujeto, predicado, objeto)
    base_total_hechos = base_conocimiento + hechos_deducidos

    # Detectar si hay variables
    tiene_variables = any(t[0].isupper() for t in (sujeto, predicado, objeto) if t)

    if tiene_variables:
        resultados = list(unificar(consulta_tripleta, base_total_hechos))
        if resultados:
            print("\nResultados encontrados:")
            for r in resultados:
                for var, valor in r.items():
                    print(f"{var} = {valor}")
            print()
        else:
            print("No se encontraron coincidencias.\n")
    else:
        if consulta_tripleta in base_total_hechos:
            print("Sí, está en la base de conocimiento.\n")
        else:
            print("No, no está en la base de conocimiento.\n")