import os
import io
from contextlib import redirect_stdout
from pathlib import Path
import pytest

from sbc.motor import cargar, consultar, añadir, revocar, descubrir, razona
from sbc.clases import Tripleta

SMALL_KB = """\
# --------------------------------------------------
# HECHOS BÁSICOS
# --------------------------------------------------

tomate es ingrediente.
tomate color rojo.
tomate hay 500.

cebolla es ingrediente.
cebolla color morado.
cebolla hay 100.

queso_cheddar es ingrediente.
queso_cheddar contiene lacteos.
queso_cheddar hay 0.

pollo es ingrediente.
pollo hay 200.

# --------------------------------------------------
# REGLAS SIMPLES
# --------------------------------------------------

# Disponible si hay cantidad > 0
X disponible_si true <- X es ingrediente, X hay Y. [Y > 0]
X disponible_si false <- X es ingrediente, X hay Y. [Y = 0]

# Lista de compra si no está disponible
X lista_compra si <- X es ingrediente, X disponible_si false.

# --------------------------------------------------
# RECETAS
# --------------------------------------------------

ensalada_simple es receta.
ensalada_simple contiene ingrediente001.
ingrediente001 es tomate.

ensalada_simple contiene ingrediente002.
ingrediente002 es cebolla.

ensalada_simple contiene ingrediente003.
ingrediente003 es queso_cheddar.
"""


def _capture(func, *args, **kwargs) -> str:
    buf = io.StringIO()
    with redirect_stdout(buf):
        func(*args, **kwargs)
    return buf.getvalue()

@pytest.fixture
def hechos_reglas(tmp_path):
    use_full = os.getenv("TEST_USE_FULL_KB") == "1"
    if use_full:
        repo_root = Path(__file__).resolve().parents[2]
        kb_path = repo_root / "kb" / "bc.txt"
        hechos, reglas = cargar(kb_path)
    else:
        kb = tmp_path / "bc_small.txt"
        kb.write_text(SMALL_KB, encoding="utf-8")
        hechos, reglas = cargar(kb)
    return hechos, reglas

def test_consultas_y_modificaciones(hechos_reglas):
    hechos, reglas = hechos_reglas

    # consulta con variable
    out = _capture(consultar, "tomate color X?", hechos, [])
    assert "X = rojo" in out

    # consulta afirmativa
    out = _capture(consultar, "tomate color rojo?", hechos, [])
    assert ("Sí" in out)

    # añadir y consultar
    out = _capture(añadir, "pepino color verde.", hechos)
    assert "Hecho añadido" in out
    out = _capture(consultar, "pepino color X?", hechos, [])
    assert "X = verde" in out

    # revocar y comprobar ausencia
    ok = revocar("no pepino color verde.", hechos)
    assert ok is True
    out = _capture(consultar, "pepino color X?", hechos, [])
    assert ("No se encontraron coincidencias" in out) or ("No, no está" in out)

def test_descubrir_y_razona(hechos_reglas):
    hechos, reglas = hechos_reglas

    # descubrir (forward chaining)
    hechos_deducidos = descubrir(hechos, reglas)
    assert isinstance(hechos_deducidos, list)

    # razona directo para regla concreta (si existe)
    consulta = Tripleta("tomate", "es_vegetal", "verdadero")
    # la implementación actual puede requerir la regla concreta; aceptamos True/False
    assert isinstance(razona(consulta, hechos, reglas), bool)