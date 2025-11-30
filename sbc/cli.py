# sbc/cli.py
# Descripción: Interfaz de línea de comandos simplificada

import click
from pathlib import Path
from pyparsing import ParseException

from sbc.motor import (
    cargar, descubrir, razona,
    ejecutar_consulta, añadir_hecho, revocar_hecho, mostrar_debug
)
from sbc.parserSBC import _parser


@click.command()
def cli():
    """Comando para cargar y consultar la base de conocimiento."""
    archivo_bc = Path(__file__).parent.parent / 'kb' / 'bc.txt'

    try:
        # Cargar base de conocimiento
        hechos, reglas = cargar(archivo_bc)
        hechos_deducidos = []

        print("\nBase de conocimiento cargada correctamente.\n")
    
        # Mostrar comandos disponibles
        _mostrar_ayuda()

        # Bucle interactivo
        while True:
            try:
                entrada = input("Entrada: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n\nSesión finalizada.")
                break

            if not entrada:
                continue

            # Procesar comandos
            if entrada in ("salir", "exit", "s"):
                print("Sesión finalizada.")
                break
            
            elif entrada == "cargar!":
                hechos, reglas = cargar(archivo_bc)
                hechos_deducidos = []
                print("Base de conocimiento recargada.\n")
            
            elif entrada == "descubrir!":
                hechos_deducidos = descubrir(hechos, reglas)
                print(f"Descubrimiento completado. "
                      f"{len(hechos_deducidos)} hechos deducidos.\n")
            
            elif entrada == "debug!":
                mostrar_debug(hechos, hechos_deducidos, reglas)
            
            elif '.' in entrada and not entrada.endswith('?'):
                # AÑADIR O REVOCAR HECHOS (con o sin extensión)
                try:
                    if entrada.lower().startswith("no "):
                        if revocar_hecho(entrada, hechos):
                            print("Hecho revocado de la memoria de trabajo.\n")
                        else:
                            print("Hecho no encontrado en la memoria de trabajo.\n")
                    else:
                        añadir_hecho(entrada, hechos)

                except ParseException as e:
                    print(f"Error al procesar hecho: {e}\n")
            
            elif entrada.startswith("razona si"):
                # Razonamiento hacia atrás
                try:
                    consulta_tripleta, _ = _parser.parsear_consulta(entrada)
                    
                    deducido, grado = razona(consulta_tripleta, hechos, reglas)
                    if deducido and grado < 1.0:
                        print(f"Sí, se puede deducir: {consulta_tripleta} "
                              f"con certeza {grado:.2f}\n")
                    elif deducido:
                        print(f"Sí, se puede deducir: {consulta_tripleta}\n")
                    else:
                        print(f"No se puede deducir: {consulta_tripleta}\n")
                        
                except ParseException as e:
                    print(f"Error de sintaxis: {e.msg}\n")
                except Exception as e:
                    print(f"Error al procesar razonamiento: {e}\n")
            
            elif entrada.endswith('?'):
                # Consulta
                ejecutar_consulta(entrada, hechos, hechos_deducidos)
            
            else:
                print("Entrada no reconocida. Use '?' para consultas, "
                      "'.' para hechos, o comandos especiales.\n")

    except FileNotFoundError:
        print(f"Error: El archivo {archivo_bc} no se encuentra.")
    except Exception as e:
        print(f"Ha ocurrido un error: {e}")


def _mostrar_ayuda():
    """Muestra la ayuda de comandos disponibles."""
    print("Comandos disponibles:")
    print('  salir | exit | s       - Salir de la sesión')
    print("  ?                      - Consulta. Ej: 'tomate tipo X?'")
    print("  .                      - Añadir/eliminar. Ej: 'tomate color rojo.'\n")
    
    print("Comandos especiales:")
    print("  cargar!                - Recargar base de conocimiento")
    print("  descubrir!             - Encadenamiento hacia adelante")
    print("  razona si ... ?        - Encadenamiento hacia atrás")
    print("  debug!                 - Mostrar toda la BC en memoria")
    print("-" * 50 + "\n")


if __name__ == "__main__":
    cli()