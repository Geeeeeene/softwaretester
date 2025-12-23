import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        // 在 Docker 环境中使用服务名，本地开发使用 localhost
        // 优先使用环境变量 VITE_API_TARGET，否则根据 DOCKER_ENV 判断
        target: process.env.VITE_API_TARGET || (process.env.DOCKER_ENV === 'true' ? 'http://backend:8000' : 'http://localhost:8000'),
        changeOrigin: true,
        rewrite: (path) => path, // 保持路径不变
      },
    },
  },
})
