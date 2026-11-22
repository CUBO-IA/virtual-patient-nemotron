"""Valida estructura y referencias de los borradores de urgencias; no evalúa pertinencia clínica."""
import json
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def norm(v):
    s = unicodedata.normalize("NFD", str(v).lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")

def main():
    casos = json.loads((ROOT / "data/urgencias.json").read_text(encoding="utf-8"))
    base = json.loads((ROOT / "data/casos.json").read_text(encoding="utf-8"))
    personas = json.loads((ROOT / "data/personas.json").read_text(encoding="utf-8"))
    ids = set(); errors = []
    required = {"id","caso_base","motivo_consulta","sintomas","antecedentes","habitos","datos_si_pregunta","restricciones","diagnostico","diagnostico_alias","lista_verificacion","banderas_rojas","urgencia","revision_clinica"}
    for c in casos:
        label = c.get("id", "(sin id)")
        if ids.__contains__(label): errors.append(f"{label}: id repetido")
        ids.add(label)
        for k in required - c.keys(): errors.append(f"{label}: falta {k}")
        if c.get("caso_base") and c["caso_base"] not in {b["id"] for b in base}: errors.append(f"{label}: caso_base inexistente")
        u = c.get("urgencia", {})
        flag_ids = {f.get("id") for f in c.get("banderas_rojas", [])}
        if not set(u.get("signos_activos", [])) <= flag_ids: errors.append(f"{label}: signos_activos no son ids de banderas_rojas")
        if u.get("nivel") not in {"rojo","amarillo","verde"}: errors.append(f"{label}: nivel inválido")
        if u.get("accion_esperada") not in {"emergencias","atencion_inmediata","evaluacion_pronto","consulta_normal"}: errors.append(f"{label}: acción inválida")
        if not u.get("explicacion"): errors.append(f"{label}: falta explicación")
        if c.get("revision_clinica", {}).get("estado") != "pendiente": errors.append(f"{label}: debe quedar pendiente de revisión clínica")
        nombres = [norm(n).strip() for n in [c.get("diagnostico", ""), *c.get("diagnostico_alias", [])] if n]
        visible = [c.get("motivo_consulta", ""), *c.get("sintomas", []), *c.get("antecedentes", []), *c.get("habitos", []),
                   *c.get("datos_si_pregunta", {}).values(), *u.get("datos_ocultos", [])]
        public = f" {norm(' '.join(visible)).strip()} "
        for n in nombres:
            if n and f" {n} " in public: errors.append(f"{label}: «{n}» aparece en lo que dice el paciente")
        if any(k not in {i.get("id") for i in c.get("lista_verificacion", [])} for k in c.get("datos_si_pregunta", {})):
            errors.append(f"{label}: datos_si_pregunta usa un tema que no está en lista_verificacion")
        r = c.get("restricciones", {})
        if not any((not r.get("sexo") or p.get("sexo") in r["sexo"]) and r.get("edad_min",0) <= p.get("edad",0) <= r.get("edad_max",200) for p in personas): errors.append(f"{label}: no hay persona compatible")
    niveles = {c.get("urgencia", {}).get("nivel") for c in casos}
    if niveles != {"rojo", "amarillo", "verde"}: errors.append(f"faltan niveles de prioridad: hay {sorted(niveles)}")
    if errors:
        print("\n".join(errors)); return 1
    print(f"{len(casos)} borradores válidos (estructura; revisión clínica pendiente).")
    return 0

if __name__ == "__main__": sys.exit(main())
