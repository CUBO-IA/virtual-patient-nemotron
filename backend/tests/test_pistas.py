"""Pruebas del sistema de pistas opcionales según pistas-por-caso.md."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_pedir_pista_niveles_y_avance():
    # 1. Crear sesión
    resp = client.post("/api/sessions")
    assert resp.status_code == 200
    sid = resp.json()["session_id"]

    # 2. Primera pista: nivel 1 del primer ítem
    p1 = client.post(f"/api/sessions/{sid}/pista")
    assert p1.status_code == 200
    d1 = p1.json()
    assert d1["disponible"] is True
    assert d1["nivel"] == 1
    assert d1["pistas_usadas"] == 1
    assert len(d1["pista"]) > 0
    item1 = d1["item"]

    # 3. Pedir pista sobre el mismo ítem sin preguntar -> sube a nivel 2
    p2 = client.post(f"/api/sessions/{sid}/pista")
    assert p2.status_code == 200
    d2 = p2.json()
    assert d2["item"] == item1
    assert d2["nivel"] == 2
    assert d2["pistas_usadas"] == 2

    # 4. Pedir pista de nuevo -> sube a nivel 3
    p3 = client.post(f"/api/sessions/{sid}/pista")
    assert p3.status_code == 200
    d3 = p3.json()
    assert d3["item"] == item1
    assert d3["nivel"] == 3
    assert d3["pistas_usadas"] == 3

    # 5. Si pide otra vez, no supera nivel 3
    p4 = client.post(f"/api/sessions/{sid}/pista")
    assert p4.status_code == 200
    d4 = p4.json()
    assert d4["item"] == item1
    assert d4["nivel"] == 3
    assert d4["pistas_usadas"] == 4

    # 6. Error 404 si sesión no existe
    p_404 = client.post("/api/sessions/inexistente/pista")
    assert p_404.status_code == 404


def test_glosario_endpoint():
    resp = client.get("/api/glosario")
    assert resp.status_code == 200
    data = resp.json()
    assert "anamnesis" in data
    assert "motivo_de_consulta" in data
