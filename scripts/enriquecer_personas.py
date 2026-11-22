"""Añade uuid y tipo de hogar verificando el orden original del dataset."""
import json
import os
import sys
import tempfile
from itertools import zip_longest
from itertools import islice
from pathlib import Path

try:
    from .build_personas import OUT, filas_validas
except ImportError:
    from build_personas import OUT, filas_validas

SENTINELA = object()


def enriquecer(personas, filas):
    """Devuelve una copia enriquecida; no modifica personas y aborta ante cualquier desajuste."""
    resultado = []
    for i, (persona, fila) in enumerate(zip_longest(personas, filas, fillvalue=SENTINELA), 1):
        if persona is SENTINELA or fila is SENTINELA:
            raise ValueError(f"La cantidad de filas no coincide con personas.json (desajuste en la persona {i}).")
        row, nombre, edad, _sexo = fila
        if (persona.get("nombre"), persona.get("edad"), persona.get("municipio")) != (
            nombre, edad, row.get("municipality")
        ):
            raise ValueError(
                f"La persona {i} ({persona.get('id')}) no coincide con el dataset en nombre, edad o municipio; no se escribió ningún cambio."
            )
        nueva = dict(persona)
        nueva["uuid"] = row.get("uuid")
        hogar = row.get("household_type")
        nueva["hogar"] = str(hogar).lower() if hogar not in (None, "") else None
        resultado.append(nueva)
    return resultado


def escribir_atomico(path: Path, personas):
    temporal = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, suffix=".tmp", delete=False) as f:
            temporal = Path(f.name)
            json.dump(personas, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(temporal, path)
    finally:
        if temporal and temporal.exists():
            temporal.unlink(missing_ok=True)


def enriquecer_archivo(path: Path, filas):
    originales = json.loads(path.read_text(encoding="utf-8"))
    actualizadas = enriquecer(originales, islice(filas, len(originales)))
    escribir_atomico(path, actualizadas)
    return actualizadas


def main():
    ruta = OUT
    try:
        actualizadas = enriquecer_archivo(ruta, filas_validas())
    except Exception as e:
        print(f"No se pudieron enriquecer las personas; personas.json quedó intacto: {e}", file=sys.stderr)
        return 1
    from collections import Counter
    distribucion = Counter(p["hogar"] or "(sin dato)" for p in actualizadas)
    print(f"{len(actualizadas)} personas actualizadas en {ruta}.")
    print("Distribución de hogar:", dict(sorted(distribucion.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
