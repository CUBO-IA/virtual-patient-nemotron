import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import Escena from './Escena.jsx'
import Diapositivas from './Diapositivas.jsx'
import { crearMusica } from './musica.js'
import './intro.css'

const CLAVE_SILENCIO = 'pv_intro_silencio'

// Línea de tiempo (milisegundos desde que empieza la escena).
const FASES = {
  lee: { duracion: 7500, siguiente: 'hallazgo' },
  hallazgo: { duracion: 4500, siguiente: 'destello' },
  destello: { duracion: 1900, siguiente: 'diapositivas' },
}

const TEXTOS = {
  lee: 'Mañana empiezo mis prácticas… ¿y si no sé qué hacer frente a un paciente de verdad?',
  hallazgo: '¿Y esto…? ¡Pacientes virtuales para practicar sin miedo!',
}
const SUBTITULOS = {
  lee: 'La noche antes de las prácticas…',
  hallazgo: 'Entonces, encuentra algo en su computadora.',
}

function leerSilencio() {
  try {
    return localStorage.getItem(CLAVE_SILENCIO) === '1'
  } catch {
    return false
  }
}

/** Escribe el texto letra por letra (desactivado si el usuario prefiere menos movimiento). */
function useMaquina(texto, activo, reducir) {
  const [n, setN] = useState(0)
  useEffect(() => {
    if (!texto || !activo) return undefined
    if (reducir) {
      setN(texto.length)
      return undefined
    }
    setN(0)
    const t = window.setInterval(() => setN((v) => (v >= texto.length ? v : v + 1)), 45)
    return () => window.clearInterval(t)
  }, [texto, activo, reducir])
  return texto ? texto.slice(0, n) : ''
}

/**
 * Introducción: pantalla de inicio → escena nocturna → destello → dos diapositivas.
 * `onTerminar` se llama cuando la persona pulsa «Comenzar» (o salta la introducción).
 */
export default function Intro({ onTerminar }) {
  const reducir = useMemo(() => window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false, [])
  const [fase, setFase] = useState(reducir ? 'diapositivas' : 'inicio')
  const [silencio, setSilencio] = useState(leerSilencio)
  const [sonidoDisponible, setSonidoDisponible] = useState(true)
  const musica = useRef(null)
  if (!musica.current) musica.current = crearMusica()

  const texto = useMaquina(TEXTOS[fase], true, reducir)
  const enEscena = fase in FASES

  // Avance automático de la escena.
  useEffect(() => {
    const cfg = FASES[fase]
    if (!cfg) return undefined
    const t = window.setTimeout(() => setFase(cfg.siguiente), cfg.duracion)
    return () => window.clearTimeout(t)
  }, [fase])

  // El destello suena en el instante en que la pantalla se enciende del todo.
  useEffect(() => {
    if (fase === 'destello') musica.current.destello()
    if (fase === 'diapositivas') musica.current.modo('esperanza')
  }, [fase])

  useEffect(() => () => musica.current.detener(0.3), [])

  // Mientras la introducción está abierta, la página de atrás no se desplaza.
  useEffect(() => {
    const anterior = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = anterior
    }
  }, [])

  const empezar = useCallback(
    async (conSonido) => {
      if (conSonido) {
        musica.current.silenciar(silencio)
        const ok = await musica.current.iniciar()
        if (!ok) setSonidoDisponible(false)
      } else {
        setSilencio(true)
      }
      setFase('lee')
    },
    [silencio],
  )

  const saltar = useCallback(() => {
    musica.current.modo('esperanza')
    setFase('diapositivas')
  }, [])

  const terminar = useCallback(() => {
    musica.current.detener(1.2)
    onTerminar()
  }, [onTerminar])

  function alternarSilencio() {
    const nuevo = !silencio
    setSilencio(nuevo)
    musica.current.silenciar(nuevo)
    try {
      localStorage.setItem(CLAVE_SILENCIO, nuevo ? '1' : '0')
    } catch {
      /* sin almacenamiento: no pasa nada */
    }
  }

  useEffect(() => {
    function tecla(e) {
      if (e.key === 'Escape' && fase !== 'diapositivas') saltar()
      if (e.key === 'Escape' && fase === 'diapositivas') terminar()
    }
    window.addEventListener('keydown', tecla)
    return () => window.removeEventListener('keydown', tecla)
  }, [fase, saltar, terminar])

  const expresion = fase === 'hallazgo' ? 'sorpresa' : fase === 'destello' ? 'feliz' : 'preocupado'

  return (
    <div className={`intro fase-${fase}`} role="dialog" aria-modal="true" aria-label="Introducción a Paciente Virtual">
      {fase !== 'inicio' && fase !== 'diapositivas' && (
        <div className="intro-escenario">
          <Escena
            expresion={expresion}
            portatilAbierto={fase === 'hallazgo' || fase === 'destello'}
            pantallaOn={fase === 'hallazgo' || fase === 'destello'}
            gota={fase === 'lee'}
          />
          {TEXTOS[fase] && (
            <p className="intro-globo" aria-live="polite">
              {texto}
              <span className="intro-cursor" aria-hidden="true" />
            </p>
          )}
          {SUBTITULOS[fase] && <p className="intro-subtitulos">{SUBTITULOS[fase]}</p>}
          <div className="intro-flash" aria-hidden="true" />
        </div>
      )}

      {fase === 'inicio' && (
        <div className="intro-bienvenida">
          <div className="intro-luna" aria-hidden="true" />
          <h1 className="intro-titulo pequeno">
            Paciente <em>Virtual</em>
          </h1>
          <p className="intro-lema">Una pequeña historia antes de empezar.</p>
          <div className="intro-acciones">
            <button type="button" className="intro-boton" onClick={() => empezar(true)} autoFocus>
              <i className="bi bi-music-note-beamed" /> Comenzar con música
            </button>
            <button type="button" className="intro-boton secundario" onClick={() => empezar(false)}>
              Sin sonido
            </button>
          </div>
          <button type="button" className="intro-enlace" onClick={terminar}>
            Saltar introducción
          </button>
        </div>
      )}

      {fase === 'diapositivas' && <Diapositivas onComenzar={terminar} />}

      {fase !== 'inicio' && (
        <div className="intro-controles">
          {sonidoDisponible && !reducir && (
            <button
              type="button"
              className="intro-icono"
              onClick={alternarSilencio}
              aria-pressed={silencio}
              aria-label={silencio ? 'Activar música' : 'Silenciar música'}
              title={silencio ? 'Activar música' : 'Silenciar música'}
            >
              <i className={`bi ${silencio ? 'bi-volume-mute-fill' : 'bi-volume-up-fill'}`} />
            </button>
          )}
          {enEscena && (
            <button type="button" className="intro-icono texto" onClick={saltar}>
              Saltar <i className="bi bi-skip-forward-fill" />
            </button>
          )}
          {fase === 'diapositivas' && (
            <button type="button" className="intro-icono texto" onClick={terminar}>
              Ir a la app <i className="bi bi-x-lg" />
            </button>
          )}
        </div>
      )}
    </div>
  )
}
