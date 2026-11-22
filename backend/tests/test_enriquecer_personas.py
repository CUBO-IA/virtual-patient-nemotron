import json
from pathlib import Path

import pytest

from scripts.enriquecer_personas import enriquecer, enriquecer_archivo


def _persona():
    return {"id":"p_001", "nombre":"Ana", "edad":34, "sexo":"F", "municipio":"San Salvador", "ocupacion":"Comercio"}


def _fila(uuid="u-1", hogar="Nuclear"):
    return ({"uuid":uuid, "household_type":hogar, "municipality":"San Salvador"}, "Ana", 34, "F")


def test_enriquece_sin_modificar_los_campos_existentes():
    original = _persona()
    resultado = enriquecer([original], [_fila()])
    assert resultado[0] == {**original, "uuid":"u-1", "hogar":"nuclear"}
    assert original == _persona()


def test_enriquecer_archivo_aborta_sin_escribir_si_no_coincide(tmp_path: Path):
    path = tmp_path / "personas.json"
    original = [_persona()]
    contenido = json.dumps(original, ensure_ascii=False)
    path.write_text(contenido, encoding="utf-8")
    fila_mala = ({"uuid":"u-1", "household_type":"Nuclear", "municipality":"Santa Tecla"}, "Ana", 34, "F")
    with pytest.raises(ValueError, match="no se escribió"):
        enriquecer_archivo(path, [fila_mala])
    assert path.read_text(encoding="utf-8") == contenido
