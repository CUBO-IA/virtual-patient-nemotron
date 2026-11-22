import React from 'react'
import PixelArt from './PixelArt.jsx'
import {
  CABEZA,
  CARAS,
  GOTA,
  MANO,
  PALETA_ESTUDIANTE,
  PALETA_GOTA,
  TRONCO,
} from './sprites.js'

// Escena de 160 × 90 «píxeles» (se escala con CSS manteniendo los bordes nítidos).
const LUNA = ['..MMM..', '.MMM...', 'MMM....', 'MMM....', 'MMM....', '.MMM...', '..MMM..']
const PALETA_LUNA = { M: '#f5efc4' }

const LIBRO = [
  '.ppppppppppppp.ppppppppppppp.',
  '.pllllllllllll.pllllllllllll.',
  '.pplllllllllll.pplllllllllll.',
  '.pllllllllllll.pllllllllllll.',
  '.bbbbbbbbbbbbbbbbbbbbbbbbbbb.',
]
const PALETA_LIBRO = { p: '#f1ead2', l: '#cfc6a3', b: '#7d3636' }

const ESTRELLAS = [
  [13, 11], [20, 16], [38, 25], [15, 30], [34, 33], [23, 12], [40, 14],
]
const LIBROS_ESTANTE = [
  ['#8a3b3b', 3, 9], ['#2f6f8f', 4, 11], ['#d1a13a', 3, 8], ['#3d7a4d', 4, 10], ['#6b4a9e', 3, 11], ['#b25d3c', 4, 9],
  ['#2f6f8f', 3, 10], ['#8a3b3b', 4, 8],
]

export default function Escena({ expresion = 'preocupado', portatilAbierto = false, pantallaOn = false, gota = true }) {
  let xLibro = 106
  return (
    <svg
      className="intro-escena"
      viewBox="0 0 160 90"
      preserveAspectRatio="xMidYMid slice"
      shapeRendering="crispEdges"
      role="img"
      aria-label="Un estudiante de medicina lee de noche, preocupado por sus prácticas. Junto a él hay una computadora."
    >
      <defs>
        <radialGradient id="intro-luz-lampara" cx="50%" cy="50%" r="50%">
          <stop offset="0" stopColor="#ffd98a" stopOpacity="0.38" />
          <stop offset="1" stopColor="#ffd98a" stopOpacity="0" />
        </radialGradient>
        <radialGradient id="intro-luz-pantalla" cx="50%" cy="50%" r="50%">
          <stop offset="0" stopColor="#bcd0ff" stopOpacity="0.8" />
          <stop offset="1" stopColor="#bcd0ff" stopOpacity="0" />
        </radialGradient>
      </defs>

      {/* Pared */}
      <rect width="160" height="90" fill="#121833" />
      <rect y="62" width="160" height="2" fill="#0e1228" />

      {/* Ventana con luna y estrellas */}
      <rect x="8" y="6" width="36" height="34" fill="#3a2f4a" />
      <rect x="10" y="8" width="32" height="30" fill="#0a0f2e" />
      <rect x="25" y="8" width="2" height="30" fill="#3a2f4a" />
      <rect x="10" y="22" width="32" height="2" fill="#3a2f4a" />
      <PixelArt mapa={LUNA} paleta={PALETA_LUNA} x={30} y={11} />
      {ESTRELLAS.map(([x, y], i) => (
        <rect key={i} className="intro-estrella" style={{ animationDelay: `${i * 0.45}s` }} x={x} y={y} width="1" height="1" fill="#fff" />
      ))}
      <rect x="6" y="40" width="40" height="2" fill="#4a3d5c" />

      {/* Reloj de pared */}
      <rect x="76" y="6" width="9" height="9" fill="#cfd6ee" />
      <rect x="77" y="7" width="7" height="7" fill="#121833" />
      <rect x="80" y="8" width="1" height="4" fill="#e9edf7" />
      <rect x="80" y="11" width="3" height="1" fill="#e9edf7" />

      {/* Estante */}
      {LIBROS_ESTANTE.map(([color, ancho, alto], i) => {
        const x = xLibro
        xLibro += ancho + 1
        return <rect key={i} x={x} y={27 - alto} width={ancho} height={alto} fill={color} />
      })}
      <rect x="104" y="27" width="46" height="2" fill="#5a3a2a" />

      {/* Luz de la lámpara */}
      <circle cx="108" cy="48" r="46" fill="url(#intro-luz-lampara)" />

      {/* Escritorio */}
      <rect y="62" width="160" height="4" fill="#7a5237" />
      <rect y="66" width="160" height="24" fill="#4a2f20" />
      <rect x="18" y="71" width="54" height="15" fill="#3d2618" />
      <rect x="20" y="73" width="50" height="11" fill="#503726" />
      <rect x="42" y="77" width="6" height="1" fill="#c9a46a" />
      <rect x="88" y="71" width="54" height="15" fill="#3d2618" />
      <rect x="90" y="73" width="50" height="11" fill="#503726" />
      <rect x="112" y="77" width="6" height="1" fill="#c9a46a" />

      {/* Pila de libros y taza */}
      <rect x="14" y="59" width="22" height="3" fill="#8a3b3b" />
      <rect x="16" y="56" width="20" height="3" fill="#2f6f8f" />
      <rect x="15" y="53" width="19" height="3" fill="#3d7a4d" />
      <rect x="46" y="57" width="6" height="5" fill="#d9d9e8" />
      <rect x="52" y="58" width="2" height="3" fill="#d9d9e8" />
      <rect className="intro-vapor" style={{ animationDelay: '0s' }} x="47" y="54" width="1" height="2" fill="#c9cde8" />
      <rect className="intro-vapor" style={{ animationDelay: '0.7s' }} x="49" y="54" width="1" height="2" fill="#c9cde8" />
      <rect className="intro-vapor" style={{ animationDelay: '1.4s' }} x="51" y="54" width="1" height="2" fill="#c9cde8" />

      {/* Estudiante */}
      <g className="intro-estudiante">
        <rect x="70" y="40" width="20" height="22" fill="#e9edf7" />
        <rect x="70" y="40" width="1" height="22" fill="#b9c2dc" />
        <rect x="89" y="40" width="1" height="22" fill="#b9c2dc" />
        <rect x="74" y="40" width="1" height="16" fill="#c9d1e6" />
        <rect x="85" y="40" width="1" height="16" fill="#c9d1e6" />
        <PixelArt mapa={TRONCO} paleta={PALETA_ESTUDIANTE} x={70} y={34} />
        <PixelArt mapa={CABEZA} paleta={PALETA_ESTUDIANTE} x={73} y={22} />
        <PixelArt mapa={CARAS[expresion] || CARAS.preocupado} paleta={PALETA_ESTUDIANTE} x={73} y={25} />
        {gota && expresion === 'preocupado' && (
          <g className="intro-gota">
            <PixelArt mapa={GOTA} paleta={PALETA_GOTA} x={88} y={24} />
          </g>
        )}
      </g>

      {/* Libro abierto y manos */}
      <PixelArt mapa={LIBRO} paleta={PALETA_LIBRO} x={66} y={57} />
      <PixelArt mapa={MANO} paleta={PALETA_ESTUDIANTE} x={69} y={54} />
      <PixelArt mapa={MANO} paleta={PALETA_ESTUDIANTE} x={87} y={54} />

      {/* Lámpara */}
      <rect x="106" y="60" width="12" height="2" fill="#2a2f4a" />
      <rect x="111" y="44" width="2" height="16" fill="#3a4060" />
      <polygon points="100,41 114,41 111,34 103,34" fill="#e0a93b" />
      <rect x="102" y="41" width="10" height="1" fill="#fff1b8" />

      {/* Computadora portátil */}
      <g className={`intro-tapa ${portatilAbierto ? 'abierta' : ''}`}>
        <rect x="125" y="44" width="26" height="16" fill="#3b4259" />
        <rect x="127" y="46" width="22" height="12" fill={pantallaOn ? '#1b2150' : '#0b0f22'} />
        {pantallaOn && (
          <g className="intro-pantalla-on">
            <rect x="137" y="48" width="2" height="6" fill="#8275e5" />
            <rect x="135" y="50" width="6" height="2" fill="#8275e5" />
            <rect x="129" y="55" width="8" height="1" fill="#aab0e8" />
            <rect x="139" y="55" width="8" height="1" fill="#aab0e8" />
          </g>
        )}
      </g>
      <rect x="122" y="60" width="32" height="3" fill="#6b7280" />
      <rect x="126" y="63" width="24" height="1" fill="#4b5262" />
      {pantallaOn && <circle className="intro-brillo" cx="138" cy="52" r="22" fill="url(#intro-luz-pantalla)" />}

      {/* Puntos del pensamiento */}
      <rect className="intro-punto" x="88" y="20" width="2" height="2" fill="#eef1ff" />
      <rect className="intro-punto" style={{ animationDelay: '0.3s' }} x="92" y="16" width="3" height="3" fill="#eef1ff" />
      <rect className="intro-punto" style={{ animationDelay: '0.6s' }} x="97" y="11" width="4" height="4" fill="#eef1ff" />
    </svg>
  )
}
