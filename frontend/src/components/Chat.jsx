import { useEffect, useRef, useState } from 'react'

export default function Chat({
  mensajes,
  enviando,
  onSend,
  nombre,
  pista,
  onPedirPista,
  onCerrarPista,
  cargandoPista,
}) {
  const [texto, setTexto] = useState('')
  const fin = useRef(null)

  useEffect(() => {
    fin.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [mensajes])

  function enviar(e) {
    e.preventDefault()
    const t = texto.trim()
    if (!t || enviando) return
    setTexto('')
    onSend(t)
  }

  return (
    <div className="chat">
      <div className="mensajes" aria-live="polite">
        {mensajes.length === 0 && (
          <p className="vacio">
            El paciente espera. Empieza la entrevista con un saludo y tu primera pregunta.
          </p>
        )}
        {mensajes.map((m, i) => (
          <div key={i} className={`msg ${m.role === 'user' ? 'yo' : 'paciente'}`}>
            <span className="quien">{m.role === 'user' ? 'Tú' : nombre}</span>
            <p>{m.content || '…'}</p>
          </div>
        ))}
        <div ref={fin} />
      </div>

      {pista && (
        <div className="pista-box" role="region" aria-label="Pista clínica">
          <div className="pista-header">
            <span className="pista-title">
              💡 <strong>Pista {pista.nivel ? `(Nivel ${pista.nivel}/3)` : ''}</strong>
            </span>
            {onCerrarPista && (
              <button
                type="button"
                className="pista-close"
                onClick={onCerrarPista}
                title="Cerrar pista"
              >
                ×
              </button>
            )}
          </div>
          <p className="pista-texto">{pista.texto}</p>
        </div>
      )}

      <form className="entrada" onSubmit={enviar}>
        <input
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          placeholder="Escribe tu pregunta al paciente…"
          maxLength={1000}
          disabled={enviando}
          autoFocus
        />
        {onPedirPista && (
          <button
            type="button"
            className="btn btn-pista"
            onClick={onPedirPista}
            disabled={enviando || cargandoPista}
            title="Pedir una pista de qué preguntar sin revelar el diagnóstico"
          >
            💡 {cargandoPista ? 'Pidiendo…' : 'Pedir pista'}
          </button>
        )}
        <button className="btn primary" disabled={enviando || !texto.trim()}>
          Enviar
        </button>
      </form>
    </div>
  )
}
