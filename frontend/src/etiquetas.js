const CIVIL = {
  soltero: { F: 'Soltera', M: 'Soltero' },
  casado: { F: 'Casada', M: 'Casado' },
  union_libre: 'Unión libre',
  separado: { F: 'Separada', M: 'Separado' },
  viudo: { F: 'Viuda', M: 'Viudo' },
  divorciado: { F: 'Divorciada', M: 'Divorciado' },
}
const ESCOLARIDAD = {
  ninguno: 'Sin estudios', primaria: 'Primaria', secundaria: 'Secundaria',
  bachillerato: 'Bachillerato', tecnico: 'Técnico', universitario: 'Universitario', posgrado: 'Posgrado',
}
const HOGAR = {
  nuclear: 'Con pareja e hijos', pareja: 'Con su pareja', extendido: 'Con familia extendida',
  monoparental: 'Con hijos, sin pareja',
}

function traducir(mapa, valor, sexo) {
  if (valor == null || String(valor).trim() === '') return null
  const original = String(valor).trim()
  const clave = original.toLowerCase()
  const etiqueta = mapa[clave]
  if (etiqueta && typeof etiqueta === 'object') return etiqueta[sexo] || etiqueta.M
  return etiqueta || original.charAt(0).toLocaleUpperCase('es') + original.slice(1)
}

export const etiquetaEstadoCivil = (valor, sexo) => traducir(CIVIL, valor, sexo)
export const etiquetaEscolaridad = (valor) => traducir(ESCOLARIDAD, valor)
export const etiquetaHogar = (valor) => traducir(HOGAR, valor)
