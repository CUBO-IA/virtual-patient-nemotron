import { useEffect, useRef, useState } from 'react'
import { crearSesion, enviarMensaje, obtenerHealth, pedirPista, terminarConsulta } from './api.js'
import Chat from './components/Chat.jsx'
import PatientCard from './components/PatientCard.jsx'
import Results from './components/Results.jsx'
import Disclaimer from './components/Disclaimer.jsx'

export default function App() {
  const [sesion, setSesion] = useState(null)
  const [mensajes, setMensajes] = useState([])
  const [fase, setFase] = useState('inicio') // inicio | chat | diagnostico | resultados
  const [verPaciente, setVerPaciente] = useState(false)
  const [enviando, setEnviando] = useState(false)
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState('')
  const [diagnostico, setDiagnostico] = useState('')
  const [resultado, setResultado] = useState(null)
  const [pista, setPista] = useState(null)
  const [cargandoPista, setCargandoPista] = useState(false)
  const [pistasUsadas, setPistasUsadas] = useState(0)
  const [healthInfo, setHealthInfo] = useState(null)
  const [healthWarning, setHealthWarning] = useState('')
  const sesionActual = useRef(null)

  useEffect(() => {
    obtenerHealth()
      .then((data) => {
        setHealthInfo(data)
        if (!data.ollama) {
          setHealthWarning('Ollama no está disponible (puerto 11434). El paciente virtual no podrá responder hasta que inicies Ollama.')
        } else if (!data.modelo_disponible) {
          setHealthWarning(`El modelo «${data.modelo}» no está descargado en Ollama. Ejecuta: ollama pull ${data.modelo}`)
        } else if (!data.datos) {
          setHealthWarning('Faltan archivos de datos de pacientes o casos en el servidor.')
        }
      })
      .catch(() => {
        setHealthWarning('No se pudo conectar con el servidor backend (FastAPI :8000).')
      })
  }, [])

  async function nuevoPaciente() {
    setCargando(true)
    setError('')
    try {
      const s = await crearSesion()
      sesionActual.current = s.session_id
      setSesion(s)
      setMensajes([])
      setVerPaciente(false)
      setDiagnostico('')
      setResultado(null)
      setPista(null)
      setPistasUsadas(0)
      setEnviando(false)
      setFase('chat')
    } catch (e) {
      setError(e.message)
    } finally {
      setCargando(false)
    }
  }

  async function solicitarPista() {
    if (!sesion || enviando) return
    setCargandoPista(true)
    try {
      const res = await pedirPista(sesion.session_id)
      setPista({ texto: res.pista, nivel: res.nivel, disponible: res.disponible })
      setPistasUsadas(res.pistas_usadas)
    } catch (e) {
      setError(e.message)
    } finally {
      setCargandoPista(false)
    }
  }

  async function enviar(texto) {
    const id = sesion.session_id
    setError('')
    setEnviando(true)
    setMensajes((m) => [...m, { role: 'user', content: texto }, { role: 'assistant', content: '' }])
    try {
      await enviarMensaje(id, texto, (tok) => {
        if (sesionActual.current !== id) return
        setMensajes((m) => m.map((x, i) => (i === m.length - 1 ? { ...x, content: x.content + tok } : x)))
      })
    } catch (e) {
      if (sesionActual.current === id) {
        setError(e.message)
        setMensajes((m) => (m.length && m[m.length - 1].content === '' ? m.slice(0, -2) : m))
      }
    } finally {
      if (sesionActual.current === id) setEnviando(false)
    }
  }

  async function terminar(e) {
    e.preventDefault()
    setCargando(true)
    setError('')
    try {
      setResultado(await terminarConsulta(sesion.session_id, diagnostico))
      setFase('resultados')
    } catch (err) {
      setError(err.message)
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <h1>Paciente Virtual</h1>
          {healthInfo && (
            <span
              className={`status-badge ${healthInfo.ok ? 'ok' : 'warn'}`}
              title={
                healthInfo.ok
                  ? `Ollama conectado (${healthInfo.modelo})`
                  : healthWarning || 'Problema de conexión con Ollama'
              }
            >
              ● {healthInfo.ok ? 'En línea' : 'Sin LLM'}
            </span>
          )}
        </div>
        <button className="btn primary" onClick={nuevoPaciente} disabled={cargando || enviando}>
          Nuevo paciente
        </button>
      </header>
      <Disclaimer />

      {healthWarning && <div className="error" role="alert">{healthWarning}</div>}
      {error && <div className="error" role="alert">{error}</div>}

      {fase === 'inicio' && (
        <section className="panel intro">
          <h2>Practica tu entrevista clínica</h2>
          <p>
            Pulsa <strong>Nuevo paciente</strong>, hazle preguntas por chat, descubre qué tiene y confirma tu
            diagnóstico al final.
          </p>
        </section>
      )}

      {sesion && fase !== 'inicio' && (
        <main className="layout">
          <PatientCard paciente={sesion.paciente} motivo={sesion.motivo_consulta} ver={verPaciente} onToggle={() => setVerPaciente((v) => !v)} />

          <section className="panel main">
            {fase === 'chat' && (
              <>
                <Chat
                  mensajes={mensajes}
                  enviando={enviando}
                  onSend={enviar}
                  nombre={sesion.paciente.nombre}
                  pista={pista}
                  onPedirPista={solicitarPista}
                  onCerrarPista={() => setPista(null)}
                  cargandoPista={cargandoPista}
                />
                <div className="actions">
                  <button className="btn" onClick={() => setFase('diagnostico')} disabled={enviando || mensajes.length === 0}>
                    Terminar y diagnosticar
                  </button>
                </div>
              </>
            )}

            {fase === 'diagnostico' && (
              <form onSubmit={terminar} className="diag">
                <h2>¿Cuál es tu diagnóstico?</h2>
                <textarea value={diagnostico} onChange={(e) => setDiagnostico(e.target.value)} rows={3} maxLength={500} placeholder="Escribe tu diagnóstico presuntivo…" autoFocus />
                <div className="actions">
                  <button type="button" className="btn" onClick={() => setFase('chat')} disabled={cargando}>Volver al chat</button>
                  <button className="btn primary" disabled={cargando || !diagnostico.trim()}>
                    {cargando ? 'Evaluando…' : 'Ver evaluación'}
                  </button>
                </div>
              </form>
            )}

            {fase === 'resultados' && resultado && <Results r={resultado} diagnosticoEstudiante={diagnostico} />}
          </section>
        </main>
      )}
    </div>
  )
}
