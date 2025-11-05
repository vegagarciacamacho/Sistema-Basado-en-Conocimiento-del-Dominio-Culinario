# sbc/cli.py
# Descripción: Interfaz de línea de comandos (CLI) basada en click que carga una
#              base de conocimiento desde el archivo kb/bc.txt y permite realizar
#              consultas interactivas en forma de tripletas (sujeto predicado objeto).
#              Soporta consultas con variables (nombres que empiezan por mayúscula)
#              para obtener sustituciones y consultas concretas que responden Sí/No.
#              Utiliza las funciones leer_base_conocimiento y consultar del módulo sbc.motor.


import click
from pathlib import Path
from sbc.motor import cargar, consultar, descubrir, añadir, revocar, debug, razona
from sbc.clases import Tripleta

@click.command()
def cli():
    """Comando para cargar y consultar la base de conocimiento."""
    archivo_base_conocimiento = Path(__file__).parent.parent / 'kb' / 'bc.txt'

    try:
        # Cargar base de conocimiento como listas
        hechos, reglas = cargar(archivo_base_conocimiento)
        hechos_deducidos = []  # se calcularán cuando el usuario pida 'descubrir!'

        print("\nBase de conocimiento cargada correctamente.\n")
    
        # Comandos
        print("Comandos disponibles:")
        print('  salir | exit | s - Salir de la sesión interactiva.')
        print("  ? Consulta un hecho. Ejemplo: 'tomate color rojo?'")
        print("  . Añadir o eliminar hechos. Ejemplo: 'tomate color rojo.' o 'no tomate color rojo.'\n")
        
        # Comandos especiales
        print("Comandos especiales:")
        print("  cargar! - Recargar la base de conocimiento.")
        print("  descubrir! - Aplicar encadenamiento hacia adelante para deducir nuevos hechos.\n")
        print("  razona si - Verificar si una consulta puede ser deducida.")
        print("-" * 50)

        # Bucle interactivo
        while True:
            usuario = input("Entrada: ").strip()
            if not usuario:
                continue

            match usuario:
                
                # Cargar
                case "cargar!":
                    hechos, reglas = cargar(archivo_base_conocimiento)
                    hechos_deducidos = []
                    print("Base de conocimiento recargada.\n")

                # Descubrir
                case "descubrir!":
                    hechos_deducidos = descubrir(hechos, reglas)
                    print(f"Descubrimiento completado. {len(hechos_deducidos)} hechos deducidos.\n")
                
                # Mostrar toda la base de conocimiento
                case "debug!":
                    debug(hechos, hechos_deducidos, reglas)

                # Añadir o eliminar hecho
                case _ if usuario.endswith('.'):

                    # Revocar hecho
                    if usuario.lower().startswith("no "):

                        if revocar(usuario, hechos):
                            print("Hecho revocado de la memoria de trabajo.\n")
                        else:
                            print("Hecho no encontrado en la memoria de trabajo.\n")

                    # Añadir hecho
                    else:
                        añadir(usuario, hechos)

                                # Razonar si
                case _ if usuario.startswith("razona si"):
                    # Eliminar "razona si" y el "?" de la consulta
                    consulta = usuario[len("razona si "):-1].strip()
                    # Crear la tripleta a partir de la consulta
                    sujeto, predicado, objeto = consulta.split()
                    consulta_tripleta = Tripleta(sujeto, predicado, objeto)
                    
                    # Llamar a la función de razonamiento
                    if razona(consulta_tripleta, hechos, reglas):
                        print(f"Sí, se puede deducir: {consulta_tripleta}")
                    else:
                        print(f"No se puede deducir: {consulta_tripleta}")

                # Consultar
                case _ if usuario.endswith('?'):
                    consultar(usuario, hechos, hechos_deducidos)

                # Comando para salir
                case "salir" | "exit" | "s":
                    print("Sesión finalizada.")
                    break  # Salir del bucle

                case _:
                    print("Entrada no reconocida. Use '?' para consultas, '.' para hechos, 'cargar!' o 'descubrir!'.\n")

    except FileNotFoundError:
        print(f"Error: El archivo {archivo_base_conocimiento} no se encuentra.")
    except Exception as e:
        print(f"Ha ocurrido un error: {e}")


if __name__ == "__main__":
    cli()
