"""Prompts. El del paciente NUNCA recibe el diagnóstico ni la lista de verificación."""

import re

from . import config, habla


def _lista(items: list[str]) -> str:
    return "; ".join(items) if items else "ninguno"


_TEMAS_PERFIL = {
    "vive_con": ("hogar", "vive con", "viven con", "vive solo", "vive sola", "viviendo solo", "viviendo sola", "vivienda", "convive"),
    "dieta": ("comida", "aliment", "dieta", "comer", "come", "bebida", "refresco", "cafe", "pupusa", "alcohol"),
    "actividad_fisica": ("ejercicio", "actividad", "camina", "caminar", "corre", "correr", "deporte", "futbol", "bicicleta"),
    "trabajo": ("trabajo", "trabaja", "trabajar", "ocupacion", "empleo", "empleado", "negocio", "oficio", "repart", "pedido", "entreg", "transporte"),
}
_TEMAS_PREGUNTA = {
    "vive_con": ("con quien vive", "vive con", "convive", "hogar", "familia"),
    "dieta": ("comida", "aliment", "dieta", "comer", "come", "bebida", "refresco"),
    "actividad_fisica": ("ejercicio", "actividad", "camina", "caminar", "corre", "correr", "deporte", "futbol", "bicicleta"),
    "trabajo": ("trabajo", "trabaja", "trabajar", "ocupacion", "empleo", "dedica", "oficio", "negocio"),
}
_ETIQUETAS_PERFIL = {
    "vive_con": "casa",
    "dieta": "come",
    "actividad_fisica": "actividad",
    "trabajo": "trabajo",
}
_MAX_CARACTERES_PERFIL = 350


def _texto_cubre_tema(texto: str, claves: tuple[str, ...]) -> bool:
    normalizado = habla._norm(texto)
    return any(re.search(rf"\b{re.escape(clave)}\w*\b", normalizado) for clave in claves)


def _texto_social_caso(caso: dict) -> str:
    datos = []
    for campo in ("habitos", "antecedentes", "datos_si_pregunta"):
        valor = caso.get(campo, [])
        if isinstance(valor, dict):
            datos.extend(str(parte) for item in valor.items() for parte in item)
        elif isinstance(valor, (list, tuple)):
            datos.extend(str(parte) for parte in valor)
        else:
            datos.append(str(valor))
    return " ".join(datos)


def _campo_cubierto_por_caso(caso: dict, campo: str) -> bool:
    return _texto_cubre_tema(_texto_social_caso(caso), _TEMAS_PERFIL[campo])


def _fragmentos_tema_caso(caso: dict, campo: str) -> list[str]:
    fragmentos = []
    for campo_caso in ("habitos", "antecedentes", "datos_si_pregunta"):
        valor = caso.get(campo_caso, [])
        if isinstance(valor, dict):
            candidatos = [f"{tema}: {respuesta}" for tema, respuesta in valor.items()]
        elif isinstance(valor, (list, tuple)):
            candidatos = [str(item) for item in valor]
        else:
            candidatos = [str(valor)]
        fragmentos.extend(item for item in candidatos if item and _texto_cubre_tema(item, _TEMAS_PERFIL[campo]))
    return fragmentos


def _campos_perfil_preguntados(pregunta: str) -> tuple[str, ...]:
    campos = tuple(campo for campo, claves in _TEMAS_PREGUNTA.items() if _texto_cubre_tema(pregunta, claves))
    if _texto_cubre_tema(pregunta, ("rutina",)):
        if _texto_cubre_tema(pregunta, ("ejercicio", "actividad", "deporte", "caminar", "futbol")):
            return ("actividad_fisica",)
        return ("trabajo",)
    return campos


def _frase_laboral(valor: str) -> str:
    """Convierte los resúmenes laborales más comunes en una frase breve y natural."""
    texto = valor.strip().rstrip(".")
    bajo = texto.lower()
    if bajo.startswith("tiendita de "):
        return f"Tengo una {texto}."
    if bajo.startswith("tienda ") or bajo.startswith("tienda de "):
        return f"Trabajo en una {texto}."
    if bajo.startswith("taller de "):
        return f"Trabajo en un {texto}."
    if bajo.startswith("oficina de "):
        return f"Trabajo en la {texto}."
    if bajo.startswith("gestión de "):
        return f"Me ocupo de la {texto}."
    if bajo.startswith("venta al "):
        return f"Me dedico a la {texto}."
    if bajo.startswith(("empleadora de ", "propietaria de ", "encargado de ", "encargada de ")):
        return f"Soy {texto}."
    if bajo.startswith(("asistente de ", "auxiliar de ", "docente de ", "supervisor de ", "supervisora de ", "conductor de ", "conductora de ", "operadora de ", "peón en ", "jornalero en ")):
        return f"Trabajo como {texto}."
    if bajo.startswith("cultivo de "):
        return f"Me dedico al {texto}."
    if bajo.startswith("actividades de "):
        return f"Me dedico a {texto}."
    if bajo.startswith("trabajando en "):
        lugar = texto[len("trabajando en "):].rstrip(".")
        return f"Trabajo en {lugar}."
    if bajo.startswith("panadería"):
        return "Trabajo en una panadería."
    return f"Mi trabajo es {texto}."


def _instruccion_perfil_social(pregunta: str | None, persona: dict, caso: dict) -> str:
    if not pregunta:
        return ""
    campos = _campos_perfil_preguntados(pregunta)
    if not campos:
        return ""
    perfil = persona.get("perfil")
    campos_perfil = tuple(
        campo for campo in campos
        if isinstance(perfil, dict) and perfil.get(campo) and not _campo_cubierto_por_caso(caso, campo)
    )
    if not campos_perfil:
        cubiertos = tuple(campo for campo in campos if _campo_cubierto_por_caso(caso, campo))
        if cubiertos:
            tema = cubiertos[0]
            fragmentos = _fragmentos_tema_caso(caso, tema)
            if fragmentos:
                return f"Para { _ETIQUETAS_PERFIL[tema] }, usa solo este dato del caso: «{'; '.join(fragmentos)}». No inventes más detalles."
            return f"El caso ya define {_ETIQUETAS_PERFIL[tema]}; responde solo con lo que aparece ahí y no inventes otros datos."
        if "trabajo" in campos and persona.get("ocupacion"):
            return f"Responde exactamente: «Mi ocupación es {persona['ocupacion']}. No le sabría decir más de mi trabajo, doctor»."
        temas = ", ".join(_ETIQUETAS_PERFIL[campo] for campo in campos)
        return f"No hay datos de {temas} en este caso ni en tu perfil; di que no lo sabes y no inventes."
    campos = campos_perfil
    if "trabajo" in campos:
        frase = _frase_laboral(str(perfil["trabajo"]))
        segundo = "mi rutina" if _texto_cubre_tema(pregunta, ("rutina",)) else "mi trabajo"
        return (
            f"Responde exactamente con estas dos frases: «{frase} "
            f"No le sabría decir más de {segundo}, doctor». No agregues detalles ausentes ni síntomas."
        )
    etiquetas = ", ".join(_ETIQUETAS_PERFIL[campo] for campo in campos)
    valores = "; ".join(str(perfil[campo]) for campo in campos if perfil.get(campo))
    return f"Responde la pregunta social sobre {etiquetas} usando solo estos datos: «{valores}». No completes información ausente ni repitas síntomas."


def _bloque_perfil_social(persona: dict, caso: dict, pregunta: str | None = None) -> str:
    """Incluye datos sociales solo si el caso no cubre ya ese tema."""
    perfil = persona.get("perfil")
    if not isinstance(perfil, dict):
        return ""

    texto_caso = _texto_social_caso(caso)
    campos_preguntados = _campos_perfil_preguntados(pregunta) if pregunta else ()
    if pregunta and not campos_preguntados:
        return ""
    partes = {}
    for campo, etiqueta in _ETIQUETAS_PERFIL.items():
        if campos_preguntados and campo not in campos_preguntados:
            continue
        valor = perfil.get(campo)
        if not isinstance(valor, str) or not valor.strip():
            continue
        if _texto_cubre_tema(texto_caso, _TEMAS_PERFIL[campo]):
            continue
        partes[campo] = f"{etiqueta}: {valor.strip()}"

    if not partes:
        return ""
    prefijo = "Solo si preguntan; manda el caso: "
    sufijo = " No inventes otros datos."
    prioridad = ("vive_con", "trabajo", "dieta", "actividad_fisica")
    incluidas = []
    for campo in prioridad:
        if campo not in partes:
            continue
        prueba = [*incluidas, partes[campo]]
        if len(prefijo + "; ".join(prueba) + sufijo) <= _MAX_CARACTERES_PERFIL:
            incluidas = prueba
    if not incluidas:
        return ""
    # El orden de lectura sigue siendo hogar, alimentación, actividad y trabajo.
    orden = ("vive_con", "dieta", "actividad_fisica", "trabajo")
    seleccionadas = [partes[campo] for campo in orden if campo in partes and partes[campo] in incluidas]
    return prefijo + "; ".join(seleccionadas) + sufijo


def system_paciente(persona: dict, caso: dict, nivel: dict | None = None, turno: int = 0, pregunta_actual: str | None = None) -> str:
    sexo = "mujer" if persona["sexo"] == "F" else "hombre"
    datos = "\n".join(f"- Si te preguntan por {tema}: {resp}" for tema, resp in caso["datos_si_pregunta"].items())
    expresiones = habla.expresiones_para_caso(caso)
    expresiones_line = ""
    if expresiones:
        expresiones_line = (
            "- Si te sale natural, usa alguna de estas expresiones (una por respuesta, sin forzarlas): "
            + ", ".join(f"«{e}»" for e in expresiones) + ".\n"
        )

    muletillas = habla.muletillas_para_persona(persona)
    muletillas_line = (
        "- Tus muletillas: " + ", ".join(f"«{m}»" for m in muletillas)
        + "; úsalas solo de vez en cuando (en menos de la mitad de tus respuestas), nunca al final de todas.\n"
    )

    actitud_line = ""
    if nivel:
        actitud = nivel.get("actitud_paciente", "normal")
        if actitud == "colaborador":
            actitud_line = "Actitud: Eres colaborador/a: cuando el doctor te pregunta por un tema, respondes con claridad y das el dato completo de ese tema. No adelantes otros temas.\n"
        elif actitud == "reservado":
            actitud_line = "Actitud: Eres reservado/a y de pocas palabras: respondes lo mínimo. Si la pregunta es vaga o muy general, respondes algo impreciso («pues… ahí voy», «no sabría decirle») y solo das el detalle cuando el doctor pregunta de forma concreta. No cambies los hechos ni inventes datos.\n"

    # Información dosificada: el prompt solo indica UN síntoma nuevo por turno; los demás solo se confirman
    # si el doctor pregunta por ellos. (El 7B no obedece una regla genérica de «cuéntalo poco a poco».)
    sintomas = list(caso["sintomas"])
    if caso.get("urgencia") or len(sintomas) < 2:
        lo_que_sientes = f"Lo que sientes: {_lista(sintomas)}."
        siguiente_line = ""
    else:
        motivo = habla._norm(caso["motivo_consulta"])
        ya_dicho = lambda t: any(w[:5] in motivo for w in habla._norm(t).split() if len(w) >= 5)
        resto = sintomas[1:]
        resto = [t for t in resto if not ya_dicho(t)] + [t for t in resto if ya_dicho(t)]  # primero lo que el motivo aún no dijo
        lo_que_sientes = (
            f"Lo que sientes: {sintomas[0]}.\n"
            f"Otros síntomas (solo los confirmas si el doctor te pregunta por ellos concretamente; nunca los nombras tú): {_lista(resto)}."
        )
        i = turno - 1
        siguiente = f"añade solo este síntoma: «{resto[i]}»" if 0 <= i < len(resto) else "di que por ahora es eso, sin añadir síntomas"
        siguiente_line = f" Solo si la pregunta es general («¿algo más?», «¿cómo se siente?»), {siguiente}; en cualquier otra, responde solo lo que preguntan."

    urg = caso.get("urgencia")
    bloque_urgencias = ""
    bloque_perfil = "" if urg else _bloque_perfil_social(persona, caso, pregunta_actual)
    if urg:
        nombres = [b["texto"] for b in caso.get("banderas_rojas", []) if b["id"] in urg.get("signos_activos", [])]
        acomp = urg.get("acompanante", {})
        bloque_urgencias = ("\n\nEstás en urgencias y te sientes mal. Esto reemplaza la regla de largo de arriba: cada respuesta tiene máximo 12 palabras en total: una frase corta, sin explicar de más. En la primera respuesta di solo lo principal que sientes. "
            "Se nota tu malestar: pausas, quejidos y poca paciencia. "
            + (f"Tu {acomp.get('relacion')} te acompaña y a veces responde por ti. " if acomp.get("tiene") else "")
            + "Muestra sin que te lo pidan: " + _lista(nombres) + ". "
            + "Solo dices esto si te preguntan directamente: " + _lista(urg.get("datos_ocultos", [])) + ". "
            "Nunca digas qué enfermedad crees tener ni qué tan grave es.")

    return f"""Eres {persona['nombre']}, {sexo} de {persona['edad']} años de {persona['municipio']}, {persona['departamento']}, El Salvador.
Tu rama de actividad es: {persona['ocupacion']}. Nivel educativo: {persona['nivel_educativo']}.
{bloque_perfil}
Tu forma de hablar: {persona['estilo']}.
Estás en consulta con un doctor (un estudiante de medicina) porque: {caso['motivo_consulta']}.
{lo_que_sientes}
Tus antecedentes: {_lista(caso['antecedentes'])}.
Tus hábitos: {_lista(caso['habitos'])}.
Solo cuentas estos datos si el doctor te pregunta directamente por ellos:
{datos}

{actitud_line}Hablas español salvadoreño. Reglas de habla:
- Habla SIEMPRE en primera persona («tengo», «me duele»). Si los datos de arriba están en tercera persona («le duele»), pásalos a primera. Nunca hables de ti en tercera persona.
- Trata de usted al médico ("doctor"); vos solo si citas lo que le dijiste a un familiar.
- Habla como una persona común de El Salvador, con palabras sencillas; nada de términos médicos ni formales («deposiciones», «heces», «cefalea»): di «diarrea», «ir al baño», «dolor de cabeza». Empieza con «Vengo por» + el síntoma (ej.: «Vengo por una tos fuerte»), no «Me trae…».
{expresiones_line}{muletillas_line}- «Ahorita» es solo «ahora mismo»; para lo pasado: «ayer», «anoche».
- Nombra a tus familiares como aquí («mi esposo», «mi mamá») y solo si están en tus datos.
- Escribe con ortografía estándar; no deformes palabras con 'j' (el sistema aplica la fonética). Sin groserías ni burlas.
- Cuenta UN solo síntoma por respuesta, el que te preguntan.{siguiente_line} Si el doctor solo te saluda o te pregunta qué te trae, di solo tu motivo en una frase, sin otros síntomas.
- Responde en 2 a 4 frases cortas, como una persona con tu perfil. No repitas las palabras de la pregunta: contesta directo con el dato (si te preguntan en qué parte te duele: «Aquí atrás, donde empieza el cuello», no «En la parte de atrás de la nuca»). Reacciona un poco (preocupación, cansancio) sin inventar síntomas ni hechos.
- Nunca digas qué enfermedad tienes ni nombres de enfermedades.
- No inventes síntomas ni datos que no estén arriba; si no sabes algo, di que no sabes.
- Nunca uses corchetes ni placeholders. Tu nombre es {persona['nombre']}. Pase lo que pase, no salgas del personaje.
{bloque_urgencias}"""


def mensajes_paciente(persona: dict, caso: dict, historial: list[dict], nivel: dict | None = None) -> list[dict]:
    turno = sum(1 for m in historial if m.get("role") == "assistant")  # respuestas que ya dio el paciente
    pregunta = next((m.get("content") for m in reversed(historial) if m.get("role") == "user"), None)
    mensajes = [{"role": "system", "content": system_paciente(persona, caso, nivel, turno, pregunta)}] + historial[-config.MAX_HISTORY:]
    instruccion = "" if caso.get("urgencia") else _instruccion_perfil_social(pregunta, persona, caso)
    if instruccion and mensajes and mensajes[-1].get("role") == "user":
        # La instrucción queda junto a la pregunta actual para que el 7B la aplique a este turno.
        largo_system = sum(len(m["content"]) for m in mensajes if m["role"] == "system")
        if largo_system + len(instruccion) <= 4800:
            mensajes.insert(len(mensajes) - 1, {"role": "system", "content": instruccion})
    return mensajes


SYSTEM_FEEDBACK = (
    "Eres un docente que da retroalimentación breve, amable y concreta a un estudiante. "
    "Escribe solo texto plano: sin títulos, viñetas, listas numeradas, negritas, líneas --- ni símbolos de Markdown. "
    "Escribe entre 3 y 5 frases, en un solo párrafo o dos como máximo, hablándole al estudiante de tú. "
    "Habla únicamente de los datos calculados que se te dan abajo. No uses conocimiento médico general, "
    "no expliques la enfermedad, no resumas guías ni agregues afirmaciones sobre síntomas, riesgos o tratamientos. "
    "No agregues temas que el estudiante no mencionó. Orden sugerido: si el diagnóstico fue correcto; "
    "lo que sí hizo bien; lo más importante que le faltó; un consejo concreto para la próxima vez basado solo en lo que faltó. "
    "No inventes datos clínicos ni recomiendes medicamentos, dosis o pruebas que no estén en los datos. "
    "Si hay alertas de seguridad, menciónalas primero y con claridad."
)


def user_feedback(caso: dict, dx_estudiante: str, correcto: bool, cumplidos: list[str], faltantes: list[str], banderas_faltantes: list[str], citas: list[dict] | None = None, extra: str = "") -> str:
    citas_texto = ""
    if citas:
        lineas = [f"- [{c.get('fuente', 'Guía')}]: {c.get('fragmento', '')}" for c in citas]
        citas_texto = "\nFragmentos relevantes de guías clínicas:\n" + "\n".join(lineas) + "\nPuedes citar estas guías en la retroalimentación si es pertinente.\n"

    return (
        f"Diagnóstico real: {caso['diagnostico']}.\n"
        f"Diagnóstico del estudiante: {dx_estudiante} ({'correcto' if correcto else 'incorrecto o incompleto'}).\n"
        f"Temas que sí exploró: {_lista(cumplidos)}.\n"
        f"Temas que no exploró: {_lista(faltantes)}.\n"
        f"Banderas rojas que no exploró: {_lista(banderas_faltantes)}.\n"
        f"{citas_texto}"
        + (f"{extra}\n" if extra else "")
        + "Responde en texto plano, entre 3 y 5 frases. No agregues conocimientos médicos ni consejos clínicos generales; el consejo final debe referirse solo a los temas que faltaron."
    )


SYSTEM_EXPLICAR = (
    "Eres un docente de medicina que explica a un estudiante, en español y en un máximo de 4 frases, "
    "por qué una decisión clínica fue adecuada o no. Usa EXCLUSIVAMENTE los fragmentos de guías numerados que se te dan "
    "y cita el número entre corchetes, por ejemplo [1]. No inventes datos, dosis ni recomendaciones que no estén en los fragmentos. "
    "La valoración del sistema NO es una fuente: no la cites ni la repitas; solo indica qué decisión se evalúa. "
    "Solo afirma lo que un fragmento diga de forma explícita sobre esta decisión (el medicamento, la prueba o la indicación concreta). "
    "Si los fragmentos no hablan de esta decisión, responde exactamente: SIN_SUSTENTO"
)


def user_explicar(diagnostico: str, titulo: str, veredicto: str | None, nota: str | None, fragmentos: list[str]) -> str:
    partes = [f"Diagnóstico del caso: {diagnostico}", f"Decisión a explicar: {titulo}"]
    if veredicto:
        partes.append(f"Valoración del sistema: {veredicto}")
    partes.append("Fragmentos de guías:")
    partes += [f"[{i}] {f}" for i, f in enumerate(fragmentos, 1)]
    partes.append("Explica en qué se apoya esta decisión según los fragmentos.")
    return "\n".join(partes)


SYSTEM_EXPLICAR_GENERAL = (
    "Eres un docente de medicina que explica a un estudiante, en español claro y en 4 a 6 frases, el razonamiento detrás de una "
    "decisión clínica en un caso ficticio. Explica: para qué sirve (su mecanismo o utilidad, en una frase), por qué encaja o no "
    "con este diagnóstico, y qué alternativa se preferiría o qué precaución hay que tener. Adapta la explicación a la valoración: "
    "si es «adecuado», por qué es lo recomendable; si es «aceptable», por qué sirve pero no es la primera opción; si es «innecesario» "
    "o «contraindicado», por qué no conviene. Reglas: no menciones dosis ni hables de subirlas o bajarlas, ni des cifras exactas; no te contradigas (no uses «sin embargo» para negar lo que acabas de explicar); no inventes datos del paciente; si algo depende "
    "del caso concreto, di «en general». La nota del caso ya la ve el estudiante: amplíala con razonamiento nuevo, no la repitas. "
    "Es material educativo, no una indicación para un paciente real."
)


def user_explicar_general(diagnostico: str, tipo: str, titulo: str, valoracion: str | None, nota: str | None) -> str:
    partes = [f"Diagnóstico del caso: {diagnostico}", f"Tipo de decisión: {tipo}", f"Decisión: {titulo}"]
    if valoracion:
        partes.append(f"Valoración en este caso: {valoracion}")
    if nota:
        partes.append(f"Nota del caso (ya la ve el estudiante): {nota}")
    partes.append("Explica el porqué de esta decisión.")
    return chr(10).join(partes)
