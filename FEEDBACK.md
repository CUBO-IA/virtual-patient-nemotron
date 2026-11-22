# Retroalimentación final: texto plano, corta y fiel a los datos

Instrucciones para un agente (Codex). Lee este archivo completo, además de `AGENTS.md`, antes de tocar código.

- **Problema:** en la pantalla de resultados, la «Retroalimentación» aparece como Markdown crudo (`###`, `####`, `**negritas**`, `---`, listas numeradas) y además es un **ensayo largo que se corta a mitad de frase** («…**Insulina Regular (Cristalina) y»). Habla de «tu análisis de la diabetes mellitus», «Definición y Clasificación», «Prediabetes», «Examen Físico»… cosas que el estudiante **nunca escribió**.
- **Objetivo:** 3 a 5 frases en **texto plano**, en segunda persona, que hablen solo de lo que el sistema ya calculó (diagnóstico, temas explorados y no explorados, pruebas, plan), sin formato Markdown, sin inventar contenido y sin cortarse.
- **Estado:** diagnosticado; nada implementado todavía.

---

## 1. Causas (en orden de importancia)

1. **El RAG inunda el prompt de la retroalimentación.** `evaluate.evaluar` hace `rag.consultar(guia_ref, f"{diagnostico} {dx_estudiante}")` y pasa los fragmentos a `prompts.user_feedback(..., citas=citas)`, que los pega enteros con la frase «Puedes citar estas guías…». Cada fragmento mide **hasta ~2.800 caracteres** (son trozos de la guía, no resúmenes) y entran hasta 3. Con `NUM_CTX=2048` eso ocupa casi todo el contexto, y el modelo (qwen2.5:7b) responde con **un resumen del capítulo de la guía** en vez de evaluar al estudiante. Por eso salen apartados como «Definición y clasificación» o «Detección temprana». Esto empezó cuando se activó `RAG_ENABLED=true`; con el RAG apagado no pasaba.
2. **El prompt no controla el formato.** `SYSTEM_FEEDBACK` pide «máximo 6 frases» pero no prohíbe Markdown ni listas, y el modelo imita el estilo de los fragmentos (que vienen con títulos y viñetas).
3. **Nada limpia ni valida la salida.** `evaluate.py` usa lo que devuelve `llm.chat_once` tal cual (con `num_predict=300`, así que se corta a mitad de frase) y el frontend lo pinta con `<p className="feedback">{r.feedback}</p>`.
4. **Mismo riesgo en «¿Por qué?»:** `explicar.py` también muestra la salida del modelo sin limpiar; un `**negrita**` aparecería crudo igual.

---

## 2. Qué hacer, por fases

Termina y verifica cada fase antes de pasar a la siguiente.

### Fase 1 — Sacar las guías del prompt de la retroalimentación

- En `evaluate.evaluar`, **no pases `citas` a `prompts.user_feedback`** (déjalo como `citas=None`, o quita el parámetro y su bloque en `prompts.py`).
- `citas` **sigue en la respuesta de `/finish`** (contrato API sin cambios): solo deja de alimentar al modelo. La retroalimentación trata del desempeño del estudiante; las guías se usan en el botón «¿Por qué?».
- Mantén la consulta al RAG solo si la interfaz usa `citas`; si no se muestra en ningún lado, puedes dejarla (no estorba) pero no la envíes al LLM.

### Fase 2 — Prompt que fija formato y alcance

Reescribe `SYSTEM_FEEDBACK` en `prompts.py` (en español) para que diga, como mínimo:

- «Escribe **solo texto plano**: sin títulos, sin viñetas, sin listas numeradas, sin negritas, sin líneas `---` ni símbolos de Markdown.»
- «Escribe **entre 3 y 5 frases**, en un solo párrafo (o dos como máximo), hablándole al estudiante de **tú**.»
- «Habla **únicamente** de los datos que se te dan abajo. **No expliques la enfermedad**, no resumas guías, no agregues temas que el estudiante no mencionó.»
- «Orden sugerido: 1) si el diagnóstico fue correcto; 2) lo que sí hizo bien; 3) lo más importante que le faltó; 4) un consejo concreto para la próxima vez.»
- Conserva las reglas existentes: no inventar datos clínicos, no recomendar medicamentos/dosis/pruebas que no estén en los datos, y las alertas de seguridad van primero.

En `user_feedback`, reemplaza el cierre «Escribe la retroalimentación para el estudiante.» por una instrucción que repita el formato («Responde en texto plano, 3 a 5 frases.»). Un 7B obedece mejor si el recordatorio está en el último mensaje.

Parámetros de la llamada: `temperature=0.2` (no 0, para no repetir exactamente el mismo texto) y `num_predict=220`.

### Fase 3 — Limpieza y validación de la salida (red de seguridad)

Crea `backend/app/texto.py` con una función pura `limpiar_texto_modelo(texto: str, max_chars: int = 700) -> str` que:

1. Quita Markdown: encabezados (`#`…), negritas/cursivas (`**`, `__`, `*`, `_` de énfasis), código (`` ` ``), reglas (`---`, `***`), citas (`>`), enlaces `[texto](url)` → `texto`.
2. Convierte viñetas y numeraciones iniciales de línea (`- `, `* `, `1. `) en frases separadas por espacio o salto de línea simple, sin dejar el símbolo.
3. Colapsa espacios y saltos repetidos; conserva como máximo **un salto de párrafo**.
4. Si supera `max_chars`, **corta en el último final de frase** (`.`, `!`, `?`) anterior al límite; si no hay ninguno, corta en la última palabra completa y añade `…`. **Nunca debe terminar a media palabra ni a media frase.**
5. Devuelve `""` si lo que queda tiene menos de ~20 caracteres.

En `evaluate.evaluar`:

- Pasa la respuesta del modelo por `limpiar_texto_modelo`.
- **Detector de desvío:** si el texto crudo tenía encabezados Markdown (`#`), más de ~900 caracteres o 3+ líneas de lista, considéralo desviado: **reintenta una vez** con el mismo prompt y `temperature=0`; si vuelve a desviarse, usa el **feedback determinista** que ya existe (`_feedback_base` + `_feedback_modulos`). No muestres texto desviado.
- Mantén intacta la regla actual: las alertas de seguridad (`_feedback_modulos(None, plan_pub)`) **van primero y no dependen del modelo**.

Aplica la misma función a la salida de `explicar.py` (`explicacion`), con `max_chars=900`.

### Fase 4 — Interfaz

- En `Results.jsx`, muestra el feedback con saltos de párrafo respetados: `<p className="feedback">` con `white-space: pre-line` (estilo en `.feedback` de `styles.css`). **No agregues una librería de Markdown** (`AGENTS.md` §9: sin dependencias nuevas): el backend ya entrega texto plano.
- `PorQue.jsx`: igual (`white-space: pre-line` en el párrafo de la explicación).
- No cambies el aviso de casos ficticios ni el resto de la pantalla.

### Fase 5 — Pruebas

En `backend/tests/test_feedback.py` (sin Ollama, con `chat_once` simulado):

- `limpiar_texto_modelo` con la salida del bug (copia un fragmento real: `### Retroalimentación… #### Aspectos Correctos 1. **Definición…** --- ####…`): el resultado no contiene `#`, `*`, `---`, ni empieza con un título.
- Un texto largo se corta en frase completa (termina en `.`, `!` o `?`) y `len ≤ max_chars`.
- Un texto sin signos de puntuación se corta en palabra completa y termina en `…`.
- `evaluar` **no envía fragmentos de guía** al modelo: con `RAG_ENABLED=true` y `rag.consultar` simulado devolviendo un texto reconocible, ese texto **no** aparece en los mensajes que recibe `chat_once`; `citas` sí sigue en la respuesta.
- Si el modelo devuelve Markdown largo dos veces, `feedback` es el determinista (contiene «El diagnóstico real era» o «Diagnóstico correcto»).
- La alerta de seguridad sigue yendo primero aunque el modelo devuelva Markdown (prueba existente `test_la_alerta_aparece_en_el_feedback_aunque_el_modelo_la_ignore`: debe seguir pasando).
- `explicar`: una `explicacion` con `**negrita**` sale sin asteriscos.
- La suite completa (`pytest backend\tests -q`) y `npm run build` siguen pasando.

### Fase 6 — Verificación con el modelo real

Con Ollama, Chroma y `RAG_ENABLED=true` (el escenario del bug), haz **10 evaluaciones** repartidas en los casos con guía (`c_dm2_01`, `c_nac_01`, `c_erc_01`, `c_gea_01`, `c_hta_01`, `c_depresion_01`) con diagnósticos correctos e incorrectos y con/sin plan. Reporta una tabla con, por respuesta: caracteres, número de frases, si contiene símbolos Markdown (debe ser **0 de 10**), si termina en puntuación (**10 de 10**) y si habla de temas ajenos a los datos (revisión manual; debe ser **0**). Guarda el script en la carpeta temporal, no en el repo.

---

## 3. Reglas

- **No cambies el contrato de la API:** `feedback` sigue siendo un `string` y `citas` sigue en `/finish`.
- **No cambies el puntaje**, ni los niveles, ni las reglas del prompt del paciente.
- **Sin dependencias nuevas.** El Markdown se **elimina**, no se renderiza.
- **No inventes contenido clínico** en el feedback determinista ni en los prompts.
- No toques `.env` ni `data/personas.json`. Sin commit.
- Todo texto de interfaz y prompts en español.
- Si algo de este documento contradice `AGENTS.md`, sigue `AGENTS.md` y avísalo.

---

## 4. Criterios de aceptación

- [ ] La retroalimentación nunca muestra `#`, `**`, `---` ni viñetas, ni en los resultados ni en «¿Por qué?».
- [ ] Mide entre ~150 y 700 caracteres y **nunca termina a media frase**.
- [ ] Con `RAG_ENABLED=true` el prompt de la retroalimentación **no contiene fragmentos de guía**; `citas` sigue llegando en `/finish`.
- [ ] Habla solo de datos calculados (diagnóstico, temas, pruebas, plan); no describe la enfermedad.
- [ ] Ante una salida desviada del modelo se usa el feedback determinista, y las alertas de seguridad siguen primero.
- [ ] `pytest backend\tests -q`, `scripts\validate_casos.py` y `npm run build` pasan.
- [ ] `AGENTS.md` tiene una nota breve (qué hace `texto.py`, que las guías no van al prompt de la retroalimentación y por qué).

---

## 5. Qué entregar

Un resumen corto con: qué cambiaste por fase y en qué archivos; la tabla de la fase 6 (10 evaluaciones); y qué no pudiste verificar. Si decides cambiar algún valor de este documento (por ejemplo, `max_chars`), explica por qué.
