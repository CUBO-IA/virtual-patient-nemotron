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


def _aciertos_diferenciales(caso: dict, dx_estudiante: str, diferenciales: list[str]) -> list[str]:
    """Evalúa los diagnósticos diferenciales ingresados por el estudiante contra los del caso.

    Un diferencial es acertado si su texto normalizado contiene (palabra completa) algún alias
    de un elemento de caso['diferenciales'], no se ha contado ya, y no repite el diagnóstico principal.
    """
    if not diferenciales or not caso.get("diferenciales"):
        return []

    aliases_principal = [caso["diagnostico"]] + caso.get("diagnostico_alias", [])
    acertados = []
    elementos_contados = set()

    for d_user in diferenciales:
        if not d_user or not isinstance(d_user, str) or not d_user.strip():
            continue
        norm_user = norm(d_user)
        # El diagnóstico principal no puede puntuar también como diferencial
        if any(norm(a) in norm_user for a in aliases_principal):
            continue

        for elem in caso.get("diferenciales", []):
            elem_nom = elem.get("nombre", "")
            if elem_nom in elementos_contados:
                continue
            aliases = [elem_nom] + elem.get("alias", [])
            if any(norm(a) in norm_user for a in aliases):
                acertados.append(elem_nom)
                elementos_contados.add(elem_nom)
                break

    return acertados


async def evaluar(session: Session, dx_estudiante: str, diferenciales_estudiante: list[str] | None = None) -> dict:
    caso = session.caso
    texto = norm(" . ".join(m["content"] for m in session.mensajes if m["role"] == "user"))

    cumplidos, faltantes = [], []
    for it in caso["lista_verificacion"]:
        (cumplidos if _hit(it["keywords"], texto) else faltantes).append(it["texto"])

    banderas = [{"id": b["id"], "texto": b["texto"], "cumplida": _hit(b["keywords"], texto)} for b in caso["banderas_rojas"]]
    banderas_faltantes = [b["texto"] for b in banderas if not b["cumplida"]]

    correcto = _diagnostico_correcto(caso, dx_estudiante)

    # Configuración de pesos y reglas del nivel
    nivel_cfg = session.nivel or {}
    pesos_base = nivel_cfg.get("pesos", {"checklist": 60, "diagnostico": 30, "banderas": 10, "diferenciales": 0})
    pesos = {k: float(v) for k, v in pesos_base.items()}
    diferenciales_req = int(nivel_cfg.get("diferenciales_requeridos", 0))
    pistas_cfg = nivel_cfg.get("pistas", {})
    penalizacion_pista = float(pistas_cfg.get("penalizacion", config.PENALIZACION_PISTA))

    # Caso límite: caso sin diferenciales en un nivel que los exige (§5.4)
    # El componente diferenciales se marca no aplica y los demás se reescalan a 100
    caso_tiene_diferenciales = bool(caso.get("diferenciales"))
    if diferenciales_req > 0 and not caso_tiene_diferenciales:
        w_dif = pesos.get("diferenciales", 0.0)
        if w_dif < 100:
            factor = 100.0 / (100.0 - w_dif)
            pesos["checklist"] *= factor
            pesos["diagnostico"] *= factor
            pesos["banderas"] *= factor
        pesos["diferenciales"] = 0.0
        diferenciales_req = 0

    frac_items = len(cumplidos) / max(len(caso["lista_verificacion"]), 1)
    frac_banderas = sum(b["cumplida"] for b in banderas) / max(len(banderas), 1)

    aciertos_dif = _aciertos_diferenciales(caso, dx_estudiante, diferenciales_estudiante or [])
    frac_diferenciales = (len(aciertos_dif) / max(diferenciales_req, 1)) if diferenciales_req > 0 else 0.0

    obt_checklist = round(pesos.get("checklist", 60.0) * frac_items, 2)
    obt_dx = round(pesos.get("diagnostico", 30.0) * (1.0 if correcto else 0.0), 2)
    obt_banderas = round(pesos.get("banderas", 10.0) * frac_banderas, 2)
    obt_diferenciales = round(pesos.get("diferenciales", 0.0) * frac_diferenciales, 2)

    base_raw = (
        (pesos.get("checklist", 60.0) * frac_items)
        + (pesos.get("diagnostico", 30.0) * (1.0 if correcto else 0.0))
        + (pesos.get("banderas", 10.0) * frac_banderas)
        + (pesos.get("diferenciales", 0.0) * frac_diferenciales)
    )
    puntaje_base = round(base_raw)
    descuento_pistas = round(session.pistas_usadas * penalizacion_pista)
    puntaje = max(0, puntaje_base - descuento_pistas)

    aprobado_desde = nivel_cfg.get("aprobado_desde", 70)
    aprobado = puntaje >= aprobado_desde

    desglose = {
        "checklist": {"obtenido": obt_checklist, "maximo": round(pesos.get("checklist", 60.0), 2)},
        "diagnostico": {"obtenido": obt_dx, "maximo": round(pesos.get("diagnostico", 30.0), 2)},
        "banderas": {"obtenido": obt_banderas, "maximo": round(pesos.get("banderas", 10.0), 2)},
        "diferenciales": {"obtenido": obt_diferenciales, "maximo": round(pesos.get("diferenciales", 0.0), 2)},
        "pistas": {"descuento": descuento_pistas},
    }

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

    diferenciales_razonables = [d["nombre"] for d in caso.get("diferenciales", [])]

    return {
        "caso_id": caso["id"],
        "nivel": {
            "id": nivel_cfg.get("id", 2),
            "nombre": nivel_cfg.get("nombre", "Intermedio"),
        },
        "preguntas_usadas": session.preguntas_usadas,
        "aprobado": aprobado,
        "desglose": desglose,
        "diferenciales_razonables": diferenciales_razonables,
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
