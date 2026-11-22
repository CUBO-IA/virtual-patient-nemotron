import json
from typing import AsyncIterator

import httpx

from . import config


class LLMError(Exception):
    pass


def _payload(messages: list[dict], stream: bool, temperature: float, num_predict: int) -> dict:
    return {
        "model": config.LLM_MODEL,
        "messages": messages,
        "stream": stream,
        "keep_alive": "30m",
        "options": {"temperature": temperature, "num_predict": num_predict, "num_ctx": config.NUM_CTX},
    }


def _conn_error(e: Exception) -> LLMError:
    return LLMError(f"No se pudo conectar con Ollama en {config.OLLAMA_URL}. ¿Está corriendo? ({type(e).__name__})")


async def stream_chat(messages: list[dict], temperature: float = 0.7, num_predict: int = 180) -> AsyncIterator[str]:
    timeout = httpx.Timeout(120.0, connect=5.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", f"{config.OLLAMA_URL}/api/chat", json=_payload(messages, True, temperature, num_predict)) as r:
                if r.status_code != 200:
                    body = (await r.aread()).decode(errors="ignore")[:300]
                    raise LLMError(f"Ollama respondió {r.status_code}: {body}")
                async for line in r.aiter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    if "error" in data:
                        raise LLMError(f"Ollama: {data['error']}")
                    piece = data.get("message", {}).get("content", "")
                    if piece:
                        yield piece
                    if data.get("done"):
                        break
    except httpx.HTTPError as e:
        raise _conn_error(e) from e


async def chat_once(messages: list[dict], temperature: float = 0.0, num_predict: int = 300) -> str:
    timeout = httpx.Timeout(120.0, connect=5.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(f"{config.OLLAMA_URL}/api/chat", json=_payload(messages, False, temperature, num_predict))
    except httpx.HTTPError as e:
        raise _conn_error(e) from e
    if r.status_code != 200:
        raise LLMError(f"Ollama respondió {r.status_code}: {r.text[:300]}")
    return r.json().get("message", {}).get("content", "").strip()


async def health() -> dict:
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            r = await client.get(f"{config.OLLAMA_URL}/api/tags")
        names = [m.get("name", "") for m in r.json().get("models", [])]
        base = config.LLM_MODEL if ":" in config.LLM_MODEL else f"{config.LLM_MODEL}:latest"
        return {"ollama": True, "modelo": config.LLM_MODEL, "modelo_disponible": base in names}
    except Exception:
        return {"ollama": False, "modelo": config.LLM_MODEL, "modelo_disponible": False}
