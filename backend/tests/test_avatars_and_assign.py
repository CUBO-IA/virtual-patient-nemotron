"""Pruebas para avatares coherentes (edad/sexo) y asignación semántica."""

import urllib.parse
from app.avatars import avatar_url
from app import assign


def test_avatar_mujer_sin_vello_facial():
    p_joven = {"id": "p_002", "nombre": "Tatiana", "edad": 22, "sexo": "F"}
    p_anciana = {"id": "p_001", "nombre": "Carolina", "edad": 67, "sexo": "F"}

    url_joven = avatar_url(p_joven)
    url_anciana = avatar_url(p_anciana)

    # Nunca debe haber probabilidad de vello facial en mujeres
    assert "facialHairProbability=0" in url_joven
    assert "facialHairProbability=0" in url_anciana

    # Anciana debe tener canas y lentes
    assert "hairColor=e8e1e1" in url_anciana
    assert "accessories=prescription01%2Cprescription02%2Cround" in url_anciana or "prescription" in url_anciana


def test_avatar_hombre_mayor_con_canas():
    p_anciano = {"id": "p_005", "nombre": "Manuel", "edad": 75, "sexo": "M"}
    url = avatar_url(p_anciano)

    assert "hairColor=e8e1e1" in url
    assert "facialHairColor=e8e1e1" in url
    assert "prescription" in url


def test_avatar_hombre_joven_sin_canas():
    p_joven = {"id": "p_003", "nombre": "Pablo", "edad": 20, "sexo": "M"}
    url = avatar_url(p_joven)

    # Pelo oscuro natural
    assert "hairColor=2c1b18%2C4a312c" in url or "2c1b18" in url
    # No cabello gris/blanco por defecto
    assert "hairColor=e8e1e1" not in url


def test_afinidad_semantica_y_asignacion_ponderada():
    # Persona agricultora rural expuesta a agroquímicos
    agricultor = {
        "id": "p_agric",
        "nombre": "José",
        "edad": 42,
        "sexo": "M",
        "ocupacion": "Cultivo de cereales y legumbres",
        "departamento": "Usulután",
        "area": "rural",
    }
    # Joven urbano repartidor en moto
    joven_moto = {
        "id": "p_moto",
        "nombre": "Carlos",
        "edad": 23,
        "sexo": "M",
        "ocupacion": "Transporte de mercancías y mensajería",
        "departamento": "San Salvador",
        "area": "urbano",
    }

    _, casos = assign._load()
    caso_erc = next(c for c in casos if c["id"] == "c_erc_01")
    caso_trauma = next(c for c in casos if c["id"] == "c_trauma_01")

    # El agricultor debe tener mayor peso/afinidad para ERC que para Trauma
    peso_agric_erc = assign.calcular_peso(agricultor, caso_erc)
    peso_agric_trauma = assign.calcular_peso(agricultor, caso_trauma)
    assert peso_agric_erc > 0
    assert assign.afinidad_semantica(agricultor, caso_erc) > assign.afinidad_semantica(agricultor, caso_trauma)

    # El joven repartidor tiene edad < 25 (edad_min de ERC es 25) -> Regla dura = 0
    assert assign.calcular_peso(joven_moto, caso_erc) == 0.0
    # Pero peso para trauma debe ser alto
    assert assign.calcular_peso(joven_moto, caso_trauma) > 0.0
