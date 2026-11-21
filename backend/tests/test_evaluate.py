"""Pruebas para evaluate.evaluar y cálculo de puntajes."""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch

from app.evaluate import evaluar, _diagnostico_correcto
from app.sessions import Session


@pytest.fixture
def dummy_caso():
    return {
        "id": "c_test_01",
        "diagnostico": "Enfermedad renal crónica",
        "diagnostico_alias": ["erc", "insuficiencia renal"],
        "lista_verificacion": [
            {"id": "item1", "texto": "Cambios de orina", "keywords": ["orina", "espuma"]},
            {"id": "item2", "texto": "Hinchazón", "keywords": ["hinch", "pies"]},
            {"id": "item3", "texto": "Agroquímicos", "keywords": ["fumiga", "quimico"]},
            {"id": "item4", "texto": "Presión arterial", "keywords": ["presion"]},
        ],
        "banderas_rojas": [
            {"id": "b1", "texto": "AINE", "keywords": ["diclofenaco", "ibuprofeno"]},
            {"id": "b2", "texto": "Diuresis baja", "keywords": ["orina poco", "orina menos"]},
        ],
    }


def test_diagnostico_alias_palabra_completa(dummy_caso):
    # 'erc' no debe coincidir dentro de 'ejercicio'
    assert not _diagnostico_correcto(dummy_caso, "El paciente necesita hacer ejercicio")
    assert not _diagnostico_correcto(dummy_caso, "acercamiento")
    assert not _diagnostico_correcto(dummy_caso, "tercer")

    # Debe coincidir como palabra completa (mayúsculas, minúsculas, puntuación)
    assert _diagnostico_correcto(dummy_caso, "El diagnóstico es erc.")
    assert _diagnostico_correcto(dummy_caso, "ERC")
    assert _diagnostico_correcto(dummy_caso, "Sospecho insuficiencia renal")
    assert _diagnostico_correcto(dummy_caso, "Enfermedad Renal Crónica")


def test_evaluar_tres_escenarios(dummy_caso):
    persona = {"nombre": "Juan", "edad": 40, "sexo": "M"}

    # Mock de LLM para no llamar a Ollama
    with patch("app.llm.chat_once", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = "Feedback del LLM"

        # Escenario 1: Todo cumplido y diagnóstico correcto = 100
        # 4 items cumplidos + 2 banderas cumplidas + dx correcto
        # puntaje = round(60 * 1.0 + 30 * 1 + 10 * 1.0) = 100
        s1 = Session(id="s1", caso=dummy_caso, persona=persona)
        s1.mensajes = [
            {"role": "user", "content": "¿Cómo está su orina y tiene espuma en los pies o hinchazón?"},
            {"role": "user", "content": "¿Usa químicos al fumigar y se ha tomado la presión?"},
            {"role": "user", "content": "¿Ha tomado diclofenaco y orina poco últimamente?"},
        ]
        res1 = asyncio.run(evaluar(s1, "Tiene ERC"))
        assert res1["diagnostico_correcto"] is True
        assert len(res1["cumplidos"]) == 4
        assert len(res1["faltantes"]) == 0
        assert all(b["cumplida"] for b in res1["banderas"])
        assert res1["puntaje"] == 100

        # Escenario 2: Nada cumplido y diagnóstico incorrecto = 0
        # 0 items + 0 banderas + dx incorrecto
        # puntaje = round(60 * 0 + 30 * 0 + 10 * 0) = 0
        s2 = Session(id="s2", caso=dummy_caso, persona=persona)
        s2.mensajes = [
            {"role": "user", "content": "Hola buenos días, ¿cómo se llama?"},
            {"role": "user", "content": "¿Qué comió hoy por la mañana?"},
        ]
        res2 = asyncio.run(evaluar(s2, "Gripe común"))
        assert res2["diagnostico_correcto"] is False
        assert len(res2["cumplidos"]) == 0
        assert len(res2["faltantes"]) == 4
        assert not any(b["cumplida"] for b in res2["banderas"])
        assert res2["puntaje"] == 0

        # Escenario 3: Mixto
        # Cumple 2 de 4 items (50% de 60 = 30)
        # Cumple 1 de 2 banderas (50% de 10 = 5)
        # Diagnóstico correcto (30)
        # puntaje = round(30 + 30 + 5) = 65
        s3 = Session(id="s3", caso=dummy_caso, persona=persona)
        s3.mensajes = [
            {"role": "user", "content": "¿Ha notado espuma en la orina?"},  # item1
            {"role": "user", "content": "¿Se le hinchan los pies?"},  # item2
            {"role": "user", "content": "¿Ha tomado diclofenaco?"},  # bandera1
        ]
        res3 = asyncio.run(evaluar(s3, "Insuficiencia renal"))
        assert res3["diagnostico_correcto"] is True
        assert len(res3["cumplidos"]) == 2
        assert len(res3["faltantes"]) == 2
        assert sum(b["cumplida"] for b in res3["banderas"]) == 1
        assert res3["puntaje"] == 65
