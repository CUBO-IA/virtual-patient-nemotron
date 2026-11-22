"""Sesiones de consulta.

Viven en memoria, pero cada cambio se guarda también en disco (`.sesiones/<id>.json`) para que
sobrevivan a un reinicio del servidor (por ejemplo, `uvicorn --reload` al editar código). Si una
sesión no está en memoria, `get()` intenta recuperarla del disco.

Solo se guardan referencias (`caso_id`, `persona_id`) y el estado de la consulta; el caso y la persona
se vuelven a leer de `data/`. Guardar es de mejor esfuerzo: si falla, la petición no se rompe.
"""
import json
import logging
import os
import re
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from . import config

log = logging.getLogger(__name__)

MAX_SESSIONS = 200
BUSY_TIMEOUT = 120  # segundos; evita que una conexión caída bloquee la sesión para siempre
VERSION_ARCHIVO = 1
DIR: Path = config.SESIONES_DIR  # las pruebas lo apuntan a una carpeta temporal

_ID_VALIDO = re.compile(r"[0-9a-f]{32}")
_INTERVALO_LIMPIEZA = 3600  # segundos
_ultima_limpieza = 0.0


@dataclass
class Session:
    id: str
    caso: dict
    persona: dict
    nivel: dict = field(default_factory=dict)
    mensajes: list = field(default_factory=list)  # [{"role": "user"|"assistant", "content": str}]
    finished: bool = False
    result: dict | None = None
    busy_at: float | None = None
    pistas_usadas: int = 0
    nivel_por_item: dict = field(default_factory=dict)  # {item_id: nivel (1..3)}
    pruebas_pedidas: list = field(default_factory=list)  # [prueba_id, ...] en orden sin repetir
    costo_pruebas: int = 0
    modulos_activos: dict = field(default_factory=dict)
    modo: str = "consulta"
    iniciada_en: float | None = None
    triaje: dict | None = None
    creada_en: float = field(default_factory=time.time)

    @property
    def preguntas_usadas(self) -> int:
        return sum(1 for m in self.mensajes if m.get("role") == "user")

    @property
    def busy(self) -> bool:
        return self.busy_at is not None and (time.time() - self.busy_at) < BUSY_TIMEOUT

    def lock(self):
        self.busy_at = time.time()

    def unlock(self):
        self.busy_at = None


_store: dict[str, Session] = {}


# ----------------------------------------------------------------------------- disco

def _ruta(session_id: str) -> Path | None:
    """Ruta del archivo de una sesión. None si el id no tiene la forma esperada (evita rutas raras)."""
    if not isinstance(session_id, str) or not _ID_VALIDO.fullmatch(session_id):
        return None
    return DIR / f"{session_id}.json"


def guardar(s: Session) -> bool:
    """Guarda el estado de la sesión en disco (escritura atómica). Devuelve False si no pudo."""
    ruta = _ruta(s.id)
    if ruta is None:
        return False
    datos = {
        "v": VERSION_ARCHIVO,
        "id": s.id,
        "caso_id": s.caso.get("id"),
        "persona_id": s.persona.get("id"),
        "nivel": s.nivel,
        "mensajes": s.mensajes,
        "finished": s.finished,
        "result": s.result,
        "pistas_usadas": s.pistas_usadas,
        "nivel_por_item": s.nivel_por_item,
        "pruebas_pedidas": s.pruebas_pedidas,
        "costo_pruebas": s.costo_pruebas,
        "modulos_activos": s.modulos_activos,
        "modo": s.modo,
        "iniciada_en": s.iniciada_en,
        "triaje": s.triaje,
        "creada_en": s.creada_en,
        "guardado": time.time(),
    }
    tmp = ruta.with_name(f".{ruta.stem}.{uuid.uuid4().hex[:8]}.tmp")
    try:
        DIR.mkdir(parents=True, exist_ok=True)
        tmp.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, ruta)
        return True
    except (OSError, TypeError, ValueError) as e:
        log.warning("No se pudo guardar la sesión %s: %s", s.id, e)
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        return False


def _cargar(session_id: str) -> Session | None:
    """Recupera una sesión del disco, o None si no existe, está corrupta o sus datos ya no existen."""
    ruta = _ruta(session_id)
    if ruta is None or not ruta.exists():
        return None
    from . import assign  # import local: assign no depende de sessions

    try:
        d = json.loads(ruta.read_text(encoding="utf-8"))
        if d.get("v") != VERSION_ARCHIVO or d.get("id") != session_id:
            raise ValueError("formato desconocido")
        modo = d.get("modo", "consulta")
        if modo == "urgencias":
            from . import urgencias  # import local: urgencias usa evaluate, que usa sessions

            caso = urgencias.buscar_caso(d["caso_id"])
        else:
            caso = assign.obtener_caso(d["caso_id"])
        persona = assign.obtener_persona(d["persona_id"])
        if caso is None or persona is None:
            log.warning("La sesión %s apunta a un caso o persona que ya no existe", session_id)
            return None
        mensajes = list(d.get("mensajes", []))
        # Una pregunta sin respuesta es de una petición que el reinicio interrumpió: se descarta
        # para que no cuente como pregunta usada ni deje el historial sin contestar.
        if mensajes and mensajes[-1].get("role") == "user":
            mensajes.pop()
        return Session(
            id=session_id,
            caso=caso,
            persona=persona,
            nivel=d.get("nivel", {}),
            mensajes=mensajes,
            finished=bool(d.get("finished")),
            result=d.get("result"),
            pistas_usadas=int(d.get("pistas_usadas", 0)),
            nivel_por_item=d.get("nivel_por_item", {}),
            pruebas_pedidas=list(d.get("pruebas_pedidas", [])),
            costo_pruebas=int(d.get("costo_pruebas", 0)),
            modulos_activos=d.get("modulos_activos", {}),
            modo=modo,
            iniciada_en=d.get("iniciada_en"),
            triaje=d.get("triaje"),
            creada_en=float(d.get("creada_en", d.get("guardado", time.time()))),
        )
    except (OSError, ValueError, KeyError, TypeError) as e:
        log.warning("Sesión %s ilegible, se descarta: %s", session_id, e)
        try:
            ruta.unlink(missing_ok=True)
        except OSError:
            pass
        return None


def limpiar() -> int:
    """Borra sesiones guardadas más viejas que el TTL y las que excedan el máximo. Devuelve cuántas borró."""
    borradas = 0
    try:
        if not DIR.exists():
            return 0
        ahora = time.time()
        limite = config.SESIONES_TTL_HORAS * 3600
        vigentes = []
        for p in DIR.iterdir():
            try:
                edad = ahora - p.stat().st_mtime
                if p.suffix == ".tmp":
                    if edad > 3600:
                        p.unlink(missing_ok=True)
                        borradas += 1
                elif p.suffix == ".json":
                    if edad > limite:
                        p.unlink(missing_ok=True)
                        borradas += 1
                    else:
                        vigentes.append((p.stat().st_mtime, p))
            except OSError:
                continue
        exceso = len(vigentes) - config.MAX_SESIONES_DISCO
        if exceso > 0:
            for _, p in sorted(vigentes, key=lambda x: x[0])[:exceso]:
                try:
                    p.unlink(missing_ok=True)
                    borradas += 1
                except OSError:
                    continue
    except OSError as e:
        log.warning("No se pudo limpiar la carpeta de sesiones: %s", e)
    return borradas


def _limpieza_periodica():
    global _ultima_limpieza
    ahora = time.time()
    if ahora - _ultima_limpieza >= _INTERVALO_LIMPIEZA:
        _ultima_limpieza = ahora
        limpiar()


# ----------------------------------------------------------------------------- memoria

def _hacer_espacio():
    if len(_store) >= MAX_SESSIONS:
        _store.pop(next(iter(_store)))  # descarta de memoria la más antigua (sigue en disco)


def create(caso: dict, persona: dict, nivel: dict | None = None, modo: str = "consulta") -> Session:
    _hacer_espacio()

    cfg_nivel = nivel or {}
    from . import seguimiento
    modulos = seguimiento.calcular_modulos_activos(cfg_nivel, caso)

    s = Session(
        id=uuid.uuid4().hex,
        caso=caso,
        persona=persona,
        nivel=cfg_nivel,
        modulos_activos=modulos,
        modo=modo,
        iniciada_en=time.time() if modo == "urgencias" else None,
    )
    _store[s.id] = s
    guardar(s)
    _limpieza_periodica()
    return s


def get(session_id: str) -> Session | None:
    s = _store.get(session_id)
    if s is None:
        s = _cargar(session_id)  # p. ej. el servidor se reinició desde que se creó
        if s is not None:
            _hacer_espacio()
            _store[s.id] = s
    return s


def casos_recientes_por_nivel(nivel_id: int, limite: int = 2) -> list[str]:
    """Ids de casos usados recientemente en ese nivel, contando sesiones activas y guardadas."""
    recientes: dict[str, float] = {}
    for s in _store.values():
        if s.modo == "consulta" and s.nivel.get("id") == nivel_id:
            recientes[s.caso.get("id", "")] = s.creada_en
    try:
        if DIR.exists():
            for ruta in DIR.glob("*.json"):
                try:
                    d = json.loads(ruta.read_text(encoding="utf-8"))
                    if d.get("modo", "consulta") == "consulta" and d.get("nivel", {}).get("id") == nivel_id:
                        cid = d.get("caso_id")
                        if cid:
                            recientes[cid] = float(d.get("creada_en", d.get("guardado", 0)))
                except (OSError, ValueError, TypeError):
                    continue
    except OSError:
        pass
    return [cid for cid, _ in sorted(recientes.items(), key=lambda item: item[1], reverse=True)[:limite]]
