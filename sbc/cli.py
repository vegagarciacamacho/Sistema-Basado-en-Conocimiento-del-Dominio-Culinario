# sbc/cli.py
import click
from pathlib import Path


def leer_base_conocimiento(ruta_archivo):
    """
    Generador que lee tripletas de la base de conocimiento.
    Devuelve una tripleta (sujeto, predicado, objeto) por cada línea válida.
    """
    with ruta_archivo.open('r') as archivo:
        for linea in archivo:
            palabras = linea.strip().split()
            if len(palabras) < 3:
                print(f"Línea no válida (menos de 3 palabras): {linea.strip()}")
                continue

            # El predicado es la palabra del medio
            mitad = len(palabras) // 2
            predicado = palabras[mitad]
            sujeto = " ".join(palabras[:mitad])
            objeto = " ".join(palabras[mitad + 1:])

            yield (sujeto, predicado, objeto)


def consultar(base_conocimiento, sujeto, predicado, objeto):
    """
    Generador que produce resultados de consulta.
    Devuelve diccionarios con las sustituciones de variables.
    """
    for (s, p, o) in base_conocimiento:
        if ((sujeto == s or sujeto[0].isupper()) and
            (predicado == p or predicado[0].isupper()) and
            (objeto == o or objeto[0].isupper())):

            sustitucion = {}
            if sujeto[0].isupper():
                sustitucion[sujeto] = s
            if predicado[0].isupper():
                sustitucion[predicado] = p
            if objeto[0].isupper():
                sustitucion[objeto] = o

            yield sustitucion


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
