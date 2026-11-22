"""Pruebas, plan de tratamiento y control (SEGUIMIENTO.md). No necesitan Ollama: el modelo se simula."""

import asyncio
import copy
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app import config, evaluate, niveles, seguimiento, sessions
from app.main import app

DATA = Path(__file__).resolve().parents[2] / "data"
client = TestClient(app)

CASOS = json.loads((DATA / "casos.json").read_text(encoding="utf-8"))
CASOS_POR_ID = {c["id"]: c for c in CASOS}
PERSONA = json.loads((DATA / "personas.json").read_text(encoding="utf-8"))[0]
CASO_IDS = [c["id"] for c in CASOS]


@pytest.fixture
def demo(monkeypatch):
    """Activa los módulos aunque los casos estén pendientes de revisión (modo demostración)."""
    monkeypatch.setattr(config, "SEGUIMIENTO_DEMO", True)


def _nivel(nid: int, dificultad_max: int = 3) -> dict:
    cfg = dict(niveles.obtener_nivel(nid))
    cfg["casos"] = {"dificultad_max": dificultad_max, "peso_dificultad_igual": 1}
    return cfg


def _sesion_api(nivel: int, caso_id: str) -> dict:
    r = client.post("/api/sessions", json={"nivel": nivel, "caso_id": caso_id})
    assert r.status_code == 200, r.text
    return r.json()


def _sesion_directa(caso_id: str, nivel: int):
    return sessions.create(copy.deepcopy(CASOS_POR_ID[caso_id]), PERSONA, nivel=_nivel(nivel))


def _texto_perfecto(caso: dict) -> str:
    kws = [it["keywords"][0] for it in caso["lista_verificacion"]] + [b["keywords"][0] for b in caso["banderas_rojas"]]
    return " ".join(kws)


def _plan_perfecto(caso: dict) -> dict:
    pe = caso["plan_esperado"]
    return {
        "disposicion": pe["disposicion"]["correcta"][0],
        "medicamentos": [{"id": m["id"]} for m in pe["medicamentos"]["adecuados"]],
        "sin_tratamiento_farmacologico": not pe["medicamentos"]["adecuados"],
        "indicaciones": list(pe["indicaciones"]["esenciales"]),
        "control_dias": 2,
    }


def _evaluar(caso_id: str, nivel: int, *, plan=None, pruebas=None, texto=None, dx=None, difs=None):
    s = _sesion_directa(caso_id, nivel)
    caso = s.caso
    s.mensajes = [{"role": "user", "content": _texto_perfecto(caso) if texto is None else texto}]
    s.pruebas_pedidas = list(caso["pruebas"]["esenciales"]) if pruebas is None else list(pruebas)
    with patch("app.llm.chat_once", new_callable=AsyncMock) as m:
        m.return_value = "Buen trabajo. Sigue explorando los demás temas."
        res = asyncio.run(evaluate.evaluar(s, caso["diagnostico"] if dx is None else dx, difs, plan))
    return s, res


def _difs(caso: dict, nivel: int):
    req = niveles.obtener_nivel(nivel).get("diferenciales_requeridos", 0)
    return [d["nombre"] for d in caso.get("diferenciales", [])][:req] or None


# ----------------------------------------------------------------- catálogos y datos

def test_catalogos_cargan_y_son_validos():
    assert seguimiento.catalogos_ok() is True
    cat = seguimiento.cargar_catalogo_pruebas()
    ids = [p["id"] for p in cat["pruebas"]]
    assert len(ids) == len(set(ids))
    assert all(p["costo"] in (1, 2, 3) for p in cat["pruebas"])
    assert all(p["categoria"] in cat["categorias"] for p in cat["pruebas"])


def test_todos_los_casos_traen_los_datos_del_modulo_y_son_consistentes():
    cat = {p["id"] for p in seguimiento.cargar_catalogo_pruebas()["pruebas"]}
    form = seguimiento.cargar_formulario()
    meds = {m["id"] for m in form["medicamentos"]}
    inds = {i["id"] for i in form["indicaciones"]}
    disps = {d["id"] for d in form["disposiciones"]}
    allfalse = {k: False for k in seguimiento.PREDICADOS_PERMITIDOS}
    for c in CASOS:
        pr = c["pruebas"]
        assert set(pr["resultados"]) <= cat, c["id"]
        assert set(pr["esenciales"]) <= set(pr["resultados"]), c["id"]
        for pid in pr["esenciales"]:
            assert pr["resultados"][pid]["pertinencia"] == "esencial", (c["id"], pid)
        pe = c["plan_esperado"]
        grupos = pe["medicamentos"]
        usados = {m["id"] for g in grupos.values() for m in g}
        assert usados <= meds, c["id"]
        assert not ({m["id"] for m in grupos["adecuados"]} & {m["id"] for m in grupos["contraindicados"]}), c["id"]
        assert set(pe["indicaciones"]["esenciales"]) <= inds, c["id"]
        assert set(pe["disposicion"]["correcta"]) | set(pe["disposicion"]["aceptable"]) <= disps, c["id"]
        for rama in c["evolucion"]["ramas"].values():
            seguimiento.evaluar_condicion_booleana(rama["condicion"], allfalse)  # no lanza


def test_informes_y_relatos_no_nombran_el_diagnostico():
    def n(t):
        return evaluate.norm(t)

    for c in CASOS:
        nombres = [c["diagnostico"]] + c.get("diagnostico_alias", [])
        nombres += [d["nombre"] for d in c.get("diferenciales", [])] + [a for d in c.get("diferenciales", []) for a in d.get("alias", [])]
        textos = [r["informe"] for r in c["pruebas"]["resultados"].values()]
        textos += [json.dumps(r.get("valores", []), ensure_ascii=False) for r in c["pruebas"]["resultados"].values()]
        textos += [r["relato"] for r in c["evolucion"]["ramas"].values()]
        textos.append(c["pruebas"]["resultado_defecto"])
        for t in textos:
            for nombre in nombres:
                assert n(nombre) not in n(t), f"{c['id']}: «{nombre}» aparece en «{t[:60]}»"


def test_ningun_caso_figura_validado_sin_un_revisor_real():
    """Garantía contra una validación inventada: 'validado' exige nombre, fecha y fuente."""
    for c in CASOS:
        rev = c["revision_clinica"]
        if rev["estado"] == "validado":
            assert rev["revisado_por"] and rev["fecha"] and rev["fuente"], c["id"]
        else:
            assert rev["estado"] == "pendiente"
            assert rev["revisado_por"] is None


# ----------------------------------------------------------------- activación de módulos

def test_casos_pendientes_no_activan_modulos_por_defecto():
    for c in CASOS:
        for n in (1, 2, 3):
            m = seguimiento.calcular_modulos_activos(niveles.obtener_nivel(n), c)
            assert m == {"pruebas": False, "plan": False, "seguimiento": False}, (c["id"], n)


def test_un_caso_validado_con_revisor_activa_modulos():
    caso = copy.deepcopy(CASOS_POR_ID["c_dengue_01"])
    caso["revision_clinica"] = {"estado": "validado", "revisado_por": "Dr. Prueba", "fecha": "2026-01-01", "fuente": "x", "observaciones": ""}
    m = seguimiento.calcular_modulos_activos(niveles.obtener_nivel(2), caso)
    assert m["pruebas"] and m["plan"] and m["seguimiento"]


def test_validado_sin_revisor_no_activa_modulos():
    caso = copy.deepcopy(CASOS_POR_ID["c_dengue_01"])
    caso["revision_clinica"] = {"estado": "validado", "revisado_por": None, "fecha": None, "fuente": None, "observaciones": ""}
    m = seguimiento.calcular_modulos_activos(niveles.obtener_nivel(2), caso)
    assert not (m["pruebas"] or m["plan"] or m["seguimiento"])
    assert seguimiento.resumen_revision(caso)["estado"] == "pendiente"


def test_modo_demo_activa_modulos(demo):
    m = seguimiento.calcular_modulos_activos(niveles.obtener_nivel(2), CASOS_POR_ID["c_dengue_01"])
    assert m["pruebas"] and m["plan"] and m["seguimiento"]


def test_catalogos_invalidos_apagan_todo_incluso_en_demo(demo, monkeypatch):
    monkeypatch.setattr(seguimiento, "catalogos_ok", lambda: False)
    m = seguimiento.calcular_modulos_activos(niveles.obtener_nivel(2), CASOS_POR_ID["c_dengue_01"])
    assert m == {"pruebas": False, "plan": False, "seguimiento": False}


def test_nivel_sin_bloque_modulos_los_deja_apagados(demo):
    nivel = {k: v for k, v in niveles.obtener_nivel(2).items() if k != "modulos"}
    m = seguimiento.calcular_modulos_activos(nivel, CASOS_POR_ID["c_dengue_01"])
    assert not (m["pruebas"] or m["plan"] or m["seguimiento"])


def test_resumen_revision_no_expone_datos_internos():
    r = seguimiento.resumen_revision(CASOS_POR_ID["c_dengue_01"])
    assert set(r) == {"estado", "revisado_por", "contenido_sin_validar"}
    assert r["contenido_sin_validar"] is True


# ----------------------------------------------------------------- API

def test_sesion_sin_demo_informa_modulos_apagados_y_revision_pendiente():
    s = _sesion_api(2, "c_dengue_01")
    assert s["modulos"] == {"pruebas": False, "plan": False, "seguimiento": False}
    assert s["revision_clinica"]["contenido_sin_validar"] is True


def test_pruebas_responde_404_con_el_modulo_apagado():
    s = _sesion_api(2, "c_dengue_01")
    assert client.post(f"/api/sessions/{s['session_id']}/pruebas", json={"ids": ["hemograma"]}).status_code == 404
    assert client.get(f"/api/sessions/{s['session_id']}/pruebas").status_code == 404


def test_catalogos_publicos_no_revelan_pertinencia_ni_casos():
    cat = client.get("/api/catalogo/pruebas")
    form = client.get("/api/catalogo/formulario")
    assert cat.status_code == 200 and form.status_code == 200
    txt = (cat.text + form.text).lower()
    for prohibido in ("pertinencia", "esencial", "plan_esperado", "evolucion", "contraindicado"):
        assert prohibido not in txt
    assert len(cat.json()["pruebas"]) >= 10 and len(form.json()["medicamentos"]) >= 10


def test_sesion_en_demo_expone_modulos_sin_filtrar_el_caso(demo):
    s = _sesion_api(2, "c_dengue_01")
    assert s["modulos"]["plan"] is True and s["modulos"]["pruebas"]["max"] == 6
    crudo = json.dumps(s, ensure_ascii=False).lower()
    caso = CASOS_POR_ID["c_dengue_01"]
    for prohibido in [caso["diagnostico"].lower(), "pertinencia", "plan_esperado", "evolucion", "lista_verificacion", "esenciales"]:
        assert prohibido not in crudo


def test_pruebas_resultado_correcto_e_idempotente(demo):
    s = _sesion_api(2, "c_dengue_01")
    sid = s["session_id"]
    r1 = client.post(f"/api/sessions/{sid}/pruebas", json={"ids": ["hemograma", "rx_torax"]})
    assert r1.status_code == 200
    j1 = r1.json()
    assert [x["id"] for x in j1["resultados"]] == ["hemograma", "rx_torax"]
    assert j1["pruebas_usadas"] == 2 and j1["costo_total"] > 0
    assert "pertinencia" not in r1.text
    hemo = next(x for x in j1["resultados"] if x["id"] == "hemograma")
    assert hemo["valores"] and hemo["informe"]

    j2 = client.post(f"/api/sessions/{sid}/pruebas", json={"ids": ["hemograma"]}).json()
    assert j2["pruebas_usadas"] == 2 and j2["costo_total"] == j1["costo_total"]
    assert j2["resultados"][0]["informe"] == hemo["informe"]

    j3 = client.get(f"/api/sessions/{sid}/pruebas").json()
    assert {x["id"] for x in j3["resultados"]} == {"hemograma", "rx_torax"}


def test_prueba_no_listada_devuelve_el_resultado_por_defecto(demo):
    s = _sesion_api(2, "c_dengue_01")
    caso = CASOS_POR_ID["c_dengue_01"]
    libre = next(p["id"] for p in seguimiento.cargar_catalogo_pruebas()["pruebas"] if p["id"] not in caso["pruebas"]["resultados"])
    j = client.post(f"/api/sessions/{s['session_id']}/pruebas", json={"ids": [libre]}).json()
    assert j["resultados"][0]["informe"] == caso["pruebas"]["resultado_defecto"]


def test_pruebas_rechaza_ids_invalidos_y_tandas_vacias_o_largas(demo):
    sid = _sesion_api(2, "c_dengue_01")["session_id"]
    assert client.post(f"/api/sessions/{sid}/pruebas", json={"ids": ["no_existe"]}).status_code == 422
    assert client.post(f"/api/sessions/{sid}/pruebas", json={"ids": []}).status_code == 422
    assert client.post(f"/api/sessions/{sid}/pruebas", json={"ids": ["a"] * 6}).status_code == 422


def test_limite_de_pruebas_es_todo_o_nada(demo):
    sid = _sesion_api(2, "c_dengue_01")["session_id"]  # nivel 2: máx. 6
    ids = [p["id"] for p in seguimiento.cargar_catalogo_pruebas()["pruebas"]]
    assert client.post(f"/api/sessions/{sid}/pruebas", json={"ids": ids[:5]}).status_code == 200
    # 5 usadas + 2 nuevas = 7 > 6: se rechaza TODA la tanda
    r = client.post(f"/api/sessions/{sid}/pruebas", json={"ids": ids[5:7]})
    assert r.status_code == 409 and "límite" in r.json()["detail"].lower()
    assert client.get(f"/api/sessions/{sid}/pruebas").json()["pruebas_usadas"] == 5
    # una más sí cabe
    assert client.post(f"/api/sessions/{sid}/pruebas", json={"ids": ids[5:6]}).status_code == 200


def test_presupuesto_de_pruebas_en_nivel_avanzado(demo):
    """Nivel 3: presupuesto de 6 puntos de costo y máx. 4 pruebas. No depende de cómo esté el catálogo."""
    sid = _sesion_api(3, "c_erc_01")["session_id"]
    pruebas = sorted(seguimiento.cargar_catalogo_pruebas()["pruebas"], key=lambda p: -p["costo"])
    gastado, pedidas, rechazo = 0, 0, None
    for p in pruebas:
        r = client.post(f"/api/sessions/{sid}/pruebas", json={"ids": [p["id"]]})
        if r.status_code == 200:
            gastado += p["costo"]
            pedidas += 1
        else:
            rechazo = r
            break
    assert rechazo is not None and rechazo.status_code == 409
    detalle = rechazo.json()["detail"].lower()
    assert "presupuesto" in detalle or "límite" in detalle
    assert gastado <= 6 and pedidas <= 4
    estado = client.get(f"/api/sessions/{sid}/pruebas").json()
    assert estado["costo_total"] == gastado and estado["presupuesto_restante"] == 6 - gastado


def test_el_presupuesto_rechaza_la_prueba_que_lo_excede(demo):
    sid = _sesion_api(3, "c_erc_01")["session_id"]
    catalogo = seguimiento.cargar_catalogo_pruebas()["pruebas"]
    caras = sorted(catalogo, key=lambda p: -p["costo"])
    # Se piden pruebas hasta que la siguiente (la más barata disponible) ya no cabe
    r = client.post(f"/api/sessions/{sid}/pruebas", json={"ids": [caras[0]["id"]]})
    assert r.status_code == 200
    restante = client.get(f"/api/sessions/{sid}/pruebas").json()["presupuesto_restante"]
    assert restante == 6 - caras[0]["costo"]


def test_no_se_piden_pruebas_tras_terminar(demo):
    sid = _sesion_api(2, "c_dengue_01")["session_id"]
    caso = CASOS_POR_ID["c_dengue_01"]
    with patch("app.llm.chat_once", new_callable=AsyncMock) as m:
        m.return_value = "ok"
        r = client.post(f"/api/sessions/{sid}/finish", json={"diagnostico_estudiante": "dengue", "plan": _plan_perfecto(caso)})
    assert r.status_code == 200
    assert client.post(f"/api/sessions/{sid}/pruebas", json={"ids": ["hemograma"]}).status_code == 409


def test_finish_exige_plan_si_el_modulo_esta_activo(demo):
    sid = _sesion_api(2, "c_dengue_01")["session_id"]
    r = client.post(f"/api/sessions/{sid}/finish", json={"diagnostico_estudiante": "dengue"})
    assert r.status_code == 422 and "plan" in r.json()["detail"].lower()


@pytest.mark.parametrize("cambio, texto", [
    ({"disposicion": "inventada"}, "disposición"),
    ({"medicamentos": [{"id": "no_existe"}]}, "Medicamento desconocido"),
    ({"medicamentos": [{"id": "acetaminofen"}, {"id": "acetaminofen"}]}, "repitas"),
    ({"medicamentos": []}, "al menos un medicamento"),
    ({"sin_tratamiento_farmacologico": True}, "sin tratamiento"),
    ({"indicaciones": ["no_existe"]}, "Indicación desconocida"),
])
def test_finish_valida_el_plan(demo, cambio, texto):
    sid = _sesion_api(2, "c_dengue_01")["session_id"]
    plan = _plan_perfecto(CASOS_POR_ID["c_dengue_01"])
    plan.update(cambio)
    r = client.post(f"/api/sessions/{sid}/finish", json={"diagnostico_estudiante": "dengue", "plan": plan})
    assert r.status_code == 422, r.text
    assert texto.lower() in r.json()["detail"].lower()


def test_finish_rechaza_control_fuera_de_rango(demo):
    sid = _sesion_api(2, "c_dengue_01")["session_id"]
    plan = _plan_perfecto(CASOS_POR_ID["c_dengue_01"])
    plan["control_dias"] = 15
    r = client.post(f"/api/sessions/{sid}/finish", json={"diagnostico_estudiante": "dengue", "plan": plan})
    assert r.status_code == 422


def test_finish_ignora_el_plan_si_el_modulo_esta_apagado():
    sid = _sesion_api(2, "c_dengue_01")["session_id"]
    plan = _plan_perfecto(CASOS_POR_ID["c_dengue_01"])
    with patch("app.llm.chat_once", new_callable=AsyncMock) as m:
        m.return_value = "ok"
        r = client.post(f"/api/sessions/{sid}/finish", json={"diagnostico_estudiante": "dengue", "plan": plan})
    j = r.json()
    assert r.status_code == 200
    assert j["plan"] is None and j["pruebas"] is None and j["seguimiento"] is None


def test_finish_con_modulos_devuelve_pruebas_plan_y_control(demo):
    sid = _sesion_api(2, "c_dengue_01")["session_id"]
    caso = CASOS_POR_ID["c_dengue_01"]
    client.post(f"/api/sessions/{sid}/pruebas", json={"ids": ["hemograma", "rx_torax"]})
    with patch("app.llm.chat_once", new_callable=AsyncMock) as m:
        m.return_value = "ok"
        j = client.post(f"/api/sessions/{sid}/finish", json={"diagnostico_estudiante": "dengue", "plan": _plan_perfecto(caso)}).json()
    assert {s["id"]: s["pertinencia"] for s in j["pruebas"]["solicitadas"]} == {"hemograma": "esencial", "rx_torax": "innecesaria"}
    assert "Prueba rápida de dengue (Antígeno NS1 y anticuerpos IgM/IgG)" in j["pruebas"]["esenciales_faltantes"]
    assert j["plan"]["disposicion"]["veredicto"] == "correcta"
    assert j["seguimiento"]["evolucion"] in ("mejora", "parcial", "empeora")
    assert j["desglose"]["pruebas"]["maximo"] > 0 and j["desglose"]["plan"]["maximo"] > 0
    assert j["revision_clinica"]["contenido_sin_validar"] is True


def test_health_informa_catalogos_y_modo_demo(demo):
    j = client.get("/api/health").json()
    assert j["catalogos"] is True and j["seguimiento_demo"] is True


# ----------------------------------------------------------------- puntaje

def test_sin_modulos_el_puntaje_clasico_no_cambia():
    for nivel, esperado in ((1, 60), (2, 60), (3, 45)):
        _, res = _evaluar("c_erc_01", nivel, difs=_difs(CASOS_POR_ID["c_erc_01"], nivel))
        assert res["desglose"]["checklist"]["maximo"] == esperado
        assert res["desglose"]["pruebas"]["maximo"] == 0 and res["desglose"]["plan"]["maximo"] == 0
        assert res["puntaje"] == 100, (nivel, res["desglose"])


@pytest.mark.parametrize("caso_id", CASO_IDS)
@pytest.mark.parametrize("nivel", [1, 2, 3])
def test_con_todo_perfecto_los_modulos_suman_100(demo, caso_id, nivel):
    caso = CASOS_POR_ID[caso_id]
    s, res = _evaluar(caso_id, nivel, plan=_plan_perfecto(caso), difs=_difs(caso, nivel))
    assert s.modulos_activos["plan"] and s.modulos_activos["pruebas"]
    assert res["puntaje"] == 100, res["desglose"]
    assert res["aprobado"] is True and res["alertas_seguridad"] == []
    assert res["seguimiento"]["evolucion"] == "mejora"
    maximos = sum(v["maximo"] for k, v in res["desglose"].items() if "maximo" in v)
    assert round(maximos) == 100


def test_con_solo_el_modulo_de_pruebas_los_pesos_se_reescalan_a_100(demo):
    s = _sesion_directa("c_dengue_01", 2)
    s.modulos_activos = {"pruebas": s.modulos_activos["pruebas"], "plan": False, "seguimiento": False}
    caso = s.caso
    s.mensajes = [{"role": "user", "content": _texto_perfecto(caso)}]
    s.pruebas_pedidas = list(caso["pruebas"]["esenciales"])
    with patch("app.llm.chat_once", new_callable=AsyncMock) as m:
        m.return_value = "ok"
        res = asyncio.run(evaluate.evaluar(s, caso["diagnostico"]))
    assert round(sum(v["maximo"] for k, v in res["desglose"].items() if "maximo" in v)) == 100
    assert res["desglose"]["plan"]["maximo"] == 0 and res["puntaje"] == 100


def test_pruebas_penaliza_innecesarias_y_faltantes():
    caso = CASOS_POR_ID["c_dengue_01"]  # esenciales: hemograma y prueba_dengue
    perfecta = seguimiento.evaluar_pruebas(caso, ["hemograma", "prueba_dengue"])
    assert perfecta["factor"] == 1.0 and perfecta["todas_esenciales"] and not perfecta["innecesarias"]
    media = seguimiento.evaluar_pruebas(caso, ["hemograma"])
    assert media["factor"] == 0.5 and media["esenciales_faltantes"]
    con_extra = seguimiento.evaluar_pruebas(caso, ["hemograma", "prueba_dengue", "rx_torax"])
    assert con_extra["factor"] == pytest.approx(0.8) and con_extra["innecesarias"]
    nada = seguimiento.evaluar_pruebas(caso, [])
    assert nada["factor"] == 0.0 and nada["ninguna_esencial"]
    asfixia = seguimiento.evaluar_pruebas(caso, ["rx_torax", "ecg", "tac_craneo", "pcr", "tsh"])
    assert asfixia["factor"] == 0.0  # nunca negativo


def test_pruebas_sin_esenciales_no_exige_nada():
    caso = {"pruebas": {"resultados": {}, "esenciales": [], "resultado_defecto": "x"}}
    assert seguimiento.evaluar_pruebas(caso, [])["factor"] == 1.0
    assert seguimiento.evaluar_pruebas(caso, ["hemograma"])["factor"] == pytest.approx(0.8)


CASO_PLAN = {
    "plan_esperado": {
        "disposicion": {"correcta": ["referencia"], "aceptable": ["observacion"]},
        "medicamentos": {
            "adecuados": [{"id": "acetaminofen", "nota": "n1"}],
            "aceptables": [{"id": "suero_fisiologico_iv", "nota": "n2"}],
            "contraindicados": [{"id": "ibuprofeno", "motivo": "riesgo de sangrado"}],
        },
        "indicaciones": {"esenciales": ["hidratacion", "control"]},
        "alergias_trampa": [],
    }
}


def _plan(**kw):
    base = {"disposicion": "referencia", "medicamentos": [{"id": "acetaminofen"}], "sin_tratamiento_farmacologico": False,
            "indicaciones": ["hidratacion", "control"], "control_dias": 2}
    base.update(kw)
    return base


def test_plan_perfecto_vale_1():
    r = seguimiento.evaluar_plan(CASO_PLAN, _plan(), [])
    assert r["factor"] == pytest.approx(1.0) and r["alertas_seguridad"] == []


def test_plan_medicacion_aceptable_innecesario_y_contraindicado():
    ev = lambda meds: seguimiento.evaluar_plan(CASO_PLAN, _plan(medicamentos=[{"id": i} for i in meds]), [])
    veredicto = lambda r: {m["id"]: m["veredicto"] for m in r["medicamentos"]}

    r = ev(["acetaminofen", "suero_fisiologico_iv"])
    assert veredicto(r) == {"acetaminofen": "adecuado", "suero_fisiologico_iv": "aceptable"}
    r = ev(["suero_fisiologico_iv"])  # solo el aceptable: 0,5 de la medicación
    assert r["factor"] == pytest.approx(0.5 * 0.5 + 0.3 + 0.2)
    r = ev(["acetaminofen", "omeprazol"])  # un innecesario resta 0,15
    assert veredicto(r)["omeprazol"] == "innecesario"
    assert r["factor"] == pytest.approx(0.5 * 0.85 + 0.3 + 0.2)
    r = ev(["acetaminofen", "ibuprofeno"])  # contraindicado: medicación 0 y alerta
    assert veredicto(r)["ibuprofeno"] == "contraindicado"
    assert r["factor"] == pytest.approx(0.3 + 0.2)
    assert any("riesgo de sangrado" in a for a in r["alertas_seguridad"])


def test_plan_sin_tratamiento_cuando_hacia_falta_medicar():
    r = seguimiento.evaluar_plan(CASO_PLAN, _plan(medicamentos=[], sin_tratamiento_farmacologico=True), [])
    assert r["medicamentos_faltantes"] and r["factor"] == pytest.approx(0.3 + 0.2)


def test_plan_disposicion_e_indicaciones():
    r = seguimiento.evaluar_plan(CASO_PLAN, _plan(disposicion="observacion"), [])
    assert r["disposicion"]["veredicto"] == "aceptable" and r["factor"] == pytest.approx(0.5 + 0.15 + 0.2)
    r = seguimiento.evaluar_plan(CASO_PLAN, _plan(disposicion="ambulatorio"), [])
    assert r["disposicion"]["veredicto"] == "insuficiente" and r["factor"] == pytest.approx(0.5 + 0.2)
    r = seguimiento.evaluar_plan(CASO_PLAN, _plan(indicaciones=["hidratacion"]), [])
    assert len(r["indicaciones"]["faltantes"]) == 1 and r["factor"] == pytest.approx(0.5 + 0.3 + 0.1)


def test_alergia_trampa_alerta_con_y_sin_haber_preguntado():
    caso = copy.deepcopy(CASO_PLAN)
    caso["plan_esperado"]["alergias_trampa"] = [{"medicamento": "amoxicilina", "dato": "alérgico a la penicilina"}]
    plan = _plan(medicamentos=[{"id": "acetaminofen"}, {"id": "amoxicilina"}])

    sin_preguntar = seguimiento.evaluar_plan(caso, plan, ["¿tiene fiebre?"])
    assert sin_preguntar["_variables"]["alergia_ignorada"] is True and sin_preguntar["_variables"]["hay_contraindicado"] is True
    assert any("Alergia no explorada" in a for a in sin_preguntar["alertas_seguridad"])

    preguntando = seguimiento.evaluar_plan(caso, plan, ["¿Es alérgico a algún medicamento?"])
    assert preguntando["_variables"]["alergia_ignorada"] is False and preguntando["_variables"]["hay_contraindicado"] is True
    assert not any("no explorada" in a for a in preguntando["alertas_seguridad"])


# ----------------------------------------------------------------- seguridad clínica

def test_contraindicado_impide_aprobar_en_el_nivel_avanzado(demo):
    caso = CASOS_POR_ID["c_dengue_01"]
    plan = _plan_perfecto(caso)
    plan["medicamentos"].append({"id": "ibuprofeno"})
    _, res = _evaluar("c_dengue_01", 3, plan=plan, difs=_difs(caso, 3))
    assert res["aprobado"] is False and res["puntaje"] <= 69
    assert res["desglose"]["seguridad"]["puntaje_original"] > 69
    assert res["alertas_seguridad"] and res["feedback"].startswith("ALERTA DE SEGURIDAD")


def test_contraindicado_no_recorta_en_niveles_sin_la_regla(demo):
    caso = CASOS_POR_ID["c_dengue_01"]
    plan = _plan_perfecto(caso)
    plan["medicamentos"].append({"id": "ibuprofeno"})
    _, res = _evaluar("c_dengue_01", 2, plan=plan)
    assert res["alertas_seguridad"] and "seguridad" not in res["desglose"]


def test_la_alerta_aparece_en_el_feedback_aunque_el_modelo_la_ignore(demo):
    caso = CASOS_POR_ID["c_dengue_01"]
    plan = _plan_perfecto(caso)
    plan["medicamentos"].append({"id": "aspirina"})
    _, res = _evaluar("c_dengue_01", 2, plan=plan)
    assert "ALERTA DE SEGURIDAD" in res["feedback"] and "Buen trabajo." in res["feedback"]


# ----------------------------------------------------------------- evolución

def test_evolucion_depende_de_las_decisiones(demo):
    caso = CASOS_POR_ID["c_dengue_01"]
    ok = _plan_perfecto(caso)
    _, r = _evaluar("c_dengue_01", 2, plan=ok)
    assert r["seguimiento"]["evolucion"] == "mejora" and r["seguimiento"]["dias"] == caso["evolucion"]["control_en_dias"]

    malo = _plan_perfecto(caso)
    malo["medicamentos"].append({"id": "ibuprofeno"})
    _, r = _evaluar("c_dengue_01", 2, plan=malo)
    assert r["seguimiento"]["evolucion"] == "empeora"

    ambulatorio = _plan_perfecto(caso)
    ambulatorio["disposicion"] = "ambulatorio"
    _, r = _evaluar("c_dengue_01", 2, plan=ambulatorio)
    assert r["seguimiento"]["evolucion"] == "empeora"


def test_empeora_tiene_prioridad_sobre_mejora():
    caso = {"evolucion": {"control_en_dias": 3, "ramas": {
        "mejora": {"condicion": "sin_contraindicados o hay_contraindicado", "relato": "bien"},
        "parcial": {"condicion": "sin_contraindicados", "relato": "regular"},
        "empeora": {"condicion": "hay_contraindicado", "relato": "mal"},
    }}}
    assert seguimiento.resolver_evolucion(caso, {"hay_contraindicado": True})["evolucion"] == "empeora"
    assert seguimiento.resolver_evolucion(caso, {"hay_contraindicado": False, "sin_contraindicados": True})["evolucion"] == "parcial"


def test_si_ninguna_rama_coincide_se_usa_parcial_y_sin_evolucion_no_hay_control():
    caso = {"evolucion": {"control_en_dias": 2, "ramas": {
        "mejora": {"condicion": "hay_contraindicado", "relato": "a"},
        "parcial": {"condicion": "hay_contraindicado", "relato": "p"},
    }}}
    r = seguimiento.resolver_evolucion(caso, {})
    assert r["evolucion"] == "parcial" and r["relato"] == "p"
    assert seguimiento.resolver_evolucion({}, {}) is None


def test_evaluador_de_condiciones_es_seguro_y_correcto():
    f = seguimiento.evaluar_condicion_booleana
    v = {"hay_contraindicado": True, "sin_contraindicados": False, "disposicion_correcta": True}
    assert f("hay_contraindicado y disposicion_correcta", v) is True
    assert f("sin_contraindicados o disposicion_correcta", v) is True
    assert f("no sin_contraindicados", v) is True
    assert f("(hay_contraindicado y no disposicion_correcta) o sin_contraindicados", v) is False
    assert f("", v) is False
    for peligrosa in ("__import__('os').system('x')", "predicado_inventado", "hay_contraindicado +", "1 + 1", "open('x')"):
        with pytest.raises(ValueError):
            f(peligrosa, v)


# ----------------------------------------------------------------- progreso y documentación

def test_el_documento_describe_el_modo_demo():
    assert "SEGUIMIENTO_DEMO" in (Path(__file__).resolve().parents[2] / ".env.example").read_text(encoding="utf-8")


# ----------------------------------------------------------------- diferenciales con alias del principal

def test_un_diferencial_que_contiene_un_alias_del_principal_si_puntua():
    """«Diabetes insípida» contiene «diabetes» (alias de la diabetes mellitus), pero es otro diagnóstico."""
    caso = CASOS_POR_ID["c_dm2_01"]
    acertados = evaluate._aciertos_diferenciales(caso, "Diabetes mellitus tipo 2", ["Diabetes insípida", "Hipertiroidismo"])
    assert "Diabetes insípida" in acertados


def test_el_diagnostico_principal_no_puntua_como_diferencial():
    caso = CASOS_POR_ID["c_dm2_01"]
    assert evaluate._aciertos_diferenciales(caso, "Diabetes mellitus tipo 2", ["diabetes mellitus", "DM2"]) == []


def test_un_diferencial_mas_especifico_no_cuenta_como_diagnostico_principal():
    caso = CASOS_POR_ID["c_dm2_01"]
    assert evaluate._diagnostico_correcto(caso, "Diabetes insípida") is False
    assert evaluate._diagnostico_correcto(caso, "Diabetes mellitus tipo 2") is True
    assert evaluate._diagnostico_correcto(caso, "diabetes") is True
    assert evaluate._diagnostico_correcto(caso, "Diabetes insípida y diabetes mellitus tipo 2") is True


def test_gastroenteritis_omitir_indicaciones_no_cuenta_como_pastilla_contraindicada(demo):
    """El relato de «empeora» en gastroenteritis habla de una pastilla contraindicada: solo debe salir con una."""
    caso = CASOS_POR_ID["c_gea_01"]
    plan = _plan_perfecto(caso)
    plan["indicaciones"] = ["hidratacion"]  # faltan indicaciones esenciales, sin ningún contraindicado
    _, r = _evaluar("c_gea_01", 2, plan=plan)
    assert r["seguimiento"]["evolucion"] == "parcial"
    assert "pastilla" not in r["seguimiento"]["relato"]

    con_contra = _plan_perfecto(caso)
    con_contra["medicamentos"].append({"id": "loperamida"})
    _, r = _evaluar("c_gea_01", 2, plan=con_contra)
    assert r["seguimiento"]["evolucion"] == "empeora" and "pastilla" in r["seguimiento"]["relato"]
