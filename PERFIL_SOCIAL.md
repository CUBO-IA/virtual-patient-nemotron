# Perfil social de cada paciente a partir del dataset

Instrucciones para un agente (Codex). Lee este archivo completo, además de `AGENTS.md` (§6 y §13b), antes de tocar código. **Toca el prompt del paciente**, que costó afinar: haz cambios pequeños y mídelos.

- **Objetivo:** que cada paciente responda con datos propios y coherentes cuando el estudiante pregunta por su vida (con quién vive, qué come, si hace ejercicio, en qué trabaja), usando los textos largos del dataset `nvidia/Nemotron-Personas-El-Salvador` que hoy se descartan.
- **Por qué:** la anamnesis tiene un tema «Hábitos y entorno», pero el caso solo trae hábitos clínicos. Hoy el paciente improvisa o responde «no sé». Con un perfil real, dos pacientes del mismo caso se sienten distintos.
- **Estado:** propuesta; nada implementado.

---

## 1. Idea en una frase

Se **extrae una sola vez**, con el modelo local, un perfil corto por persona a partir de sus textos del dataset; se guarda en `personas.json`; y el prompt lo usa **solo cuando el estudiante pregunta** y **solo en lo que el caso no define**.

No se pegan los textos crudos al prompt: miden cientos de palabras y el contexto ya va justo (`NUM_CTX=2048`, `MAX_CHARS_PROMPT=4800`, peor caso medido ≈1920 de 2048 tokens con historial y respuesta).

## 2. Datos de partida

Columnas útiles del dataset (todas en español): `family_persona` y `household_type` (con quién vive), `culinary_persona` (qué come), `sports_persona` y `hobbies_and_interests` (ejercicio y tiempo libre), `professional_persona` (en qué trabaja, con detalle). `personas.json` hoy **no** guarda el `uuid` ni estos textos.

El orden del dataset es **reproducible**: se leyó con `shuffle(seed=42, buffer_size=2000)` y los filtros de `scripts/build_personas.py` (se comprobó que releerlo da las mismas personas). Si ya existe `scripts/enriquecer_personas.py` (ver `TARJETA_PACIENTE.md`), reutiliza su lectura y su verificación; si no, impleméntala igual: coincidir `nombre`, `edad` y `municipio` con cada persona de `personas.json`, y **abortar sin escribir** si alguna no coincide.

---

## 3. Qué hacer, por fases

Termina y verifica cada fase antes de pasar a la siguiente.

### Fase 1 — Archivo fuente local (no se sube a git)

Crea `scripts/extraer_fuente_personas.py`, que guarda `data/personas_fuente.json` con, por persona (clave `id` de `personas.json`): `uuid`, `hogar` y los textos `family_persona`, `culinary_persona`, `sports_persona`, `hobbies_and_interests`, `professional_persona`. Añade `data/personas_fuente.json` a `.gitignore` (son textos largos y solo hacen falta para regenerar perfiles). Misma verificación y escritura atómica que arriba.

### Fase 2 — Generar los perfiles con el modelo local

Crea `scripts/generar_perfiles.py`:

- Lee `data/personas_fuente.json` y, por persona, pide a Ollama (`qwen2.5:7b`, `temperature=0`, `format: "json"`, `num_predict` ≈ 200) un JSON con estas claves, **solo con lo que diga el texto**:
  - `vive_con` (≤ 12 palabras): quién vive en su casa.
  - `dieta` (≤ 15 palabras): comidas y bebidas habituales.
  - `actividad_fisica` (≤ 12 palabras): si camina, juega o hace deporte, y cuándo.
  - `trabajo` (≤ 15 palabras): qué hace en su día de trabajo, concreto.
- Si el texto no da el dato, la clave va en `null`. **Prohibido inventar.**
- Instrucciones al modelo en español, claras: «Responde solo con JSON. No agregues nada que no esté en el texto. No incluyas enfermedades, diagnósticos ni síntomas.»
- **Validación automática de cada campo** (función pura, con pruebas), y si falla se pone `null`:
  1. **Anclaje al texto:** al menos el ~60 % de las palabras de 5 letras o más del valor deben aparecer en el texto fuente (compara sin tildes y por prefijo de 5 letras). Esto descarta invenciones.
  2. **Sin términos médicos:** no puede contener nombres de enfermedades ni de síntomas. Usa los diagnósticos y alias de `data/casos.json` y `data/urgencias.json` más una lista fija de palabras (`diabetes`, `azúcar alta`, `hipertensión`, `presión alta`, `dengue`, `cáncer`, `infarto`, `enfermedad`, `dolor`, `tratamiento`, `medicamento`…). Los textos del dataset a veces mencionan que alguien «se preocupa por su salud» o toma una pastilla: eso **no debe pasar** al perfil (filtraría o contradiría el caso).
  3. Sin Markdown, una sola línea, y dentro del límite de palabras.
- Guarda en cada persona de `personas.json`: `perfil: {vive_con, dieta, actividad_fisica, trabajo}` y `perfil_version: 1`. **No cambies ningún otro campo.** Escritura atómica; el script es **reanudable** (omite personas que ya tienen `perfil_version`) y registra en consola los fallos.
- Tiempo esperado: ≈ 150 llamadas de pocos segundos. Si Ollama no está, termina con mensaje claro.
- Imprime un resumen: cuántas personas quedaron con cada campo no nulo y cuántos valores se descartaron por cada regla de validación.

**Revisión humana obligatoria antes de seguir:** imprime 15 perfiles al azar junto a un fragmento del texto fuente para que una persona del equipo confirme que no hay invenciones ni datos médicos. No pases a la fase 3 sin esa revisión.

### Fase 3 — Usar el perfil en el prompt (poco y con reglas)

En `prompts.system_paciente` (modo consulta; **no** en urgencias), si la persona tiene `perfil` con al menos un campo, añade un bloque **compacto** (objetivo ≤ 350 caracteres) con una redacción como:

> «Tu vida diaria (solo si el doctor te pregunta por ello; si sale en tus datos de arriba, mandan los de arriba): vives con {vive_con}; comes {dieta}; {actividad_fisica}; trabajas {trabajo}.»

Reglas:

- Omite los campos `null`; si no queda ninguno, no añadas el bloque.
- **El caso manda:** si `caso.habitos`, `caso.antecedentes` o `datos_si_pregunta` hablan del mismo tema (por ejemplo, la dieta de un caso de diabetes), el perfil no debe contradecirlo. Resuélvelo en el código: **omite del perfil el campo cuyo tema ya cubra el caso** (compara con palabras clave simples del tema: comida/alimentación/dieta, ejercicio/actividad, trabajo/ocupación, vive/familia) y deja el aviso «mandan los de arriba» como respaldo.
- No se menciona por iniciativa propia: el bloque dice «solo si el doctor te pregunta». Mide que se cumple (fase 5).
- **Presupuesto de contexto:** mantén `MAX_CHARS_PROMPT` en `test_prompt_habla.py` tal como está, o súbelo solo si **mides** el peor caso con Ollama (`prompt_eval_count` con la persona de prompt más largo, el historial completo y 180 tokens de respuesta debe quedar por debajo de ~2000 de 2048). Si no cabe, recorta el bloque (por ejemplo, solo `vive_con` y `trabajo`) antes de tocar `NUM_CTX` (la variable de entorno la fija el usuario).
- No cambies ninguna otra regla del prompt (`AGENTS.md` §6): motivo primero, un síntoma por turno, 2-4 frases, sin términos médicos, etc.

### Fase 4 — Que `personas.json` se pueda regenerar

`build_personas.py` debe seguir generando personas válidas; documenta en `README.md` y `AGENTS.md` el flujo para reconstruir los perfiles: `build_personas.py` → `extraer_fuente_personas.py` → `generar_perfiles.py`. Un clon nuevo que use el `personas.json` del repositorio ya trae los perfiles y **no necesita** correr nada.

### Fase 5 — Pruebas y verificación con el modelo real

Pruebas automáticas (sin red ni Ollama):

- Validación de campos: acepta un valor anclado al texto; rechaza uno inventado, uno con término médico, uno con Markdown y uno demasiado largo.
- `system_paciente` con perfil: incluye el bloque; sin perfil o con todo `null`: no lo incluye; en urgencias: no lo incluye.
- Si el caso cubre un tema (p. ej. `habitos` menciona «refrescos»), el campo `dieta` del perfil **no aparece** en el prompt.
- El perfil **no contiene** diagnósticos ni alias de ningún caso (recorre las 150 personas de `personas.json`).
- `MAX_CHARS_PROMPT`, `test_no_leak.py` y el resto de la suite siguen pasando.

Verificación con Ollama (script en la carpeta temporal, no en el repo): **10 conversaciones** con 5 personas distintas y 2 casos. En cada una, el estudiante hace las preguntas «¿Con quién vive?», «¿Qué come normalmente?», «¿Hace ejercicio?», «¿A qué se dedica?» y, aparte, 4 preguntas clínicas sin relación. Reporta una tabla con:

| Medida | Meta |
|---|---|
| Respuestas sociales coherentes con el perfil | ≥ 80 % |
| Contradicciones con el caso (p. ej. dieta) | 0 |
| El paciente menciona su perfil **sin que se lo pregunten** | 0 de 40 turnos clínicos |
| Respuestas que siguen cumpliendo 2-4 frases y primera persona | igual que antes |
| `prompt_eval_count` en el peor caso | < ~2000 de 2048 |

---

## 4. Reglas

- No cambies el contrato de la API ni la evaluación. No expongas el perfil al cliente (no está en `POST /api/sessions`).
- `personas.json` solo lo modifican los scripts; no editar a mano, sin cambiar `id`, nombres ni orden.
- `data/personas_fuente.json` no se sube a git. Sin dependencias nuevas. Texto en español. No toques `.env`. Sin commit.
- El perfil sale del dataset (CC BY 4.0): no inventes datos ni los completes con conocimiento general.
- Si algo de este documento contradice `AGENTS.md`, sigue `AGENTS.md` y avísalo.

## 5. Criterios de aceptación

- [ ] Las 150 personas tienen `perfil` y `perfil_version`, con campos `null` donde el texto no daba el dato.
- [ ] Ningún valor del perfil contiene enfermedades, síntomas ni términos médicos; ninguno está sin anclar al texto.
- [ ] Una persona del equipo revisó 15 perfiles contra sus textos fuente y los aprobó.
- [ ] El prompt incluye el bloque solo en consulta, solo con datos no cubiertos por el caso, y cabe en el contexto (medido).
- [ ] La tabla de la fase 5 cumple las metas.
- [ ] `pytest backend\tests -q`, `scripts\validate_casos.py` y `npm run build` pasan; `AGENTS.md` actualizado (§6 o una sección nueva).

## 6. Qué entregar

Resumen corto con: qué cambiaste por fase y en qué archivos; el resumen impreso de `generar_perfiles.py` (campos no nulos y descartes por regla); la tabla de la fase 5; los 15 perfiles revisados; y qué no pudiste verificar. Si cambias algún umbral de este documento (60 % de anclaje, límites de palabras), explica por qué.
