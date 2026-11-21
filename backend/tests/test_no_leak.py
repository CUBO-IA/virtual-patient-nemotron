"""Pruebas de no-fuga de campos sensibles y diagnósticos."""

import json
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.prompts import system_paciente
from app.evaluate import norm

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
