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
#     - añadir(entrada, base_conocimiento):
#         Añade un nuevo hecho a la base de conocimiento después de parsearlo.
#
#     - revocar(entrada, base_conocimiento):
#         Revoca (elimina) un hecho de la base de conocimiento.
#
#      - descubrir(hechos, reglas):
#         Aplica encadenamiento hacia adelante sobre las reglas para deducir nuevos hechos.
#
#     - razona(consulta, hechos, reglas, visitados):
#         Aplica encadenamiento hacia atrás para deducir si la consulta es derivable.
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
from sbc.clases import Tripleta, Sustitucion, Regla, Extension
from pyparsing import ParseException

from sbc.parserSBC import _parser

def cargar(ruta_archivo: str | Path) -> tuple[list[Tripleta], list[Regla]]:
    """
    Carga una base de conocimiento desde un archivo de texto.

    Args:
        ruta_archivo (str | Path): Ruta del archivo de base de conocimiento.

    Returns:
        tuple[list[Tripleta], list[Regla]]: Tupla con listas de hechos y reglas.
    """
    # Separar entre reglas y hechos
    hechos = []
    reglas = []

    with Path(ruta_archivo).open('r', encoding='utf-8') as archivo:
        for num_linea, linea in enumerate(archivo, 1):
            linea = linea.strip()
            
            # Ignorar líneas vacías y comentarios
            if not linea or linea.startswith("#"):
                continue

            try:
                tipo, contenido = _parser.parsear_linea_archivo(linea)
                
                if tipo == 'regla':
                    reglas.append(contenido)
                else:  # 'hecho' o 'tripleta'
                    hechos.append(contenido)
                    
            except ParseException as e:
                warnings.warn(
                    f"Línea {num_linea}: No se pudo analizar '{linea}'. "
                    f"Error en columna {e.column}: {e.msg}",
                    RuntimeWarning
                )
            except Exception as e:
                warnings.warn(
                    f"Línea {num_linea}: Error inesperado al procesar '{linea}': {e}",
                    RuntimeWarning
                )

    return hechos, reglas

def consultar(entrada: str, base_conocimiento: list[Tripleta], hechos_deducidos: list[Tripleta]) -> None:
    """
    Procesa una consulta usando el parser modular.
    
    Args:
        entrada: texto en formato "sujeto predicado objeto?" o "razona si ...?"
        base_conocimiento: lista de hechos base
        hechos_deducidos: lista de hechos deducidos
    """
    try:
        consulta_tripleta, es_razonamiento = _parser.parsear_consulta(entrada)
        
        # Si es razonamiento, no procesamos aquí (se debe llamar a razona directamente)
        if es_razonamiento:
            print("Use el comando 'razona si' correctamente desde el CLI.\n")
            return
        
        base_total_hechos = base_conocimiento + hechos_deducidos
        
        # Detectar si hay variables
        tiene_variables = any(
            t[0].isupper() 
            for t in (consulta_tripleta.sujeto, consulta_tripleta.predicado, consulta_tripleta.objeto) 
            if t
        )

        if tiene_variables:
            resultados = []
            for hecho in base_total_hechos:
                asignacion = {}
                ok = True

                campos_consulta = [consulta_tripleta.sujeto, consulta_tripleta.predicado, consulta_tripleta.objeto]
                campos_hecho = [hecho.sujeto, hecho.predicado, hecho.objeto]

                for c_val, h_val in zip(campos_consulta, campos_hecho):
                    if not c_val:
                        # campo vacío en la consulta: no coincide
                        ok = False
                        break

                    if c_val[0].isupper():
                        var = c_val
                        # consistencia de la variable si aparece repetida
                        if var in asignacion:
                            if asignacion[var] != h_val:
                                ok = False
                                break
                        else:
                            asignacion[var] = h_val
                    else:
                        # debe coincidir exactamente
                        if c_val != h_val:
                            ok = False
                            break

                if ok and asignacion:
                    resultados.append(asignacion)

            if resultados:
                print("\nResultados encontrados:")
                for r in resultados:
                    for var, valor in r.items():
                        print(f"  {var} = {valor}")
                print()
            else:
                print("No se encontraron coincidencias.\n")
        else:
            if consulta_tripleta in base_total_hechos:
                print("Sí, está en la base de conocimiento.\n")
            else:
                print("No, no está en la base de conocimiento.\n")
                
    except ParseException as e:
        print(f"Error de sintaxis: {e.msg}\n")
    except Exception as e:
        print(f"Error al procesar consulta: {e}\n")

def añadir(entrada: str, base_conocimiento: list[Tripleta]) -> None:
    """Añade un hecho a la base de conocimiento usando el parser."""
    try:
        tripleta, extension = _parser.parsear_afirmacion(entrada)
        base_conocimiento.append(tripleta)
        
        msg = f"Hecho añadido: {tripleta}"
        if extension:
            detalles = []
            if extension.difusa is not None:
                detalles.append(f"difusa={extension.difusa}")
            if extension.precedencia is not None:
                detalles.append(f"precedencia={extension.precedencia}")
            if extension.restricciones:
                detalles.append(f"restricciones={extension.restricciones}")
            msg += f" [{'; '.join(detalles)}]"
        
        print(f"{msg}\n")
        
    except ParseException as e:
        print(f"Error de sintaxis: {e.msg}\n")
    except Exception as e:
        print(f"Error al añadir hecho: {e}\n")

def revocar(entrada: str, base_conocimiento: list[Tripleta]) -> bool:
    """Revoca (elimina) un hecho de la base de conocimiento usando el parser."""
    try:
        tripleta = _parser.parsear_negacion(entrada)
        
        if tripleta in base_conocimiento:
            base_conocimiento.remove(tripleta)
            return True
        
        return False
        
    except ParseException as e:
        print(f"Error de sintaxis: {e.msg}\n")
        return False
    except Exception as e:
        print(f"Error al revocar hecho: {e}\n")
        return False

# Encadenamiento hacia adelante
def descubrir(hechos: list[Tripleta], reglas: list[Regla]) -> list[Tripleta]:
    """
    Aplica encadenamiento hacia adelante sobre las reglas.
    Retorna los nuevos hechos deducidos sin modificar la base original.
    """
    hechos_deducidos = []
    hechos_totales = hechos.copy()

    nuevos = True
    while nuevos:
        nuevos = False
        for regla in reglas:
            # Verificar si todos los antecedentes están en los hechos
            if all(ant in hechos_totales for ant in regla.antecedentes):
                # Si el consecuente no está ya deducido, lo añadimos
                if regla.consecuente not in hechos_totales:
                    hechos_deducidos.append(regla.consecuente)
                    hechos_totales.append(regla.consecuente)
                    nuevos = True
                    
    return hechos_deducidos

def debug(hechos: list[Tripleta], hechos_deducidos: list[Tripleta], reglas: list[Regla]):
    """Muestra toda la base de conocimiento cargada en memoria."""
    print("\n" + "=" * 5 + " BASE DE CONOCIMIENTO EN MEMORIA" + "=" * 5)
    
    print(f"\n--- HECHOS BASE ({len(hechos)}) ---")
    for h in hechos:
        print(f"  - {h}")
    
    print(f"\n--- HECHOS DEDUCIDOS ({len(hechos_deducidos)}) ---")
    for h in hechos_deducidos:
        print(f"  - {h}")
    
    print(f"\n--- REGLAS ({len(reglas)}) ---")
    for regla in reglas:
        antecedentes_str = ", ".join(str(ant) for ant in regla.antecedentes)
        print(f"  {regla.consecuente} <- {antecedentes_str}")
        if regla.extension:
            ext = regla.extension
            detalles = []
            if ext.difusa is not None:
                detalles.append(f"difusa={ext.difusa}")
            if ext.precedencia is not None:
                detalles.append(f"precedencia={ext.precedencia}")
            if ext.restricciones:
                detalles.append(f"restricciones={ext.restricciones}")
            print(f"    [{'; '.join(detalles)}]")
    
    print("=" * 25 + "\n")

# Encadenamiento hacia atrás    
def razona(consulta: Tripleta, hechos: list[Tripleta], reglas: list[Regla], 
           visitados: set = None) -> bool:
    """
    Aplica encadenamiento hacia atrás para deducir si la consulta es derivable.
    """
    if visitados is None:
        visitados = set()
    
    # Evitar ciclos infinitos
    consulta_tuple = (consulta.sujeto, consulta.predicado, consulta.objeto)
    if consulta_tuple in visitados:
        return False
    visitados.add(consulta_tuple)
    
    # 1. Verificar si está directamente en los hechos
    if consulta in hechos:
        return True
    
    # 2. Buscar reglas cuyo consecuente coincida con la consulta
    for regla in reglas:
        if regla.consecuente == consulta:
            # Verificar si todos los antecedentes se pueden demostrar
            if all(razona(ant, hechos, reglas, visitados) for ant in regla.antecedentes):
                return True
    
    return False