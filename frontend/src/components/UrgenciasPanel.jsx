import React, { useEffect, useRef, useState } from 'react'
import Chat from './Chat.jsx'
import { enviarTriaje } from '../api.js'

const AVISO = 'Esto es una práctica con casos ficticios. En una emergencia real, llama a los servicios de emergencia de tu país.'

const PRIORIDADES = [
  { id: 'rojo', texto: 'Rojo', ayuda: 'Riesgo para la vida: atención inmediata' },
  { id: 'amarillo', texto: 'Amarillo', ayuda: 'Puede empeorar si espera: evaluación pronto' },
  { id: 'verde', texto: 'Verde', ayuda: 'Estable: puede esperar' },
]

const ACCIONES = [
  { id: 'emergencias', texto: 'Llamar a emergencias' },
  { id: 'atencion_inmediata', texto: 'Atención médica inmediata' },
  { id: 'evaluacion_pronto', texto: 'Evaluación médica pronto' },
  { id: 'consulta_normal', texto: 'Consulta normal o cuidados en casa' },
]

const etiqueta = (lista, id) => lista.find((x) => x.id === id)?.texto ?? id
const formatoTiempo = (s) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`

/** Modo Urgencias: cronómetro, chat limitado, semáforo, acción y resultado del triaje. */
export default function UrgenciasPanel({
  sesion,
  mensajes,
  enviando,
  onSend,
  pista,
  onPedirPista,
  onCerrarPista,
  cargandoPista,
  onVozEstado,
  onEscuchando,
  vistaPrevia = false,
  onNueva,
  onSalir,
}) {
  const [prioridad, setPrioridad] = useState('')
  const [accion, setAccion] = useState('')
  const [resultado, setResultado] = useState(null)
  const [enviandoTriaje, setEnviandoTriaje] = useState(false)
  const [error, setError] = useState('')
  const [restante, setRestante] = useState(sesion.tiempo_limite_seg)
  const fin = useRef(Date.now() + sesion.tiempo_limite_seg * 1000)

  const usadas = mensajes.filter((m) => m.role === 'user' && !m.ejemplo).length
  const limitePreguntas = usadas >= sesion.max_preguntas
  const sinTiempo = restante <= 0
  const puedeElegir = usadas >= sesion.preguntas_minimas_semaforo
  const chatCerrado = limitePreguntas || sinTiempo

  // El reloj se calcula contra una hora de fin (no acumula errores). El servidor aplica el mismo límite.
  useEffect(() => {
    if (resultado) return undefined
    const t = window.setInterval(() => setRestante(Math.max(0, Math.ceil((fin.current - Date.now()) / 1000))), 500)
    return () => window.clearInterval(t)
  }, [resultado])

  async function enviar() {
    setEnviandoTriaje(true)
    setError('')
    try {
      setResultado(await enviarTriaje(sesion.session_id, prioridad, accion))
    } catch (e) {
      setError(e.message)
    } finally {
      setEnviandoTriaje(false)
    }
  }

  if (resultado) return <ResultadoTriaje r={resultado} onNueva={onNueva} onSalir={onSalir} />

  return (
    <div className="urgencias">
      <p className="urgencias-aviso" role="note">
        <i className="bi bi-info-circle" /> {AVISO}
      </p>
      <p className="revision-aviso sin-validar" role="note">
        Contenido de urgencias sin validar clínicamente. Solo demostración.
      </p>

      <div
        className={`urgencias-reloj ${restante <= 30 ? 'urgencias-reloj-rojo' : ''}`}
        role="timer"
        aria-live={restante <= 30 ? 'assertive' : 'off'}
      >
        <i className="bi bi-stopwatch" /> {formatoTiempo(restante)}
        <span className="urgencias-contador">
          {usadas} de {sesion.max_preguntas} preguntas
        </span>
      </div>

      {sesion.acompanante?.relacion && (
        <p className="urgencias-acompanante">
          <i className="bi bi-people" /> Lo acompaña su {sesion.acompanante.relacion}, que a veces responde por el paciente.
        </p>
      )}

      {chatCerrado && (
        <div className="urgencias-fin" role="alert">
          {sinTiempo ? 'Se acabó el tiempo.' : 'Llegaste al límite de preguntas.'} Elige la prioridad y la acción.
        </div>
      )}

      <Chat
        sessionId={sesion.session_id}
        mensajes={mensajes}
        enviando={enviando}
        onSend={onSend}
        sinEnvio={vistaPrevia || chatCerrado}
        nombre={sesion.paciente.nombre}
        nivel={null}
        pista={pista}
        onPedirPista={onPedirPista}
        onCerrarPista={onCerrarPista}
        cargandoPista={cargandoPista}
        onVozEstado={onVozEstado}
        onEscuchando={onEscuchando}
      />

      <section className="triaje" aria-label="Decisión de prioridad">
        <h3>¿Qué prioridad tiene este paciente?</h3>
        {!puedeElegir && (
          <p className="triaje-ayuda">
            Haz al menos {sesion.preguntas_minimas_semaforo} preguntas antes de decidir ({usadas} hechas).
          </p>
        )}
        <div className="triaje-prioridades" role="radiogroup">
          {PRIORIDADES.map((p) => (
            <button
              key={p.id}
              type="button"
              role="radio"
              aria-checked={prioridad === p.id}
              className={`triaje-btn triaje-${p.id} ${prioridad === p.id ? 'elegido' : ''}`}
              disabled={!puedeElegir}
              onClick={() => setPrioridad(p.id)}
              title={p.ayuda}
            >
              <i className="bi bi-circle-fill" /> {p.texto}
            </button>
          ))}
        </div>

        <label className="triaje-accion">
          ¿Qué haría?
          <select value={accion} onChange={(e) => setAccion(e.target.value)} disabled={!puedeElegir}>
            <option value="">Selecciona…</option>
            {ACCIONES.map((a) => (
              <option key={a.id} value={a.id}>
                {a.texto}
              </option>
            ))}
          </select>
        </label>

        {error && (
          <div className="error" role="alert">
            {error}
          </div>
        )}
        <button
          type="button"
          className="btn primary"
          disabled={!prioridad || !accion || enviando || enviandoTriaje}
          onClick={enviar}
        >
          {enviandoTriaje ? 'Enviando…' : 'Enviar decisión'}
        </button>
        <p className="triaje-ayuda">Una vez enviada, no se puede cambiar.</p>
      </section>
    </div>
  )
}

function ResultadoTriaje({ r, onNueva, onSalir }) {
  const d = r.desglose || {}
  return (
    <section className="triaje-resultado" aria-live="polite">
      <h2>Resultado de la práctica</h2>
      <p className="urgencias-aviso" role="note">
        <i className="bi bi-info-circle" /> {AVISO}
      </p>

      {r.alerta_seguridad && (
        <div className="seguridad-banner" role="alert">
          <strong>
            <i className="bi bi-exclamation-triangle-fill" /> Alerta de seguridad
          </strong>
          <p>{r.alerta_seguridad}</p>
        </div>
      )}

      <p className={`triaje-veredicto ${r.aprobado ? 'ok' : 'mal'}`}>
        <strong>{r.aprobado ? 'Bien resuelto' : 'Por mejorar'}</strong> · Puntaje: <strong>{r.puntaje}</strong> / 100
      </p>

      <ul className="lista">
        <li>
          Prioridad correcta: <span className={`triaje-chip triaje-${r.prioridad_correcta}`}>{etiqueta(PRIORIDADES, r.prioridad_correcta)}</span>
          {' · '}elegiste: <span className={`triaje-chip triaje-${r.prioridad_elegida}`}>{etiqueta(PRIORIDADES, r.prioridad_elegida)}</span>
        </li>
        <li>
          Acción correcta: <strong>{etiqueta(ACCIONES, r.accion_correcta)}</strong>
          {' · '}elegiste: <strong>{etiqueta(ACCIONES, r.accion_elegida)}</strong>
        </li>
      </ul>

      <h3>Por qué</h3>
      <p>{r.explicacion}</p>

      <h3>Señales de alarma</h3>
      {r.signos.encontrados.length === 0 && r.signos.faltantes.length === 0 ? (
        <p>Este paciente no tenía señales de alarma.</p>
      ) : (
        <ul className="lista">
          {r.signos.encontrados.map((t) => (
            <li key={t} className="ok">
              <i className="bi bi-check-lg" /> {t}
            </li>
          ))}
          {r.signos.faltantes.map((t) => (
            <li key={t} className="mal">
              <i className="bi bi-x-lg" /> {t} <span className="chip">no preguntaste</span>
            </li>
          ))}
        </ul>
      )}

      {r.preguntas_esenciales.faltantes.length > 0 && (
        <p className="mal-texto">
          <strong>Preguntas que faltaron:</strong> {r.preguntas_esenciales.faltantes.join('; ')}.
        </p>
      )}

      <h3>Cómo se calculó</h3>
      <ul className="lista">
        <li>Prioridad: {d.prioridad} / 50</li>
        <li>Señales encontradas: {d.signos} / 30</li>
        <li>Preguntas esenciales: {d.esenciales} / 10</li>
        <li>Rapidez: {d.rapidez} / 10</li>
        {d.pistas !== 0 && <li>Pistas usadas ({r.pistas_usadas}): {d.pistas}</li>}
      </ul>

      <div className="acciones-resultado">
        <button type="button" className="btn primary" onClick={onNueva}>
          Otro caso de urgencias
        </button>
        <button type="button" className="btn" onClick={onSalir}>
          Volver al inicio
        </button>
      </div>
    </section>
  )
}
