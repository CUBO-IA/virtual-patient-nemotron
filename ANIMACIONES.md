# Animación del paciente y entrada de voz

Guía para que el paciente se vea "vivo" (respira, habla, siente dolor) y para que el estudiante pueda **hablarle con el micrófono**. Enfocada en lo funcional: pocas imágenes, CSS y un par de hooks de React. Sin APIs de pago.

> Adaptada a este proyecto (React + Vite, FastAPI, voz de Edge TTS). Reemplaza a `animaciones-pacientes.md`, que asumía un proyecto distinto.
>
> **Decisión actual: personajes ilustrados con capas** (10 pacientes según sexo y edad, §5). DiceBear dejó de mostrarse; el backend aún envía `avatar_url` y se conserva como dato, pero la interfaz no lo usa.
>
> **Estado:** los pasos 1 a 5 están implementados con el sistema de personajes ilustrados: parpadeo, boca sincronizada con el audio real (Web Audio), estados con movimiento muy leve y respaldo sin internet. La «j» se ve en pantalla solo desde el nivel 2 y la voz siempre pronuncia con ella (§7).

---

## 1. Qué ya existe y qué cambia

| Pieza | Hoy | Con esta guía |
|---|---|---|
| Imagen del paciente | Personaje ilustrado en capas (base, ojos y boca), elegido por sexo y edad, solo al activar «Ver paciente» | Parpadea, mueve la boca con la voz y tiene gesto de molestia (§5) |
| Voz del paciente | Edge TTS (`es-SV`) desde el servidor; `Chat.jsx` usa `new Audio(...)` con `onended` | Igual, pero la boca se mueve mientras suena |
| Texto que lee la voz | Siempre con la «j» de la aspiración (`texto_voz`); en pantalla la «j» solo desde el nivel 2 | Igual (§7) |
| Estado del paciente | No existe | Un estado derivado en `App.jsx` (§3) |
| Entrada del estudiante | Solo escribir | Escribir o hablar (§8) |

Decisiones que ya están tomadas:

- **No se usa `speechSynthesis` del navegador.** La voz salvadoreña de Edge TTS es mejor y no cambia según el navegador.
- **Se mantiene el avatar de DiceBear.** No hace falta preparar imágenes; el pixel art (6 arquetipos) es una opción futura (§4).
- El **dolor se marca sin imagen extra** y sin movimiento brusco (§5).
- Se descartan la hoja de sprites y el video con IA (§11).

---

## 2. Plan por pasos

| Paso | Qué | Esfuerzo | Imágenes nuevas |
|---|---|---|---|
| 1 | Animación del anillo por estado (pensar, hablar, escuchar) | 30 min | No |
| 2 | (Opcional) Boca y ojos por parámetro de DiceBear | 30 min | No |
| 3 | Boca sincronizada con el audio que ya existe | 1 h | No |
| 4 | Entrada de voz del estudiante (micrófono) | 1-2 h | No |
| 5 | Pulido de la interfaz (mensajes, «escribiendo…») | 1 h | No |
| Extra | Parpadeo (`eyes=closed`), entrada del paciente | 1 h | No |

**Con el paso 1 ya se ve un paciente que reacciona** (el anillo late al hablar y se atenúa al pensar), que es lo importante para la demo. Los pasos 2 y 3 (mover la boca) son opcionales y se pueden hacer en cualquier orden con el 4.

---

## 3. Estados del paciente

El estado **no vive en `PatientCard`**, porque lo deciden el chat, el audio y el micrófono. Se **deriva** en `App.jsx` de valores que ya existen; así no hay que sincronizar `useState` a mano.

| Estado | Cuándo | Animación |
|---|---|---|
| `entrando` | Al iniciar la consulta | Aparece con un desvanecido |
| `reposo` | Esperando | Quieto |
| `escuchando` | El estudiante está dictando | El anillo se marca |
| `pensando` | Desde que se envía la pregunta hasta el primer token | El anillo se atenúa y vuelve, despacio |
| `hablando` | Llegan tokens **o** suena el audio | El anillo pulsa con suavidad |
| `despedida` | Pantalla de resultados | Sin animación propia |

La expresión (`dolor`) es independiente del estado; hoy solo sirve para interpretar el motivo de consulta y ya no cambia el avatar (§5).

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

> **Nota:** esta sección describe el avatar anterior (DiceBear). Ya no se muestra; se deja como referencia y como posible respaldo.

### Expresión serena (ya aplicada)

DiceBear elige ojos, cejas y boca al azar, y salían avatares con el ceño fruncido, guiños y bocas raras que desentonaban con un paciente que viene a consulta. `backend/app/avatars.py` fija esas tres partes a opciones calmadas (`eyes=default,squint`, `eyebrows=defaultNatural,flatNatural,sadConcernedNatural`, `mouth=default,concerned,serious`). Dentro de ese conjunto la semilla de cada paciente elige una variante, así que el rostro sigue siendo estable pero nunca enojado.

### Pixel art (opción futura)

Si más adelante quieren un estilo pixel art, la idea sería **6 arquetipos** (hombre o mujer × joven, adulto, mayor; mismos cortes de edad que `avatars.py`) con `neutral`, `habla` y `parpadeo` en `frontend/public/pacientes/`, editando la boca y los ojos a mano en Piskel. DiceBear quedaría de respaldo. No es necesario para que la animación funcione.

---

## 5. Personajes ilustrados en capas (sistema actual)

Cada paciente se dibuja con **3 imágenes apiladas** dentro de un recuadro de 140 px (`.paciente-stage`): `base.png` (cuerpo y cara), `ojos*.png` y `boca*.png`. Código: `frontend/src/components/PacienteAnimado.jsx`.

**Qué personaje se elige** (`getPatientId`): hay 10, 5 mujeres y 5 hombres, por sexo y edad (menos de 25, 25 a 59 y 60 o más; en cada grupo medio y mayor hay dos y se desempata con un hash estable del nombre). Con 150 personas y 10 dibujos, varios pacientes comparten ilustración; es una decisión consciente.

| Capa | Variantes |
|---|---|
| Ojos | `ojos`, `ojos_cerrados` (parpadeo cada 3 a 6 s) y `ojos_dolor` (si el motivo menciona dolor) |
| Boca | `boca_cerrada`, `boca_entreabierta`, `boca_abierta`, `boca_o` y `boca_dolor` |

**Sincronía con la voz.** `Chat.jsx` avisa con los eventos `pv-audio-play` y `pv-audio-stop` y guarda el audio en `window.__pvCurrentAudio`. El componente conecta ese audio a un `AnalyserNode` de Web Audio y, cada ~90 ms, elige la forma de la boca según el volumen medio del espectro (menos de 12 = cerrada, menos de 40 = entreabierta, más de 40 alterna abierta y «o»). Si no puede analizar el audio, usa una cadencia fija mientras el estado es `hablando`. Medido con la voz real del servidor, las sílabas dan un volumen medio de ~50 y las pausas de ~3, así que los umbrales funcionan.

**Reglas de movimiento (importante).** Todo es muy leve y se aplica a las **capas**, no al marco: respirar (±1,5 px), pensar (±1,2°), hablar (cabeza ±1°). El marco nunca se mueve y ya no hay temblor ni resplandor rojo con el dolor: esa expresión la dan las capas de ojos y boca. Si agregas movimientos, no los pongas sobre `.paciente-stage` (la tarjeta «temblaba»).

**Respaldos.** Si falla una capa, se usa la imagen consolidada `/pacientes/paciente_NN[_dolor].png`; si falla también, un círculo con las iniciales. Las 9 imágenes del personaje se **precargan** al mostrarlo: sin eso, la boca parpadea en blanco la primera vez que cambia de forma.

**Archivos** (`frontend/public/pacientes/`): `capas/paciente_NN/*.png` (9 por personaje) y `paciente_NN.png` / `paciente_NN_dolor.png` (consolidadas). Pesan ~27 MB; las consolidadas son ~850 KB cada una y solo son respaldo, así que redimensionarlas o pasarlas a WebP las aligeraría.

**Scripts** (`scripts/build_patient_illustrations.py`, `fix_patient_mouths.py`, `process_desktop_images.py`): sirvieron para preparar las imágenes; usan rutas del equipo de quien las hizo y no pueden ejecutarse tal cual en otra máquina.

Con `prefers-reduced-motion` las animaciones CSS se desactivan (§11).

---

## 6. Pasos 2 y 3: boca y sincronía con la voz

> **Estado: aplicado de otra forma.** La boca ya se mueve, pero con la sincronía por Web Audio descrita en §5, no con el hook `useBoca` (que sigue en `frontend/src/hooks/useBoca.js` sin usarse y puede borrarse). Esta sección queda como referencia.

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

## 7. Voz y aspiración de la «j» (decidido)

La aspiración regional de la «s» («dos veces» → «doj vecej») le da carácter a los pacientes del oriente, pero escrita dificulta la lectura de quien empieza. La decisión tomada después de probarlo:

| Dónde | Qué se ve u oye |
|---|---|
| **Pantalla, nivel 1 (Básico)** | Ortografía normal: «dos veces» |
| **Pantalla, niveles 2 y 3** | Con la aspiración, si el paciente es del oriente: «doj vecej» |
| **Voz (TTS)**, en todos los niveles | Siempre con la aspiración |
| **Historial que ve el modelo** | Siempre el texto original, sin «j», para no contaminar su contexto |

Cómo está hecho (`backend/app/main.py`, dentro de `gen()` del chat):

```python
mostrar_j = s.nivel.get("texto_aspirado", s.nivel.get("id") != 1)   # configurable por nivel
flujo = habla.aspirar_stream(tap(tok_stream), nivel) if mostrar_j else tap(tok_stream)
...
done_payload = {
    "done": True,
    "texto_original": texto_limpio,                  # sin «j»
    "texto_voz": habla.aspirar(texto_limpio, nivel), # con «j»: lo que lee la voz
    ...
}
```

En el frontend (`App.jsx`) el evento `done` guarda `texto_voz` en el mensaje (`voz`) y `reproducirAudio` lo usa; si no viene, cae a `content`. Pruebas en `test_habla.py`: el nivel 1 muestra «Fueron dos veces.» con `texto_voz` aspirado, y el nivel 2 conserva la «j» en pantalla.

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

- **Dónde funciona:** Chrome y Edge de escritorio, en `http://localhost` (no hace falta HTTPS). Firefox no incluye `SpeechRecognition`: ahí el botón se oculta y se sigue escribiendo. En navegadores integrados dentro de otras aplicaciones suele fallar (no traen el servicio de voz del navegador): ante la duda, pruébalo en Chrome o Edge.
- **Privacidad:** el reconocimiento no es local. Chrome envía el audio a los servidores de Google y Edge a los de Microsoft. Para pacientes ficticios no importa, pero hay que avisar al usuario que no dicte datos personales reales.
- **Idioma:** el hook pide `es-SV`; si el navegador responde `language-not-supported`, reintenta solo con `es-MX`. La detección de la evaluación ignora tildes y mayúsculas, así que un dictado sin tildes puntúa igual.
- **Errores que ve el usuario** (en español, sin códigos): permiso denegado («Permite el micrófono en el navegador para poder dictar.»), servicio no permitido, silencio («No se oyó nada. Inténtalo de nuevo.»), sin micrófono, y sin internet («El reconocimiento de voz necesita conexión a internet.»). Cualquier otro error muestra su código para poder reportarlo.
- **Exactitud:** los términos médicos son lo más propenso a fallar («diclofenaco» → «dicloro neto»). Por eso el texto se revisa antes de enviarlo y nunca se envía solo.
- **Limpieza:** al desmontar el componente el hook cancela el reconocimiento (`abort()`), de modo que el micrófono no queda abierto si el estudiante sale de la consulta.

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

**Automáticas** (ya existen en `backend/tests/test_habla.py`): en el nivel 1 el chat muestra ortografía normal y `texto_voz` trae la aspiración; en el nivel 2 la «j» se ve en pantalla; el historial del modelo no contiene «j» de aspiración.

**Manuales:**

- [ ] «Ver paciente» sigue mostrando el avatar de DiceBear de siempre (mismo tamaño y círculo).
- [ ] Sin internet (avatar que no carga), la ficha se ve bien y no queda una imagen rota.
- [ ] Estados: `reposo` (quieto) al esperar, `pensando` (anillo que se atenúa) hasta el primer token, `hablando` (anillo que pulsa) mientras llegan tokens y suena el audio, `reposo` al terminar.
- [ ] Con la voz silenciada, el anillo sigue pulsando mientras llegan los tokens.
- [ ] La imagen del paciente no se mueve ni tiembla en ningún estado y no aparece ningún recuadro alrededor del círculo.
- [ ] Los avatares nunca muestran cejas enojadas ni guiños.
- [ ] Con «reducir movimiento» activado en el sistema, no hay animaciones.
- [ ] 🎤: pide permiso, escribe el texto reconocido en el campo, **no** lo envía solo, y se desactiva mientras el paciente habla.
- [ ] 🎤 sin permiso, sin micrófono, sin internet y en Firefox: mensaje claro o botón oculto, y se puede seguir escribiendo.
- [ ] En el nivel 1 el texto se ve con ortografía normal y el audio pronuncia con «j» (paciente de San Miguel); en el nivel 2 la «j» también se ve escrita.
- [ ] `npm run build` compila y `pytest backend\tests -q` pasa.

---

## 14. Resumen de tiempos

| Bloque | Tiempo |
|---|---|
| Pasos 1 + 2 (CSS y, opcional, boca por parámetro) | ~1 h |
| Paso 3 (sincronía) | ~1 h |
| §7 (voz con «j», nivel 1 sin «j» en pantalla) | ~30 min |
| Paso 4 (micrófono) | ~1-2 h |
| Paso 5 (pulido) | ~1 h |
| Extras | ~1 h |

Mínimo vistoso para la demo: **pasos 1, 2 y 3**. El micrófono (paso 4) añade interacción pero depende del navegador y de internet: pruébalo en el equipo de la demo antes de presentarlo.
