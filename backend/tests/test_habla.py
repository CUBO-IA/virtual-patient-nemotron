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
