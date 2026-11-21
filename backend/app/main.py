import json
from urllib.parse import quote

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse

from . import assign, avatars, config, evaluate, habla, llm, prompts, rag, sessions, tts_service
from .models import ChatIn, FinishIn

app = FastAPI(title="Paciente Virtual")
app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"])


def _sse(data: dict, event: str | None = None) -> str:
    head = f"event: {event}\n" if event else ""
    return f"{head}data: {json.dumps(data, ensure_ascii=False)}\n\n"


def _get_session(session_id: str) -> sessions.Session:
    s = sessions.get(session_id)
    if not s:
        raise HTTPException(404, "Sesión no encontrada. Pulsa «Nuevo paciente».")
    return s


@app.get("/api/health")
async def health():
    info = await llm.health()
    try:
        personas, casos = assign.counts()
        info.update(personas=personas, casos=casos, datos=True)
    except FileNotFoundError as e:
        info.update(datos=False, error=str(e))
    info["rag"] = await rag.health()
    info["ok"] = info["ollama"] and info["modelo_disponible"] and info["datos"]
    return info


@app.post("/api/sessions")
async def crear_sesion():
    try:
        caso, persona = assign.sortear()
    except (FileNotFoundError, RuntimeError) as e:
        raise HTTPException(503, str(e))
    s = sessions.create(caso, persona)
    return {
        "session_id": s.id,
        "paciente": {
            "nombre": persona["nombre"],
            "edad": persona["edad"],
            "sexo": persona["sexo"],
            "ocupacion": persona["ocupacion"],
            "departamento": persona["departamento"],
            "municipio": persona["municipio"],
            "avatar_url": avatars.avatar_url(persona),
            "habla": habla.obtener_habla(persona),
        },
        "motivo_consulta": caso["motivo_consulta"],
    }


@app.post("/api/sessions/{session_id}/chat")
async def chat(session_id: str, body: ChatIn):
    s = _get_session(session_id)
    if s.finished:
        raise HTTPException(409, "La consulta ya terminó. Pulsa «Nuevo paciente».")
    if s.busy:
        raise HTTPException(409, "El paciente aún está respondiendo.")
    texto = body.message.strip()
    if not texto:
        raise HTTPException(422, "Mensaje vacío.")

    s.lock()
    s.mensajes.append({"role": "user", "content": texto})
    n_antes = len(s.mensajes)

    async def gen():
        partial: list[str] = []
        nivel = habla.nivel_aspiracion(s.persona)
        try:
            tok_stream = llm.stream_chat(prompts.mensajes_paciente(s.persona, s.caso, s.mensajes))
            async for tok in habla.aspirar_stream(tok_stream, nivel):
                partial.append(tok)
                yield _sse({"token": tok})
            yield _sse({"done": True})
        except llm.LLMError as e:
            yield _sse({"error": str(e)}, event="error")
        finally:
            respuesta = "".join(partial).strip()
            if respuesta:
                s.mensajes.append({"role": "assistant", "content": respuesta})
            elif len(s.mensajes) == n_antes:
                s.mensajes.pop()  # sin respuesta: se quita la pregunta para no dejar el historial inconsistente
            s.unlock()

    return StreamingResponse(gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/api/sessions/{session_id}/pista")
async def pedir_pista(session_id: str):
    s = _get_session(session_id)
    if s.finished:
        raise HTTPException(409, "La consulta ya terminó.")
    if s.busy:
        raise HTTPException(409, "El paciente aún está respondiendo.")

    pistas = s.caso.get("pistas", [])
    if not pistas:
        return {
            "pista": "No hay pistas disponibles para este caso.",
            "disponible": False,
            "nivel": 0,
            "pistas_usadas": s.pistas_usadas,
        }

    texto_usuario = evaluate.norm(" . ".join(m["content"] for m in s.mensajes if m["role"] == "user"))
    items_preguntados = {
        it["id"] for it in s.caso.get("lista_verificacion", [])
        if evaluate._hit(it["keywords"], texto_usuario)
    }

    pendiente = None
    for p in pistas:
        if p["item"] not in items_preguntados:
            pendiente = p
            break

    if not pendiente:
        return {
            "pista": "Ya preguntaste lo esencial. Revisa si falta algo más.",
            "disponible": False,
            "nivel": 0,
            "pistas_usadas": s.pistas_usadas,
        }

    item_id = pendiente["item"]
    nivel_actual = s.nivel_por_item.get(item_id, 0)
    nuevo_nivel = min(nivel_actual + 1, 3)
    s.nivel_por_item[item_id] = nuevo_nivel
    s.pistas_usadas += 1

    texto_pista = pendiente.get(f"nivel_{nuevo_nivel}", "")
    return {
        "pista": texto_pista,
        "disponible": True,
        "nivel": nuevo_nivel,
        "item": item_id,
        "pistas_usadas": s.pistas_usadas,
    }


@app.get("/api/glosario")
async def obtener_glosario():
    glosario_path = config.DATA_DIR / "glosario.json"
    if glosario_path.exists():
        try:
            return json.loads(glosario_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


async def _audio_paciente(session_id: str, texto: str) -> Response:
    """Sintetiza la respuesta del paciente. El navegador la pide por GET para poder
    llamar a play() en el mismo clic; un fetch previo pierde el permiso de audio."""
    s = _get_session(session_id)
    limpio = (texto or "").strip()
    if not limpio:
        raise HTTPException(422, "Texto vacío.")
    if len(limpio) > 4000:
        raise HTTPException(422, "El texto es demasiado largo para leerlo en voz alta.")
    voz, perfil = tts_service.voz_y_perfil_persona(s.persona)
    try:
        audio_bytes = await tts_service.sintetizar_bytes(limpio, voz, perfil)
    except ValueError as e:
        raise HTTPException(422, str(e))
    except Exception as e:
        raise HTTPException(503, f"No se pudo generar la voz. Revisa la conexión a internet. ({e})")
    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={"Cache-Control": "private, max-age=3600"},
    )


@app.get("/api/sessions/{session_id}/tts")
async def sintetizar_audio_get(session_id: str, texto: str = ""):
    return await _audio_paciente(session_id, texto)


@app.post("/api/sessions/{session_id}/tts")
async def sintetizar_audio(session_id: str, body: dict):
    return await _audio_paciente(session_id, body.get("texto", ""))


@app.post("/api/sessions/{session_id}/finish")
async def terminar(session_id: str, body: FinishIn):
    s = _get_session(session_id)
    if s.result:
        return s.result
    if s.busy:
        raise HTTPException(409, "El paciente aún está respondiendo.")
    s.lock()
    try:
        s.result = await evaluate.evaluar(s, body.diagnostico_estudiante.strip())
        s.finished = True
    finally:
        s.unlock()
    return s.result
