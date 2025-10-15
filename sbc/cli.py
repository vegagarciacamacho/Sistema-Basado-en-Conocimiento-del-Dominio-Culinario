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

         # Mostrar las tripletas para verificar
        print("Base de conocimiento cargada:")
        for tripleta in base_conocimiento:
            print(f"{tripleta[0]} {tripleta[1]} {tripleta[2]}")

    except FileNotFoundError:
        print(f"Error: El archivo {archivo_base_conocimiento} no se encuentra.")
    except Exception as e:
        print(f"Ha ocurrido un error: {e}")


cli()
