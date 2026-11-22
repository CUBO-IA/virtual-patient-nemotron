"""Pruebas exhaustivas para el sistema de niveles (NIVELES.md)."""

from collections import Counter
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from app import assign, evaluate, llm, niveles, prompts, sessions
from app.main import app

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
client = TestClient(app)


# 1. Configuración de niveles
def test_configuracion_niveles():
    data = niveles.cargar_niveles()
    assert data["version"] == 1
    assert data["nivel_por_defecto"] == 2
    assert len(data["niveles"]) == 3

    ids = [n["id"] for n in data["niveles"]]
    assert ids == [1, 2, 3]

    for n in data["niveles"]:
        pesos = n["pesos"]
        assert sum(pesos.values()) == 100
        if n.get("diferenciales_requeridos", 0) > 0:
            assert pesos.get("diferenciales", 0) > 0
        if not n.get("pistas", {}).get("permitidas", True):
            assert n.get("pistas", {}).get("max") == 0
        assert n["actitud_paciente"] in ("colaborador", "normal", "reservado")


# 2. Creación de sesiones por nivel y validaciones
def test_sesion_creacion_por_nivel():
    # Sin cuerpo -> nivel 2 por defecto
    r_def = client.post("/api/sessions")
    assert r_def.status_code == 200
    d_def = r_def.json()
    assert d_def["nivel"]["id"] == 2
    assert d_def["nivel"]["max_preguntas"] == 25
    assert d_def["nivel"]["guia_anamnesis"] is None

    # Nivel 1 -> Básico con guía de anamnesis
    r_n1 = client.post("/api/sessions", json={"nivel": 1})
    assert r_n1.status_code == 200
    d_n1 = r_n1.json()
    assert d_n1["nivel"]["id"] == 1
    assert d_n1["nivel"]["max_preguntas"] is None
    assert d_n1["nivel"]["pistas"]["penalizacion"] == 0
    assert isinstance(d_n1["nivel"]["guia_anamnesis"], list)
    assert len(d_n1["nivel"]["guia_anamnesis"]) == 9
    # No filtra keywords en guia_anamnesis
    assert "keywords" not in d_n1["nivel"]["guia_anamnesis"][0]

    # Nivel 3 -> Avanzado sin pistas
    r_n3 = client.post("/api/sessions", json={"nivel": 3})
    assert r_n3.status_code == 200
    d_n3 = r_n3.json()
    assert d_n3["nivel"]["id"] == 3
    assert d_n3["nivel"]["max_preguntas"] == 15
    assert d_n3["nivel"]["pistas"]["permitidas"] is False
    assert d_n3["nivel"]["diferenciales_requeridos"] == 2

    # Niveles inválidos -> 422
    for inv in [0, 4, "a"]:
        r_inv = client.post("/api/sessions", json={"nivel": inv})
        assert r_inv.status_code == 422

    # caso_id inexistente -> 503 o 422
    r_no_caso = client.post("/api/sessions", json={"nivel": 1, "caso_id": "c_inexistente_99"})
    assert r_no_caso.status_code in (422, 503)

    # caso_id demasiado difícil para nivel 1 -> 422 (c_erc_01 es dificultad 3)
    r_dif = client.post("/api/sessions", json={"nivel": 1, "caso_id": "c_erc_01"})
    assert r_dif.status_code == 422


# 3. Sorteo por nivel (distribución y compatibilidad)
def test_sorteo_por_nivel():
    n1 = niveles.obtener_nivel(1)
    n2 = niveles.obtener_nivel(2)
    n3 = niveles.obtener_nivel(3)

    # Nivel 1: solo dificultad 1
    for _ in range(100):
        c, p = assign.sortear(nivel=n1)
        assert c["dificultad"] == 1

    # Nivel 2: dificultad <= 2 y mayoría de 2 (por peso_dificultad_igual = 2)
    dificultades_n2 = []
    for _ in range(200):
        c, p = assign.sortear(nivel=n2)
        assert c["dificultad"] in (1, 2)
        dificultades_n2.append(c["dificultad"])
    counts_n2 = Counter(dificultades_n2)
    assert counts_n2[2] > counts_n2[1]

    # Nivel 3: pueden salir todos
    dificultades_n3 = set()
    for _ in range(200):
        c, p = assign.sortear(nivel=n3)
        assert c["dificultad"] in (1, 2, 3)
        dificultades_n3.add(c["dificultad"])
    assert 3 in dificultades_n3

    # caso_id fijo respeta el caso
    c_fijo, _ = assign.sortear(caso_id="c_dengue_01", nivel=n1)
    assert c_fijo["id"] == "c_dengue_01"


# 4. Pistas por nivel
def test_pistas_por_nivel():
    # Nivel 3: pistas no permitidas -> 403
    r_s3 = client.post("/api/sessions", json={"nivel": 3})
    sid3 = r_s3.json()["session_id"]
    r_pista3 = client.post(f"/api/sessions/{sid3}/pista")
    assert r_pista3.status_code == 403

    # Nivel 1: penalización 0
    r_s1 = client.post("/api/sessions", json={"nivel": 1})
    sid1 = r_s1.json()["session_id"]
    r_pista1 = client.post(f"/api/sessions/{sid1}/pista")
    assert r_pista1.status_code == 200
    assert r_pista1.json()["penalizacion"] == 0

    # Nivel 2: penalización 0.5
    r_s2 = client.post("/api/sessions", json={"nivel": 2})
    sid2 = r_s2.json()["session_id"]
    r_pista2 = client.post(f"/api/sessions/{sid2}/pista")
    assert r_pista2.status_code == 200
    assert r_pista2.json()["penalizacion"] == 0.5


# 5. Límite de preguntas
async def mock_stream_tokens(*args, **kwargs):
    yield "Respuesta paciente."


def test_limite_de_preguntas():
    r_s3 = client.post("/api/sessions", json={"nivel": 3})
    sid3 = r_s3.json()["session_id"]

    # Nivel 3 permite 15 preguntas
    with patch("app.llm.stream_chat", side_effect=mock_stream_tokens):
        for i in range(15):
            res = client.post(f"/api/sessions/{sid3}/chat", json={"message": f"Pregunta {i+1}?"})
            assert res.status_code == 200

        # La 16.ª debe dar 409
        res_bloqueado = client.post(f"/api/sessions/{sid3}/chat", json={"message": "Pregunta 16?"})
        assert res_bloqueado.status_code == 409
        assert "Alcanzaste el límite de preguntas" in res_bloqueado.json()["detail"]


# 6. Evento done con contador y guia_cubierta
def test_evento_done_y_guia_cubierta():
    # Nivel 1
    r_s1 = client.post("/api/sessions", json={"nivel": 1})
    sid1 = r_s1.json()["session_id"]

    with patch("app.llm.stream_chat", side_effect=mock_stream_tokens):
        res1 = client.post(f"/api/sessions/{sid1}/chat", json={"message": "¿Cuál es su motivo de consulta y desde cuándo empezó?"})
        assert res1.status_code == 200
        text1 = res1.text
        assert "preguntas" in text1
        assert "guia_cubierta" in text1
        assert "motivo" in text1 or "inicio" in text1

    # Nivel 2 (no incluye guia_cubierta)
    r_s2 = client.post("/api/sessions", json={"nivel": 2})
    sid2 = r_s2.json()["session_id"]
    with patch("app.llm.stream_chat", side_effect=mock_stream_tokens):
        res2 = client.post(f"/api/sessions/{sid2}/chat", json={"message": "Hola"})
        assert res2.status_code == 200
        text2 = res2.text
        assert "preguntas" in text2
        assert "guia_cubierta" not in text2


# 7. Puntaje, desglose y regresión
@pytest.mark.anyio
async def test_puntaje_desglose_y_regresion():
    casos = json.loads((DATA_DIR / "casos.json").read_text(encoding="utf-8"))
    c_dengue = next(c for c in casos if c["id"] == "c_dengue_01")
    persona = {"nombre": "Test", "edad": 25, "sexo": "M"}

    # Nivel 2: regresión exacta
    s2 = sessions.Session(
        id="s_test_2",
        caso=c_dengue,
        persona=persona,
        nivel=niveles.obtener_nivel(2),
        mensajes=[
            {"role": "user", "content": "frecuencia del dolor retroocular, fiebre, contactos"},
            {"role": "assistant", "content": "tengo dolor"},
        ],
        pistas_usadas=2,
    )
    with patch("app.llm.chat_once", new_callable=AsyncMock) as m_llm:
        m_llm.return_value = "Feedback"
        res2 = await evaluate.evaluar(s2, "Dengue")

    assert res2["descuento_pistas"] == 1  # 2 pistas * 0.5 = 1
    assert "desglose" in res2
    assert "checklist" in res2["desglose"]
    assert "diagnostico" in res2["desglose"]
    assert "banderas" in res2["desglose"]
    assert "diferenciales" in res2["desglose"]

    # Nivel 1: pistas gratis (descuento 0)
    s1 = sessions.Session(
        id="s_test_1",
        caso=c_dengue,
        persona=persona,
        nivel=niveles.obtener_nivel(1),
        mensajes=list(s2.mensajes),
        pistas_usadas=5,
    )
    with patch("app.llm.chat_once", new_callable=AsyncMock) as m_llm:
        m_llm.return_value = "Feedback"
        res1 = await evaluate.evaluar(s1, "Dengue")
    assert res1["descuento_pistas"] == 0


# 8. Diagnóstico diferencial en Nivel 3
def test_diferenciales_nivel_3():
    r_s3 = client.post("/api/sessions", json={"nivel": 3, "caso_id": "c_erc_01"})
    sid3 = r_s3.json()["session_id"]

    # Faltan diferenciales -> 422
    r_fin_falta = client.post(f"/api/sessions/{sid3}/finish", json={"diagnostico_estudiante": "Enfermedad renal crónica"})
    assert r_fin_falta.status_code == 422

    # Diferenciales repetidos -> 422
    r_fin_rep = client.post(
        f"/api/sessions/{sid3}/finish",
        json={
            "diagnostico_estudiante": "Enfermedad renal crónica",
            "diferenciales": ["Insuficiencia cardíaca", "Insuficiencia cardíaca"],
        },
    )
    assert r_fin_rep.status_code == 422

    # Diferencial igual al principal -> 422
    r_fin_igual = client.post(
        f"/api/sessions/{sid3}/finish",
        json={
            "diagnostico_estudiante": "Enfermedad renal crónica",
            "diferenciales": ["Enfermedad renal crónica", "Cirrosis hepática"],
        },
    )
    assert r_fin_igual.status_code == 422

    # Válido con aciertos
    with patch("app.llm.chat_once", new_callable=AsyncMock) as m_llm:
        m_llm.return_value = "Buen trabajo"
        r_fin_ok = client.post(
            f"/api/sessions/{sid3}/finish",
            json={
                "diagnostico_estudiante": "Enfermedad renal crónica",
                "diferenciales": ["falla cardiaca", "cirrosis"],
            },
        )
        assert r_fin_ok.status_code == 200
        res = r_fin_ok.json()
        assert res["desglose"]["diferenciales"]["obtenido"] == 10.0
        assert "diferenciales_razonables" in res
        assert "Insuficiencia cardíaca" in res["diferenciales_razonables"]


# 9. No-fuga crítica
def test_no_fuga_niveles():
    casos = json.loads((DATA_DIR / "casos.json").read_text(encoding="utf-8"))
    personas = json.loads((DATA_DIR / "personas.json").read_text(encoding="utf-8"))

    # A. POST /api/sessions no expone datos sensibles
    r_ses = client.post("/api/sessions", json={"nivel": 1})
    data = r_ses.json()
    assert "caso_id" not in data
    assert "dificultad" not in data
    assert "diferenciales" not in data
    assert "pistas" not in data
    assert "lista_verificacion" not in data

    # B. anamnesis_guia.json no contiene diagnósticos ni diferenciales
    guia = json.loads((DATA_DIR / "anamnesis_guia.json").read_text(encoding="utf-8"))
    todos_terminos = []
    for c in casos:
        todos_terminos.append(c["diagnostico"])
        todos_terminos.extend(c.get("diagnostico_alias", []))
        for d in c.get("diferenciales", []):
            todos_terminos.append(d["nombre"])
            todos_terminos.extend(d.get("alias", []))

    for it in guia["items"]:
        t = it["texto"]
        kws = it["keywords"]
        for term in todos_terminos:
            tn = evaluate.norm(term)
            assert tn not in evaluate.norm(t), f"Término '{term}' en texto de guía"
            for kw in kws:
                assert tn not in evaluate.norm(kw), f"Término '{term}' en keyword '{kw}'"

    # C. Prompt del paciente en cualquier nivel no contiene el diagnóstico
    for nivel_id in (1, 2, 3):
        cfg = niveles.obtener_nivel(nivel_id)
        for c in casos:
            p = personas[0]
            pr = prompts.system_paciente(p, c, nivel=cfg)
            assert c["diagnostico"] not in pr
            for alias in c.get("diagnostico_alias", []):
                assert evaluate.norm(alias) not in evaluate.norm(pr)
