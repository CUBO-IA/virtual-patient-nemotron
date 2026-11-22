"""Dataset nvidia/Nemotron-Personas-El-Salvador -> data/personas.json

Columnas reales usadas del dataset: sex, age, occupation, department, municipality,
area, education_level, marital_status. El dataset NO trae columna de nombre: el
primer nombre se extrae del texto de las columnas *_persona ("Oseas, de 29 años ...").
Las personas sin nombre extraible se descartan.

Uso:  python scripts/build_personas.py [N]
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

from datasets import load_dataset

OUT = Path(__file__).resolve().parent.parent / "data" / "personas.json"
SEED = 42

UP = "A-ZÁÉÍÓÚÑ"
LOW = "a-záéíóúñü"
NAME_RE = re.compile(rf"^([{UP}][{LOW}]+(?: [{UP}][{LOW}]+)?),\s+(?:de\s+)?\d+")
NAME_FIELDS = ["professional_persona", "sports_persona", "arts_persona", "family_persona", "culinary_persona"]


def extract_name(row):
    votes = Counter()
    for f in NAME_FIELDS:
        text = (row.get(f) or "").replace(" ", " ").replace("\xa0", " ")
        m = NAME_RE.match(text)
        if m:
            votes[m.group(1)] += 1
    return votes.most_common(1)[0][0] if votes else None


def estilo(row):
    edu = (row.get("education_level") or "").lower()
    rural = (row.get("area") or "").lower() == "rural"
    if "univers" in edu or "superior" in edu or "posgrado" in edu:
        base = "habla con claridad y vocabulario variado, pero sin tecnicismos médicos"
    elif "bachiller" in edu:
        base = "habla con claridad, lenguaje cotidiano y algunos modismos salvadoreños"
    elif any(k in edu for k in ("primaria", "ningun", "sin_", "sin ", "parvularia", "basica", "básica")):
        base = "habla muy sencilla, frases cortas, modismos salvadoreños"
    else:
        base = "habla sencilla, frases cortas y modismos salvadoreños"
    extra = ", con expresiones del campo" if rural else ""
    return f"{base}{extra}; trata de usted al doctor"


def filas_validas():
    """Filas del dataset en orden reproducible, después de los filtros canónicos."""
    ds = load_dataset("nvidia/Nemotron-Personas-El-Salvador", split="train", streaming=True)
    ds = ds.shuffle(seed=SEED, buffer_size=2000)
    for row in ds:
        try:
            edad = int(row["age"])
        except (TypeError, ValueError):
            continue
        if edad < 18:
            continue
        nombre = extract_name(row)
        sexo = {"Masculino": "M", "Femenino": "F"}.get(row.get("sex"))
        if not nombre or not sexo:
            continue
        yield row, nombre, edad, sexo


def main(n=None):
    n = n if n is not None else (int(sys.argv[1]) if len(sys.argv) > 1 else 150)
    personas, vistos = [], 0
    for row, nombre, edad, sexo in filas_validas():
        vistos += 1
        p_data = {
            "id": f"p_{len(personas) + 1:03d}",
            "nombre": nombre,
            "edad": edad,
            "sexo": sexo,
            "ocupacion": row.get("occupation") or "sin dato",
            "departamento": row.get("department"),
            "municipio": row.get("municipality"),
            "area": row.get("area"),
            "nivel_educativo": row.get("education_level"),
            "estado_civil": row.get("marital_status"),
            "uuid": row.get("uuid"),
            "hogar": (row.get("household_type") or "").lower() or None,
            "estilo": estilo(row),
        }
        es_oriente = p_data["departamento"] in {"San Miguel", "Usulután", "La Unión", "Morazán"}
        p_data["habla"] = {
            "trato_medico": "usted",
            "aspiracion": "media" if es_oriente else "ninguna",
            "voseo_con_familia": True,
            "regionalismos": ["calentura", "cuerpo cortado", "ruco", "pisto"] if edad >= 60 else ["calentura", "cipote", "ahorita", "cabal"],
        }
        personas.append(p_data)
        if len(personas) >= n:
            break

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(personas, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(personas)} personas guardadas en {OUT} (filas leídas: {vistos})")
    print("nivel_educativo:", Counter(p["nivel_educativo"] for p in personas).most_common())
    print("sexo:", Counter(p["sexo"] for p in personas).most_common())
    print("área:", Counter(p["area"] for p in personas).most_common())


if __name__ == "__main__":
    main()
