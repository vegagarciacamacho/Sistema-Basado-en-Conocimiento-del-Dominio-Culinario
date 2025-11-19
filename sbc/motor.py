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

from pathlib import Path
from typing import Iterator, Iterable
from sbc.clases import Tripleta, Sustitucion, Regla, Extension
from pyparsing import ParseException

from sbc.parserSBC import _parser
from sbc.manejo_errores import advertir_error_sintaxis, advertir_error_general

def cargar(ruta_archivo: str | Path) -> tuple[list[Tripleta], list[Regla]]:
    """
    Carga una base de conocimiento desde un archivo de texto.

    Args:
        ruta_archivo (str | Path): Ruta del archivo de base de conocimiento.

    Returns:
        tuple[list[Tripleta], list[Regla]]: Tupla con listas de hechos y reglas.
    """
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
                advertir_error_sintaxis(num_linea, linea, e.column, e.msg)

            except Exception as e:
                advertir_error_general(num_linea, linea, str(e))

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
                asignacion = unificar(consulta_tripleta, hecho)
                if asignacion:
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
    Encadenamiento hacia adelante con soporte de variables.
    Aplica reglas mientras genere nuevos hechos. Devuelve solo los deducidos.
    """
    hechos_totales = hechos.copy()
    hechos_deducidos = []

    cambio = True
    while cambio:
        cambio = False

        for regla in reglas:
            # Necesitamos encontrar TODAS las asignaciones válidas para los antecedentes
            asignaciones_posibles = [{}]  # empezamos con asignación vacía

            for antecedente in regla.antecedentes:
                nuevas_asignaciones = []

                for asignacion_actual in asignaciones_posibles:
                    antecedente_inst = aplicar_asignacion(antecedente, asignacion_actual)

                    # Intentar unificación con todos los hechos
                    for hecho in hechos_totales:
                        asignacion_unif = unificar(antecedente_inst, hecho)

                        if asignacion_unif is not None:
                            # combinación de ambas asignaciones
                            asignacion_combinada = asignacion_actual.copy()

                            conflict = False
                            for var, val in asignacion_unif.items():
                                if var in asignacion_combinada and asignacion_combinada[var] != val:
                                    conflict = True
                                    break
                                asignacion_combinada[var] = val

                            if not conflict:
                                nuevas_asignaciones.append(asignacion_combinada)

                asignaciones_posibles = nuevas_asignaciones

            # Si no hay asignaciones completas válidas, no se puede disparar la regla
            for asignacion_final in asignaciones_posibles:
                consecuente_inst = aplicar_asignacion(regla.consecuente, asignacion_final)

                # Solo añadir si es nuevo
                if consecuente_inst not in hechos_totales:
                    hechos_totales.append(consecuente_inst)
                    hechos_deducidos.append(consecuente_inst)
                    cambio = True

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

def unificar(consulta: Tripleta, hecho: Tripleta) -> dict:
    """
    Unifica dos tripletas (consulta y hecho), devolviendo un diccionario con las asignaciones
    de las variables si es posible, o None si no se puede unificar.
    """
    asignacion = {}
    #print(f"Intentando unificar: consulta={consulta} con hecho={hecho}")

    for c_val, h_val in zip([consulta.sujeto, consulta.predicado, consulta.objeto], 
                             [hecho.sujeto, hecho.predicado, hecho.objeto]):
        if not c_val:
            continue  # Si el valor de la consulta es None, no se compara (se omite)
        
        if c_val[0].isupper():  # Es una variable
            if c_val in asignacion:
                if asignacion[c_val] != h_val:
                    #print(f"No se puede unificar: la variable {c_val} tiene valores diferentes")
                    return None  # No se puede unificar, ya que la variable tiene un valor diferente
            else:
                asignacion[c_val] = h_val
                #print(f"Se ha unificado: {c_val} = {h_val}")
        else:
            # Comparación directa si no es una variable
            if c_val != h_val:
                #print(f"No se puede unificar: {c_val} != {h_val}")
                return None  # No se puede unificar, ya que los valores no coinciden
    
    #print(f"Unificación exitosa: {asignacion}")
    return asignacion

def razona(consulta: Tripleta, hechos: list[Tripleta], reglas: list[Regla]) -> bool:
    """
    Aplica encadenamiento hacia atrás para deducir si la consulta es derivable.
    Primero verifica si el consecuente está en los hechos. Si no, intenta unificar los antecedentes.
    """

    #print(f"\nIntentando deducir: {consulta}")

    # 1. Verificar si el consecuente de alguna regla ya está en los hechos
    if consulta in hechos:
        #print(f"Consulta encontrada directamente en los hechos: {consulta}")
        return True

    # 2. Buscar reglas cuyo consecuente coincida con la consulta
    for regla in reglas:
        #print(f"Verificando regla: {regla.consecuente} <- {regla.antecedentes}")
        
        # Intentamos unificar el consecuente de la regla con la consulta
        asignacion = unificar(regla.consecuente, consulta)
        if asignacion:
            print(f"El consecuente se ha unificado con la consulta: {asignacion}")
            
            # 3. Verificar si todos los antecedentes de la regla se pueden demostrar
            for antecedente in regla.antecedentes:
                #print(f"Verificando antecedente: {antecedente}")
                antecedente_aplicado = aplicar_asignacion(antecedente, asignacion)
                # Primero, verificar si el antecedente ya está en los hechos
                if antecedente_aplicado in hechos:
                    print(f"Antecedente {antecedente_aplicado} encontrado en hechos.")
                else:
                    # Si no está en los hechos, intentar unificarlo con los hechos disponibles
                    unificado = False
                    for hecho in hechos:
                        asignacion_antecedente = unificar(antecedente_aplicado, hecho)
                        if asignacion_antecedente:
                            asignacion.update(asignacion_antecedente)  # Actualizar la asignación global
                            # Si la unificación es exitosa, crear una nueva consulta unificada
                            antecedente_unificado = aplicar_asignacion(antecedente_aplicado,asignacion_antecedente)
                            print(f"Antecedente unificado: {antecedente_unificado}")
                            if razona(antecedente_unificado, hechos, reglas):
                                unificado = True
                                break
                    
                    if not unificado:
                        #print(f"No se pudo unificar el antecedente {antecedente}.")
                        # Si no puede unificarse con ningún hecho, intentamos con las reglas
                        if not razona(antecedente_aplicado, hechos, reglas):
                            return False  # No se puede demostrar el antecedente

            #print(f"Todos los antecedentes demostrados. Se puede deducir: {consulta}")
            return True
        
    return False

def aplicar_asignacion(antecedente: Tripleta, asignacion: dict) -> Tripleta:
    """Aplica la asignación a un antecedente para sustituir las variables por los valores asignados."""
    return Tripleta(
        sujeto=asignacion.get(antecedente.sujeto, antecedente.sujeto),
        predicado=asignacion.get(antecedente.predicado, antecedente.predicado),
        objeto=asignacion.get(antecedente.objeto, antecedente.objeto)
    )