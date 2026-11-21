"""Pruebas para assign.sortear."""

import json
from pathlib import Path
from app import assign

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def test_sortear_respeta_sexo_y_edad_200_sorteos_por_caso():
    casos = json.loads((DATA_DIR / "casos.json").read_text(encoding="utf-8"))
    assert len(casos) >= 8

    for caso in casos:
        restr = caso["restricciones"]
        sexos_permitidos = set(restr["sexo"])
        edad_min = restr["edad_min"]
        edad_max = restr["edad_max"]

        for _ in range(200):
            c, persona = assign.sortear(caso_id=caso["id"])
            assert c["id"] == caso["id"]
            assert persona["sexo"] in sexos_permitidos, (
                f"Caso {caso['id']}: persona {persona['id']} sexo {persona['sexo']} no en {sexos_permitidos}"
            )
            assert edad_min <= persona["edad"] <= edad_max, (
                f"Caso {caso['id']}: persona {persona['id']} edad {persona['edad']} fuera del rango [{edad_min}, {edad_max}]"
            )


def test_sortear_azar_sin_caso_id():
    """Verifica que sortear sin argumentos funciona y devuelve un caso y persona compatibles."""
    c, p = assign.sortear()
    restr = c["restricciones"]
    assert p["sexo"] in restr["sexo"]
    assert restr["edad_min"] <= p["edad"] <= restr["edad_max"]
