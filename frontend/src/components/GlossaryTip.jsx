import React from 'react'

export const GLOSARIO = {
  // Clínicos
  anamnesis: "Entrevista clínica donde el estudiante hace preguntas al paciente para conocer su motivo de consulta y síntomas.",
  motivo_de_consulta: "La queja o razón principal expresada por el paciente por la cual acude a buscar atención.",
  sintomas: "Molestias subjetivas que el paciente siente y relata (ej. dolor, náuseas o mareo).",
  antecedentes: "Historial de salud previo del paciente y de su familia (enfermedades, cirugías o medicamentos).",
  habitos: "Costumbres y condiciones de vida cotidiana (alimentación, exposición laboral o consumo de sustancias).",
  signos_de_alarma: "Datos clínicos que indican peligro inminente o complicaciones graves que requieren atención inmediata.",
  diagnostico_presuntivo: "La sospecha médica razonada a la que llega el estudiante tras evaluar la entrevista.",
  lista_de_verificacion: "Guía de temas esenciales que todo estudiante debe indagar durante la consulta médica.",
  pistas: "Orientaciones en 3 niveles que ayudan a saber qué preguntar sin revelar el diagnóstico.",

  // Vocabulario de salud salvadoreño
  calentura: "Fiebre o elevación anormal de la temperatura corporal.",
  cuerpo_cortado: "Malestar general, dolor osteomuscular difuso, pesadez o quebranto físico.",
  cursera: "Diarrea o evacuaciones intestinales líquidas frecuentes.",
  descompuesto: "Malestar gastrointestinal, con náuseas, indigestión o diarrea.",
  empacho: "Indigestión o malestar gastrointestinal tras ingerir alimentos pesados o en exceso.",
  arrojar: "Vomitar o expulsar el contenido gástrico.",
  barriga: "Abdomen o estómago.",
  zancudo: "Mosquito o zancudo vector de infecciones como dengue, zika o chikungunya.",
  suero: "Solución de rehidratación oral o electrolitos para reponer pérdidas de líquido.",
  se_me_sube_la_presion: "Hipertensión arterial o sensación de alza en la presión sanguínea.",
  azucar_alta: "Diabetes mellitus o elevación de los niveles de glucosa en sangre.",

  // Vocabulario cotidiano salvadoreño
  cipote: "Niño, joven, muchacho o hijo.",
  chucho: "Perro.",
  chunche: "Cosa, objeto o aparato.",
  pisto: "Dinero o recursos económicos.",
  ruco: "Persona de edad avanzada o mayor.",
  cabal: "Exacto, correcto o justo.",
  puchica: "Exclamación salvadoreña de lamento, queja o sorpresa.",
  vaya_pues: "Expresión coloquial de acuerdo, conformidad o despedida.",
  chivo: "Genial, bueno, agradable o favorable.",
  chele: "Persona de tez o piel clara.",
  que_torta: "Qué problema o contratiempo difícil.",
  ahorita: "En este preciso momento o hace poco tiempo."
}

export default function GlossaryTip({ term }) {
  const def = GLOSARIO[term]
  if (!def) return null
  return (
    <span
      className="glossary-tip"
      title={def}
      tabIndex={0}
      aria-label={`${term}: ${def}`}
    >
      ?
    </span>
  )
}

const REGIONAL_PATTERNS = [
  { regex: /\b(cuerpo\s+cortado)\b/gi, term: "cuerpo_cortado" },
  { regex: /\b(se\s+me\s+sube\s+la\s+presi[oó]n)\b/gi, term: "se_me_sube_la_presion" },
  { regex: /\b(az[uú]car\s+alta)\b/gi, term: "azucar_alta" },
  { regex: /\b(vaya\s+pue[sj]?)\b/gi, term: "vaya_pues" },
  { regex: /\b(qu[eé]\s+torta)\b/gi, term: "que_torta" },
  { regex: /\b(calentura[sj]?)\b/gi, term: "calentura" },
  { regex: /\b(cursera[sj]?)\b/gi, term: "cursera" },
  { regex: /\b(descompuest[oa][sj]?)\b/gi, term: "descompuesto" },
  { regex: /\b(empacho[sj]?)\b/gi, term: "empacho" },
  { regex: /\b(arrojar|arroj[eé]|arroj[oó]|arrojando)\b/gi, term: "arrojar" },
  { regex: /\b(barriga[sj]?)\b/gi, term: "barriga" },
  { regex: /\b(zancudo[sj]?)\b/gi, term: "zancudo" },
  { regex: /\b(suero[sj]?)\b/gi, term: "suero" },
  { regex: /\b(cipote[sj]?|cipota[sj]?)\b/gi, term: "cipote" },
  { regex: /\b(chucho[sj]?|chucha[sj]?)\b/gi, term: "chucho" },
  { regex: /\b(chunche[sj]?)\b/gi, term: "chunche" },
  { regex: /\b(pisto[sj]?)\b/gi, term: "pisto" },
  { regex: /\b(ruco[sj]?|ruca[sj]?)\b/gi, term: "ruco" },
  { regex: /\b(cabal)\b/gi, term: "cabal" },
  { regex: /\b(p[uú]chica[sj]?)\b/gi, term: "puchica" },
  { regex: /\b(chivo|chilero)\b/gi, term: "chivo" },
  { regex: /\b(chele[sj]?|chela[sj]?)\b/gi, term: "chele" },
  { regex: /\b(ahorita)\b/gi, term: "ahorita" }
]

export function renderWithGlossaryTips(text) {
  if (!text || typeof text !== 'string') return text

  // Encuentra coincidencias no superpuestas
  const matches = []
  for (const { regex, term } of REGIONAL_PATTERNS) {
    let m
    const re = new RegExp(regex.source, regex.flags)
    while ((m = re.exec(text)) !== null) {
      matches.push({
        start: m.index,
        end: m.index + m[0].length,
        text: m[0],
        term
      })
    }
  }

  if (matches.length === 0) return text

  // Ordenar y descartar solapamientos
  matches.sort((a, b) => a.start - b.start)
  const nonOverlapping = []
  let lastEnd = 0
  for (const match of matches) {
    if (match.start >= lastEnd) {
      nonOverlapping.push(match)
      lastEnd = match.end
    }
  }

  const nodes = []
  let cursor = 0
  nonOverlapping.forEach((m, idx) => {
    if (m.start > cursor) {
      nodes.push(text.slice(cursor, m.start))
    }
    nodes.push(
      <span key={`term-${idx}`} className="glossary-term">
        {m.text}
        <GlossaryTip term={m.term} />
      </span>
    )
    cursor = m.end
  })

  if (cursor < text.length) {
    nodes.push(text.slice(cursor))
  }

  return nodes
}
