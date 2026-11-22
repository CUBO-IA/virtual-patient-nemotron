"""Script de medición de detección según DETECCION.md Fase 2."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.evaluate import _hit, norm

PREGUNTAS_PATH = ROOT / "data" / "preguntas_ejemplo.json"
GUIA_PATH = ROOT / "data" / "anamnesis_guia.json"
CASOS_PATH = ROOT / "data" / "casos.json"


def medir_entidad(nombre, items_dict, preguntas_entidad, detalle=False):
    """
    items_dict: {item_id: [keywords]}
    preguntas_entidad: {item_id: {"desarrollo": [...], "reserva": [...]}}
    """
    total_des = 0
    hit_des = 0
    total_res = 0
    hit_res = 0
    total_cruces = 0
    pares_cruces = 0

    no_detectadas_des = []
    no_detectadas_res = []

    # Construir banco de todas las preguntas por tema
    todas_por_tema = {}
    for tid, qdata in preguntas_entidad.items():
        todas_por_tema[tid] = qdata.get("desarrollo", []) + qdata.get("reserva", [])

    for tid, kws in items_dict.items():
        qdata = preguntas_entidad.get(tid, {})
        des_list = qdata.get("desarrollo", [])
        res_list = qdata.get("reserva", [])

        # 1. Desarrollo
        for q in des_list:
            total_des += 1
            if _hit(kws, norm(q)):
                hit_des += 1
            else:
                no_detectadas_des.append((tid, q))

        # 2. Reserva
        for q in res_list:
            total_res += 1
            if _hit(kws, norm(q)):
                hit_res += 1
            else:
                no_detectadas_res.append((tid, q))

        # 3. Cruces falsos: preguntas de OTROS temas que marcan este tema
        for other_tid, other_qs in todas_por_tema.items():
            if other_tid == tid:
                continue
            for q in other_qs:
                pares_cruces += 1
                if _hit(kws, norm(q)):
                    total_cruces += 1

    pct_des = (hit_des / total_des * 100) if total_des else 0.0
    pct_res = (hit_res / total_res * 100) if total_res else 0.0
    pct_cruces = (total_cruces / pares_cruces * 100) if pares_cruces else 0.0

    return {
        "nombre": nombre,
        "temas": len(items_dict),
        "pct_des": pct_des,
        "hit_des": hit_des,
        "total_des": total_des,
        "pct_res": pct_res,
        "hit_res": hit_res,
        "total_res": total_res,
        "pct_cruces": pct_cruces,
        "total_cruces": total_cruces,
        "pares_cruces": pares_cruces,
        "no_detectadas_des": no_detectadas_des,
        "no_detectadas_res": no_detectadas_res,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--detalle", action="store_true", help="Mostrar preguntas no detectadas")
    args = parser.parse_args()

    preguntas = json.loads(PREGUNTAS_PATH.read_text(encoding="utf-8"))
    guia = json.loads(GUIA_PATH.read_text(encoding="utf-8"))
    casos = json.loads(CASOS_PATH.read_text(encoding="utf-8"))

    resultados = []

    # 1. Guía de anamnesis
    guia_items = {it["id"]: it["keywords"] for it in guia.get("items", [])}
    r_guia = medir_entidad("Guía anamnesis", guia_items, preguntas.get("guia", {}), args.detalle)
    resultados.append(r_guia)

    # 2. Casos clínicos
    for caso in casos:
        cid = caso["id"]
        caso_items = {}
        for it in caso.get("lista_verificacion", []):
            caso_items[it["id"]] = it["keywords"]
        for b in caso.get("banderas_rojas", []):
            if b["id"] in caso_items:
                # Si ya existe con el mismo ID, combinar keywords
                caso_items[b["id"]] = list(set(caso_items[b["id"]] + b["keywords"]))
            else:
                caso_items[b["id"]] = b["keywords"]

        preg_caso = preguntas.get("casos", {}).get(cid, {})
        r_caso = medir_entidad(cid, caso_items, preg_caso, args.detalle)
        resultados.append(r_caso)

    # Imprimir tabla
    print("=" * 82)
    print(f"{'Entidad':<18} | {'Temas':<5} | {'Desarrollo':<12} | {'Reserva':<12} | {'Cruces falsos':<13} | {'Estado':<6}")
    print("=" * 82)

    todos_ok = True
    for r in resultados:
        # Criterios: Desarrollo >= 95%, Reserva >= 80%, Cruces <= 5%
        ok_des = r["pct_des"] >= 95.0
        ok_res = r["pct_res"] >= 80.0
        ok_cruces = r["pct_cruces"] <= 5.0
        aprobado = ok_des and ok_res and ok_cruces
        if not aprobado:
            todos_ok = False

        des_str = f"{r['pct_des']:.1f}% ({r['hit_des']}/{r['total_des']})"
        res_str = f"{r['pct_res']:.1f}% ({r['hit_res']}/{r['total_res']})"
        cruces_str = f"{r['pct_cruces']:.1f}% ({r['total_cruces']}/{r['pares_cruces']})"
        status_str = "OK" if aprobado else "FAIL"

        print(f"{r['nombre']:<18} | {r['temas']:<5} | {des_str:<12} | {res_str:<12} | {cruces_str:<13} | {status_str:<6}")

    print("=" * 82)

    # Promedios globales
    t_des = sum(r["total_des"] for r in resultados)
    h_des = sum(r["hit_des"] for r in resultados)
    t_res = sum(r["total_res"] for r in resultados)
    h_res = sum(r["hit_res"] for r in resultados)
    t_cr = sum(r["total_cruces"] for r in resultados)
    p_cr = sum(r["pares_cruces"] for r in resultados)
    print(
        f"{'PROMEDIO GLOBAL':<18} | {sum(r['temas'] for r in resultados):<5} | "
        f"{(h_des/t_des*100):.1f}% ({h_des}/{t_des}) | "
        f"{(h_res/t_res*100):.1f}% ({h_res}/{t_res}) | "
        f"{(t_cr/p_cr*100):.1f}% ({t_cr}/{p_cr}) | "
        f"{'OK' if todos_ok else 'FAIL'}"
    )
    print("=" * 82)

    if args.detalle or not todos_ok:
        print("\n--- DETALLE DE PREGUNTAS NO DETECTADAS ---")
        for r in resultados:
            if r["no_detectadas_des"] or r["no_detectadas_res"]:
                print(f"\n[{r['nombre']}]")
                if r["no_detectadas_des"]:
                    print("  No detectadas en DESARROLLO:")
                    for tid, q in r["no_detectadas_des"]:
                        print(f"    - ({tid}): \"{q}\"")
                if r["no_detectadas_res"]:
                    print("  No detectadas en RESERVA:")
                    for tid, q in r["no_detectadas_res"]:
                        print(f"    - ({tid}): \"{q}\"")

    return 0 if todos_ok else 1


if __name__ == "__main__":
    sys.exit(main())
