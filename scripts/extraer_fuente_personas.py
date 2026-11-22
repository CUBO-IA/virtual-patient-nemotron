"""Extrae una copia local mínima de textos fuente para generar perfiles sociales."""
import json
import os
import sys
import tempfile
from itertools import islice, zip_longest
from pathlib import Path

try:
    from .build_personas import OUT as PERSONAS_PATH, filas_validas
except ImportError:
    from build_personas import OUT as PERSONAS_PATH, filas_validas

ROOT = Path(__file__).resolve().parents[1]
FUENTE_PATH = ROOT / "data" / "personas_fuente.json"
SENTINELA = object()
CAMPOS = ("family_persona", "culinary_persona", "sports_persona", "hobbies_and_interests", "professional_persona")


def crear_fuente(personas, filas):
    fuente = {}
    for i, (p, fila) in enumerate(zip_longest(personas, filas, fillvalue=SENTINELA), 1):
        if p is SENTINELA or fila is SENTINELA:
            raise ValueError(f"La cantidad de filas no coincide con personas.json (desajuste en la persona {i}).")
        row, nombre, edad, _sexo = fila
        if (p.get("nombre"), p.get("edad"), p.get("municipio")) != (nombre, edad, row.get("municipality")):
            raise ValueError(f"La persona {i} ({p.get('id')}) no coincide con nombre, edad o municipio; no se escribió ningún cambio.")
        fuente[p["id"]] = {
            "uuid": row.get("uuid"),
            "hogar": (row.get("household_type") or "").lower() or None,
            **{campo: row.get(campo) for campo in CAMPOS},
        }
    return fuente


def escribir_atomico(path: Path, objeto):
    temporal = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, suffix=".tmp", delete=False) as f:
            temporal = Path(f.name)
            json.dump(objeto, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(temporal, path)
    finally:
        if temporal and temporal.exists():
            temporal.unlink(missing_ok=True)


def main():
    try:
        personas = json.loads(PERSONAS_PATH.read_text(encoding="utf-8"))
        fuente = crear_fuente(personas, islice(filas_validas(), len(personas)))
        escribir_atomico(FUENTE_PATH, fuente)
        print(f"Fuente local guardada para {len(fuente)} personas en {FUENTE_PATH}.")
        return 0
    except Exception as e:
        print(f"No se pudo extraer la fuente; no se escribió el archivo: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
