"""Script para enriquecer y afinar keywords en data/casos.json según DETECCION.md Fase 3."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASOS_PATH = ROOT / "data" / "casos.json"

# Reemplazos específicos de palabras aisladas excesivamente ambiguas por frases específicas
REEMPLAZOS = {
    "c_hta_01": {
        "cefalea_carac": {
            "dolor": "dolor de cabeza",
        },
        "dolor_toracico": {
            "pecho": "opresion en el pecho",
            "corazon": "ataque al corazon",
        },
    },
    "c_trauma_01": {
        "sensibilidad_motora": {
            "siente": "siente las piernas",
            "mover": "mover los dedos",
        },
    },
    "c_gea_01": {
        "vomitos_tolerancia": {
            "liquido": "tolerar liquidos",
        },
        "origen_alimentos": {
            "agua": "agua de chorro",
        },
    },
    "c_nac_01": {
        "dolor_pleuritico": {
            "pecho": "dolor en el pecho al respirar",
            "respira": "puntada al respirar",
            "toser": "puntada al toser",
        },
    },
}

ADICIONES = {
    "c_dengue_01": {
        "fiebre_dur": ["calentur", "temperatura", "escalofri", "termometr", "continua", "cuantos dias", "baja la fiebre", "subido la calentura"],
        "dolor_ojos": ["dolor de cabeza", "cabeza", "pesadez", "retroocular", "mover los ojos", "frente", "cuencas", "le duele la cabeza"],
        "dolor_musc": ["cuerpo cortado", "adolorid", "hueso", "coyuntur", "muscul", "articulac", "piernas y la espalda"],
        "contactos": ["trabajo o comunidad", "vecin", "alguien mas con calentura", "canton", "caserio", "hospital", "alguien cercano"],
        "zancudos": ["recipiente", "estancad", "pila", "criadero", "llantas o botellas", "fumig", "repelente", "mosquiter", "pican"],
        "viajes": ["costera", "oriental", "departamento", "interior", "paseo al campo", "playa", "fuera de su", "viaj"],
        "medicinas": ["inyect", "antiinflamat", "acetaminofen", "calmante", "farmacia", "bajar la fiebre", "pastilla"],
        "piel": ["lesion cutanea", "erupci", "roncha", "picazon", "enrojecim", "pecas de sangre", "brote", "sarpullid"],
        "sangrado": ["moret", "escupir", "lavarse", "sonarse", "cepillado", "manchas de sangre", "orina con sangre"],
        "dolor_abd": ["abdomen duro", "panza", "boca del estomago", "retortij", "vientre", "costillas", "presionarse", "doloroso"],
        "vomitos": ["constante", "seguido", "no le paran", "intenta tomar", "basca", "ultimas horas"],
    },
    "c_erc_01": {
        "orina": ["cambios en la orina", "color", "espum", "jabon", "te cargado", "inodoro", "chorro", "turbia"],
        "hinchazon": ["espinilla", "tobillo", "parpado", "pesad", "zapato", "hoyito", "retencion de liquidos", "manos"],
        "trabajo": ["agricola", "campo", "condiciones", "jornalero", "horas pasa", "esfuerzo fisico", "labora diariamente"],
        "agua_calor": ["cuanta agua", "toma agua", "deshidratacion frecuente", "jornada", "sofocad", "pachon", "botella", "milpa", "cuanto liquido"],
        "agroquimicos": ["veneno", "plaguicida", "fertilizante", "quimico", "fumig", "paraquat", "herbicida", "bomba de fumigar", "regando"],
        "aine": ["frecuentemente", "calmante", "analgesic", "pastillas para el dolor", "dolores musculares", "dorival", "voltaren", "pastillas de la tienda"],
        "familia": ["dialisis", "hemodialisis", "pariente", "muerto de los rinon", "danado"],
        "presion": ["tension arterial", "tension", "sabe en cuanto", "hipertension", "chequearon", "unidad de salud", "arriba de lo normal"],
        "diuresis": ["gotita", "drasticamente", "caido", "cuerpo retiene", "no hace pipi", "anuria", "dejo de orinar", "sin orinar casi nada", "casi nada", "retencion severa", "doce horas", "un poquito", "orina minima"],
    },
    "c_dm2_01": {
        "sed": ["todas horas", "no se le quita la sequedad", "sequedad en la boca", "desesperacion", "ganas excesivas", "garganta y boca", "pichel", "insaciable", "tomar agua", "resequedad en la garganta"],
        "orina": ["frecuencia al bano", "a cada rato", "gran cantidad", "pipi", "no aguanta", "vejiga"],
        "peso": ["bajado de peso", "perdido peso", "ropa", "floja", "adelgaz", "disminucion", "libras", "delgado"],
        "vision": ["dificultad para ver", "enfocar", "nublad", "cansancio para ver", "empanad", "claridad", "lentes", "neblina", "ver de lejos"],
        "familia": ["pariente", "metformina", "insulina", "historia familiar", "materna", "paterna", "abunda", "azucar"],
        "dieta": ["pan dulce", "tortilla", "gaseosa", "cafe con azucar", "desayuno y almuerzo", "carbohidrato", "soda", "fritura", "harina"],
        "actividad": ["actividad diaria", "tiempo sentado", "caminar", "trotar", "deporte", "rutina", "sedentaria", "media hora", "nivel de actividad"],
        "hormigueo": ["plantas de los pies", "agujas", "piquetes", "calambre", "sensibilidad en los pies", "entumec", "acorchad", "queman", "descalzo"],
        "heridas": ["llaga", "pie", "cicatric", "talon", "dedos", "infecc", "raspon", "semanas en cerrar", "pus", "espina"],
        "hiperglucemia": ["frutal", "manzana", "rapida y profunda", "desorientad", "frutas podridas", "somnolencia extrema", "atarantad", "desmayarse"],
    },
    "c_hta_01": {
        "cefalea_carac": ["en que parte", "detras del cuello", "late", "pulsa", "golpe", "aumento despacio", "trasera de la cabeza", "en las sienes", "mover el cuello", "dolor de cabeza"],
        "tinnitus_vision": ["pito", "silbido", "chispita", "luces", "manchas brillantes", "destello", "ruidos extranos", "retumban", "estrellitas", "agacha"],
        "adherencia": ["todos los dias", "dejo de tomar", "se le olvido", "dosis", "terminaron las pastillas", "irregular", "porque ya se sentia", "medicamento para la presion"],
        "dolor_pecho": ["pesadez en el pecho", "opresion en el medio", "zona del torax", "sube gradas", "aprieta el pecho", "angustia", "izquierdo del pecho"],
        "disnea": ["agarrar aire", "se fatiga", "se ahoga al caminar", "pocos pasos", "oxigeno al estar acostado", "cuesta", "almohadas", "sofoca"],
        "habitos_sal": ["comidas", "cargado", "estimulante", "tabaco", "plato antes de probar", "boquita", "fritura salada", "dia normal", "consome"],
        "antecedentes_fam": ["muerte subita", "cardiovascular", "infartos en su familia", "hermano suyo", "presion alta en su familia"],
        "dolor_toracico": ["pata de elefante", "irradia", "brazo izquierdo", "mandibula", "sudar frio", "quemante", "desgarrante", "faja", "veinte minutos", "opresion intensa", "esternon", "dura mas de 20 minutos"],
        "deficit_neuro": ["fuerza en un brazo", "pierna", "se le cae la saliva", "pronunciar palabras", "dormido o debil", "torpeza", "se le trabo", "lengua", "cayo un objeto", "mitad del cuerpo"],
        "dificultad_respiratoria": ["repentino", "plano", "sentarse al borde", "asfixiando", "quejido", "silbidos humedos", "mecedora", "espuma rosada", "aire a los pulmones"],
    },
    "c_trauma_01": {
        "mecanismo_lesion": ["accidente", "motocicleta", "automovil", "velocidad", "impacto", "atropellad", "derrapo", "pavimento", "expulsado", "de frente", "choque lateral", "volcado"],
        "uso_casco": ["abrochado", "solto", "quebro", "integral", "tipo bacinica", "chaleco", "rodilla", "reglamentario", "amortiguo", "zafo"],
        "perdida_conciencia": ["conocimiento", "inconsciente", "tras el golpe", "aturdido", "memoria", "amnesia", "borro la pelicula", "reaccionaba", "despertar", "recuerda todo", "paso durante el choque"],
        "dolor_toracico": ["costillas al respirar", "meter aire", "directo en el torax", "manubrio", "caja toracica", "timon", "costado derecho"],
        "dolor_cervical": ["nuca", "columna cervical", "latigazo", "espalda alta", "tragar", "vertebras", "tiron", "girar la cabeza"],
        "sensibilidad_motora": ["dedos de las manos", "hormigueo", "muslos", "apretar", "extremidades", "camilla", "cosquilleo", "falta de sensibilidad", "entumecimiento", "fuerza normal", "paralisis en las piernas"],
        "vacuna_tetanos": ["ultimos 5 anos", "esquema", "al dia", "abiertas", "refuerzo", "carne", "inyeccion del tetanos", "raspones anteriores", "antitoxina"],
        "trauma_craneal": ["proyectil", "liquido transparente", "pupilas", "convulsiones", "ataques", "insoportable", "donde vive", "ojos negros", "moretones alrededor", "desorientado o con somnolencia", "somnolencia anormal"],
        "compromiso_respiratorio": ["asfixia por el golpe", "hunden las costillas", "cuello al respirar", "dos palabras seguidas", "crujidos", "burbujas", "labios morados"],
        "hemorragia_activa": ["abierta que este sangrando", "vendaje", "empapado", "sangre fresca", "chorro", "palidez", "se desmaya por la sangre", "pierna o brazo", "sangrado activo", "no se detiene", "sigue saliendo", "sangre perdida"],
    },
    "c_gea_01": {
        "heces_frecuencia": ["cursera", "evacu", "suelto del estomago", "popo", "al bano", "sanitario", "taza del bano", "consistencia"],
        "sangre_moco": ["moquito", "coagulo", "gelatinosa", "papel", "hilachas", "mucosidad", "flema"],
        "vomitos_tolerancia": ["arroj", "le cae mal", "aguanta", "nausea", "basca", "saliva que traga", "amarillo", "verde", "bocado"],
        "signos_deshidratacion": ["reseca", "mareo", "mareado", "orin", "lengua como lija", "concentrada", "cabeza ligera", "lagrimas", "ojos hundidos", "sin saliva"],
        "origen_alimentos": ["mal estado", "almorz", "cen", "desayun", "que comio", "pupusa", "marisco", "mayonesa", "agua de chorro", "hervir", "guardados", "refrigeradora", "frescos"],
        "fiebre": ["caliente", "escalofri", "termometro", "calentura", "tacto en la frente", "sudoracion", "hirviendo", "chuchos de frio"],
        "tratamiento_previo": ["se ha tomado algo", "automedic", "toma algo", "se tomo algo", "sales de rehidratacion", "taparse", "farmacia", "manzanilla", "sobre de suero", "purgante"],
        "deshidratacion_severa": ["no puede sostenerse", "horas sin orinar", "agrietados", "pulso muy rapido", "piel fria", "fuerza completamente", "lengua completamente seca", "doce horas", "perdido el sentido", "somnoliento"],
        "intolerancia_oral": ["ni medio sorbo", "devuelve todo", "incoercibles", "en seco", "cucharadita de suero", "arqueandose", "cada trago"],
        "sangrado_heces": ["pura sangre fresca", "coagulos grandes", "ano", "rojo brillante", "hemorragia digestiva", "sangre viva", "sangrado rojo"],
    },
    "c_nac_01": {
        "tos_expectoracion": ["flema", "expectoraci", "gargajo", "pecho cargado", "dormir", "espesas", "pegajosas", "arrancar las flemas"],
        "fiebre_escalofrios": ["calentura fuerte", "temblores en los dientes", "sudando frio", "paños de agua", "quema la frente", "cobijas"],
        "dolor_pleuritico": ["costado al meter aire", "puntada", "punal", "meter aire", "paletilla", "espina clavada", "suspirar", "inhalar", "duele el torax"],
        "dificultad_respiratoria": ["falta de aire", "fatiga al dar", "descansando", "agitada", "silba el pecho", "tramo corto", "sofoco constante", "aire no le entra", "no entra suficiente aire"],
        "exposicion_humo": ["cocina con leña", "poyo", "quema de basura", "maleza", "vapores", "chimenea", "cuarto", "hacer tortillas"],
        "antecedentes_vacunas": ["neumonia", "gripe este ano", "defensas de los pulmones", "campaña de vacunacion", "vigentes", "carne de vacunacion"],
        "medicacion_previa": ["jarabes", "capsulas de antibiotico", "eucalipto", "remedios caseros para la tos", "automedico amoxicilina"],
        "insuficiencia_respiratoria": ["azul o morado", "desesperante que no le calma", "hunden las costillas", "jadeando", "oxigeno de forma critica", "sofocando"],
        "compromiso_conciencia": ["confuso", "desorientado", "mente perdida", "fecha estamos", "demasiado dormido", "incoherente", "desvarios", "atolondrado", "sin sentido"],
        "hemoptisis": ["flemas con sangre", "sangre viva en la tos", "hemoptoica", "panuelo", "franca del pecho", "sangrado pulmonar", "pura sangre liquida"],
    },
    "c_depresion_01": {
        "animo_tristeza": ["desanimado", "decaido", "ganas de llorar", "tristeza profunda", "llanto facil", "brillo o alegria", "llorando a solas", "pena o amargura"],
        "anhedonia": ["interes o placer", "nada le llama la atencion", "divierte", "pasatiempos", "indiferencia", "aficiones", "satisfaccion", "escuchar musica", "vida cotidiana", "alegria"],
        "alteracion_sueno": ["durmiendo", "insomnio", "madrugada", "pesadillas", "interrumpido", "dando vueltas", "3 de la manana", "reparador"],
        "apetito_peso": ["hambre", "obligacion", "bajado o subido", "desgano para probar", "holgada", "plato de comida", "insipida", "asco"],
        "energia_fatiga": ["fuerzas en el cuerpo", "agotado", "tareas mas sencillas", "pesadez en el cuerpo", "peso encima", "banarse o peinarse", "silla"],
        "red_apoyo": ["solo", "amigos", "confianza", "perdida de un ser querido", "duelo", "separacion", "divorcio", "tienda la mano", "desahogarse", "seres queridos", "en la casa"],
        "concentracion": ["concentrarse", "olvidan las cosas", "decisiones", "dispersa", "distrae", "leer varias veces", "mente nublada", "coordina", "decidir"],
        "ideacion_suicida": ["no vale la pena", "hacerse dano", "dormirse y no despertar", "suicidarse", "terminar con su sufrimiento", "planear alguna forma", "estaria mejor", "autolesionarse", "acabar con su vida"],
        "aislamiento_total": ["encerrado en su habitacion", "aislado por completo", "dejado de banarse", "cambiarse de ropa", "evita contestar", "aseo", "pijama sin asearse", "mundo exterior"],
    },
}


def main():
    # Primero restaurar casos limpios si se requiere o aplicar sobre casos limpios
    casos = json.loads(CASOS_PATH.read_text(encoding="utf-8"))

    for caso in casos:
        cid = caso["id"]
        reemplazos_caso = REEMPLAZOS.get(cid, {})
        adiciones_caso = ADICIONES.get(cid, {})

        for it in caso.get("lista_verificacion", []):
            iid = it["id"]
            if iid in reemplazos_caso:
                for viejo, nuevo in reemplazos_caso[iid].items():
                    it["keywords"] = [nuevo if k == viejo else k for k in it["keywords"]]
            if iid in adiciones_caso:
                for nueva in adiciones_caso[iid]:
                    if nueva not in it["keywords"]:
                        it["keywords"].append(nueva)

        for br in caso.get("banderas_rojas", []):
            bid = br["id"]
            if bid in reemplazos_caso:
                for viejo, nuevo in reemplazos_caso[bid].items():
                    br["keywords"] = [nuevo if k == viejo else k for k in br["keywords"]]
            if bid in adiciones_caso:
                for nueva in adiciones_caso[bid]:
                    if nueva not in br["keywords"]:
                        br["keywords"].append(nueva)

    CASOS_PATH.write_text(json.dumps(casos, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"OK: keywords enriquecidas y afinadas en {CASOS_PATH}")


if __name__ == "__main__":
    main()
