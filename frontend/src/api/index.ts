import axios, { AxiosInstance } from 'axios'
import { ElMessage } from 'element-plus'

// API响应格式
interface ApiResponse<T = any> {
  code: number
  msg: string
  data: T
}

// 自定义axios实例类型，拦截器返回完整的API响应
interface CustomAxiosInstance extends Omit<AxiosInstance, 'get' | 'post' | 'put' | 'delete'> {
  get<T = any>(url: string, config?: any): Promise<ApiResponse<T>>
  post<T = any>(url: string, data?: any, config?: any): Promise<ApiResponse<T>>
  put<T = any>(url: string, data?: any, config?: any): Promise<ApiResponse<T>>
  delete<T = any>(url: string, config?: any): Promise<ApiResponse<T>>
}

// 创建axios实例
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
}) as CustomAxiosInstance

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 自动添加会话ID到请求头
    if (typeof window !== 'undefined' && window.sessionId) {
      config.headers['X-Session-Id'] = window.sessionId
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    const { data } = response
    
    // 检查业务状态码
    if (data.code !== 0) {
      ElMessage.error(data.msg || '请求失败')
      return Promise.reject(new Error(data.msg || '请求失败'))
    }
    
    return data  // 返回完整的响应对象，包含code, msg, data字段
  },
  (error) => {
    const message = error.response?.data?.msg || error.message || '网络错误'
    
    // 如果是401错误（会话无效），可以在这里处理登出逻辑
    if (error.response?.status === 401) {
      // 会话相关错误，需要重新登录
      ElMessage.error('会话已过期，请重新登录')
      // 这里可以触发登出逻辑或跳转到登录页面
      if (typeof window !== 'undefined') {
        delete window.sessionId
        localStorage.removeItem('sessionId')
        localStorage.removeItem('sessionToken')
      }
    } else {
      ElMessage.error(message)
    }
    
    return Promise.reject(error)
  }
)

export { api, type CustomAxiosInstance }
export default api