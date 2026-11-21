const GLOSARIO = {
  anamnesis: "Entrevista clínica donde el estudiante hace preguntas al paciente para conocer su motivo de consulta y síntomas.",
  motivo_de_consulta: "La queja o razón principal expresada por el paciente por la cual acude a buscar atención.",
  sintomas: "Molestias subjetivas que el paciente siente y relata (ej. dolor, náuseas o mareo).",
  antecedentes: "Historial de salud previo del paciente y de su familia (enfermedades, cirugías o medicamentos).",
  habitos: "Costumbres y condiciones de vida cotidiana (alimentación, exposición laboral o consumo de sustancias).",
  signos_de_alarma: "Datos clínicos que indican peligro inminente o complicaciones graves que requieren atención inmediata.",
  diagnostico_presuntivo: "La sospecha médica razonada a la que llega el estudiante tras evaluar la entrevista.",
  lista_de_verificacion: "Guía de temas esenciales que todo estudiante debe indagar durante la consulta médica.",
  pistas: "Orientaciones en 3 niveles que ayudan a saber qué preguntar sin revelar el diagnóstico."
}

export default function GlossaryTip({ term }) {
  const def = GLOSARIO[term]
  if (!def) return null
  return (
    <span className="glossary-tip" title={def} tabIndex={0} aria-label={def}>
      ?
    </span>
  )
}
