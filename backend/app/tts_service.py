"""Servicio de texto a voz para el paciente virtual.

Usa edge-tts con las voces de El Salvador y ajusta tono y velocidad según la edad.
"""

import asyncio
import logging
import re
from pathlib import Path

import edge_tts

log = logging.getLogger(__name__)

# Claves en minúsculas: el nombre oficial lleva mayúsculas y un lookup
# con .lower() no lo encontraba.
VOCES_DISPONIBLES = {
    "femenina": "es-SV-LorenaNeural",
    "masculina": "es-SV-RodrigoNeural",
    "lorena": "es-SV-LorenaNeural",
    "rodrigo": "es-SV-RodrigoNeural",
    "es-sv-lorenaneural": "es-SV-LorenaNeural",
    "es-sv-rodrigoneural": "es-SV-RodrigoNeural",
}

# edge-tts exige el signo en pitch y rate, incluso cuando el valor es cero.
PERFILES_EDAD = {
    "joven": {"pitch": "+10Hz", "rate": "+5%"},
    "adulto": {"pitch": "+0Hz", "rate": "+0%"},
    "adulto_mayor": {"pitch": "-15Hz", "rate": "-10%"},
}

_INTENTOS = 3


def resolver_voz(voz: str) -> str:
    """Devuelve el nombre oficial de la voz. Si no se reconoce, usa Rodrigo."""
    clave = (voz or "").strip().lower()
    return VOCES_DISPONIBLES.get(clave, "es-SV-RodrigoNeural")


def voz_y_perfil_persona(persona: dict) -> tuple[str, str]:
    """Elige voz (sexo) y perfil de edad del paciente."""
    sexo = (persona.get("sexo") or "M").strip().upper()
    voz = "es-SV-LorenaNeural" if sexo == "F" else "es-SV-RodrigoNeural"

    try:
        edad = int(persona.get("edad", 35))
    except (TypeError, ValueError):
        edad = 35

    if edad < 30:
        perfil = "joven"
    elif edad >= 60:
        perfil = "adulto_mayor"
    else:
        perfil = "adulto"

    return voz, perfil


def _perfil(perfil_edad: str) -> dict:
    clave = (perfil_edad or "adulto").strip().lower().replace(" ", "_")
    return PERFILES_EDAD.get(clave, PERFILES_EDAD["adulto"])


async def _sintetizar_una_vez(texto: str, voz: str, perfil_edad: str) -> bytes:
    config = _perfil(perfil_edad)
    comunicador = edge_tts.Communicate(
        text=texto,
        voice=resolver_voz(voz),
        pitch=config["pitch"],
        rate=config["rate"],
    )
    chunks: list[bytes] = []
    async for chunk in comunicador.stream():
        if chunk.get("type") == "audio" and chunk.get("data"):
            chunks.append(chunk["data"])
    audio = b"".join(chunks)
    if not audio:
        raise RuntimeError("Edge TTS no devolvió audio.")
    return audio


def limpiar_texto_para_tts(texto: str) -> str:
    """Remueve marcas de formato y acotaciones tipo *tose* o *suspira*."""
    if not texto:
        return ""
    # Acotaciones entre corchetes: [tose]
    t = re.sub(r"\[[^\]]+\]", "", texto)
    # Acotaciones escénicas típicas entre asteriscos (ej. *suspira*, *se toca el pecho*)
    t = re.sub(r"\*(?:suspira|tose|queja|llora|pausa|duda|asiente|se\s+[^*]+|\w+ndo)\*", "", t, flags=re.IGNORECASE)
    # Quitar asteriscos y guiones bajos restantes (negritas/cursivas: **dolor** -> dolor)
    t = t.replace("*", "").replace("_", "")
    limpio = " ".join(t.split()).strip()
    return limpio or texto.strip()


async def sintetizar_bytes(texto: str, voz: str, perfil_edad: str) -> bytes:
    """Genera el MP3 en memoria. Reintenta si el servicio de Microsoft no manda audio."""
    limpio = (texto or "").strip()
    if not limpio:
        raise ValueError("El texto a sintetizar no puede estar vacío.")

    texto_audio = limpiar_texto_para_tts(limpio)
    ultimo: Exception | None = None
    for intento in range(1, _INTENTOS + 1):
        try:
            return await _sintetizar_una_vez(texto_audio, voz, perfil_edad)
        except ValueError:
            raise
        except Exception as e:
            ultimo = e
            log.warning("Intento %s/%s de TTS falló: %s", intento, _INTENTOS, e)
            if intento < _INTENTOS:
                await asyncio.sleep(0.4 * intento)

    raise RuntimeError(f"No se pudo generar la voz: {ultimo}")


async def generar_audio_paciente(
    texto: str,
    voz: str,
    perfil_edad: str,
    nombre_archivo: str = "respuesta_paciente.mp3",
) -> str:
    """Genera un archivo MP3 en disco. Pensado para pruebas manuales."""
    try:
        audio_bytes = await sintetizar_bytes(texto, voz, perfil_edad)
        ruta = Path(nombre_archivo)
        if ruta.parent and not ruta.parent.exists():
            ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_bytes(audio_bytes)
        return f"Audio generado: {ruta} ({len(audio_bytes)} bytes)"
    except Exception as e:
        return f"Error al generar audio con Edge-TTS: {e}"
