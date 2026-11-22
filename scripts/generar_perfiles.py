"""Genera perfiles sociales concisos con Ollama y valida anclaje y contenido."""
import json
import os
import random
import re
import sys
import tempfile
import unicodedata
from collections import Counter
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PERSONAS_PATH = DATA / "personas.json"
FUENTE_PATH = DATA / "personas_fuente.json"
FIELDS = {"vive_con": 12, "dieta": 15, "actividad_fisica": 12, "trabajo": 15}
FUENTE_FIELDS = {
    "vive_con": ("household_type", "family_persona"),
    "dieta": ("culinary_persona",),
    "actividad_fisica": ("sports_persona", "hobbies_and_interests"),
    "trabajo": ("professional_persona",),
}
MODEL = "qwen2.5:7b"
OLLAMA = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
VERSION = 1


def normalizar(texto):
    s = unicodedata.normalize("NFD", str(texto).lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def _medicos(casos_path=None, urgencias_path=None):
    casos_path = casos_path or DATA / "casos.json"
    urgencias_path = urgencias_path or DATA / "urgencias.json"
    terms = {
        "diabetes", "azucar alta", "hipertension", "presion alta", "dengue", "cancer", "infarto",
        "enfermedad", "dolor", "tratamiento", "medicamento", "medicamentos", "pastilla", "pastillas",
        "medicina", "salud", "sintoma", "sintomas", "fiebre", "sangrado", "sangre", "vomito", "vomitos",
        "tos", "diarrea", "nausea", "nauseas", "presion arterial", "insulina", "depresion", "neumonia",
    }
    for path in (casos_path, urgencias_path):
        if not path.exists():
            continue
        for caso in json.loads(path.read_text(encoding="utf-8")):
            terms.add(normalizar(caso.get("diagnostico", "")))
            terms.update(normalizar(a) for a in caso.get("diagnostico_alias", []))
    return {x for x in terms if x}


def validar_campo(valor, fuente, max_palabras, terminos_medicos):
    """Retorna (valor aceptado o None, regla de rechazo o None). Función pura."""
    if valor is None:
        return None, None
    if not isinstance(valor, str):
        return None, "tipo"
    valor = valor.strip()
    if not valor:
        return None, None
    if "\n" in valor or "\r" in valor or re.search(r"[#*_`\[\]<>]", valor) or re.match(r"\s*(?:[-+>]\s|\d+[.)]\s)", valor):
        return None, "markdown"
    if len(valor.split()) > max_palabras:
        return None, "longitud"
    n_valor = normalizar(valor)
    padded = f" {n_valor} "
    if any(f" {term} " in padded for term in terminos_medicos):
        return None, "medico"
    palabras = [w for w in n_valor.split() if len(w) >= 5]
    if not palabras:
        return None, "anclaje"
    fuente_words = [w for w in normalizar(fuente).split() if len(w) >= 5]
    prefijos = {w[:5] for w in fuente_words}
    ancladas = sum(1 for w in palabras if w[:5] in prefijos)
    if ancladas / len(palabras) < 0.60:
        return None, "anclaje"
    return valor, None


def validar_perfil(perfil, textos, terminos_medicos=None):
    terminos_medicos = terminos_medicos if terminos_medicos is not None else _medicos()
    limpios, descartes = {}, Counter()
    if not isinstance(perfil, dict):
        return {k: None for k in FIELDS}, Counter({"formato": 1})
    for field, limite in FIELDS.items():
        fuente = " ".join(str(textos.get(k) or "") for k in FUENTE_FIELDS[field])
        valor, regla = validar_campo(perfil.get(field), fuente, limite, terminos_medicos)
        limpios[field] = valor
        if regla:
            descartes[regla] += 1
    return limpios, descartes


def _prompt_fuente(textos):
    nombres = {
        "household_type": "Tipo de hogar", "family_persona": "Vida familiar",
        "culinary_persona": "Alimentación", "sports_persona": "Deportes",
        "hobbies_and_interests": "Intereses", "professional_persona": "Trabajo",
    }
    return "\n".join(f"{nombres[k]}: {textos.get(k) or '(sin dato)'}" for k in nombres)


def pedir_perfil(client, textos):
    system = (
        "Extraes datos breves de una persona solo de los textos fuente. Responde únicamente un objeto JSON con las claves "
        "vive_con, dieta, actividad_fisica y trabajo; cada valor es una cadena o null. No agregues nada que no esté en el texto. "
        "No incluyas enfermedades, diagnósticos, síntomas, medicamentos ni consejos. Mantén los límites: vive_con 12 palabras, "
        "dieta 15, actividad_fisica 12 y trabajo 15. Si falta el dato, usa null."
    )
    response = client.post(f"{OLLAMA}/api/chat", json={
        "model": MODEL,
        "messages": [{"role":"system", "content":system}, {"role":"user", "content":_prompt_fuente(textos)}],
        "stream": False,
        "format": "json",
        "options": {"temperature": 0, "num_predict": 400, "num_ctx": 2048},
    })
    response.raise_for_status()
    contenido = response.json().get("message", {}).get("content", "{}")
    try:
        return json.loads(contenido)
    except json.JSONDecodeError as e:
        raise ValueError(f"Respuesta JSON inválida de Ollama: {e}; final recibido: {contenido[-240:]}") from e


def escribir_atomico(path, personas):
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


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    if not FUENTE_PATH.exists():
        print("Falta data/personas_fuente.json. Ejecuta scripts/extraer_fuente_personas.py primero.", file=sys.stderr)
        return 1
    try:
        with httpx.Client(timeout=httpx.Timeout(180, connect=5)) as client:
            health = client.get(f"{OLLAMA}/api/tags")
            health.raise_for_status()
            models = [m.get("name", "") for m in health.json().get("models", [])]
            if not any(m == MODEL or m.startswith(MODEL + ":") for m in models):
                raise RuntimeError(f"No está disponible el modelo {MODEL}. Descárgalo con: ollama pull {MODEL}")
            personas = json.loads(PERSONAS_PATH.read_text(encoding="utf-8"))
            fuente = json.loads(FUENTE_PATH.read_text(encoding="utf-8"))
            terminos = _medicos()
            descartes = Counter()
            for persona in personas:
                if persona.get("perfil_version") == VERSION:
                    continue
                texto = fuente.get(persona["id"])
                if texto is None:
                    raise ValueError(f"Falta fuente para {persona['id']}; se detiene sin perder los perfiles ya guardados.")
                try:
                    perfil_crudo = pedir_perfil(client, texto)
                except Exception as e:
                    print(f"Fallo en {persona['id']}: {e}", file=sys.stderr)
                    continue
                perfil, rechazados = validar_perfil(perfil_crudo, texto, terminos)
                descartes.update(rechazados)
                persona["perfil"] = perfil
                persona["perfil_version"] = VERSION
                escribir_atomico(PERSONAS_PATH, personas)
            completas = [p for p in personas if p.get("perfil_version") == VERSION]
            print(f"Perfiles con versión {VERSION}: {len(completas)}/{len(personas)}")
            for campo in FIELDS:
                n = sum(bool(p.get("perfil", {}).get(campo)) for p in completas)
                print(f"{campo}: {n} con valor")
            print("Descartes por validación:", dict(sorted(descartes.items())) or "ninguno")
            muestra = random.Random(42).sample(completas, min(15, len(completas)))
            print("\nMUESTRA PARA REVISIÓN HUMANA (perfil y fragmentos fuente):")
            for p in muestra:
                src = fuente[p["id"]]
                frag = " | ".join(str(src.get(k) or "")[:180] for k in ("family_persona", "culinary_persona", "sports_persona", "hobbies_and_interests", "professional_persona"))
                print(f"\n{p['id']} {p['nombre']} — {json.dumps(p.get('perfil', {}), ensure_ascii=False)}\nFuente: {frag}")
        return 0 if len(completas) == len(personas) else 1
    except Exception as e:
        print(f"No se pudo generar perfiles. Revisa Ollama y los datos: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
