# sbc/motor.py
# Descripción: Motor de inferencia para el sistema de bases de conocimiento

from pathlib import Path
from typing import Iterator, Callable
from sbc.clases import Tripleta, Sustitucion, Regla, Extension, LogicaDifusa
from sbc.parserSBC import _parser
from pyparsing import ParseException
from sbc.manejo_errores import advertir_error_sintaxis, advertir_error_general


def verificar_restricciones(
    sustitucion: Sustitucion, restricciones: list[tuple[str, str, int]]
) -> bool:
    """
    Verifica que una sustitución cumpla todas las restricciones.

    Args:
        sustitucion: Diccionario de variables -> valores
        restricciones: Lista de (variable, operador, valor)

    Returns:
        True si todas las restricciones se cumplen
    """
    if not restricciones:
        return True

    operadores = {
        "<": lambda x, y: x < y,
        "<=": lambda x, y: x <= y,
        "=": lambda x, y: x == y,
        ">=": lambda x, y: x >= y,
        ">": lambda x, y: x > y,
    }

    for var, op, valor in restricciones:
        if var not in sustitucion:
            continue  # Variable no sustituida aún

        try:
            valor_var = int(sustitucion[var])
            if not operadores[op](valor_var, valor):
                return False
        except (ValueError, KeyError):
            # Si no se puede convertir a entero, la restricción falla
            return False

    return True


def combinar_extensiones(
    ext1: Extension | None, ext2: Extension | None
) -> Extension | None:
    """Combina dos extensiones, priorizando restricciones y grados."""
    if ext1 is None and ext2 is None:
        return None

    resultado = Extension()

    # Difusa: tomar el mínimo
    if ext1 and ext1.difusa:
        resultado.difusa = ext1.difusa
    if ext2 and ext2.difusa:
        if resultado.difusa:
            valor_difuso = LogicaDifusa.t_min(resultado.difusa.valor, ext2.difusa.valor)
            resultado.difusa = LogicaDifusa(valor_difuso)
        else:
            resultado.difusa = ext2.difusa

    # Precedencia: tomar la mayor
    if ext1 and ext1.precedencia:
        resultado.precedencia = ext1.precedencia
    if ext2 and ext2.precedencia:
        if resultado.precedencia:
            resultado.precedencia = max(resultado.precedencia, ext2.precedencia)
        else:
            resultado.precedencia = ext2.precedencia

    # Restricciones: unir ambas listas
    if ext1 and ext1.restricciones:
        resultado.restricciones.extend(ext1.restricciones)
    if ext2 and ext2.restricciones:
        resultado.restricciones.extend(ext2.restricciones)

    return (
        resultado
        if (resultado.difusa or resultado.precedencia or resultado.restricciones)
        else None
    )


def unificar(
    patron: Tripleta,
    hecho: Tripleta,
    sustitucion: Sustitucion = None,
    extension: Extension = None,
) -> tuple[Sustitucion | None, float]:
    """
    Unifica dos tripletas considerando extensiones (difusa, restricciones).

    Args:
        patron: Tripleta con posibles variables
        hecho: Tripleta concreta
        sustitucion: Sustitución preexistente
        extension: Extensión que puede incluir restricciones

    Returns:
        Tupla (sustitucion, grado_certeza)
        - sustitucion: None si falla, Sustitucion si tiene éxito
        - grado_certeza: 1.0 para booleano, 0.0-1.0 para difuso
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
                return None, 0.0  # Conflicto: la variable ya tenía otro valor
        else:
            # Es un literal: debe coincidir exactamente
            if p_comp != h_comp:
                return None, 0.0  # No coincide

    # Verificar restricciones si existen
    if extension and extension.restricciones:
        if not verificar_restricciones(sustitucion, extension.restricciones):
            return None, 0.0

    # Determinar grado de certeza
    grado = 1.0
    if extension and extension.difusa:
        grado = extension.difusa.valor

    return sustitucion, grado


def consultar(
    patron: Tripleta,
    base: list[tuple[Tripleta, Extension | None]],
    extension: Extension = None,
) -> Iterator[tuple[Sustitucion, float]]:
    """
    Genera sustituciones con sus grados de certeza.

    Args:
        patron: Tripleta patrón
        base: Lista de (tripleta, extension)
        extension: Extensión de la regla que hace la consulta

    Yields:
        Tuplas (sustitucion, grado_certeza)
    """
    for hecho, ext_hecho in base:
        # Combinar extensiones
        ext_combinada = combinar_extensiones(ext_hecho, extension)

        sustitucion, grado = unificar(patron, hecho, None, ext_combinada)

        if sustitucion is not None:
            yield sustitucion, grado


def aplicar(
    regla: Regla,
    hechos: list[tuple[Tripleta, Extension | None]],
    norma: Callable[[float, float], float] = None,
    impl_func: Callable[[float, float], float] = None,
) -> Iterator[tuple[Tripleta, float, Extension | None]]:
    """
    Aplica una regla con soporte para lógica difusa.

    Args:
        regla: Regla a aplicar
        hechos: Base de hechos con extensiones
        t_norma: Función para combinar antecedentes (default: min)
        impl_func: Función de implicación (default: Mamdani)

    Yields:
        Tuplas (tripleta_nueva, grado_certeza, extension)
    """
    if norma is None:
        norma = LogicaDifusa.t_min
    if impl_func is None:
        impl_func = LogicaDifusa.impl_mamdani

    # Generar todas las combinaciones de sustituciones que satisfacen los antecedentes
    for sustitucion, grado_antecedentes in _resolver_antecedentes(
        regla.antecedentes, hechos, regla.extension, norma
    ):
        # Aplicar implicación difusa
        grado_consecuente = 1.0
        if regla.extension and regla.extension.difusa:
            grado_consecuente = regla.extension.difusa.valor

        grado_final = impl_func(grado_antecedentes, grado_consecuente)

        # Crear extensión para el nuevo hecho
        ext_nueva = Extension(difusa=LogicaDifusa(grado_final))

        # Aplicar la sustitución al consecuente
        tripleta_nueva = regla.consecuente.aplicar(sustitucion)

        yield tripleta_nueva, grado_final, ext_nueva


def razona(
    objetivo: Tripleta,
    hechos: list[tuple[Tripleta, Extension | None]],
    reglas: list[Regla],
    umbral_certeza: float = 0.5,
    visitados: set = None,
) -> tuple[bool, float]:
    """
    Encadenamiento hacia atrás: intenta probar un objetivo recursivamente.

    Args:
        objetivo: Tripleta a demostrar (puede contener variables)
        hechos: Base de hechos con extensiones
        reglas: Reglas de inferencia disponibles
        umbral_certeza: Grado mínimo para considerar un hecho como cierto
        visitados: Objetivos ya visitados (para evitar ciclos)

    Returns:
        Tupla (es_demostrable, grado_certeza)

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
        return False, 0.0
    visitados.add(objetivo_str)

    # Caso base: el objetivo está directamente en los hechos
    for hecho, ext in hechos:
        sust, grado = unificar(objetivo, hecho)

        if sust is None:
            continue  # no unifica, sigue

        if grado >= umbral_certeza:
            return True, grado

    # Caso recursivo: buscar reglas que puedan probar el objetivo
    max_grado = 0.0

    for regla in reglas:
        # Intentar unificar el consecuente de la regla con el objetivo
        sustitucion, _ = unificar(regla.consecuente, objetivo)
        if sustitucion is None:
            continue  # Esta regla no aplica

        # Aplicar la sustitución a los antecedentes
        antecedentes_instanciados = [
            ant.aplicar(sustitucion) for ant in regla.antecedentes
        ]

        grado_acumulado = 1.0
        todos_probados = True

        # Intentar probar todos los antecedentes recursivamente
        for antecedente in antecedentes_instanciados:
            probado, grado_ant = razona(
                antecedente, hechos, reglas, umbral_certeza, visitados.copy()
            )

            if not probado:
                todos_probados = False
                break

            grado_acumulado = LogicaDifusa.t_min(grado_acumulado, grado_ant)

        if todos_probados:
            # Aplicar implicación
            if regla.extension and regla.extension.difusa:
                grado_regla = regla.extension.difusa.valor
            else:
                grado_regla = 1.0

            grado_final = LogicaDifusa.impl_mamdani(grado_acumulado, grado_regla)
            max_grado = max(max_grado, grado_final)

            if grado_final >= umbral_certeza:
                return True, grado_final

    return max_grado >= umbral_certeza, max_grado


def _resolver_antecedentes(
    antecedentes: list[Tripleta],
    hechos: list[tuple[Tripleta, Extension | None]],
    extension: Extension | None,
    norma: Callable[[float, float], float],
) -> Iterator[tuple[Sustitucion, float]]:
    """
    Genera todas las sustituciones que satisfacen una lista de antecedentes.

    Es una función recursiva que va componiendo sustituciones:
    - Para el primer antecedente, encuentra todas sus posibles sustituciones
    - Para cada una, intenta resolver el resto de antecedentes
    - Solo devuelve sustituciones que satisfacen TODOS los antecedentes
    """
    if not antecedentes:
        yield Sustitucion(), 1.0  # Caso base: no hay antecedentes que satisfacer
        return

    primer_ant, *resto = antecedentes

    # Resolver el primer antecedente
    for sust_parcial, grado_parcial in consultar(primer_ant, hechos, extension):
        # Aplicar la sustitución parcial al resto de antecedentes
        resto_instanciado = [ant.aplicar(sust_parcial) for ant in resto]

        # Resolver el resto recursivamente
        for sust_resto, grado_resto in _resolver_antecedentes(
            resto_instanciado, hechos, extension, norma
        ):
            # Componer ambas sustituciones
            sust_total = sust_parcial.componer(sust_resto)
            if sust_total is not None:
                # Combinar grados con t-norma
                grado_total = norma(grado_parcial, grado_resto)
                yield sust_total, grado_total


def cargar(
    ruta_archivo: str | Path,
) -> tuple[list[tuple[Tripleta, Extension | None]], list[Regla]]:
    """
    Carga una base de conocimiento desde un archivo.

    Args:
        ruta_archivo: Ruta al archivo de base de conocimiento

    Returns:
        Tupla (hechos, reglas) con el contenido parseado
    """
    hechos = []
    reglas = []

    with Path(ruta_archivo).open("r", encoding="utf-8") as archivo:
        for num_linea, linea in enumerate(archivo, 1):
            linea = linea.strip()

            # Ignorar líneas vacías y comentarios
            if not linea or linea.startswith("#"):
                continue

            try:
                tipo, contenido = _parser.parsear_linea_archivo(linea)

                if tipo == "regla":
                    reglas.append(contenido)
                else:  # 'hecho' o 'tripleta'
                    hechos.append(contenido)

            except ParseException as e:
                advertir_error_sintaxis(num_linea, linea, e.column, e.msg)
            except Exception as e:
                advertir_error_general(num_linea, linea, str(e))

    return hechos, reglas


def descubrir(
    hechos: list[tuple[Tripleta, Extension | None]], reglas: list[Regla]
) -> list[tuple[Tripleta, Extension | None]]:
    """
    Encadenamiento hacia adelante: aplica reglas iterativamente hasta que
    no se puedan deducir más hechos nuevos.

    Args:
        hechos: Hechos base conocidos
        reglas: Reglas de inferencia

    Returns:
        Lista de nuevos hechos con sus extensiones
    """
    # Ordenar reglas por precedencia (mayor precedencia = mayor prioridad)
    reglas_ordenadas = sorted(
        reglas,
        key=lambda r: r.extension.precedencia
        if r.extension and r.extension.precedencia
        else 500,
        reverse=True,
    )

    hechos_totales = hechos.copy()
    hechos_nuevos = []

    # Diccionario para controlar conflictos.
    control_precedencia = {}

    cambio = True
    while cambio:
        cambio = False

        for regla in reglas_ordenadas:
            # Obtener precedencia de la regla actual
            prec_regla = 0
            if regla.extension and regla.extension.precedencia is not None:
                prec_regla = regla.extension.precedencia

            # Aplicar la regla y obtener nuevos consecuentes
            for nuevo_hecho, grado, ext in aplicar(regla, hechos_totales):
                clave_conflicto = (nuevo_hecho.sujeto, nuevo_hecho.predicado)

                if clave_conflicto in control_precedencia:
                    if control_precedencia[clave_conflicto] > prec_regla:
                        continue

                # Verificar si ya existe
                existe = False
                for t_existente, ext_existente in hechos_totales:
                    if t_existente == nuevo_hecho:
                        existe = True
                        # Actualizar grado si es mayor
                        if ext_existente and ext_existente.difusa:
                            if grado > ext_existente.difusa.valor:
                                ext_existente.difusa.valor = grado
                        break

                if not existe:
                    hechos_totales.append((nuevo_hecho, ext))
                    hechos_nuevos.append((nuevo_hecho, ext))
                    
                    # Registramos que esta precedencia
                    control_precedencia[clave_conflicto] = prec_regla
                    cambio = True
                else:
                    # Aunque exista, actualizamos el control si esta regla es válida
                    if clave_conflicto not in control_precedencia:
                        control_precedencia[clave_conflicto] = prec_regla

    return hechos_nuevos


def ejecutar_consulta(
    entrada: str,
    base_conocimiento: list[Tripleta, Extension | None],
    hechos_deducidos: list[Tripleta, Extension | None],
) -> None:
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
                for sust, grado in resultados:
                    if sust:  # Si hay variables asignadas
                        if grado < 1.0:
                            print(f"  {sust} [certeza: {grado:.2f}]")
                        else:
                            print(f"  {sust}")
                    else:  # Consulta sin variables que se cumple
                        if grado < 1.0:
                            print(f"  Sí [certeza: {grado:.2f}]")
                        else:
                            print(f"  Sí")
                print()
            else:
                print("No se encontraron coincidencias.\n")
        else:
            # Consulta sin variables: verificar existencia
            grados = [
                (ext.difusa.valor if ext and ext.difusa else 1.0)
                for tripleta, ext in base_total
                if tripleta == consulta_tripleta
            ]

            if not grados:
                print("No, no está en la base.")
            else:
                g = max(grados)
                if g == 1.0:
                    print("Sí, está en la base.")
                else:
                    print(f"Sí, está en la base. [certeza: {g:.2f}]")

    except ParseException as e:
        print(f"Error de sintaxis: {e.msg}\n")
    except Exception as e:
        print(f"Error al procesar consulta: {e}\n")


def añadir_hecho(
    entrada: str, base_conocimiento: list[tuple[Tripleta, Extension | None]]
) -> None:
    """Añade un hecho a la base de conocimiento."""
    try:
        tripleta, extension = _parser.parsear_afirmacion(entrada)

        # Evitar duplicados exactos
        for h, ext in base_conocimiento:
            if h == tripleta:
                print("El hecho ya existe en la base.\n")
                return

        base_conocimiento.append((tripleta, extension))

        msg = f"Hecho añadido: {tripleta}"
        if extension and (
            extension.difusa or extension.precedencia or extension.restricciones
        ):
            detalles = []
            if extension.difusa is not None:
                detalles.append(f"difusa={extension.difusa}")
            if extension.precedencia is not None:
                detalles.append(f"precedencia={extension.precedencia}")
            if extension.restricciones:
                detalles.append(f"restricciones={len(extension.restricciones)}")
            msg += f" [{'; '.join(detalles)}]"

        print(f"{msg}\n")

    except ParseException as e:
        print(f"Error de sintaxis: {e.msg}\n")
    except Exception as e:
        print(f"Error al añadir hecho: {e}\n")


def revocar_hecho(
    entrada: str, base_conocimiento: list[tuple[Tripleta, Extension | None]]
) -> bool:
    """Elimina un hecho de la base de conocimiento."""
    try:
        tripleta = _parser.parsear_negacion(entrada)

        for i, (hecho, ext) in enumerate(base_conocimiento):
            if hecho == tripleta:
                del base_conocimiento[i]
                return True

        return False

    except ParseException as e:
        print(f"Error de sintaxis: {e.msg}\n")
        return False
    except Exception as e:
        print(f"Error al revocar hecho: {e}\n")
        return False


def mostrar_debug(
    hechos: list[tuple[Tripleta, Extension | None]],
    hechos_deducidos: list[tuple[Tripleta, Extension | None]],
    reglas: list[Regla],
) -> None:
    """Muestra toda la base de conocimiento en memoria."""
    print("\n" + "=" * 50)
    print("BASE DE CONOCIMIENTO EN MEMORIA")
    print("=" * 50)

    print(f"\n--- HECHOS BASE ({len(hechos)}) ---")
    for h, ext in hechos:
        if ext and (ext.difusa or ext.precedencia or ext.restricciones):
            print(f"  {h} {ext}")
        else:
            print(f"  {h}")

    print(f"\n--- HECHOS DEDUCIDOS ({len(hechos_deducidos)}) ---")
    for h, ext in hechos_deducidos:
        if ext and (ext.difusa or ext.precedencia or ext.restricciones):
            print(f"  {h} {ext}")
        else:
            print(f"  {h}")

    print(f"\n--- REGLAS ({len(reglas)}) ---")
    for regla in reglas:
        if regla.extension and (
            regla.extension.difusa
            or regla.extension.precedencia
            or regla.extension.restricciones
        ):
            print(f"  {regla} {regla.extension}")
        else:
            print(f"  {regla}")

    print("=" * 50 + "\n")
