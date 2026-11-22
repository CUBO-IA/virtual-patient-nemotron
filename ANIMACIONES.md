# Animación del paciente y entrada de voz

Guía para que el paciente se vea "vivo" (respira, habla, siente dolor) y para que el estudiante pueda **hablarle con el micrófono**. Enfocada en lo funcional: pocas imágenes, CSS y un par de hooks de React. Sin APIs de pago.

> Adaptada a este proyecto (React + Vite, FastAPI, voz de Edge TTS). Reemplaza a `animaciones-pacientes.md`, que asumía un proyecto distinto.
>
> **Decisión: se mantiene el avatar de DiceBear (el método actual).** No hay que crear imágenes. El pixel art por arquetipos queda como opción futura (§4).

---

## 1. Qué ya existe y qué cambia

| Pieza | Hoy | Con esta guía |
|---|---|---|
| Imagen del paciente | Avatar de DiceBear (`avatar_url`), solo al activar «Ver paciente» | **Se mantiene.** Solo se anima con CSS (§5) |
| Voz del paciente | Edge TTS (`es-SV`) desde el servidor; `Chat.jsx` usa `new Audio(...)` con `onended` | Igual, pero la boca se mueve mientras suena |
| Texto que lee la voz | El que se ve en pantalla, **con la «j» de la aspiración** | El texto original, sin «j» (§7) |
| Estado del paciente | No existe | Un estado derivado en `App.jsx` (§3) |
| Entrada del estudiante | Solo escribir | Escribir o hablar (§8) |

Decisiones que ya están tomadas:

- **No se usa `speechSynthesis` del navegador.** La voz salvadoreña de Edge TTS es mejor y no cambia según el navegador.
- **Se mantiene el avatar de DiceBear.** No hace falta preparar imágenes; el pixel art (6 arquetipos) es una opción futura (§4).
- El **dolor se hace con CSS**, sin imagen extra (§5).
- Se descartan la hoja de sprites y el video con IA (§11).

---

## 2. Plan por pasos

| Paso | Qué | Esfuerzo | Imágenes nuevas |
|---|---|---|---|
| 1 | Movimiento con CSS por estado (respirar, pensar, hablar, dolor) | 30 min | No |
| 2 | (Opcional) Boca y ojos por parámetro de DiceBear | 30 min | No |
| 3 | Boca sincronizada con el audio que ya existe | 1 h | No |
| 4 | Entrada de voz del estudiante (micrófono) | 1-2 h | No |
| 5 | Pulido de la interfaz (mensajes, «escribiendo…») | 1 h | No |
| Extra | Parpadeo (`eyes=closed`), entrada del paciente | 1 h | No |

**Con los pasos 1 y 2 ya se ve un paciente que habla y reacciona**, que es lo importante para la demo. Los pasos 3 y 4 se pueden hacer en cualquier orden.

---

## 3. Estados del paciente

El estado **no vive en `PatientCard`**, porque lo deciden el chat, el audio y el micrófono. Se **deriva** en `App.jsx` de valores que ya existen; así no hay que sincronizar `useState` a mano.

| Estado | Cuándo | Animación |
|---|---|---|
| `entrando` | Al iniciar la consulta (extra, §10) | Camina hacia el centro |
| `reposo` | Esperando | Respira suave |
| `escuchando` | El estudiante está dictando | Se inclina un poco hacia adelante |
| `pensando` | Desde que se envía la pregunta hasta el primer token | Balanceo lento |
| `hablando` | Llegan tokens **o** suena el audio | Boca alternando + rebote |
| `despedida` | Pantalla de resultados | Un pequeño saludo |

La expresión (`dolor`) es independiente del estado y se combina con él (§5).

```jsx
// App.jsx
const [audioSonando, setAudioSonando] = useState(false) // lo avisa Chat.jsx (§6)
const [escuchando, setEscuchando] = useState(false)     // lo avisa el dictado (§8)

const ultimo = mensajes[mensajes.length - 1]
const hayTokens = ultimo?.role === 'assistant' && ultimo.content.length > 0

const estadoPaciente =
  fase === 'resultados' ? 'despedida'
  : audioSonando ? 'hablando'
  : enviando ? (hayTokens ? 'hablando' : 'pensando')
  : escuchando ? 'escuchando'
  : 'reposo'

// Expresión: se deduce del motivo de consulta, que ya es público (no revela nada nuevo)
const expresion = /dolor|duele|cólico|molest/i.test(sesion?.motivo_consulta || '') ? 'dolor' : 'neutral'
```

---

## 4. Imagen del paciente: se mantiene DiceBear

El paciente sigue usando el avatar de DiceBear que ya entrega el servidor (`paciente.avatar_url`, generado en `backend/app/avatars.py` según sexo y edad). **No hay que crear ni descargar imágenes.** El componente `PacienteAnimado` solo le aplica movimiento CSS (§5). Si el avatar no carga (sin internet), la ficha se ve igual, sin la imagen.

### Boca y ojos con DiceBear (opcional)

DiceBear permite cambiar la boca y los ojos con parámetros en la URL. Comprobado con el estilo `avataaars`:

| Parámetro | Valores que respondieron bien |
|---|---|
| `mouth` | `default`, `eating`, `twinkle`, `serious`, `smile` |
| `eyes` | `default`, `closed` |

Un valor que no existe devuelve error 400, así que solo se usan valores de la lista (hay más en la documentación de DiceBear). Con eso se puede, sin imágenes nuevas:

- **Hablar:** alternar `mouth=default` y `mouth=eating` (o `twinkle`) con el hook `useBoca` (§6).
- **Parpadear:** `eyes=closed` durante ~150 ms (§10).

Cosas a tener en cuenta:

- Hay que **mirar cuál boca parece mejor "hablando"** antes de elegirla.
- Para tener una cara de reposo consistente conviene fijar `mouth=default&eyes=default`; sin ellos, la semilla puede sacar ojos o bocas poco apropiados para un paciente. Eso cambia un poco el aspecto actual, por eso es opcional.
- Cada variante es una petición a internet: se **precargan** con `new Image().src = …` al mostrar al paciente, para evitar parpadeos.

### Pixel art (opción futura)

Si más adelante quieren un estilo pixel art, la idea sería **6 arquetipos** (hombre o mujer × joven, adulto, mayor; mismos cortes de edad que `avatars.py`) con `neutral`, `habla` y `parpadeo` en `frontend/public/pacientes/`, editando la boca y los ojos a mano en Piskel. DiceBear quedaría de respaldo. No es necesario para que la animación funcione.

---

## 5. Paso 1: movimiento con CSS

Regla para que no se pisen las animaciones:

- Un elemento **no puede tener dos animaciones sobre `transform`**. Por eso el **dolor va en el contenedor** y el estado (respirar, hablar…) va en la imagen.

```jsx
// frontend/src/components/PacienteAnimado.jsx
import { useEffect, useState } from 'react'

export default function PacienteAnimado({ paciente, estado, expresion }) {
  const [falla, setFalla] = useState(false)
  useEffect(() => setFalla(false), [paciente.avatar_url])
  if (falla || !paciente?.avatar_url) return null

  return (
    <div className={`paciente-wrap ${expresion === 'dolor' ? 'con-dolor' : ''}`}>
      <img
        src={paciente.avatar_url}
        alt={`Avatar de ${paciente.nombre}`}
        className={`paciente ${estado || 'reposo'}`}
        onError={() => setFalla(true)}
      />
    </div>
  )
}
```

```css
/* frontend/src/styles.css */
.paciente-wrap { display: inline-block; }
/* El tamaño y el círculo del avatar ya los da `.datos img` (120 px), no se redefinen aquí. */

/* Estados (en la imagen) */
.paciente.reposo     { animation: respirar 4s ease-in-out infinite; }
.paciente.pensando   { animation: pensar 1.6s ease-in-out infinite; }
.paciente.hablando   { animation: rebotar .4s ease-in-out infinite alternate; }
.paciente.escuchando { transform: scale(1.03) translateY(2px); }
.paciente.despedida  { animation: saludar .6s ease-in-out 2; }

/* Dolor (en el contenedor): temblor leve y un tono rojizo, sin imagen extra */
.paciente-wrap.con-dolor { animation: temblar .6s ease-in-out infinite; }
.paciente-wrap.con-dolor .paciente { filter: saturate(1.25) drop-shadow(0 0 5px rgb(200 60 50 / .55)); }

@keyframes respirar { 0%,100% { transform: scale(1); } 50% { transform: scale(1.02); } }
@keyframes pensar   { 0%,100% { transform: rotate(0); } 50% { transform: rotate(-1.5deg); } }
@keyframes rebotar  { from { transform: translateY(0); } to { transform: translateY(-3px); } }
@keyframes temblar  { 0%,100% { transform: translateX(0); } 25% { transform: translateX(-2px); } 75% { transform: translateX(2px); } }
@keyframes saludar  { 0%,100% { transform: rotate(0); } 50% { transform: rotate(4deg); } }
```

En `PatientCard.jsx` se reemplaza el `<img src={paciente.avatar_url}>` por `<PacienteAnimado paciente={paciente} estado={estado} expresion={expresion} />` y se pasan `estado` y `expresion` como props desde `App.jsx`. El interruptor «Ver paciente» no cambia.

---

## 6. Pasos 2 y 3: boca y sincronía con la voz

**Boca (paso 2).** Un hook alterna `neutral` y `habla` mientras el estado es `hablando`:

```js
// frontend/src/hooks/useBoca.js
import { useEffect, useState } from 'react'

export function useBoca(activo, ms = 180) {
  const [abierta, setAbierta] = useState(false)
  useEffect(() => {
    const reducir = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (!activo || reducir) { setAbierta(false); return }
    const t = setInterval(() => setAbierta((b) => !b), ms)
    return () => clearInterval(t)
  }, [activo, ms])
  return abierta
}
```

**Sincronía con el audio (paso 3).** `Chat.jsx` ya crea el audio y sabe cuándo termina. Solo hay que avisar a `App.jsx`:

```jsx
// Chat.jsx: nueva prop onVozEstado
const audio = new Audio(urlAudioPaciente(sessionId, contenido))
audio.onplay  = () => onVozEstado?.(true)
audio.onended = () => { onVozEstado?.(false) /* … lo que ya hace */ }
audio.onpause = () => onVozEstado?.(false)
audio.onerror = () => onVozEstado?.(false)
```

En `App.jsx`: `<Chat … onVozEstado={setAudioSonando} />`. Si la voz está silenciada, la boca sigue moviéndose mientras llegan los tokens (`hayTokens`), así que siempre hay respuesta visual.

---

## 7. Requisito previo: la voz debe leer el texto sin «j»

Hoy el servidor guarda y manda a la voz el texto **después** de `aspirar()` («ejtoy», «Buenaj tardej»), y ese mismo texto vuelve al modelo en el historial. Hay que conservar el original:

```python
# backend/app/main.py (dentro de gen() del chat), esquema
crudo: list[str] = []
async def tap(stream):
    async for tok in stream:
        crudo.append(tok)       # texto original del modelo
        yield tok

async for tok in habla.aspirar_stream(tap(llm.stream_chat(...)), nivel):
    partial.append(tok)         # lo que se muestra (con «j» si corresponde)
    yield _sse({"token": tok})

# al terminar: done_payload["texto_original"] = "".join(crudo)
# y en el historial del modelo: guardar "".join(crudo), no el aspirado
```

En el frontend cada mensaje guarda `content` (lo que se ve) y `voz` (`texto_original`), y `reproducirAudio` usa `voz`. Prueba sugerida: un paciente de San Miguel (aspiración `media`) cuyo `done` trae `texto_original` sin «j».

> Alternativa más simple: dejar de escribir la «j» en pantalla y no hacer nada de lo anterior. Es la decisión pendiente sobre la aspiración.

---

## 8. Paso 4: entrada de voz del estudiante (STT)

**Es posible y barato.** Hay dos caminos:

| Opción | Cómo | Ventajas | Desventajas |
|---|---|---|---|
| **A. API de voz del navegador** (recomendada) | `SpeechRecognition` / `webkitSpeechRecognition` | Gratis, sin instalar nada, unas decenas de líneas | Chrome y Edge (no Firefox); **envía el audio al servicio del navegador** (necesita internet); puede errar términos médicos |
| B. Whisper local | El navegador graba con `MediaRecorder`, el backend transcribe con `faster-whisper` | Funciona sin internet, no depende del navegador | Dependencia y modelo de cientos de MB; compite por CPU y memoria con Qwen; hay que medir la latencia |

**Empieza por la A.** La B queda como mejora si necesitan funcionar sin internet.

### Comportamiento recomendado

- Botón **🎤 Hablar** junto al campo de texto. Un clic empieza a escuchar; otro, o el silencio, termina.
- El texto reconocido **se escribe en el campo** (en gris mientras es provisional) y el estudiante **lo revisa y pulsa Enviar**. No se envía solo por defecto, porque un error de reconocimiento («diclofenaco» → «dicloro neto») cambiaría la pregunta. Un interruptor opcional «Enviar al terminar» queda apagado.
- Mientras se escucha, el paciente pasa a `escuchando` (§3).
- **Anti-eco:** el botón se desactiva mientras el paciente está hablando (`audioSonando`) o respondiendo (`enviando`), y al empezar a dictar se pausa cualquier audio. Con altavoces, el micrófono captaría la voz del paciente; lo ideal es usar audífonos.
- Cada pregunta dictada cuenta igual que una escrita para el límite de preguntas del nivel.
- Si el navegador no lo soporta, el botón **no se muestra** y todo sigue funcionando por teclado.

### Hook

```js
// frontend/src/hooks/useDictado.js
import { useEffect, useRef, useState } from 'react'

const SR = typeof window !== 'undefined' ? window.SpeechRecognition || window.webkitSpeechRecognition : null

const MENSAJES = {
  'not-allowed': 'Permite el micrófono en el navegador para poder dictar.',
  'service-not-allowed': 'El navegador no permite el reconocimiento de voz.',
  'no-speech': 'No se oyó nada. Inténtalo de nuevo.',
  'audio-capture': 'No se encontró un micrófono.',
  network: 'El reconocimiento de voz necesita conexión a internet.',
}

export function useDictado({ lang = 'es-SV', onTexto, onEscuchando }) {
  const [escuchando, setEscuchando] = useState(false)
  const [error, setError] = useState('')
  const rec = useRef(null)
  const soportado = Boolean(SR)

  function cambiar(v) { setEscuchando(v); onEscuchando?.(v) }

  function iniciar(idioma = lang) {
    if (!SR || escuchando) return
    const r = new SR()
    r.lang = idioma
    r.interimResults = true
    r.continuous = false
    r.onstart = () => { setError(''); cambiar(true) }
    r.onresult = (e) => {
      const texto = Array.from(e.results).map((x) => x[0].transcript).join(' ').trim()
      onTexto?.(texto, e.results[e.results.length - 1].isFinal)
    }
    r.onerror = (e) => {
      if (e.error === 'language-not-supported' && idioma !== 'es-MX') return iniciar('es-MX') // respaldo
      setError(MENSAJES[e.error] || `Error de voz: ${e.error}`)
    }
    r.onend = () => cambiar(false)
    rec.current = r
    r.start()
  }

  function detener() { rec.current?.stop() }
  useEffect(() => () => rec.current?.abort(), [])

  return { soportado, escuchando, error, iniciar, detener }
}
```

### Uso en `Chat.jsx`

```jsx
const [provisional, setProvisional] = useState('')
const dictado = useDictado({
  onEscuchando: onEscuchando, // prop que sube a App.jsx → setEscuchando
  onTexto: (t, final) => (final ? (setTexto(t), setProvisional('')) : setProvisional(t)),
})

{dictado.soportado && (
  <button
    type="button"
    className={`btn btn-mic ${dictado.escuchando ? 'grabando' : ''}`}
    onClick={() => {
      if (dictado.escuchando) return dictado.detener()
      audioRef.current?.pause()           // no dictar encima de la voz del paciente
      dictado.iniciar()
    }}
    disabled={enviando || reproduciendoIdx !== null}
    aria-pressed={dictado.escuchando}
    title="Hablar con el paciente"
  >
    {dictado.escuchando ? '⏹ Escuchando…' : '🎤 Hablar'}
  </button>
)}
{dictado.error && <p className="error" role="alert">{dictado.error}</p>}
```

El campo de texto muestra `provisional` mientras `texto` esté vacío. Estilo mínimo: `.btn-mic.grabando` con un punto rojo que pulsa (y sin pulso si `prefers-reduced-motion`).

### Cosas que hay que saber

- **Dónde funciona:** Chrome y Edge de escritorio. Firefox no lo trae. Funciona en `http://localhost` sin HTTPS. Es muy probable que **no funcione en el navegador integrado de la aplicación de escritorio de Claude** (no incluye las claves del servicio de voz): pruébalo en Chrome o Edge.
- **Privacidad:** en Chrome el audio se procesa en los servidores de Google (en Edge, de Microsoft). Para una demo con pacientes ficticios no importa; indícalo en el README y que no digan datos personales reales.
- **Idioma:** `es-SV` (El Salvador) existe en Chrome; si no, se usa `es-MX`. Las palabras clave de la evaluación ignoran tildes y mayúsculas, así que un dictado sin tildes puntúa igual.
- **Exactitud:** los términos médicos son lo más propenso a errores. Por eso el texto se revisa antes de enviarlo.

---

## 9. Paso 5: pulido de la interfaz

Todo en CSS, sin librerías:

```css
/* Mensajes del chat: aparecen con un deslizamiento suave */
.msg { animation: aparecer .25s ease-out; }
@keyframes aparecer { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

/* «Escribiendo…»: tres puntos mientras el mensaje del paciente está vacío */
.escribiendo span { display: inline-block; animation: saltar 1s infinite; }
.escribiendo span:nth-child(2) { animation-delay: .15s; }
.escribiendo span:nth-child(3) { animation-delay: .3s; }
@keyframes saltar { 0%,60%,100% { transform: translateY(0); } 30% { transform: translateY(-4px); } }
```

```jsx
{m.content || <span className="escribiendo" aria-label="El paciente está respondiendo"><span>•</span><span>•</span><span>•</span></span>}
```

Hoy el mensaje vacío muestra «…»; esto lo reemplaza. La caja de pista puede reutilizar `aparecer`.

---

## 10. Extras (si hay tiempo)

**Parpadeo** (con DiceBear: la misma URL con `eyes=closed` durante ~150 ms, precargada). Se aplica cuando no está hablando; la boca tiene prioridad:

```js
// dentro de PacienteAnimado: variante = hablando ? habla : parpadeando ? parpadeo : neutral
useEffect(() => {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
  let t1, t2
  const siguiente = () => {
    t1 = setTimeout(() => {
      setParpadeando(true)
      t2 = setTimeout(() => { setParpadeando(false); siguiente() }, 150)
    }, 3000 + Math.random() * 2000)
  }
  siguiente()
  return () => { clearTimeout(t1); clearTimeout(t2) }
}, [])
```

**Entrada del paciente** (1 s, para no estorbar en consultas repetidas). Requiere `overflow: hidden` en el contenedor (ya está en `.paciente-wrap`):

```css
.paciente.entrando { animation: entrar 1s linear forwards, pasos .4s steps(2) 2; }
@keyframes entrar { from { transform: translateX(-150%); } to { transform: translateX(0); } }
@keyframes pasos  { 0%,100% { margin-top: 0; } 50% { margin-top: -4px; } }
```

Para usarla, el estado `entrando` dura 1 s al crear la sesión (un `setTimeout` en `App.jsx`).

---

## 11. Accesibilidad

```css
@media (prefers-reduced-motion: reduce) {
  .paciente, .paciente-wrap, .escribiendo span, .msg, .btn-mic.grabando { animation: none; }
}
```

Los hooks de boca y parpadeo ya comprueban `prefers-reduced-motion` y no alternan imágenes. Además:

- El botón del micrófono usa `aria-pressed` y el error se anuncia con `role="alert"`.
- El estado del paciente es decorativo: no debe ser la única forma de saber que está respondiendo (el texto «…» o los puntos lo cubren).

---

## 12. Descartado

- **Hoja de sprites:** mucho trabajo de dibujo por poco resultado frente a cambiar boca y ojos.
- **Video con IA (SadTalker, Wav2Lip…):** pensado para fotos reales, no en tiempo real, requiere GPU que ya usa Qwen.
- **`speechSynthesis` del navegador:** reemplazado por la voz de Edge TTS que ya tiene el proyecto.
- **Framer Motion:** no hace falta; con CSS alcanza.

---

## 13. Pruebas y criterio de terminado

**Automáticas** (si se hace el §7): el `done` del chat trae `texto_original` sin «j» y el historial del modelo no contiene «j» de aspiración.

**Manuales:**

- [ ] «Ver paciente» sigue mostrando el avatar de DiceBear de siempre (mismo tamaño y círculo).
- [ ] Sin internet (avatar que no carga), la ficha se ve bien y no queda una imagen rota.
- [ ] Estados: `reposo` al esperar, `pensando` hasta el primer token, `hablando` con la boca alternando mientras llegan tokens y suena el audio, `reposo` al terminar.
- [ ] Con la voz silenciada, la boca sigue moviéndose mientras llegan los tokens.
- [ ] Un motivo con «dolor» muestra el temblor y el tono rojizo; uno sin dolor, no.
- [ ] Con «reducir movimiento» activado en el sistema, no hay animaciones ni cambio de boca.
- [ ] 🎤: pide permiso, escribe el texto reconocido en el campo, **no** lo envía solo, y se desactiva mientras el paciente habla.
- [ ] 🎤 sin permiso, sin micrófono, sin internet y en Firefox: mensaje claro o botón oculto, y se puede seguir escribiendo.
- [ ] El audio del paciente lee el texto **sin «j»** (paciente de San Miguel).
- [ ] `npm run build` compila y `pytest backend\tests -q` pasa.

---

## 14. Resumen de tiempos

| Bloque | Tiempo |
|---|---|
| Pasos 1 + 2 (CSS y, opcional, boca por parámetro) | ~1 h |
| Paso 3 (sincronía) | ~1 h |
| §7 (voz sin «j») | ~30 min |
| Paso 4 (micrófono) | ~1-2 h |
| Paso 5 (pulido) | ~1 h |
| Extras | ~1 h |

Mínimo vistoso para la demo: **pasos 1, 2 y 3**. El micrófono (paso 4) añade interacción pero depende del navegador y de internet: pruébalo en el equipo de la demo antes de presentarlo.
