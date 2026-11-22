import React from 'react'

export default function AnamnesisGuide({ items = [], cubiertos = [] }) {
  if (!items || items.length === 0) return null

  const cubiertosSet = new Set(cubiertos)
  const total = items.length
  const completados = items.filter((it) => cubiertosSet.has(it.id)).length

  return (
    <aside className="anamnesis-guide" aria-label="Guía de anamnesis">
      <div className="anamnesis-header">
        <div className="anamnesis-title">
          📋 <strong>Guía de anamnesis</strong>
        </div>
        <span className="anamnesis-badge">
          {completados} / {total} temas
        </span>
      </div>
      <p className="anamnesis-desc">
        Estructura recomendada de la entrevista. Se marcarán conforme explores cada área:
      </p>
      <ul className="anamnesis-list">
        {items.map((it) => {
          const hecho = cubiertosSet.has(it.id)
          return (
            <li key={it.id} className={`anamnesis-item ${hecho ? 'cubierto' : ''}`}>
              <span className="anamnesis-check" aria-hidden="true">
                {hecho ? '✓' : '○'}
              </span>
              <span className="anamnesis-texto">{it.texto}</span>
            </li>
          )
        })}
      </ul>
    </aside>
  )
}
