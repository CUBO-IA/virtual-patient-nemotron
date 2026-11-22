"""Módulo de Pruebas, Plan de Tratamiento y Seguimiento Clínico (SEGUIMIENTO.md).

Carga catálogos clínicos, valida reglas de predicados deterministas,
resuelve ramas de evolución y provee utilidades para sesiones y evaluación.
"""

import ast
import json
from pathlib import Path

from . import config

CATALOGO_PRUEBAS_PATH = config.DATA_DIR / "catalogo_pruebas.json"
FORMULARIO_PATH = config.DATA_DIR / "formulario.json"

_catalogo_pruebas_cache: dict | None = None
_formulario_cache: dict | None = None

PREDICADOS_PERMITIDOS = {
    "disposicion_correcta",
    "disposicion_aceptable",
    "disposicion_insuficiente",
    "hay_contraindicado",
    "sin_contraindicados",
    "medicacion_adecuada_completa",
    "faltan_medicamentos_adecuados",
    "indicaciones_esenciales_completas",
    "faltan_indicaciones_esenciales",
    "pidio_pruebas_esenciales",
    "no_pidio_pruebas_esenciales",
    "alergia_ignorada",
}


def cargar_catalogo_pruebas() -> dict:
    global _catalogo_pruebas_cache
    if _catalogo_pruebas_cache is None:
        if not CATALOGO_PRUEBAS_PATH.exists():
            raise FileNotFoundError(f"No existe {CATALOGO_PRUEBAS_PATH}")
        _catalogo_pruebas_cache = json.loads(CATALOGO_PRUEBAS_PATH.read_text(encoding="utf-8"))
    return _catalogo_pruebas_cache


def cargar_formulario() -> dict:
    global _formulario_cache
    if _formulario_cache is None:
        if not FORMULARIO_PATH.exists():
            raise FileNotFoundError(f"No existe {FORMULARIO_PATH}")
        _formulario_cache = json.loads(FORMULARIO_PATH.read_text(encoding="utf-8"))
    return _formulario_cache


def catalogos_ok() -> bool:
    try:
        cp = cargar_catalogo_pruebas()
        form = cargar_formulario()
        return bool(cp.get("pruebas")) and bool(form.get("medicamentos"))
    except Exception:
        return False


def catalogo_pruebas_publico() -> dict:
    cp = cargar_catalogo_pruebas()
    return {
        "version": cp.get("version", 1),
        "categorias": cp.get("categorias", []),
        "pruebas": cp.get("pruebas", []),
    }


def formulario_publico() -> dict:
    form = cargar_formulario()
    return {
        "version": form.get("version", 1),
        "medicamentos": form.get("medicamentos", []),
        "indicaciones": form.get("indicaciones", []),
        "disposiciones": form.get("disposiciones", []),
    }


def obtener_prueba_catalogo(prueba_id: str) -> dict | None:
    cp = cargar_catalogo_pruebas()
    for p in cp.get("pruebas", []):
        if p["id"] == prueba_id:
            return p
    return None


def obtener_medicamento_catalogo(med_id: str) -> dict | None:
    form = cargar_formulario()
    for m in form.get("medicamentos", []):
        if m["id"] == med_id:
            return m
    return None


def obtener_disposicion_catalogo(disp_id: str) -> dict | None:
    form = cargar_formulario()
    for d in form.get("disposiciones", []):
        if d["id"] == disp_id:
            return d
    return None


def obtener_indicacion_catalogo(ind_id: str) -> dict | None:
    form = cargar_formulario()
    for i in form.get("indicaciones", []):
        if i["id"] == ind_id:
            return i
    return None


def resumen_revision(caso: dict) -> dict:
    """Estado de la revisión clínica que se muestra al estudiante (sin datos internos)."""
    rev = caso.get("revision_clinica") or {}
    validado = rev.get("estado") == "validado" and bool(rev.get("revisado_por"))
    return {
        "estado": "validado" if validado else "pendiente",
        "revisado_por": rev.get("revisado_por") if validado else None,
        "contenido_sin_validar": not validado,
    }


def calcular_modulos_activos(nivel: dict, caso: dict) -> dict:
    """Determina los módulos activos para una sesión (Nivel × revisión clínica × datos).

    Solo un caso `validado` activa los módulos, salvo en modo demostración
    (SEGUIMIENTO_DEMO=true). Si los catálogos no cargan, todo queda apagado.
    """
    rev = caso.get("revision_clinica", {})
    rev_ok = (rev.get("estado") == "validado" and bool(rev.get("revisado_por"))) or config.SEGUIMIENTO_DEMO
    if not catalogos_ok():
        rev_ok = False

    cfg_mod = nivel.get("modulos", {})
    p_cfg = cfg_mod.get("pruebas", {})
    plan_cfg = cfg_mod.get("plan", {})
    seg_cfg = cfg_mod.get("seguimiento", {})

    pruebas_habilitadas = bool(rev_ok and p_cfg.get("habilitado", False) and "pruebas" in caso)
    plan_habilitado = bool(rev_ok and plan_cfg.get("habilitado", False) and "plan_esperado" in caso)
    seguimiento_habilitado = bool(rev_ok and seg_cfg.get("habilitado", False) and "evolucion" in caso)

    return {
        "pruebas": p_cfg if pruebas_habilitadas else False,
        "plan": plan_habilitado,
        "seguimiento": seguimiento_habilitado,
    }


def evaluar_condicion_booleana(condicion: str, variables: dict[str, bool]) -> bool:
    """Evalúa de forma segura una expresión lógica compuesta por predicados permitidos.

    Soporta 'y', 'o', 'no' y paréntesis. Jamás utiliza eval().
    """
    if not condicion or not condicion.strip():
        return False

    # Reemplazar operadores en español por operadores python
    # Se reemplazan como palabras completas
    tokens_raw = condicion.strip()
    # Mapeo de operadores
    import re
    tokens_python = re.sub(r"\by\b", " and ", tokens_raw)
    tokens_python = re.sub(r"\bo\b", " or ", tokens_python)
    tokens_python = re.sub(r"\bno\b", " not ", tokens_python)

    try:
        # .strip(): «no x» queda « not  x» y un espacio inicial es un error de sintaxis en Python
        node = ast.parse(tokens_python.strip(), mode="eval")
    except SyntaxError as e:
        raise ValueError(f"Sintaxis inválida en condición: {condicion} ({e})")

    def _eval_node(n):
        if isinstance(n, ast.Expression):
            return _eval_node(n.body)
        elif isinstance(n, ast.Name):
            var_name = n.id
            if var_name not in PREDICADOS_PERMITIDOS:
                raise ValueError(f"Predicado no permitido: '{var_name}'")
            return bool(variables.get(var_name, False))
        elif isinstance(n, ast.BoolOp):
            if isinstance(n.op, ast.And):
                return all(_eval_node(val) for val in n.values)
            elif isinstance(n.op, ast.Or):
                return any(_eval_node(val) for val in n.values)
        elif isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.Not):
            return not _eval_node(n.operand)
        elif isinstance(n, ast.Constant) and isinstance(n.value, bool):
            return n.value
        raise ValueError(f"Operación o nodo no soportado en condición: {type(n).__name__}")

    return bool(_eval_node(node))


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def _norm(texto: str) -> str:
    import re
    import unicodedata

    t = unicodedata.normalize("NFD", (texto or "").lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return " " + re.sub(r"[^a-z0-9]+", " ", t).strip() + " "


def _nombre_prueba(prueba_id: str) -> str:
    p = obtener_prueba_catalogo(prueba_id)
    return p["nombre"] if p else prueba_id


def _nombre_medicamento(med_id: str) -> str:
    m = obtener_medicamento_catalogo(med_id)
    return m["nombre"] if m else med_id


class SeguimientoError(Exception):
    """Error de validación o de regla con su código HTTP y un mensaje para el estudiante."""

    def __init__(self, status: int, mensaje: str):
        super().__init__(mensaje)
        self.status = status
        self.mensaje = mensaje


# ---------------------------------------------------------------------------
# Módulo A: pruebas
# ---------------------------------------------------------------------------

def _resultado_prueba(caso: dict, prueba_id: str) -> dict:
    """Resultado visible para el estudiante. Nunca incluye `pertinencia` ni el diagnóstico."""
    cat = obtener_prueba_catalogo(prueba_id)
    datos = caso.get("pruebas", {})
    res = datos.get("resultados", {}).get(prueba_id)
    out = {
        "id": prueba_id,
        "nombre": cat["nombre"],
        "categoria": cat["categoria"],
        "costo": cat["costo"],
        "informe": res["informe"] if res else datos.get("resultado_defecto", "Sin hallazgos relevantes."),
    }
    if res and res.get("valores"):
        out["valores"] = res["valores"]
    return out


def estado_pruebas(sesion, ids: list[str] | None = None) -> dict:
    cfg = sesion.modulos_activos.get("pruebas") or {}
    ids = list(sesion.pruebas_pedidas) if ids is None else ids
    presupuesto = cfg.get("presupuesto")
    return {
        "resultados": [_resultado_prueba(sesion.caso, i) for i in ids],
        "pruebas_usadas": len(sesion.pruebas_pedidas),
        "limite": cfg.get("max"),
        "costo_total": sesion.costo_pruebas,
        "presupuesto": presupuesto,
        "presupuesto_restante": None if presupuesto is None else max(0, presupuesto - sesion.costo_pruebas),
        "mostrar_costo": bool(cfg.get("mostrar_costo", False)),
    }


def solicitar_pruebas(sesion, ids: list[str]) -> dict:
    """Pide pruebas en una tanda «todo o nada». Una prueba repetida no cuesta ni cuenta de nuevo."""
    cfg = sesion.modulos_activos.get("pruebas")
    if not cfg:
        raise SeguimientoError(404, "Este caso no incluye pruebas.")
    if sesion.finished:
        raise SeguimientoError(409, "La consulta ya terminó. Pulsa «Nuevo paciente».")

    unicos = list(dict.fromkeys(ids))
    for pid in unicos:
        if obtener_prueba_catalogo(pid) is None:
            raise SeguimientoError(422, f"Prueba desconocida: {pid}")

    nuevas = [p for p in unicos if p not in sesion.pruebas_pedidas]
    limite = cfg.get("max")
    if limite is not None and len(sesion.pruebas_pedidas) + len(nuevas) > limite:
        raise SeguimientoError(409, f"Alcanzaste el límite de {limite} pruebas de este nivel.")
    presupuesto = cfg.get("presupuesto")
    costo_nuevo = sum(obtener_prueba_catalogo(p)["costo"] for p in nuevas)
    if presupuesto is not None and sesion.costo_pruebas + costo_nuevo > presupuesto:
        raise SeguimientoError(409, f"Superarías el presupuesto de pruebas de este nivel ({presupuesto} puntos de costo).")

    sesion.pruebas_pedidas.extend(nuevas)
    sesion.costo_pruebas += costo_nuevo
    return estado_pruebas(sesion, unicos)


def evaluar_pruebas(caso: dict, pedidas: list[str]) -> dict:
    """Pertinencia de lo pedido. Solo se revela tras /finish."""
    datos = caso.get("pruebas", {})
    resultados = datos.get("resultados", {})
    esenciales = list(datos.get("esenciales", []))

    def pertinencia(pid: str) -> str:
        return resultados.get(pid, {}).get("pertinencia", "innecesaria")

    solicitadas = [
        {"id": pid, "nombre": _nombre_prueba(pid), "pertinencia": pertinencia(pid),
         "costo": (obtener_prueba_catalogo(pid) or {}).get("costo", 0)}
        for pid in pedidas
    ]
    esenciales_pedidas = [e for e in esenciales if e in pedidas]
    faltantes = [_nombre_prueba(e) for e in esenciales if e not in pedidas]
    innecesarias = [_nombre_prueba(p) for p in pedidas if pertinencia(p) == "innecesaria"]

    frac = (len(esenciales_pedidas) / len(esenciales)) if esenciales else 1.0
    factor = max(0.0, min(1.0, frac - 0.2 * len(innecesarias)))  # 0,2 por cada innecesaria
    return {
        "solicitadas": solicitadas,
        "esenciales_faltantes": faltantes,
        "esenciales_faltantes_ids": [e for e in esenciales if e not in pedidas],
        "innecesarias": innecesarias,
        "costo_total": sum(s["costo"] for s in solicitadas),
        "factor": factor,
        "todas_esenciales": len(esenciales_pedidas) == len(esenciales),
        "ninguna_esencial": bool(esenciales) and not esenciales_pedidas,
    }


# ---------------------------------------------------------------------------
# Módulo B: plan de tratamiento
# ---------------------------------------------------------------------------

def validar_plan(plan: dict | None) -> dict:
    """Valida el plan contra los catálogos y lo devuelve normalizado."""
    if not plan:
        raise SeguimientoError(422, "Falta el plan de tratamiento.")
    if obtener_disposicion_catalogo(plan.get("disposicion")) is None:
        raise SeguimientoError(422, "Elige una disposición válida para el paciente.")

    meds = plan.get("medicamentos") or []
    ids = [m["id"] for m in meds]
    for mid in ids:
        if obtener_medicamento_catalogo(mid) is None:
            raise SeguimientoError(422, f"Medicamento desconocido: {mid}")
    if len(set(ids)) != len(ids):
        raise SeguimientoError(422, "No repitas medicamentos en el plan.")

    sin_tx = bool(plan.get("sin_tratamiento_farmacologico"))
    if sin_tx and ids:
        raise SeguimientoError(422, "Marcaste «sin tratamiento farmacológico» pero elegiste medicamentos.")
    if not sin_tx and not ids:
        raise SeguimientoError(422, "Elige al menos un medicamento o marca «sin tratamiento farmacológico».")

    indicaciones = list(dict.fromkeys(plan.get("indicaciones") or []))
    for iid in indicaciones:
        if obtener_indicacion_catalogo(iid) is None:
            raise SeguimientoError(422, f"Indicación desconocida: {iid}")

    control = plan.get("control_dias")
    if control is not None and not (1 <= int(control) <= 14):
        raise SeguimientoError(422, "El control debe ser entre 1 y 14 días.")

    return {
        "disposicion": plan["disposicion"],
        "medicamentos": meds,
        "sin_tratamiento_farmacologico": sin_tx,
        "indicaciones": indicaciones,
        "control_dias": control,
    }


def evaluar_plan(caso: dict, plan: dict, mensajes_estudiante: list[str]) -> dict:
    """Veredicto del plan frente a `plan_esperado`. Las dosis NO se puntúan (v1)."""
    esperado = caso.get("plan_esperado", {})
    meds_cfg = esperado.get("medicamentos", {})
    adecuados = {m["id"]: m for m in meds_cfg.get("adecuados", [])}
    aceptables = {m["id"]: m for m in meds_cfg.get("aceptables", [])}
    contraindicados = {m["id"]: m for m in meds_cfg.get("contraindicados", [])}
    trampas = {t["medicamento"]: t for t in esperado.get("alergias_trampa", [])}

    texto_est = _norm(" . ".join(mensajes_estudiante))
    pregunto_alergias = " alergi" in texto_est

    elegidos = [m["id"] for m in plan["medicamentos"]]
    medicamentos, alertas = [], []
    n_adecuados = n_aceptables = n_innecesarios = 0
    hay_contra = False
    alergia_ignorada = False

    for mid in elegidos:
        nombre = _nombre_medicamento(mid)
        if mid in contraindicados:
            veredicto, nota = "contraindicado", contraindicados[mid].get("motivo")
            alertas.append(f"{nombre}: {nota}")
            hay_contra = True
        elif mid in trampas:
            veredicto, nota = "contraindicado", trampas[mid].get("dato")
            alertas.append(f"{nombre}: {nota}")
            hay_contra = True
            if not pregunto_alergias:
                alergia_ignorada = True
                alertas.append("Alergia no explorada: no preguntaste por alergias a medicamentos antes de recetar.")
        elif mid in adecuados:
            veredicto, nota = "adecuado", adecuados[mid].get("nota")
            n_adecuados += 1
        elif mid in aceptables:
            veredicto, nota = "aceptable", aceptables[mid].get("nota")
            n_aceptables += 1
        else:
            veredicto, nota = "innecesario", None
            n_innecesarios += 1
        medicamentos.append({"id": mid, "nombre": nombre, "veredicto": veredicto, "nota": nota})

    faltantes_med = [_nombre_medicamento(i) for i in adecuados if i not in elegidos]

    # Medicación: adecuados / totales (aceptable cuenta 0,5), -0,15 por innecesario; contraindicado -> 0
    if hay_contra:
        frac_med = 0.0
    else:
        base = ((n_adecuados + 0.5 * n_aceptables) / len(adecuados)) if adecuados else 1.0
        frac_med = max(0.0, min(1.0, base) - 0.15 * n_innecesarios)

    # Disposición
    disp = esperado.get("disposicion", {})
    elegida = plan["disposicion"]
    if elegida in disp.get("correcta", []):
        veredicto_disp, frac_disp = "correcta", 1.0
    elif elegida in disp.get("aceptable", []):
        veredicto_disp, frac_disp = "aceptable", 0.5
    else:
        veredicto_disp, frac_disp = "insuficiente", 0.0

    # Indicaciones esenciales
    esenciales = esperado.get("indicaciones", {}).get("esenciales", [])
    cumplidas = [i for i in esenciales if i in plan["indicaciones"]]
    faltantes_ind = [i for i in esenciales if i not in plan["indicaciones"]]
    frac_ind = (len(cumplidas) / len(esenciales)) if esenciales else 1.0

    def _texto_ind(iid: str) -> str:
        i = obtener_indicacion_catalogo(iid)
        return i["texto"] if i else iid

    disp_cat = obtener_disposicion_catalogo(elegida) or {}
    return {
        "medicamentos": medicamentos,
        "medicamentos_faltantes": faltantes_med,
        "medicamentos_faltantes_ids": [i for i in adecuados if i not in elegidos],
        "disposicion": {"elegida": elegida, "texto": disp_cat.get("texto", elegida), "veredicto": veredicto_disp},
        "indicaciones": {
            "cumplidas": [_texto_ind(i) for i in cumplidas],
            "faltantes": [_texto_ind(i) for i in faltantes_ind],
            "faltantes_ids": list(faltantes_ind),
        },
        "alertas_seguridad": alertas,
        "factor": 0.5 * frac_med + 0.3 * frac_disp + 0.2 * frac_ind,
        "_variables": {
            "disposicion_correcta": veredicto_disp == "correcta",
            "disposicion_aceptable": veredicto_disp == "aceptable",
            "disposicion_insuficiente": veredicto_disp == "insuficiente",
            "hay_contraindicado": hay_contra,
            "sin_contraindicados": not hay_contra,
            "medicacion_adecuada_completa": not faltantes_med,
            "faltan_medicamentos_adecuados": bool(faltantes_med),
            "indicaciones_esenciales_completas": not faltantes_ind,
            "faltan_indicaciones_esenciales": bool(faltantes_ind),
            "alergia_ignorada": alergia_ignorada,
        },
    }


# ---------------------------------------------------------------------------
# Módulo C: seguimiento (control)
# ---------------------------------------------------------------------------

ORDEN_RAMAS = ("empeora", "parcial", "mejora")  # la seguridad manda: «empeora» se evalúa primero


def resolver_evolucion(caso: dict, variables: dict[str, bool]) -> dict | None:
    """Elige la rama de evolución del control con reglas (sin modelo). Devuelve texto pregrabado."""
    evo = caso.get("evolucion")
    if not evo or not evo.get("ramas"):
        return None
    ramas = evo["ramas"]
    for nombre in ORDEN_RAMAS:
        rama = ramas.get(nombre)
        if not rama:
            continue
        try:
            if evaluar_condicion_booleana(rama.get("condicion", ""), variables):
                return {"dias": evo.get("control_en_dias"), "evolucion": nombre, "relato": rama.get("relato", "")}
        except ValueError:
            continue  # condición inválida: la ignora (el validador de datos ya la reporta)
    rama = ramas.get("parcial") or next(iter(ramas.values()))
    return {"dias": evo.get("control_en_dias"), "evolucion": "parcial", "relato": rama.get("relato", "")}
