import { useEffect, useRef, useState } from 'react'

export default function Chat({ mensajes, enviando, onSend, nombre }) {
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
        {mensajes.length === 0 && <p className="vacio">El paciente espera. Empieza la entrevista con un saludo y tu primera pregunta.</p>}
        {mensajes.map((m, i) => (
          <div key={i} className={`msg ${m.role === 'user' ? 'yo' : 'paciente'}`}>
            <span className="quien">{m.role === 'user' ? 'Tú' : nombre}</span>
            <p>{m.content || '…'}</p>
          </div>
        ))}
        <div ref={fin} />
      </div>
      <form className="entrada" onSubmit={enviar}>
        <input value={texto} onChange={(e) => setTexto(e.target.value)} placeholder="Escribe tu pregunta al paciente…" maxLength={1000} disabled={enviando} autoFocus />
        <button className="btn primary" disabled={enviando || !texto.trim()}>Enviar</button>
      </form>
    </div>
  )
}
