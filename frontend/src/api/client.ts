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
    
    // 清理概念资金流API的无效参数（保留date/limit或start_date/end_date，移除其他无效参数）
    if (config.url?.includes('/stock-fund-flow/concept') && config.params) {
      // 处理不同类型的params对象
      let params: Record<string, any> = {}
      
      if (config.params instanceof URLSearchParams) {
        // 如果是URLSearchParams，转换为普通对象
        config.params.forEach((value, key) => {
          params[key] = value
        })
      } else if (typeof config.params === 'object') {
        params = { ...config.params }
      }
      
      // 创建新的干净参数对象
      const cleanParams: Record<string, any> = {}
      
      // 日期范围查询参数（优先级高于单日期查询）
      if (params.start_date !== undefined && params.start_date !== null) {
        cleanParams.start_date = params.start_date
      }
      if (params.end_date !== undefined && params.end_date !== null) {
        cleanParams.end_date = params.end_date
      }
      
      // 单日期查询参数（仅在日期范围查询不存在时保留）
      if (!cleanParams.start_date && !cleanParams.end_date) {
        if (params.date !== undefined && params.date !== null) {
          cleanParams.date = params.date
        }
        if (params.limit !== undefined && params.limit !== null) {
          cleanParams.limit = params.limit
        }
      }
      
      // 其他通用参数
      if (params.concept !== undefined && params.concept !== null) {
        cleanParams.concept = params.concept
      }
      if (params.page !== undefined && params.page !== null) {
        cleanParams.page = params.page
      }
      if (params.page_size !== undefined && params.page_size !== null) {
        cleanParams.page_size = params.page_size
      }
      if (params.sort_by !== undefined && params.sort_by !== null) {
        cleanParams.sort_by = params.sort_by
      }
      if (params.order !== undefined && params.order !== null) {
        cleanParams.order = params.order
      }
      
      // 确保使用清理后的参数
      config.params = cleanParams
    }
    
    // 调试日志
    console.log('API请求:', config.method?.toUpperCase(), config.baseURL + config.url)
    if (config.params) {
      console.log('请求参数:', JSON.stringify(config.params, null, 2))
      const paramsStr = new URLSearchParams(config.params as any).toString()
      console.log('完整URL:', config.baseURL + config.url + (paramsStr ? '?' + paramsStr : ''))
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
    const fullUrl = response.config.baseURL + response.config.url
    console.log('API响应:', fullUrl, response.status, Array.isArray(response.data) ? `Array(${response.data.length})` : typeof response.data, response.data)
    return response.data
  },
  (error) => {
    const url = error.config?.url || error.request?.responseURL || 'unknown'
    const status = error.response?.status
    const data = error.response?.data
    console.error('API错误:', url, status || 'no status', data || 'no data', error.message || '')
    if (error.response) {
      const { status, data } = error.response
      if (status === 401) {
        localStorage.removeItem('token')
        window.location.href = '/login'
      } else if (status === 422) {
        // 422 错误通常是参数验证失败，不显示通用错误消息
        const detail = data?.detail
        if (Array.isArray(detail) && detail.length > 0) {
          ElMessage.error(detail.map((d: any) => d.msg || d).join(', '))
        } else if (typeof detail === 'string') {
          ElMessage.error(detail)
        } else {
          ElMessage.error('请求参数错误，请检查输入')
        }
      } else {
        ElMessage.error(data?.detail || '请求失败')
      }
    } else if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      ElMessage.error('请求超时，请稍后重试')
    } else {
      ElMessage.error('网络错误，请检查网络连接')
    }
    return Promise.reject(error)
  }
)

export default apiClient

