import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    proxy: {
      // Same-origin from the browser's point of view - the dev server
      // proxies server-side to the backend, so no CORS/hostname wrangling
      // is needed even behind Codespaces' forwarded-port URLs.
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      // Uploaded reference materials are served directly from the
      // backend at this path (see app.main) - proxy it too so links to
      // them resolve in dev, same as they do same-origin in prod.
      '/files': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
