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
        for pregunta in ("¿Con quién vive?", "¿Qué come normalmente?", "¿Hace ejercicio?", "¿A qué se dedica?"):
            mensajes = prompts.mensajes_paciente(peor, caso, [{"role": "user", "content": pregunta}], nivel=cfg)
            total = sum(len(m["content"]) for m in mensajes if m["role"] == "system")
            assert total <= MAX_CHARS_PROMPT, f"{caso['id']} / {pregunta}: {total} caracteres"


def test_prompt_incluye_perfil_y_prohibe_deducir_detalles_laborales():
    persona = next(p for p in json.loads((DATA / "personas.json").read_text(encoding="utf-8")) if p["id"] == "p_102")
    caso = _casos()[0]
    prompt = prompts.system_paciente(persona, caso)
    assert "trabajo: tiendita de alimentos, bebidas y tabaco" in prompt
    assert "Solo si preguntan; manda el caso" in prompt
    assert "No inventes otros datos" in prompt
    assert len(prompts._bloque_perfil_social(persona, caso)) <= 350


def test_el_caso_que_define_trabajo_prevalece_sobre_perfil():
    persona = next(p for p in json.loads((DATA / "personas.json").read_text(encoding="utf-8")) if p["id"] == "p_102")
    caso = next(c for c in _casos() if c["id"] == "c_trauma_01")
    mensajes = prompts.mensajes_paciente(persona, caso, [
        {"role": "assistant", "content": "Vengo por el choque en moto de hoy."},
        {"role": "user", "content": "¿Cuál es su rutina?"},
    ])
    prompt = mensajes[0]["content"]
    assert "trabajo: tiendita de alimentos, bebidas y tabaco" not in prompt
    assert len(mensajes) == 4
    assert "maneja moto todos los días para repartir pedidos" in prompt
    assert "usa solo este dato del caso" in mensajes[-2]["content"]
    assert "maneja moto todos los días para repartir pedidos" in mensajes[-2]["content"]
    assert len(prompt) <= MAX_CHARS_PROMPT


def test_perfil_se_limita_a_la_pregunta_actual():
    persona = next(p for p in json.loads((DATA / "personas.json").read_text(encoding="utf-8")) if p["id"] == "p_102")
    caso = next(c for c in _casos() if c["id"] == "c_trauma_01")
    historial = lambda pregunta: [{"role": "user", "content": pregunta}]
    mensajes_rutina = prompts.mensajes_paciente(persona, caso, historial("¿Cuál es su rutina?"))
    pregunta_social = mensajes_rutina[0]["content"]
    assert "trabajo: tiendita de alimentos, bebidas y tabaco" not in pregunta_social
    assert "actividad:" not in pregunta_social and "come:" not in pregunta_social
    assert "usa solo este dato del caso" in mensajes_rutina[-2]["content"]

    mensajes_hogar = prompts.mensajes_paciente(persona, caso, historial("¿Con quién vive?"))
    pregunta_hogar = mensajes_hogar[0]["content"]
    assert "casa: mamá, papá, abuela, dos primitos" in pregunta_hogar
    assert "solo estos datos" in mensajes_hogar[-2]["content"]

    mensajes_trabajo = prompts.mensajes_paciente(persona, caso, historial("¿A qué se dedica?"))
    pregunta_trabajo = mensajes_trabajo[0]["content"]
    assert "trabajo: tiendita de alimentos, bebidas y tabaco" not in pregunta_trabajo
    assert "usa solo este dato del caso" in mensajes_trabajo[-2]["content"]

    pregunta_clinica = prompts.mensajes_paciente(persona, caso, historial("¿Puede levantar el brazo?"))[0]["content"]
    assert "trabajo: tiendita de alimentos, bebidas y tabaco" not in pregunta_clinica
    assert "Pregunta sobre rutina" not in pregunta_clinica


def test_si_falta_perfil_laboral_se_usa_solo_la_rama_general():
    persona = next(p for p in json.loads((DATA / "personas.json").read_text(encoding="utf-8")) if p["id"] == "p_027")
    caso = next(c for c in _casos() if c["id"] == "c_dengue_01")
    mensajes = prompts.mensajes_paciente(persona, caso, [{"role": "user", "content": "¿A qué se dedica?"}])
    assert persona["perfil"]["trabajo"] is None
    assert "cafetería" not in mensajes[0]["content"].lower()
    assert "Responde exactamente" in mensajes[-2]["content"]
    assert "Mi ocupación es Otras actividades de servicios financieros" in mensajes[-2]["content"]
    assert persona["ocupacion"] in mensajes[-2]["content"]


def test_caso_con_un_dato_de_dieta_no_permita_inventar_comidas():
    persona = next(p for p in json.loads((DATA / "personas.json").read_text(encoding="utf-8")) if p["id"] == "p_029")
    caso = next(c for c in _casos() if c["id"] == "c_trauma_01")
    mensajes = prompts.mensajes_paciente(persona, caso, [{"role": "user", "content": "¿Qué come normalmente?"}])
    assert "come:" not in mensajes[0]["content"]
    assert "no había consumido bebidas alcohólicas antes del choque" in mensajes[-2]["content"]
    assert "No inventes más detalles" in mensajes[-2]["content"]


def test_perfil_omite_temas_que_el_caso_ya_cubre():
    persona = next(p for p in json.loads((DATA / "personas.json").read_text(encoding="utf-8")) if p["id"] == "p_102")
    caso = {"habitos": ["toma refrescos todos los días"], "antecedentes": [], "datos_si_pregunta": {}}
    bloque = prompts._bloque_perfil_social(persona, caso)
    assert "comida:" not in bloque
    assert "casa:" in bloque and "actividad:" in bloque and "trabajo:" in bloque


def test_perfil_no_aparece_si_no_hay_datos_o_en_urgencias():
    persona = next(p for p in json.loads((DATA / "personas.json").read_text(encoding="utf-8")) if p["id"] == "p_102")
    caso = _casos()[0]
    sin_perfil = {**persona, "perfil": None}
    perfil_vacio = {**persona, "perfil": {k: None for k in ("vive_con", "dieta", "actividad_fisica", "trabajo")}}
    assert prompts._bloque_perfil_social(sin_perfil, caso) == ""
    assert prompts._bloque_perfil_social(perfil_vacio, caso) == ""

    urgencia = json.loads((DATA / "urgencias.json").read_text(encoding="utf-8"))[0]
    prompt = prompts.system_paciente(persona, urgencia)
    assert "Estás en urgencias" in prompt
    assert "Solo si preguntan; manda el caso" not in prompt


def test_perfil_no_se_impone_si_caso_define_el_hogar():
    persona = next(p for p in json.loads((DATA / "personas.json").read_text(encoding="utf-8")) if p["id"] == "p_102")
    caso = {"habitos": ["Vive con su familia extendida"], "antecedentes": [], "datos_si_pregunta": {}}
    assert "casa:" not in prompts._bloque_perfil_social(persona, caso)
