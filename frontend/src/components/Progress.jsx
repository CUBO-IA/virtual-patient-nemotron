import React, { useRef, useState } from 'react'
import {
  borrarProgreso,
  cargarProgreso,
  exportarProgresoArchivo,
  importarProgresoArchivo,
  obtenerEstadisticasNivel,
} from '../progress.js'

const TOTAL_CASOS_CATALOGO = 8

export default function Progress({ onVolver, niveles = [] }) {
  const [progreso, setProgreso] = useState(cargarProgreso())
  const [mensaje, setMensaje] = useState(null)
  const fileInputRef = useRef(null)

  function refrescar() {
    setProgreso(cargarProgreso())
  }

  function manejarBorrar() {
    if (window.confirm('¿Seguro que deseas reiniciar tu progreso? Se perderá el historial local de consultas.')) {
      borrarProgreso()
      refrescar()
      setMensaje('Progreso reiniciado correctamente.')
      setTimeout(() => setMensaje(null), 3000)
    }
  }

  function manejarImportar(e) {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = (event) => {
      try {
        importarProgresoArchivo(event.target.result)
        refrescar()
        setMensaje('Progreso importado con éxito.')
        setTimeout(() => setMensaje(null), 3000)
      } catch (err) {
        alert(err.message)
      }
    }
    reader.readAsText(file)
    e.target.value = ''
  }

  // Mapa de enfermedades ya vistas (§6.2)
  const mapaVistas = {}
  progreso.historial.forEach((h) => {
    if (!mapaVistas[h.caso_id]) {
      mapaVistas[h.caso_id] = {
        caso_id: h.caso_id,
        nombre: h.diagnostico_real || 'Enfermedad clínica',
        mejorPuntaje: h.puntaje,
        veces: 1,
      }
    } else {
      mapaVistas[h.caso_id].veces += 1
      if (h.puntaje > mapaVistas[h.caso_id].mejorPuntaje) {
        mapaVistas[h.caso_id].mejorPuntaje = h.puntaje
      }
    }
  })

  const vistasLista = Object.values(mapaVistas)
  const noVistasCount = Math.max(0, TOTAL_CASOS_CATALOGO - vistasLista.length)

  return (
    <div className="progress-screen panel">
      <div className="progress-header">
        <div>
          <h2>Mi progreso de <span className="title-accent">aprendizaje</span></h2>
          <p className="progress-subtitle">
            Seguimiento de tu evolución en razonamiento clínico y dominio de casos.
          </p>
        </div>
        <button type="button" className="btn" onClick={onVolver}>
          ← Volver
        </button>
      </div>

      {mensaje && (
        <div className="info-banner" role="status">
          <i className="bi bi-check-circle-fill" /> {mensaje}
        </div>
      )}

      {/* Resumen por niveles */}
      <div className="progress-stats-grid">
        {niveles.map((n) => {
          const stats = obtenerEstadisticasNivel(n.id)
          return (
            <div key={n.id} className="stat-card">
              <div className="stat-header">
                <strong>Nivel {n.id}: {n.nombre}</strong>
                <span className="stat-sub">«{n.lema}»</span>
              </div>
              <div className="stat-body">
                <div>Consultas: <strong>{stats.consultas}</strong></div>
                <div>Promedio: <strong>{stats.promedio !== null ? stats.promedio : '—'}</strong></div>
                <div>Mejor puntaje: <strong>{stats.mejorPuntaje !== null ? stats.mejorPuntaje : '—'}</strong></div>
                <div>
                  Diagnósticos acertados:{' '}
                  <strong>{stats.tasaCorrectos !== null ? `${stats.tasaCorrectos}%` : '—'}</strong>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Mapa de enfermedades */}
      <section className="enfermedades-section">
        <h3><i className="bi bi-map" /> Mapa de enfermedades ({vistasLista.length} / {TOTAL_CASOS_CATALOGO} descubiertas)</h3>
        <p className="enfermedades-desc">
          Enfermedades a las que te has enfrentado en consulta. Obtén 80 o más puntos para considerarla dominada:
        </p>
        <div className="enfermedades-grid">
          {vistasLista.map((enf) => {
            const dominada = enf.mejorPuntaje >= 80
            return (
              <div key={enf.caso_id} className={`enfermedad-card ${dominada ? 'dominada' : ''}`}>
                <div className="enfermedad-top">
                  <span className="enf-status">
                    {dominada ? (
                      <>
                        <i className="bi bi-star-fill" /> Dominada
                      </>
                    ) : (
                      <>
                        <i className="bi bi-heart-pulse" /> En práctica
                      </>
                    )}
                  </span>
                  <span className="enf-score">{enf.mejorPuntaje} pts</span>
                </div>
                <div className="enfermedad-nombre">{enf.nombre}</div>
                <div className="enfermedad-veces">Atendido {enf.veces} {enf.veces === 1 ? 'vez' : 'veces'}</div>
              </div>
            )
          })}
          {Array.from({ length: noVistasCount }).map((_, idx) => (
            <div key={`novista-${idx}`} className="enfermedad-card misterio">
              <div className="misterio-icon">
                <i className="bi bi-question-circle" />
              </div>
              <div className="misterio-title">Caso por descubrir</div>
              <div className="misterio-desc">Sigue practicando para encontrarlo</div>
            </div>
          ))}
        </div>
      </section>

      {/* Tabla de historial */}
      <section className="historial-section">
        <h3>Historial de consultas ({progreso.historial.length})</h3>
        {progreso.historial.length === 0 ? (
          <p className="sin-historial">Aún no has completado ninguna consulta médica.</p>
        ) : (
          <div className="table-wrapper">
            <table className="historial-tabla">
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Nivel</th>
                  <th>Diagnóstico real</th>
                  <th>Resultado</th>
                  <th>Puntaje</th>
                  <th>Pistas</th>
                  <th>Preguntas</th>
                </tr>
              </thead>
              <tbody>
                {[...progreso.historial].reverse().map((item, idx) => (
                  <tr key={idx}>
                    <td>{new Date(item.fecha).toLocaleString()}</td>
                    <td>
                      <span className={`tag-nivel nivel-${item.nivel}`}>
                        Nivel {item.nivel}
                      </span>
                    </td>
                    <td><strong>{item.diagnostico_real || item.caso_id}</strong></td>
                    <td>
                      <span className={`badge-acierto ${item.diagnostico_correcto ? 'ok' : 'fallo'}`}>
                        {item.diagnostico_correcto ? (
                          <>
                            <i className="bi bi-check-lg" /> Acertado
                          </>
                        ) : (
                          <>
                            <i className="bi bi-x-lg" /> Incorrecto
                          </>
                        )}
                      </span>
                    </td>
                    <td><strong>{item.puntaje}</strong> pts</td>
                    <td>{item.pistas_usadas}</td>
                    <td>{item.preguntas_usadas}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Acciones de respaldo */}
      <div className="progress-actions">
        <button type="button" className="btn" onClick={exportarProgresoArchivo}>
          <i className="bi bi-download" /> Exportar progreso (JSON)
        </button>

        <button type="button" className="btn" onClick={() => fileInputRef.current?.click()}>
          <i className="bi bi-upload" /> Importar progreso
        </button>
        <input
          type="file"
          accept=".json"
          ref={fileInputRef}
          style={{ display: 'none' }}
          onChange={manejarImportar}
        />

        <button type="button" className="btn danger" onClick={manejarBorrar}>
          <i className="bi bi-trash3" /> Reiniciar mi progreso
        </button>
      </div>
    </div>
  )
}
