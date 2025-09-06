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

export interface SerialConnectionInfo {
  serial_id: number
  port: string
  baudrate: number
  bytesize: number
  parity: string
  stopbits: number
  timeout: number
  is_connected: boolean
}

export interface SerialConnectionStatus {
  connected_serials: SerialConnectionInfo[]
  total_connections: number
}

export interface SerialConnectResponse {
  serial_id: number
  port: string
  message: string
}

export interface RawDataRequest {
  data: string
  serial_id?: number
}

export interface RawDataResponse {
  serial_id: number
  sent_data: string
  received_data: string
  timestamp: number
}

// API接口 - 支持通用指令交互
export const serialAPI = {
  // 获取可用串口列表
  async getAvailablePorts(): Promise<SerialPortInfo[]> {
    const response = await api.get<SerialPortInfo[]>('/serial/ports')
    return response
  },

  // 自动检测串口
  async autoDetectPort(): Promise<string> {
    const response = await api.get<{ port: string }>('/serial/auto-detect')
    return response.port
  },

  // 连接串口
  async connectSerial(config: SerialConfig): Promise<SerialConnectResponse> {
    const response = await api.post<SerialConnectResponse>('/serial/connect', config)
    return response
  },

  // 断开串口连接
  async disconnectSerial(serialId?: number): Promise<void> {
    await api.post('/serial/disconnect', { serial_id: serialId })
  },

  // 获取连接状态
  async getConnectionStatus(): Promise<SerialConnectionStatus> {
    const response = await api.get<SerialConnectionStatus>('/serial/status')
    return response
  },

  // 发送指令（支持AT指令和其他自定义指令）
  async sendATCommand(command: string, serialId?: number): Promise<RawDataResponse> {
    const response = await api.post<RawDataResponse>('/serial/send-at', { 
      data: command, 
      serial_id: serialId 
    })
    return response
  },

  // 发送原始数据
  async sendRawData(data: string, serialId?: number): Promise<RawDataResponse> {
    const response = await api.post<RawDataResponse>('/serial/raw-data', { 
      data, 
      serial_id: serialId 
    })
    return response
  },
}