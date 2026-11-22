import { useEffect, useRef, useState } from 'react'
import {
  crearSesion,
  esSesionPerdida,
  enviarMensaje,
  obtenerCatalogoPruebas,
  obtenerFormulario,
  obtenerHealth,
  obtenerNiveles,
  pedirPista,
  pedirPruebas,
  terminarConsulta,
} from './api.js'
import Chat from './components/Chat.jsx'
import PatientCard from './components/PatientCard.jsx'
import Results from './components/Results.jsx'
import Disclaimer from './components/Disclaimer.jsx'
import LevelSelect from './components/LevelSelect.jsx'
import Progress from './components/Progress.jsx'
import UrgenciasPanel from './components/UrgenciasPanel.jsx'
import Intro from './intro/Intro.jsx'
import PruebasPanel from './components/PruebasPanel.jsx'
import PlanForm, { PLAN_VACIO, planParaEnviar, validarPlan } from './components/PlanForm.jsx'
import {
  cargarProgreso,
  estaNivelDesbloqueado,
  registrarConsulta,
  setModoDemo,
} from './progress.js'

const CLAVE_INTRO = 'pv_intro_vista'

/** La introducción se muestra al abrir la app (una vez por sesión del navegador). ?intro=1 la fuerza y ?intro=0 la omite. */
function debeMostrarIntro() {
  try {
    const p = new URLSearchParams(window.location.search).get('intro')
    if (p === '1') return true
    if (p === '0') return false
    return sessionStorage.getItem(CLAVE_INTRO) !== '1'
  } catch {
    return true
  }
}

export default function App() {
  const [intro, setIntro] = useState(debeMostrarIntro)
  const cerrarIntro = () => {
    try {
      sessionStorage.setItem(CLAVE_INTRO, '1')
    } catch {
      /* sin almacenamiento: se mostrará de nuevo la próxima vez */
    }
    setIntro(false)
  }
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

  // Animación del paciente y voz (ANIMACIONES.md)
  const [audioSonando, setAudioSonando] = useState(false)
  const [escuchando, setEscuchando] = useState(false)
  const [entrando, setEntrando] = useState(false)

  // Pruebas y plan de tratamiento (SEGUIMIENTO.md)
  const [tabConsulta, setTabConsulta] = useState('entrevista') // entrevista | pruebas
  const [catalogoPruebas, setCatalogoPruebas] = useState(null)
  const [formulario, setFormulario] = useState(null)
  const [pruebasEstado, setPruebasEstado] = useState(null)
  const [pidiendoPruebas, setPidiendoPruebas] = useState(false)
  const [pasoCierre, setPasoCierre] = useState(1) // 1 = diagnóstico, 2 = plan
  const [plan, setPlan] = useState(PLAN_VACIO)

  // Niveles y estado
  const [configNiveles, setConfigNiveles] = useState({ niveles: [], desbloqueo: {} })
  const [nivelSeleccionado, setNivelSeleccionado] = useState(1)
  const [modoDemo, setModoDemoState] = useState(false)

  // Health
  const [healthInfo, setHealthInfo] = useState(null)
  const [healthWarning, setHealthWarning] = useState('')
  // Vista previa: se fuerza con ?vista_previa=1 o se activa sola cuando no hay modelo de lenguaje
  const [vistaPreviaForzada] = useState(
    () => new URLSearchParams(window.location.search).get('vista_previa') === '1',
  )
  const sesionActual = useRef(null)

  useEffect(() => {
    // Cargar progreso inicial
    const prog = cargarProgreso()
    setModoDemoState(prog.modo_demo)

    // Consultar health
    comprobarHealth()

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

  /** Consulta /api/health. Se usa al abrir la app y en «Reintentar conexión» del modo vista previa. */
  function comprobarHealth() {
    setHealthWarning('')
    return obtenerHealth()
      .then((data) => {
        setHealthInfo(data)
        if (!data.ollama) {
          setHealthWarning('Ollama no está disponible (puerto 11434).')
        } else if (!data.modelo_disponible) {
          setHealthWarning(`El modelo «${data.modelo}» no está descargado en Ollama (ollama pull ${data.modelo}).`)
        } else if (!data.datos) {
          setHealthWarning('Faltan archivos de datos de pacientes o casos en el servidor.')
        } else if (!data.niveles) {
          setHealthWarning('Falta archivo data/niveles.json en el servidor.')
        }
      })
      .catch(() => {
        setHealthInfo(null)
        setHealthWarning('No se pudo conectar con el servidor backend (FastAPI :8000).')
      })
  }

  function manejarToggleDemo(val) {
    setModoDemoState(val)
    setModoDemo(val)
  }

  async function iniciarConsulta(nivelId = null, casoId = null, modo = 'consulta') {
    const nivelTarget = nivelId || nivelSeleccionado || 1
    setCargando(true)
    setError('')
    try {
      const opciones = { nivel: nivelTarget, modo }
      if (casoId) opciones.caso_id = casoId

      const s = await crearSesion(opciones)
      sesionActual.current = s.session_id
      setSesion(s)
      // En vista previa no hay modelo: se muestran dos mensajes de ejemplo (solo locales, no se envían)
      setMensajes(
        vistaPrevia
          ? [
              { role: 'user', content: 'Buenas tardes, ¿qué le trae por aquí?', ejemplo: true },
              { role: 'assistant', content: s.motivo_consulta, ejemplo: true },
            ]
          : [],
      )
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
      setTabConsulta('entrevista')
      setPasoCierre(1)
      setPlan(PLAN_VACIO)
      setEntrando(true)
      setTimeout(() => setEntrando(false), 1000)

      // Módulos de pruebas y plan: solo si el caso los activa (validado, o modo demostración del servidor)
      const cfgPruebas = s.modulos?.pruebas
      setPruebasEstado(
        cfgPruebas
          ? {
              resultados: [],
              pruebas_usadas: 0,
              limite: cfgPruebas.max ?? null,
              costo_total: 0,
              presupuesto: cfgPruebas.presupuesto ?? null,
              presupuesto_restante: cfgPruebas.presupuesto ?? null,
              mostrar_costo: Boolean(cfgPruebas.mostrar_costo),
            }
          : null,
      )
      if (cfgPruebas && !catalogoPruebas) {
        obtenerCatalogoPruebas().then(setCatalogoPruebas).catch((e) => setError(e.message))
      }
      if (s.modulos?.plan && !formulario) {
        obtenerFormulario().then(setFormulario).catch((e) => setError(e.message))
      }
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
      if (esSesionPerdida(e)) {
        setError('La consulta ya no está disponible en el servidor (se reinició o caducó). Tu progreso anterior sigue guardado.')
        setFase('inicio')
        setSesion(null)
      } else {
        setError(e.message)
      }
    } finally {
      setCargandoPista(false)
    }
  }

  async function solicitarPrueba(pruebaId) {
    if (!sesion || pidiendoPruebas) return
    const id = sesion.session_id
    setPidiendoPruebas(true)
    setError('')
    try {
      const res = await pedirPruebas(id, [pruebaId])
      if (sesionActual.current !== id) return
      setPruebasEstado((prev) => {
        const nuevos = res.resultados
        const resto = (prev?.resultados || []).filter((r) => !nuevos.some((n) => n.id === r.id))
        return { ...res, resultados: [...nuevos, ...resto] }
      })
    } catch (e) {
      if (sesionActual.current === id) {
        if (esSesionPerdida(e)) {
          setError('La consulta ya no está disponible en el servidor (se reinició o caducó). Tu progreso anterior sigue guardado.')
          setFase('inicio')
          setSesion(null)
        } else {
          setError(e.message)
        }
      }
    } finally {
      setPidiendoPruebas(false)
    }
  }

  async function enviar(texto) {
    if (vistaPrevia) return // sin modelo de lenguaje no se envían mensajes
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
          if (donePayload.texto_voz) {
            // La voz pronuncia con la aspiración aunque en pantalla (nivel 1) el texto vaya con ortografía normal
            setMensajes((m) => m.map((x, i) => (i === m.length - 1 ? { ...x, voz: donePayload.texto_voz } : x)))
          }
        }
      )
    } catch (e) {
      if (sesionActual.current === id) {
        if (esSesionPerdida(e)) {
          setError('La consulta ya no está disponible en el servidor (se reinició o caducó). Tu progreso anterior sigue guardado.')
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

  const necesitaPlan = Boolean(sesion?.modulos?.plan)

  /** Valida diagnóstico y diferenciales en el cliente. Devuelve la lista de diferenciales (o null) o undefined si hay error. */
  function validarDiagnostico() {
    if (!diagnostico.trim()) return undefined
    const reqDiferenciales = sesion?.nivel?.diferenciales_requeridos || 0
    if (reqDiferenciales === 0) return null

    const d1 = diferencial1.trim()
    const d2 = diferencial2.trim()
    if (!d1 || !d2) {
      setError('En nivel Avanzado debes ingresar ambos diagnósticos diferenciales.')
      return undefined
    }
    if (d1.toLowerCase() === d2.toLowerCase()) {
      setError('Los diagnósticos diferenciales no pueden ser repetidos.')
      return undefined
    }
    if (d1.toLowerCase() === diagnostico.trim().toLowerCase() || d2.toLowerCase() === diagnostico.trim().toLowerCase()) {
      setError('Los diagnósticos diferenciales no pueden ser idénticos al diagnóstico principal.')
      return undefined
    }
    return [d1, d2]
  }

  async function terminar(e) {
    e.preventDefault()
    const difs = validarDiagnostico()
    if (difs === undefined) return

    // Con el módulo de plan activo, el cierre tiene dos pasos: diagnóstico y luego plan.
    if (necesitaPlan && pasoCierre === 1) {
      setError('')
      setPasoCierre(2)
      return
    }
    if (necesitaPlan) {
      const msg = validarPlan(plan)
      if (msg) {
        setError(msg)
        return
      }
    }

    setCargando(true)
    setError('')

    // Verificar estado de desbloqueo previo para detectar nuevos logros (§7.2)
    const n2Antes = estaNivelDesbloqueado(2, configNiveles.desbloqueo).desbloqueado
    const n3Antes = estaNivelDesbloqueado(3, configNiveles.desbloqueo).desbloqueado

    try {
      const res = await terminarConsulta(
        sesion.session_id,
        diagnostico.trim(),
        difs,
        necesitaPlan ? planParaEnviar(plan) : null,
      )
      setResultado(res)

      // Guardar consulta en progreso local
      const d = res.desglose || {}
      registrarConsulta({
        nivel: res.nivel?.id || sesion?.nivel?.id || 1,
        caso_id: res.caso_id,
        diagnostico_real: res.diagnostico_real,
        puntaje: res.puntaje,
        diagnostico_correcto: res.diagnostico_correcto,
        pistas_usadas: res.pistas_usadas,
        preguntas_usadas: res.preguntas_usadas,
        pruebas_puntaje: d.pruebas?.maximo > 0 ? d.pruebas.obtenido : null,
        plan_puntaje: d.plan?.maximo > 0 ? d.plan.obtenido : null,
        alertas_seguridad: res.plan ? (res.alertas_seguridad || []).length : null,
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
      if (esSesionPerdida(err)) {
        setError('La consulta ya no está disponible en el servidor (se reinició o caducó). Tu progreso anterior sigue guardado.')
        setFase('inicio')
        setSesion(null)
      } else {
        setError(err.message)
      }
    } finally {
      setCargando(false)
    }
  }

  // Sin Ollama (o sin el modelo) la app sigue siendo navegable: solo se bloquea el envío de mensajes.
  const sinLLM = Boolean(healthInfo && (!healthInfo.ollama || !healthInfo.modelo_disponible))
  const vistaPrevia = vistaPreviaForzada || sinLLM

  const rev = sesion?.revision_clinica
  const hayModulos = Boolean(sesion?.modulos?.pruebas || sesion?.modulos?.plan)

  // Estado del paciente derivado (ANIMACIONES.md §3)
  const ultimo = mensajes[mensajes.length - 1]
  const hayTokens = ultimo?.role === 'assistant' && ((ultimo.content && ultimo.content.length > 0) || (ultimo.voz && ultimo.voz.length > 0))
  const estadoPaciente =
    entrando ? 'entrando'
    : fase === 'resultados' ? 'despedida'
    : audioSonando ? 'hablando'
    : enviando ? (hayTokens ? 'hablando' : 'pensando')
    : escuchando ? 'escuchando'
    : 'reposo'

  const expresion = /dolor|duele|c[oó]lico|molest/i.test(sesion?.motivo_consulta || '') ? 'dolor' : 'neutral'

  return (
    <div className="app">
      {intro && <Intro onTerminar={cerrarIntro} />}
      <header className="topbar">
        <div className="brand">
          <div className="brand-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M12 2v20M2 12h20" />
            </svg>
          </div>
          <h1>Paciente <span className="brand-accent">Virtual</span></h1>
          {healthInfo && (
            <span
              className={`status-badge ${healthInfo.ok && !vistaPrevia ? 'ok' : 'warn'}`}
              title={
                vistaPrevia
                  ? 'Modo vista previa: el paciente no responde'
                  : healthInfo.ok
                    ? `Ollama conectado (${healthInfo.modelo})`
                    : healthWarning || 'Problema de conexión con Ollama'
              }
            >
              <i className="bi bi-circle-fill status-dot" /> {vistaPrevia ? 'Vista previa' : healthInfo.ok ? 'En línea' : 'Sin LLM'}
            </span>
          )}
        </div>

        <div className="topbar-actions">
          <button type="button" className="btn" onClick={() => setIntro(true)} title="Ver la introducción">
            <i className="bi bi-film" /> Intro
          </button>
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
              <i className="bi bi-bar-chart-line" /> Mi progreso
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

      {vistaPrevia && (
        <div className="vista-previa-banner" role="status">
          <div>
            <strong>Modo vista previa.</strong>{' '}
            {sinLLM
              ? `${healthWarning || 'No hay modelo de lenguaje disponible.'} `
              : 'Activado con ?vista_previa=1. '}
            Puedes recorrer toda la interfaz (niveles, pruebas, plan y resultados), pero el paciente no responde y no se envían mensajes.
          </div>
          {sinLLM && (
            <button type="button" className="btn" onClick={comprobarHealth}>
              Reintentar conexión
            </button>
          )}
        </div>
      )}
      {/* Sin modelo, el aviso ya es el banner de vista previa; los demás problemas se siguen mostrando como error */}
      {healthWarning && !sinLLM && <div className="error" role="alert">{healthWarning}</div>}
      {error && <div className="error" role="alert">{error}</div>}

      {/* Pantalla 1: Selector de niveles (§6.2) */}
      {fase === 'inicio' && healthInfo?.urgencias && (
        <div className="urgencias-inicio">
          <div>
            <strong><i className="bi bi-heart-pulse" /> Modo Urgencias</strong>
            <p>Práctica aparte: reconoce señales de alarma y decide la prioridad en poco tiempo.</p>
          </div>
          <button type="button" className="btn" disabled={cargando} onClick={() => iniciarConsulta(1, null, 'urgencias')}>
            Empezar
          </button>
        </div>
      )}
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
            estado={estadoPaciente}
            expresion={expresion}
          />

          <section className="panel main">
            {sesion.modo === 'urgencias' ? (
              <UrgenciasPanel
                key={sesion.session_id}
                sesion={sesion}
                mensajes={mensajes}
                enviando={enviando}
                onSend={enviar}
                pista={pista}
                onPedirPista={solicitarPista}
                onCerrarPista={() => setPista(null)}
                cargandoPista={cargandoPista}
                onVozEstado={setAudioSonando}
                onEscuchando={setEscuchando}
                vistaPrevia={vistaPrevia}
                onNueva={() => iniciarConsulta(1, null, 'urgencias')}
                onSalir={() => setFase('inicio')}
              />
            ) : <>
            {hayModulos && rev && (
              <p className={`revision-aviso ${rev.contenido_sin_validar ? 'sin-validar' : 'validado'}`} role="note">
                {rev.contenido_sin_validar
                  ? 'Contenido de pruebas y plan sin validar clínicamente (modo demostración).'
                  : `Caso validado por ${rev.revisado_por}.`}
              </p>
            )}

            {fase === 'chat' && (
              <>
                {sesion.modulos?.pruebas && (
                  <div className="tabs-consulta" role="tablist" aria-label="Secciones de la consulta">
                    <button
                      type="button"
                      role="tab"
                      aria-selected={tabConsulta === 'entrevista'}
                      className={`tab ${tabConsulta === 'entrevista' ? 'activa' : ''}`}
                      onClick={() => setTabConsulta('entrevista')}
                    >
                      Entrevista
                    </button>
                    <button
                      type="button"
                      role="tab"
                      aria-selected={tabConsulta === 'pruebas'}
                      className={`tab ${tabConsulta === 'pruebas' ? 'activa' : ''}`}
                      onClick={() => setTabConsulta('pruebas')}
                    >
                      Pruebas{pruebasEstado?.pruebas_usadas ? ` (${pruebasEstado.pruebas_usadas})` : ''}
                    </button>
                  </div>
                )}

                {/* El chat se mantiene montado (solo oculto) para no perder el audio ni el desplazamiento */}
                <div hidden={tabConsulta !== 'entrevista'}>
                  <Chat
                    sessionId={sesion.session_id}
                    mensajes={mensajes}
                    enviando={enviando}
                    onSend={enviar}
                    sinEnvio={vistaPrevia}
                    nombre={sesion.paciente.nombre}
                    nivel={sesion.nivel}
                    guiaCubierta={guiaCubierta}
                    pista={pista}
                    onPedirPista={solicitarPista}
                    onCerrarPista={() => setPista(null)}
                    cargandoPista={cargandoPista}
                    onVozEstado={setAudioSonando}
                    onEscuchando={setEscuchando}
                  />
                </div>

                {tabConsulta === 'pruebas' && sesion.modulos?.pruebas && pruebasEstado && (
                  <PruebasPanel
                    catalogo={catalogoPruebas}
                    estado={pruebasEstado}
                    nivelId={sesion.nivel?.id}
                    onPedir={solicitarPrueba}
                    pidiendo={pidiendoPruebas}
                  />
                )}

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
                {necesitaPlan && (
                  <p className="paso-cierre" aria-live="polite">
                    Paso {pasoCierre} de 2 · {pasoCierre === 1 ? 'Diagnóstico' : 'Plan de tratamiento'}
                  </p>
                )}

                {pasoCierre === 1 && (
                  <>
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
                        placeholder="Escribe el diagnóstico que sospechas…"
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
                            placeholder="Primer diagnóstico diferencial…"
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
                            placeholder="Segundo diagnóstico diferencial…"
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
                        {necesitaPlan
                          ? 'Continuar al plan de tratamiento →'
                          : cargando
                            ? 'Evaluando desempeño…'
                            : 'Entregar diagnóstico y ver evaluación'}
                      </button>
                    </div>
                  </>
                )}

                {pasoCierre === 2 && (
                  <>
                    <h2>Plan de tratamiento</h2>
                    <p className="diag-sub">
                      Indica qué harías con el paciente: disposición, medicamentos e indicaciones.
                    </p>
                    <PlanForm formulario={formulario} plan={plan} onChange={setPlan} />
                    <div className="actions">
                      <button type="button" className="btn" onClick={() => setPasoCierre(1)} disabled={cargando}>
                        ← Volver al diagnóstico
                      </button>
                      <button className="btn primary" disabled={cargando || !formulario}>
                        {cargando ? 'Evaluando desempeño…' : 'Entregar y ver evaluación'}
                      </button>
                    </div>
                  </>
                )}
              </form>
            )}
            </>}

            {fase === 'resultados' && resultado && (
              <Results
                r={resultado}
                sessionId={sesion?.session_id}
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
