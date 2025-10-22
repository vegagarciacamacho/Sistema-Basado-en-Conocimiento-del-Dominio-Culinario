# sbc/cli.py
# Descripción: Interfaz de línea de comandos (CLI) basada en click que carga una
#              base de conocimiento desde el archivo kb/bc.txt y permite realizar
#              consultas interactivas en forma de tripletas (sujeto predicado objeto).
#              Soporta consultas con variables (nombres que empiezan por mayúscula)
#              para obtener sustituciones y consultas concretas que responden Sí/No.
#              Utiliza las funciones leer_base_conocimiento y consultar del módulo sbc.motor.


import click
from pathlib import Path
from sbc.motor import leer_base_conocimiento, consultar

@click.command()
def cli():
    """Comando para cargar y consultar la base de conocimiento."""
    archivo_base_conocimiento = Path(__file__).parent.parent / 'kb' / 'bc.txt'

    try:
        # Cargar base de conocimiento como lista (podrías dejarlo como generador si prefieres)
        base_conocimiento = list(leer_base_conocimiento(archivo_base_conocimiento))
        print("Base de conocimiento cargada correctamente.\n")

        # Bucle interactivo
        while True:
            usuario = input("Consulta (sujeto predicado objeto): ").strip()
            if not usuario:
                continue

            palabras = usuario.split()
            if len(palabras) < 2:
                print("Error: la consulta debe tener al menos 2 palabras.\n")
                continue

            # Si el usuario no pone objeto, asumimos una variable por defecto
            if len(palabras) == 2:
                palabras.append("X")

            mitad = len(palabras) // 2
            predicado = palabras[mitad]
            sujeto = " ".join(palabras[:mitad])
            objeto = " ".join(palabras[mitad + 1:])

            # Verificamos si hay variables
            tiene_variables = (
                sujeto[0].isupper() or predicado[0].isupper() or objeto[0].isupper()
            )

            if tiene_variables:
                resultados = list(consultar(base_conocimiento, sujeto, predicado, objeto))
                if resultados:
                    print("\nResultados encontrados:")
                    for r in resultados:
                        for var, valor in r.items():
                            print(f"{var} = {valor}")
                    print()
                else:
                    print("No se encontraron coincidencias.\n")
            else:
                # Consulta concreta: respuesta Sí / No
                if (sujeto, predicado, objeto) in base_conocimiento:
                    print("Sí, está en la base de conocimiento.\n")
                else:
                    print("No, no está en la base de conocimiento.\n")

            # Preguntar si desea continuar
            respuesta = input("¿Deseas terminar la sesión? (s/n): ").strip().lower()
            if respuesta in ("s", "si", "sí"):
                print("\nSesión finalizada.")
                break

    except FileNotFoundError:
        print(f"Error: El archivo {archivo_base_conocimiento} no se encuentra.")
    except Exception as e:
        print(f"Ha ocurrido un error: {e}")


if __name__ == "__main__":
    cli()
