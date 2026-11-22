import React, { useMemo } from 'react'

/**
 * Dibuja un sprite descrito como texto: cada carácter es un píxel y la paleta dice de qué color.
 * «.» (o un carácter sin color) es transparente. Se agrupan los píxeles contiguos en un solo trazo por color,
 * así un sprite de 300 píxeles son unas pocas decenas de rectángulos y se ve nítido a cualquier tamaño.
 */
export default function PixelArt({ mapa, paleta, x = 0, y = 0, className }) {
  const trazos = useMemo(() => {
    const porColor = {}
    mapa.forEach((fila, j) => {
      let i = 0
      while (i < fila.length) {
        const c = fila[i]
        if (c === '.' || !paleta[c]) {
          i += 1
          continue
        }
        let k = i
        while (k < fila.length && fila[k] === c) k += 1
        ;(porColor[c] ||= []).push(`M${i} ${j}h${k - i}v1h-${k - i}z`)
        i = k
      }
    })
    return Object.entries(porColor)
  }, [mapa, paleta])

  return (
    <g transform={`translate(${x} ${y})`} className={className}>
      {trazos.map(([c, d]) => (
        <path key={c} d={d.join('')} fill={paleta[c]} />
      ))}
    </g>
  )
}
