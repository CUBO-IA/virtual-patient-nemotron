"""Modo Urgencias (URGENCIAS.md): carga de casos, datos públicos de la sesión y triaje.

La prioridad correcta, los signos y la acción esperada salen siempre del JSON; el modelo no interviene.
Nada de `urgencia` sale al cliente hasta que se envía el triaje.
"""
import json
import random
import time

from . import config, evaluate

NIVELES = ("verde", "amarillo", "rojo")  # de menos a más urgente
ACCIONES = ("consulta_normal", "evaluacion_pronto", "atencion_inmediata", "emergencias")
ORDEN_PRIORIDAD = {n: i for i, n in enumerate(NIVELES)}
ORDEN_ACCION = {a: i for i, a in enumerate(ACCIONES)}

PESOS = {"prioridad": 50, "signos": 30, "esenciales": 10, "rapidez": 10}
PENALIZACION_PISTA = 5
MAX_PISTAS = 2
APROBADO_DESDE = 70


class UrgenciasError(Exception):
    def __init__(self, status: int, mensaje: str):
        super().__init__(mensaje)
        self.status = status
        self.mensaje = mensaje


def cargar_casos() -> list[dict]:
    try:
        return json.loads((config.DATA_DIR / "urgencias.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise UrgenciasError(503, f"No se pudieron cargar los casos de urgencias: {e}")


def buscar_caso(caso_id: str) -> dict | None:
    """Caso por id, sin filtrar por revisión (se usa al restaurar una sesión del disco)."""
    try:
        return next((c for c in cargar_casos() if c.get("id") == caso_id), None)
    except UrgenciasError:
        return None


def habilitado(caso: dict) -> bool:
    """Un caso solo se ofrece si está validado por una persona o el servidor está en modo demostración."""
    return caso.get("revision_clinica", {}).get("estado") == "validado" or config.SEGUIMIENTO_DEMO


def disponible() -> bool:
    """¿Hay al menos un caso que se pueda ofrecer? (para mostrar u ocultar el modo en la interfaz)"""
    try:
        return any(habilitado(c) for c in cargar_casos())
    except UrgenciasError:
        return False


def elegir_caso(caso_id: str | None = None) -> dict:
    casos = [c for c in cargar_casos() if habilitado(c)]
    if not casos:
        raise UrgenciasError(
            403, "Urgencias está desactivado hasta la revisión clínica; activa SEGUIMIENTO_DEMO para demostración."
        )
    if caso_id:
        caso = next((c for c in casos if c["id"] == caso_id), None)
        if caso is None:
            raise UrgenciasError(404, "No existe ese caso de urgencias.")
        return caso
    return random.choice(casos)


def datos_publicos(caso: dict) -> dict:
    """Lo único de `urgencia` que ve el cliente antes del triaje."""
    u = caso["urgencia"]
    acomp = u.get("acompanante") or {}
    return {
        "tiempo_limite_seg": u["tiempo_limite_seg"],
        "max_preguntas": u["max_preguntas"],
        "preguntas_minimas_semaforo": u["preguntas_minimas_semaforo"],
        "acompanante": {"relacion": acomp.get("relacion")} if acomp.get("tiene") else None,
        "revision_clinica": {"estado": "pendiente", "contenido_sin_validar": True},
    }


def verificar_limites(s) -> None:
    """Límites de preguntas y de tiempo, con el reloj del servidor. Lanza 409 si se superan."""
    u = s.caso["urgencia"]
    if s.preguntas_usadas >= u["max_preguntas"]:
        raise UrgenciasError(409, "Alcanzaste el límite de preguntas; elige la prioridad.")
    if s.iniciada_en is not None and time.time() - s.iniciada_en >= u["tiempo_limite_seg"]:
        raise UrgenciasError(409, "Se acabó el tiempo; elige la prioridad.")


def puntaje_prioridad(elegida: str, correcta: str) -> int:
    """Equivocarse hacia menos urgencia es más grave que hacia más urgencia."""
    d = ORDEN_PRIORIDAD[elegida] - ORDEN_PRIORIDAD[correcta]
    if d == 0:
        return PESOS["prioridad"]
    return PESOS["prioridad"] // 2 if d > 0 else 0


def calcular_triaje(s, prioridad: str, accion: str, ahora: float | None = None) -> dict:
    """Valida y puntúa el triaje de una sesión de urgencias. No guarda nada."""
    if s.triaje:
        raise UrgenciasError(409, "El triaje ya fue enviado.")
    u = s.caso["urgencia"]
    minimas = u["preguntas_minimas_semaforo"]
    if s.preguntas_usadas < minimas:
        raise UrgenciasError(409, f"Haz al menos {minimas} preguntas antes de elegir.")
    if prioridad not in ORDEN_PRIORIDAD or accion not in ORDEN_ACCION:
        raise UrgenciasError(422, "Prioridad o acción no válida.")

    preguntas = evaluate.norm(" ".join(m["content"] for m in s.mensajes if m["role"] == "user"))
    activos = list(u["signos_activos"])
    banderas = {b["id"]: b for b in s.caso["banderas_rojas"]}
    encontrados = [i for i in activos if i in banderas and evaluate._hit(banderas[i]["keywords"], preguntas)]
    faltantes = [i for i in activos if i not in encontrados]

    esenciales = s.caso["lista_verificacion"]
    hechas = [i["id"] for i in esenciales if evaluate._hit(i["keywords"], preguntas)]
    sin_hacer = [i["id"] for i in esenciales if i["id"] not in hechas]

    ahora = time.time() if ahora is None else ahora
    usado = min(1.0, (ahora - (s.iniciada_en or ahora)) / u["tiempo_limite_seg"])

    d = {
        "prioridad": puntaje_prioridad(prioridad, u["nivel"]),
        # Sin signos activos (caso verde) no hay nada que encontrar: se otorgan completos.
        "signos": PESOS["signos"] if not activos else round(PESOS["signos"] * len(encontrados) / len(activos)),
        "esenciales": round(PESOS["esenciales"] * len(hechas) / len(esenciales)) if esenciales else PESOS["esenciales"],
        "rapidez": round(PESOS["rapidez"] * (1 - usado)),
        "pistas": -PENALIZACION_PISTA * min(MAX_PISTAS, s.pistas_usadas),
    }
    puntaje = max(0, min(100, sum(d.values())))

    inseguro = ORDEN_PRIORIDAD[prioridad] < ORDEN_PRIORIDAD[u["nivel"]] or ORDEN_ACCION[accion] < ORDEN_ACCION[u["accion_esperada"]]
    alerta = None
    if inseguro:
        alerta = "Elegiste menos urgencia de la necesaria: en una emergencia real, eso retrasaría la atención."

    textos = {i: b["texto"] for i, b in banderas.items()}
    ids_esenciales = {i["id"]: i["texto"] for i in esenciales}
    return {
        "prioridad_correcta": u["nivel"],
        "accion_correcta": u["accion_esperada"],
        "prioridad_elegida": prioridad,
        "accion_elegida": accion,
        "signos": {"encontrados": [textos[i] for i in encontrados], "faltantes": [textos[i] for i in faltantes]},
        "preguntas_esenciales": {"hechas": [ids_esenciales[i] for i in hechas], "faltantes": [ids_esenciales[i] for i in sin_hacer]},
        "puntaje": puntaje,
        "desglose": d,
        "aprobado": puntaje >= APROBADO_DESDE and not inseguro,
        "alerta_seguridad": alerta,
        "explicacion": u["explicacion"],
        "pistas_usadas": s.pistas_usadas,
    }
