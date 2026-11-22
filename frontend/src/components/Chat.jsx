import { useEffect, useRef, useState } from 'react'
import { urlAudioPaciente } from '../api.js'
import { renderWithGlossaryTips } from './GlossaryTip.jsx'
import AnamnesisGuide from './AnamnesisGuide.jsx'

// WAV vacío para habilitar audio en móviles y navegadores con autoplay restringido
const SILENCIO =
  'data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA='

export default function Chat({
  sessionId,
  mensajes,
  enviando,
  onSend,
  nombre,
  nivel,
  guiaCubierta = [],
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

  const preguntasUsadas = mensajes.filter((m) => m.role === 'user').length
  const maxPreguntas = nivel?.max_preguntas || null
  const preguntasRestantes = maxPreguntas !== null ? Math.max(0, maxPreguntas - preguntasUsadas) : null
  const limiteAlcanzado = maxPreguntas !== null && preguntasRestantes === 0

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
      return
    }

    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current = null
    }

    const miPedido = ++pedido.current
    setErrorVoz('')
    setCargandoAudioIdx(idx)

    const audio = new Audio(urlAudioPaciente(sessionId, contenido))
    audioRef.current = audio

    audio.onended = () => {
      if (pedido.current === miPedido) setReproduciendoIdx(null)
    }
    audio.onerror = () => {
      if (pedido.current === miPedido) {
        setReproduciendoIdx(null)
        setCargandoAudioIdx(null)
        setErrorVoz('No se pudo reproducir la voz.')
      }
    }

    const prom = audio.play()
    if (prom && typeof prom.then === 'function') {
      prom
        .then(() => {
          if (pedido.current === miPedido) {
            setCargandoAudioIdx(null)
            setReproduciendoIdx(idx)
          }
        })
        .catch((err) => {
          if (pedido.current === miPedido) {
            setCargandoAudioIdx(null)
            setReproduciendoIdx(null)
            if (err.name === 'NotAllowedError') {
              setErrorVoz('Pulsa el botón de volumen para escuchar al paciente.')
            }
          }
        })
    } else {
      setCargandoAudioIdx(null)
      setReproduciendoIdx(idx)
    }
  }

  function desbloquearAudioNavegador() {
    try {
      const a = new Audio(SILENCIO)
      a.volume = 0
      const p = a.play()
      if (p && typeof p.then === 'function') p.catch(() => {})
    } catch {}
  }

  function enviar(e) {
    e.preventDefault()
    const t = texto.trim()
    if (!t || enviando || limiteAlcanzado) return
    desbloquearAudioNavegador()
    setTexto('')
    onSend(t)
  }

  const pistasPermitidas = nivel?.pistas?.permitidas !== false
  const penalizacionPista = nivel?.pistas?.penalizacion ?? 0.5
  const textoBotonPista =
    penalizacionPista === 0 ? '💡 Pedir pista (gratis)' : '💡 Pedir pista (−0,5 pts)'

  return (
    <div className="chat-layout-wrapper">
      <div className="chat">
        <div className="chat-topbar">
          <div className="chat-level-badge">
            <span className={`nivel-pill nivel-${nivel?.id || 2}`}>
              Nivel {nivel?.id || 2} · {nivel?.nombre || 'Intermedio'}
            </span>
            {maxPreguntas !== null && (
              <span
                className={`preguntas-counter ${preguntasRestantes <= 3 ? 'warning' : ''} ${limiteAlcanzado ? 'limit-reached' : ''}`}
                aria-live="polite"
              >
                Preguntas: <strong>{preguntasUsadas} / {maxPreguntas}</strong>
                {preguntasRestantes <= 3 && preguntasRestantes > 0 && (
                  <span className="quedan-tag">¡Te quedan {preguntasRestantes}!</span>
                )}
              </span>
            )}
          </div>

          <div className="chat-controls-right">
            {errorVoz && <span className="error-voz">{errorVoz}</span>}
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
              {autoVoz ? '🔊 Voz activa' : '🔇 Silenciada'}
            </button>
          </div>
        </div>

        {limiteAlcanzado && (
          <div className="limite-preguntas-banner" role="alert">
            🛑 <strong>Alcanzaste el límite de preguntas de este nivel.</strong> Pulsa «Terminar y diagnosticar» para emitir tu conclusión.
          </div>
        )}

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
            placeholder={limiteAlcanzado ? 'Límite alcanzado. Pulsa Terminar y diagnosticar.' : 'Escribe tu pregunta al paciente…'}
            maxLength={1000}
            disabled={enviando || limiteAlcanzado}
            autoFocus
          />
          {pistasPermitidas && onPedirPista && (
            <button
              type="button"
              className="btn btn-pista"
              onClick={onPedirPista}
              disabled={enviando || cargandoPista}
              title={penalizacionPista === 0 ? 'Pedir orientación clínica sin descuento de puntaje' : 'Pedir orientación clínica (−0,5 puntos)'}
            >
              {cargandoPista ? 'Pidiendo…' : textoBotonPista}
            </button>
          )}
          <button className="btn primary" disabled={enviando || !texto.trim() || limiteAlcanzado}>
            Enviar
          </button>
        </form>
      </div>

      {nivel?.guia_anamnesis && (
        <AnamnesisGuide items={nivel.guia_anamnesis} cubiertos={guiaCubierta} />
      )}
    </div>
  )
}
