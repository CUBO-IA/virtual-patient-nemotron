import React, { useState } from 'react'
import { explicarDecision } from '../api.js'

/** Botón «¿Por qué?»: pide al backend la explicación de una decisión y la muestra debajo. */
export default function PorQue({ sessionId, tipo, id }) {
  const [estado, setEstado] = useState('cerrado') // cerrado | cargando | listo | error
  const [datos, setDatos] = useState(null)
  const [abierto, setAbierto] = useState(false)

  if (!sessionId || !id) return null

  async function cargar() {
    setEstado('cargando')
    try {
      setDatos(await explicarDecision(sessionId, tipo, id))
      setEstado('listo')
    } catch {
      setEstado('error')
    }
  }

  function alternar() {
    if (abierto) return setAbierto(false)
    setAbierto(true)
    if (!datos) cargar()
  }

  const sinModelo = estado === 'listo' && datos && !datos.explicacion

  return (
    <>
      <button type="button" className="btn-porque" onClick={alternar} aria-expanded={abierto}>
        <i className="bi bi-question-circle" /> ¿Por qué?
      </button>
      {abierto && (
        <div className="porque-panel" role="region" aria-live="polite" aria-busy={estado === 'cargando'}>
          {estado === 'cargando' && <p className="porque-nota">Pensando la explicación…</p>}
          {(estado === 'error' || sinModelo) && (
            <p className="porque-nota">
              {sinModelo && datos.fuentes.length > 0
                ? 'El modelo no está disponible para redactar la explicación; estas son las fuentes encontradas.'
                : 'No pude obtener la explicación ahora (el modelo de lenguaje no respondió).'}{' '}
              <button type="button" className="btn-porque" onClick={cargar}>
                Reintentar
              </button>
            </p>
          )}
          {estado === 'listo' && datos?.explicacion && (
            <>
              <p className="porque-explicacion">{datos.explicacion}</p>
              {datos.fuentes.length > 0 && (
                <details className="porque-fuentes">
                  <summary>Fuentes ({datos.fuentes.length})</summary>
                  {datos.fuentes.map((f, i) => (
                    <blockquote key={i}>
                      <strong>[{i + 1}] {f.fuente}</strong>
                      <br />
                      {f.fragmento}
                    </blockquote>
                  ))}
                </details>
              )}
              <p className="porque-aviso">
                {datos.origen === 'guia'
                  ? 'Explicación generada con IA a partir de guías clínicas; contenido sin validar por un profesional.'
                  : 'Explicación generada con IA como apoyo educativo (sin guía clínica que la respalde); contenido sin validar por un profesional.'}
              </p>
            </>
          )}
          {sinModelo && datos.fuentes.length > 0 && (
            <details className="porque-fuentes" open>
              <summary>Fuentes ({datos.fuentes.length})</summary>
              {datos.fuentes.map((f, i) => (
                <blockquote key={i}>
                  <strong>[{i + 1}] {f.fuente}</strong>
                  <br />
                  {f.fragmento}
                </blockquote>
              ))}
            </details>
          )}
        </div>
      )}
    </>
  )
}
