import { api } from './index'

// 串口登录配置接口
export interface SerialLoginConfig {
  id?: number
  name: string
  port: string
  baudrate: number
  bytesize: number
  parity: string
  stopbits: number
  timeout: number
  auto_connect: boolean
  login_command?: string
  expected_response?: string
  retry_count: number
  retry_delay: number
  is_active?: boolean
  created_at?: string
  updated_at?: string
}

// 创建配置请求
export interface CreateSerialLoginConfigRequest {
  name: string
  port: string
  baudrate?: number
  bytesize?: number
  parity?: string
  stopbits?: number
  timeout?: number
  auto_connect?: boolean
  login_command?: string
  expected_response?: string
  retry_count?: number
  retry_delay?: number
}

// 更新配置请求
export interface UpdateSerialLoginConfigRequest {
  name?: string
  port?: string
  baudrate?: number
  bytesize?: number
  parity?: string
  stopbits?: number
  timeout?: number
  auto_connect?: boolean
  login_command?: string
  expected_response?: string
  retry_count?: number
  retry_delay?: number
}

// 测试请求
export interface SerialLoginTestRequest {
  config_id?: number
  temp_config?: Omit<SerialLoginConfig, 'id' | 'is_active' | 'created_at' | 'updated_at'>
}

// 测试响应
export interface SerialLoginTestResponse {
  success: boolean
  message: string
  connection_time: number
  login_time?: number
  response_data?: string
  error_details?: string
}

// API响应格式
export interface APIResponse<T = any> {
  code: number
  msg: string
  data: T
}

/**
 * 获取所有串口登录配置
 */
export const getSerialLoginConfigs = async (): Promise<APIResponse<SerialLoginConfig[]>> => {
  return await api.get('/serial-login/configs')
}

/**
 * 获取指定串口登录配置
 */
export const getSerialLoginConfig = async (configId: number): Promise<APIResponse<SerialLoginConfig>> => {
  return await api.get(`/serial-login/configs/${configId}`)
}

/**
 * 创建串口登录配置
 */
export const createSerialLoginConfig = async (config: CreateSerialLoginConfigRequest): Promise<APIResponse<SerialLoginConfig>> => {
  return await api.post('/serial-login/configs', config)
}

/**
 * 更新串口登录配置
 */
export const updateSerialLoginConfig = async (configId: number, config: UpdateSerialLoginConfigRequest): Promise<APIResponse<SerialLoginConfig>> => {
  return await api.put(`/serial-login/configs/${configId}`, config)
}

/**
 * 删除串口登录配置
 */
export const deleteSerialLoginConfig = async (configId: number): Promise<APIResponse> => {
  return await api.delete(`/serial-login/configs/${configId}`)
}

/**
 * 激活串口登录配置
 */
export const activateSerialLoginConfig = async (configId: number): Promise<APIResponse> => {
  return await api.post(`/serial-login/configs/${configId}/activate`)
}

/**
 * 测试串口登录配置
 */
export const testSerialLoginConfig = async (testRequest: SerialLoginTestRequest): Promise<APIResponse<SerialLoginTestResponse>> => {
  return await api.post('/serial-login/test', testRequest)
}

/**
 * 使用激活的配置连接串口
 */
export const connectWithActiveConfig = async (): Promise<APIResponse> => {
  return await api.post('/serial-login/connect')
}

/**
 * 获取当前激活的配置
 */
export const getActiveConfig = async (): Promise<APIResponse<SerialLoginConfig | null>> => {
  return await api.get('/serial-login/active-config')
}