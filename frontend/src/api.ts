import axios from 'axios'

// 默认走 Vite 代理（/api -> http://127.0.0.1:8000），如需直连可设置 VITE_API_BASE
const API_BASE = import.meta.env.VITE_API_BASE ?? '/api'

// 允许通过环境变量手动配置超时时间（毫秒）
// 使用方式：在 .env 或启动命令中设置 VITE_API_TIMEOUT_MS，例如 120000 表示 120 秒
const API_TIMEOUT_MS = (() => {
  const v = Number(import.meta.env.VITE_API_TIMEOUT_MS)
  return Number.isFinite(v) && v > 0 ? v : 60000
})()

export const api = axios.create({
  baseURL: API_BASE,
  timeout: API_TIMEOUT_MS,
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
  }
})

// 添加请求拦截器用于调试
api.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method?.toUpperCase(), config.url)
    return config
  },
  (error) => {
    console.error('API Request Error:', error)
    return Promise.reject(error)
  }
)

// 添加响应拦截器用于调试
api.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.status, response.config.url)
    return response
  },
  (error) => {
    console.error('API Response Error:', error.response?.status, error.response?.data, error.config?.url)
    return Promise.reject(error)
  }
)
