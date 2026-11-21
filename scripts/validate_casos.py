"""Validador de casos clínicos según AGENTS.md sección 5 y 7."""

import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASOS_PATH = ROOT / "data" / "casos.json"
PERSONAS_PATH = ROOT / "data" / "personas.json"

REQUIRED_FIELDS = [
    "id",
    "motivo_consulta",
    "sintomas",
    "antecedentes",
    "habitos",
    "datos_si_pregunta",
    "restricciones",
    "diagnostico",
    "diagnostico_alias",
    "lista_verificacion",
    "banderas_rojas",
]

ID_PATTERN = re.compile(r"^c_[a-z0-9]+_\d{2}$")


def norm(text: str) -> str:
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return f" {text.strip()} "


def contains_whole_phrase(target: str, container: str) -> bool:
    target_norm = norm(target)
    if not target_norm.strip():
        return False
    return target_norm in norm(container)


def validate() -> list[str]:
    errors: list[str] = []

    if not CASOS_PATH.exists():
        return [f"No existe el archivo de casos: {CASOS_PATH}"]
    if not PERSONAS_PATH.exists():
        return [f"No existe el archivo de personas: {PERSONAS_PATH}"]

    try:
        casos = json.loads(CASOS_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        return [f"Error al parsear casos.json: {e}"]

    try:
        personas = json.loads(PERSONAS_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        return [f"Error al parsear personas.json: {e}"]

    if not isinstance(casos, list):
        return ["casos.json debe ser una lista de casos."]
    if not isinstance(personas, list) or len(personas) == 0:
        return ["personas.json debe ser una lista con al menos una persona."]

    seen_ids: set[str] = set()

    for idx, caso in enumerate(casos):
        prefix = f"Caso [{idx}]"
        caso_id = caso.get("id") if isinstance(caso, dict) else None
        if caso_id:
            prefix = f"Caso '{caso_id}'"

        if not isinstance(caso, dict):
            errors.append(f"{prefix}: debe ser un objeto JSON.")
            continue

        # 1. Campos obligatorios
        for field in REQUIRED_FIELDS:
            if field not in caso:
                errors.append(f"{prefix}: falta campo obligatorio '{field}'.")

        # Formato de id
        if "id" in caso:
            if not isinstance(caso["id"], str) or not ID_PATTERN.match(caso["id"]):
                errors.append(f"{prefix}: id '{caso['id']}' no cumple el patrón 'c_<tema>_NN'.")
            elif caso["id"] in seen_ids:
                errors.append(f"{prefix}: id duplicado '{caso['id']}'.")
            else:
                seen_ids.add(caso["id"])

        # 2. Diagnóstico y alias
        diag = caso.get("diagnostico", "")
        aliases = caso.get("diagnostico_alias", [])
        if not isinstance(diag, str) or not diag.strip():
            errors.append(f"{prefix}: 'diagnostico' debe ser una cadena no vacía.")
        if not isinstance(aliases, list):
            errors.append(f"{prefix}: 'diagnostico_alias' debe ser una lista de cadenas.")
            aliases = []

        all_names = [diag] + [a for a in aliases if isinstance(a, str) and a.strip()]

        # 3. Restricciones
        restr = caso.get("restricciones")
        if not isinstance(restr, dict):
            errors.append(f"{prefix}: 'restricciones' debe ser un diccionario.")
            restr = {}
        else:
            sexo = restr.get("sexo")
            edad_min = restr.get("edad_min")
            edad_max = restr.get("edad_max")

            if not isinstance(sexo, list) or not set(sexo).issubset({"F", "M"}) or len(sexo) == 0:
                errors.append(f"{prefix}: restricciones.sexo debe ser una lista con 'F' y/o 'M'.")
            if not isinstance(edad_min, (int, float)) or not isinstance(edad_max, (int, float)):
                errors.append(f"{prefix}: restricciones.edad_min y edad_max deben ser numéricos.")
            elif edad_min > edad_max:
                errors.append(f"{prefix}: edad_min ({edad_min}) > edad_max ({edad_max}).")
            else:
                # Verificar compatibilidad con al menos una persona
                compatibles = [
                    p for p in personas
                    if p.get("sexo") in sexo and edad_min <= p.get("edad", -1) <= edad_max
                ]
                if not compatibles:
                    errors.append(
                        f"{prefix}: no existe ninguna persona en personas.json compatible con sexo={sexo} y edad=[{edad_min}, {edad_max}]."
                    )

        # 4. Listas no vacías
        for list_field in ["sintomas", "antecedentes", "habitos"]:
            val = caso.get(list_field)
            if not isinstance(val, list):
                errors.append(f"{prefix}: '{list_field}' debe ser una lista de textos.")

        # lista_verificacion y banderas_rojas
        lv = caso.get("lista_verificacion")
        if not isinstance(lv, list) or len(lv) == 0:
            errors.append(f"{prefix}: 'lista_verificacion' debe ser una lista no vacía.")
        else:
            for i, item in enumerate(lv):
                if not isinstance(item, dict) or "id" not in item or "texto" not in item or "keywords" not in item:
                    errors.append(f"{prefix}: item {i} de lista_verificacion inválido (requiere id, texto, keywords).")
                elif not isinstance(item["keywords"], list) or len(item["keywords"]) == 0:
                    errors.append(f"{prefix}: item '{item.get('id', i)}' de lista_verificacion tiene keywords vacías.")

        br = caso.get("banderas_rojas")
        if not isinstance(br, list) or len(br) == 0:
            errors.append(f"{prefix}: 'banderas_rojas' debe ser una lista no vacía.")
        else:
            for i, item in enumerate(br):
                if not isinstance(item, dict) or "id" not in item or "texto" not in item or "keywords" not in item:
                    errors.append(f"{prefix}: item {i} de banderas_rojas inválido (requiere id, texto, keywords).")
                elif not isinstance(item["keywords"], list) or len(item["keywords"]) == 0:
                    errors.append(f"{prefix}: item '{item.get('id', i)}' de banderas_rojas tiene keywords vacías.")

        # datos_si_pregunta
        dsp = caso.get("datos_si_pregunta")
        if not isinstance(dsp, dict):
            errors.append(f"{prefix}: 'datos_si_pregunta' debe ser un diccionario.")
            dsp = {}

        # 5. Fuga del diagnóstico o alias en campos visibles para el paciente
        campos_a_verificar: list[tuple[str, str]] = []
        if isinstance(caso.get("motivo_consulta"), str):
            campos_a_verificar.append(("motivo_consulta", caso["motivo_consulta"]))
        for s in caso.get("sintomas", []):
            if isinstance(s, str):
                campos_a_verificar.append(("sintomas", s))
        for a in caso.get("antecedentes", []):
            if isinstance(a, str):
                campos_a_verificar.append(("antecedentes", a))
        for h in caso.get("habitos", []):
            if isinstance(h, str):
                campos_a_verificar.append(("habitos", h))
        for k, v in dsp.items():
            if isinstance(k, str):
                campos_a_verificar.append(("datos_si_pregunta (clave)", k))
            if isinstance(v, str):
                campos_a_verificar.append(("datos_si_pregunta (valor)", v))

        # 6. Validación de pistas según pistas-por-caso.md
        pistas = caso.get("pistas")
        if pistas is not None:
            if not isinstance(pistas, list):
                errors.append(f"{prefix}: 'pistas' debe ser una lista.")
            else:
                pistas_by_item = {}
                for p_idx, p in enumerate(pistas):
                    if not isinstance(p, dict) or "item" not in p:
                        errors.append(f"{prefix}: pista {p_idx} no tiene campo 'item'.")
                        continue
                    item_key = p["item"]
                    pistas_by_item[item_key] = p
                    for lvl in ["nivel_1", "nivel_2", "nivel_3"]:
                        val = p.get(lvl)
                        if not isinstance(val, str) or not val.strip():
                            errors.append(f"{prefix}: pista '{item_key}' falta '{lvl}'.")
                        else:
                            words = val.strip().split()
                            if len(words) > 20:
                                errors.append(f"{prefix}: pista '{item_key}' {lvl} excede 20 palabras ({len(words)} palabras).")
                            campos_a_verificar.append((f"pista {item_key} ({lvl})", val))

                # Verificar que cada ítem de lista_verificacion tenga su pista
                if isinstance(lv, list):
                    for it in lv:
                        if isinstance(it, dict) and "id" in it and it["id"] not in pistas_by_item:
                            errors.append(f"{prefix}: falta pista para el ítem '{it['id']}' de lista_verificacion.")

        # Verificar también textos de lista_verificacion
        if isinstance(lv, list):
            for it in lv:
                if isinstance(it, dict) and "texto" in it:
                    campos_a_verificar.append((f"lista_verificacion ({it.get('id', '')})", it["texto"]))

        # 7. Fuga del diagnóstico o alias en campos visibles para el paciente
        for name in all_names:
            for campo_nombre, texto in campos_a_verificar:
                if contains_whole_phrase(name, texto):
                    errors.append(
                        f"{prefix}: el término diagnóstico '{name}' aparece en '{campo_nombre}': \"{texto}\"."
                    )

        # 8. Campo opcional guia_ref
        if "guia_ref" in caso:
            if not isinstance(caso["guia_ref"], str) or not caso["guia_ref"].strip():
                errors.append(f"{prefix}: 'guia_ref' debe ser una cadena no vacía.")

    return errors


def main():
    errors = validate()
    if errors:
        print(f"FAILED: Se encontraron {len(errors)} error(es) en los casos clínicos:\n")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("OK: Todos los casos clínicos son válidos.")
        sys.exit(0)


if __name__ == "__main__":
    main()
