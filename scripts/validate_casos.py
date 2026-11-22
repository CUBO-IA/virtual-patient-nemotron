"""Validador de casos clínicos según AGENTS.md sección 5 y 7."""

import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASOS_PATH = ROOT / "data" / "casos.json"
PERSONAS_PATH = ROOT / "data" / "personas.json"
NIVELES_PATH = ROOT / "data" / "niveles.json"
GUIA_PATH = ROOT / "data" / "anamnesis_guia.json"

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
    "dificultad",
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

        # 8. Validación de dificultad y diferenciales (NIVELES.md)
        dif = caso.get("dificultad")
        if dif is not None:
            if not isinstance(dif, int) or dif not in (1, 2, 3):
                errors.append(f"{prefix}: 'dificultad' debe ser un entero entre 1 y 3 (obtenido: {dif}).")

        diferenciales = caso.get("diferenciales")
        if dif == 3 and not diferenciales:
            errors.append(f"{prefix}: casos con dificultad 3 deben incluir 'diferenciales'.")

        if diferenciales is not None:
            if not isinstance(diferenciales, list):
                errors.append(f"{prefix}: 'diferenciales' debe ser una lista.")
            else:
                for d_idx, d in enumerate(diferenciales):
                    if not isinstance(d, dict) or "nombre" not in d or "alias" not in d:
                        errors.append(f"{prefix}: diferencial {d_idx} inválido (requiere 'nombre' y 'alias').")
                        continue
                    d_nom = d.get("nombre", "")
                    d_aliases = d.get("alias", [])
                    if not isinstance(d_nom, str) or not d_nom.strip():
                        errors.append(f"{prefix}: diferencial {d_idx} 'nombre' debe ser no vacío.")
                    if not isinstance(d_aliases, list):
                        errors.append(f"{prefix}: diferencial {d_idx} 'alias' debe ser lista.")
                    else:
                        d_all = [d_nom] + [a for a in d_aliases if isinstance(a, str) and a.strip()]
                        for n_dif in d_all:
                            for campo_nombre, texto in campos_a_verificar:
                                if contains_whole_phrase(n_dif, texto):
                                    errors.append(
                                        f"{prefix}: el diferencial '{n_dif}' aparece en '{campo_nombre}': \"{texto}\"."
                                    )

        # 9. Campo opcional guia_ref
        if "guia_ref" in caso:
            if not isinstance(caso["guia_ref"], str) or not caso["guia_ref"].strip():
                errors.append(f"{prefix}: 'guia_ref' debe ser una cadena no vacía.")

    # 10. Validación de balance por niveles (§11.2)
    casos_n1 = [c for c in casos if isinstance(c, dict) and c.get("dificultad", 99) <= 1]
    casos_n2 = [c for c in casos if isinstance(c, dict) and c.get("dificultad", 99) <= 2]
    casos_n3 = [c for c in casos if isinstance(c, dict) and c.get("dificultad", 99) <= 3]
    if len(casos_n1) < 3:
        errors.append(f"Nivel 1 debe tener al menos 3 casos elegibles (obtenidos: {len(casos_n1)}).")
    if len(casos_n2) < 3:
        errors.append(f"Nivel 2 debe tener al menos 3 casos elegibles (obtenidos: {len(casos_n2)}).")
    if len(casos_n3) < 3:
        errors.append(f"Nivel 3 debe tener al menos 3 casos elegibles (obtenidos: {len(casos_n3)}).")

    # 11. Validación de data/niveles.json si existe
    if NIVELES_PATH.exists():
        try:
            niveles_data = json.loads(NIVELES_PATH.read_text(encoding="utf-8"))
            niveles_list = niveles_data.get("niveles", [])
            ids_vistos = set()
            for n in niveles_list:
                nid = n.get("id")
                ids_vistos.add(nid)
                pesos = n.get("pesos", {})
                if sum(pesos.values()) != 100:
                    errors.append(f"Nivel {nid}: los pesos no suman 100 (suma: {sum(pesos.values())}).")
                dif_req = n.get("diferenciales_requeridos", 0)
                dif_peso = pesos.get("diferenciales", 0)
                if dif_req > 0 and dif_peso <= 0:
                    errors.append(f"Nivel {nid}: requiere diferenciales pero su peso es 0.")
                if not n.get("pistas", {}).get("permitidas", True) and n.get("pistas", {}).get("max") != 0:
                    errors.append(f"Nivel {nid}: pistas no permitidas debe tener max=0.")
                if n.get("actitud_paciente") not in ("colaborador", "normal", "reservado"):
                    errors.append(f"Nivel {nid}: actitud_paciente '{n.get('actitud_paciente')}' inválida.")

            if ids_vistos != {1, 2, 3}:
                errors.append(f"niveles.json debe contener exactamente los niveles 1, 2 y 3 (obtenidos: {ids_vistos}).")
            if niveles_data.get("nivel_por_defecto") not in ids_vistos:
                errors.append("nivel_por_defecto en niveles.json no corresponde a un nivel existente.")
        except Exception as e:
            errors.append(f"Error al validar niveles.json: {e}")

    # 12. Validación de no-fuga en data/anamnesis_guia.json si existe
    if GUIA_PATH.exists():
        try:
            guia_data = json.loads(GUIA_PATH.read_text(encoding="utf-8"))
            todos_nombres_clinicos = []
            for c in casos:
                if isinstance(c, dict):
                    todos_nombres_clinicos.append(c.get("diagnostico", ""))
                    todos_nombres_clinicos.extend(c.get("diagnostico_alias", []))
                    for d in c.get("diferenciales", []):
                        todos_nombres_clinicos.append(d.get("nombre", ""))
                        todos_nombres_clinicos.extend(d.get("alias", []))

            for it in guia_data.get("items", []):
                t_item = it.get("texto", "")
                kws = it.get("keywords", [])
                for clin in todos_nombres_clinicos:
                    if clin and (contains_whole_phrase(clin, t_item) or any(contains_whole_phrase(clin, kw) for kw in kws)):
                        errors.append(f"anamnesis_guia.json: término clínico '{clin}' aparece en ítem '{it.get('id')}'.")
        except Exception as e:
            errors.append(f"Error al validar anamnesis_guia.json: {e}")

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
