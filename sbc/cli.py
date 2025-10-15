#sbc/cli.py
import click
from pathlib import Path

@click.command()
def cli():
    """Comando para cargar y mostrar la base de conocimiento"""
    # Usamos pathlib para manejar la ruta de forma segura
    archivo_base_conocimiento = Path(__file__).parent.parent / 'kb' / 'bc.txt'

    try:
        # Leer el archivo de texto
        with archivo_base_conocimiento.open('r') as archivo:
            lineas = archivo.readlines()

        # Almacenar las líneas leídas en una lista
        base_conocimiento = [] 
        for linea in lineas:
            # Suponiendo que los datos están separados por comas
            tripleta = tuple(linea.strip().split(' '))
            base_conocimiento.append(tripleta)

        # Preguntar por tripleta
        continuar = True
        while continuar:
            usuario = input("Tripleta: ").strip()
            try:
                usuario_tripleta = tuple(usuario.split())
                assert len(usuario_tripleta) == 3, "Debe tener exactamente 3 elementos (sujeto, predicado, objeto)."

                if usuario_tripleta in base_conocimiento:
                    print("Esta en la base de conocimiento\n")
                else:
                    print("No esta en la base de conocimiento\n")

            except AssertionError as e:
                print(f"Error: {e}\n")
            except Exception:
                print("Error: la consulta tiene que tener el formato 'sujeto predicado objeto'.\n")

            # Preguntar si desea continuar
            respuesta = input("¿Deseas terminar la sesión? (s/n): ").strip().lower()
            if respuesta in ("s", "si", "sí"):
                continuar = False
                print("\n Sesión finalizada.")
            
            

    except FileNotFoundError:
        print(f"Error: El archivo {archivo_base_conocimiento} no se encuentra.")
    except Exception as e:
        print(f"Ha ocurrido un error: {e}")


cli()
