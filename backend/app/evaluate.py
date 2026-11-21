"""Evaluación: palabras clave sobre lo que PREGUNTÓ el estudiante + diagnóstico + feedback del LLM.

Las keywords se comparan como prefijo de palabra sobre texto sin tildes ni mayúsculas
("viaj" detecta "viajó", "viajado"). Limitación conocida: es una heurística; no entiende
negaciones ni paráfrasis lejanas.
"""
import re
import unicodedata

from . import config, llm, prompts, rag
from .sessions import Session


def norm(text: str) -> str:
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return f" {text.strip()} "


def _hit(keywords: list[str], texto: str) -> bool:
    return any(norm(k).rstrip() in texto for k in keywords)


def _diagnostico_correcto(caso: dict, dx_estudiante: str) -> bool:
    dx = norm(dx_estudiante)
    aliases = [caso["diagnostico"]] + caso.get("diagnostico_alias", [])
    return any(norm(a) in dx for a in aliases)  # palabra completa (norm agrega espacios en los bordes)


def _feedback_base(correcto: bool, caso: dict, faltantes: list[str], banderas_faltantes: list[str]) -> str:
    partes = [
        "Diagnóstico correcto." if correcto else f"El diagnóstico real era: {caso['diagnostico']}.",
    ]
    if faltantes:
        partes.append("Te faltó explorar: " + "; ".join(faltantes) + ".")
    if banderas_faltantes:
        partes.append("Señales de alarma que no preguntaste: " + "; ".join(banderas_faltantes) + ".")
    if not faltantes and not banderas_faltantes:
        partes.append("Cubriste todos los temas clave de la entrevista.")
    return " ".join(partes)


async def evaluar(session: Session, dx_estudiante: str) -> dict:
    caso = session.caso
    texto = norm(" . ".join(m["content"] for m in session.mensajes if m["role"] == "user"))

    cumplidos, faltantes = [], []
    for it in caso["lista_verificacion"]:
        (cumplidos if _hit(it["keywords"], texto) else faltantes).append(it["texto"])

    banderas = [{"id": b["id"], "texto": b["texto"], "cumplida": _hit(b["keywords"], texto)} for b in caso["banderas_rojas"]]
    banderas_faltantes = [b["texto"] for b in banderas if not b["cumplida"]]

    correcto = _diagnostico_correcto(caso, dx_estudiante)
    frac_items = len(cumplidos) / max(len(caso["lista_verificacion"]), 1)
    frac_banderas = sum(b["cumplida"] for b in banderas) / max(len(banderas), 1)
    puntaje_base = round(60 * frac_items + 30 * (1 if correcto else 0) + 10 * frac_banderas)
    descuento_pistas = round(session.pistas_usadas * config.PENALIZACION_PISTA)
    puntaje = max(0, puntaje_base - descuento_pistas)

    citas = []
    if config.RAG_ENABLED:
        try:
            citas = await rag.consultar(caso.get("guia_ref"), query=f"{caso['diagnostico']} {dx_estudiante}")
        except Exception:
            citas = []

    feedback = _feedback_base(correcto, caso, faltantes, banderas_faltantes)
    if session.mensajes:
        try:
            narrativo = await llm.chat_once([
                {"role": "system", "content": prompts.SYSTEM_FEEDBACK},
                {"role": "user", "content": prompts.user_feedback(caso, dx_estudiante, correcto, cumplidos, faltantes, banderas_faltantes, citas=citas)},
            ])
            if narrativo:
                feedback = narrativo
        except llm.LLMError:
            pass  # se conserva el feedback determinista

    return {
        "diagnostico_real": caso["diagnostico"],
        "diagnostico_correcto": correcto,
        "puntaje": puntaje,
        "puntaje_base": puntaje_base,
        "pistas_usadas": session.pistas_usadas,
        "descuento_pistas": descuento_pistas,
        "cumplidos": cumplidos,
        "faltantes": faltantes,
        "banderas": banderas,
        "feedback": feedback,
        "citas": citas,
    }
