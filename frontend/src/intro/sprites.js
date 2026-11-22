// Sprites del estudiante de medicina. Cada fila mide lo mismo; «.» es transparente.
// Cuadrícula de la escena: 160 × 90 píxeles.

export const PALETA_ESTUDIANTE = {
  H: '#2b1d17', // pelo
  S: '#f2c39a', // piel
  s: '#d9a37a', // piel en sombra
  W: '#e9edf7', // bata
  w: '#b9c2dc', // bata en sombra
  T: '#2fa39b', // camiseta (verde azulado)
  K: '#6b7280', // estetoscopio
  B: '#2b1d17', // cejas
  E: '#1a1a2e', // ojos
  X: '#ffffff', // blanco del ojo
  M: '#8a3b3b', // boca
  C: '#e79a8a', // mejillas
}

// Cabeza 14 × 12 (sin cara).
export const CABEZA = [
  '...HHHHHHHH...',
  '..HHHHHHHHHH..',
  '.HHHHHHHHHHHH.',
  '.HHSSSSSSSSHH.',
  '.HSSSSSSSSSSH.',
  '.HSSSSSSSSSSH.',
  '.HSSSSSSSSSSH.',
  '..SSSSSSSSSS..',
  '..SSSSSSSSSS..',
  '...SSSSSSSS...',
  '....SSSSSS....',
  '.....ssss.....',
]

// Caras: 14 × 7, se superponen a la cabeza desde la fila 3.
export const CARAS = {
  preocupado: [
    '....BB..BB....',
    '...B......B...',
    '....E....E....',
    '....E....E....',
    '..C........C..',
    '......MM......',
    '.....M..M.....',
  ],
  sorpresa: [
    '...BB....BB...',
    '..............',
    '...XEX..XEX...',
    '...XEX..XEX...',
    '..C........C..',
    '......MM......',
    '......MM......',
  ],
  feliz: [
    '...BB....BB...',
    '..............',
    '....E....E....',
    '...E.E..E.E...',
    '..C........C..',
    '.....M..M.....',
    '......MM......',
  ],
}

// Parte superior del tronco 20 × 6: bata, camiseta y estetoscopio.
export const TRONCO = [
  '...WWWWWTTTTWWWWW...',
  '..WWWWWWTTTTWWWWWW..',
  '.WWWWWWKTTTTKWWWWWW.',
  '.WWWWWWKTTTTKWWWWWW.',
  '.WWWWWWWKTTKWWWWWWW.',
  '.WWWWWWWWKKWWWWWWWW.',
]

// Gota de sudor 3 × 5.
export const GOTA = [
  '.b.',
  '.b.',
  'bBb',
  'bBb',
  '.b.',
]
export const PALETA_GOTA = { b: '#8fd3ff', B: '#d9f1ff' }

// Mano 4 × 3.
export const MANO = ['.SSS', 'SSSS', 'sSS.']
