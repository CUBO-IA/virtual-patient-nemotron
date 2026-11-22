import json

from scripts.generar_perfiles import DATA, FIELDS, _medicos, normalizar, validar_campo, validar_perfil
from scripts.extraer_fuente_personas import crear_fuente


MEDICOS = {"diabetes", "dolor", "pastillas"}


def test_validacion_acepta_valor_anclado():
    valor, regla = validar_campo("vive con su madre", "Vive con su madre en la casa familiar", 12, MEDICOS)
    assert valor == "vive con su madre" and regla is None


def test_validacion_rechaza_inventado_medico_markdown_y_largo():
    fuente = "Vive en casa con su familia y sus hermanos."
    assert validar_campo("vive en una finca lejana", fuente, 12, MEDICOS)[1] == "anclaje"
    assert validar_campo("toma pastillas", "toma pastillas todos los días", 12, MEDICOS)[1] == "medico"
    assert validar_campo("**vive con familia**", fuente, 12, MEDICOS)[1] == "markdown"
    assert validar_campo("vive con madre padre hermanos primos sobrinos vecinos compañeros", fuente, 5, MEDICOS)[1] == "longitud"


def test_validar_perfil_anula_solo_el_campo_invalido():
    perfil = {"vive_con":"vive con su madre", "dieta":"comidas inventadas", "actividad_fisica":None, "trabajo":"trabaja en comercio"}
    textos = {"family_persona":"vive con su madre", "household_type":None, "culinary_persona":"", "sports_persona":"", "hobbies_and_interests":"", "professional_persona":"trabaja en comercio"}
    validado, descartes = validar_perfil(perfil, textos, set())
    assert validado == {"vive_con":"vive con su madre", "dieta":None, "actividad_fisica":None, "trabajo":"trabaja en comercio"}
    assert descartes["anclaje"] == 1


def test_extraer_fuente_compara_identidad_y_crea_registro_por_id():
    persona = {"id":"p_001", "nombre":"Ana", "edad":30, "municipio":"San Salvador"}
    row = {"uuid":"abc", "household_type":"Nuclear", "municipality":"San Salvador", "family_persona":"texto"}
    fuente = crear_fuente([persona], [(row, "Ana", 30, "F")])
    assert fuente["p_001"]["uuid"] == "abc" and fuente["p_001"]["hogar"] == "nuclear"
    assert fuente["p_001"]["family_persona"] == "texto"


def test_todas_las_personas_tienen_perfil_v1_sin_diagnosticos_ni_aliases():
    personas = json.loads((DATA / "personas.json").read_text(encoding="utf-8"))
    terminos = _medicos()
    assert len(personas) == 150
    for persona in personas:
        assert persona["perfil_version"] == 1
        assert set(persona["perfil"]) == set(FIELDS)
        for valor in persona["perfil"].values():
            if valor is None:
                continue
            texto = f" {normalizar(valor)} "
            assert not any(f" {termino} " in texto for termino in terminos), (persona["id"], valor)
