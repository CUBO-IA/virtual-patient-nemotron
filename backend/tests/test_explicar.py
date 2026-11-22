"""«¿Por qué?»: explicación de decisiones apoyada en guías (RAG). No necesita Ollama ni Chroma."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app import config, explicar
from app.main import app

client = TestClient(app)

PLAN = {
    "disposicion": "ambulatorio",
    "medicamentos": [{"id": "sales_rehidratacion"}, {"id": "ibuprofeno"}],
    "indicaciones": ["hidratacion"],
    "control_dias": 3,
}


@pytest.fixture
def terminada(monkeypatch):
    """Consulta de gastroenteritis ya terminada (módulos activos en modo demostración)."""
    monkeypatch.setattr(config, "SEGUIMIENTO_DEMO", True)
    sid = client.post("/api/sessions", json={"nivel": 1, "caso_id": "c_gea_01"}).json()["session_id"]
    return sid


def _finish(sid):
    with patch("app.llm.chat_once", new_callable=AsyncMock) as m:
        m.return_value = "Bien."
        r = client.post(f"/api/sessions/{sid}/finish",
                        json={"diagnostico_estudiante": "gastroenteritis aguda", "plan": PLAN})
    assert r.status_code == 200, r.text
    return r.json()


def _pedir(sid, tipo, id_):
    return client.post(f"/api/sessions/{sid}/explicar", json={"tipo": tipo, "id": id_})


def test_no_se_puede_explicar_antes_de_terminar(terminada):
    r = _pedir(terminada, "medicamento", "sales_rehidratacion")
    assert r.status_code == 409


def test_tipo_invalido_y_decision_inexistente(terminada):
    _finish(terminada)
    assert _pedir(terminada, "nada", "x").status_code == 422
    assert _pedir(terminada, "medicamento", "no_existe").status_code == 404
    assert client.post("/api/sessions/" + "0" * 32 + "/explicar", json={"tipo": "prueba", "id": "x"}).status_code == 404


def test_sin_rag_devuelve_solo_la_nota_del_caso(terminada, monkeypatch):
    monkeypatch.setattr(config, "RAG_ENABLED", False)
    _finish(terminada)
    d = _pedir(terminada, "medicamento", "sales_rehidratacion").json()
    assert d["origen"] == "caso" and d["explicacion"] is None and d["fuentes"] == []
    assert d["nota"]  # nota escrita en el caso


def test_con_guia_el_modelo_recibe_solo_los_fragmentos(terminada, monkeypatch):
    monkeypatch.setattr(config, "RAG_ENABLED", True)
    _finish(terminada)
    frags = [{"fuente": "gastroenteritis.pdf", "fragmento": "Las SRO previenen la deshidratación."}]
    with patch("app.rag.consultar", new_callable=AsyncMock, return_value=frags) as consulta, \
            patch("app.llm.chat_once", new_callable=AsyncMock, return_value="Se apoya en [1].") as llm:
        d = _pedir(terminada, "medicamento", "sales_rehidratacion").json()
    assert d["origen"] == "guia" and d["explicacion"] == "Se apoya en [1]."
    assert d["fuentes"][0]["fuente"] == "gastroenteritis.pdf"
    # se aplicó el umbral de relevancia y la guía del caso
    assert consulta.await_args.kwargs["max_distancia"] == config.RAG_MAX_DISTANCIA_LEXICA
    assert consulta.await_args.args[0] == "gastroenteritis"
    prompt = llm.await_args.args[0][1]["content"]
    assert "[1] Las SRO previenen la deshidratación." in prompt


def test_sin_sustento_no_inventa_explicacion(terminada, monkeypatch):
    monkeypatch.setattr(config, "RAG_ENABLED", True)
    _finish(terminada)
    frags = [{"fuente": "gastroenteritis.pdf", "fragmento": "Texto sin relación."}]
    with patch("app.rag.consultar", new_callable=AsyncMock, return_value=frags), \
            patch("app.llm.chat_once", new_callable=AsyncMock, return_value="SIN_SUSTENTO"):
        d = _pedir(terminada, "medicamento", "ibuprofeno").json()
    assert d["origen"] == "caso" and d["explicacion"] is None and d["fuentes"] == []


def test_fragmentos_de_bibliografia_se_descartan(terminada, monkeypatch):
    monkeypatch.setattr(config, "RAG_ENABLED", True)
    _finish(terminada)
    frags = [{"fuente": "x.pdf", "fragmento": "Lecturas recomendadas 1. Políticas de tratamiento..."},
             {"fuente": "x.pdf", "fragmento": "Goicoechea M, et al. Aspirin. Available from: http://x"}]
    with patch("app.rag.consultar", new_callable=AsyncMock, return_value=frags), \
            patch("app.llm.chat_once", new_callable=AsyncMock) as llm:
        d = _pedir(terminada, "indicacion", "hidratacion").json()
    assert d["origen"] == "caso" and d["fuentes"] == []
    llm.assert_not_awaited()


def test_si_el_modelo_falla_se_devuelven_las_fuentes(terminada, monkeypatch):
    from app import llm as llm_mod
    monkeypatch.setattr(config, "RAG_ENABLED", True)
    _finish(terminada)
    frags = [{"fuente": "gastroenteritis.pdf", "fragmento": "Las SRO previenen la deshidratación."}]
    with patch("app.rag.consultar", new_callable=AsyncMock, return_value=frags), \
            patch("app.llm.chat_once", new_callable=AsyncMock, side_effect=llm_mod.LLMError("caído")):
        d = _pedir(terminada, "medicamento", "sales_rehidratacion").json()
    assert d["origen"] == "guia" and d["explicacion"] is None and len(d["fuentes"]) == 1


def test_finish_expone_ids_de_lo_que_falto(terminada):
    r = _finish(terminada)
    assert "faltantes_ids" in r["plan"]["indicaciones"]
    assert "medicamentos_faltantes_ids" in r["plan"]
    assert len(r["plan"]["indicaciones"]["faltantes"]) == len(r["plan"]["indicaciones"]["faltantes_ids"])


def test_busqueda_hibrida_prioriza_fragmentos_que_nombran_la_decision():
    cand = [
        {"fuente": "n.pdf", "fragmento": "Definición general de la neumonía.", "distancia": 559.0},
        {"fuente": "n.pdf", "fragmento": "Se indica amoxicilina más ácido clavulánico en pacientes con comorbilidad.", "distancia": 700.0},
        {"fuente": "n.pdf", "fragmento": "Otra cosa sin relación.", "distancia": 770.0},
    ]
    elegidos = explicar._elegir(cand, "Amoxicilina + Ácido clavulánico 875/125 mg")
    assert elegidos[0]["fragmento"].startswith("Se indica amoxicilina")   # léxico primero
    assert len(elegidos) == 2                                           # + el cercano; el lejano sin término se descarta
    assert all("Otra cosa" not in e["fragmento"] for e in elegidos)


def test_recorte_se_centra_en_el_termino():
    largo = "x " * 800 + "amoxicilina clavulánico se recomienda " + "y " * 800
    rec = explicar._recorte(largo, "Amoxicilina 500 mg")
    assert "amoxicilina" in rec and len(rec) <= explicar.MAX_FRAGMENTO


def test_umbral_de_rag_filtra_por_distancia(monkeypatch):
    """rag.consultar descarta fragmentos más lejanos que max_distancia."""
    import asyncio
    from app import rag

    class FakeColl:
        def query(self, **kw):
            return {"documents": [["cerca", "lejos"]], "metadatas": [[{"fuente": "a"}, {"fuente": "b"}]],
                    "distances": [[500.0, 800.0]]}

    class FakeClient:
        def __init__(self, **kw): pass
        def get_collection(self, name): return FakeColl()

    import chromadb
    monkeypatch.setattr(config, "RAG_ENABLED", True)
    monkeypatch.setattr(chromadb, "HttpClient", FakeClient)
    monkeypatch.setattr(rag, "embed_query", AsyncMock(return_value=[0.1]))
    todos = asyncio.run(rag.consultar("erc", "q"))
    filtrados = asyncio.run(rag.consultar("erc", "q", max_distancia=660))
    assert [c["fragmento"] for c in todos] == ["cerca", "lejos"]
    assert [c["fragmento"] for c in filtrados] == ["cerca"]
