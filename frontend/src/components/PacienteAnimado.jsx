import { useEffect, useState } from 'react'

export default function PacienteAnimado({ paciente, estado, expresion }) {
  const [falla, setFalla] = useState(false)
  useEffect(() => setFalla(false), [paciente.avatar_url])

  if (falla || !paciente?.avatar_url) return null

  return (
    <div className={`paciente-wrap ${expresion === 'dolor' ? 'con-dolor' : ''}`}>
      <img
        src={paciente.avatar_url}
        alt={`Avatar de ${paciente.nombre}`}
        className={`paciente ${estado || 'reposo'}`}
        onError={() => setFalla(true)}
      />
    </div>
  )
}
