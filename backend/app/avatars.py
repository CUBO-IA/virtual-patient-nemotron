"""Generación de URLs de avatares coherentes con sexo y edad del paciente."""

import urllib.parse


def avatar_url(persona: dict) -> str:
    """Genera una URL de avatar en Dicebear avataaars que respeta estrictamente

    el sexo y el rango etario del paciente para evitar incoherencias visuales
    (ej. mujeres con barba, ancianos con cabello juvenil sin canas, etc.).
    """
    edad = int(persona.get("edad", 30))
    sexo = persona.get("sexo", "M").upper()
    nombre = persona.get("nombre", "")
    pid = persona.get("id", "")
    seed = f"{pid}_{nombre}"

    params: list[tuple[str, str]] = [("seed", seed)]

    if sexo == "F":
        # Las pacientes femeninas nunca deben tener vello facial
        params.append(("facialHairProbability", "0"))

        if edad >= 60:
            # Adultas mayores: peinados clásicos, canas (blanco/plata) y lentes
            params.append(("top", "bun,bob,curly,bigHair,straight01"))
            params.append(("hairColor", "e8e1e1"))
            params.append(("accessories", "prescription01,prescription02,round"))
            params.append(("accessoriesProbability", "70"))
        elif edad >= 40:
            # Mujeres maduras: peinados variados, tonos oscuros o entrecanos
            params.append(("top", "bob,curly,curvy,straight01,straight02,bun"))
            params.append(("hairColor", "2c1b18,4a312c,724133"))
            params.append(("accessories", "prescription01,prescription02,round"))
            params.append(("accessoriesProbability", "35"))
        else:
            # Mujeres jóvenes (< 40)
            params.append(("top", "longButNotTooLong,miaWallace,straight01,straight02,curly,curvy"))
            params.append(("hairColor", "2c1b18,4a312c,724133"))
            params.append(("accessoriesProbability", "15"))
    else:
        # Pacientes masculinos
        if edad >= 60:
            # Adultos mayores: calvicie incipiente / cabello clásico canoso
            params.append(("top", "sides,shortFlat,shortRound,theCaesar,shortWaved"))
            params.append(("hairColor", "e8e1e1"))
            params.append(("facialHairColor", "e8e1e1"))
            params.append(("facialHair", "beardLight,moustacheMagnum,beardMedium"))
            params.append(("facialHairProbability", "40"))
            params.append(("accessories", "prescription01,prescription02,round"))
            params.append(("accessoriesProbability", "70"))
        elif edad >= 40:
            # Hombres maduros
            params.append(("top", "shortFlat,shortRound,shortWaved,theCaesar,theCaesarAndSidePart"))
            params.append(("hairColor", "2c1b18,4a312c,724133"))
            params.append(("facialHairColor", "2c1b18,4a312c,724133"))
            params.append(("facialHair", "beardLight,moustacheMagnum,beardMedium"))
            params.append(("facialHairProbability", "35"))
            params.append(("accessories", "prescription01,prescription02,round"))
            params.append(("accessoriesProbability", "30"))
        else:
            # Hombres jóvenes (< 40)
            params.append(("top", "shortCurly,shortFlat,shortRound,shortWaved,shavedSides"))
            params.append(("hairColor", "2c1b18,4a312c"))
            params.append(("facialHairProbability", "15"))
            params.append(("accessoriesProbability", "10"))

    query = urllib.parse.urlencode(params)
    return f"https://api.dicebear.com/9.x/avataaars/svg?{query}"
