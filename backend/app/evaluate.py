"""Evaluación: palabras clave sobre lo que PREGUNTÓ el estudiante + diagnóstico + feedback del LLM.

Las keywords se comparan como prefijo de palabra sobre texto sin tildes ni mayúsculas
("viaj" detecta "viajó", "viajado"). Limitación conocida: es una heurística; no entiende
negaciones ni paráfrasis lejanas.

Con los módulos de SEGUIMIENTO.md activos, el puntaje también incluye las pruebas pedidas y el
plan de tratamiento. Todo es determinista: el modelo solo redacta la retroalimentación.
"""
import re
import unicodedata
from functools import lru_cache

from . import config, llm, prompts, rag, seguimiento
from .sessions import Session

PESOS_POR_DEFECTO = {"checklist": 60, "diagnostico": 30, "banderas": 10, "diferenciales": 0}
COMPONENTES = ("checklist", "diagnostico", "banderas", "diferenciales", "pruebas", "plan")


def norm(text: str) -> str:
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return f" {text.strip()} "


SUFIJOS = [
    "amientos", "imientos", "amiento", "imiento", "aciones", "iciones", "acion", "icion",
    "ando", "iendo", "ados", "idos", "adas", "idas", "ado", "ido", "ada", "ida",
    "ar", "er", "ir", "es", "as", "os", "an", "en", "a", "e", "o", "s"
]
EQUIV = {"del": "de", "al": "a"}


@lru_cache(maxsize=8192)
def _raiz(w: str) -> str:
    if len(w) <= 4:
        return w
    for s in SUFIJOS:
        if w.endswith(s) and len(w) - len(s) >= 4:
            return w[: -len(s)]
    return w


@lru_cache(maxsize=65536)
def _tok_coincide(k: str, t: str) -> bool:
    if k == t or t.startswith(k):  # comportamiento actual
        return True
    if len(k) <= 4 or len(t) <= 4:
        return False
    rk, rt = _raiz(k), _raiz(t)
    return (
        len(rk) >= 4
        and len(rt) >= 4
        and abs(len(rk) - len(rt)) <= 4
        and (rk.startswith(rt) or rt.startswith(rk))
    )


@lru_cache(maxsize=4096)
def _clave_tokens(k: str) -> tuple[str, ...]:
    return tuple(EQUIV.get(p, p) for p in norm(k).split())


def _hit(keywords: list[str], texto: str) -> bool:
    palabras = [EQUIV.get(p, p) for p in texto.split()]
    for k in keywords:
        clave = _clave_tokens(k)
        if clave and any(
            all(_tok_coincide(clave[j], palabras[i + j]) for j in range(len(clave)))
            for i in range(len(palabras) - len(clave) + 1)
        ):
            return True
    return False


def _alias_principales_efectivos(caso: dict, texto_norm: str) -> list[str]:
    """Alias del diagnóstico principal presentes en el texto (ya normalizado).

    Un alias que forma parte de un diferencial más específico NO cuenta: «diabetes» dentro de
    «diabetes insípida» no convierte a ese texto en el diagnóstico principal (diabetes mellitus).
    """
    principales = [caso["diagnostico"]] + caso.get("diagnostico_alias", [])
    coinciden = [a for a in principales if norm(a) in texto_norm]
    if not coinciden:
        return []
    alias_dif = [
        a
        for d in caso.get("diferenciales", [])
        for a in [d.get("nombre", "")] + d.get("alias", [])
        if a and norm(a) in texto_norm
    ]
    return [a for a in coinciden if not any(norm(a) in norm(da) and norm(a) != norm(da) for da in alias_dif)]


def _diagnostico_correcto(caso: dict, dx_estudiante: str) -> bool:
    # palabra completa (norm agrega espacios en los bordes)
    return bool(_alias_principales_efectivos(caso, norm(dx_estudiante)))


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


def _feedback_modulos(pruebas: dict | None, plan: dict | None) -> str:
    """Frases deterministas sobre pruebas y plan. Las alertas de seguridad van primero."""
    partes = []
    if plan and plan["alertas_seguridad"]:
        partes.append("ALERTA DE SEGURIDAD: " + " ".join(plan["alertas_seguridad"]))
    if pruebas:
        if pruebas["esenciales_faltantes"]:
            partes.append("Pruebas esenciales que no pediste: " + "; ".join(pruebas["esenciales_faltantes"]) + ".")
        if pruebas["innecesarias"]:
            partes.append("Pruebas sin indicación en este caso: " + "; ".join(pruebas["innecesarias"]) + ".")
    if plan:
        if plan["medicamentos_faltantes"]:
            partes.append("Medicamentos que faltaban en el plan: " + "; ".join(plan["medicamentos_faltantes"]) + ".")
        if plan["disposicion"]["veredicto"] == "insuficiente":
            partes.append("La disposición elegida no era suficiente para este caso.")
        if plan["indicaciones"]["faltantes"]:
            partes.append("Indicaciones esenciales que faltaron: " + "; ".join(plan["indicaciones"]["faltantes"]) + ".")
    return " ".join(partes)


def _texto_modulos_para_llm(pruebas: dict | None, plan: dict | None) -> str:
    """Listas ya calculadas que el modelo puede usar. No debe salirse de ellas."""
    lineas = []
    if pruebas:
        lineas.append("Pruebas solicitadas: " + ("; ".join(f"{s['nombre']} ({s['pertinencia']})" for s in pruebas["solicitadas"]) or "ninguna") + ".")
        lineas.append("Pruebas esenciales no solicitadas: " + ("; ".join(pruebas["esenciales_faltantes"]) or "ninguna") + ".")
    if plan:
        lineas.append("Medicamentos recetados: " + ("; ".join(f"{m['nombre']} ({m['veredicto']}" + (f": {m['nota']}" if m.get("nota") else "") + ")" for m in plan["medicamentos"]) or "ninguno") + ".")
        lineas.append("Medicamentos adecuados que faltaron: " + ("; ".join(plan["medicamentos_faltantes"]) or "ninguno") + ".")
        lineas.append(f"Disposición elegida: {plan['disposicion']['texto']} ({plan['disposicion']['veredicto']}).")
        lineas.append("Indicaciones esenciales que faltaron: " + ("; ".join(plan["indicaciones"]["faltantes"]) or "ninguna") + ".")
        lineas.append("Alertas de seguridad: " + ("; ".join(plan["alertas_seguridad"]) or "ninguna") + ".")
    return "\n".join(lineas)


def _aciertos_diferenciales(caso: dict, dx_estudiante: str, diferenciales: list[str]) -> list[str]:
    """Evalúa los diagnósticos diferenciales ingresados por el estudiante contra los del caso.

    Un diferencial es acertado si su texto normalizado contiene (palabra completa) algún alias
    de un elemento de caso['diferenciales'], no se ha contado ya, y no repite el diagnóstico principal.
    """
    if not diferenciales or not caso.get("diferenciales"):
        return []

    acertados = []
    elementos_contados = set()

    for d_user in diferenciales:
        if not d_user or not isinstance(d_user, str) or not d_user.strip():
            continue
        norm_user = norm(d_user)
        # El diagnóstico principal no puede puntuar también como diferencial
        if _alias_principales_efectivos(caso, norm_user):
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


def _reescalar(base: dict, excluir: set[str]) -> dict:
    """Reparte a 100 los pesos de los componentes que aplican; los excluidos quedan en 0."""
    conservados = {k: float(v) for k, v in base.items() if k not in excluir}
    total = sum(conservados.values())
    factor = (100.0 / total) if total > 0 else 1.0
    pesos = {k: conservados.get(k, 0.0) * factor for k in COMPONENTES}
    return pesos


async def evaluar(
    session: Session,
    dx_estudiante: str,
    diferenciales_estudiante: list[str] | None = None,
    plan_estudiante: dict | None = None,
) -> dict:
    caso = session.caso
    mensajes_est = [m["content"] for m in session.mensajes if m["role"] == "user"]
    texto = norm(" . ".join(mensajes_est))

    cumplidos, faltantes = [], []
    for it in caso["lista_verificacion"]:
        (cumplidos if _hit(it["keywords"], texto) else faltantes).append(it["texto"])

    banderas = [{"id": b["id"], "texto": b["texto"], "cumplida": _hit(b["keywords"], texto)} for b in caso["banderas_rojas"]]
    banderas_faltantes = [b["texto"] for b in banderas if not b["cumplida"]]

    correcto = _diagnostico_correcto(caso, dx_estudiante)

    # --- Configuración del nivel y módulos que aplican -------------------------------------
    nivel_cfg = session.nivel or {}
    modulos = session.modulos_activos or {}
    diferenciales_req = int(nivel_cfg.get("diferenciales_requeridos", 0))
    pistas_cfg = nivel_cfg.get("pistas", {})
    penalizacion_pista = float(pistas_cfg.get("penalizacion", config.PENALIZACION_PISTA))

    pruebas_aplica = bool(modulos.get("pruebas")) and "pruebas" in caso
    plan_aplica = bool(modulos.get("plan")) and "plan_esperado" in caso and plan_estudiante is not None

    # Sin módulos se usan los pesos clásicos (pesos_sin_modulos): el puntaje no cambia.
    legacy = nivel_cfg.get("pesos_sin_modulos")
    if not pruebas_aplica and not plan_aplica and legacy:
        base_pesos = legacy
    else:
        base_pesos = nivel_cfg.get("pesos", PESOS_POR_DEFECTO)

    excluir: set[str] = set()
    if not pruebas_aplica:
        excluir.add("pruebas")
    if not plan_aplica:
        excluir.add("plan")
    # Un caso sin `diferenciales` en un nivel que los exige: el componente no aplica (§5.4 de NIVELES.md)
    if diferenciales_req > 0 and not caso.get("diferenciales"):
        excluir.add("diferenciales")
        diferenciales_req = 0
    pesos = _reescalar(base_pesos, excluir)

    # --- Componentes ----------------------------------------------------------------------
    frac_items = len(cumplidos) / max(len(caso["lista_verificacion"]), 1)
    frac_banderas = sum(b["cumplida"] for b in banderas) / max(len(banderas), 1)

    aciertos_dif = _aciertos_diferenciales(caso, dx_estudiante, diferenciales_estudiante or [])
    frac_diferenciales = (len(aciertos_dif) / max(diferenciales_req, 1)) if diferenciales_req > 0 else 0.0

    pruebas_eval = seguimiento.evaluar_pruebas(caso, session.pruebas_pedidas) if "pruebas" in caso else None
    plan_eval = seguimiento.evaluar_plan(caso, plan_estudiante, mensajes_est) if plan_aplica else None

    obt = {
        "checklist": pesos["checklist"] * frac_items,
        "diagnostico": pesos["diagnostico"] * (1.0 if correcto else 0.0),
        "banderas": pesos["banderas"] * frac_banderas,
        "diferenciales": pesos["diferenciales"] * frac_diferenciales,
        "pruebas": pesos["pruebas"] * pruebas_eval["factor"] if pruebas_aplica and pruebas_eval else 0.0,
        "plan": pesos["plan"] * plan_eval["factor"] if plan_aplica and plan_eval else 0.0,
    }
    puntaje_base = round(sum(obt.values()))
    descuento_pistas = round(session.pistas_usadas * penalizacion_pista)
    puntaje = max(0, puntaje_base - descuento_pistas)

    aprobado_desde = nivel_cfg.get("aprobado_desde", 70)
    aprobado = puntaje >= aprobado_desde

    # --- Seguridad clínica ----------------------------------------------------------------
    alertas = list(plan_eval["alertas_seguridad"]) if plan_eval else []
    bloquea = bool(nivel_cfg.get("modulos", {}).get("plan", {}).get("bloquea_aprobado_si_contraindicado", False))
    recorte_seguridad = None
    if alertas and bloquea:
        aprobado = False
        tope = aprobado_desde - 1
        if puntaje > tope:
            recorte_seguridad = {"puntaje_original": puntaje, "tope": tope}
            puntaje = tope

    desglose = {k: {"obtenido": round(obt[k], 2), "maximo": round(pesos[k], 2)} for k in COMPONENTES}
    desglose["pistas"] = {"descuento": descuento_pistas}
    if recorte_seguridad:
        desglose["seguridad"] = recorte_seguridad

    # --- Seguimiento (control) --------------------------------------------------------------
    seguimiento_res = None
    if plan_eval and modulos.get("seguimiento"):
        variables = dict(plan_eval["_variables"])
        if pruebas_aplica and pruebas_eval:
            variables["pidio_pruebas_esenciales"] = pruebas_eval["todas_esenciales"]
            variables["no_pidio_pruebas_esenciales"] = pruebas_eval["ninguna_esencial"]
        else:  # sin módulo de pruebas el predicado es neutro
            variables["pidio_pruebas_esenciales"] = True
            variables["no_pidio_pruebas_esenciales"] = False
        seguimiento_res = seguimiento.resolver_evolucion(caso, variables)

    # --- RAG y retroalimentación -----------------------------------------------------------
    citas = []
    if config.RAG_ENABLED:
        try:
            citas = await rag.consultar(caso.get("guia_ref"), query=f"{caso['diagnostico']} {dx_estudiante}")
        except Exception:
            citas = []

    pruebas_pub = None
    if pruebas_aplica and pruebas_eval:
        pruebas_pub = {k: pruebas_eval[k] for k in ("solicitadas", "esenciales_faltantes", "innecesarias", "costo_total")}
    plan_pub = {k: v for k, v in plan_eval.items() if k not in ("factor", "_variables")} if plan_eval else None

    feedback = " ".join(p for p in (
        _feedback_modulos(pruebas_pub, plan_pub),
        _feedback_base(correcto, caso, faltantes, banderas_faltantes),
    ) if p)
    if session.mensajes:
        try:
            narrativo = await llm.chat_once([
                {"role": "system", "content": prompts.SYSTEM_FEEDBACK},
                {"role": "user", "content": prompts.user_feedback(
                    caso, dx_estudiante, correcto, cumplidos, faltantes, banderas_faltantes,
                    citas=citas, extra=_texto_modulos_para_llm(pruebas_pub, plan_pub),
                )},
            ])
            if narrativo:
                # La alerta de seguridad nunca depende de que el modelo la mencione.
                feedback = (_feedback_modulos(None, plan_pub) + " " + narrativo).strip() if alertas else narrativo
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
        "pruebas": pruebas_pub,
        "plan": plan_pub,
        "seguimiento": seguimiento_res,
        "alertas_seguridad": alertas,
        "revision_clinica": seguimiento.resumen_revision(caso),
        "feedback": feedback,
        "citas": citas,
    }
