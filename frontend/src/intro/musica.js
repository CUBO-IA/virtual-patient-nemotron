// Música de fondo generada con Web Audio: no usa archivos de audio, así que no hay derechos de autor que cuidar
// ni nada que descargar. Una progresión suave estilo «lo‑fi» (pad + bajo + arpegio) que empieza melancólica
// y, con el destello, cambia a una más luminosa.

const mtof = (n) => 440 * 2 ** ((n - 69) / 12)

// Notas MIDI por acorde (la más grave es la fundamental).
const PROGRESIONES = {
  nocturna: [
    [57, 60, 64, 67], // Am7
    [53, 57, 60, 64], // Fmaj7
    [48, 52, 55, 59], // Cmaj7
    [55, 59, 62, 65], // G7
  ],
  esperanza: [
    [60, 64, 67, 71], // Cmaj7
    [55, 59, 62, 64], // G6
    [57, 60, 64, 67], // Am7
    [53, 57, 60, 64], // Fmaj7
  ],
}
const ARPEGIO = [0, 2, 1, 3, 2, 1, 3, 2]
const BPM = 72
const VOLUMEN = 0.9

export function crearMusica() {
  const Contexto = typeof window !== 'undefined' && (window.AudioContext || window.webkitAudioContext)
  if (!Contexto) {
    // Sin Web Audio: todo son funciones vacías y la intro sigue funcionando sin sonido.
    return { iniciar: async () => false, silenciar() {}, modo() {}, destello() {}, detener() {}, activo: () => false }
  }

  const beat = 60 / BPM
  let ctx = null
  let master = null
  let temporizador = null
  let proximo = 0
  let compas = 0
  let modoActual = 'nocturna'
  let silenciado = false
  let sonando = false

  function nota(freq, t0, dur, tipo, vol, corte, ataque = 0.4) {
    const o = ctx.createOscillator()
    const f = ctx.createBiquadFilter()
    const g = ctx.createGain()
    o.type = tipo
    o.frequency.value = freq
    f.type = 'lowpass'
    f.frequency.value = corte
    g.gain.setValueAtTime(0.0001, t0)
    g.gain.linearRampToValueAtTime(vol, t0 + Math.min(ataque, dur * 0.4))
    g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur)
    o.connect(f).connect(g).connect(master)
    o.start(t0)
    o.stop(t0 + dur + 0.05)
  }

  function programarCompas(t0) {
    const progresion = PROGRESIONES[modoActual]
    const acorde = progresion[compas % progresion.length]
    const luminoso = modoActual === 'esperanza'
    acorde.forEach((n) => nota(mtof(n), t0, beat * 4.3, 'sine', 0.08, 1100, 0.6)) // pad
    nota(mtof(acorde[0] - 12), t0, beat * 3.6, 'sine', 0.24, 320, 0.05) // bajo
    for (let i = 0; i < 8; i += 1) {
      if (Math.random() < 0.78) {
        const n = acorde[ARPEGIO[i]] + 12 + (luminoso && i % 4 === 3 ? 12 : 0)
        nota(mtof(n), t0 + (i * beat) / 2, beat * 1.6, 'triangle', luminoso ? 0.12 : 0.09, 2400, 0.01)
      }
    }
    compas += 1
  }

  function avanzar() {
    while (proximo < ctx.currentTime + 0.8) {
      programarCompas(proximo)
      proximo += beat * 4
    }
  }

  function rampa(valor, segundos) {
    if (!master) return
    const t = ctx.currentTime
    master.gain.cancelScheduledValues(t)
    master.gain.setValueAtTime(master.gain.value, t)
    master.gain.linearRampToValueAtTime(valor, t + segundos)
  }

  return {
    // Debe llamarse desde un clic o toque: los navegadores no dejan sonar nada antes.
    async iniciar() {
      if (sonando) return true
      try {
        ctx = new Contexto()
        if (ctx.state === 'suspended') await ctx.resume()
        master = ctx.createGain()
        master.gain.value = 0.0001
        // Un compresor al final de la cadena evita saturaciones cuando suenan varias notas a la vez.
        const limitador = ctx.createDynamicsCompressor()
        limitador.threshold.value = -14
        limitador.ratio.value = 6
        master.connect(limitador).connect(ctx.destination)
        proximo = ctx.currentTime + 0.1
        avanzar()
        temporizador = window.setInterval(avanzar, 200)
        sonando = true
        rampa(silenciado ? 0.0001 : VOLUMEN, 2.5)
        return true
      } catch {
        return false
      }
    },

    silenciar(valor) {
      silenciado = valor
      rampa(valor ? 0.0001 : VOLUMEN, 0.4)
    },

    modo(nuevo) {
      if (PROGRESIONES[nuevo]) modoActual = nuevo
    },

    // Destello de luz: un barrido de notas agudas que sube y se apaga.
    destello() {
      if (!sonando) return
      const t0 = ctx.currentTime + 0.02
      ;[72, 76, 79, 83, 88, 91, 95].forEach((n, i) => nota(mtof(n), t0 + i * 0.07, 1.6, 'sine', 0.16, 6000, 0.01))
      nota(mtof(48), t0, 2.2, 'sawtooth', 0.08, 700, 0.5)
      modoActual = 'esperanza'
    },

    detener(segundos = 1.5) {
      if (!sonando) return
      sonando = false
      rampa(0.0001, segundos)
      window.clearInterval(temporizador)
      const c = ctx
      window.setTimeout(() => c.close().catch(() => {}), segundos * 1000 + 200)
    },

    activo: () => sonando,
  }
}
