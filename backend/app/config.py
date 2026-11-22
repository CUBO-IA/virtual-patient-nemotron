import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"


def _load_env_file():
    path = ROOT / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


_load_env_file()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:7b")
EMBED_MODEL = os.getenv("EMBED_MODEL", "bge-m3")
CHROMA_URL = os.getenv("CHROMA_URL", "http://localhost:8001").rstrip("/")
RAG_ENABLED = os.getenv("RAG_ENABLED", "false").lower() in ("true", "1", "yes")
GUIAS_DIR = DATA_DIR / "guias"
NUM_CTX = int(os.getenv("NUM_CTX", "2048"))
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]

# Mensajes de historial enviados al modelo (evita desbordar el contexto y perder el prompt de sistema).
MAX_HISTORY = 16

# Activa los módulos de pruebas, plan y control aunque el caso NO esté validado por un profesional
# (revision_clinica.estado != "validado"). Solo para demostraciones: la interfaz muestra el aviso
# «Contenido sin validar clínicamente». Por defecto está apagado.
SEGUIMIENTO_DEMO = os.getenv("SEGUIMIENTO_DEMO", "false").lower() in ("true", "1", "yes")

# Las sesiones se guardan en disco para que sobrevivan a un reinicio del servidor (p. ej. uvicorn --reload).
SESIONES_DIR = Path(os.getenv("SESIONES_DIR", str(ROOT / ".sesiones")))
SESIONES_TTL_HORAS = float(os.getenv("SESIONES_TTL_HORAS", "24"))  # las más viejas se borran
MAX_SESIONES_DISCO = int(os.getenv("MAX_SESIONES_DISCO", "500"))

# Penalización en puntaje por cada pista usada (configurable por .env)
PENALIZACION_PISTA = float(os.getenv("PENALIZACION_PISTA", "0.5"))
