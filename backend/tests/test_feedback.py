import asyncio
from unittest.mock import AsyncMock, patch

from app import config, explicar
from app.evaluate import evaluar
from app.sessions import Session
from app.texto import limpiar_texto_modelo


def _caso():
    return {"id":"c_feedback","diagnostico":"Caso ficticio","diagnostico_alias":[],"lista_verificacion":[{"id":"inicio","texto":"Inicio de síntomas","keywords":["cuando"]}],"banderas_rojas":[],"guia_ref":"prueba"}


def test_limpia_markdown_y_titulos():
    raw = "### Retroalimentación\n\n#### Aspectos Correctos\n1. **Definición y Clasificación**\n---\n#### Recomendaciones\n- Preguntaste por el inicio."
    out = limpiar_texto_modelo(raw)
    assert not any(x in out for x in ("#", "*", "---"))
    assert not out.lower().startswith(("retroalimentación", "aspectos correctos"))


def test_corta_en_frase_completa():
    out = limpiar_texto_modelo(("Esta es una frase completa. " * 40), max_chars=90)
    assert len(out) <= 90 and out.endswith((".", "!", "?"))


def test_sin_puntuacion_corta_palabra_completa_con_elipsis():
    out = limpiar_texto_modelo("palabra " * 50, max_chars=45)
    assert len(out) <= 45 and out.endswith("…") and out[:-1].split()[-1] == "palabra"


def test_evaluar_no_pasa_guias_y_conserva_citas(monkeypatch):
    monkeypatch.setattr(config, "RAG_ENABLED", True)
    cita = {"fuente":"guia.pdf", "fragmento":"SECRETO_DE_GUIA_123"}
    s = Session(id="f1", caso=_caso(), persona={"nombre":"Ana"}, mensajes=[{"role":"user","content":"¿Cuándo empezó?"}])
    async def fake_llm(messages, **kwargs):
        assert "SECRETO_DE_GUIA_123" not in str(messages)
        return "Tu diagnóstico fue incorrecto. Preguntaste por el inicio. Te faltó explorar otros datos. La próxima vez revisa la lista completa."
    with patch("app.rag.consultar", new_callable=AsyncMock, return_value=[cita]), patch("app.llm.chat_once", new_callable=AsyncMock, side_effect=fake_llm):
        res = asyncio.run(evaluar(s, "Otro"))
    assert res["citas"] == [cita]


def test_si_reintento_sigue_desviado_usa_feedback_determinista():
    s = Session(id="f2", caso=_caso(), persona={"nombre":"Ana"}, mensajes=[{"role":"user","content":"Hola"}])
    desviado = "### Resumen\n" + ("1. **Tema ajeno**\n" * 100)
    with patch("app.llm.chat_once", new_callable=AsyncMock, side_effect=[desviado, desviado]) as modelo:
        res = asyncio.run(evaluar(s, "Otro"))
    assert modelo.await_count == 2
    assert "El diagnóstico real era" in res["feedback"]
    assert "Tema ajeno" not in res["feedback"]


def test_explicar_limpia_markdown():
    s = Session(id="f3", caso=_caso(), persona={"nombre":"Ana"}, result={})
    with patch("app.explicar.resolver", return_value={"titulo":"Prueba", "valoracion":"útil", "nota":None}), \
         patch("app.explicar._fragmentos", new_callable=AsyncMock, return_value=[]), \
         patch("app.llm.chat_once", new_callable=AsyncMock, return_value="**Explicación clara para esta decisión.**"):
        result = asyncio.run(explicar.explicar(s, s.caso, "prueba", "x"))
    assert result["explicacion"] == "Explicación clara para esta decisión."


def test_citas_de_la_evaluacion_se_recortan_y_descartan_bibliografia(monkeypatch):
    """Las citas de /finish no vuelcan fragmentos crudos de ~2.800 caracteres ni listas de referencias."""
    import asyncio
    from unittest.mock import AsyncMock, patch
    from app import config, evaluate

    largo = "La diabetes se diagnostica con glucemia en ayunas. " * 40
    crudas = [
        {"fuente": "dm2.pdf", "fragmento": largo, "distancia": 500.0},
        {"fuente": "dm2.pdf", "fragmento": "Referencias 1. Goicoechea M, et al. Available from: http://x", "distancia": 520.0},
        {"fuente": "dm2.pdf", "fragmento": "Segunda cita   con\n saltos y espacios.", "distancia": 540.0},
    ]
    monkeypatch.setattr(config, "RAG_ENABLED", True)
    with patch("app.rag.consultar", new_callable=AsyncMock, return_value=crudas) as consulta:
        citas = asyncio.run(evaluate._citas_relevantes({"guia_ref": "dm2", "diagnostico": "Diabetes"}, "diabetes"))
    assert consulta.await_args.kwargs["max_distancia"] == config.RAG_MAX_DISTANCIA
    assert len(citas) == 2 and all(set(c) == {"fuente", "fragmento"} for c in citas)
    assert len(citas[0]["fragmento"]) <= evaluate.MAX_CHARS_CITA + 1 and citas[0]["fragmento"].endswith("…")
    assert citas[1]["fragmento"] == "Segunda cita con saltos y espacios."
