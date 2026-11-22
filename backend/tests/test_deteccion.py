"""Calidad del detector de preguntas (DETECCION.md): motor, banco de preguntas y claves."""
import json
import time
from pathlib import Path

import pytest

from app.evaluate import _hit, norm

ROOT = Path(__file__).resolve().parents[2]
BANCO = json.loads((ROOT / "data" / "preguntas_ejemplo.json").read_text(encoding="utf-8"))
CASOS = json.loads((ROOT / "data" / "casos.json").read_text(encoding="utf-8"))
GUIA = json.loads((ROOT / "data" / "anamnesis_guia.json").read_text(encoding="utf-8"))

# Claves que existían antes y se recortaron a propósito por producir cruces falsos (> 5 %).
CLAVES_RECORTADAS = {
    ("c_hta_01", "dolor_toracico"): {"pecho", "corazon"},
    ("c_trauma_01", "sensibilidad_motora"): {"siente"},
    ("c_gea_01", "vomitos_tolerancia"): {"liquido"},
    ("c_gea_01", "origen_alimentos"): {"agua"},
    ("c_nac_01", "dolor_pleuritico"): {"pecho"},
}


def _h(claves, texto):
    return _hit(claves, norm(texto))


# ---------- Fase 1: motor ----------

@pytest.mark.parametrize("clave,texto", [
    ("mejora", "¿hay algo que lo mejore?"),
    ("familiar", "¿alguien de su familia?"),
    ("operaci", "¿le han operado?"),
    ("evacuaciones", "¿con qué frecuencia evacúa?"),
    ("de 1 a 10", "del 1 al 10, ¿cuánto le duele?"),
])
def test_raiz_y_contracciones(clave, texto):
    assert _h([clave], texto)


def test_comportamiento_anterior_se_conserva():
    assert _h(["viaj"], "¿viajó recientemente?")
    assert _h(["fiebre"], "¿ha tenido fiebre?")
    assert not _h(["fiebre"], "¿ha tenido tos?")


def test_palabras_cortas_solo_por_inicio_de_palabra():
    assert _h(["sed"], "¿tiene sed?")
    assert _h(["sed"], "¿le dieron un sedante?")  # ya ocurría: prefijo de palabra
    assert not _h(["sed"], "¿ha pasado?")


def test_clave_de_varias_palabras_exige_consecutivas():
    assert _h(["mal estado"], "¿comió algo en mal estado?")
    assert not _h(["mal estado"], "¿estado de ánimo, mal?")


def test_rendimiento():
    texto = norm(" ".join(["palabra"] * 499 + ["fiebre"]))
    claves = ["fiebre", "mal estado", "del 1 al 10", "evacu", "cursera"]
    t0 = time.perf_counter()
    for _ in range(1000):
        _hit(claves, texto)
    assert time.perf_counter() - t0 < 1.0


# ---------- Fases 2-4: banco y claves ----------

def _items_caso(caso):
    items = {}
    for sec in ("lista_verificacion", "banderas_rojas"):
        for it in caso[sec]:
            items.setdefault(it["id"], []).extend(it["keywords"])
    return items


def _entidades():
    ents = [("guia", {i["id"]: i["keywords"] for i in GUIA["items"]}, BANCO["guia"])]
    for c in CASOS:
        ents.append((c["id"], _items_caso(c), BANCO["casos"][c["id"]]))
    return ents


def _medir(items, banco):
    des = res = hd = hr = cr = pc = 0
    for tid, kws in items.items():
        for q in banco[tid]["desarrollo"]:
            des += 1
            hd += _h(kws, q)
        for q in banco[tid]["reserva"]:
            res += 1
            hr += _h(kws, q)
        for otro, qs in banco.items():
            if otro == tid:
                continue
            for q in qs["desarrollo"] + qs["reserva"]:
                pc += 1
                cr += _h(kws, q)
    return hd / des, hr / res, cr / pc


IDS = [e[0] for e in _entidades()]


@pytest.mark.parametrize("nombre,items,banco", _entidades(), ids=IDS)
def test_banco_cubre_todos_los_temas(nombre, items, banco):
    for tid in items:
        assert tid in banco, f"{nombre}: falta {tid}"
        assert len(banco[tid]["desarrollo"]) >= 5
        assert len(banco[tid]["reserva"]) >= 3


@pytest.mark.parametrize("nombre,items,banco", _entidades(), ids=IDS)
def test_calidad_de_deteccion(nombre, items, banco):
    des, res, cruces = _medir(items, banco)
    assert des >= 0.95, f"{nombre}: desarrollo {des:.1%}"
    assert res >= 0.80, f"{nombre}: reserva {res:.1%}"
    assert cruces <= 0.05, f"{nombre}: cruces falsos {cruces:.1%}"


def test_claves_no_contienen_el_diagnostico():
    for c in CASOS:
        nombres = [norm(n).strip() for n in [c["diagnostico"], *c.get("diagnostico_alias", [])]]
        for tid, kws in _items_caso(c).items():
            for k in kws:
                for n in nombres:
                    assert f' {n} ' not in norm(k), f"{c['id']}/{tid}: la clave «{k}» contiene «{n}»"


def test_claves_recortadas_estan_documentadas():
    """Las claves recortadas no deben volver sin revisar los cruces falsos."""
    por_caso = {c["id"]: _items_caso(c) for c in CASOS}
    for (cid, tid), claves in CLAVES_RECORTADAS.items():
        assert not (claves & set(por_caso[cid][tid]))
