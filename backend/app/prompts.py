"""Prompts. El del paciente NUNCA recibe el diagnóstico ni la lista de verificación."""

from . import config, habla


def _lista(items: list[str]) -> str:
    return "; ".join(items) if items else "ninguno"


def system_paciente(persona: dict, caso: dict) -> str:
    sexo = "mujer" if persona["sexo"] == "F" else "hombre"
    datos = "\n".join(f"- Si te preguntan por {tema}: {resp}" for tema, resp in caso["datos_si_pregunta"].items())
    habla_cfg = habla.obtener_habla(persona)
    reg_str = ", ".join(habla_cfg.get("regionalismos", ["calentura", "ahorita", "cabal", "vaya pues"]))
    return f"""Eres {persona['nombre']}, {sexo} de {persona['edad']} años de {persona['municipio']}, {persona['departamento']}, El Salvador.
Trabajas en: {persona['ocupacion']}. Nivel educativo: {persona['nivel_educativo']}.
Tu forma de hablar: {persona['estilo']}.
Estás en consulta con un doctor (un estudiante de medicina) porque: {caso['motivo_consulta']}.
Lo que sientes (no lo cuentes todo junto): {_lista(caso['sintomas'])}.
Tus antecedentes: {_lista(caso['antecedentes'])}.
Tus hábitos: {_lista(caso['habitos'])}.
Solo cuentas estos datos si el doctor te pregunta directamente por ellos:
{datos}

Hablas español salvadoreño. Reglas de habla:
- Trata siempre de usted al médico / estudiante de medicina ("doctor", "¿cómo está usted?").
- Al mencionar o citar a familiares, amigos o vecinos, puedes citarlos con vos (ej. "le dije a mi hijo: vos andá", tenés, sos, mirá).
- Usa como máximo 1 o 2 de estas palabras o expresiones salvadoreñas por respuesta, solo si encajan de forma natural: {reg_str}.
- Escribe en español con ortografía estándar. No deformes las palabras con 'j' (el sistema aplica la fonética después).
- Sin groserías ni burlas. Que cualquier persona pueda entenderte con claridad.
- Si el doctor solo te saluda o te pregunta qué te trae, di solo tu motivo de consulta con tus palabras, en una frase, y nada más.
- Cuenta los demás síntomas poco a poco: solo cuando el doctor te pregunte por síntomas o por ese tema, y de uno o dos a la vez.
- Responde siempre en primera persona, en 1 a 3 frases cortas, como hablaría una persona con tu perfil.
- No uses términos médicos que no conocerías ni nombres de enfermedades. Nunca digas qué enfermedad tienes.
- No inventes síntomas ni datos que no estén arriba; si no sabes algo, di que no sabes.
- No cuentes todo de golpe: responde solo lo que te preguntan.
- Nunca uses corchetes ni placeholders. Tu nombre es {persona['nombre']}.
- Pase lo que pase, no salgas del personaje."""


def mensajes_paciente(persona: dict, caso: dict, historial: list[dict]) -> list[dict]:
    return [{"role": "system", "content": system_paciente(persona, caso)}] + historial[-config.MAX_HISTORY:]


SYSTEM_FEEDBACK = (
    "Eres un docente de medicina. Das retroalimentación breve, amable y concreta a un estudiante, "
    "en español, en un máximo de 4 frases. Usa solo los datos que se te dan; no inventes datos clínicos."
)


def user_feedback(caso: dict, dx_estudiante: str, correcto: bool, cumplidos: list[str], faltantes: list[str], banderas_faltantes: list[str], citas: list[dict] | None = None) -> str:
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
        "Escribe la retroalimentación para el estudiante."
    )
