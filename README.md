# Paciente Virtual

Simulador de entrevistas clínicas para estudiantes de medicina. El estudiante conversa por chat (y escucha por voz) con un **paciente virtual salvadoreño**, descubre qué tiene, propone un diagnóstico y recibe una evaluación con el diagnóstico real.

> **Casos ficticios, solo para práctica educativa. No sustituye consejo ni diagnóstico médico.**

- Las personas salen de **Nemotron-Personas-El-Salvador** (NVIDIA): sexo, edad, ocupación, zona y nivel educativo reales de la distribución del país.
- El modelo de lenguaje corre **en tu computadora** con Ollama. No hay APIs de pago ni claves.
- Docker es **opcional**: solo se usa para el RAG de guías clínicas (citas en la evaluación).

## Qué hace

| Función | Detalle |
|---|---|
| 8 casos clínicos | Dengue, enfermedad renal crónica, diabetes tipo 2, crisis hipertensiva, trauma por accidente de tránsito, gastroenteritis, neumonía y depresión. |
| Paciente coherente | Cada caso se asigna a una persona compatible (sexo, edad, zona y ocupación típicas). Habla en español salvadoreño, trata de usted al doctor y no revela el diagnóstico. |
| Chat en streaming | El paciente responde en 1-3 frases y cuenta los síntomas poco a poco, solo si se le pregunta. |
| Voz | Voz salvadoreña (Lorena/Rodrigo) con tono y ritmo según la edad. |
| Avatar | "Ver paciente" muestra un avatar coherente con sexo y edad. |
| Pistas | Tres niveles de pista sin revelar el diagnóstico; cada una resta puntos. |
| Glosario | Términos médicos con ayuda emergente (35 términos). |
| Evaluación | Puntaje 0-100, diagnóstico real, qué preguntaste y qué faltó, señales de alarma y retroalimentación del modelo. |
| Pruebas, plan y control | Módulos opcionales: pides pruebas (hemograma, radiografía…), indicas un plan de tratamiento y ves cómo evoluciona el paciente a los N días. **Solo se activan en casos validados por un profesional de la salud** (ver más abajo). |
| RAG (opcional) | Con guías clínicas cargadas, la evaluación cita fragmentos de referencia. |

## Cómo funciona

```
Navegador ──► React (Vite) :5173 ──/api──► FastAPI :8000 ──► Ollama :11434   (modelo local, usa la GPU)
                                               │
                                               ├──► Chroma :8001  (Docker, opcional: guías clínicas)
                                               └──► Internet: voz (Edge TTS) y avatares (DiceBear)
```

- El **diagnóstico y las listas de verificación nunca salen del servidor** hasta que el estudiante pulsa «Ver evaluación».
- Solo el backend habla con Ollama y con Chroma.
- El RAG **no** alimenta al paciente (filtraría el diagnóstico); solo mejora la retroalimentación final.
- Si Chroma o la voz fallan, la app sigue funcionando sin citas o sin audio.

## Requisitos

| Qué | Para qué | Notas |
|---|---|---|
| Windows 10/11 | `iniciar.bat` | En otros sistemas, usa la ejecución manual. |
| Python 3.11+ | Backend | Marca «Add to PATH» al instalar. |
| Node.js 18+ | Frontend | |
| [Ollama](https://ollama.com) | Modelo local | `ollama pull qwen2.5:7b` (≈4,7 GB). |
| GPU NVIDIA (recomendada) | Velocidad | Con una RTX 4050 de 6 GB mide ≈22 tok/s. Sin GPU funciona, más lento. |
| Docker Desktop (opcional) | RAG con Chroma | Solo si quieres citas de guías. |
| Internet | Voz y avatares | Sin internet el chat funciona, pero no hay voz ni avatar. |

## Inicio rápido (Windows)

```powershell
git clone https://github.com/mariomarroquin3/virtual-patient.git
cd virtual-patient
ollama pull qwen2.5:7b
.\iniciar.bat
```

`iniciar.bat` (o `run.bat`) hace todo esto por ti:

1. Crea `.env` desde `.env.example` si no existe.
2. Crea `.venv` e instala las dependencias de Python (y las repara si una instalación se interrumpió).
3. Valida los 8 casos clínicos.
4. Instala las dependencias del frontend.
5. Arranca Ollama si no está corriendo y **avisa si falta el modelo**.
6. Si `RAG_ENABLED=true` en `.env`, levanta Chroma con Docker.
7. Abre el backend, el frontend y el navegador en <http://localhost:5173>.

> Las 150 personas ya vienen en el repositorio (`data/personas.json`); no hace falta descargar el dataset.

## Ejecución manual

```powershell
# Backend (:8000)
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --port 8000 --reload
```

```powershell
# Frontend (:5173), en otra terminal
cd frontend
npm install
npm run dev
```

## Configuración (`.env`)

| Variable | Por defecto | Qué hace |
|---|---|---|
| `OLLAMA_URL` | `http://localhost:11434` | Dónde está Ollama. |
| `LLM_MODEL` | `qwen2.5:7b` | Modelo del paciente y del feedback. `qwen2.5:3b` es más rápido. |
| `NUM_CTX` | `2048` | Contexto. Con 6 GB de VRAM, 2048 mantiene el modelo casi entero en GPU. |
| `RAG_ENABLED` | `false` | Activa las citas de guías clínicas. |
| `EMBED_MODEL` | `bge-m3` | Modelo de embeddings (solo RAG). |
| `CHROMA_URL` | `http://localhost:8001` | Dónde está Chroma (solo RAG). |
| `PENALIZACION_PISTA` | `0.5` | Puntos que resta cada pista. |
| `SEGUIMIENTO_DEMO` | `false` | Activa pruebas, plan y control aunque el caso **no** esté validado. Solo para demostraciones: la interfaz muestra «Contenido sin validar clínicamente». |
| `CORS_ORIGINS` | `http://localhost:5173` | Orígenes permitidos por el backend. |

## RAG con Docker (opcional)

Sirve para que la evaluación cite guías clínicas reales. Sin documentos en `data/guias/`, el RAG no devuelve citas.

```powershell
# 1. Modelo de embeddings (≈1,2 GB)
ollama pull bge-m3

# 2. Chroma en Docker (abre Docker Desktop antes)
docker compose up -d chroma

# 3. Coloca guías públicas o de licencia abierta en data/guias/
#    El nombre del archivo debe ser el guia_ref del caso: dengue.md, erc.pdf, dm2.txt ...
#    (ver data/guias/README.md)

# 4. Indexar
.\.venv\Scripts\python.exe scripts\ingest_guias.py

# 5. Activar en .env y reiniciar el backend
#    RAG_ENABLED=true
```

Comprueba que está activo en <http://localhost:8000/api/health>: debe mostrar `"rag": true`.

## Cómo mostrar Ollama y Docker mientras se usan (demos)

Ollama y Docker trabajan en segundo plano; para que el público los vea, abre estas ventanas junto a la app:

| Qué quieres mostrar | Cómo |
|---|---|
| Modelo cargado y si usa GPU | `ollama ps` (columna `PROCESSOR`: p. ej. `100% GPU`) |
| Uso de la GPU en vivo | `nvidia-smi -l 1`, o Administrador de tareas → Rendimiento → GPU |
| Velocidad real del modelo | `ollama run qwen2.5:7b --verbose "Hola"` → línea `eval rate` (tokens/s) |
| Chroma funcionando | Docker Desktop → Containers → `paciente-virtual-chroma` → Logs / Stats |
| Logs y consumo de Chroma | `docker compose logs -f chroma` y `docker stats` |
| Estado de todo el sistema | <http://localhost:8000/api/health> (Ollama, modelo, datos, RAG) |
| Documentación de la API | <http://localhost:8000/docs> |
| Registro del backend | La ventana «Paciente Virtual - Backend» |

La insignia junto al título de la app (● En línea / Sin LLM) indica si el modelo responde.

## Módulos clínicos: pruebas, plan y control

Cierran el ciclo clínico después de la entrevista. Detalle del diseño en [SEGUIMIENTO.md](SEGUIMIENTO.md).

1. **Pruebas:** una pestaña junto al chat con un catálogo único (22 pruebas, el mismo para todos los casos). Cada resultado sale de datos escritos, nunca lo inventa el modelo. Algunos niveles limitan la cantidad o el costo.
2. **Plan de tratamiento:** al terminar, tras el diagnóstico, eliges disposición, medicamentos e indicaciones. Se compara con un plan esperado; un medicamento contraindicado genera una **alerta de seguridad** y, en el nivel Avanzado, impide aprobar. Las dosis son informativas (no se puntúan).
3. **Control:** el paciente vuelve y cuenta cómo evolucionó según lo que decidiste (mejora, mejora parcial o empeora). Es un texto pregrabado elegido por reglas.

**Importante:** estos módulos solo se activan en un caso con `revision_clinica.estado: "validado"` y un revisor real (`revisado_por`, `fecha`, `fuente`). Hoy los 8 casos están en `pendiente`: el contenido clínico lo redactó una IA y **nadie lo ha revisado**. Por eso, por defecto, la aplicación funciona como antes (entrevista, diagnóstico y puntaje clásico).

Para demostrarlos antes de tener revisión médica:

```powershell
# en .env
SEGUIMIENTO_DEMO=true
```

Con eso aparecen la pestaña «Pruebas» y el paso del plan, con el aviso visible de contenido sin validar. Cuando un médico revise un caso, cambia su `revision_clinica` a `validado` con su nombre, fecha y la guía en la que se basó; el validador (`scripts\validate_casos.py`) rechaza `validado` sin esos datos.

## Pruebas y validaciones

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
.\.venv\Scripts\python.exe scripts\validate_casos.py          # integridad de los 8 casos
.\.venv\Scripts\python.exe -m pytest backend\tests -q         # ~130 pruebas (no necesitan Ollama)
cd frontend; npm run build                                     # compila el frontend
```

Las pruebas incluyen que ni la API ni el prompt del paciente expongan el diagnóstico.

## Estructura

```
├─ iniciar.bat · run.bat        arranque con un clic (Windows)
├─ docker-compose.yml           Chroma (opcional), versión fijada
├─ .env.example                 configuración de ejemplo
├─ data/
│  ├─ personas.json             150 adultos del dataset
│  ├─ casos.json                8 casos clínicos ficticios
│  ├─ glosario.json             términos médicos
│  └─ guias/                    guías clínicas para el RAG
├─ scripts/                     build_personas · validate_casos · ingest_guias
├─ backend/app/                 FastAPI: sesiones, prompts, evaluación, voz, RAG
├─ backend/tests/               pytest
└─ frontend/src/                React: chat, ficha del paciente, resultados
```

## Modo vista previa (sin Ollama)

Pensado para quien solo necesita **ver o editar la interfaz** (diseño, textos, estilos) en un equipo sin Ollama ni GPU. Si el servidor no encuentra Ollama o el modelo, la app abre sola en modo vista previa:

- Aparece la insignia «Vista previa» y un banner azul con el motivo y un botón **Reintentar conexión**.
- Se puede recorrer **todo**: selector de niveles, ficha del paciente, pestaña de pruebas, plan de tratamiento, resultados y progreso. También funcionan las pistas.
- **Solo se bloquea el envío de mensajes:** el campo de texto y el micrófono quedan desactivados.
- El chat muestra dos mensajes de **ejemplo** (marcados «ejemplo», que no se envían ni cuentan como preguntas), para ver cómo se ven las burbujas. «Terminar y diagnosticar» queda habilitado.
- La evaluación funciona igual, con la retroalimentación automática en lugar de la del modelo.

Cómo arrancarlo en un equipo sin Ollama: `iniciar.bat` (avisa y sigue), o a mano el backend y el frontend como en [Ejecución manual](#ejecución-manual). Las voces y los avatares siguen necesitando internet.

Otras formas de usarlo:

- **Forzarlo aunque haya Ollama:** abre `http://localhost:5173/?vista_previa=1`.
- **Dos backends a la vez** (por ejemplo, uno sin Ollama para probar este modo): en PowerShell, `$env:API_TARGET="http://localhost:8010"; npm run dev -- --port 5180` hace que ese frontend use ese backend.

## Solución de problemas

| Síntoma | Qué hacer |
|---|---|
| Insignia «Vista previa» y banner azul | No hay Ollama o falta el modelo: abre Ollama o ejecuta `ollama serve` y pulsa «Reintentar conexión». Ver [Modo vista previa](#modo-vista-previa-sin-ollama). |
| Aviso «El modelo … no está descargado» | `ollama pull qwen2.5:7b`. |
| El paciente responde lento | Cierra programas que usen la GPU; prueba `LLM_MODEL=qwen2.5:3b` o `NUM_CTX=2048`. |
| No suena la voz o no carga el avatar | Revisa tu conexión a internet; ambos son servicios externos. |
| `docker compose` falla con «cannot find the file specified» | Docker Desktop está apagado: ábrelo y espera a que diga «Running». |
| `"rag": false` con RAG activado | Verifica `docker ps`, que `RAG_ENABLED=true` y que Chroma responda en <http://localhost:8001/api/v2/heartbeat>. |
| Puerto 8000 o 5173 ocupado | Cierra la ventana anterior del backend o frontend. |
| El RAG no devuelve citas | Falta ejecutar `scripts\ingest_guias.py` o no hay documentos en `data/guias/`. |

## Limitaciones conocidas

- Los casos **no han sido revisados por un profesional de la salud**.
- La evaluación usa palabras clave sobre lo que pregunta el estudiante: no entiende negaciones ni paráfrasis lejanas.
- El modelo local de 7B a veces cuenta más síntomas de los esperados en una sola respuesta.
- Las sesiones viven en memoria: al reiniciar el backend se pierden.

## Créditos y licencias

- Personas: [Nemotron-Personas-El-Salvador](https://huggingface.co/datasets/nvidia/Nemotron-Personas-El-Salvador) de NVIDIA, desarrollado con la Agencia Nacional de IA de El Salvador (ANIA) y WideLabs, bajo licencia **CC BY 4.0**. Los datos son sintéticos y no identifican a personas reales.
- Modelo de lenguaje: Qwen2.5 (vía Ollama). Voz: Microsoft Edge TTS. Avatares: DiceBear.
- Este repositorio todavía no incluye un archivo `LICENSE`.
