# sbc/manejo_errores.py
"""Módulo para el manejo y visualización de errores de sintaxis
en el sistema de bases de conocimiento."""

import warnings

# Códigos ANSI para colores
class Color:
    ROJO = '\033[91m'
    AMARILLO = '\033[93m'
    AZUL = '\033[94m'
    VERDE = '\033[92m'
    RESET = '\033[0m'
    NEGRITA = '\033[1m'


def formatwarning_personalizado(message, category, filename, lineno, line=None):
    """Formato personalizado para warnings con colores y sin información de archivo."""
    return f"{Color.AMARILLO}{category.__name__}:{Color.RESET} {message}\n"


def advertir_error_sintaxis(num_linea: int, texto: str, columna: int = None, mensaje: str = ""):
    """
    Emite un warning de error de sintaxis con formato visual.
    
    Args:
        num_linea: Número de línea donde ocurrió el error.
        texto: Contenido de la línea con error.
        columna: Columna donde se detectó el error (opcional).
        mensaje: Mensaje descriptivo del error.
    """
    # Construir mensaje con indicador visual
    msg_completo = (
        f"\n{Color.AZUL}Línea {num_linea}:{Color.RESET}\n"
        f"  {texto}\n"
    )
    
    if columna is not None:
        espacios = ' ' * (columna - 1)
        msg_completo += (
            f"  {espacios}{Color.ROJO}^{Color.RESET}\n"
            f"  {Color.ROJO}└─ {mensaje}{Color.RESET}"
        )
    else:
        msg_completo += f"  {Color.ROJO}└─ {mensaje}{Color.RESET}"
    
    warnings.warn(msg_completo, SyntaxWarning, stacklevel=2)


def advertir_error_general(num_linea: int, texto: str, mensaje: str):
    """
    Emite un warning de error general (no de sintaxis).
    
    Args:
        num_linea: Número de línea donde ocurrió el error.
        texto: Contenido de la línea con error.
        mensaje: Mensaje descriptivo del error.
    """
    msg_completo = (
        f"\n{Color.AZUL}Línea {num_linea}:{Color.RESET}\n"
        f"  {texto}\n"
        f"  {Color.ROJO}└─ {mensaje}{Color.RESET}"
    )
    
    warnings.warn(msg_completo, RuntimeWarning, stacklevel=2)


# Aplicar el formato personalizado al importar el módulo
warnings.formatwarning = formatwarning_personalizado