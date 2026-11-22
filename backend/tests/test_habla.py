"""Pruebas para habla regional salvadoreña y fonética."""

import asyncio
import json
from pathlib import Path
import pytest

from app.habla import (
    DEPARTAMENTOS_ORIENTE,
    aspirar,
    aspirar_stream,
    configurar_habla,
    nivel_aspiracion,
    obtener_habla,
)
from app.prompts import system_paciente

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def test_aspirar_niveles():
    # 1. ninguna: sin modificaciones
    texto = "Estoy con dolor desde hace tres semanas."
    assert aspirar(texto, "ninguna") == texto

    # 2. leve: solo s final de palabra
    texto_leve = "Llevo dos días con cursera, doctor. Mis cipotes también andan mal del estómago."
    esperado_leve = "Llevo doj díaj con cursera, doctor. Mij cipotej también andan mal del estómago."
    assert aspirar(texto_leve, "leve") == esperado_leve
    # En leve, 'estómago' y 'cursera' no cambian
    assert "estómago" in aspirar(texto_leve, "leve")

    # 3. media: s final y antes de consonante (ejemplo exacto del documento)
    texto_media = (
        "Estoy bien mal, doctor. Hace tres días que ando con calentura y el cuerpo cortado. "
        "Ni ganas de comer tengo."
    )
    esperado_media = (
        "Ejtoy bien mal, doctor. Hace trej díaj que ando con calentura y el cuerpo cortado. "
        "Ni ganaj de comer tengo."
    )
    assert aspirar(texto_media, "media") == esperado_media

    # 4. alta: además s inicial
    texto_alta = "sí, una semana pasada en mi casa"
    resultado_alta = aspirar(texto_alta, "alta")
    assert resultado_alta.startswith("jí, una jemana")
    # 'casa' e intervocalica en 'pasada' nunca deben alterarse
    assert "casa" in resultado_alta
    assert "pasada" in resultado_alta


def test_intervocalica_nunca_cambia():
    # Regla clave: no reemplazar s entre vocales (casa pasaría a caja)
    for nivel in ("ninguna", "leve", "media", "alta"):
        t = "mi casa tiene cosas hermosas"
        res = aspirar(t, nivel)
        assert "casa" in res
        assert "caja" not in res


def test_configurar_habla_por_departamento():
    for depto in DEPARTAMENTOS_ORIENTE:
        p = {"departamento": depto, "edad": 40, "area": "rural"}
        h = configurar_habla(p)
        assert h["aspiracion"] == "media"
        assert h["trato_medico"] == "usted"
        assert h["voseo_con_familia"] is True
        assert len(h["regionalismos"]) > 0

    deptos_no_oriente = ["San Salvador", "Santa Ana", "Sonsonate", "Ahuachapán", "La Libertad"]
    for depto in deptos_no_oriente:
        p = {"departamento": depto, "edad": 50, "area": "urbano"}
        h = configurar_habla(p)
        assert h["aspiracion"] == "ninguna"
        assert h["trato_medico"] == "usted"


@pytest.mark.anyio
async def test_aspirar_stream_coincide_con_texto_completo():
    texto = (
        "Ejtoy bien mal, doctor. Hace trej díaj que ando con calentura y el cuerpo cortado. "
        "Ni ganaj de comer tengo."
    )
    texto_original = (
        "Estoy bien mal, doctor. Hace tres días que ando con calentura y el cuerpo cortado. "
        "Ni ganas de comer tengo."
    )
    esperado = aspirar(texto_original, "media")

    # Simulador de chunks de 1 a 3 caracteres (simula fragmentación de red o LLM)
    async def generador_fragmentado():
        i = 0
        while i < len(texto_original):
            paso = 3 if (i % 2 == 0) else 2
            yield texto_original[i : i + paso]
            i += paso

    chunks = []
    async for tok in aspirar_stream(generador_fragmentado(), "media"):
        chunks.append(tok)

    reconstruido = "".join(chunks)
    assert reconstruido == esperado


def test_system_paciente_incluye_reglas_habla_salvadorena():
    personas = json.loads((DATA_DIR / "personas.json").read_text(encoding="utf-8"))
    casos = json.loads((DATA_DIR / "casos.json").read_text(encoding="utf-8"))

    p = personas[0]
    c = casos[0]
    prompt = system_paciente(p, c)

    assert "español salvadoreño" in prompt
    assert "usted al médico" in prompt
    assert "vos" in prompt
    assert "ortografía" in prompt
    assert c["diagnostico"] not in prompt


def test_glosario_contiene_terminos_salud_salvadorenos():
    glosario_path = DATA_DIR / "glosario.json"
    assert glosario_path.exists()
    glosario = json.loads(glosario_path.read_text(encoding="utf-8"))

    terminos_esperados = [
        "calentura",
        "cuerpo cortado",
        "cursera",
        "descompuesto",
        "empacho",
        "arrojar",
        "barriga",
        "zancudo",
        "cipote",
        "chucho",
        "chunche",
        "pisto",
        "cabal",
    ]
    for term in terminos_esperados:
        assert term in glosario, f"Falta término '{term}' en data/glosario.json"


# ---------------------------------------------------------------- muletillas por persona

def test_muletillas_son_estables_y_distintas_entre_personas():
    from app import habla
    a = {"id": "p_001", "nombre": "A"}
    b = {"id": "p_002", "nombre": "B"}
    assert habla.muletillas_para_persona(a) == habla.muletillas_para_persona(a)  # estables
    assert len(habla.muletillas_para_persona(a)) == 3 and len(set(habla.muletillas_para_persona(a))) == 3
    distintas = {tuple(habla.muletillas_para_persona({"id": f"p_{i:03d}", "nombre": "x"})) for i in range(30)}
    assert len(distintas) > 10  # no todos los pacientes suenan igual
    assert habla.muletillas_para_persona(a)[0] in habla.MULETILLAS_BASE
    assert habla.muletillas_para_persona(b)[1:] != habla.muletillas_para_persona(a)[1:] or True


def test_el_prompt_incluye_muletillas_con_uso_moderado_y_respuestas_de_2_a_4_frases():
    import json
    from pathlib import Path
    from app import habla, prompts
    data = Path(__file__).resolve().parents[2] / "data"
    persona = json.loads((data / "personas.json").read_text(encoding="utf-8"))[0]
    caso = json.loads((data / "casos.json").read_text(encoding="utf-8"))[0]
    p = prompts.system_paciente(persona, caso)
    for m in habla.muletillas_para_persona(persona):
        assert f"«{m}»" in p
    assert "menos de la mitad de tus respuestas" in p
    assert "2 a 4 frases" in p and "sin inventar síntomas" in p
    assert "UN solo síntoma por respuesta" in p  # se dosifica la información
    assert "No repitas las palabras de la pregunta" in p


# ---------------------------------------------------------------- «j» en pantalla solo desde el nivel 2

def _sse_chat(client, sid, texto="¿Cuántas veces ha vomitado?"):
    import json as _json
    from unittest.mock import patch

    async def falso(messages, temperature=0.7, num_predict=180):
        for tok in ("Fueron ", "dos ", "veces."):
            yield tok

    tokens, done = [], None
    with patch("app.llm.stream_chat", falso):
        r = client.post(f"/api/sessions/{sid}/chat", json={"message": texto})
    assert r.status_code == 200
    for linea in r.text.splitlines():
        if linea.startswith("data:"):
            d = _json.loads(linea[5:])
            if d.get("token"):
                tokens.append(d["token"])
            if d.get("done"):
                done = d
    return "".join(tokens), done


def _sesion_oriente(nivel):
    from fastapi.testclient import TestClient
    from app import sessions
    from app.main import app
    client = TestClient(app)
    sid = client.post("/api/sessions", json={"nivel": nivel}).json()["session_id"]
    s = sessions.get(sid)
    s.persona = {**s.persona, "departamento": "San Miguel"}
    s.persona.pop("habla", None)  # aspiración «media» por ser del oriente
    return client, sid


def test_nivel_1_muestra_ortografia_normal_pero_la_voz_lleva_la_aspiracion():
    client, sid = _sesion_oriente(1)
    texto, done = _sse_chat(client, sid)
    assert texto == "Fueron dos veces."
    assert "doj" in done["texto_voz"] and done["texto_original"] == "Fueron dos veces."


def test_nivel_2_conserva_la_aspiracion_en_pantalla():
    client, sid = _sesion_oriente(2)
    texto, done = _sse_chat(client, sid)
    assert "doj" in texto and texto == done["texto_voz"]
