import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig(({ mode }) => {
  // Load env from parent directory (project root)
  const env = loadEnv(mode, process.cwd() + '/..', ['AICM_', 'VITE_'])
  
  const frontendPort = parseInt(env.AICM_FRONTEND_PORT || '3100')
  const backendPort = parseInt(env.VITE_BACKEND_PORT || env.AICM_BACKEND_PORT || '8100')
  
  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    server: {
      port: frontendPort,
      proxy: {
        '/api': {
          target: `http://localhost:${backendPort}`,
          changeOrigin: true,
        },
      },
    },
  }
})
