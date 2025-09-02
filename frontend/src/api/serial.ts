import api from './index'

export interface SerialPortInfo {
  device: string
  name: string
  description: string
  hwid: string
  manufacturer: string
}

export interface SerialConfig {
  port: string
  baudrate: number
  bytesize: number
  parity: string
  stopbits: number
  timeout: number
}

export interface SerialConnectionStatus {
  connected: boolean
  port?: string
  baudrate?: number
  bytesize?: number
  parity?: string
  stopbits?: number
  timeout?: number
}

export interface RawDataRequest {
  data: string
}

export interface RawDataResponse {
  sent_data: string
  received_data: string
  timestamp: number
}

// API接口 - 专注于AT指令交互
export const serialAPI = {
  // 获取可用串口列表
  async getAvailablePorts(): Promise<SerialPortInfo[]> {
    const response = await api.get('/serial/ports')
    return response.data
  },

  // 自动检测串口
  async autoDetectPort(): Promise<string> {
    const response = await api.get('/serial/auto-detect')
    return response.data.port
  },

  // 连接串口
  async connectSerial(config: SerialConfig): Promise<void> {
    await api.post('/serial/connect', config)
  },

  // 断开串口连接
  async disconnectSerial(): Promise<void> {
    await api.post('/serial/disconnect')
  },

  // 获取连接状态
  async getConnectionStatus(): Promise<SerialConnectionStatus> {
    const response = await api.get('/serial/status')
    return response.data
  },

  // 发送AT指令
  async sendATCommand(command: string): Promise<RawDataResponse> {
    const response = await api.post('/serial/send-at', { data: command })
    return response.data
  },

  // 发送原始数据
  async sendRawData(data: string): Promise<RawDataResponse> {
    const response = await api.post('/serial/raw-data', { data })
    return response.data
  },
}