async function apiError(r) {
  let detalle = `Error ${r.status}`
  try {
    const j = await r.json()
    if (typeof j.detail === 'string') detalle = j.detail
  } catch {
    /* sin cuerpo JSON */
  }
  return new Error(detalle)
}

export async function obtenerHealth() {
  const r = await fetch('/api/health')
  if (!r.ok) throw await apiError(r)
  return r.json()
}

export async function crearSesion() {
  const r = await fetch('/api/sessions', { method: 'POST' })
  if (!r.ok) throw await apiError(r)
  return r.json()
}

// Envía un mensaje y llama onToken(texto) por cada fragmento (SSE sobre fetch).
export async function enviarMensaje(sessionId, message, onToken) {
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
    }
  }
}

export async function terminarConsulta(sessionId, diagnostico) {
  const r = await fetch(`/api/sessions/${sessionId}/finish`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ diagnostico_estudiante: diagnostico }),
  })
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
