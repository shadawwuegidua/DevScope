import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        // 使用 127.0.0.1 确保走 IPv4，避免部分环境 localhost 解析到 IPv6 导致连接被拒
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
        ws: true,
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('代理错误:', err)
          })
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log('发送请求到后端:', req.method, req.url)
          })
          proxy.on('proxyRes', (proxyRes, req, _res) => {
            console.log('收到后端响应:', proxyRes.statusCode, req.url)
          })
        }
      }
    }
  }
})
