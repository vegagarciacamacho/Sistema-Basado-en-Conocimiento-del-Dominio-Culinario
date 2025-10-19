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
            # Los datos se separan por espacios
            palabras = linea.strip().split()
            #Si la línea tiene menos de tres palabras no es válida
            if len(palabras) < 3:
                print(f"Linea no valida")
            else:
                # Dividimos la tripleta en Sujeto-Predicado-Objeto
                # El predicado es la palabra del medio 
                mitad = len(palabras) // 2
                predicado = palabras[mitad]

                # El sujeto son las palabras de antes del predicado
                sujeto = " ".join(palabras[:mitad])

                # El objeto son las palabras de después del predicado
                objeto = " ".join(palabras[mitad + 1:])

                tripleta = (sujeto, predicado, objeto)
                base_conocimiento.append(tripleta)

        # Preguntar por tripleta
        continuar = True
        while continuar:
            usuario = input("Tripleta: ").strip()
            try:
                palabras = usuario.split()
                # Comprobamos que la tripleta tenga las palabras suficientes
                if len(palabras) < 3:
                    raise AssertionError("Debe tener al menos 3 palabras")
                
                # Volvemos a comprobar las palabras de la tripleta
                mitad = len(palabras) // 2
                predicado = palabras[mitad]
                sujeto = " ".join(palabras[:mitad])
                objeto = " ".join(palabras[mitad + 1: ])
                usuario_tripleta = (sujeto, predicado, objeto)

                if usuario_tripleta in base_conocimiento:
                    print("Está en la base de conocimiento\n")
                else:
                    print("No está en la base de conocimiento\n")

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
