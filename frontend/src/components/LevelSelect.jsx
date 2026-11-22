import React, { useState } from 'react'
import {
  estaNivelDesbloqueado,
  obtenerEstadisticasNivel,
  obtenerPuntoDebil,
} from '../progress.js'

export default function LevelSelect({
  niveles = [],
  nivelSeleccionado = 1,
  onSelectNivel,
  configDesbloqueo = {},
  onIniciar,
  onVerProgreso,
  modoDemo = false,
  onToggleModoDemo,
  cargando = false,
}) {
  const [puntoDebilInfo, setPuntoDebilInfo] = useState(null)

  function manejarPuntoDebil() {
    const casoPuntoDebil = obtenerPuntoDebil(nivelSeleccionado, [
      'c_dengue_01', 'c_dm2_01', 'c_gea_01', 'c_nac_01', 'c_hta_01', 'c_trauma_01', 'c_erc_01', 'c_depresion_01'
    ])
    if (casoPuntoDebil) {
      onIniciar(nivelSeleccionado, casoPuntoDebil)
    } else {
      setPuntoDebilInfo('Aún no tienes suficiente historial en este nivel para identificar tu punto débil.')
      setTimeout(() => setPuntoDebilInfo(null), 4000)
    }
  }

  const nivelActualObj = niveles.find((n) => n.id === nivelSeleccionado) || niveles[0]
  const desbloqueoActual = nivelActualObj
    ? estaNivelDesbloqueado(nivelActualObj.id, configDesbloqueo)
    : { desbloqueado: true }

  return (
    <div className="level-select-container">
      <div className="level-select-header">
        <h2>Elige tu <span className="title-accent">nivel de práctica</span></h2>
        <p className="level-select-subtitle">
          Avanza progresivamente desde una consulta guiada hasta la simulación de una consulta médica real.
        </p>

        <div className="demo-mode-bar">
          <label className="demo-toggle">
            <input
              type="checkbox"
              checked={modoDemo}
              onChange={(e) => onToggleModoDemo(e.target.checked)}
            />
            <span>
              <i className="bi bi-unlock-fill" /> Modo demostración (desbloquea todos los niveles para evaluación)
            </span>
          </label>
        </div>
      </div>

      <div className="level-cards-grid" role="radiogroup" aria-label="Nivel de dificultad">
        {niveles.map((n) => {
          const stats = obtenerEstadisticasNivel(n.id)
          const estado = estaNivelDesbloqueado(n.id, configDesbloqueo)
          const seleccionado = nivelSeleccionado === n.id
          const bloqueado = !estado.desbloqueado

          return (
            <div
              key={n.id}
              role="radio"
              aria-checked={seleccionado}
              aria-disabled={bloqueado}
              tabIndex={bloqueado ? -1 : 0}
              className={`level-card level-${n.id} ${seleccionado ? 'selected' : ''} ${bloqueado ? 'locked' : ''}`}
              onClick={() => {
                if (!bloqueado) onSelectNivel(n.id)
              }}
              onKeyDown={(e) => {
                if (!bloqueado && (e.key === 'Enter' || e.key === ' ')) {
                  e.preventDefault()
                  onSelectNivel(n.id)
                }
              }}
            >
              <div className="level-card-top">
                <div className="level-card-badge">Nivel {n.id}</div>
                {bloqueado ? (
                  <span className="lock-icon" title="Nivel bloqueado" aria-label="Bloqueado">
                    <i className="bi bi-lock-fill" />
                  </span>
                ) : (
                  <span className="level-lema">«{n.lema}»</span>
                )}
              </div>

              <h3 className="level-nombre">{n.nombre}</h3>
              <p className="level-descripcion">{n.descripcion}</p>

              <div className="level-rules">
                <div className="rule-item">
                  <span className="rule-icon"><i className="bi bi-clipboard2-pulse" /></span>
                  <span>{n.guia_anamnesis ? 'Guía de anamnesis en vivo' : 'Sin guía asistida'}</span>
                </div>
                <div className="rule-item">
                  <span className="rule-icon"><i className="bi bi-lightbulb" /></span>
                  <span>
                    {!n.pistas.permitidas
                      ? 'Sin pistas disponibles'
                      : n.pistas.penalizacion === 0
                      ? 'Pistas ilimitadas gratis'
                      : 'Pistas con −0,5 pts'}
                  </span>
                </div>
                <div className="rule-item">
                  <span className="rule-icon"><i className="bi bi-stopwatch" /></span>
                  <span>{n.max_preguntas ? `Máximo ${n.max_preguntas} preguntas` : 'Preguntas ilimitadas'}</span>
                </div>
                <div className="rule-item">
                  <span className="rule-icon"><i className="bi bi-chat-quote" /></span>
                  <span>
                    Paciente {n.actitud_paciente === 'colaborador' ? 'colaborador' : n.actitud_paciente === 'reservado' ? 'reservado (pocas palabras)' : 'habitual'}
                  </span>
                </div>
                <div className="rule-item">
                  <span className="rule-icon"><i className="bi bi-heart-pulse" /></span>
                  <span>
                    {n.diferenciales_requeridos > 0
                      ? `Diagnóstico + ${n.diferenciales_requeridos} diferenciales`
                      : 'Diagnóstico principal'}
                  </span>
                </div>
              </div>

              {bloqueado ? (
                <div className="lock-requisito" role="note">
                  <div className="lock-title">Requisito para desbloquear:</div>
                  <p>{estado.requisito}</p>
                </div>
              ) : (
                <div className="level-stats">
                  {stats.consultas > 0 ? (
                    <div className="stats-row">
                      <span>{stats.consultas} consulta{stats.consultas > 1 ? 's' : ''}</span>
                      <span>Promedio: <strong>{stats.promedio}</strong></span>
                      <span>Mejor: <strong>{stats.mejorPuntaje}</strong></span>
                    </div>
                  ) : (
                    <span className="sin-consultas">Sin consultas completadas</span>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {puntoDebilInfo && (
        <div className="info-banner" role="status">
          <i className="bi bi-info-circle-fill" /> {puntoDebilInfo}
        </div>
      )}

      <div className="level-select-actions">
        <button
          type="button"
          className="btn"
          onClick={onVerProgreso}
          title="Ver historial y mapa de enfermedades"
        >
          <i className="bi bi-bar-chart-line" /> Mi progreso
        </button>

        <button
          type="button"
          className="btn"
          onClick={manejarPuntoDebil}
          disabled={cargando || !desbloqueoActual.desbloqueado}
          title="Practicar el caso con menor puntaje registrado"
        >
          <i className="bi bi-bullseye" /> Practicar mi punto débil
        </button>

        <button
          type="button"
          className="btn primary btn-comenzar"
          disabled={cargando || !desbloqueoActual.desbloqueado}
          onClick={() => onIniciar(nivelSeleccionado)}
        >
          {cargando ? 'Iniciando sesión…' : `Iniciar consulta en nivel ${nivelActualObj?.nombre || ''}`}
        </button>
      </div>
    </div>
  )
}
