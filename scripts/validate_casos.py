"""Validador de casos clínicos según AGENTS.md, NIVELES.md y SEGUIMIENTO.md."""

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
CATALOGO_PRUEBAS_PATH = ROOT / "data" / "catalogo_pruebas.json"
FORMULARIO_PATH = ROOT / "data" / "formulario.json"

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

PREDICADOS_PERMITIDOS = {
    "disposicion_correcta",
    "disposicion_aceptable",
    "disposicion_insuficiente",
    "hay_contraindicado",
    "sin_contraindicados",
    "medicacion_adecuada_completa",
    "faltan_medicamentos_adecuados",
    "indicaciones_esenciales_completas",
    "faltan_indicaciones_esenciales",
    "pidio_pruebas_esenciales",
    "no_pidio_pruebas_esenciales",
    "alergia_ignorada",
}


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

    # Validar catalogo_pruebas.json si existe
    pruebas_ids_validos = set()
    if CATALOGO_PRUEBAS_PATH.exists():
        try:
            cat_pruebas = json.loads(CATALOGO_PRUEBAS_PATH.read_text(encoding="utf-8"))
            categorias = set(cat_pruebas.get("categorias", []))
            for p in cat_pruebas.get("pruebas", []):
                pid = p.get("id")
                if not pid or pid in pruebas_ids_validos:
                    errors.append(f"catalogo_pruebas.json: id '{pid}' inválido o duplicado.")
                pruebas_ids_validos.add(pid)
                if p.get("categoria") not in categorias:
                    errors.append(f"catalogo_pruebas.json: prueba '{pid}' categoría inválida '{p.get('categoria')}'.")
                if p.get("costo") not in (1, 2, 3):
                    errors.append(f"catalogo_pruebas.json: prueba '{pid}' costo '{p.get('costo')}' fuera de rango (1-3).")
                if p.get("nivel_atencion") not in ("primer_nivel", "hospital"):
                    errors.append(f"catalogo_pruebas.json: prueba '{pid}' nivel_atencion '{p.get('nivel_atencion')}' inválido.")
        except Exception as e:
            errors.append(f"Error al validar catalogo_pruebas.json: {e}")

    # Validar formulario.json si existe
    meds_ids_validos = set()
    indicaciones_ids_validos = set()
    disposiciones_ids_validos = set()
    if FORMULARIO_PATH.exists():
        try:
            form_data = json.loads(FORMULARIO_PATH.read_text(encoding="utf-8"))
            for m in form_data.get("medicamentos", []):
                mid = m.get("id")
                if not mid or mid in meds_ids_validos:
                    errors.append(f"formulario.json: medicamento id '{mid}' inválido o duplicado.")
                meds_ids_validos.add(mid)
            for ind in form_data.get("indicaciones", []):
                iid = ind.get("id")
                if not iid or iid in indicaciones_ids_validos:
                    errors.append(f"formulario.json: indicacion id '{iid}' inválido o duplicado.")
                indicaciones_ids_validos.add(iid)
            for disp in form_data.get("disposiciones", []):
                did = disp.get("id")
                if not did or did in disposiciones_ids_validos:
                    errors.append(f"formulario.json: disposicion id '{did}' inválido o duplicado.")
                disposiciones_ids_validos.add(did)
        except Exception as e:
            errors.append(f"Error al validar formulario.json: {e}")

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

        # 5. Campos a verificar contra fugas
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

        # 6. Validación de pistas
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

                if isinstance(lv, list):
                    for it in lv:
                        if isinstance(it, dict) and "id" in it and it["id"] not in pistas_by_item:
                            errors.append(f"{prefix}: falta pista para el ítem '{it['id']}' de lista_verificacion.")

        if isinstance(lv, list):
            for it in lv:
                if isinstance(it, dict) and "texto" in it:
                    campos_a_verificar.append((f"lista_verificacion ({it.get('id', '')})", it["texto"]))

        # 7. Validación de dificultad y diferenciales
        dif = caso.get("dificultad")
        if dif is not None:
            if not isinstance(dif, int) or dif not in (1, 2, 3):
                errors.append(f"{prefix}: 'dificultad' debe ser un entero entre 1 y 3 (obtenido: {dif}).")

        diferenciales = caso.get("diferenciales")
        if dif == 3 and not diferenciales:
            errors.append(f"{prefix}: casos con dificultad 3 deben incluir 'diferenciales'.")

        all_dif_names = []
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
                        all_dif_names.extend(d_all)

        # 8. SEGUIMIENTO.md: revision_clinica
        rev = caso.get("revision_clinica")
        if rev is not None:
            if not isinstance(rev, dict):
                errors.append(f"{prefix}: 'revision_clinica' debe ser un diccionario.")
            else:
                estado = rev.get("estado")
                if estado not in ("pendiente", "validado"):
                    errors.append(f"{prefix}: revision_clinica.estado debe ser 'pendiente' o 'validado'.")
                elif estado == "validado":
                    for req_rev in ["revisado_por", "fecha", "fuente"]:
                        if not rev.get(req_rev) or not str(rev.get(req_rev)).strip():
                            errors.append(f"{prefix}: revision_clinica 'validado' requiere '{req_rev}' no vacío.")

        # 9. SEGUIMIENTO.md: pruebas
        pruebas = caso.get("pruebas")
        if pruebas is not None:
            if not isinstance(pruebas, dict):
                errors.append(f"{prefix}: 'pruebas' debe ser un diccionario.")
            else:
                if not pruebas.get("resultado_defecto") or not isinstance(pruebas["resultado_defecto"], str):
                    errors.append(f"{prefix}: pruebas falta 'resultado_defecto' no vacío.")
                res_dict = pruebas.get("resultados", {})
                if not isinstance(res_dict, dict):
                    errors.append(f"{prefix}: pruebas.resultados debe ser un diccionario.")
                else:
                    for pid, pdata in res_dict.items():
                        if pid not in pruebas_ids_validos and pruebas_ids_validos:
                            errors.append(f"{prefix}: prueba '{pid}' en resultados no existe en catalogo_pruebas.json.")
                        if not isinstance(pdata, dict):
                            errors.append(f"{prefix}: resultado de prueba '{pid}' debe ser diccionario.")
                            continue
                        if pdata.get("pertinencia") not in ("esencial", "util", "innecesaria"):
                            errors.append(f"{prefix}: prueba '{pid}' pertinencia '{pdata.get('pertinencia')}' inválida.")
                        informe = pdata.get("informe")
                        if not informe or not isinstance(informe, str):
                            errors.append(f"{prefix}: prueba '{pid}' falta 'informe' de texto.")
                        else:
                            campos_a_verificar.append((f"informe de prueba {pid}", informe))

                esenciales = pruebas.get("esenciales", [])
                if not isinstance(esenciales, list):
                    errors.append(f"{prefix}: pruebas.esenciales debe ser una lista.")
                else:
                    for eid in esenciales:
                        if eid not in pruebas_ids_validos and pruebas_ids_validos:
                            errors.append(f"{prefix}: prueba esencial '{eid}' no existe en catalogo_pruebas.json.")

        # 10. SEGUIMIENTO.md: plan_esperado
        plan_esp = caso.get("plan_esperado")
        if plan_esp is not None:
            if not isinstance(plan_esp, dict):
                errors.append(f"{prefix}: 'plan_esperado' debe ser un diccionario.")
            else:
                disp = plan_esp.get("disposicion", {})
                for k in ["correcta", "aceptable"]:
                    for did in disp.get(k, []):
                        if did not in disposiciones_ids_validos and disposiciones_ids_validos:
                            errors.append(f"{prefix}: disposicion '{did}' en plan_esperado no existe en formulario.json.")

                meds = plan_esp.get("medicamentos", {})
                adecuados_ids = {m.get("id") for m in meds.get("adecuados", []) if isinstance(m, dict)}
                contra_ids = {m.get("id") for m in meds.get("contraindicados", []) if isinstance(m, dict)}
                cruce_meds = adecuados_ids.intersection(contra_ids)
                if cruce_meds:
                    errors.append(f"{prefix}: medicamentos figuran como adecuados y contraindicados a la vez: {cruce_meds}.")

                for group_name in ["adecuados", "aceptables", "contraindicados"]:
                    for m in meds.get(group_name, []):
                        mid = m.get("id") if isinstance(m, dict) else m
                        if mid not in meds_ids_validos and meds_ids_validos:
                            errors.append(f"{prefix}: medicamento '{mid}' ({group_name}) no existe en formulario.json.")

                ind_esp = plan_esp.get("indicaciones", {}).get("esenciales", [])
                for iid in ind_esp:
                    if iid not in indicaciones_ids_validos and indicaciones_ids_validos:
                        errors.append(f"{prefix}: indicacion esencial '{iid}' no existe en formulario.json.")

        # 11. SEGUIMIENTO.md: evolucion
        evol = caso.get("evolucion")
        if evol is not None:
            if not isinstance(evol, dict):
                errors.append(f"{prefix}: 'evolucion' debe ser un diccionario.")
            else:
                if not isinstance(evol.get("control_en_dias"), int) or evol["control_en_dias"] <= 0:
                    errors.append(f"{prefix}: evolucion.control_en_dias debe ser un entero positivo.")
                ramas = evol.get("ramas", {})
                for rama_nombre in ["mejora", "parcial", "empeora"]:
                    if rama_nombre not in ramas:
                        errors.append(f"{prefix}: evolucion falta rama '{rama_nombre}'.")
                    else:
                        rdata = ramas[rama_nombre]
                        if not isinstance(rdata, dict):
                            errors.append(f"{prefix}: evolucion rama '{rama_nombre}' debe ser diccionario.")
                            continue
                        relato = rdata.get("relato", "")
                        if not relato or not isinstance(relato, str):
                            errors.append(f"{prefix}: evolucion rama '{rama_nombre}' falta 'relato'.")
                        else:
                            campos_a_verificar.append((f"relato evolucion ({rama_nombre})", relato))
                        cond = rdata.get("condicion", "")
                        # Validar predicados en condicion
                        tokens = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", cond)
                        for tok in tokens:
                            if tok not in ("y", "o", "no") and tok not in PREDICADOS_PERMITIDOS:
                                errors.append(f"{prefix}: predicado '{tok}' no permitido en condicion de '{rama_nombre}'.")

        # 12. Fuga del diagnóstico o alias en campos visibles para el paciente
        todos_clinicos = all_names + all_dif_names
        for name in todos_clinicos:
            for campo_nombre, texto in campos_a_verificar:
                if contains_whole_phrase(name, texto):
                    errors.append(
                        f"{prefix}: el término clínico '{name}' aparece en '{campo_nombre}': \"{texto}\"."
                    )

        # 13. Campo opcional guia_ref
        if "guia_ref" in caso:
            if not isinstance(caso["guia_ref"], str) or not caso["guia_ref"].strip():
                errors.append(f"{prefix}: 'guia_ref' debe ser una cadena no vacía.")

    # 14. Balance por niveles
    casos_n1 = [c for c in casos if isinstance(c, dict) and c.get("dificultad", 99) <= 1]
    casos_n2 = [c for c in casos if isinstance(c, dict) and c.get("dificultad", 99) <= 2]
    casos_n3 = [c for c in casos if isinstance(c, dict) and c.get("dificultad", 99) <= 3]
    if len(casos_n1) < 3:
        errors.append(f"Nivel 1 debe tener al menos 3 casos elegibles (obtenidos: {len(casos_n1)}).")
    if len(casos_n2) < 3:
        errors.append(f"Nivel 2 debe tener al menos 3 casos elegibles (obtenidos: {len(casos_n2)}).")
    if len(casos_n3) < 3:
        errors.append(f"Nivel 3 debe tener al menos 3 casos elegibles (obtenidos: {len(casos_n3)}).")

    # 15. Validación de data/niveles.json
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

    # 16. Validación de no-fuga en data/anamnesis_guia.json
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
