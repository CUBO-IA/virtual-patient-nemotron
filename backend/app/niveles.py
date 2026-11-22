"""Gestión y reglas de niveles de práctica según NIVELES.md."""

from functools import lru_cache
import json
from pathlib import Path

from . import config, evaluate


@lru_cache(maxsize=1)
def cargar_niveles() -> dict:
    path = config.DATA_DIR / "niveles.json"
    if not path.exists():
        raise FileNotFoundError("Falta data/niveles.json")
    data = json.loads(path.read_text(encoding="utf-8"))

    # Validaciones fundamentales
    niveles = data.get("niveles", [])
    ids = {n["id"] for n in niveles if "id" in n}
    if ids != {1, 2, 3}:
        raise ValueError("niveles.json debe contener exactamente los niveles 1, 2 y 3")
    if data.get("nivel_por_defecto") not in ids:
        raise ValueError("nivel_por_defecto no es válido")

    for n in niveles:
        pesos = n.get("pesos", {})
        if sum(pesos.values()) != 100:
            raise ValueError(f"Los pesos del nivel {n.get('id')} deben sumar 100")
        # Pesos que se usan cuando los módulos de pruebas y plan no aplican (puntaje clásico).
        legacy = n.get("pesos_sin_modulos")
        if legacy is not None and sum(legacy.values()) != 100:
            raise ValueError(f"Los pesos_sin_modulos del nivel {n.get('id')} deben sumar 100")

    return data


def obtener_nivel(nivel_id: int | None = None) -> dict:
    """Retorna una copia de la configuración del nivel solicitado (o el por defecto)."""
    data = cargar_niveles()
    if nivel_id is None:
        nivel_id = data.get("nivel_por_defecto", 2)
    for n in data.get("niveles", []):
        if n["id"] == nivel_id:
            return dict(n)
    raise ValueError(f"Nivel {nivel_id} no existe en niveles.json")


@lru_cache(maxsize=1)
def cargar_guia_anamnesis() -> dict:
    path = config.DATA_DIR / "anamnesis_guia.json"
    if not path.exists():
        raise FileNotFoundError("Falta data/anamnesis_guia.json")
    return json.loads(path.read_text(encoding="utf-8"))


def guia_publica() -> list[dict]:
    """Retorna los ítems de la guía genérica sin keywords para la interfaz."""
    guia = cargar_guia_anamnesis()
    return [{"id": it["id"], "texto": it["texto"]} for it in guia.get("items", [])]


def calcular_guia_cubierta(mensajes_usuario: list[str]) -> list[str]:
    """Determina qué ítems de la guía genérica fueron cubiertos por el estudiante."""
    if not mensajes_usuario:
        return []
    guia = cargar_guia_anamnesis()
    texto_usuario = evaluate.norm(" . ".join(mensajes_usuario))
    cubiertos = []
    for it in guia.get("items", []):
        if evaluate._hit(it.get("keywords", []), texto_usuario):
            cubiertos.append(it["id"])
    return cubiertos


def health() -> bool:
    try:
        cargar_niveles()
        cargar_guia_anamnesis()
        return True
    except Exception:
        return False
