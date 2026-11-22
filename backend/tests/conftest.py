"""Aislamiento de las pruebas: no deben depender del .env de quien las corre.

`app.config` lee el `.env` de la raíz. Si alguien activa SEGUIMIENTO_DEMO=true para una demostración,
las pruebas que asumen «módulos apagados por defecto» fallarían. Aquí se fija el valor por defecto;
las pruebas que necesitan el modo demostración lo activan con su propia fixture.
"""
import pytest

from app import config


@pytest.fixture(autouse=True)
def _config_aislada(monkeypatch):
    monkeypatch.setattr(config, "SEGUIMIENTO_DEMO", False)
    monkeypatch.setattr(config, "RAG_ENABLED", False)
