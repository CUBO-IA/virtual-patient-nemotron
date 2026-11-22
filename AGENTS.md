# AGENTS.md — Paciente Virtual

Instrucciones permanentes para Codex. Lee este archivo completo antes de tocar código. La tarea concreta de cada sesión está en `PROMPT_CODEX.md`.

## 1. Qué es

Simulador de pacientes para estudiantes de medicina (hackathon, equipo de 2).
El estudiante entrevista por chat a un **paciente virtual salvadoreño** y al final recibe una evaluación con el diagnóstico real.

- Las personas salen de **nvidia/Nemotron-Personas-El-Salvador** (Hugging Face, CC BY 4.0).
- Los casos clínicos son **ficticios** (`data/casos.json`).
- El LLM corre **local y gratis** con Ollama (`qwen2.5:7b`, ~22 tok/s en la RTX 4050 de 6 GB). Sin APIs de pago.
- Todo el texto de la app y de los prompts va **en español**.
- Aviso obligatorio visible en la UI: *"Casos ficticios, solo para práctica educativa. No sustituye consejo ni diagnóstico médico."*

## 2. Estado actual

**Hecho y verificado:**
- Flujo completo Nuevo paciente → chat en streaming → "Ver paciente" → diagnóstico → evaluación; 150 personas generadas.
- 8 casos clínicos con contexto salvadoreño validados por `scripts/validate_casos.py` (pendientes de revisión médica por profesional).

**Pendiente:**
- Fase 2: RAG con Chroma en Docker para citar guías clínicas en la evaluación.
- Pruebas automáticas (pytest) y pulido.
- Revisión médica de los casos (la hace una persona, no Codex).

## 3. Arquitectura

```
React (Vite) :5173 ──/api (proxy)──► FastAPI :8000 ──► Ollama (HOST) :11434
                                         │
                                         └─(fase 2)──► Chroma (Docker) :8001
```

- **El diagnóstico nunca sale al cliente hasta `/finish`.** Casos y sesiones viven en el backend (memoria).
- **Solo el backend habla con Ollama.** Vite hace proxy de `/api` a `:8000`, no hay CORS que configurar en desarrollo.
- **Ollama corre en el host**, no en Docker (usa la GPU). Un contenedor lo alcanza en `http://host.docker.internal:11434`; si no conecta, arrancar Ollama con `OLLAMA_HOST=0.0.0.0`.
- **RAG nunca alimenta al paciente** (filtraría el diagnóstico). Solo se usa en la evaluación/feedback.
- **La app debe funcionar sin Docker ni RAG.** Si Chroma cae, se degrada sin citas.

## 4. Estructura real del repo

```
ai_in_action/
├─ AGENTS.md · PROMPT_CODEX.md · .env.example · .gitignore
├─ data/
│  ├─ personas.json            # generado por scripts/build_personas.py (150 adultos)
│  ├─ casos.json               # 3 casos hoy; meta: 8
│  └─ guias/                   # (fase 2) documentos para RAG
├─ scripts/
│  └─ build_personas.py        # dataset HF (streaming) -> personas.json
├─ backend/
│  ├─ requirements.txt
│  └─ app/
│     ├─ main.py               # rutas FastAPI + SSE
│     ├─ config.py             # env (.env en la raíz) y constantes
│     ├─ models.py             # ChatIn, FinishIn
│     ├─ sessions.py           # sesiones en memoria, lock con timeout
│     ├─ assign.py             # sorteo caso + persona compatible
│     ├─ prompts.py            # prompt del paciente y del feedback
│     ├─ llm.py                # cliente Ollama (stream_chat, chat_once, health)
│     └─ evaluate.py           # keywords + diagnóstico + feedback
└─ frontend/                   # Vite + React
   └─ src/ api.js · App.jsx · styles.css · components/{Chat,PatientCard,Results,Disclaimer}.jsx
```

El entorno virtual de Python está en `.venv/` (raíz). Python 3.13, Node 26.

## 5. Contratos de datos

### `data/personas.json` (generado; no editar a mano)
Campos reales: `id, nombre, edad, sexo ("F"|"M"), ocupacion, departamento, municipio, area, nivel_educativo, estado_civil, uuid, hogar, estilo` (`uuid` y `hogar` se añaden desde el dataset con `scripts/enriquecer_personas.py`).
El dataset **no trae nombre**: el primer nombre se extrae del texto de las columnas `*_persona`. `ocupacion` es una rama de actividad (p. ej. "Cultivo de hortalizas y melones…"), no un cargo.

### `data/casos.json` (lista de casos)
Campos obligatorios por caso:

| Campo | Contenido |
|---|---|
| `id` | `c_<tema>_NN` |
| `motivo_consulta` | frase del paciente, sin nombrar la enfermedad |
| `sintomas`, `antecedentes`, `habitos` | listas de texto en lenguaje llano |
| `datos_si_pregunta` | `{ tema: respuesta }`; solo se revelan si el estudiante pregunta |
| `restricciones` | `sexo[]`, `edad_min`, `edad_max`; opcionales `departamentos_tipicos[]`, `ocupaciones_tipicas[]` (prefijos en minúscula que se buscan en `ocupacion`) |
| `diagnostico` | nombre oficial |
| `diagnostico_alias` | variantes aceptadas (se comparan por palabra completa) |
| `lista_verificacion` | `[{id, texto, keywords[]}]`, `texto` en forma neutral ("Duración de la fiebre") |
| `banderas_rojas` | `[{id, texto, keywords[]}]`, señales de alarma |

Reglas de los casos: clínicamente simples y correctos; **nunca** poner el nombre del diagnóstico en `motivo_consulta`, `sintomas`, `antecedentes`, `habitos` ni `datos_si_pregunta`; keywords sin tildes ni mayúsculas, se comparan como **prefijo de palabra** (`"viaj"` detecta "viajó"); cuidado con prefijos que coinciden con palabras no relacionadas.

### API

| Método | Ruta | Cuerpo | Respuesta |
|---|---|---|---|
| GET | `/api/health` | — | `{ok, ollama, modelo, modelo_disponible, personas, casos, datos}` (+ `rag` en fase 2) |
| POST | `/api/sessions` | — | `{session_id, paciente:{nombre,edad,sexo,ocupacion,departamento,municipio,estado_civil,nivel_educativo,hogar,avatar_url}, motivo_consulta}` |
| POST | `/api/sessions/{id}/chat` | `{message}` | SSE: `data: {"token": "…"}`, `data: {"done": true}` o `event: error` |
| POST | `/api/sessions/{id}/finish` | `{diagnostico_estudiante}` | `{diagnostico_real, diagnostico_correcto, puntaje, cumplidos[], faltantes[], banderas[{id,texto,cumplida}], feedback, citas[{fuente,fragmento}]}` |

Códigos: 404 sesión inexistente, 409 sesión ocupada o terminada, 422 mensaje vacío, 503 faltan datos.
**Nunca** devolver `diagnostico`, `lista_verificacion`, `datos_si_pregunta` ni `banderas_rojas` antes de `/finish`.

### Puntaje
`puntaje = round(60 × fracción_checklist + 30 × diagnóstico_correcto + 10 × fracción_banderas)`.

## 6. Prompt del paciente (`prompts.py`)

Recibe la persona y lo que el paciente sabe de sí mismo; **jamás** el diagnóstico ni la lista de verificación. Reglas ya validadas que no se deben aflojar: motivo primero y síntomas poco a poco, 2-4 frases cortas con algo de emoción y muletillas propias de cada persona (sin inventar síntomas), sin términos médicos ni nombres de enfermedades, sin placeholders, no salir del personaje. Parámetros: `temperature 0.7`, `num_predict 180`, `num_ctx` desde `NUM_CTX` (2048 por defecto), últimos 12 mensajes de historial (peor caso medido: prompt con síntoma del turno, 12 mensajes largos y 180 tokens de respuesta ≈1920 de 2048; una consulta normal usa ≈1100).

## 7. RAG con Docker (fase 2)

Propósito: que el feedback cite guías clínicas reales. No toca el prompt del paciente.

- `docker-compose.yml` con servicio `chroma` (`chromadb/chroma`, puerto host 8001, volumen persistente). El backend sigue corriendo fuera de Docker en desarrollo.
- `scripts/ingest_guias.py`: lee `data/guias/*.md|*.txt|*.pdf`, parte en chunks (~500-800 tokens, solape ~80), embeddings con Ollama `bge-m3`, guarda en la colección `guias` con metadatos `{fuente, enfermedad, pagina}`. El nombre del archivo (sin extensión) es el `guia_ref` del caso.
- `backend/app/rag.py`: consulta top-k (3-4) filtrando por `enfermedad == caso["guia_ref"]`; devuelve `[{fuente, fragmento}]`.
- `evaluate.py`: con `RAG_ENABLED=true` pasa los fragmentos al prompt del feedback y rellena `citas`. Si Chroma o el embedding fallan, **continúa sin citas** y `/api/health` reporta `rag: false`.
- Solo documentos públicos o de licencia abierta (MINSAL, OPS/OMS). **No inventar contenido de guías ni copiar material con derechos.** Si no hay documentos, el ingest termina con mensaje claro, no con error.

## 8. Comandos

```powershell
# Ejecución completa (todo en uno)
.\iniciar.bat

# Backend (desde la raíz)
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --port 8000 --reload

# Frontend
cd frontend; npm install; npm run dev          # http://localhost:5173

# Datos
.\.venv\Scripts\python.exe scripts\build_personas.py 150

# Modelo (Ollama ya instalado)
ollama pull qwen2.5:7b
ollama pull bge-m3                              # solo fase 2

# Fase 2
docker compose up -d chroma
.\.venv\Scripts\python.exe scripts\ingest_guias.py
```

Variables en `.env` (ver `.env.example`): `OLLAMA_URL, LLM_MODEL, EMBED_MODEL, CHROMA_URL, RAG_ENABLED, NUM_CTX`.

## 9. Reglas para Codex

- Cambios pequeños y verificables; ejecuta lo que escribes (backend, tests, build del frontend) y reporta qué probaste y qué no.
- No cambies el contrato de la API ni el esquema de `casos.json` sin actualizar este archivo en el mismo cambio.
- No expongas campos ocultos antes de `/finish`. Hay (o debe haber) una prueba que lo verifique.
- No aflojes las reglas del prompt del paciente.
- Maneja errores explícitamente (Ollama caído, Chroma caído, archivo faltante) con mensajes claros; no los silencies.
- Estado compartido: las sesiones son por `session_id`; sin variables globales mutables para el chat.
- Sin secretos en el código; todo por `.env`. No toques `.env` real ni `data/personas.json` a mano.
- No añadas dependencias ni servicios fuera de este documento sin justificarlo en el resumen final.
- Texto de interfaz y prompts en español.
- Al terminar, no hagas commit salvo que se pida; el repo aún no usa git.

## 10. Definición de terminado

**Casos:** 8 casos que pasan el validador, con al menos 4 de contexto salvadoreño, ninguno nombra su diagnóstico fuera de `diagnostico`/`alias`.
**Tests:** `pytest` pasa; incluye prueba de que `/api/sessions` y `/chat` no exponen campos ocultos.
**RAG (si se hace):** con Chroma arriba y al menos 1 documento ingerido, `/finish` devuelve `citas`; con Chroma caído, devuelve lo mismo sin `citas` y sin error.
**UI:** el flujo completo sigue funcionando y el aviso de casos ficticios sigue visible.

## 11. Pruebas, plan y control (SEGUIMIENTO.md)

- Los módulos solo se activan si el caso tiene `revision_clinica.estado == "validado"` **con** `revisado_por`, `fecha` y `fuente` reales, o si el servidor corre con `SEGUIMIENTO_DEMO=true` (aviso visible de contenido sin validar).
- **Nunca marques un caso como `validado` ni inventes un revisor, una fecha o una fuente.** Todo el contenido clínico de pruebas, plan y evolución está hoy en `pendiente`: lo redactó una IA y nadie lo ha revisado. Solo una persona del área de la salud puede cambiar ese estado.
- El modelo no genera resultados de pruebas, medicamentos, dosis ni evolución: todo sale de `data/casos.json`, `data/catalogo_pruebas.json` y `data/formulario.json`. El modelo solo redacta la retroalimentación sobre listas ya calculadas.
- `niveles.json` tiene `pesos` (con módulos) y `pesos_sin_modulos` (clásicos). Los dos deben sumar 100.
- Endpoints nuevos: `GET /api/catalogo/pruebas`, `GET /api/catalogo/formulario`, `GET|POST /api/sessions/{id}/pruebas`; `POST /api/sessions/{id}/finish` acepta `plan`. Nada de `pertinencia`, `plan_esperado` ni `evolucion` sale al cliente antes de `/finish`.

## 12. Sesiones en disco

- Las sesiones viven en memoria **y** se guardan en `.sesiones/<id>.json` (`backend/app/sessions.py`), de modo que sobreviven a un reinicio del servidor. `sessions.get()` recupera del disco las que no están en memoria.
- Solo se guardan referencias (`caso_id`, `persona_id`) y el estado de la consulta; no se copia el contenido del caso. Guardar es de mejor esfuerzo: un fallo de escritura no rompe la petición.
- **Todo cambio de una sesión debe llamar a `sessions.guardar(s)`** (hoy: crear, chat, pista, pruebas, finish). Si añades un endpoint que modifica la sesión, guárdala también.
- Una pregunta sin respuesta (el reinicio interrumpió la petición) se descarta al restaurar.
- El sorteo normal reduce repeticiones excluyendo los dos casos más recientes del nivel cuando hay alternativas compatibles; si no quedan alternativas, conserva el sorteo normal. Un `caso_id` solicitado explícitamente siempre se respeta.
- Las pruebas usan una carpeta temporal (`conftest.py`); no escribas en `.sesiones/` desde los tests.
- `iniciar.bat` no usa `--reload`; `iniciar-dev.bat` sí (solo `backend/`).


## 13. Detección de preguntas

- `evaluate._hit(keywords, texto_normalizado)` es la **única** lógica de detección (guía de anamnesis, evaluación final y pistas). Compara por inicio de palabra, por raíz (sufijos, raíz ≥ 4 letras) y con contracciones `del→de`, `al→a`; claves de varias palabras deben coincidir consecutivas.
- `data/preguntas_ejemplo.json` es el banco de preguntas realistas (guía y los 8 casos), con `desarrollo` (para ajustar claves) y `reserva` (solo para medir, no copiar a las claves).
- Medir: `.\.venv\Scripts\python.exe scripts\medir_deteccion.py`. Umbrales (también en `backend/tests/test_deteccion.py`): desarrollo ≥ 95 %, reserva ≥ 80 %, cruces falsos ≤ 5 % por entidad.
- Al añadir o recortar claves: no incluir el diagnóstico ni sus alias, no usar palabras genéricas sueltas (`dolor`, `pecho`, `agua`…) si suben los cruces, y anotar en `CLAVES_RECORTADAS` (del test) las que se quiten.


## 13b. Habla del paciente

- Respuestas de 2-4 frases con reacción emocional breve; el primer mensaje es solo el motivo, en una frase. Cada persona tiene 3 **muletillas** estables (`habla.muletillas_para_persona`, semilla = id de la persona) que el prompt pide usar en menos de la mitad de las respuestas: sin esa instrucción el 7B las pegaba al final de todas. Cada muletilla lleva su uso entre paréntesis cuando se presta a mal uso («ni modo» = resignación ante algo inevitable). Dosificación: `system_paciente(..., turno)` (turno = respuestas previas del paciente, calculado en `mensajes_paciente`) separa el síntoma principal de «otros síntomas» (solo se confirman si preguntan por ellos) e indica **un único síntoma nuevo por turno** para las preguntas generales («¿algo más?»), empezando por los que el motivo no menciona. Una regla genérica de «poco a poco» no bastaba con el 7B. Medido en HTA: de 4+ síntomas por respuesta a 1-3; no es determinista. No uses esto con urgencias (allí los signos se muestran sin que los pidan). También exige **no repetir las palabras de la pregunta** (contestar directo). Son un borrador sin validar por hablantes nativos, igual que `data/habla_salvadorena.json`.
- **«j» de la aspiración:** en pantalla solo desde el nivel 2 (en el 1 dificulta la lectura; configurable con `texto_aspirado` en el nivel). La **voz** (TTS) siempre pronuncia con «j»: el `done` del chat trae `texto_voz` (aspirado) y el frontend lo guarda en `voz`. `texto_original` (sin «j») sigue en el `done`; el historial del modelo guarda el texto sin «j».
- Si añades reglas al prompt, mantén `MAX_CHARS_PROMPT` en `test_prompt_habla.py` (peor caso ≈1320 tokens de 2048).

## 14. «¿Por qué?» (explicaciones)

- `POST /api/sessions/{id}/explicar` con `{tipo: "prueba"|"medicamento"|"indicacion"|"disposicion", id}`. Solo tras `/finish` (409 antes). Devuelve `{tipo, id, titulo, valoracion, nota, explicacion, fuentes[{fuente,fragmento}], origen: "guia"|"ia"|"caso", modelo_no_disponible}`.
- Lógica en `backend/app/explicar.py`, en dos niveles:
  1. **Con guía** (`origen: "guia"`): si `RAG_ENABLED=true` y hay fragmentos relevantes, el modelo redacta **solo** a partir de ellos y cita `[n]`. Búsqueda híbrida: primero los fragmentos con términos propios de la decisión (hasta `RAG_MAX_DISTANCIA_LEXICA`, 780) y luego los cercanos (≤ `RAG_MAX_DISTANCIA`, 660; distancia L2 de Chroma con `bge-m3`, relevantes ~480-640, ajenos >700). Se descartan fragmentos de bibliografía y el prompt no incluye la nota del caso (el modelo no debe presentarla como cita).
  2. **Sin guía** (`origen: "ia"`): si el RAG está apagado, no hay fragmentos o el modelo responde `SIN_SUSTENTO`, el modelo **razona de forma general** (para qué sirve, por qué encaja con el diagnóstico según la valoración, alternativa o precaución). El prompt le prohíbe dosis y contradicciones y le pide ampliar, no repetir, la nota del caso; el nombre llega sin dosis (`sin_dosis`: «Enalapril 20 mg» → «Enalapril»). Es lo que hace útil el botón sin necesidad de guías: **no vuelvas a devolver solo la nota**, que el estudiante ya ve en la lista.
  3. `origen: "caso"` solo si el modelo no está disponible (`modelo_no_disponible: true`); la interfaz lo dice y ofrece reintentar.
- La explicación general sale del conocimiento del 7B, **sin validar**: se muestra siempre como «generada con IA como apoyo educativo, sin validar por un profesional». Medido con el 7B: razona bien el mecanismo y el porqué, pero puede ser impreciso en matices clínicos (p. ej. afirmar que conviene no medicar al inicio, o cómo actúa el reposo); no la presentes como recomendación médica.
- `/finish` añade ids opcionales (`pruebas.esenciales_faltantes_ids`, `plan.medicamentos_faltantes_ids`, `plan.indicaciones.faltantes_ids`) para pedir la explicación de lo que faltó.
- Los PDFs de `data/guias/` no se suben a git; fuentes y enlaces en `data/guias/README.md`. No inventes contenido de guías.
- **Rendimiento (6 GB de VRAM):** los embeddings de las consultas se piden con `num_gpu: 0` (`EMBED_EN_CPU=true`). Con `bge-m3` en la GPU, Ollama expulsaba a `qwen2.5:7b` y lo recargaba en la respuesta siguiente: cada par embedding+respuesta pasaba de ≈5 s a ≈17 s. No quites esa opción sin volver a medirlo (`ollama ps` debe mostrar ambos modelos cargados).
- Interfaz: `frontend/src/components/PorQue.jsx` (botón «¿Por qué?» en `Results.jsx`; «Pensando…» mientras responde, ~6-9 s con el 7B).

## 15. Modo urgencias (borrador)

- Datos en `data/urgencias.json` (5 casos: 3 rojos, 1 amarillo, 1 verde); misma estructura conversacional que `casos.json` más `caso_base`, `urgencia` y `revision_clinica`. Validación: `scripts/validate_urgencias.py` (estructura, ids de signos, alias del diagnóstico fuera de lo que dice el paciente, los tres niveles presentes).
- Lógica en `backend/app/urgencias.py` (carga, límites, datos públicos y `calcular_triaje`); `main.py` solo enruta. **No metas lógica de urgencias en `main.py`.** Cuidado con los imports locales: un `import json` dentro de una función hace local ese nombre en toda la función (rompió `sessions._cargar` una vez).
- Todo caso de urgencias debe permanecer `revision_clinica.estado: "pendiente"` hasta revisión real por personal de salud. El modo solo se ofrece con `SEGUIMIENTO_DEMO=true` o con casos `validado`; `GET /api/health` reporta `urgencias: true|false` y la interfaz oculta el modo si es `false`. Muestra aviso de contenido no validado.
- `POST /api/sessions` acepta `modo: "consulta"|"urgencias"`. En urgencias solo expone `tiempo_limite_seg`, `max_preguntas`, `preguntas_minimas_semaforo` y `acompanante: {relacion}`; nunca prioridad correcta, signos, acción ni explicación antes del triaje. `caso_id` inexistente → 404.
- `POST /api/sessions/{id}/triaje` acepta `{prioridad, accion}` (409 con menos preguntas de las mínimas o si ya se envió, 422 valores inválidos). Devuelve prioridad/acción correctas y elegidas, signos y preguntas esenciales como **texto**, `puntaje`, `desglose`, `aprobado`, `alerta_seguridad`, `explicacion`. El reloj y los límites (8 preguntas, 180 s, 2 pistas) se aplican en el servidor.
- Puntaje: prioridad 50 (exacta) / 25 (más urgente de lo necesario) / 0 (menos urgente); signos 30 (un caso sin signos activos, como el verde, los otorga completos); esenciales 10; rapidez 10; −5 por pista (máx. 2). Prioridad o acción menos urgente que la esperada → `alerta_seguridad` y `aprobado: false`. El modelo no decide nada de esto.
- El prompt de urgencias **se añade** al del paciente (`prompts.system_paciente`); no aflojes las reglas de `AGENTS.md` §6. Medido con `qwen2.5:7b` (30 respuestas): 0 fugas de la enfermedad o la prioridad, 1 respuesta de 13 palabras; el acompañante casi nunca responde por el paciente.
- Interfaz: `frontend/src/components/UrgenciasPanel.jsx` (cronómetro, chat, semáforo, acción, resultado).
- Aviso obligatorio en todas las pantallas: «Esto es una práctica con casos ficticios. En una emergencia real, llama a los servicios de emergencia de tu país.»
- Estas decisiones clínicas son borradores generados y no deben presentarse como recomendación médica. La activación real requiere revisión profesional completa.

## 16. Introducción (escena pixel art + diapositivas)

- Código en `frontend/src/intro/`: `Intro.jsx` (línea de tiempo), `Escena.jsx` (SVG de 160×90 «píxeles»), `PixelArt.jsx` + `sprites.js` (sprites descritos como texto: un carácter = un píxel), `Diapositivas.jsx` (portada + contenido), `musica.js` (música sintetizada con Web Audio: **sin archivos de audio ni derechos de autor**) e `intro.css`.
- Flujo: pantalla de inicio («Comenzar con música» / «Sin sonido» / «Saltar introducción», porque los navegadores no permiten sonar sin un clic) → escena nocturna (el estudiante lee, preocupado) → encuentra la app en su computadora → destello → dos diapositivas → la app.
- Se muestra al abrir la app una vez por sesión del navegador (`sessionStorage.pv_intro_vista`). `?intro=1` la fuerza, `?intro=0` la omite y el botón «Intro» de la cabecera la repite. Con `prefers-reduced-motion` salta directo a las diapositivas, sin animación.
- El silencio se recuerda en `localStorage.pv_intro_silencio`. Las dimensiones usan unidades de contenedor (`cqw/cqh`) para no depender de `vw`.
- Las diapositivas solo afirman lo que es cierto (modelo local con Ollama, 8 casos ficticios, contenido clínico sin validar). **Si cambias el producto, revisa el texto de `Diapositivas.jsx`.** La voz de los pacientes usa un servicio en internet (edge-tts), así que no digas «todo funciona sin conexión».

## 17. Retroalimentación generada

- `backend/app/texto.py` limpia Markdown, limita la longitud y evita cortar a media frase; `evaluate.py` reintenta una salida desviada y cae al feedback determinista si persiste.
- Las citas RAG siguen en la respuesta de `/finish`, pero no se incluyen en el prompt de retroalimentación: las guías se reservan para «¿Por qué?» para evitar que el feedback resuma capítulos en vez de describir el desempeño calculado.

## 18. Personajes ilustrados

- `PacienteAnimado.jsx` dibuja al paciente en 3 capas (base, ojos, boca) tomadas de `frontend/public/pacientes/capas/paciente_NN/`, con parpadeo y boca sincronizada con el audio (Web Audio `AnalyserNode`; `Chat.jsx` emite `pv-audio-play` / `pv-audio-stop` y guarda `window.__pvCurrentAudio`). Hay 10 personajes, elegidos por sexo y edad. Detalle en `ANIMACIONES.md` §5.
- **Movimiento solo en las capas, nunca en el marco** (`.paciente-stage`) y sin temblor ni resplandor rojo con el dolor. Precarga las 9 imágenes de cada personaje. Respaldos: imagen consolidada y luego iniciales.
- No dupliques las imágenes en otras carpetas (ya se quitaron ~44 MB de copias idénticas) ni subas archivos de trabajo (`scratch/` está en `.gitignore`). `avatar_url` (DiceBear) sigue en la API pero la interfaz ya no lo usa.
