"""Módulo RAG (Fase 2) para consulta de guías clínicas en Chroma."""

import logging
from urllib.parse import urlparse
import httpx

from . import config

logger = logging.getLogger(__name__)


async def health() -> bool:
    """Verifica si Chroma está disponible."""
    if not config.RAG_ENABLED:
        return False
    try:
        async with httpx.AsyncClient(timeout=1.5) as client:
            # Chroma 1.x eliminó la API v1 (responde 410); la v2 es la vigente.
            resp = await client.get(f"{config.CHROMA_URL}/api/v2/heartbeat")
            return resp.status_code == 200
    except Exception:
        return False


async def embed_query(text: str) -> list[float] | None:
    """Genera vector de embedding para una consulta usando Ollama."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{config.OLLAMA_URL}/api/embeddings",
                json={"model": config.EMBED_MODEL, "prompt": text},
            )
            if resp.status_code == 200:
                return resp.json().get("embedding")
    except Exception as e:
        logger.warning(f"Error al generar embedding para RAG: {e}")
    return None


async def consultar(guia_ref: str | None, query: str, top_k: int = 3, max_distancia: float | None = None) -> list[dict]:
    """Consulta fragmentos relevantes de guías clínicas en Chroma.

    Devuelve lista de [{"fuente": str, "fragmento": str}].
    Con `max_distancia` descarta fragmentos poco relevantes (puede devolver []).
    Degrada elegantemente a [] en caso de fallo o si RAG no está activo.
    """
    if not config.RAG_ENABLED or not guia_ref:
        return []

    try:
        vec = await embed_query(query)
        if not vec:
            return []

        import chromadb

        u = urlparse(config.CHROMA_URL)
        host = u.hostname or "localhost"
        port = u.port or 8001
        client = chromadb.HttpClient(host=host, port=port)

        try:
            coll = client.get_collection(name="guias")
        except Exception:
            return []

        results = coll.query(
            query_embeddings=[vec],
            n_results=top_k,
            where={"enfermedad": guia_ref},
        )

        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0] or [0.0] * len(docs)

        citas = []
        for d, m, dist in zip(docs, metas, dists):
            if max_distancia is not None and dist > max_distancia:
                continue
            if d:
                cita = {"fuente": m.get("fuente", "Guía clínica"), "fragmento": d.strip()}
                if max_distancia is not None:
                    cita["distancia"] = round(float(dist), 1)
                citas.append(cita)
        return citas
    except Exception as e:
        logger.warning(f"Error en consulta RAG a Chroma: {e}")
        return []
