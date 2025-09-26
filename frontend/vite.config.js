import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // Needed for the Docker Container port mapping to work
    port: 5173,
    watch: {
      usePolling: true,
    },
    // Proxy API requests to the backend server to avoid CORS issues
    proxy: {
      '/api': {
        target: 'http://api:8000', // The service name and port from docker-compose
        changeOrigin: true,
        secure: false,
      },
    },
  },
})

