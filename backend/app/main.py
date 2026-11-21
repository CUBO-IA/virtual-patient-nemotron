import json
from urllib.parse import quote

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from . import assign, config, evaluate, llm, prompts, rag, sessions
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
            "avatar_url": f"https://api.dicebear.com/9.x/avataaars/svg?seed={quote(persona['id'] + persona['nombre'])}",
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
        try:
            async for tok in llm.stream_chat(prompts.mensajes_paciente(s.persona, s.caso, s.mensajes)):
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
