import axios, { AxiosInstance } from 'axios'
import { ElMessage } from 'element-plus'

// 自定义axios实例类型，拦截器会直接返回数据
interface CustomAxiosInstance extends Omit<AxiosInstance, 'get' | 'post' | 'put' | 'delete'> {
  get<T = any>(url: string, config?: any): Promise<T>
  post<T = any>(url: string, data?: any, config?: any): Promise<T>
  put<T = any>(url: string, data?: any, config?: any): Promise<T>
  delete<T = any>(url: string, config?: any): Promise<T>
}

// 创建axios实例
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
}) as CustomAxiosInstance

// 请求拦截器
api.interceptors.request.use(
  (config) => {
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
    
    return data.data  // 返回实际的业务数据
  },
  (error) => {
    const message = error.response?.data?.msg || error.message || '网络错误'
    
    ElMessage.error(message)
    
    return Promise.reject(error)
  }
)

export { api, type CustomAxiosInstance }
export default api