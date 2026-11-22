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


def test_sortear_evitar_casos_recientes_si_hay_alternativas():
    casos = json.loads((DATA_DIR / "casos.json").read_text(encoding="utf-8"))
    nivel = {"id": 1, "casos": {"dificultad_max": 1}}
    elegibles = [c for c in casos if c.get("dificultad", 1) <= 1]
    esperado = elegibles[-1]
    recientes = [c["id"] for c in elegibles if c["id"] != esperado["id"]]
    c, p = assign.sortear(nivel=nivel, casos_recientes=recientes)
    assert c["id"] == esperado["id"]
    assert assign._compatible(p, c)


def test_sortear_repite_si_todos_los_casos_estan_en_la_lista_reciente():
    nivel = {"id": 1, "casos": {"dificultad_max": 1}}
    recientes = [c["id"] for c in json.loads((DATA_DIR / "casos.json").read_text(encoding="utf-8")) if c.get("dificultad", 1) <= 1]
    c, p = assign.sortear(nivel=nivel, casos_recientes=recientes)
    assert c["id"] in recientes and assign._compatible(p, c)
