import { useEffect, useRef, useState } from 'react'

const SR = typeof window !== 'undefined' ? window.SpeechRecognition || window.webkitSpeechRecognition : null

const MENSAJES = {
  'not-allowed': 'Permite el micrófono en el navegador para poder dictar.',
  'service-not-allowed': 'El navegador no permite el reconocimiento de voz.',
  'no-speech': 'No se oyó nada. Inténtalo de nuevo.',
  'audio-capture': 'No se encontró un micrófono.',
  network: 'El reconocimiento de voz necesita conexión a internet.',
}

export function useDictado({ lang = 'es-SV', onTexto, onEscuchando }) {
  const [escuchando, setEscuchando] = useState(false)
  const [error, setError] = useState('')
  const rec = useRef(null)
  const soportado = Boolean(SR)

  function cambiar(v) {
    setEscuchando(v)
    onEscuchando?.(v)
  }

  function iniciar(idioma = lang) {
    if (!SR || escuchando) return
    try {
      const r = new SR()
      r.lang = idioma
      r.interimResults = true
      r.continuous = false
      r.onstart = () => {
        setError('')
        cambiar(true)
      }
      r.onresult = (e) => {
        const texto = Array.from(e.results)
          .map((x) => x[0].transcript)
          .join(' ')
          .trim()
        const isFinal = e.results[e.results.length - 1].isFinal
        onTexto?.(texto, isFinal)
      }
      r.onerror = (e) => {
        if (e.error === 'language-not-supported' && idioma !== 'es-MX') {
          return iniciar('es-MX') // respaldo
        }
        setError(MENSAJES[e.error] || `Error de voz: ${e.error}`)
      }
      r.onend = () => cambiar(false)
      rec.current = r
      r.start()
    } catch (err) {
      setError('No se pudo iniciar el micrófono.')
      cambiar(false)
    }
  }

  function detener() {
    rec.current?.stop()
  }

  useEffect(() => () => rec.current?.abort(), [])

  return { soportado, escuchando, error, iniciar, detener }
}
