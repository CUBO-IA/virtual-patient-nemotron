// La clave conserva «v1» para no perder el progreso ya guardado; el formato interno va en `version`.
const STORAGE_KEY = 'pv_progreso_v1'
const MAX_HISTORIAL = 200
const VERSION_ACTUAL = 2 // v2: añade pruebas_puntaje, plan_puntaje y alertas_seguridad por consulta

function crearProgresoInicial() {
  return {
    version: VERSION_ACTUAL,
    creado: new Date().toISOString(),
    modo_demo: false,
    historial: [],
  }
}

/** Migra v1 -> v2: los registros antiguos reciben null en los campos nuevos. */
function migrar(progreso) {
  if (progreso.version === VERSION_ACTUAL) return progreso
  return {
    ...progreso,
    version: VERSION_ACTUAL,
    historial: progreso.historial.map((h) => ({
      pruebas_puntaje: null,
      plan_puntaje: null,
      alertas_seguridad: null,
      ...h,
    })),
  }
}

export function cargarProgreso() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return crearProgresoInicial()
    const parsed = JSON.parse(raw)
    if (parsed && (parsed.version === 1 || parsed.version === 2) && Array.isArray(parsed.historial)) {
      return migrar(parsed)
    }
  } catch (e) {
    console.warn('No se pudo leer localStorage para el progreso:', e)
  }
  return crearProgresoInicial()
}

export function guardarProgreso(progreso) {
  try {
    const seguro = {
      version: VERSION_ACTUAL,
      creado: progreso.creado || new Date().toISOString(),
      modo_demo: !!progreso.modo_demo,
      historial: (progreso.historial || []).slice(-MAX_HISTORIAL),
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(seguro))
    return true
  } catch (e) {
    console.warn('No se pudo guardar en localStorage:', e)
    return false
  }
}

export function registrarConsulta(registro) {
  const progreso = cargarProgreso()
  progreso.historial.push({
    fecha: new Date().toISOString(),
    nivel: registro.nivel || 1,
    caso_id: registro.caso_id,
    diagnostico_real: registro.diagnostico_real,
    puntaje: registro.puntaje,
    diagnostico_correcto: !!registro.diagnostico_correcto,
    pistas_usadas: registro.pistas_usadas || 0,
    preguntas_usadas: registro.preguntas_usadas || 0,
    pruebas_puntaje: registro.pruebas_puntaje ?? null,
    plan_puntaje: registro.plan_puntaje ?? null,
    alertas_seguridad: registro.alertas_seguridad ?? null,
  })
  guardarProgreso(progreso)
  return progreso
}

export function setModoDemo(activo) {
  const progreso = cargarProgreso()
  progreso.modo_demo = !!activo
  guardarProgreso(progreso)
  return progreso
}

export function obtenerEstadisticasNivel(nivelId) {
  const progreso = cargarProgreso()
  const consultas = progreso.historial.filter((h) => h.nivel === nivelId)
  if (consultas.length === 0) {
    return {
      consultas: 0,
      promedio: null,
      mejorPuntaje: null,
      correctos: 0,
      tasaCorrectos: null,
    }
  }
  const totalPuntos = consultas.reduce((acc, c) => acc + (c.puntaje || 0), 0)
  const mejor = Math.max(...consultas.map((c) => c.puntaje || 0))
  const correctos = consultas.filter((c) => c.diagnostico_correcto).length

  return {
    consultas: consultas.length,
    promedio: Math.round(totalPuntos / consultas.length),
    mejorPuntaje: mejor,
    correctos,
    tasaCorrectos: Math.round((correctos / consultas.length) * 100),
  }
}

export function estaNivelDesbloqueado(nivelId, configDesbloqueo = {}) {
  const progreso = cargarProgreso()
  if (progreso.modo_demo) {
    return { desbloqueado: true, motivo: 'Modo demostración activo' }
  }
  if (nivelId === 1) {
    return { desbloqueado: true }
  }

  const ventana = configDesbloqueo.ventana || 3
  const promedioMin = configDesbloqueo.promedio_minimo || 70
  const correctosMin = configDesbloqueo.diagnosticos_correctos_minimos || 2
  const nivelPrevio = nivelId - 1
  const prevNombre = nivelPrevio === 1 ? 'Básico' : 'Intermedio'

  const consultasPrevias = progreso.historial.filter((h) => h.nivel === nivelPrevio)

  // Comprobar si en algún momento de la historia se cumplió la ventana requerida (§7.2)
  let cumplido = false
  if (consultasPrevias.length >= ventana) {
    for (let i = 0; i <= consultasPrevias.length - ventana; i++) {
      const slice = consultasPrevias.slice(i, i + ventana)
      const prom = slice.reduce((acc, c) => acc + (c.puntaje || 0), 0) / ventana
      const corr = slice.filter((c) => c.diagnostico_correcto).length
      if (prom >= promedioMin && corr >= correctosMin) {
        cumplido = true
        break
      }
    }
  }

  if (cumplido) {
    return { desbloqueado: true }
  }

  const hechas = Math.min(consultasPrevias.length, ventana)
  return {
    desbloqueado: false,
    requisito: `Completa ${ventana} consultas del nivel ${prevNombre} con promedio ≥ ${promedioMin} y ${correctosMin} diagnósticos correctos. Llevas ${hechas}/${ventana}.`,
    progresoActual: hechas,
    ventana,
  }
}

export function obtenerPuntoDebil(nivelId, casosPermitidos = []) {
  const progreso = cargarProgreso()
  const permitidosIds = new Set(casosPermitidos.map((c) => c.id || c))

  // Buscar casos en el historial que estén dentro de los permitidos para este nivel
  const historialPermitido = progreso.historial.filter((h) => permitidosIds.has(h.caso_id))
  if (historialPermitido.length === 0) return null

  // Agrupar por caso_id para encontrar el mejor puntaje de cada uno
  const casosMap = {}
  historialPermitido.forEach((h) => {
    if (!casosMap[h.caso_id]) {
      casosMap[h.caso_id] = { caso_id: h.caso_id, mejorPuntaje: h.puntaje, ultimaFecha: h.fecha }
    } else {
      if (h.puntaje > casosMap[h.caso_id].mejorPuntaje) {
        casosMap[h.caso_id].mejorPuntaje = h.puntaje
      }
      if (new Date(h.fecha) > new Date(casosMap[h.caso_id].ultimaFecha)) {
        casosMap[h.caso_id].ultimaFecha = h.fecha
      }
    }
  })

  // Ordenar: peor mejor-puntaje ascendente; empates -> fecha más antigua
  const candidatos = Object.values(casosMap)
  candidatos.sort((a, b) => {
    if (a.mejorPuntaje !== b.mejorPuntaje) {
      return a.mejorPuntaje - b.mejorPuntaje
    }
    return new Date(a.ultimaFecha) - new Date(b.ultimaFecha)
  })

  return candidatos[0]?.caso_id || null
}

export function exportarProgresoArchivo() {
  const progreso = cargarProgreso()
  const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(progreso, null, 2))
  const a = document.createElement('a')
  a.setAttribute('href', dataStr)
  a.setAttribute('download', `progreso_paciente_virtual_${new Date().toISOString().slice(0, 10)}.json`)
  document.body.appendChild(a)
  a.click()
  a.remove()
}

export function importarProgresoArchivo(jsonString) {
  try {
    const data = JSON.parse(jsonString)
    if (!data || (data.version !== 1 && data.version !== 2) || !Array.isArray(data.historial)) {
      throw new Error('El formato del archivo de progreso no es válido.')
    }
    guardarProgreso(data)
    return true
  } catch (e) {
    throw new Error(`Error importando progreso: ${e.message}`)
  }
}

export function borrarProgreso() {
  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch (e) {
    console.warn(e)
  }
}
