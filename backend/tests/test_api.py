"""Pruebas de la API FastAPI con TestClient."""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


async def mock_stream_tokens(mensajes):
    tokens = ["Hola", ", ", "tengo ", "dolor."]
    for t in tokens:
        yield t


def test_api_flujo_completo_y_errores():
    # 1. Crear sesión
    resp = client.post("/api/sessions")
    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert "paciente" in data
    assert "motivo_consulta" in data
    sid = data["session_id"]

    # 2. Chat con LLM simulado
    with patch("app.llm.stream_chat", side_effect=mock_stream_tokens):
        chat_resp = client.post(f"/api/sessions/{sid}/chat", json={"message": "¿Desde cuándo le duele?"})
        assert chat_resp.status_code == 200
        assert "text/event-stream" in chat_resp.headers["content-type"]
        body_text = chat_resp.text
        assert "Hola" in body_text
        assert "done" in body_text

    # 3. Validaciones de error 422 (mensaje vacío o solo espacios)
    empty_resp1 = client.post(f"/api/sessions/{sid}/chat", json={"message": ""})
    assert empty_resp1.status_code == 422

    empty_resp2 = client.post(f"/api/sessions/{sid}/chat", json={"message": "   "})
    assert empty_resp2.status_code == 422

    # 4. Error 404 (sesión inexistente)
    not_found_chat = client.post("/api/sessions/id_que_no_existe/chat", json={"message": "Hola"})
    assert not_found_chat.status_code == 404

    not_found_finish = client.post("/api/sessions/id_que_no_existe/finish", json={"diagnostico_estudiante": "Dengue"})
    assert not_found_finish.status_code == 404

    # 5. Terminar sesión (/finish)
    with patch("app.llm.chat_once", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = "Buen trabajo en la consulta."
        finish_resp = client.post(f"/api/sessions/{sid}/finish", json={"diagnostico_estudiante": "Dengue"})
        assert finish_resp.status_code == 200
        res = finish_resp.json()
        assert "diagnostico_real" in res
        assert "puntaje" in res
        assert "cumplidos" in res
        assert "faltantes" in res

        # 6. finish idempotente: volver a llamar devuelve el mismo resultado
        finish_resp2 = client.post(f"/api/sessions/{sid}/finish", json={"diagnostico_estudiante": "Dengue"})
        assert finish_resp2.status_code == 200
        assert finish_resp2.json() == res

    # 7. Error 409 si ya terminó y se intenta chatear
    chat_after_finish = client.post(f"/api/sessions/{sid}/chat", json={"message": "Una pregunta más"})
    assert chat_after_finish.status_code == 409
