import { useEffect, useRef, useState } from 'react'
import {
  crearSesion,
  enviarMensaje,
  obtenerHealth,
  obtenerNiveles,
  pedirPista,
  terminarConsulta,
} from './api.js'
import Chat from './components/Chat.jsx'
import PatientCard from './components/PatientCard.jsx'
import Results from './components/Results.jsx'
import Disclaimer from './components/Disclaimer.jsx'
import LevelSelect from './components/LevelSelect.jsx'
import Progress from './components/Progress.jsx'
import {
  cargarProgreso,
  estaNivelDesbloqueado,
  registrarConsulta,
  setModoDemo,
} from './progress.js'

export default function App() {
  const [sesion, setSesion] = useState(null)
  const [mensajes, setMensajes] = useState([])
  const [fase, setFase] = useState('inicio') // inicio | chat | diagnostico | resultados | progreso
  const [verPaciente, setVerPaciente] = useState(false)
  const [enviando, setEnviando] = useState(false)
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState('')

  // Diagnósticos
  const [diagnostico, setDiagnostico] = useState('')
  const [diferencial1, setDiferencial1] = useState('')
  const [diferencial2, setDiferencial2] = useState('')
  const [resultado, setResultado] = useState(null)
  const [desbloqueoNuevo, setDesbloqueoNuevo] = useState(null)

  // Pistas y guía
  const [pista, setPista] = useState(null)
  const [cargandoPista, setCargandoPista] = useState(false)
  const [pistasUsadas, setPistasUsadas] = useState(0)
  const [guiaCubierta, setGuiaCubierta] = useState([])

  // Niveles y estado
  const [configNiveles, setConfigNiveles] = useState({ niveles: [], desbloqueo: {} })
  const [nivelSeleccionado, setNivelSeleccionado] = useState(1)
  const [modoDemo, setModoDemoState] = useState(false)

  // Health
  const [healthInfo, setHealthInfo] = useState(null)
  const [healthWarning, setHealthWarning] = useState('')
  const sesionActual = useRef(null)

  useEffect(() => {
    // Cargar progreso inicial
    const prog = cargarProgreso()
    setModoDemoState(prog.modo_demo)

    // Consultar health
    obtenerHealth()
      .then((data) => {
        setHealthInfo(data)
        if (!data.ollama) {
          setHealthWarning('Ollama no está disponible (puerto 11434). El paciente virtual no podrá responder hasta que inicies Ollama.')
        } else if (!data.modelo_disponible) {
          setHealthWarning(`El modelo «${data.modelo}» no está descargado en Ollama. Ejecuta: ollama pull ${data.modelo}`)
        } else if (!data.datos) {
          setHealthWarning('Faltan archivos de datos de pacientes o casos en el servidor.')
        } else if (!data.niveles) {
          setHealthWarning('Falta archivo data/niveles.json en el servidor.')
        }
      })
      .catch(() => {
        setHealthWarning('No se pudo conectar con el servidor backend (FastAPI :8000).')
      })

    // Cargar configuración de niveles
    obtenerNiveles()
      .then((data) => {
        setConfigNiveles(data)
        if (data.nivel_por_defecto && !data.niveles.some((n) => n.id === nivelSeleccionado)) {
          setNivelSeleccionado(data.nivel_por_defecto)
        }
      })
      .catch((e) => {
        console.warn('No se pudieron cargar los niveles:', e)
      })
  }, [])

  function manejarToggleDemo(val) {
    setModoDemoState(val)
    setModoDemo(val)
  }

  async function iniciarConsulta(nivelId = null, casoId = null) {
    const nivelTarget = nivelId || nivelSeleccionado || 1
    setCargando(true)
    setError('')
    try {
      const opciones = { nivel: nivelTarget }
      if (casoId) opciones.caso_id = casoId

      const s = await crearSesion(opciones)
      sesionActual.current = s.session_id
      setSesion(s)
      setMensajes([])
      setVerPaciente(false)
      setDiagnostico('')
      setDiferencial1('')
      setDiferencial2('')
      setResultado(null)
      setPista(null)
      setPistasUsadas(0)
      setGuiaCubierta([])
      setDesbloqueoNuevo(null)
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
      if (e.message.includes('404')) {
        setError('La consulta se perdió porque el servidor se reinició. Tu progreso anterior sigue guardado.')
        setFase('inicio')
        setSesion(null)
      } else {
        setError(e.message)
      }
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
      await enviarMensaje(
        id,
        texto,
        (tok) => {
          if (sesionActual.current !== id) return
          setMensajes((m) => m.map((x, i) => (i === m.length - 1 ? { ...x, content: x.content + tok } : x)))
        },
        (donePayload) => {
          if (sesionActual.current !== id) return
          if (donePayload.guia_cubierta) {
            setGuiaCubierta(donePayload.guia_cubierta)
          }
        }
      )
    } catch (e) {
      if (sesionActual.current === id) {
        if (e.message.includes('404')) {
          setError('La consulta se perdió porque el servidor se reinició. Tu progreso anterior sigue guardado.')
          setFase('inicio')
          setSesion(null)
        } else {
          setError(e.message)
          setMensajes((m) => (m.length && m[m.length - 1].content === '' ? m.slice(0, -2) : m))
        }
      }
    } finally {
      if (sesionActual.current === id) setEnviando(false)
    }
  }

  async function terminar(e) {
    e.preventDefault()
    if (!diagnostico.trim()) return

    const reqDiferenciales = sesion?.nivel?.diferenciales_requeridos || 0
    let difs = null

    if (reqDiferenciales > 0) {
      const d1 = diferencial1.trim()
      const d2 = diferencial2.trim()
      if (!d1 || !d2) {
        setError('En nivel Avanzado debes ingresar ambos diagnósticos diferenciales.')
        return
      }
      if (d1.toLowerCase() === d2.toLowerCase()) {
        setError('Los diagnósticos diferenciales no pueden ser repetidos.')
        return
      }
      if (d1.toLowerCase() === diagnostico.trim().toLowerCase() || d2.toLowerCase() === diagnostico.trim().toLowerCase()) {
        setError('Los diagnósticos diferenciales no pueden ser idénticos al diagnóstico principal.')
        return
      }
      difs = [d1, d2]
    }

    setCargando(true)
    setError('')

    // Verificar estado de desbloqueo previo para detectar nuevos logros (§7.2)
    const n2Antes = estaNivelDesbloqueado(2, configNiveles.desbloqueo).desbloqueado
    const n3Antes = estaNivelDesbloqueado(3, configNiveles.desbloqueo).desbloqueado

    try {
      const res = await terminarConsulta(sesion.session_id, diagnostico.trim(), difs)
      setResultado(res)

      // Guardar consulta en progreso local
      registrarConsulta({
        nivel: res.nivel?.id || sesion?.nivel?.id || 1,
        caso_id: res.caso_id,
        diagnostico_real: res.diagnostico_real,
        puntaje: res.puntaje,
        diagnostico_correcto: res.diagnostico_correcto,
        pistas_usadas: res.pistas_usadas,
        preguntas_usadas: res.preguntas_usadas,
      })

      // Verificar si se desbloqueó un nivel nuevo
      const n2Despues = estaNivelDesbloqueado(2, configNiveles.desbloqueo).desbloqueado
      const n3Despues = estaNivelDesbloqueado(3, configNiveles.desbloqueo).desbloqueado

      if (!n2Antes && n2Despues) {
        setDesbloqueoNuevo('¡Has desbloqueado el nivel Intermedio («Autónomo»)!')
      } else if (!n3Antes && n3Despues) {
        setDesbloqueoNuevo('¡Has desbloqueado el nivel Avanzado («Consulta real»)!')
      }

      setFase('resultados')
    } catch (err) {
      if (err.message.includes('404')) {
        setError('La consulta se perdió porque el servidor se reinició. Tu progreso anterior sigue guardado.')
        setFase('inicio')
        setSesion(null)
      } else {
        setError(err.message)
      }
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

        <div className="topbar-actions">
          {fase !== 'inicio' && (
            <button
              type="button"
              className="btn"
              onClick={() => {
                if (fase === 'chat' && !window.confirm('¿Deseas salir al menú de niveles? Se descartará la consulta actual.')) {
                  return
                }
                setFase('inicio')
              }}
              disabled={cargando || enviando}
            >
              Niveles
            </button>
          )}

          {fase === 'inicio' && (
            <button
              type="button"
              className="btn"
              onClick={() => setFase('progreso')}
            >
              📊 Mi progreso
            </button>
          )}

          <button
            type="button"
            className="btn primary"
            onClick={() => iniciarConsulta(nivelSeleccionado)}
            disabled={cargando || enviando}
          >
            Nuevo paciente
          </button>
        </div>
      </header>
      <Disclaimer />

      {healthWarning && <div className="error" role="alert">{healthWarning}</div>}
      {error && <div className="error" role="alert">{error}</div>}

      {/* Pantalla 1: Selector de niveles (§6.2) */}
      {fase === 'inicio' && (
        <LevelSelect
          niveles={configNiveles.niveles}
          nivelSeleccionado={nivelSeleccionado}
          onSelectNivel={(nid) => setNivelSeleccionado(nid)}
          configDesbloqueo={configNiveles.desbloqueo}
          onIniciar={(nid, cid) => iniciarConsulta(nid, cid)}
          onVerProgreso={() => setFase('progreso')}
          modoDemo={modoDemo}
          onToggleModoDemo={manejarToggleDemo}
          cargando={cargando}
        />
      )}

      {/* Pantalla: Mi progreso (§6.2) */}
      {fase === 'progreso' && (
        <Progress
          onVolver={() => setFase('inicio')}
          niveles={configNiveles.niveles}
        />
      )}

      {/* Pantallas de consulta activa */}
      {sesion && fase !== 'inicio' && fase !== 'progreso' && (
        <main className="layout">
          <PatientCard
            paciente={sesion.paciente}
            motivo={sesion.motivo_consulta}
            ver={verPaciente}
            onToggle={() => setVerPaciente((v) => !v)}
          />

          <section className="panel main">
            {fase === 'chat' && (
              <>
                <Chat
                  sessionId={sesion.session_id}
                  mensajes={mensajes}
                  enviando={enviando}
                  onSend={enviar}
                  nombre={sesion.paciente.nombre}
                  nivel={sesion.nivel}
                  guiaCubierta={guiaCubierta}
                  pista={pista}
                  onPedirPista={solicitarPista}
                  onCerrarPista={() => setPista(null)}
                  cargandoPista={cargandoPista}
                />
                <div className="actions">
                  <button
                    className="btn primary btn-terminar-consulta"
                    onClick={() => setFase('diagnostico')}
                    disabled={enviando || mensajes.length === 0}
                  >
                    Terminar y diagnosticar →
                  </button>
                </div>
              </>
            )}

            {fase === 'diagnostico' && (
              <form onSubmit={terminar} className="diag">
                <h2>Conclusión diagnóstica</h2>
                <p className="diag-sub">
                  {sesion?.nivel?.id === 3
                    ? 'Nivel Avanzado: ingresa el diagnóstico de mayor sospecha y dos alternativas clínicas para tu diagnóstico diferencial.'
                    : 'Ingresa el diagnóstico médico que sospechas tras la entrevista clínica.'}
                </p>

                <div className="form-group">
                  <label htmlFor="dx-principal">
                    <strong>Diagnóstico principal:</strong>
                  </label>
                  <input
                    id="dx-principal"
                    type="text"
                    value={diagnostico}
                    onChange={(e) => setDiagnostico(e.target.value)}
                    maxLength={500}
                    placeholder="Ej. Dengue con signos de alarma…"
                    autoFocus
                    required
                  />
                </div>

                {sesion?.nivel?.diferenciales_requeridos > 0 && (
                  <div className="diferenciales-inputs-group">
                    <h3>Diagnósticos diferenciales (obligatorios en Nivel Avanzado)</h3>
                    <div className="form-group">
                      <label htmlFor="dx-dif1">Diferencial 1:</label>
                      <input
                        id="dx-dif1"
                        type="text"
                        value={diferencial1}
                        onChange={(e) => setDiferencial1(e.target.value)}
                        maxLength={500}
                        placeholder="Ej. Chikungunya…"
                        required
                      />
                    </div>
                    <div className="form-group">
                      <label htmlFor="dx-dif2">Diferencial 2:</label>
                      <input
                        id="dx-dif2"
                        type="text"
                        value={diferencial2}
                        onChange={(e) => setDiferencial2(e.target.value)}
                        maxLength={500}
                        placeholder="Ej. Leptospirosis…"
                        required
                      />
                    </div>
                  </div>
                )}

                <div className="actions">
                  <button type="button" className="btn" onClick={() => setFase('chat')} disabled={cargando}>
                    Volver al chat
                  </button>
                  <button
                    className="btn primary"
                    disabled={
                      cargando ||
                      !diagnostico.trim() ||
                      (sesion?.nivel?.diferenciales_requeridos > 0 && (!diferencial1.trim() || !diferencial2.trim()))
                    }
                  >
                    {cargando ? 'Evaluando desempeño…' : 'Entregar diagnóstico y ver evaluación'}
                  </button>
                </div>
              </form>
            )}

            {fase === 'resultados' && resultado && (
              <Results
                r={resultado}
                diagnosticoEstudiante={diagnostico}
                diferencialesEstudiante={diferencial1 && diferencial2 ? [diferencial1, diferencial2] : []}
                desbloqueoNuevo={desbloqueoNuevo}
                onNuevoMismoNivel={() => iniciarConsulta(sesion.nivel?.id)}
                onCambiarNivel={() => setFase('inicio')}
                onVerProgreso={() => setFase('progreso')}
              />
            )}
          </section>
        </main>
      )}
    </div>
  )
}
