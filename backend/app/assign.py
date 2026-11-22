"""Asignación de caso clínico y persona según relacion-persona-enfermedad.md.

Implementa 4 capas:
1. Reglas duras: descarta incompatibilidades absolutas (edad, sexo).
2. Prevalencia: ponderación epidemiológica base (1 a 3).
3. Similitud semántica: afinidad entre el perfil de la persona
   (ocupación, hábitos, área rural/urbana, departamento, edad) y la enfermedad.
4. Sorteo ponderado: peso = prevalencia * (0.5 + similitud).
"""

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


def obtener_caso(caso_id: str) -> dict | None:
    """Caso por id (para restaurar una sesión guardada en disco)."""
    _, casos = _load()
    return next((c for c in casos if c.get("id") == caso_id), None)


def obtener_persona(persona_id: str) -> dict | None:
    personas, _ = _load()
    return next((p for p in personas if p.get("id") == persona_id), None)


def counts() -> tuple[int, int]:
    personas, casos = _load()
    return len(personas), len(casos)


def _compatible(p: dict, caso: dict) -> bool:
    """Capa 1: Reglas duras de compatibilidad biológica y etaria."""
    r = caso.get("restricciones", {})
    if "sexo" in r and p.get("sexo") not in r["sexo"]:
        return False
    edad = p.get("edad", 0)
    if edad < r.get("edad_min", 0) or edad > r.get("edad_max", 200):
        return False
    return True


def afinidad_semantica(persona: dict, caso: dict) -> float:
    """Capa 3: Calcula similitud semántica y epidemiológica [0.0, 1.0]

    entre el perfil sociodemográfico de la persona y los factores de riesgo de la enfermedad.
    """
    score = 0.0
    r = caso.get("restricciones", {})

    # 1. Afinidad ocupacional (hasta 0.35)
    ocup_persona = (persona.get("ocupacion") or "").lower()
    ocup_tipicas = [o.lower() for o in r.get("ocupaciones_tipicas", [])]
    if ocup_tipicas:
        if any(o in ocup_persona for o in ocup_tipicas):
            score += 0.35
        else:
            # Palabras clave del entorno laboral en hábitos del caso
            habitos_str = " ".join(caso.get("habitos", [])).lower()
            tokens = [t for t in ocup_persona.split() if len(t) > 3 and t not in ("para", "otras", "actividades")]
            if any(t in habitos_str for t in tokens):
                score += 0.15
    else:
        score += 0.18  # caso general sin ocupación restrictiva

    # 2. Afinidad geográfica / departamental (hasta 0.25)
    deptos_tipicos = r.get("departamentos_tipicos", [])
    depto_persona = persona.get("departamento")
    if deptos_tipicos:
        if depto_persona in deptos_tipicos:
            score += 0.25
    else:
        score += 0.15

    # 3. Afinidad de entorno (área rural / urbana y estilo de vida) (hasta 0.20)
    area = (persona.get("area") or "").lower()
    contexto = " ".join(caso.get("habitos", []) + list(caso.get("datos_si_pregunta", {}).values())).lower()
    if area == "rural":
        if any(k in contexto for k in ("zancudo", "campo", "fumiga", "leña", "pila", "barril", "chorro", "cultiv", "agric")):
            score += 0.20
        else:
            score += 0.10
    elif area == "urbano":
        if any(k in contexto for k in ("moto", "estres", "calle", "mercado", "restaurante", "pupusa", "puesto", "gaseosa", "pan dulce")):
            score += 0.20
        else:
            score += 0.10
    else:
        score += 0.10

    # 4. Afinidad etaria dentro del rango permitido (hasta 0.20)
    edad = persona.get("edad", 30)
    cid = caso.get("id", "")
    if cid in ("c_hta_01", "c_dm2_01", "c_nac_01") and edad >= 50:
        score += 0.20
    elif cid == "c_trauma_01" and edad <= 35:
        score += 0.20
    elif cid == "c_erc_01" and 30 <= edad <= 55:
        score += 0.20
    elif cid == "c_depresion_01" and edad >= 40:
        score += 0.20
    else:
        score += 0.10

    return min(max(score, 0.0), 1.0)


def calcular_peso(persona: dict, caso: dict) -> float:
    """Capa 4: Combina reglas duras, prevalencia y similitud semántica.

    peso = prevalencia * (0.5 + similitud) si cumple reglas duras; 0 en caso contrario.
    """
    if not _compatible(persona, caso):
        return 0.0
    prevalencia = float(caso.get("prevalencia", 2))
    sim = afinidad_semantica(persona, caso)
    return prevalencia * (0.5 + sim)


def sortear(caso_id: str | None = None, nivel: dict | None = None, casos_recientes: list[str] | None = None) -> tuple[dict, dict]:
    """Sorteo de caso y persona compatible con alta coherencia semántica y filtro por nivel.

    - Si se indica caso_id: valida dificultad contra el nivel y sortea una persona compatible.
    - Si caso_id es None: filtra casos por dificultad_max y pondera favoreciendo la dificultad del nivel.
    """
    personas, casos = _load()

    dif_max = 3
    peso_dif_igual = 1
    nivel_id = None
    if nivel:
        dif_max = nivel.get("casos", {}).get("dificultad_max", 3)
        peso_dif_igual = nivel.get("casos", {}).get("peso_dificultad_igual", 2)
        nivel_id = nivel.get("id")

    casos_candidatos = [c for c in casos if c.get("dificultad", 1) <= dif_max]
    if not casos_candidatos:
        raise RuntimeError(f"No hay casos disponibles con dificultad <= {dif_max}")

    if caso_id:
        caso = next((c for c in casos if c["id"] == caso_id), None)
        if not caso:
            raise RuntimeError(f"Caso con id '{caso_id}' no encontrado.")
        if caso.get("dificultad", 1) > dif_max:
            raise ValueError(
                f"El caso '{caso_id}' tiene dificultad {caso.get('dificultad')} superior a la permitida ({dif_max}) para este nivel."
            )
        compatibles = [p for p in personas if _compatible(p, caso)]
        if not compatibles:
            raise RuntimeError(f"No hay personas compatibles para el caso {caso_id}")
        pesos = [0.5 + afinidad_semantica(p, caso) for p in compatibles]
        persona_elegida = random.choices(compatibles, weights=pesos, k=1)[0]
        return caso, persona_elegida

    # Evita repetir los dos casos más recientes del mismo nivel cuando hay alternativas.
    excluidos = set(casos_recientes or [])
    diversos = [c for c in casos_candidatos if c.get("id") not in excluidos]
    if diversos:
        casos_candidatos = diversos

    # Ponderar casos elegibles por prevalencia y dificultad del nivel
    pesos_casos = []
    for c in casos_candidatos:
        p = float(c.get("prevalencia", 2))
        if nivel_id and c.get("dificultad") == nivel_id:
            p *= peso_dif_igual
        pesos_casos.append(p)

    # Intentar asignar caso ponderado con persona compatible por afinidad
    indices_ordenados = list(range(len(casos_candidatos)))
    for _ in range(50):
        c_idx = random.choices(indices_ordenados, weights=pesos_casos, k=1)[0]
        caso_elegido = casos_candidatos[c_idx]
        compatibles = [p for p in personas if _compatible(p, caso_elegido)]
        if compatibles:
            pesos_p = [0.5 + afinidad_semantica(p, caso_elegido) for p in compatibles]
            persona_elegida = random.choices(compatibles, weights=pesos_p, k=1)[0]
            return caso_elegido, persona_elegida

    raise RuntimeError("Ningún caso es compatible con las personas cargadas para este nivel")
