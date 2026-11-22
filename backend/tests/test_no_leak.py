"""Pruebas de no-fuga de campos sensibles y diagnósticos."""

import json
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.prompts import mensajes_paciente, system_paciente
from app.evaluate import norm
from app import config

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
client = TestClient(app)

HIDDEN_FIELDS = {"diagnostico", "lista_verificacion", "datos_si_pregunta", "banderas_rojas"}


def test_api_sessions_no_contiene_campos_ocultos():
    for _ in range(50):
        resp = client.post("/api/sessions")
        assert resp.status_code == 200
        data = resp.json()
        for field in HIDDEN_FIELDS:
            assert field not in data, f"Campo oculto '{field}' expuesto en POST /api/sessions"
            assert field not in data.get("paciente", {}), f"Campo oculto '{field}' expuesto en paciente"
        assert "perfil" not in data["paciente"], "El perfil social no se devuelve al cliente"
        assert {"estado_civil", "nivel_educativo", "hogar"} <= set(data["paciente"])


def test_api_sessions_urgencias_expone_perfil_sin_campos_de_urgencia(monkeypatch):
    monkeypatch.setattr(config, "SEGUIMIENTO_DEMO", True)
    resp = client.post("/api/sessions", json={"modo":"urgencias", "caso_id":"u_infarto_01"})
    assert resp.status_code == 200
    data = resp.json()
    assert {"estado_civil", "nivel_educativo", "hogar"} <= set(data["paciente"])
    for field in HIDDEN_FIELDS | {"signos_activos", "accion_esperada", "datos_ocultos", "explicacion"}:
        assert field not in json.dumps(data, ensure_ascii=False)
    assert "nivel" not in data and "urgencia" not in data


def test_system_paciente_no_contiene_diagnostico_ni_alias():
    casos = json.loads((DATA_DIR / "casos.json").read_text(encoding="utf-8"))
    personas = json.loads((DATA_DIR / "personas.json").read_text(encoding="utf-8"))
    assert len(casos) >= 8

    # Para cada caso, probamos con una persona compatible
    for caso in casos:
        p = next(
            p for p in personas
            if p["sexo"] in caso["restricciones"]["sexo"]
            and caso["restricciones"]["edad_min"] <= p["edad"] <= caso["restricciones"]["edad_max"]
        )

        prompt = system_paciente(p, caso)
        prompt_norm = norm(prompt)

        # Verificar que el diagnóstico no aparece
        diag_norm = norm(caso["diagnostico"])
        assert diag_norm not in prompt_norm, (
            f"El diagnóstico '{caso['diagnostico']}' aparece en system_paciente para el caso {caso['id']}"
        )

        # Verificar que ningún alias aparece
        for alias in caso.get("diagnostico_alias", []):
            alias_norm = norm(alias)
            assert alias_norm not in prompt_norm, (
                f"El alias '{alias}' de {caso['id']} aparece en system_paciente"
            )


def test_mensajes_paciente_con_perfil_no_contienen_diagnostico_ni_alias():
    casos = json.loads((DATA_DIR / "casos.json").read_text(encoding="utf-8"))
    personas = json.loads((DATA_DIR / "personas.json").read_text(encoding="utf-8"))
    for caso in casos:
        persona = next(
            p for p in personas
            if p["sexo"] in caso["restricciones"]["sexo"]
            and caso["restricciones"]["edad_min"] <= p["edad"] <= caso["restricciones"]["edad_max"]
        )
        mensajes = mensajes_paciente(persona, caso, [{"role": "user", "content": "¿A qué se dedica?"}])
        contenido = norm(" ".join(m["content"] for m in mensajes))
        assert norm(caso["diagnostico"]) not in contenido
        for alias in caso.get("diagnostico_alias", []):
            assert norm(alias) not in contenido


def test_glosario_y_placeholders_no_nombran_diagnosticos():
    """El glosario (tooltips del chat) y los placeholders del formulario no deben regalar el diagnóstico."""
    import json
    import re
    from pathlib import Path
    from app.evaluate import norm

    raiz = Path(__file__).resolve().parents[2]
    casos = json.loads((raiz / "data" / "casos.json").read_text(encoding="utf-8"))
    nombres = set()
    for c in casos:
        nombres.add(norm(c["diagnostico"]).strip())
        nombres.update(norm(a).strip() for a in c.get("diagnostico_alias", []))
    extra = {"dengue", "chikungunya", "zika", "leptospirosis", "hipertension arterial", "diabetes mellitus", "diabetes"}
    nombres = {n for n in nombres | extra if len(n) >= 5}

    textos = list(json.loads((raiz / "data" / "glosario.json").read_text(encoding="utf-8")).values())
    jsx = (raiz / "frontend" / "src" / "components" / "GlossaryTip.jsx").read_text(encoding="utf-8")
    textos += re.findall(r':\s*"([^"]+)"', jsx.split("export default")[0])
    app = (raiz / "frontend" / "src" / "App.jsx").read_text(encoding="utf-8")
    textos += re.findall(r'placeholder="([^"]+)"', app)
    pruebas = (raiz / "frontend" / "src" / "components" / "PruebasPanel.jsx").read_text(encoding="utf-8")
    textos += re.findall(r'placeholder="([^"]+)"', pruebas)

    for t in textos:
        n = f" {norm(t).strip()} "
        for nombre in nombres:
            assert f" {nombre} " not in n and f" {nombre}s " not in n, f"«{t}» nombra «{nombre}»"
