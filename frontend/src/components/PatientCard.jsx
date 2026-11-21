import { useEffect, useState } from 'react'

export default function PatientCard({ paciente, motivo, ver, onToggle }) {
  const [imgFalla, setImgFalla] = useState(false)
  useEffect(() => setImgFalla(false), [paciente.avatar_url])

  return (
    <aside className="panel card">
      <h2>Paciente</h2>
      <p className="motivo">
        <span className="label">Motivo de consulta</span>
        {motivo}
      </p>

      <label className="switch">
        <input type="checkbox" checked={ver} onChange={onToggle} />
        <span>Ver paciente</span>
      </label>

      {ver && (
        <div className="datos">
          {!imgFalla && <img src={paciente.avatar_url} alt={`Avatar de ${paciente.nombre}`} onError={() => setImgFalla(true)} />}
          <dl>
            <dt>Nombre</dt><dd>{paciente.nombre}</dd>
            <dt>Edad</dt><dd>{paciente.edad} años</dd>
            <dt>Ocupación</dt><dd>{paciente.ocupacion}</dd>
            <dt>Procedencia</dt><dd>{paciente.municipio}, {paciente.departamento}</dd>
          </dl>
        </div>
      )}
    </aside>
  )
}
