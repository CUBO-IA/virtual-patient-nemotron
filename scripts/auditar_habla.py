"""Auditoría de habla salvadoreña de los pacientes virtuales.

1) Auditoría de datos: busca palabras de registro médico en los textos de los que el
   paciente copia lo que dice (motivo, síntomas, antecedentes, hábitos, datos_si_pregunta).
2) Muestras (opcional, requiere Ollama): genera respuestas reales de pacientes y las revisa,
   para que un hablante salvadoreño las califique.

Uso:
  python scripts/auditar_habla.py                         # solo auditoría de datos
  python scripts/auditar_habla.py --muestras 1            # + 1 paciente por caso (Ollama)
  python scripts/auditar_habla.py --muestras 2 --caso c_gea_01

Escribe el informe en informes/habla_auditoria.md. Código de salida 1 si la auditoría
de datos encuentra términos a evitar.
"""
import argparse
import asyncio
import json
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

GLOSARIO = ROOT / "data" / "habla_salvadorena.json"
CASOS = ROOT / "data" / "casos.json"
INFORME = ROOT / "informes" / "habla_auditoria.md"

CAMPOS_LISTA = ["sintomas", "antecedentes", "habitos"]


def norm(text: str) -> str:
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return f" {text.strip()} "


def cargar_glosario() -> dict:
    return json.loads(GLOSARIO.read_text(encoding="utf-8"))


def _patron(termino: str) -> str:
    """Prefijo de palabra por defecto; palabra completa si el término termina en $."""
    if termino.endswith("$"):
        return norm(termino[:-1])  # " palabra "
    return norm(termino).rstrip()  # " prefijo"


def buscar_terminos(texto: str, glosario: dict) -> list[dict]:
    """Devuelve las entradas del glosario cuyos términos a evitar aparecen en el texto."""
    t = norm(texto)
    hallazgos = []
    for entrada in glosario["terminos"]:
        for termino in entrada["evitar"]:
            if _patron(termino) in t:
                hallazgos.append({"termino": termino.rstrip("$"), "entrada": entrada["id"], "entrada_obj": entrada})
    return hallazgos


def sugerencias(entrada: dict, n: int = 3) -> str:
    orden = {"alta": 0, "media": 1, "baja": 2}
    opciones = sorted(entrada["coloquial"], key=lambda c: orden.get(c["confianza"], 3))
    return ", ".join(f"«{c['texto']}»" for c in opciones[:n])


def textos_del_paciente(caso: dict) -> list[tuple[str, str]]:
    """(campo, texto) de lo que el paciente usa para hablar."""
    salida = [("motivo_consulta", caso["motivo_consulta"])]
    for campo in CAMPOS_LISTA:
        for i, t in enumerate(caso.get(campo, [])):
            salida.append((f"{campo}[{i}]", t))
    for tema, resp in caso.get("datos_si_pregunta", {}).items():
        salida.append((f"datos_si_pregunta['{tema}']", resp))
    if caso.get("evolucion"):
        for rama, d in caso["evolucion"].get("ramas", {}).items():
            salida.append((f"evolucion.{rama}.relato", d.get("relato", "")))
    return salida


def auditar_datos(casos: list[dict], glosario: dict) -> tuple[list[dict], list[dict]]:
    errores, avisos = [], []
    for caso in casos:
        for campo, texto in textos_del_paciente(caso):
            for h in buscar_terminos(texto, glosario):
                errores.append({"caso": caso["id"], "campo": campo, "texto": texto, **h})
        # Los temas (claves) llegan al prompt como "Si te preguntan por {tema}": pueden contagiar.
        for tema in caso.get("datos_si_pregunta", {}):
            for h in buscar_terminos(tema, glosario):
                avisos.append({"caso": caso["id"], "campo": f"tema '{tema}'", "texto": tema, **h})
    return errores, avisos


# Heurística: el paciente habla en 1.ª persona; si el texto del caso está en 3.ª
# («ha bajado 5 libras», «le duele la barriga»), el modelo lo repite como narrador.
TERCERA_PERSONA = re.compile(
    r"(^|[,;.] ?|\by |\ba veces |\bsolo |\bya )"
    r"(ha |han |le |les |tiene |tienen |siente |sienten |toma |ve |come |orina |duerme |se le |su |sus |"
    r"lleva |va |sufre |fuma |trabaja |vive |hace |dice |cuenta |sale |salio |salieron |sangro |sangraron |vomito )"
)


def en_tercera_persona(texto: str) -> bool:
    return bool(TERCERA_PERSONA.search(norm(texto).strip()))


def auditar_tercera_persona(casos: list[dict]) -> tuple[int, int, list[dict]]:
    """(en_3a_persona, total, ejemplos) sobre lo que el paciente usa para hablar."""
    total, hallados = 0, []
    for caso in casos:
        for campo, texto in textos_del_paciente(caso):
            total += 1
            if en_tercera_persona(texto):
                hallados.append({"caso": caso["id"], "campo": campo, "texto": texto})
    return len(hallados), total, hallados


# ---------------------------------------------------------------- muestras con Ollama

def _ngramas(texto: str, n: int = 5) -> set[tuple]:
    toks = norm(texto).split()
    return {tuple(toks[i:i + n]) for i in range(len(toks) - n + 1)}


def copias_literales(respuesta: str, caso: dict) -> list[str]:
    """Frases de 5 palabras que el paciente copió tal cual del texto del caso."""
    base = set()
    for _, t in textos_del_paciente(caso):
        base |= _ngramas(t)
    toks = norm(respuesta).split()
    copiadas = []
    for i in range(len(toks) - 4):
        if tuple(toks[i:i + 5]) in base:
            copiadas.append(" ".join(toks[i:i + 5]))
    return copiadas


PREGUNTA_INICIAL = "Buenas tardes, ¿qué le trae por aquí?"


async def generar_muestras(casos: list[dict], por_caso: int, glosario: dict) -> list[dict]:
    from app import assign, habla, llm, niveles, prompts

    base = niveles.obtener_nivel(2)  # actitud normal
    cfg = dict(base)
    cfg["casos"] = {"dificultad_max": 3, "peso_dificultad_igual": 1}

    resultados = []
    for caso in casos:
        for _ in range(por_caso):
            try:
                caso_sorteado, persona = assign.sortear(caso_id=caso["id"], nivel=cfg)
            except Exception as e:
                print(f"  ! {caso['id']}: {e}")
                continue
            nivel_asp = habla.nivel_aspiracion(persona)
            preguntas = [PREGUNTA_INICIAL] + [f"¿Me puede contar sobre {tema}?" for tema in list(caso["datos_si_pregunta"])[:4]]
            historial, turnos = [], []
            print(f"  {caso['id']} · {persona['nombre']} ({persona['edad']}, {persona['departamento']})")
            for q in preguntas:
                historial.append({"role": "user", "content": q})
                msgs = prompts.mensajes_paciente(persona, caso_sorteado, historial, cfg)
                try:
                    r = await llm.chat_once(msgs, temperature=0.7, num_predict=120)
                except Exception as e:
                    print(f"    ! error del modelo: {e}")
                    break
                historial.append({"role": "assistant", "content": r})
                hall = buscar_terminos(r, glosario)
                turnos.append({
                    "pregunta": q,
                    "respuesta": r,
                    "mostrada": habla.aspirar(r, nivel_asp),
                    "tercera_persona": en_tercera_persona(r),
                    "terminos": [h["termino"] for h in hall],
                    "sugerencias": {h["termino"]: sugerencias(h["entrada_obj"]) for h in hall},
                    "copias": copias_literales(r, caso),
                })
            resultados.append({"caso": caso["id"], "persona": persona, "aspiracion": nivel_asp, "turnos": turnos})
    return resultados


# ---------------------------------------------------------------- informe

def escribir_informe(errores, avisos, muestras, casos, tercera=None) -> str:
    L = []
    L.append("# Auditoría de habla salvadoreña")
    L.append("")
    L.append(f"Generado: {datetime.now():%Y-%m-%d %H:%M}. Glosario: `data/habla_salvadorena.json` (**borrador, sin validar por hablantes**).")
    L.append("")
    L.append("## 1. Auditoría de datos (casos)")
    L.append("")
    L.append(f"- Casos revisados: **{len(casos)}**")
    L.append(f"- Términos a evitar en lo que el paciente dice o copia: **{len(errores)}**")
    L.append(f"- Temas (claves de `datos_si_pregunta`) con vocabulario técnico: **{len(avisos)}** (entran al prompt como «Si te preguntan por…»)")
    L.append("")
    if errores:
        L.append("### Errores")
        L.append("")
        for e in errores:
            L.append(f"- `{e['caso']}` · `{e['campo']}`: «{e['texto']}» → contiene **{e['termino']}**. Alternativas: {sugerencias(e['entrada_obj'])}")
        L.append("")
    if avisos:
        L.append("### Avisos (temas)")
        L.append("")
        for a in avisos:
            L.append(f"- `{a['caso']}` · {a['campo']} → **{a['termino']}**. Alternativas: {sugerencias(a['entrada_obj'])}")
        L.append("")
    if not errores and not avisos:
        L.append("Sin hallazgos.")
        L.append("")

    if tercera is not None:
        n3, total3, ej3 = tercera
        pct = (100 * n3 // total3) if total3 else 0
        L.append("### Redacción en tercera persona")
        L.append("")
        L.append(f"**{n3} de {total3}** textos del paciente ({pct} %) parecen estar escritos en 3.ª persona (heurística). "
                 "El modelo los repite como un narrador («ha bajado unas 5 libras», «le duele al tomar aire»).")
        L.append("")
        for e in ej3[:20]:
            L.append(f"- `{e['caso']}` · `{e['campo']}`: «{e['texto']}»")
        if len(ej3) > 20:
            L.append(f"- … y {len(ej3) - 20} más")
        L.append("")

    if muestras is not None:
        total_t = sum(len(m["turnos"]) for m in muestras)
        con_term = sum(1 for m in muestras for t in m["turnos"] if t["terminos"])
        con_copia = sum(1 for m in muestras for t in m["turnos"] if t["copias"])
        L.append("## 2. Muestras reales del paciente")
        L.append("")
        L.append(f"- Pacientes simulados: **{len(muestras)}** · respuestas: **{total_t}**")
        L.append(f"- Respuestas con vocabulario médico: **{con_term}** de {total_t}")
        L.append(f"- Respuestas que copian frases (5+ palabras) del texto del caso: **{con_copia}** de {total_t} (es esperable: el caso es la fuente de los hechos; lo que importa es *cómo* se dicen)")
        con_3 = sum(1 for m in muestras for t in m["turnos"] if t.get("tercera_persona"))
        L.append(f"- Respuestas con posible 3.ª persona: **{con_3}** de {total_t}")
        L.append("")
        L.append("Para el revisor salvadoreño: califica cada respuesta de 1 (no suena salvadoreño) a 5 (suena natural) y anota qué palabra cambiarías.")
        L.append("")
        for m in muestras:
            p = m["persona"]
            L.append(f"### {m['caso']} — {p['nombre']}, {p['edad']} años ({p['municipio']}, {p['departamento']}, {p.get('area')})")
            L.append(f"_Escolaridad: {p['nivel_educativo']} · aspiración de la s: {m['aspiracion']}_")
            L.append("")
            for t in m["turnos"]:
                L.append(f"- **Doctor:** {t['pregunta']}")
                L.append(f"  - **Paciente (modelo):** {t['respuesta']}")
                if m["aspiracion"] != "ninguna":
                    L.append(f"  - **Se muestra en pantalla:** {t['mostrada']}")
                if t["terminos"]:
                    det = "; ".join(f"**{k}** → {v}" for k, v in t["sugerencias"].items())
                    L.append(f"  - ⚠ Vocabulario médico: {det}")
                if t.get("tercera_persona"):
                    L.append("  - ⚠ Posible 3.ª persona (suena a narrador, no al paciente)")
                if t["copias"]:
                    L.append(f"  - ℹ Copia literal del caso: «{t['copias'][0]}…»")
                L.append("  - Calificación: __ / 5 · Cambiaría: ____________")
            L.append("")
    texto = "\n".join(L) + "\n"
    INFORME.parent.mkdir(parents=True, exist_ok=True)
    INFORME.write_text(texto, encoding="utf-8")
    return texto


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--muestras", type=int, default=0, help="pacientes por caso a generar con Ollama (0 = solo auditoría de datos)")
    ap.add_argument("--caso", help="limitar a un id de caso")
    args = ap.parse_args()

    glosario = cargar_glosario()
    casos = json.loads(CASOS.read_text(encoding="utf-8"))
    if args.caso:
        casos = [c for c in casos if c["id"] == args.caso]
        if not casos:
            print(f"No existe el caso {args.caso}")
            return 2

    errores, avisos = auditar_datos(casos, glosario)
    print(f"Auditoría de datos: {len(errores)} errores, {len(avisos)} avisos en {len(casos)} casos")
    for e in errores:
        print(f"  ERROR {e['caso']} {e['campo']}: «{e['termino']}» → {sugerencias(e['entrada_obj'])}")
    for a in avisos:
        print(f"  aviso {a['caso']} {a['campo']}: «{a['termino']}»")

    muestras = None
    if args.muestras > 0:
        print(f"\nGenerando muestras con Ollama ({args.muestras} por caso)…")
        muestras = asyncio.run(generar_muestras(casos, args.muestras, glosario))
        total = sum(len(m["turnos"]) for m in muestras)
        marcadas = sum(1 for m in muestras for t in m["turnos"] if t["terminos"])
        copiadas = sum(1 for m in muestras for t in m["turnos"] if t["copias"])
        print(f"Muestras: {total} respuestas · {marcadas} con vocabulario médico · {copiadas} con copia literal")

    tercera = auditar_tercera_persona(casos)
    print(f"Redacción en 3.ª persona: {tercera[0]} de {tercera[1]} textos del paciente")

    escribir_informe(errores, avisos, muestras, casos, tercera)
    print(f"\nInforme: {INFORME}")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
