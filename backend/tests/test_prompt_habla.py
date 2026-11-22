"""Prompt del paciente: habla salvadoreña natural, primera persona y expresiones por caso."""

import json
from pathlib import Path
from unittest.mock import patch

from app import assign, habla, niveles, prompts

DATA = Path(__file__).resolve().parents[2] / "data"
PALABRAS_FORZADAS = ["ruco", "cipote", "pisto", "chivo", "chunche", "chucho"]
# Tope del prompt de sistema en el peor caso (persona con ocupación larga, nivel 3).
# Medido con qwen2.5:7b: ≈3,9 caracteres por token, así que 4800 caracteres ≈ 1320 tokens. Con num_ctx=2048
# quedan ≈750 para el historial (12 mensajes ≈ 400) y la respuesta (180). Medido en el peor caso: 1939 de 2048.
# Si necesitas más reglas, recorta otras o sube NUM_CTX; no subas este número sin pensarlo.
MAX_CHARS_PROMPT = 4800


def _casos():
    return json.loads((DATA / "casos.json").read_text(encoding="utf-8"))


def _persona():
    return json.loads((DATA / "personas.json").read_text(encoding="utf-8"))[0]


def _prompt(caso):
    return prompts.system_paciente(_persona(), caso, niveles.obtener_nivel(2))


def test_prompt_exige_primera_persona_y_registro_cotidiano():
    p = _prompt(_casos()[0])
    assert "primera persona" in p
    assert "Nunca hables de ti en tercera persona" in p
    assert "Vengo por" in p
    assert "deposiciones" in p  # figura como ejemplo de lo que NO se debe decir


def test_prompt_ya_no_incluye_ejemplo_del_vos_con_el_hijo_ni_palabras_forzadas():
    for caso in _casos():
        p = _prompt(caso).lower()
        assert "mi hijo: vos" not in p
        for w in PALABRAS_FORZADAS:
            assert w not in p, f"'{w}' no debe forzarse en el prompt ({caso['id']})"


def test_ahorita_se_limita_a_ahora_mismo():
    p = _prompt(_casos()[0])
    assert "«Ahorita» es solo «ahora mismo»" in p
    assert "«ayer», «anoche»" in p


def test_expresiones_regionales_dependen_del_caso():
    por_id = {c["id"]: c for c in _casos()}
    gea = habla.expresiones_para_caso(por_id["c_gea_01"])
    dengue = habla.expresiones_para_caso(por_id["c_dengue_01"])
    assert "cursera" in gea
    assert "calentura" in dengue and "cursera" not in dengue
    for caso in por_id.values():
        assert len(habla.expresiones_para_caso(caso)) <= 3


def test_expresiones_aparecen_en_el_prompt_del_caso():
    gea = next(c for c in _casos() if c["id"] == "c_gea_01")
    assert "«cursera»" in _prompt(gea)


def test_expresiones_solo_incluyen_regionales_de_confianza_alta():
    glosario = json.loads((DATA / "habla_salvadorena.json").read_text(encoding="utf-8"))
    permitidas = {c["texto"] for t in glosario["terminos"] for c in t["coloquial"]
                  if c.get("regional") and c["confianza"] == "alta"}
    for caso in _casos():
        for e in habla.expresiones_para_caso(caso):
            assert e in permitidas


def test_sin_glosario_el_prompt_sigue_funcionando():
    habla._glosario_coloquial.cache_clear()
    try:
        with patch("app.habla.config.DATA_DIR", Path("/no/existe")):
            habla._glosario_coloquial.cache_clear()
            assert habla.expresiones_para_caso(_casos()[0]) == []
            assert "Hablas español salvadoreño" in _prompt(_casos()[0])
    finally:
        habla._glosario_coloquial.cache_clear()


def test_tamano_del_prompt_cabe_en_el_contexto():
    """Determinista: peor caso = persona con la ocupación y el estilo más largos."""
    personas = json.loads((DATA / "personas.json").read_text(encoding="utf-8"))
    peor = max(personas, key=lambda p: len(p["ocupacion"]) + len(p["estilo"]) + len(p["municipio"]))
    cfg = niveles.obtener_nivel(3)  # el nivel 3 añade la línea de actitud: es el más largo
    for caso in _casos():
        largo = max(len(prompts.system_paciente(peor, caso, cfg, turno=t)) for t in (0, 1, 2))
        assert largo <= MAX_CHARS_PROMPT, f"{caso['id']}: {largo} caracteres (máx. {MAX_CHARS_PROMPT})"
