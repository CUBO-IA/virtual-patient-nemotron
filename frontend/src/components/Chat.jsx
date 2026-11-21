import { useEffect, useRef, useState } from 'react'
import { urlAudioPaciente } from '../api.js'
import { renderWithGlossaryTips } from './GlossaryTip.jsx'

// WAV vacío. Se reproduce en el clic de Enviar para que el navegador
// permita el audio automático cuando el paciente termine de responder.
const SILENCIO =
  'data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA='

export default function Chat({
  sessionId,
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
  const [autoVoz, setAutoVoz] = useState(true)
  const [reproduciendoIdx, setReproduciendoIdx] = useState(null)
  const [cargandoAudioIdx, setCargandoAudioIdx] = useState(null)
  const [errorVoz, setErrorVoz] = useState('')
  const audioRef = useRef(null)
  const pedido = useRef(0)
  const prevEnviando = useRef(enviando)
  const fin = useRef(null)

  useEffect(() => {
    fin.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [mensajes])

  // Reproducción automática de la voz cuando el paciente termina de responder
  useEffect(() => {
    if (prevEnviando.current && !enviando && autoVoz && mensajes.length > 0) {
      const ultimoIdx = mensajes.length - 1
      const ultimo = mensajes[ultimoIdx]
      if (ultimo && ultimo.role === 'assistant' && ultimo.content?.trim()) {
        reproducirAudio(ultimo.content, ultimoIdx)
      }
    }
    prevEnviando.current = enviando
  }, [enviando, autoVoz, mensajes])

  // Limpiar reproductor al desmontar componente
  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause()
        audioRef.current = null
      }
    }
  }, [])

  function reproducirAudio(contenido, idx) {
    if (!sessionId || !contenido?.trim()) return

    if (reproduciendoIdx === idx && audioRef.current && !audioRef.current.paused) {
      audioRef.current.pause()
      setReproduciendoIdx(null)
      setCargandoAudioIdx(null)
      return
    }

    const id = ++pedido.current
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current.src = ''
    }

    setErrorVoz('')
    setCargandoAudioIdx(idx)
    const audio = new Audio(urlAudioPaciente(sessionId, contenido))
    audioRef.current = audio
    audio.onplaying = () => {
      if (pedido.current !== id) return
      setCargandoAudioIdx(null)
      setReproduciendoIdx(idx)
    }
    audio.onended = () => {
      if (pedido.current !== id) return
      setReproduciendoIdx(null)
      setCargandoAudioIdx(null)
    }
    audio.onerror = () => {
      if (pedido.current !== id) return
      setCargandoAudioIdx(null)
      setReproduciendoIdx(null)
      setErrorVoz('No se pudo generar la voz. Comprueba que hay internet: usa el servicio de Microsoft Edge.')
    }
    // play() va en este mismo turno, sin await previo. Si se espera el MP3
    // antes, el navegador rechaza el audio por falta de gesto del usuario.
    const intento = audio.play()
    if (intento) {
      intento.catch((err) => {
        if (pedido.current !== id) return
        setCargandoAudioIdx(null)
        setReproduciendoIdx(null)
        if (err && err.name === 'NotAllowedError') {
          setErrorVoz('El navegador bloqueó la reproducción automática. Pulsa el botón 🔊 del mensaje para escucharlo.')
        } else {
          setErrorVoz('No se pudo reproducir el sonido. Comprueba la conexión o que el backend esté activo.')
        }
      })
    }
  }

  function enviar(e) {
    e.preventDefault()
    const t = texto.trim()
    if (!t || enviando) return
    const previo = new Audio(SILENCIO)
    previo.play().catch(() => {})
    setTexto('')
    onSend(t)
  }

  return (
    <div className="chat">
      <div className="chat-topbar">
        <button
          type="button"
          className={`btn-toggle-voz ${autoVoz ? 'activa' : ''}`}
          onClick={() => {
            if (audioRef.current) {
              audioRef.current.pause()
              setReproduciendoIdx(null)
            }
            setAutoVoz((v) => !v)
          }}
          title={autoVoz ? 'Voz automática activada (clic para silenciar)' : 'Voz silenciada (clic para activar)'}
        >
          {autoVoz ? '🔊 Voz del paciente: Activa' : '🔇 Voz del paciente: Silenciada'}
        </button>
      </div>
      {errorVoz && <p className="voz-error" role="alert">{errorVoz}</p>}

      <div className="mensajes" aria-live="polite">
        {mensajes.length === 0 && (
          <p className="vacio">
            El paciente espera. Empieza la entrevista con un saludo y tu primera pregunta.
          </p>
        )}
        {mensajes.map((m, i) => (
          <div key={i} className={`msg ${m.role === 'user' ? 'yo' : 'paciente'}`}>
            <div className="msg-header">
              <span className="quien">{m.role === 'user' ? 'Tú' : nombre}</span>
              {m.role === 'assistant' && m.content && (
                <button
                  type="button"
                  className={`btn-audio-msg ${reproduciendoIdx === i ? 'sonando' : ''}`}
                  onClick={() => reproducirAudio(m.content, i)}
                  title={reproduciendoIdx === i ? 'Pausar audio' : 'Escuchar respuesta'}
                  disabled={cargandoAudioIdx === i}
                >
                  {cargandoAudioIdx === i ? '⏳' : reproduciendoIdx === i ? '⏸️' : '🔊'}
                </button>
              )}
            </div>
            <p>
              {m.role === 'user'
                ? m.content || '…'
                : renderWithGlossaryTips(m.content) || '…'}
            </p>
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
