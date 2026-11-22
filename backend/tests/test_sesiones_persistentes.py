"""Las sesiones sobreviven a un reinicio del servidor (se guardan en disco). No necesitan Ollama."""

import json
import os
import time
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app import config, sessions
from app.main import app

client = TestClient(app)


async def _stream_falso(messages, temperature=0.7, num_predict=120):
    for tok in ("Tengo ", "calentura, ", "doctor."):
        yield tok


def _crear(nivel=2, caso_id="c_dengue_01") -> str:
    r = client.post("/api/sessions", json={"nivel": nivel, "caso_id": caso_id})
    assert r.status_code == 200, r.text
    return r.json()["session_id"]


def _chat(sid: str, texto: str):
    with patch("app.llm.stream_chat", _stream_falso):
        r = client.post(f"/api/sessions/{sid}/chat", json={"message": texto})
    assert r.status_code == 200, r.text
    return r


def _reiniciar_servidor():
    """Simula el reinicio: se pierde la memoria; el disco se conserva."""
    sessions._store.clear()


def _archivo(sid: str):
    return sessions.DIR / f"{sid}.json"


def _finish(sid: str, dx="dengue"):
    with patch("app.llm.chat_once", new_callable=AsyncMock) as m:
        m.return_value = "Buen trabajo."
        return client.post(f"/api/sessions/{sid}/finish", json={"diagnostico_estudiante": dx})


# ----------------------------------------------------------------- guardado

def test_crear_una_sesion_la_guarda_en_disco_sin_el_diagnostico():
    sid = _crear()
    assert _archivo(sid).exists()
    contenido = _archivo(sid).read_text(encoding="utf-8")
    datos = json.loads(contenido)
    assert datos["caso_id"] == "c_dengue_01" and datos["persona_id"]
    # Solo referencias: no se copia el contenido del caso
    for prohibido in ("Dengue con signos de alarma", "datos_si_pregunta", "lista_verificacion", "diagnostico_alias"):
        assert prohibido not in contenido


def test_la_escritura_deja_un_json_valido_y_sin_temporales():
    sid = _crear()
    _chat(sid, "¿Desde cuándo tiene fiebre?")
    assert json.loads(_archivo(sid).read_text(encoding="utf-8"))["mensajes"]
    assert list(sessions.DIR.glob("*.tmp")) == [] and list(sessions.DIR.glob(".*.tmp")) == []


# ----------------------------------------------------------------- recuperación tras un reinicio

def test_la_sesion_sobrevive_a_un_reinicio_y_conserva_todo(monkeypatch):
    monkeypatch.setattr(config, "SEGUIMIENTO_DEMO", True)
    sid = _crear(nivel=2)
    _chat(sid, "¿Cuánto tiempo lleva con fiebre?")
    client.post(f"/api/sessions/{sid}/pista")
    client.post(f"/api/sessions/{sid}/pruebas", json={"ids": ["hemograma"]})
    antes = sessions.get(sid)
    esperado = (antes.mensajes, antes.pistas_usadas, antes.nivel_por_item, antes.pruebas_pedidas, antes.costo_pruebas, antes.modulos_activos)

    _reiniciar_servidor()
    assert sid not in sessions._store

    despues = sessions.get(sid)
    assert despues is not None
    assert (despues.mensajes, despues.pistas_usadas, despues.nivel_por_item, despues.pruebas_pedidas, despues.costo_pruebas, despues.modulos_activos) == esperado
    assert despues.caso["id"] == "c_dengue_01" and despues.persona["id"] == antes.persona["id"]
    assert not despues.busy


def test_tras_un_reinicio_se_puede_seguir_con_el_chat_las_pistas_y_las_pruebas(monkeypatch):
    monkeypatch.setattr(config, "SEGUIMIENTO_DEMO", True)
    sid = _crear(nivel=2)
    _chat(sid, "¿Cuánto tiempo lleva con fiebre?")
    client.post(f"/api/sessions/{sid}/pista")
    client.post(f"/api/sessions/{sid}/pruebas", json={"ids": ["hemograma"]})

    _reiniciar_servidor()

    assert client.get(f"/api/sessions/{sid}/pruebas").json()["pruebas_usadas"] == 1
    assert client.post(f"/api/sessions/{sid}/pista").json()["pistas_usadas"] == 2  # continúa la cuenta
    _chat(sid, "¿Ha tenido sangrado?")
    assert sessions.get(sid).preguntas_usadas == 2  # la pregunta anterior no se perdió


def test_la_evaluacion_usa_lo_que_se_pregunto_antes_del_reinicio():
    sid = _crear(nivel=2)
    _chat(sid, "¿Cuánto tiempo lleva con fiebre?")
    _reiniciar_servidor()
    j = _finish(sid).json()
    assert any("fiebre" in t.lower() for t in j["cumplidos"])


def test_finish_es_idempotente_y_la_consulta_sigue_terminada_tras_un_reinicio():
    sid = _crear(nivel=2)
    _chat(sid, "¿Tiene fiebre?")
    primero = _finish(sid).json()
    _reiniciar_servidor()
    segundo = _finish(sid).json()
    assert segundo["puntaje"] == primero["puntaje"] and segundo["feedback"] == primero["feedback"]
    with patch("app.llm.stream_chat", _stream_falso):
        r = client.post(f"/api/sessions/{sid}/chat", json={"message": "hola"})
    assert r.status_code == 409


def test_una_sesion_sacada_de_memoria_por_el_limite_se_restaura(monkeypatch):
    monkeypatch.setattr(sessions, "MAX_SESSIONS", 2)
    primera = _crear()
    _crear()
    _crear()
    assert primera not in sessions._store  # descartada de memoria...
    assert sessions.get(primera) is not None  # ...pero recuperada del disco


def test_la_pregunta_interrumpida_por_el_reinicio_se_descarta():
    sid = _crear()
    s = sessions.get(sid)
    s.mensajes = [
        {"role": "user", "content": "¿Tiene fiebre?"},
        {"role": "assistant", "content": "Sí, doctor."},
        {"role": "user", "content": "¿Y vómitos?"},  # el reinicio ocurrió antes de la respuesta
    ]
    sessions.guardar(s)
    _reiniciar_servidor()
    r = sessions.get(sid)
    assert [m["role"] for m in r.mensajes] == ["user", "assistant"]
    assert r.preguntas_usadas == 1


def test_el_estado_ocupado_no_se_guarda():
    sid = _crear()
    s = sessions.get(sid)
    s.lock()
    sessions.guardar(s)
    _reiniciar_servidor()
    assert not sessions.get(sid).busy


# ----------------------------------------------------------------- robustez y seguridad

def test_ids_con_forma_invalida_no_tocan_el_disco():
    for malo in ("../../etc/passwd", "..\\..\\x", "zzzz", "A" * 32, "", "a" * 31):
        assert sessions.get(malo) is None
    assert client.post("/api/sessions/zzzz/pista").status_code == 404
    assert not sessions.DIR.exists() or list(sessions.DIR.iterdir()) == []


def test_un_archivo_corrupto_se_descarta_sin_romper_nada():
    sid = _crear()
    _archivo(sid).write_text("{esto no es json", encoding="utf-8")
    _reiniciar_servidor()
    assert sessions.get(sid) is None
    assert not _archivo(sid).exists()
    assert client.post(f"/api/sessions/{sid}/pista").status_code == 404


def test_un_archivo_de_version_desconocida_se_ignora():
    sid = _crear()
    datos = json.loads(_archivo(sid).read_text(encoding="utf-8"))
    datos["v"] = 99
    _archivo(sid).write_text(json.dumps(datos), encoding="utf-8")
    _reiniciar_servidor()
    assert sessions.get(sid) is None


def test_si_el_caso_ya_no_existe_la_sesion_no_se_restaura():
    sid = _crear()
    datos = json.loads(_archivo(sid).read_text(encoding="utf-8"))
    datos["caso_id"] = "c_borrado_99"
    _archivo(sid).write_text(json.dumps(datos), encoding="utf-8")
    _reiniciar_servidor()
    assert sessions.get(sid) is None


def test_un_fallo_al_escribir_no_rompe_la_peticion(monkeypatch):
    def falla(*a, **k):
        raise OSError("disco lleno")

    monkeypatch.setattr(sessions.os, "replace", falla)
    r = client.post("/api/sessions", json={"nivel": 2, "caso_id": "c_dengue_01"})
    assert r.status_code == 200
    sid = r.json()["session_id"]
    assert not _archivo(sid).exists()
    assert list(sessions.DIR.glob(".*.tmp")) == []  # no deja temporales
    # y la sesión sigue funcionando en memoria
    with patch("app.llm.stream_chat", _stream_falso):
        assert client.post(f"/api/sessions/{sid}/chat", json={"message": "hola"}).status_code == 200


# ----------------------------------------------------------------- limpieza

def _envejecer(ruta, horas):
    t = time.time() - horas * 3600
    os.utime(ruta, (t, t))


def test_la_limpieza_borra_las_sesiones_viejas_y_conserva_las_recientes(monkeypatch):
    monkeypatch.setattr(config, "SESIONES_TTL_HORAS", 24)
    vieja, nueva = _crear(), _crear()
    _envejecer(_archivo(vieja), 25)
    assert sessions.limpiar() >= 1
    assert not _archivo(vieja).exists() and _archivo(nueva).exists()


def test_la_limpieza_respeta_el_maximo_de_sesiones_en_disco(monkeypatch):
    monkeypatch.setattr(config, "MAX_SESIONES_DISCO", 2)
    ids = [_crear() for _ in range(4)]
    for i, sid in enumerate(ids):  # la 0 es la más antigua
        _envejecer(_archivo(sid), 4 - i)
    sessions.limpiar()
    quedan = [sid for sid in ids if _archivo(sid).exists()]
    assert quedan == ids[2:]


def test_la_limpieza_borra_temporales_abandonados():
    sessions.DIR.mkdir(parents=True, exist_ok=True)
    tmp = sessions.DIR / ".abandonado.tmp"
    tmp.write_text("x")
    _envejecer(tmp, 2)
    sessions.limpiar()
    assert not tmp.exists()


def test_limpiar_sin_carpeta_no_falla():
    assert sessions.limpiar() == 0
