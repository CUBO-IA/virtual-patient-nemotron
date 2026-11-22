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
Campos reales: `id, nombre, edad, sexo ("F"|"M"), ocupacion, departamento, municipio, area, nivel_educativo, estado_civil, estilo`.
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
| POST | `/api/sessions` | — | `{session_id, paciente:{nombre,edad,sexo,ocupacion,departamento,municipio,avatar_url}, motivo_consulta}` |
| POST | `/api/sessions/{id}/chat` | `{message}` | SSE: `data: {"token": "…"}`, `data: {"done": true}` o `event: error` |
| POST | `/api/sessions/{id}/finish` | `{diagnostico_estudiante}` | `{diagnostico_real, diagnostico_correcto, puntaje, cumplidos[], faltantes[], banderas[{id,texto,cumplida}], feedback, citas[{fuente,fragmento}]}` |

Códigos: 404 sesión inexistente, 409 sesión ocupada o terminada, 422 mensaje vacío, 503 faltan datos.
**Nunca** devolver `diagnostico`, `lista_verificacion`, `datos_si_pregunta` ni `banderas_rojas` antes de `/finish`.

### Puntaje
`puntaje = round(60 × fracción_checklist + 30 × diagnóstico_correcto + 10 × fracción_banderas)`.

## 6. Prompt del paciente (`prompts.py`)

Recibe la persona y lo que el paciente sabe de sí mismo; **jamás** el diagnóstico ni la lista de verificación. Reglas ya validadas que no se deben aflojar: motivo primero y síntomas poco a poco, 1-3 frases, sin términos médicos ni nombres de enfermedades, sin placeholders, no salir del personaje. Parámetros: `temperature 0.7`, `num_predict 120`, `num_ctx` desde `NUM_CTX` (2048 por defecto), últimos 16 mensajes de historial.

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
- Las pruebas usan una carpeta temporal (`conftest.py`); no escribas en `.sesiones/` desde los tests.
- `iniciar.bat` no usa `--reload`; `iniciar-dev.bat` sí (solo `backend/`).


## 13. Detección de preguntas

- `evaluate._hit(keywords, texto_normalizado)` es la **única** lógica de detección (guía de anamnesis, evaluación final y pistas). Compara por inicio de palabra, por raíz (sufijos, raíz ≥ 4 letras) y con contracciones `del→de`, `al→a`; claves de varias palabras deben coincidir consecutivas.
- `data/preguntas_ejemplo.json` es el banco de preguntas realistas (guía y los 8 casos), con `desarrollo` (para ajustar claves) y `reserva` (solo para medir, no copiar a las claves).
- Medir: `.\.venv\Scripts\python.exe scripts\medir_deteccion.py`. Umbrales (también en `backend/tests/test_deteccion.py`): desarrollo ≥ 95 %, reserva ≥ 80 %, cruces falsos ≤ 5 % por entidad.
- Al añadir o recortar claves: no incluir el diagnóstico ni sus alias, no usar palabras genéricas sueltas (`dolor`, `pecho`, `agua`…) si suben los cruces, y anotar en `CLAVES_RECORTADAS` (del test) las que se quiten.
