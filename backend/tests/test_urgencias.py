"""Modo Urgencias (URGENCIAS.md). No necesita Ollama."""
import json
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app import config, prompts, sessions, urgencias
from app.main import app

client = TestClient(app)
ROOT = Path(__file__).resolve().parents[2]
IDS = [c["id"] for c in json.loads((ROOT / "data" / "urgencias.json").read_text(encoding="utf-8"))]
OCULTOS = ("signos_activos", "accion_esperada", "datos_ocultos", "explicacion", "diagnostico", "lista_verificacion", "banderas_rojas", "keywords")


@pytest.fixture(autouse=True)
def _demo(monkeypatch):
    monkeypatch.setattr(config, "SEGUIMIENTO_DEMO", True)


async def _stream_falso(messages, temperature=0.7, num_predict=120):
    for tok in ("Me ", "duele."):
        yield tok


def _crear(caso_id="u_infarto_01"):
    r = client.post("/api/sessions", json={"modo": "urgencias", "caso_id": caso_id})
    assert r.status_code == 200, r.text
    return r.json()


def _preguntar(sid, texto):
    with patch("app.llm.stream_chat", _stream_falso):
        return client.post(f"/api/sessions/{sid}/chat", json={"message": texto})


def _con_preguntas(sid, *preguntas):
    s = sessions.get(sid)
    s.mensajes = [{"role": "user", "content": q} for q in preguntas]
    sessions.guardar(s)
    return s


def _triaje(sid, prioridad, accion):
    return client.post(f"/api/sessions/{sid}/triaje", json={"prioridad": prioridad, "accion": accion})


# ---------------------------------------------------------------- acceso y datos públicos

@pytest.mark.parametrize("caso_id", IDS)
def test_todos_los_casos_arrancan_y_no_exponen_nada_oculto(caso_id):
    data = _crear(caso_id)
    texto = json.dumps(data, ensure_ascii=False)
    for k in OCULTOS:
        assert k not in texto, k
    assert data["modo"] == "urgencias" and data["tiempo_limite_seg"] > 0 and data["max_preguntas"] > 0
    assert set(data) >= {"session_id", "paciente", "motivo_consulta", "preguntas_minimas_semaforo"}


def test_requiere_demo_o_caso_validado(monkeypatch):
    monkeypatch.setattr(config, "SEGUIMIENTO_DEMO", False)
    assert client.post("/api/sessions", json={"modo": "urgencias"}).status_code == 403
    assert client.get("/api/health").json()["urgencias"] is False
    caso_validado = {"revision_clinica": {"estado": "validado"}}
    assert urgencias.habilitado(caso_validado) is True
    assert urgencias.habilitado({"revision_clinica": {"estado": "pendiente"}}) is False


def test_health_indica_si_urgencias_esta_disponible():
    assert client.get("/api/health").json()["urgencias"] is True


def test_modo_y_caso_invalidos():
    assert client.post("/api/sessions", json={"modo": "otro"}).status_code == 422
    assert client.post("/api/sessions", json={"modo": "urgencias", "caso_id": "no_existe"}).status_code == 404


def test_el_modo_consulta_no_cambia():
    r = client.post("/api/sessions", json={"nivel": 1})
    assert r.status_code == 200 and "tiempo_limite_seg" not in r.json()


def test_prompt_agrega_el_bloque_sin_filtrar_diagnostico_ni_prioridad():
    s = sessions.get(_crear()["session_id"])
    prompt = prompts.system_paciente(s.persona, s.caso, s.nivel)
    assert "Estás en urgencias" in prompt and "máximo 12 palabras" in prompt
    assert "Nunca digas qué enfermedad" in prompt
    assert s.caso["diagnostico"].lower() not in prompt.lower()
    assert "rojo" not in prompt.lower().replace("corrojo", "") and "emergencias" not in prompt.lower()
    assert "Tu hija te acompaña" in prompt  # u_infarto_01 tiene acompañante


# ---------------------------------------------------------------- límites (servidor)

def test_limite_de_preguntas():
    sid = _crear()["session_id"]
    maximo = sessions.get(sid).caso["urgencia"]["max_preguntas"]
    _con_preguntas(sid, *[f"pregunta {i}" for i in range(maximo)])
    r = _preguntar(sid, "una más")
    assert r.status_code == 409 and "límite" in r.json()["detail"]


def test_limite_de_tiempo_con_el_reloj_del_servidor():
    sid = _crear()["session_id"]
    assert _preguntar(sid, "¿Desde cuándo?").status_code == 200
    s = sessions.get(sid)
    s.iniciada_en = time.time() - s.caso["urgencia"]["tiempo_limite_seg"] - 1
    sessions.guardar(s)
    r = _preguntar(sid, "¿Y ahora?")
    assert r.status_code == 409 and "tiempo" in r.json()["detail"]


def test_maximo_de_dos_pistas():
    sid = _crear()["session_id"]
    s = sessions.get(sid)
    s.pistas_usadas = urgencias.MAX_PISTAS
    sessions.guardar(s)
    assert client.post(f"/api/sessions/{sid}/pista").status_code == 409


# ---------------------------------------------------------------- triaje

def test_triaje_exige_minimo_de_preguntas_valores_validos_y_es_unico():
    sid = _crear()["session_id"]
    assert _triaje(sid, "rojo", "emergencias").status_code == 409  # 0 preguntas
    _con_preguntas(sid, "¿Desde cuándo?", "¿Le cuesta respirar?", "¿Dónde le duele?")
    assert _triaje(sid, "naranja", "emergencias").status_code == 422
    assert _triaje(sid, "rojo", "nada").status_code == 422
    assert _triaje(sid, "rojo", "emergencias").status_code == 200
    assert _triaje(sid, "rojo", "emergencias").status_code == 409  # no se puede cambiar
    assert _preguntar(sid, "¿Algo más?").status_code == 409  # la consulta terminó


def test_triaje_en_sesion_de_consulta_normal_da_404():
    sid = client.post("/api/sessions", json={"nivel": 1}).json()["session_id"]
    assert _triaje(sid, "rojo", "emergencias").status_code == 404


@pytest.mark.parametrize("elegida,correcta,esperado", [
    ("rojo", "rojo", 50), ("amarillo", "amarillo", 50), ("verde", "verde", 50),
    ("rojo", "amarillo", 25), ("rojo", "verde", 25), ("amarillo", "verde", 25),
    ("verde", "rojo", 0), ("verde", "amarillo", 0), ("amarillo", "rojo", 0),
])
def test_tabla_de_prioridad(elegida, correcta, esperado):
    assert urgencias.puntaje_prioridad(elegida, correcta) == esperado


def test_signos_y_esenciales_se_detectan_con_las_keywords():
    sid = _crear("u_infarto_01")["session_id"]
    _con_preguntas(sid, "¿Desde cuándo le duele el pecho?", "¿Está sudando frío?", "¿Le cuesta respirar?")
    r = _triaje(sid, "rojo", "emergencias").json()
    assert "Presión fuerte en el pecho" in r["signos"]["encontrados"]
    assert "Sudor frío" in r["signos"]["encontrados"]
    assert "Dolor que se va al brazo o a la mandíbula" in r["signos"]["faltantes"]
    assert "Cuándo empezó el dolor" in r["preguntas_esenciales"]["hechas"]
    assert r["desglose"]["prioridad"] == 50 and r["desglose"]["signos"] == 20
    assert 0 <= r["puntaje"] <= 100 and r["explicacion"]


def test_minimizar_la_urgencia_da_cero_y_alerta_de_seguridad():
    sid = _crear("u_infarto_01")["session_id"]
    _con_preguntas(sid, "¿Desde cuándo?", "¿Le duele el pecho?", "¿Siente sudor frío?")
    r = _triaje(sid, "verde", "consulta_normal").json()
    assert r["desglose"]["prioridad"] == 0
    assert r["alerta_seguridad"] and r["aprobado"] is False


def test_accion_menos_urgente_de_lo_esperado_tambien_alerta():
    sid = _crear("u_infarto_01")["session_id"]
    _con_preguntas(sid, "¿Desde cuándo?", "¿Le duele el pecho?", "¿Siente sudor frío?")
    r = _triaje(sid, "rojo", "evaluacion_pronto").json()
    assert r["desglose"]["prioridad"] == 50 and r["alerta_seguridad"] and r["aprobado"] is False


def test_pasarse_de_prudente_no_alerta():
    sid = _crear("u_gastro_leve_01")["session_id"]
    _con_preguntas(sid, "¿Desde cuándo?", "¿Ha visto sangre?", "¿Toma líquidos?")
    r = _triaje(sid, "amarillo", "evaluacion_pronto").json()
    assert r["desglose"]["prioridad"] == 25 and r["alerta_seguridad"] is None


def test_caso_verde_sin_signos_otorga_los_puntos_de_signos_completos():
    sid = _crear("u_gastro_leve_01")["session_id"]
    _con_preguntas(sid, "¿Desde cuándo?", "¿Ha visto sangre?", "¿Toma líquidos?", "¿Orina normal?", "¿Fiebre?")
    r = _triaje(sid, "verde", "consulta_normal").json()
    assert r["signos"] == {"encontrados": [], "faltantes": []}
    assert r["desglose"]["signos"] == 30
    assert r["puntaje"] >= 90 and r["aprobado"] is True and r["alerta_seguridad"] is None


def test_rapidez_y_pistas_en_el_puntaje():
    sid = _crear("u_gastro_leve_01")["session_id"]
    s = _con_preguntas(sid, "¿Desde cuándo?", "¿Ha visto sangre?", "¿Toma líquidos?")
    limite = s.caso["urgencia"]["tiempo_limite_seg"]
    rapido = urgencias.calcular_triaje(s, "verde", "consulta_normal", ahora=s.iniciada_en)
    lento = urgencias.calcular_triaje(s, "verde", "consulta_normal", ahora=s.iniciada_en + limite)
    assert rapido["desglose"]["rapidez"] == 10 and lento["desglose"]["rapidez"] == 0
    s.pistas_usadas = 5  # solo cuentan 2
    con_pistas = urgencias.calcular_triaje(s, "verde", "consulta_normal", ahora=s.iniciada_en)
    assert con_pistas["desglose"]["pistas"] == -2 * urgencias.PENALIZACION_PISTA
    assert con_pistas["puntaje"] == rapido["puntaje"] - 10


# ---------------------------------------------------------------- persistencia y validador

def test_la_sesion_de_urgencias_sobrevive_a_un_reinicio():
    sid = _crear()["session_id"]
    s = sessions.get(sid)
    s.mensajes = [m for q in ("¿Desde cuándo?", "¿Le duele el pecho?", "¿Siente sudor frío?")
                  for m in ({"role": "user", "content": q}, {"role": "assistant", "content": "Me duele."})]
    sessions.guardar(s)
    iniciada = s.iniciada_en
    sessions._store.clear()  # reinicio del servidor
    s = sessions.get(sid)
    assert s is not None and s.modo == "urgencias" and s.iniciada_en == iniciada
    assert s.caso["id"] == "u_infarto_01" and s.preguntas_usadas == 3
    assert _triaje(sid, "rojo", "emergencias").status_code == 200
    sessions._store.clear()
    assert sessions.get(sid).triaje["prioridad_elegida"] == "rojo"


def test_validador_de_urgencias():
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate_urgencias.py")], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_todos_los_casos_siguen_pendientes_de_revision():
    for c in json.loads((ROOT / "data" / "urgencias.json").read_text(encoding="utf-8")):
        assert c["revision_clinica"] == {"estado": "pendiente", "revisado_por": None, "fecha": None, "fuente": None}
