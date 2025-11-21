# sbc/motor.py
# =============================================================================
# Módulo: motor
#
# Descripción:
#   Motor de inferencia simplificado para un sistema basado en conocimiento.
#   Implementa las funciones core que el profesor especificó:
#   - unificar: une dos tripletas generando sustituciones
#   - consultar: busca hechos que unifiquen con un patrón
#   - aplicar: aplica una regla dados sus antecedentes probados
#   - razona: encadenamiento hacia atrás (backward chaining)
#
#   Funciones auxiliares para el CLI:
#   - cargar: lee archivo de base de conocimiento
#   - descubrir: encadenamiento hacia adelante (forward chaining)
# =============================================================================

from pathlib import Path
from typing import Iterator
from sbc.clases import Tripleta, Sustitucion, Regla
from sbc.parserSBC import _parser
from pyparsing import ParseException
from sbc.manejo_errores import advertir_error_sintaxis, advertir_error_general

def unificar(patron: Tripleta, hecho: Tripleta, 
             sustitucion: Sustitucion = None) -> Sustitucion | None:
    """
    Unifica un patrón (con posibles variables) con un hecho concreto.
    
    Args:
        patron: Tripleta que puede contener variables (ej: "X es Y")
        hecho: Tripleta concreta (ej: "tomate es ingrediente")
        sustitucion: Sustitución preexistente a extender
        
    Returns:
        Sustitución resultante si la unificación tiene éxito, None si falla
    """
    if sustitucion is None:
        sustitucion = Sustitucion()
    else:
        sustitucion = Sustitucion(sustitucion)  # Copiar para no mutar
    
    # Unificar cada componente (sujeto, predicado, objeto)
    for p_comp, h_comp in zip(patron, hecho):
        if patron.es_variable(p_comp):
            # Es una variable: intentar asignarla
            if not sustitucion.agregar(p_comp, h_comp):
                return None  # Conflicto: la variable ya tenía otro valor
        else:
            # Es un literal: debe coincidir exactamente
            if p_comp != h_comp:
                return None  # No coincide
    
    return sustitucion


def consultar(patron: Tripleta, base: list[Tripleta]) -> Iterator[Sustitucion]:
    """
    Genera todas las sustituciones que unifican el patrón con hechos en la base.
    
    Args:
        patron: Tripleta patrón (puede contener variables)
        base: Lista de hechos (tripletas concretas)
        
    Yields:
        Sustituciones que hacen que el patrón coincida con algún hecho
    """
    for hecho in base:
        sustitucion = unificar(patron, hecho)
        if sustitucion is not None:
            yield sustitucion

def aplicar(regla: Regla, hechos: list[Tripleta]) -> Iterator[Tripleta]:
    """
    Aplica una regla: encuentra todas las formas de satisfacer los antecedentes
    y genera los consecuentes resultantes.
    
    Args:
        regla: Regla a aplicar
        hechos: Base de hechos conocidos
        
    Yields:
        Nuevos hechos derivados de aplicar la regla
    """
    # Generar todas las combinaciones de sustituciones que satisfacen los antecedentes
    for sustitucion in _resolver_antecedentes(regla.antecedentes, hechos):
        # Aplicar la sustitución al consecuente
        yield regla.consecuente.aplicar(sustitucion)


def razona(objetivo: Tripleta, hechos: list[Tripleta], 
           reglas: list[Regla], visitados: set = None) -> bool:
    """
    Encadenamiento hacia atrás: intenta probar un objetivo recursivamente.
    
    Args:
        objetivo: Tripleta a demostrar (puede contener variables)
        hechos: Base de hechos conocidos
        reglas: Reglas de inferencia disponibles
        visitados: Objetivos ya visitados (para evitar ciclos)
        
    Returns:
        True si el objetivo es demostrable, False en caso contrario
        
    Estrategia:
        1. Si el objetivo está en los hechos → éxito
        2. Si no, buscar reglas cuyo consecuente unifique con el objetivo
        3. Para cada regla, intentar probar todos sus antecedentes
        4. Si todos los antecedentes se prueban → éxito
    """
    if visitados is None:
        visitados = set()
    
    # Evitar ciclos infinitos
    objetivo_str = str(objetivo)
    if objetivo_str in visitados:
        return False
    visitados.add(objetivo_str)
    
    # Caso base: el objetivo está directamente en los hechos
    if any(unificar(objetivo, hecho) is not None for hecho in hechos):
        return True
    
    # Caso recursivo: buscar reglas que puedan probar el objetivo
    for regla in reglas:
        # Intentar unificar el consecuente de la regla con el objetivo
        sustitucion = unificar(regla.consecuente, objetivo)
        if sustitucion is None:
            continue  # Esta regla no aplica
        
        # Aplicar la sustitución a los antecedentes
        antecedentes_instanciados = [ant.aplicar(sustitucion) 
                                     for ant in regla.antecedentes]
        
        # Intentar probar todos los antecedentes recursivamente
        if all(razona(ant, hechos, reglas, visitados.copy()) 
               for ant in antecedentes_instanciados):
            return True  # Todos los antecedentes se probaron
    
    return False  # No se pudo probar el objetivo

def _resolver_antecedentes(antecedentes: list[Tripleta], 
                           hechos: list[Tripleta]) -> Iterator[Sustitucion]:
    """
    Genera todas las sustituciones que satisfacen una lista de antecedentes.
    
    Es una función recursiva que va componiendo sustituciones:
    - Para el primer antecedente, encuentra todas sus posibles sustituciones
    - Para cada una, intenta resolver el resto de antecedentes
    - Solo devuelve sustituciones que satisfacen TODOS los antecedentes
    """
    if not antecedentes:
        yield Sustitucion()  # Caso base: no hay antecedentes que satisfacer
        return
    
    primer_ant, *resto = antecedentes
    
    # Resolver el primer antecedente
    for sust_parcial in consultar(primer_ant, hechos):
        # Aplicar la sustitución parcial al resto de antecedentes
        resto_instanciado = [ant.aplicar(sust_parcial) for ant in resto]
        
        # Resolver el resto recursivamente
        for sust_resto in _resolver_antecedentes(resto_instanciado, hechos):
            # Componer ambas sustituciones
            sust_total = sust_parcial.componer(sust_resto)
            if sust_total is not None:
                yield sust_total


def cargar(ruta_archivo: str | Path) -> tuple[list[Tripleta], list[Regla]]:
    """
    Carga una base de conocimiento desde un archivo.
    
    Args:
        ruta_archivo: Ruta al archivo de base de conocimiento
        
    Returns:
        Tupla (hechos, reglas) con el contenido parseado
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

def descubrir(hechos: list[Tripleta], reglas: list[Regla]) -> list[Tripleta]:
    """
    Encadenamiento hacia adelante: aplica reglas iterativamente hasta que
    no se puedan deducir más hechos nuevos.
    
    Args:
        hechos: Hechos base conocidos
        reglas: Reglas de inferencia
        
    Returns:
        Lista de nuevos hechos deducidos (sin incluir los originales)
    """
    hechos_totales = hechos.copy()
    hechos_nuevos = []
    
    cambio = True
    while cambio:
        cambio = False
        
        for regla in reglas:
            # Aplicar la regla y obtener nuevos consecuentes
            for nuevo_hecho in aplicar(regla, hechos_totales):
                if nuevo_hecho not in hechos_totales:
                    hechos_totales.append(nuevo_hecho)
                    hechos_nuevos.append(nuevo_hecho)
                    cambio = True
    
    return hechos_nuevos

def ejecutar_consulta(entrada: str, base_conocimiento: list[Tripleta], 
                      hechos_deducidos: list[Tripleta]) -> None:
    """
    Procesa una consulta del usuario y muestra los resultados.
    """
    try:
        consulta_tripleta, es_razonamiento = _parser.parsear_consulta(entrada)
        
        if es_razonamiento:
            print("Use el comando 'razona si' correctamente desde el CLI.\n")
            return
        
        base_total = base_conocimiento + hechos_deducidos
        
        if consulta_tripleta.tiene_variables():
            # Consulta con variables: mostrar todas las sustituciones
            resultados = list(consultar(consulta_tripleta, base_total))
            
            if resultados:
                for sust in resultados:
                    if sust:  # Si hay variables asignadas
                        print(f"  {sust}")
                    else:  # Consulta sin variables que se cumple
                        print(f"  Sí")
                print()
            else:
                print("No se encontraron coincidencias.\n")
        else:
            # Consulta sin variables: verificar existencia
            if consulta_tripleta in base_total:
                print("Sí, está en la base de conocimiento.\n")
            else:
                print("No, no está en la base de conocimiento.\n")
                
    except ParseException as e:
        print(f"Error de sintaxis: {e.msg}\n")
    except Exception as e:
        print(f"Error al procesar consulta: {e}\n")


def añadir_hecho(entrada: str, base_conocimiento: list[Tripleta]) -> None:
    """Añade un hecho a la base de conocimiento."""
    try:
        tripleta, extension = _parser.parsear_afirmacion(entrada)
        base_conocimiento.append(tripleta)
        
        msg = f"Hecho añadido: {tripleta}"
        if extension and (extension.difusa or extension.precedencia or 
                         extension.restricciones):
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


def revocar_hecho(entrada: str, base_conocimiento: list[Tripleta]) -> bool:
    """Elimina un hecho de la base de conocimiento."""
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


def mostrar_debug(hechos: list[Tripleta], hechos_deducidos: list[Tripleta], 
                  reglas: list[Regla]) -> None:
    """Muestra toda la base de conocimiento en memoria."""
    print("\n" + "=" * 50)
    print("BASE DE CONOCIMIENTO EN MEMORIA")
    print("=" * 50)
    
    print(f"\n--- HECHOS BASE ({len(hechos)}) ---")
    for h in hechos:
        print(f"  {h}")
    
    print(f"\n--- HECHOS DEDUCIDOS ({len(hechos_deducidos)}) ---")
    for h in hechos_deducidos:
        print(f"  {h}")
    
    print(f"\n--- REGLAS ({len(reglas)}) ---")
    for regla in reglas:
        print(f"  {regla}")
    
    print("=" * 50 + "\n")