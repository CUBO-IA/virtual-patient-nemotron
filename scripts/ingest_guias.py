"""Script para ingesta de guías clínicas en Chroma (Fase 2)."""

import os
import sys
from pathlib import Path
from urllib.parse import urlparse
import httpx

ROOT = Path(__file__).resolve().parents[1]
GUIAS_DIR = ROOT / "data" / "guias"


def _load_env():
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


_load_env()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
EMBED_MODEL = os.getenv("EMBED_MODEL", "bge-m3")
CHROMA_URL = os.getenv("CHROMA_URL", "http://localhost:8001").rstrip("/")


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 80) -> list[str]:
    words = text.split()
    if not words:
        return []
    chunks = []
    step = max(1, chunk_size - overlap)
    for i in range(0, len(words), step):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks


def extract_text_and_pages(file_path: Path) -> list[tuple[str, int]]:
    suffix = file_path.suffix.lower()
    if suffix in [".md", ".txt"]:
        content = file_path.read_text(encoding="utf-8", errors="replace")
        return [(content, 1)]
    elif suffix == ".pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(str(file_path))
            pages = []
            for idx, page in enumerate(reader.pages):
                txt = page.extract_text() or ""
                if txt.strip():
                    pages.append((txt, idx + 1))
            return pages
        except ImportError:
            print("Aviso: 'pypdf' no está instalado. Omitiendo archivo PDF:", file_path.name)
            return []
    return []


def get_embedding(client: httpx.Client, text: str) -> list[float]:
    resp = client.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()["embedding"]


def main():
    if not GUIAS_DIR.exists():
        print(f"No existe el directorio de guías: {GUIAS_DIR}")
        sys.exit(0)

    # Buscar archivos .md, .txt, .pdf excluyendo README.md
    files = [
        f for f in GUIAS_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in [".md", ".txt", ".pdf"] and f.name.lower() != "readme.md"
    ]

    if not files:
        print("No se encontraron documentos (.md, .txt, .pdf) en data/guias/ para ingerir.")
        print("Coloca documentos clínicos oficiales nombrados según su 'guia_ref' (ej. dengue.md).")
        sys.exit(0)

    import chromadb

    u = urlparse(CHROMA_URL)
    host = u.hostname or "localhost"
    port = u.port or 8001
    try:
        chroma_client = chromadb.HttpClient(host=host, port=port)
    except Exception as e:
        print(f"Error conectando a Chroma en {CHROMA_URL}: {e}")
        print("Asegúrate de que Chroma esté ejecutándose (ej. 'docker compose up -d chroma').")
        sys.exit(1)

    collection = chroma_client.get_or_create_collection(name="guias")

    with httpx.Client() as http_client:
        total_chunks = 0
        for f in files:
            enfermedad = f.stem  # nombre sin extensión = guia_ref
            fuente = f.name
            print(f"Procesando '{f.name}' para enfermedad '{enfermedad}'...")

            pages = extract_text_and_pages(f)
            chunks_to_insert = []
            metadatas = []
            ids = []

            for page_text, page_num in pages:
                chunks = chunk_text(page_text)
                for c_idx, chunk in enumerate(chunks):
                    chunks_to_insert.append(chunk)
                    metadatas.append({
                        "fuente": fuente,
                        "enfermedad": enfermedad,
                        "pagina": page_num,
                    })
                    ids.append(f"{enfermedad}_{page_num}_{c_idx}")

            if not chunks_to_insert:
                print(f"  Sin texto extraíble en {f.name}")
                continue

            print(f"  Generando embeddings para {len(chunks_to_insert)} fragmentos con Ollama ({EMBED_MODEL})...")
            embeddings = []
            for chunk in chunks_to_insert:
                emb = get_embedding(http_client, chunk)
                embeddings.append(emb)

            collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=chunks_to_insert,
                metadatas=metadatas,
            )
            total_chunks += len(chunks_to_insert)
            print(f"  Ingeridos {len(chunks_to_insert)} fragmentos de {f.name}.")

        print(f"\nIngesta completa: {total_chunks} fragmentos indexados en la colección 'guias'.")


if __name__ == "__main__":
    main()
