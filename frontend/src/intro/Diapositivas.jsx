import React, { useEffect, useState } from 'react'

const TARJETAS = [
  {
    icono: 'bi-chat-dots-fill',
    titulo: 'Entrevista por chat y voz',
    texto: 'Conversa con pacientes que hablan con modismos salvadoreños. Dicta con tu micrófono y escucha sus respuestas.',
  },
  {
    icono: 'bi-people-fill',
    titulo: 'Pacientes con perfil real',
    texto: 'Cada paciente sale de NVIDIA Nemotron‑Personas‑El‑Salvador y vive uno de 8 casos clínicos ficticios.',
  },
  {
    icono: 'bi-clipboard2-pulse-fill',
    titulo: 'Diagnóstico, pruebas y plan',
    texto: 'Pide estudios, receta y recibe una evaluación. El botón «¿Por qué?» te explica cada decisión (con IA, sin validar).',
  },
  {
    icono: 'bi-heart-pulse-fill',
    titulo: 'Tres niveles y Urgencias',
    texto: 'Empieza con guía y pistas, y sube de nivel. En Urgencias decides la prioridad contra el reloj (demostración).',
  },
]

/** Dos diapositivas: portada y contenido. Se navega con los botones, los puntos o las flechas del teclado. */
export default function Diapositivas({ onComenzar }) {
  const [actual, setActual] = useState(0)

  useEffect(() => {
    function tecla(e) {
      if (e.key === 'ArrowRight') setActual(1)
      if (e.key === 'ArrowLeft') setActual(0)
      if (e.key === 'Enter' && actual === 1) onComenzar()
    }
    window.addEventListener('keydown', tecla)
    return () => window.removeEventListener('keydown', tecla)
  }, [actual, onComenzar])

  return (
    <div className="intro-diapositivas">
      <div className={`intro-slide intro-portada ${actual === 0 ? 'activa' : ''}`} aria-hidden={actual !== 0}>
        <div className="intro-logo" aria-hidden="true">
          <span />
          <span />
        </div>
        <p className="intro-etiqueta">Simulador de pacientes para estudiantes de medicina</p>
        <h1 className="intro-titulo">
          Paciente <em>Virtual</em>
        </h1>
        <p className="intro-lema">
          Practica la entrevista clínica con pacientes salvadoreños virtuales, antes de tu primera práctica de verdad.
        </p>
        <button type="button" className="intro-boton" onClick={() => setActual(1)} tabIndex={actual === 0 ? 0 : -1}>
          Siguiente <i className="bi bi-arrow-right" />
        </button>
        <p className="intro-aviso">Casos ficticios, solo para práctica educativa. No sustituye consejo ni diagnóstico médico.</p>
      </div>

      <div className={`intro-slide intro-contenido ${actual === 1 ? 'activa' : ''}`} aria-hidden={actual !== 1}>
        <h2 className="intro-subtitulo">¿Qué puedes hacer aquí?</h2>
        <div className="intro-tarjetas">
          {TARJETAS.map((t) => (
            <article key={t.titulo} className="intro-tarjeta">
              <i className={`bi ${t.icono}`} aria-hidden="true" />
              <h3>{t.titulo}</h3>
              <p>{t.texto}</p>
            </article>
          ))}
        </div>
        <p className="intro-nota">
          El modelo de lenguaje corre en tu propio equipo (Ollama). El contenido clínico es un borrador pendiente de revisión por
          profesionales de la salud.
        </p>
        <div className="intro-acciones">
          <button type="button" className="intro-boton secundario" onClick={() => setActual(0)} tabIndex={actual === 1 ? 0 : -1}>
            <i className="bi bi-arrow-left" /> Atrás
          </button>
          <button type="button" className="intro-boton" onClick={onComenzar} tabIndex={actual === 1 ? 0 : -1}>
            Comenzar a practicar <i className="bi bi-arrow-right" />
          </button>
        </div>
      </div>

      <div className="intro-puntos" role="tablist" aria-label="Diapositivas">
        {[0, 1].map((i) => (
          <button
            key={i}
            type="button"
            role="tab"
            aria-selected={actual === i}
            aria-label={`Diapositiva ${i + 1}`}
            className={actual === i ? 'activo' : ''}
            onClick={() => setActual(i)}
          />
        ))}
      </div>
    </div>
  )
}
