import { useEffect, useState } from 'react'

export function useBoca(activo, ms = 180) {
  const [abierta, setAbierta] = useState(false)
  useEffect(() => {
    const reducir = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (!activo || reducir) {
      setAbierta(false)
      return
    }
    const t = setInterval(() => setAbierta((b) => !b), ms)
    return () => clearInterval(t)
  }, [activo, ms])
  return abierta
}
