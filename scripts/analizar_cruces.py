import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.evaluate import _hit, norm

PREGUNTAS_PATH = ROOT / "data" / "preguntas_ejemplo.json"
CASOS_PATH = ROOT / "data" / "casos.json"

preguntas = json.loads(PREGUNTAS_PATH.read_text(encoding="utf-8"))
casos = json.loads(CASOS_PATH.read_text(encoding="utf-8"))

for caso in casos:
    cid = caso["id"]
    if cid not in ['c_hta_01', 'c_gea_01', 'c_nac_01', 'c_trauma_01', 'c_erc_01']:
        continue
    
    caso_items = {}
    for it in caso.get("lista_verificacion", []):
        caso_items[it["id"]] = it["keywords"]
    for b in caso.get("banderas_rojas", []):
        if b["id"] in caso_items:
            caso_items[b["id"]] = list(set(caso_items[b["id"]] + b["keywords"]))
        else:
            caso_items[b["id"]] = b["keywords"]

    preg_caso = preguntas.get("casos", {}).get(cid, {})
    
    todas_por_tema = {}
    for tid, qdata in preg_caso.items():
        todas_por_tema[tid] = qdata.get("desarrollo", []) + qdata.get("reserva", [])

    cruces = []
    for tid, kws in caso_items.items():
        for other_tid, other_qs in todas_por_tema.items():
            if other_tid == tid:
                continue
            for q in other_qs:
                if _hit(kws, norm(q)):
                    matching_kws = [k for k in kws if _hit([k], norm(q))]
                    cruces.append((tid, other_tid, tuple(matching_kws), q))

    pares = len(caso_items) * (len(caso_items) - 1) * 8  # approx
    print(f"\n=== {cid}: {len(cruces)} cruces (tasa aprox {len(cruces)/(len(caso_items)*len(todas_por_tema)*8)*100:.1f}%) ===")
    c_kw = Counter([kws for _, _, kws, _ in cruces])
    for kws, cnt in c_kw.most_common(6):
        print(f"  {kws}: {cnt} veces")
        for tid, other_tid, mkws, q in cruces:
            if mkws == kws:
                print(f"     Tema [{tid}] se activo con pregunta de [{other_tid}]: \"{q}\"")
                break
