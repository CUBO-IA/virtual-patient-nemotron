async function apiError(r) {
  let detalle = `Error ${r.status}`
  try {
    const j = await r.json()
    if (typeof j.detail === 'string') detalle = j.detail
  } catch {
    /* sin cuerpo JSON */
  }
  const err = new Error(detalle)
  err.status = r.status // el código HTTP, para decidir sin depender del texto del mensaje
  return err
}

/** 404 «Sesión no encontrada»: el servidor ya no conoce la consulta (se borró o caducó). */
export function esSesionPerdida(e) {
  return e?.status === 404 && /sesi[oó]n/i.test(e.message || '')
}

export async function obtenerHealth() {
  const r = await fetch('/api/health')
  if (!r.ok) throw await apiError(r)
  return r.json()
}

export async function obtenerNiveles() {
  const r = await fetch('/api/niveles')
  if (!r.ok) throw await apiError(r)
  return r.json()
}

export async function crearSesion(opciones = {}) {
  const r = await fetch('/api/sessions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(opciones),
  })
  if (!r.ok) throw await apiError(r)
  return r.json()
}

// Envía un mensaje y llama onToken(texto) por cada fragmento, y onDone(payload) al terminar (SSE sobre fetch).
export async function enviarMensaje(sessionId, message, onToken, onDone) {
  const r = await fetch(`/api/sessions/${sessionId}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  })
  if (!r.ok) throw await apiError(r)

  const reader = r.body.getReader()
  const decoder = new TextDecoder()
  let buf = ''
  for (;;) {
    const { value, done } = await reader.read()
    if (done) break
    buf += decoder.decode(value, { stream: true })
    const eventos = buf.split('\n\n')
    buf = eventos.pop()
    for (const ev of eventos) {
      let nombre = 'message'
      let datos = ''
      for (const linea of ev.split('\n')) {
        if (linea.startsWith('event:')) nombre = linea.slice(6).trim()
        else if (linea.startsWith('data:')) datos += linea.slice(5).trim()
      }
      if (!datos) continue
      const payload = JSON.parse(datos)
      if (nombre === 'error') throw new Error(payload.error)
      if (payload.token) onToken(payload.token)
      if (payload.done && onDone) onDone(payload)
    }
  }
}

export async function obtenerCatalogoPruebas() {
  const r = await fetch('/api/catalogo/pruebas')
  if (!r.ok) throw await apiError(r)
  return r.json()
}

export async function obtenerFormulario() {
  const r = await fetch('/api/catalogo/formulario')
  if (!r.ok) throw await apiError(r)
  return r.json()
}

/** Solicita pruebas (tanda «todo o nada»). Una prueba repetida no cuesta ni cuenta de nuevo. */
export async function pedirPruebas(sessionId, ids) {
  const r = await fetch(`/api/sessions/${sessionId}/pruebas`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ids }),
  })
  if (!r.ok) throw await apiError(r)
  return r.json()
}

export async function terminarConsulta(sessionId, diagnostico, diferenciales = null, plan = null) {
  const body = { diagnostico_estudiante: diagnostico }
  if (diferenciales) {
    body.diferenciales = diferenciales
  }
  if (plan) {
    body.plan = plan
  }
  const r = await fetch(`/api/sessions/${sessionId}/finish`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!r.ok) throw await apiError(r)
  return r.json()
}

export async function enviarTriaje(sessionId, prioridad, accion) {
  const r = await fetch(`/api/sessions/${sessionId}/triaje`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ prioridad, accion }) })
  if (!r.ok) throw await apiError(r)
  return r.json()
}

export async function pedirPista(sessionId) {
  const r = await fetch(`/api/sessions/${sessionId}/pista`, { method: 'POST' })
  if (!r.ok) throw await apiError(r)
  return r.json()
}

export async function obtenerGlosario() {
  const r = await fetch('/api/glosario')
  if (!r.ok) throw await apiError(r)
  return r.json()
}

/** URL que el elemento <audio> puede cargar solo. play() tiene que llamarse en el clic, sin un fetch previo. */
export function urlAudioPaciente(sessionId, texto) {
  return `/api/sessions/${encodeURIComponent(sessionId)}/tts?texto=${encodeURIComponent(texto)}`
}

// «¿Por qué?»: explicación de una decisión (solo tras terminar la consulta)
export async function explicarDecision(sessionId, tipo, id) {
  const r = await fetch(`/api/sessions/${sessionId}/explicar`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tipo, id }),
  })
  if (!r.ok) throw await apiError(r)
  return r.json()
}
