"""Habla regional salvadoreña para pacientes virtuales.

Implementa:
1. Reglas generales de habla salvadoreña (trato de usted al médico,
   voseo limitado a citar allegados, muletillas y regionalismos).
2. Pronunciación fonética de la 'j' (aspiración de 's') por zona:
   - Oriente (San Miguel, Usulután, La Unión, Morazán): 'media' por defecto.
   - Centro y Occidente: 'ninguna' por defecto.
   - Niveles: 'leve', 'media', 'alta', 'ninguna'.
3. Aspiración en streaming SSE mediante búfer de palabras seguras.
"""

import re
from typing import AsyncGenerator

DEPARTAMENTOS_ORIENTE = {"San Miguel", "Usulután", "La Unión", "Morazán"}

# Vocabulario cotidiano y de salud salvadoreño
REGIONALISMOS_SALVADORENOS = [
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
    "ruco",
    "cabal",
    "púchica",
    "vaya pues",
    "ahorita",
    "chivo",
]

DELIM_RE = re.compile(r"[\s\.,;:!?\n\(\)\[\]\"'«»—–-]+")


def configurar_habla(persona: dict) -> dict:
    """Genera la configuración de habla para una persona según su departamento y perfil."""
    depto = persona.get("departamento", "")
    es_oriente = depto in DEPARTAMENTOS_ORIENTE
    aspiracion = "media" if es_oriente else "ninguna"

    edad = persona.get("edad", 35)
    area = (persona.get("area") or "").lower()

    # Selección coherente de 2 a 4 regionalismos según edad y área
    pool: list[str] = []
    if edad >= 60:
        pool.extend(["calentura", "cuerpo cortado", "ruco", "pisto", "vaya pues", "púchica"])
    elif edad <= 30:
        pool.extend(["cipote", "ahorita", "cabal", "púchica", "chivo"])
    else:
        pool.extend(["calentura", "cipote", "ahorita", "cabal", "púchica"])

    if area == "rural":
        pool.extend(["zancudo", "chunche", "chucho"])

    # Evitar duplicados manteniendo orden
    vistos: set[str] = set()
    regionalismos = [w for w in pool if not (w in vistos or vistos.add(w))][:4]

    return {
        "trato_medico": "usted",
        "aspiracion": aspiracion,
        "voseo_con_familia": True,
        "regionalismos": regionalismos,
    }


def obtener_habla(persona: dict) -> dict:
    """Devuelve la configuración de habla de la persona, autogenerándola si no existe."""
    habla = persona.get("habla")
    if isinstance(habla, dict) and "aspiracion" in habla:
        return habla
    return configurar_habla(persona)


def nivel_aspiracion(persona: dict) -> str:
    """Devuelve el nivel de aspiración de la persona ('ninguna', 'leve', 'media', 'alta')."""
    return obtener_habla(persona).get("aspiracion", "ninguna")


def aspirar(texto: str, nivel: str = "media") -> str:
    """Aplica la pronunciación regional salvadoreña de la 's' aspirada -> 'j'.

    Niveles:
    - ninguna: texto sin cambios.
    - leve: 's' al final de palabra -> 'j'.
    - media: 's' al final y antes de consonante -> 'j' (no afecta s intervocalica).
    - alta: además 's' inicial antes de vocal -> 'j'.
    """
    if nivel == "ninguna" or not texto:
        return texto

    # s al final de palabra -> j
    texto = re.sub(r"s\b", "j", texto)
    texto = re.sub(r"S\b", "J", texto)

    if nivel in ("media", "alta"):
        # s antes de consonante (estoy -> ejtoy, bastante -> bajtante)
        texto = re.sub(r"s(?=[bcdfgklmnpqrtvwxzBCDFGKLMNPQRTVWXZ])", "j", texto)
        texto = re.sub(r"S(?=[bcdfgklmnpqrtvwxzBCDFGKLMNPQRTVWXZ])", "J", texto)

    if nivel == "alta":
        # s inicial antes de vocal (semana -> jemana, sí -> jí)
        texto = re.sub(r"\bs(?=[aeiouáéíóúAEIOUÁÉÍÓÚ])", "j", texto)
        texto = re.sub(r"\bS(?=[aeiouáéíóúAEIOUÁÉÍÓÚ])", "J", texto)

    return texto


async def aspirar_stream(
    token_generator: AsyncGenerator[str, None],
    nivel: str = "media",
) -> AsyncGenerator[str, None]:
    """Procesa el flujo asíncrono de tokens aplicando aspiración palabra por palabra.

    Usa un búfer para evitar aspirar a mitad de una palabra incompleta.
    """
    if nivel == "ninguna":
        async for tok in token_generator:
            yield tok
        return

    buffer = ""
    async for tok in token_generator:
        if not tok:
            continue
        buffer += tok
        matches = list(DELIM_RE.finditer(buffer))
        if matches:
            idx = matches[-1].end()
            seguro = buffer[:idx]
            buffer = buffer[idx:]
            yield aspirar(seguro, nivel)

    if buffer:
        yield aspirar(buffer, nivel)
