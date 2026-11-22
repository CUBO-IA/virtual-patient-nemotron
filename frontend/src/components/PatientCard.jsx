import GlossaryTip from './GlossaryTip.jsx'
import PacienteAnimado from './PacienteAnimado.jsx'

export default function PatientCard({ paciente, motivo, ver, onToggle, estado, expresion }) {
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

      {ver && (
        <div className="datos">
          <PacienteAnimado paciente={paciente} estado={estado} expresion={expresion} />
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
