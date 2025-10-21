# sbc/cli.py
import click
from pathlib import Path

@click.command()
def cli():
    """Comando para cargar y mostrar la base de conocimiento"""
    archivo_base_conocimiento = Path(__file__).parent.parent / 'kb' / 'bc.txt'

    try:
        with archivo_base_conocimiento.open('r') as archivo:
            lineas = archivo.readlines()

        # Leer las tripletas (admite sujetos y objetos con varias palabras)
        base_conocimiento = []
        for linea in lineas:
            palabras = linea.strip().split()
            if len(palabras) < 3:
                print(f"Línea no válida (menos de 3 palabras): {linea.strip()}")
                continue

            # El predicado es la palabra del medio
            mitad = len(palabras) // 2
            predicado = palabras[mitad]
            sujeto = " ".join(palabras[:mitad])
            objeto = " ".join(palabras[mitad + 1:])
            base_conocimiento.append((sujeto, predicado, objeto))

        print("Base de conocimiento cargada correctamente.\n")

        # Bucle de interacción
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

            resultados = []

            for (s, p, o) in base_conocimiento:
                if ((sujeto == s or sujeto[0].isupper()) and
                    (predicado == p or predicado[0].isupper()) and
                    (objeto == o or objeto[0].isupper())):

                    sustitucion = {}
                    if sujeto and sujeto[0].isupper():
                        sustitucion[sujeto] = s
                    if predicado and predicado[0].isupper():
                        sustitucion[predicado] = p
                    if objeto and objeto[0].isupper():
                        sustitucion[objeto] = o

                    resultados.append(sustitucion)

            if resultados:
                print("\nResultados encontrados:")
                for r in resultados:
                    for var, valor in r.items():
                        print(f"{var} = {valor}")
                print()
            else:
                print("No se encontraron coincidencias.\n")

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
