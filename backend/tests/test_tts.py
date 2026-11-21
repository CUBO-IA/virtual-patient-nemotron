"""Selección de voz salvadoreña. No llama al servicio de Microsoft."""

import asyncio

import pytest

from app.tts_service import resolver_voz, sintetizar_bytes, voz_y_perfil_persona


def test_voz_por_sexo_y_edad():
    assert voz_y_perfil_persona({"sexo": "F", "edad": 22}) == ("es-SV-LorenaNeural", "joven")
    assert voz_y_perfil_persona({"sexo": "m", "edad": 45}) == ("es-SV-RodrigoNeural", "adulto")
    assert voz_y_perfil_persona({"sexo": "F", "edad": "68"}) == ("es-SV-LorenaNeural", "adulto_mayor")
    assert voz_y_perfil_persona({"sexo": "F", "edad": None}) == ("es-SV-LorenaNeural", "adulto")


def test_resolver_voz_ignora_mayusculas():
    assert resolver_voz("es-sv-lorenaneural") == "es-SV-LorenaNeural"
    assert resolver_voz("LORENA") == "es-SV-LorenaNeural"
    assert resolver_voz("desconocida") == "es-SV-RodrigoNeural"


def test_texto_vacio_no_llama_al_servicio():
    with pytest.raises(ValueError):
        asyncio.run(sintetizar_bytes("   ", "es-SV-LorenaNeural", "adulto"))
