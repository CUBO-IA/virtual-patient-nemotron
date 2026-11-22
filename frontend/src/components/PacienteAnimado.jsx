import { useEffect, useRef, useState } from 'react'

/**
 * Asigna la imagen y animación correspondiente según género, edad y perfil
 * de la persona (ver ANIMACIONES.md).
 *
 * 5 Mujeres:
 *  - 1 Adolescente (< 25): salvadoran_teen_girl_16 (paciente_02)
 *  - 2 Mediana edad (25-59): salvadoran_woman_32 (paciente_04), salvadoran_woman_37 (paciente_06)
 *  - 2 Mayores (>= 60): salvadoran_elder_woman_60s (paciente_08), salvadoran_elder_woman_70s (paciente_10)
 *
 * 5 Hombres:
 *  - 1 Adolescente (< 25): salvadoran_teen_16 (paciente_01)
 *  - 2 Mediana edad (25-59): salvadoran_man_32 (paciente_03), salvadoran_man_37 (paciente_05)
 *  - 2 Mayores (>= 60): salvadoran_elder_60s (paciente_07), salvadoran_elder_70s (paciente_09)
 */
function getPatientId(paciente) {
  if (!paciente) return 'paciente_03'
  const sexo = (paciente.sexo || 'M').toUpperCase()
  const edad = Number(paciente.edad) || 30

  // Hash determinista del paciente para desempatar sin repetir cuando
  // dos pacientes comparten mismo género y grupo de edad
  const seed = `${paciente.id || ''}_${paciente.nombre || ''}`
  let hash = 0
  for (let i = 0; i < seed.length; i++) {
    hash = ((hash << 5) - hash) + seed.charCodeAt(i)
    hash |= 0
  }
  const alternar = Math.abs(hash) % 2 === 0

  if (sexo === 'F') {
    if (edad < 25) {
      // Adolescente (16 años)
      return 'paciente_02'
    } else if (edad >= 60) {
      // Adultas mayores: 60s vs 70s
      if (edad >= 70) return 'paciente_10'
      if (edad < 68) return 'paciente_08'
      return alternar ? 'paciente_08' : 'paciente_10'
    } else {
      // Mediana edad: 32 vs 37
      if (edad < 35) return 'paciente_04'
      if (edad >= 42) return 'paciente_06'
      return alternar ? 'paciente_04' : 'paciente_06'
    }
  } else {
    // Masculino
    if (edad < 25) {
      // Adolescente (16 años)
      return 'paciente_01'
    } else if (edad >= 60) {
      // Adultos mayores: 60s vs 70s
      if (edad >= 70) return 'paciente_09'
      if (edad < 68) return 'paciente_07'
      return alternar ? 'paciente_07' : 'paciente_09'
    } else {
      // Mediana edad: 32 vs 37
      if (edad < 35) return 'paciente_03'
      if (edad >= 42) return 'paciente_05'
      return alternar ? 'paciente_03' : 'paciente_05'
    }
  }
}

export default function PacienteAnimado({ paciente, estado, expresion }) {
  const [fallaCapas, setFallaCapas] = useState(false)
  const [sinImagen, setSinImagen] = useState(false) // fallaron también las imágenes consolidadas
  const [parpadeando, setParpadeando] = useState(false)
  const [formaBoca, setFormaBoca] = useState('cerrada') // 'cerrada' | 'entreabierta' | 'abierta' | 'o' | 'dolor'
  const audioContextRef = useRef(null)
  const analyserRef = useRef(null)
  const sourceRef = useRef(null)
  const currentAudioRef = useRef(null)
  const animFrameRef = useRef(null)
  const lastMouthChangeRef = useRef(0)
  const contadorAlternanciaRef = useRef(0)
  const blinkTimerRef = useRef(null)

  const patientId = getPatientId(paciente)
  const esDolor = expresion === 'dolor'
  const hablando = estado === 'hablando'

  // Reset de fallback si cambia el paciente
  useEffect(() => {
    setFallaCapas(false)
    setSinImagen(false)
  }, [paciente?.nombre, paciente?.id])

  // Precarga todas las capas del personaje: sin esto, la primera vez que la boca cambia de forma la imagen
  // se descarga en ese momento y se ve un parpadeo en blanco.
  useEffect(() => {
    const nombres = ['base', 'ojos', 'ojos_cerrados', 'ojos_dolor', 'boca_cerrada', 'boca_entreabierta', 'boca_abierta', 'boca_o', 'boca_dolor']
    nombres.forEach((n) => {
      const img = new Image()
      img.src = `/pacientes/capas/${patientId}/${n}.png`
    })
  }, [patientId])

  // =========================================================================
  // 1. PARPADEO NATURAL (Cada 3 a 6 segundos, duración 120-180 ms)
  // =========================================================================
  useEffect(() => {
    let activo = true

    function programarSiguienteParpadeo() {
      const espera = 3000 + Math.random() * 3000 // 3 a 6 segundos
      blinkTimerRef.current = setTimeout(() => {
        if (!activo) return
        setParpadeando(true)
        const duracion = 120 + Math.random() * 60 // 120 a 180 ms
        setTimeout(() => {
          if (!activo) return
          setParpadeando(false)
          programarSiguienteParpadeo()
        }, duracion)
      }, espera)
    }

    programarSiguienteParpadeo()

    return () => {
      activo = false
      if (blinkTimerRef.current) clearTimeout(blinkTimerRef.current)
    }
  }, [patientId])

  // =========================================================================
  // 2. SINCRONIZACIÓN CON AUDIO (Web Audio API AnalyserNode + Fallback suave)
  // =========================================================================
  useEffect(() => {
    function conectarAudio(audioEl) {
      if (!audioEl) return
      try {
        if (!audioContextRef.current) {
          const AudioCtx = window.AudioContext || window.webkitAudioContext
          if (AudioCtx) {
            audioContextRef.current = new AudioCtx()
          }
        }
        const ctx = audioContextRef.current
        if (!ctx) return

        if (ctx.state === 'suspended') {
          ctx.resume().catch(() => {})
        }

        if (currentAudioRef.current !== audioEl) {
          currentAudioRef.current = audioEl
          if (sourceRef.current) {
            try { sourceRef.current.disconnect() } catch (_) {}
          }
          const analyser = ctx.createAnalyser()
          analyser.fftSize = 256
          analyser.smoothingTimeConstant = 0.5
          analyserRef.current = analyser

          const source = ctx.createMediaElementSource(audioEl)
          source.connect(analyser)
          analyser.connect(ctx.destination)
          sourceRef.current = source
        }
      } catch (err) {
        // En caso de restricción CORS en source o error de nodo, queda activo el analizador fallback
        analyserRef.current = null
      }
    }

    function iniciarLoopAnalisis() {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current)

      function loop() {
        const now = performance.now()
        const dt = now - lastMouthChangeRef.current

        if (analyserRef.current && currentAudioRef.current && !currentAudioRef.current.paused) {
          const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount)
          analyserRef.current.getByteFrequencyData(dataArray)

          let sum = 0
          for (let i = 0; i < dataArray.length; i++) {
            sum += dataArray[i]
          }
          const promedio = sum / dataArray.length

          // Suavizado: cambiar como máximo cada 85-100 ms
          if (dt >= 90) {
            lastMouthChangeRef.current = now
            if (promedio < 12) {
              setFormaBoca(esDolor ? 'dolor' : 'cerrada')
            } else if (promedio < 40) {
              setFormaBoca('entreabierta')
            } else {
              contadorAlternanciaRef.current++
              // Variar entre abierta y redonda ('o')
              if (contadorAlternanciaRef.current % 4 === 0) {
                setFormaBoca('o')
              } else {
                setFormaBoca('abierta')
              }
            }
          }
        } else if (hablando) {
          // Fallback con cadencia fonética realista si el nodo directo no está disponible
          if (dt >= 90) {
            lastMouthChangeRef.current = now
            contadorAlternanciaRef.current++
            const ciclo = contadorAlternanciaRef.current % 6
            if (ciclo === 0) setFormaBoca(esDolor ? 'dolor' : 'cerrada')
            else if (ciclo === 1 || ciclo === 4) setFormaBoca('entreabierta')
            else if (ciclo === 2 || ciclo === 5) setFormaBoca('abierta')
            else setFormaBoca('o')
          }
        } else {
          setFormaBoca(esDolor ? 'dolor' : 'cerrada')
        }

        animFrameRef.current = requestAnimationFrame(loop)
      }

      loop()
    }

    function detenerAnalisis() {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current)
      setFormaBoca(esDolor ? 'dolor' : 'cerrada')
    }

    const handlePlay = (e) => {
      conectarAudio(e.detail || window.__pvCurrentAudio)
      iniciarLoopAnalisis()
    }

    const handleStop = () => {
      detenerAnalisis()
    }

    window.addEventListener('pv-audio-play', handlePlay)
    window.addEventListener('pv-audio-stop', handleStop)

    if (hablando) {
      if (window.__pvCurrentAudio) {
        conectarAudio(window.__pvCurrentAudio)
      }
      iniciarLoopAnalisis()
    } else {
      detenerAnalisis()
    }

    return () => {
      window.removeEventListener('pv-audio-play', handlePlay)
      window.removeEventListener('pv-audio-stop', handleStop)
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current)
    }
  }, [hablando, esDolor])

  // Rutas de capas e imágenes consolidadas
  const capasDir = `/pacientes/capas/${patientId}`
  const baseSrc = `${capasDir}/base.png`
  const ojosSrc = parpadeando
    ? `${capasDir}/ojos_cerrados.png`
    : esDolor
      ? `${capasDir}/ojos_dolor.png`
      : `${capasDir}/ojos.png`

  let bocaSrc = `${capasDir}/boca_cerrada.png`
  if (formaBoca === 'entreabierta') bocaSrc = `${capasDir}/boca_entreabierta.png`
  else if (formaBoca === 'abierta') bocaSrc = `${capasDir}/boca_abierta.png`
  else if (formaBoca === 'o') bocaSrc = `${capasDir}/boca_o.png`
  else if (formaBoca === 'dolor') bocaSrc = `${capasDir}/boca_dolor.png`

  const imagenConsolidada = esDolor
    ? `/pacientes/${patientId}_dolor.png`
    : `/pacientes/${patientId}.png`

  // Si fallan las capas por cualquier motivo, imagen estática consolidada
  if (fallaCapas && !sinImagen) {
    return (
      <div className={`paciente-wrap ${esDolor ? 'con-dolor' : ''}`}>
        <img
          src={imagenConsolidada}
          alt={`Paciente ${paciente?.nombre || ''}`}
          className={`paciente paciente-standalone ${estado || 'reposo'}`}
          onError={() => setSinImagen(true)}
        />
      </div>
    )
  }

  // Último recurso: las iniciales del paciente
  if (sinImagen) {
    const iniciales = (paciente?.nombre || '?').trim().split(/\s+/).slice(0, 2).map((p) => p[0]?.toUpperCase()).join('')
    return (
      <div className="paciente-wrap" role="img" aria-label={`Paciente ${paciente?.nombre || ''}`}>
        <div className="paciente paciente-stage reposo">
          <span className="paciente-iniciales" aria-hidden="true">{iniciales}</span>
        </div>
      </div>
    )
  }

  return (
    <div className={`paciente-wrap ${esDolor ? 'con-dolor' : ''}`}>
      <div
        className={`paciente paciente-stage ${estado || 'reposo'} ${hablando ? 'hablando' : ''}`}
        title={`Paciente ${paciente?.nombre || ''}`}
      >
        {/* Capa Base: Cabeza, torso, cabello, ropa y accesorios */}
        <img
          src={baseSrc}
          alt={`Paciente ${paciente?.nombre || ''}`}
          className="paciente-layer layer-base"
          style={{ background: 'transparent', border: 'none', boxShadow: 'none' }}
          onError={() => setFallaCapas(true)}
        />
        {/* Capa Ojos: Abiertos, cerrados (parpadeo) o molestia */}
        <img
          src={ojosSrc}
          alt=""
          aria-hidden="true"
          className="paciente-layer layer-ojos"
          style={{ background: 'transparent', border: 'none', boxShadow: 'none' }}
          onError={() => setFallaCapas(true)}
        />
        {/* Capa Boca: Sincronizada con el audio mediante Web Audio API */}
        <img
          src={bocaSrc}
          alt=""
          aria-hidden="true"
          className="paciente-layer layer-boca"
          style={{ background: 'transparent', border: 'none', boxShadow: 'none' }}
          onError={() => setFallaCapas(true)}
        />
      </div>
    </div>
  )
}
