"""Pruebas de integración de RAG (Fase 2) y degradación elegante."""

import asyncio
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app import evaluate, rag
from app.sessions import Session

client = TestClient(app)


def test_health_con_rag():
    with patch("app.rag.health", new_callable=AsyncMock) as mock_rag_health:
        mock_rag_health.return_value = True
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["rag"] is True

        mock_rag_health.return_value = False
        resp2 = client.get("/api/health")
        assert resp2.status_code == 200
        assert resp2.json()["rag"] is False


def test_finish_con_chroma_simulado_llena_citas():
    caso = {
        "id": "c_dengue_01",
        "guia_ref": "dengue",
        "diagnostico": "Dengue con signos de alarma",
        "diagnostico_alias": ["dengue"],
        "lista_verificacion": [{"id": "f", "texto": "Fiebre", "keywords": ["fiebre"]}],
        "banderas_rojas": [{"id": "s", "texto": "Sangrado", "keywords": ["sangre"]}],
    }
    persona = {"nombre": "Carlos", "edad": 30, "sexo": "M"}
    session = Session(id="s_rag_1", caso=caso, persona=persona)
    session.mensajes = [{"role": "user", "content": "¿Tiene fiebre o sangre?"}]

    fake_citas = [
        {"fuente": "guia_minsal_dengue.pdf", "fragmento": "El dengue con signos de alarma requiere monitoreo constante."},
        {"fuente": "ops_dengue_2024.md", "fragmento": "Signos de alarma: dolor abdominal intenso y sangrado de mucosas."},
    ]

    with patch("app.config.RAG_ENABLED", True), \
         patch("app.rag.consultar", new_callable=AsyncMock) as mock_consultar, \
         patch("app.llm.chat_once", new_callable=AsyncMock) as mock_llm:
        mock_consultar.return_value = fake_citas
        mock_llm.return_value = "Feedback con citas"

        res = asyncio.run(evaluate.evaluar(session, "Dengue"))
        assert res["citas"] == fake_citas
        assert len(res["citas"]) == 2
        assert res["diagnostico_correcto"] is True


def test_finish_con_chroma_caido_degrada_sin_citas_y_sin_error():
    caso = {
        "id": "c_dengue_01",
        "guia_ref": "dengue",
        "diagnostico": "Dengue con signos de alarma",
        "diagnostico_alias": ["dengue"],
        "lista_verificacion": [{"id": "f", "texto": "Fiebre", "keywords": ["fiebre"]}],
        "banderas_rojas": [{"id": "s", "texto": "Sangrado", "keywords": ["sangre"]}],
    }
    persona = {"nombre": "Carlos", "edad": 30, "sexo": "M"}
    session = Session(id="s_rag_2", caso=caso, persona=persona)
    session.mensajes = [{"role": "user", "content": "¿Tiene fiebre?"}]

    with patch("app.config.RAG_ENABLED", True), \
         patch("app.rag.consultar", side_effect=Exception("Chroma connection refused [WinError 10061]")), \
         patch("app.llm.chat_once", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = "Feedback sin citas"

        # Debe completar con éxito sin lanzar excepción
        res = asyncio.run(evaluate.evaluar(session, "Dengue"))
        assert res["citas"] == []
        assert res["diagnostico_correcto"] is True
        assert res["puntaje"] > 0
