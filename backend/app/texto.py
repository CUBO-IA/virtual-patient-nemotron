"""Limpieza y límites de texto generado por el modelo; sin dependencias externas."""
import re


def limpiar_texto_modelo(texto: str, max_chars: int = 700) -> str:
    if not texto:
        return ""
    s = str(texto)
    s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"(?m)^\s*```.*$", "", s)
    s = s.replace("```", "").replace("`", "")
    s = re.sub(r"(?m)^\s*(?:---+|\*{3,}|_{3,})\s*$", " ", s)
    s = re.sub(r"(?m)^\s*>\s?", "", s)
    s = re.sub(r"(?m)^\s*#{1,6}\s*[^\n]*$", "", s)
    s = re.sub(r"(?m)^\s*\d+[.)]\s+\*\*[^*]+\*\*\s*$", "", s)
    s = re.sub(r"(?m)^\s*(?:[-*+]\s+|\d+[.)]\s+)", "", s)
    s = re.sub(r"\*\*(.*?)\*\*|__(.*?)__", lambda m: m.group(1) or m.group(2), s, flags=re.S)
    s = re.sub(r"(?<!\w)[*_]([^*_]+)[*_](?!\w)", r"\1", s)
    s = re.sub(r"(?m)^\s*(?:---+|\*{3,}|_{3,})\s*$", " ", s)
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in s.splitlines()]
    paragraphs = []
    for line in lines:
        if line:
            if paragraphs and paragraphs[-1] != "": paragraphs.append(" ")
            paragraphs.append(line)
        elif paragraphs and paragraphs[-1] != "":
            paragraphs.append("")
    s = " ".join(p for p in paragraphs if p).strip()
    s = re.sub(r"\s+", " ", s)
    if len(s) > max_chars:
        prefix = s[:max_chars + 1]
        finales = [m.end() for m in re.finditer(r"[.!?](?:[\"'»)]*)?(?:\s|$)", prefix) if m.end() <= max_chars]
        if finales:
            s = s[:finales[-1]].rstrip()
        else:
            recorte = s[:max_chars - 1].rsplit(" ", 1)[0].rstrip(" ,;:-")
            s = recorte + "…" if recorte else ""
    return s if len(s) >= 20 else ""
