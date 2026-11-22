import React, { useState } from 'react'
import { explicarDecision } from '../api.js'

/** Botón «¿Por qué?»: pide al backend la explicación de una decisión y la muestra debajo. */
export default function PorQue({ sessionId, tipo, id }) {
  const [estado, setEstado] = useState('cerrado') // cerrado | cargando | listo | error
  const [datos, setDatos] = useState(null)
  const [abierto, setAbierto] = useState(false)

  if (!sessionId || !id) return null

  async function alternar() {
    if (abierto) return setAbierto(false)
    setAbierto(true)
    if (datos) return
    setEstado('cargando')
    try {
      setDatos(await explicarDecision(sessionId, tipo, id))
      setEstado('listo')
    } catch {
      setEstado('error')
    }
  }

  return (
    <>
      <button type="button" className="btn-porque" onClick={alternar} aria-expanded={abierto}>
        <i className="bi bi-question-circle" /> ¿Por qué?
      </button>
      {abierto && (
        <div className="porque-panel" role="region" aria-live="polite">
          {estado === 'cargando' && <p className="porque-nota">Buscando en las guías…</p>}
          {estado === 'error' && <p className="porque-nota">No pude obtener la explicación. Inténtalo de nuevo.</p>}
          {estado === 'listo' && datos && (
            <>
              {datos.explicacion && <p>{datos.explicacion}</p>}
              {!datos.explicacion && datos.nota && <p>{datos.nota}</p>}
              {datos.explicacion && datos.nota && <p className="porque-nota">Nota del caso: {datos.nota}</p>}
              {!datos.explicacion && !datos.nota && datos.fuentes.length === 0 && (
                <p className="porque-nota">
                  No hay una guía cargada que respalde esta decisión, así que no puedo explicarla con fuentes.
                </p>
              )}
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
              {datos.origen === 'guia' && (
                <p className="porque-aviso">
                  Explicación generada con IA a partir de guías clínicas; contenido sin validar por un profesional.
                </p>
              )}
            </>
          )}
        </div>
      )}
    </>
  )
}
