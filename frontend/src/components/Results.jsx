import React from 'react'

export default function Results({
  r,
  diagnosticoEstudiante,
  diferencialesEstudiante = [],
  desbloqueoNuevo = null,
  onNuevoMismoNivel,
  onCambiarNivel,
  onVerProgreso,
}) {
  const aprobado = r.aprobado ?? (r.puntaje >= 70)
  const desglose = r.desglose || {}

  return (
    <div className="results">
      {desbloqueoNuevo && (
        <div className="achievement-banner" role="status">
          🎉 <strong>¡Felicitaciones!</strong> {desbloqueoNuevo}
        </div>
      )}

      <div className="results-header-card">
        <div className="score-block">
          <span className="num">{r.puntaje}</span>
          <span className="de">/ 100</span>
          <span className={`aprobado-badge ${aprobado ? 'aprobado' : 'a-mejorar'}`}>
            {aprobado ? '✓ Aprobado' : '⚠ A mejorar'}
          </span>
        </div>

        <div className="level-summary-pill">
          {r.nivel?.nombre ? `Nivel ${r.nivel.id} · ${r.nivel.nombre}` : 'Consulta completada'}
        </div>
      </div>

      {/* Tabla de desglose de puntaje (§5.1, §6.2) */}
      {desglose.checklist && (
        <section className="desglose-section">
          <h3>Desglose del puntaje</h3>
          <div className="desglose-grid">
            <div className="desglose-item">
              <span className="desglose-label">Lista de verificación</span>
              <span className="desglose-val">
                <strong>{desglose.checklist.obtenido}</strong> / {desglose.checklist.maximo} pts
              </span>
            </div>
            <div className="desglose-item">
              <span className="desglose-label">Diagnóstico principal</span>
              <span className="desglose-val">
                <strong>{desglose.diagnostico.obtenido}</strong> / {desglose.diagnostico.maximo} pts
              </span>
            </div>
            <div className="desglose-item">
              <span className="desglose-label">Señales de alarma</span>
              <span className="desglose-val">
                <strong>{desglose.banderas.obtenido}</strong> / {desglose.banderas.maximo} pts
              </span>
            </div>
            {desglose.diferenciales?.maximo > 0 && (
              <div className="desglose-item">
                <span className="desglose-label">Diagnóstico diferencial</span>
                <span className="desglose-val">
                  <strong>{desglose.diferenciales.obtenido}</strong> / {desglose.diferenciales.maximo} pts
                </span>
              </div>
            )}
            {r.pistas_usadas > 0 && (
              <div className="desglose-item penalizacion">
                <span className="desglose-label">Descuento por pistas ({r.pistas_usadas})</span>
                <span className="desglose-val">
                  {desglose.pistas?.descuento > 0 ? `−${desglose.pistas.descuento} pts` : 'Gratis (0 pts)'}
                </span>
              </div>
            )}
          </div>
        </section>
      )}

      <p className={`dx ${r.diagnostico_correcto ? 'ok' : 'mal'}`}>
        <strong>Diagnóstico real:</strong> {r.diagnostico_real}
        <br />
        <strong>Tu diagnóstico:</strong> {diagnosticoEstudiante} {r.diagnostico_correcto ? '✓' : '✗'}
      </p>

      {/* Diagnósticos diferenciales en Nivel Avanzado (§6.2) */}
      {r.diferenciales_razonables?.length > 0 && (
        <section className="diferenciales-feedback-box">
          <h3>Diagnósticos diferenciales</h3>
          {diferencialesEstudiante?.length > 0 && (
            <p className="diferenciales-propuestos">
              <strong>Tus diferenciales:</strong> {diferencialesEstudiante.join(', ')}
            </p>
          )}
          <p className="diferenciales-razonables-text">
            <strong>Diferenciales razonables para este caso:</strong>{' '}
            {r.diferenciales_razonables.join(', ')}
          </p>
        </section>
      )}

      <p className="feedback">{r.feedback}</p>

      <div className="cols">
        <section>
          <h3>Lo que preguntaste</h3>
          <ul className="lista ok">
            {r.cumplidos.length ? r.cumplidos.map((t) => <li key={t}>{t}</li>) : <li>Nada de la lista clave.</li>}
          </ul>
        </section>
        <section>
          <h3>Lo que faltó</h3>
          <ul className="lista mal">
            {r.faltantes.length ? r.faltantes.map((t) => <li key={t}>{t}</li>) : <li>Cubriste todo.</li>}
          </ul>
        </section>
      </div>

      <section>
        <h3>Señales de alarma</h3>
        <ul className="lista">
          {r.banderas.map((b) => (
            <li key={b.id} className={b.cumplida ? 'ok' : 'mal'}>
              {b.cumplida ? '✓' : '✗'} {b.texto}
            </li>
          ))}
        </ul>
      </section>

      {r.citas?.length > 0 && (
        <section className="citas-box">
          <h3>Guías clínicas de referencia</h3>
          <ul className="lista citas">
            {r.citas.map((c, i) => (
              <li key={i}>
                <strong>{c.fuente}:</strong> {c.fragmento}
              </li>
            ))}
          </ul>
        </section>
      )}

      <div className="results-actions-footer">
        <button type="button" className="btn primary" onClick={onNuevoMismoNivel}>
          🔄 Practicar otro paciente ({r.nivel?.nombre || 'mismo nivel'})
        </button>
        <button type="button" className="btn" onClick={onCambiarNivel}>
          🎚️ Cambiar de nivel
        </button>
        <button type="button" className="btn" onClick={onVerProgreso}>
          📊 Ver mi progreso
        </button>
      </div>
    </div>
  )
}
