# Prompt para Codex

Copia y pega todo lo que está debajo de la línea en Codex, con la carpeta `ai_in_action` como directorio de trabajo.

---

Lee `AGENTS.md` completo y trabaja siguiendo sus reglas. El proyecto "Paciente Virtual" ya tiene la fase 1 funcionando (backend FastAPI, frontend React, 150 personas, 3 casos). Tu trabajo es completar lo pendiente, en este orden. Termina y verifica cada tarea antes de pasar a la siguiente.

## Tarea 1 — Validador y más casos clínicos

1. Crea `scripts/validate_casos.py` que lea `data/casos.json` y falle con mensajes claros si:
   - falta algún campo obligatorio del esquema de `AGENTS.md` sección 5;
   - algún `id` se repite;
   - el nombre del diagnóstico (o cualquier alias) aparece en `motivo_consulta`, `sintomas`, `antecedentes`, `habitos` o `datos_si_pregunta` (comparación sin tildes ni mayúsculas, palabra completa);
   - `edad_min > edad_max`, o `lista_verificacion`/`banderas_rojas` vacías;
   - no existe ninguna persona de `data/personas.json` compatible con las restricciones del caso.
2. Añade 5 casos nuevos a `data/casos.json` con el mismo esquema, clínicamente simples y correctos, que sean frecuentes en El Salvador y distintos entre sí. Sugeridos: crisis o descontrol de hipertensión arterial, trauma por accidente de moto, gastroenteritis aguda con deshidratación, neumonía adquirida en la comunidad, depresión o ansiedad. Cada uno con `lista_verificacion` de 6-8 ítems y 2-3 `banderas_rojas`. Usa `departamentos_tipicos` y `ocupaciones_tipicas` donde tenga sentido clínico.
3. Si un caso necesita datos que el dataset de personas no tiene, no modifiques `personas.json`; ajusta las restricciones del caso.
4. Corre el validador y deja que pase. Marca en `AGENTS.md` (sección 2) que los casos están pendientes de revisión médica.

## Tarea 2 — Pruebas automáticas

1. Agrega `pytest` (y `httpx` si hace falta para `TestClient`) a un `backend/requirements-dev.txt`.
2. Crea `backend/tests/` con pruebas que **no requieran Ollama** (mockea `llm.stream_chat` y `llm.chat_once`):
   - `norm()` y el matching de keywords (prefijo de palabra; tildes; que `"pie"` no coincida por error con palabras ajenas según los casos reales).
   - `evaluate.evaluar`: puntaje en tres escenarios (todo cumplido y diagnóstico correcto = 100; nada = 0; mixto), y diagnóstico por alias con palabra completa (por ejemplo `"erc"` no debe coincidir dentro de "ejercicio").
   - `assign.sortear`: respeta sexo y edad en 200 sorteos por caso.
   - API con `TestClient`: crear sesión, chat con LLM simulado, `finish` idempotente, 404, 422, 409 si ya terminó.
   - **No-fuga:** la respuesta de `POST /api/sessions` y los mensajes del chat no contienen `diagnostico`, `lista_verificacion`, `datos_si_pregunta` ni `banderas_rojas`, y `system_paciente()` no contiene el nombre del diagnóstico ni sus alias para ningún caso.
3. Si una prueba revela un bug real, corrígelo en el código (cambio mínimo) y menciónalo en el resumen final.

## Tarea 3 — Fase 2: RAG con Chroma en Docker

Sigue la sección 7 de `AGENTS.md`.

1. `docker-compose.yml` con el servicio `chroma` (puerto host 8001, volumen persistente).
2. `scripts/ingest_guias.py` y `backend/app/rag.py` como se describe allí. Añade el cliente de Chroma a `backend/requirements.txt` (usa el cliente HTTP, `chromadb-client` o equivalente ligero, y justifícalo).
3. Integra RAG en `evaluate.py` detrás de `RAG_ENABLED`, con degradación elegante, y añade `rag: true|false` a `/api/health`.
4. En `data/guias/` crea solo un `README.md` que explique qué documentos colocar (uno por enfermedad, nombre de archivo igual al `guia_ref` del caso) y que deben ser públicos o de licencia abierta. **No inventes ni redactes guías clínicas.** Para probar el pipeline usa un archivo temporal de prueba que borres al final, o pruebas con datos simulados.
5. Añade `guia_ref` a cada caso de `casos.json` y al validador (opcional si no hay guía).
6. Pruebas: con Chroma simulado, `citas` se llena; con Chroma caído, `/finish` responde igual sin `citas` y sin error.
7. Si Docker está disponible, levanta `chroma`, ingiere un documento de prueba, confirma que `/finish` devuelve `citas` y baja el servicio. Si no puedes ejecutar Docker, dilo explícitamente en el resumen.

## Tarea 4 — Pulido de la interfaz (solo si las 3 anteriores están completas)

- Indicador de estado en la cabecera que consulte `/api/health` y avise si Ollama está caído o falta el modelo, con mensaje claro.
- Mostrar `citas` en `Results.jsx` cuando existan (el componente ya las soporta; verifica que se vean bien).
- Que el botón "Terminar y diagnosticar" no se active hasta que el estudiante haya enviado al menos una pregunta (ya lo hace por `mensajes.length`; confirma que sigue así).
- No rediseñes la interfaz ni cambies dependencias.

## Restricciones

- No cambies las reglas del prompt del paciente en `prompts.py`.
- No cambies el contrato de la API ni el esquema de casos sin actualizar `AGENTS.md` en el mismo cambio.
- No toques `data/personas.json` ni `.env`.
- No hagas commit.

## Al terminar

Entrega un resumen corto con: qué hiciste por tarea, comandos que ejecutaste y su resultado (validador, `pytest`, `npm run build`, prueba del flujo real con Ollama si está corriendo), qué no pudiste verificar, y cualquier bug que encontraste. Si algo de este prompt contradice `AGENTS.md`, sigue `AGENTS.md` y avísame.
