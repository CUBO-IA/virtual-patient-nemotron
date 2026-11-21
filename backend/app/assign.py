import json
import random
from functools import lru_cache

from . import config


@lru_cache(maxsize=1)
def _load():
    personas_path = config.DATA_DIR / "personas.json"
    casos_path = config.DATA_DIR / "casos.json"
    if not personas_path.exists():
        raise FileNotFoundError("Falta data/personas.json. Ejecuta: python scripts/build_personas.py")
    if not casos_path.exists():
        raise FileNotFoundError("Falta data/casos.json")
    personas = json.loads(personas_path.read_text(encoding="utf-8"))
    casos = json.loads(casos_path.read_text(encoding="utf-8"))
    return personas, casos


def counts() -> tuple[int, int]:
    personas, casos = _load()
    return len(personas), len(casos)


def _compatible(p: dict, caso: dict) -> bool:
    r = caso.get("restricciones", {})
    if "sexo" in r and p["sexo"] not in r["sexo"]:
        return False
    if p["edad"] < r.get("edad_min", 0) or p["edad"] > r.get("edad_max", 200):
        return False
    return True


def sortear(caso_id: str | None = None) -> tuple[dict, dict]:
    """Elige un caso al azar (o el indicado) y una persona compatible. Prefiere ocupaciones y zonas típicas del caso."""
    personas, casos = _load()
    candidatos = [c for c in casos if c["id"] == caso_id] if caso_id else random.sample(casos, len(casos))
    for caso in candidatos:
        comp = [p for p in personas if _compatible(p, caso)]
        if not comp:
            continue
        r = caso.get("restricciones", {})
        ocup = [o.lower() for o in r.get("ocupaciones_tipicas", [])]
        deptos = r.get("departamentos_tipicos", [])
        pool = []
        if ocup:
            pool = [p for p in comp if any(o in (p["ocupacion"] or "").lower() for o in ocup)]
        if not pool and deptos:
            pool = [p for p in comp if p["departamento"] in deptos]
        return caso, random.choice(pool or comp)
    raise RuntimeError("Ningún caso es compatible con las personas cargadas")
