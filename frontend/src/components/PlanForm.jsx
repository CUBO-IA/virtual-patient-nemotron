import { useMemo } from 'react'

/** Estado inicial del plan (lo usa App.jsx). */
export const PLAN_VACIO = {
  disposicion: '',
  medicamentos: [], // [{ id, dosis, frecuencia, duracion }]
  sin_tratamiento: false,
  indicaciones: [],
  control_dias: '',
}

/** Convierte el estado del formulario al cuerpo que espera POST /finish. */
export function planParaEnviar(plan) {
  return {
    disposicion: plan.disposicion,
    medicamentos: plan.medicamentos.map((m) => ({
      id: m.id,
      dosis: m.dosis?.trim() || null,
      frecuencia: m.frecuencia?.trim() || null,
      duracion: m.duracion?.trim() || null,
    })),
    sin_tratamiento_farmacologico: plan.sin_tratamiento,
    indicaciones: plan.indicaciones,
    control_dias: plan.control_dias ? Number(plan.control_dias) : null,
  }
}

/** Devuelve un mensaje de error o '' si el plan está completo. */
export function validarPlan(plan) {
  if (!plan.disposicion) return 'Elige qué hacer con el paciente (disposición).'
  if (!plan.sin_tratamiento && plan.medicamentos.length === 0) {
    return 'Elige al menos un medicamento o marca «Sin tratamiento farmacológico».'
  }
  return ''
}

export default function PlanForm({ formulario, plan, onChange }) {
  const grupos = useMemo(() => {
    if (!formulario) return []
    const mapa = new Map()
    for (const m of formulario.medicamentos) {
      const g = m.grupo || 'Otros'
      if (!mapa.has(g)) mapa.set(g, [])
      mapa.get(g).push(m)
    }
    return [...mapa.entries()]
  }, [formulario])

  if (!formulario) return <p className="vacio">Cargando formulario…</p>

  const elegido = (id) => plan.medicamentos.find((m) => m.id === id)

  function alternarMedicamento(id) {
    if (elegido(id)) {
      onChange({ ...plan, medicamentos: plan.medicamentos.filter((m) => m.id !== id) })
    } else {
      onChange({
        ...plan,
        sin_tratamiento: false,
        medicamentos: [...plan.medicamentos, { id, dosis: '', frecuencia: '', duracion: '' }],
      })
    }
  }

  function campoMedicamento(id, campo, valor) {
    onChange({
      ...plan,
      medicamentos: plan.medicamentos.map((m) => (m.id === id ? { ...m, [campo]: valor } : m)),
    })
  }

  function alternarSinTratamiento(activo) {
    onChange({ ...plan, sin_tratamiento: activo, medicamentos: activo ? [] : plan.medicamentos })
  }

  function alternarIndicacion(id) {
    const ya = plan.indicaciones.includes(id)
    onChange({ ...plan, indicaciones: ya ? plan.indicaciones.filter((i) => i !== id) : [...plan.indicaciones, id] })
  }

  return (
    <div className="plan-form">
      <p className="plan-aviso" role="note">
        Ejercicio educativo. No uses esta aplicación para decidir tratamientos reales.
      </p>

      <fieldset>
        <legend>¿Qué harías con el paciente?</legend>
        {formulario.disposiciones.map((d) => (
          <label key={d.id} className="opcion">
            <input
              type="radio"
              name="disposicion"
              value={d.id}
              checked={plan.disposicion === d.id}
              onChange={() => onChange({ ...plan, disposicion: d.id })}
            />
            <span>{d.texto}</span>
          </label>
        ))}
      </fieldset>

      <fieldset>
        <legend>Medicamentos</legend>
        <label className="opcion sin-tx">
          <input type="checkbox" checked={plan.sin_tratamiento} onChange={(e) => alternarSinTratamiento(e.target.checked)} />
          <span>Sin tratamiento farmacológico</span>
        </label>

        {grupos.map(([grupo, meds]) => (
          <div key={grupo} className="plan-grupo">
            <h4>{grupo}</h4>
            {meds.map((m) => {
              const sel = elegido(m.id)
              return (
                <div key={m.id} className={`plan-med ${sel ? 'sel' : ''}`}>
                  <label className="opcion">
                    <input type="checkbox" checked={Boolean(sel)} onChange={() => alternarMedicamento(m.id)} />
                    <span>{m.nombre}</span>
                  </label>
                  {sel && (
                    <div className="plan-med-campos">
                      <input
                        aria-label={`Dosis de ${m.nombre}`}
                        placeholder="Dosis (opcional)"
                        value={sel.dosis}
                        maxLength={60}
                        onChange={(e) => campoMedicamento(m.id, 'dosis', e.target.value)}
                      />
                      <input
                        aria-label={`Frecuencia de ${m.nombre}`}
                        placeholder="Frecuencia (opcional)"
                        value={sel.frecuencia}
                        maxLength={60}
                        onChange={(e) => campoMedicamento(m.id, 'frecuencia', e.target.value)}
                      />
                      <input
                        aria-label={`Duración de ${m.nombre}`}
                        placeholder="Duración (opcional)"
                        value={sel.duracion}
                        maxLength={60}
                        onChange={(e) => campoMedicamento(m.id, 'duracion', e.target.value)}
                      />
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        ))}
        <p className="plan-nota">Dosis, frecuencia y duración son informativas: en esta versión no se puntúan.</p>
      </fieldset>

      <fieldset>
        <legend>Indicaciones</legend>
        <div className="plan-indicaciones">
          {formulario.indicaciones.map((i) => (
            <label key={i.id} className="opcion">
              <input type="checkbox" checked={plan.indicaciones.includes(i.id)} onChange={() => alternarIndicacion(i.id)} />
              <span>{i.texto}</span>
            </label>
          ))}
        </div>
      </fieldset>

      <div className="form-group">
        <label htmlFor="plan-control">Cita de control en:</label>
        <select id="plan-control" value={plan.control_dias} onChange={(e) => onChange({ ...plan, control_dias: e.target.value })}>
          <option value="">Sin cita de control</option>
          {Array.from({ length: 14 }, (_, i) => i + 1).map((d) => (
            <option key={d} value={d}>
              {d} {d === 1 ? 'día' : 'días'}
            </option>
          ))}
        </select>
      </div>
    </div>
  )
}
