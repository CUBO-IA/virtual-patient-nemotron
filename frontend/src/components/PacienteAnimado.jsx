import { useEffect, useState } from 'react'

export default function PacienteAnimado({ paciente, estado, expresion }) {
  const [falla, setFalla] = useState(false)
  useEffect(() => setFalla(false), [paciente.avatar_url])

  // Sin internet (o si DiceBear falla) no hay imagen: se muestran las iniciales dentro del mismo círculo.
  if (falla || !paciente?.avatar_url) {
    const iniciales = (paciente?.nombre || '?').trim().split(/\s+/).slice(0, 2).map((p) => p[0]?.toUpperCase()).join('')
    return (
      <div className={`paciente-wrap ${estado || 'reposo'}`} role="img" aria-label={`Paciente ${paciente?.nombre || ''}`}>
        <span className="paciente-iniciales" aria-hidden="true">{iniciales}</span>
      </div>
    )
  }

  return (
    <div className={`paciente-wrap ${estado || 'reposo'} ${expresion === 'dolor' ? 'con-dolor' : ''}`}>
      <img
        src={paciente.avatar_url}
        alt={`Avatar de ${paciente.nombre}`}
        className={`paciente ${estado || 'reposo'}`}
        onError={() => setFalla(true)}
      />
    </div>
  )
}
