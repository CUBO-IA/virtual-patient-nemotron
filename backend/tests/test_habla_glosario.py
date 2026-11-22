"""Estructura del glosario coloquial salvadoreño (borrador) y de la auditoría de habla."""

import importlib.util
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GLOSARIO = ROOT / "data" / "habla_salvadorena.json"
CONFIANZAS = {"alta", "media", "baja"}


def _norm(t: str) -> str:
    t = unicodedata.normalize("NFD", t.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def _cargar():
    return json.loads(GLOSARIO.read_text(encoding="utf-8"))


def _auditor():
    spec = importlib.util.spec_from_file_location("auditar_habla", ROOT / "scripts" / "auditar_habla.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_glosario_estructura():
    g = _cargar()
    assert g["estado"] == "borrador_pendiente_validacion"
    ids = [t["id"] for t in g["terminos"]]
    assert len(ids) == len(set(ids)), "ids de términos repetidos"
    for t in g["terminos"]:
        assert t["evitar"] and all(isinstance(x, str) and x for x in t["evitar"]), t["id"]
        assert t["coloquial"], t["id"]
        for c in t["coloquial"]:
            assert c["texto"] and c["confianza"] in CONFIANZAS, (t["id"], c)


def test_ningun_coloquial_es_un_termino_a_evitar():
    g = _cargar()
    evitar = {_norm(x.rstrip("$")) for t in g["terminos"] for x in t["evitar"]}
    for t in g["terminos"]:
        for c in t["coloquial"]:
            assert _norm(c["texto"]) not in evitar, f"{c['texto']} está como coloquial y como a evitar"


def test_auditoria_detecta_deposiciones_y_respeta_palabra_completa():
    a = _auditor()
    g = a.cargar_glosario()
    hallados = {h["entrada"] for h in a.buscar_terminos("deposiciones líquidas como seis veces al día", g)}
    assert "diarrea" in hallados
    # "presenta$" solo coincide como palabra completa
    assert not a.buscar_terminos("me represento bien", g)
    assert any(h["entrada"] == "registro_clinico" for h in a.buscar_terminos("el paciente presenta fiebre", g))


def test_auditoria_no_marca_lenguaje_coloquial():
    a = _auditor()
    g = a.cargar_glosario()
    assert a.buscar_terminos("tengo cursera, calentura y el cuerpo cortado, doctor", g) == []
