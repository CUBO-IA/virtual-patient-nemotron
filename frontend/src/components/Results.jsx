export default function Results({ r, diagnosticoEstudiante }) {
  return (
    <div className="results">
      <div className="score">
        <span className="num">{r.puntaje}</span>
        <span className="de">/ 100</span>
        {r.pistas_usadas > 0 && (
          <span className="pistas-tag" title={r.descuento_pistas ? `Descuento de ${r.descuento_pistas} pts por pistas` : 'Sin penalización'}>
            💡 {r.pistas_usadas} {r.pistas_usadas === 1 ? 'pista usada' : 'pistas usadas'}{r.descuento_pistas > 0 ? ` (-${r.descuento_pistas} pts)` : ''}
          </span>
        )}
      </div>

      <p className={`dx ${r.diagnostico_correcto ? 'ok' : 'mal'}`}>
        <strong>Diagnóstico real:</strong> {r.diagnostico_real}
        <br />
        <strong>Tu diagnóstico:</strong> {diagnosticoEstudiante} {r.diagnostico_correcto ? '✓' : '✗'}
      </p>

      <p className="feedback">{r.feedback}</p>

      <div className="cols">
        <section>
          <h3>Lo que preguntaste</h3>
          <ul className="lista ok">{r.cumplidos.length ? r.cumplidos.map((t) => <li key={t}>{t}</li>) : <li>Nada de la lista clave.</li>}</ul>
        </section>
        <section>
          <h3>Lo que faltó</h3>
          <ul className="lista mal">{r.faltantes.length ? r.faltantes.map((t) => <li key={t}>{t}</li>) : <li>Cubriste todo.</li>}</ul>
        </section>
      </div>

      <section>
        <h3>Señales de alarma</h3>
        <ul className="lista">
          {r.banderas.map((b) => (
            <li key={b.id} className={b.cumplida ? 'ok' : 'mal'}>{b.cumplida ? '✓' : '✗'} {b.texto}</li>
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

      <p className="nota">Pulsa «Nuevo paciente» para practicar con otro caso.</p>
    </div>
  )
}
