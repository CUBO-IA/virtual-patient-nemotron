import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// API_TARGET permite apuntar el proxy a otro backend (p. ej. API_TARGET=http://localhost:8010).
const apiTarget = process.env.API_TARGET || 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { '/api': apiTarget },
  },
})
