import path from 'path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
const API = `127.0.0.1:${process.env.STUDIO_API_PORT || 8000}`
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { '@': path.resolve(__dirname, './src') } },
  server: { host: '0.0.0.0', port: Number(process.env.STUDIO_UI_PORT || 5173), proxy: {
    '/api': `http://${API}`,
    '/ws': { target: `ws://${API}`, ws: true },
  } },
})
