import { useMemo, useState } from 'react'

const ETIQUETA_ESTADO = { bajo: '▼ Bajo', alto: '▲ Alto', normal: '● Normal' }

function normalizar(t) {
  return (t || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '')
}

/**
 * Pestaña «Pruebas»: catálogo único (el mismo para todos los casos) y resultados ya obtenidos.
 * No indica qué prueba es pertinente: eso solo se revela al terminar la consulta.
 */
export default function PruebasPanel({ catalogo, estado, nivelId, onPedir, pidiendo }) {
  const [busqueda, setBusqueda] = useState('')

  const pedidas = useMemo(() => new Set(estado.resultados.map((r) => r.id)), [estado.resultados])
  const limiteAlcanzado = estado.limite != null && estado.pruebas_usadas >= estado.limite

  const grupos = useMemo(() => {
    if (!catalogo) return []
    const q = normalizar(busqueda)
    const filtradas = catalogo.pruebas.filter(
      (p) => !q || normalizar(p.nombre).includes(q) || normalizar(p.nota).includes(q),
    )
    return catalogo.categorias
      .map((cat) => ({ categoria: cat, pruebas: filtradas.filter((p) => p.categoria === cat) }))
      .filter((g) => g.pruebas.length > 0)
  }, [catalogo, busqueda])

  function motivoBloqueo(p) {
    if (pedidas.has(p.id)) return 'Ya solicitada'
    if (limiteAlcanzado) return 'Límite de pruebas alcanzado'
    if (estado.presupuesto_restante != null && p.costo > estado.presupuesto_restante) return 'Excede el presupuesto'
    return ''
  }

  const ultimo = estado.resultados[0]

  return (
    <div className="pruebas-panel">
      <div className="pruebas-resumen" role="status">
        <span>
          <strong>Pruebas solicitadas:</strong> {estado.pruebas_usadas}
          {estado.limite != null ? ` / ${estado.limite}` : ''}
        </span>
        {estado.presupuesto != null && (
          <span>
            <strong>Presupuesto:</strong> {estado.costo_total} de {estado.presupuesto} puntos de costo
          </span>
        )}
      </div>

      {nivelId === 1 && (
        <p className="pruebas-pista">
          Piensa: ¿qué prueba confirmaría o descartaría lo que sospechas? Pedir pruebas innecesarias también cuenta.
        </p>
      )}

      <div className="sr-only-pv" aria-live="polite">
        {ultimo ? `Resultado disponible: ${ultimo.nombre}` : ''}
      </div>

      <div className="pruebas-columnas">
        <section className="pruebas-catalogo" aria-label="Catálogo de pruebas">
          <label className="pruebas-buscar">
            <span className="sr-only-pv">Buscar una prueba</span>
            <input
              type="search"
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              placeholder="Buscar prueba…"
            />
          </label>

          {!catalogo && <p className="vacio">Cargando catálogo…</p>}
          {catalogo && grupos.length === 0 && <p className="vacio">No hay pruebas que coincidan.</p>}

          {grupos.map((g) => (
            <div key={g.categoria} className="pruebas-grupo">
              <h4>{g.categoria}</h4>
              <ul>
                {g.pruebas.map((p) => {
                  const bloqueo = motivoBloqueo(p)
                  return (
                    <li key={p.id} className={`prueba-item ${pedidas.has(p.id) ? 'pedida' : ''}`}>
                      <div className="prueba-info">
                        <strong>{p.nombre}</strong>
                        {p.nota && <span className="prueba-nota">{p.nota}</span>}
                        <span className="prueba-meta">
                          {estado.mostrar_costo && <span className="chip">Costo {p.costo}</span>}
                          {p.nivel_atencion === 'hospital' && <span className="chip">Requiere referencia</span>}
                        </span>
                      </div>
                      <button
                        type="button"
                        className="btn"
                        onClick={() => onPedir(p.id)}
                        disabled={Boolean(bloqueo) || pidiendo}
                        title={bloqueo || 'Solicitar esta prueba'}
                      >
                        {bloqueo || 'Solicitar'}
                      </button>
                    </li>
                  )
                })}
              </ul>
            </div>
          ))}
        </section>

        <section className="pruebas-resultados" aria-label="Resultados obtenidos">
          <h4>Resultados obtenidos</h4>
          {estado.resultados.length === 0 && <p className="vacio">Aún no has solicitado pruebas.</p>}
          {estado.resultados.map((r) => (
            <article key={r.id} className="prueba-resultado">
              <header>
                <strong>{r.nombre}</strong>
                <span className="chip">{r.categoria}</span>
              </header>
              <p>{r.informe}</p>
              {r.valores?.length > 0 && (
                <table className="prueba-valores">
                  <thead>
                    <tr>
                      <th scope="col">Análisis</th>
                      <th scope="col">Valor</th>
                      <th scope="col">Referencia</th>
                      <th scope="col">Estado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {r.valores.map((v) => (
                      <tr key={v.analito}>
                        <td>{v.analito}</td>
                        <td>
                          {v.valor} {v.unidad}
                        </td>
                        <td>{v.referencia}</td>
                        <td className={`estado-${v.estado}`}>{ETIQUETA_ESTADO[v.estado] || v.estado}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </article>
          ))}
        </section>
      </div>
    </div>
  )
}
