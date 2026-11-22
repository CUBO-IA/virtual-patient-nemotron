"""Explicación «¿Por qué?» de una decisión clínica, apoyada en guías (RAG).

Solo se usa tras /finish. El modelo redacta únicamente a partir de fragmentos recuperados;
si no hay fragmentos relevantes, se devuelve solo la nota escrita en el caso.
"""
import re

from . import config, llm, prompts, rag, seguimiento
from .sessions import Session

TIPOS = ("prueba", "medicamento", "indicacion", "disposicion")
MAX_FRAGMENTO = 900
_GENERICAS = {"oral", "prueba", "completo", "completa", "cuantitativa", "manejo", "estudio", "tratamiento", "ambulatorio", "hogar", "unidad", "salud"}


def rag_norm(t: str) -> str:
    import unicodedata
    t = unicodedata.normalize("NFD", t.lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")
_BIBLIOGRAFIA = re.compile(r"lecturas recomendadas|referencias|bibliograf|available from|doi\.org|https?://|cochrane database|\bet al\b", re.I)


def _terminos(titulo: str) -> list[str]:
    """Raíces (6 letras) de las palabras propias del título de la decisión."""
    out = []
    for w in re.findall(r"[a-zñ]+", rag_norm(titulo)):
        if len(w) >= 5 and w not in _GENERICAS:
            out.append(w[:6])
    return out


def _elegir(candidatos: list[dict], titulo: str, maximo: int = 3) -> list[dict]:
    """Búsqueda híbrida: primero los fragmentos que nombran la decisión; luego los semánticamente cercanos."""
    terminos = _terminos(titulo)
    lexicos = [c for c in candidatos if any(t in rag_norm(c["fragmento"]) for t in terminos)]
    cercanos = [c for c in candidatos if c.get("distancia", 0) <= config.RAG_MAX_DISTANCIA and c not in lexicos]
    return (lexicos + cercanos)[:maximo]


def _recorte(texto: str, titulo: str) -> str:
    """Recorta el fragmento alrededor del primer término propio de la decisión (si lo hay)."""
    if len(texto) <= MAX_FRAGMENTO:
        return texto
    bajo = rag_norm(texto)
    pos = min((bajo.find(t) for t in _terminos(titulo) if t in bajo), default=-1)
    ini = max(0, pos - MAX_FRAGMENTO // 3) if pos >= 0 else 0
    return texto[ini: ini + MAX_FRAGMENTO]


def resolver(caso: dict, resultado: dict, tipo: str, item_id: str) -> dict | None:
    """Título, valoración y nota (escrita en el caso) de un ítem. None si el ítem no existe."""
    if tipo == "prueba":
        p = seguimiento.obtener_prueba_catalogo(item_id)
        if not p:
            return None
        pert = caso.get("pruebas", {}).get("resultados", {}).get(item_id, {}).get("pertinencia")
        if item_id in caso.get("pruebas", {}).get("esenciales", []):
            pert = "esencial"
        valoracion = {"esencial": "prueba esencial", "util": "prueba útil"}.get(pert, "sin indicación clara en este caso")
        return {"titulo": p["nombre"], "valoracion": valoracion, "nota": p.get("nota")}
    if tipo == "medicamento":
        m = seguimiento.obtener_medicamento_catalogo(item_id)
        if not m:
            return None
        cfg = caso.get("plan_esperado", {}).get("medicamentos", {})
        for clave, val in (("adecuados", "adecuado"), ("aceptables", "aceptable"), ("contraindicados", "contraindicado")):
            for e in cfg.get(clave, []):
                if e["id"] == item_id:
                    return {"titulo": m["nombre"], "valoracion": val, "nota": e.get("nota") or e.get("motivo")}
        return {"titulo": m["nombre"], "valoracion": "innecesario en este caso", "nota": None}
    if tipo == "indicacion":
        i = seguimiento.obtener_indicacion_catalogo(item_id)
        return {"titulo": i["texto"], "valoracion": None, "nota": None} if i else None
    if tipo == "disposicion":
        d = seguimiento.obtener_disposicion_catalogo(item_id)
        return {"titulo": d["texto"], "valoracion": None, "nota": None} if d else None
    return None


async def explicar(session: Session, caso: dict, tipo: str, item_id: str) -> dict | None:
    info = resolver(caso, session.result or {}, tipo, item_id)
    if info is None:
        return None
    salida = {
        "tipo": tipo, "id": item_id, "titulo": info["titulo"], "valoracion": info["valoracion"],
        "nota": info["nota"], "explicacion": None, "fuentes": [], "origen": "caso",
    }
    if not config.RAG_ENABLED:
        return salida

    consulta = f"{info['titulo']} {caso['diagnostico']}"
    try:
        candidatos = await rag.consultar(caso.get("guia_ref"), consulta, top_k=6, max_distancia=config.RAG_MAX_DISTANCIA_LEXICA)
    except Exception:
        candidatos = []
    candidatos = [c for c in candidatos if not _BIBLIOGRAFIA.search(c["fragmento"])]
    frags = _elegir(candidatos, info["titulo"])
    if not frags:
        return salida

    frags = [{"fuente": f["fuente"], "fragmento": _recorte(f["fragmento"], info["titulo"])} for f in frags]
    if not frags:
        return salida
    salida["fuentes"] = frags
    salida["origen"] = "guia"
    try:
        texto = await llm.chat_once([
            {"role": "system", "content": prompts.SYSTEM_EXPLICAR},
            {"role": "user", "content": prompts.user_explicar(
                caso["diagnostico"], info["titulo"], info["valoracion"], info["nota"],
                [f["fragmento"] for f in frags])},
        ], num_predict=260)
    except llm.LLMError:
        texto = ""  # se devuelven los fragmentos literales como cita
    texto = (texto or "").strip()
    if "SIN_SUSTENTO" in texto:
        salida["fuentes"], salida["origen"] = [], "caso"
    else:
        salida["explicacion"] = texto or None
    return salida
