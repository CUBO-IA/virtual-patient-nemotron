import { useState } from 'react'
import GlossaryTip from './GlossaryTip.jsx'
import PacienteAnimado from './PacienteAnimado.jsx'
import { etiquetaEstadoCivil, etiquetaEscolaridad, etiquetaHogar } from '../etiquetas.js'

export default function PatientCard({ paciente, motivo, ver, onToggle, estado, expresion }) {
  const [perfilVisible, setPerfilVisible] = useState(false)
  return (
    <aside className="panel card">
      <h2>Paciente</h2>
      <p className="motivo">
        <span className="label">
          Motivo de consulta <GlossaryTip term="motivo_de_consulta" />
        </span>
        {motivo}
      </p>

      <label className="switch">
        <input type="checkbox" checked={ver} onChange={onToggle} />
        <span>Ver paciente</span>
      </label>

      <button
        type="button"
        className="btn perfil-paciente-toggle"
        aria-expanded={perfilVisible}
        aria-controls="perfil-sociodemografico"
        onClick={() => setPerfilVisible((visible) => !visible)}
      >
        <i className={`bi ${perfilVisible ? 'bi-person-vcard-fill' : 'bi-person-vcard'}`} />
        {perfilVisible ? 'Ocultar datos personales' : 'Ver datos personales'}
      </button>

      {ver && (
        <div className="datos">
          <PacienteAnimado paciente={paciente} estado={estado} expresion={expresion} />
        </div>
      )}

      {perfilVisible && (
        <div className="perfil-paciente" id="perfil-sociodemografico">
          <dl>
            <dt>Nombre</dt><dd>{paciente.nombre}</dd>
            <dt>Edad</dt><dd>{paciente.edad} años</dd>
            <dt>Ocupación</dt><dd>{paciente.ocupacion}</dd>
            {etiquetaEstadoCivil(paciente.estado_civil, paciente.sexo) && <><dt>Estado civil</dt><dd>{etiquetaEstadoCivil(paciente.estado_civil, paciente.sexo)}</dd></>}
            {etiquetaEscolaridad(paciente.nivel_educativo) && <><dt>Escolaridad</dt><dd>{etiquetaEscolaridad(paciente.nivel_educativo)}</dd></>}
            {etiquetaHogar(paciente.hogar) && <><dt>Hogar</dt><dd>{etiquetaHogar(paciente.hogar)}</dd></>}
            <dt>Procedencia</dt><dd>{paciente.municipio}, {paciente.departamento}</dd>
          </dl>
        </div>
      )}
    </aside>
  )
}
