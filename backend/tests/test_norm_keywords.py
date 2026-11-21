"""Pruebas para norm() y el matching de keywords según AGENTS.md."""

import json
from pathlib import Path
from app.evaluate import norm, _hit

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def test_norm_tildes_y_mayusculas():
    raw = "¿CUÁNDO empezó la FIEBRE y los VÓMITOS?"
    res = norm(raw)
    assert res == " cuando empezo la fiebre y los vomitos "
    # Sin tildes
    for char in ["á", "é", "í", "ó", "ú", "Á", "É", "Í", "Ó", "Ú"]:
        assert char not in res


def test_norm_caracteres_especiales():
    raw = "¡Hola! ¿Tiene dolor (de cabeza) / mareos...?"
    res = norm(raw)
    assert res == " hola tiene dolor de cabeza mareos "


def test_keyword_prefix_matching():
    # 'viaj' detecta 'viajó', 'viajado', 'viajes'
    texto = norm("El paciente viajó al campo el mes pasado")
    assert _hit(["viaj"], texto)

    texto2 = norm("Ha realizado varios viajes recientemente")
    assert _hit(["viaj"], texto2)

    # Pero no debe detectar si 'viaj' está a la mitad de una palabra sin espacio previo
    texto3 = norm("desviaje o extraviaje")
    assert not _hit(["viaj"], texto3)


def test_pie_y_palabras_reales():
    """Verifica que palabras como 'pierna' o 'piel' no coincidan por error

    con keywords no deseadas, y que las keywords reales de los casos no generen falsos positivos.
    """
    casos = json.loads((DATA_DIR / "casos.json").read_text(encoding="utf-8"))

    # En c_erc_01 la keyword para hinchazón es 'pies', no 'pie'
    caso_erc = next(c for c in casos if c["id"] == "c_erc_01")
    kw_hinchazon = next(it["keywords"] for it in caso_erc["lista_verificacion"] if it["id"] == "hinchazon")
    assert "pies" in kw_hinchazon
    assert "pie" not in kw_hinchazon  # No se usa 'pie' para evitar falsos positivos con 'pierna' o 'piel'

    texto_pierna = norm("¿Siente dolor o pesadez en la pierna?")
    # Preguntar por 'pierna' no debe cumplir hinchazón de 'pies'
    assert not _hit(["pies"], texto_pierna)

    # En c_dengue_01 la keyword es 'piel'
    caso_dengue = next(c for c in casos if c["id"] == "c_dengue_01")
    kw_piel = next(it["keywords"] for it in caso_dengue["lista_verificacion"] if it["id"] == "piel")
    assert "piel" in kw_piel
    # 'piel' no debe coincidir con 'pierna' ni con 'pies'
    assert not _hit(kw_piel, texto_pierna)

    texto_piel = norm("¿Le han salido ronchas en la piel?")
    assert _hit(kw_piel, texto_piel)

    texto_pies = norm("Se le hinchan los pies al final del día")
    assert _hit(kw_hinchazon, texto_pies)
