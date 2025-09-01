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

export interface ReadRegistersRequest {
  slave_id: number
  start_addr: number
  count: number
  function_code: number
}

export interface WriteRegisterRequest {
  slave_id: number
  addr: number
  value: number
}

export interface WriteRegistersRequest {
  slave_id: number
  start_addr: number
  values: number[]
}

export interface RegisterData {
  address: number
  value: number
}

export interface ReadRegistersResponse {
  slave_id: number
  start_addr: number
  count: number
  registers: RegisterData[]
}

export interface WriteResponse {
  slave_id: number
  success: boolean
  message: string
}

export interface RawDataRequest {
  data: string
}

export interface RawDataResponse {
  sent_data: string
  received_data: string
  timestamp: number
}

// API接口
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

  // 读取寄存器
  async readRegisters(request: ReadRegistersRequest): Promise<ReadRegistersResponse> {
    const response = await api.post('/serial/read-registers', request)
    return response.data
  },

  // 写入单个寄存器
  async writeRegister(request: WriteRegisterRequest): Promise<WriteResponse> {
    const response = await api.post('/serial/write-register', request)
    return response.data
  },

  // 写入多个寄存器
  async writeRegisters(request: WriteRegistersRequest): Promise<WriteResponse> {
    const response = await api.post('/serial/write-registers', request)
    return response.data
  },

  // 发送原始数据
  async sendRawData(request: RawDataRequest): Promise<RawDataResponse> {
    const response = await api.post('/serial/raw-data', request)
    return response.data
  },
}