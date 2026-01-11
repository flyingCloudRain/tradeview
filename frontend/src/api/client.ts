import axios from 'axios'
import { ElMessage } from 'element-plus'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 60000, // 增加到60秒，因为龙虎榜数据查询包含机构明细，可能需要更长时间
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    // 调试日志
    console.log('API请求:', config.method?.toUpperCase(), config.baseURL + config.url)
    if (config.params) {
      console.log('请求参数:', JSON.stringify(config.params, null, 2))
      console.log('完整URL:', config.baseURL + config.url + '?' + new URLSearchParams(config.params as any).toString())
    }
    if (config.data) {
      console.log('请求体:', JSON.stringify(config.data, null, 2))
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    console.log('API响应:', response.config.url, response.status, response.data)
    return response.data
  },
  (error) => {
    console.error('API错误:', error.config?.url, error.response?.status, error.response?.data)
    if (error.response) {
      const { status, data } = error.response
      if (status === 401) {
        localStorage.removeItem('token')
        window.location.href = '/login'
      } else {
        ElMessage.error(data?.detail || '请求失败')
      }
    } else {
      ElMessage.error('网络错误，请检查网络连接')
    }
    return Promise.reject(error)
  }
)

export default apiClient

