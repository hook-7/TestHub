/**
 * Web Serial API 服务封装
 * 基于浏览器原生 Web Serial API 实现串口通信
 */

// ==================== 类型定义 ====================

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
  bytesize: 7 | 8
  parity: 'none' | 'even' | 'odd'
  stopbits: 1 | 2
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

export interface RawDataResponse {
  serial_id: number
  sent_data: string
  received_data: string
  timestamp: number
}

export type SerialDataCallback = (data: string, serialId: number) => void

// ==================== 错误类型 ====================

export class SerialError extends Error {
  constructor(message: string, public code?: string) {
    super(message)
    this.name = 'SerialError'
  }
}

export class SerialNotSupportedError extends SerialError {
  constructor() {
    super('Web Serial API not supported in this browser. Please use Chrome 89+, Edge 89+, or Opera 76+.', 'NOT_SUPPORTED')
  }
}

export class SerialConnectionError extends SerialError {
  constructor(message: string, public serialId?: number) {
    super(message, 'CONNECTION_ERROR')
  }
}

export class SerialDataError extends SerialError {
  constructor(message: string, public serialId?: number) {
    super(message, 'DATA_ERROR')
  }
}

// ==================== 主服务类 ====================

export class WebSerialService {
  // ==================== 私有属性 ====================
  private readonly ports = new Map<number, SerialPort>()
  private readonly portConfigs = new Map<number, SerialConfig>()
  private readonly dataCallbacks = new Map<number, SerialDataCallback>()
  private readonly readers = new Map<number, ReadableStreamDefaultReader>()
  private readonly writers = new Map<number, WritableStreamDefaultWriter>()
  private readonly isReading = new Map<number, boolean>()
  private readonly dataBuffers = new Map<number, string>()
  private readonly dataTimeouts = new Map<number, number>()

  // ==================== 常量 ====================
  private static readonly DEFAULT_TIMEOUT = 5000
  private static readonly BUFFER_FLUSH_TIMEOUT = 100
  private static readonly MAX_BUFFER_SIZE = 1000

  constructor() {
    this.checkSupport()
  }

  // ==================== 初始化方法 ====================
  
  private checkSupport(): void {
    if (!this.isSupported()) {
      throw new SerialNotSupportedError()
    }
  }

  // ==================== 公共API方法 ====================
  
  /**
   * 检查Web Serial API是否支持
   */
  isSupported(): boolean {
    return 'serial' in navigator
  }

  // ==================== 串口管理方法 ====================
  
  /**
   * 获取下一个可用的串口ID（从1开始，复用断开的ID）
   */
  private getNextSerialId(): number {
    if (this.ports.size === 0) {
      return 1
    }
    
    const usedIds = Array.from(this.ports.keys())
    for (let serialId = 1; serialId <= Math.max(...usedIds) + 1; serialId++) {
      if (!usedIds.includes(serialId)) {
        return serialId
      }
    }
    
    return Math.max(...usedIds) + 1
  }

  /**
   * 获取第一个已连接的串口ID
   */
  private getFirstConnectedSerialId(): number | null {
    for (const [serialId, port] of this.ports.entries()) {
      if (port.readable && port.writable) {
        return serialId
      }
    }
    return null
  }

  /**
   * 检查串口是否连接
   */
  isSerialConnected(serialId: number): boolean {
    const port = this.ports.get(serialId)
    return port !== undefined && port.readable !== null && port.writable !== null
  }

  // ==================== 串口发现方法 ====================
  
  /**
   * 获取可用串口列表
   * 注意：Web Serial API需要用户手动选择串口，无法直接枚举
   */
  async getAvailablePorts(): Promise<SerialPortInfo[]> {
    try {
      const port = await navigator.serial.requestPort()
      const info = port.getInfo()
      
      return [{
        device: `${info.usbVendorId?.toString(16).padStart(4, '0')}:${info.usbProductId?.toString(16).padStart(4, '0')}`,
        name: `USB Serial Device`,
        description: `USB Serial Device (VID:${info.usbVendorId}, PID:${info.usbProductId})`,
        hwid: `USB\\VID_${info.usbVendorId?.toString(16).padStart(4, '0')}&PID_${info.usbProductId?.toString(16).padStart(4, '0')}`,
        manufacturer: 'Unknown'
      }]
    } catch (error) {
      if (error instanceof DOMException && error.name === 'NotFoundError') {
        return []
      }
      throw new SerialConnectionError(`获取串口列表失败: ${error instanceof Error ? error.message : '未知错误'}`)
    }
  }

  /**
   * 自动检测串口（模拟实现）
   */
  async autoDetectPort(): Promise<string | null> {
    try {
      const ports = await this.getAvailablePorts()
      return ports.length > 0 ? ports[0].device : null
    } catch (error) {
      console.error('Auto detect port failed:', error)
      return null
    }
  }

  // ==================== 串口连接方法 ====================
  
  /**
   * 连接串口
   */
  async connectSerial(config: SerialConfig): Promise<SerialConnectResponse> {
    try {
      const port = await navigator.serial.requestPort()
      const portConfig = this.createPortConfig(config)
      
      await port.open(portConfig)

      const serialId = this.getNextSerialId()
      const actualPort = this.generatePortName(port)
      const actualConfig = { ...config, port: actualPort }

      this.ports.set(serialId, port)
      this.portConfigs.set(serialId, actualConfig)

      // 异步启动数据读取
      this.startReading(serialId, port).catch(error => {
        console.error(`Error starting reading for serial ${serialId}:`, error)
      })
      
      this.isReading.set(serialId, true)

      console.log(`Serial port connected: ${actualPort} at ${config.baudrate} baud with serial_id ${serialId}`)
      
      return {
        serial_id: serialId,
        port: actualPort,
        message: `串口连接成功！分配ID: ${serialId}`
      }
    } catch (error) {
      console.error('Failed to connect serial port:', error)
      throw new SerialConnectionError(`串口连接失败: ${error instanceof Error ? error.message : '未知错误'}`)
    }
  }

  /**
   * 创建串口配置
   */
  private createPortConfig(config: SerialConfig): SerialPortOpenOptions {
    return {
      baudRate: config.baudrate,
      dataBits: config.bytesize,
      parity: config.parity,
      stopBits: config.stopbits,
      flowControl: 'none'
    }
  }

  /**
   * 生成端口名称
   */
  private generatePortName(port: SerialPort): string {
    const portInfo = port.getInfo()
    return `COM${portInfo.usbVendorId}-${portInfo.usbProductId}` || 'Unknown'
  }

  /**
   * 断开串口连接
   */
  async disconnectSerial(serialId?: number): Promise<boolean> {
    try {
      if (serialId !== undefined) {
        await this.disconnectSinglePort(serialId)
      } else {
        const portIds = Array.from(this.ports.keys())
        for (const id of portIds) {
          await this.disconnectSinglePort(id)
        }
      }
      return true
    } catch (error) {
      console.error('Failed to disconnect serial port:', error)
      throw new SerialConnectionError(`断开串口连接失败: ${error instanceof Error ? error.message : '未知错误'}`)
    }
  }

  /**
   * 断开单个串口
   */
  private async disconnectSinglePort(serialId: number): Promise<void> {
    const port = this.ports.get(serialId)
    if (!port) return

    this.isReading.set(serialId, false)
    
    await this.closeReader(serialId)
    await this.closeWriter(serialId)
    await this.closePort(port)

    this.cleanupSerialData(serialId)
    console.log(`Serial port ${serialId} disconnected`)
  }

  /**
   * 关闭读取器
   */
  private async closeReader(serialId: number): Promise<void> {
    const reader = this.readers.get(serialId)
    if (reader) {
      try {
        await reader.cancel()
      } catch (error) {
        console.warn('Error canceling reader:', error)
      }
      this.readers.delete(serialId)
    }
  }

  /**
   * 关闭写入器
   */
  private async closeWriter(serialId: number): Promise<void> {
    const writer = this.writers.get(serialId)
    if (writer) {
      try {
        await writer.close()
      } catch (error) {
        console.warn('Error closing writer:', error)
      }
      this.writers.delete(serialId)
    }
  }

  /**
   * 关闭串口
   */
  private async closePort(port: SerialPort): Promise<void> {
    try {
      await port.close()
    } catch (error) {
      console.warn('Error closing port:', error)
    }
  }

  /**
   * 清理串口数据
   */
  private cleanupSerialData(serialId: number): void {
    this.ports.delete(serialId)
    this.portConfigs.delete(serialId)
    this.dataCallbacks.delete(serialId)
    this.isReading.delete(serialId)
    this.dataBuffers.delete(serialId)
    this.dataTimeouts.delete(serialId)
  }

  // ==================== 状态查询方法 ====================
  
  /**
   * 获取连接状态
   */
  async getConnectionStatus(): Promise<SerialConnectionStatus> {
    const connectedSerials = this.getConnectedSerials()
    return {
      connected_serials: connectedSerials,
      total_connections: connectedSerials.length
    }
  }

  /**
   * 获取已连接的串口列表
   */
  getConnectedSerials(): SerialConnectionInfo[] {
    const connectedSerials: SerialConnectionInfo[] = []
    
    for (const [serialId, port] of this.ports.entries()) {
      if (port.readable && port.writable) {
        const config = this.portConfigs.get(serialId)
        if (config) {
          connectedSerials.push({
            serial_id: serialId,
            port: config.port,
            baudrate: config.baudrate,
            bytesize: config.bytesize,
            parity: config.parity,
            stopbits: config.stopbits,
            timeout: config.timeout,
            is_connected: true
          })
        }
      }
    }

    return connectedSerials
  }

  // ==================== 数据发送方法 ====================
  
  /**
   * 发送AT指令
   */
  async sendATCommand(command: string, serialId?: number): Promise<RawDataResponse> {
    const targetSerialId = this.getTargetSerialId(serialId)
    const port = this.getPort(targetSerialId)

    try {
      const writer = await this.getWriter(targetSerialId, port)
      const data = new TextEncoder().encode(command + '\r\n')
      await writer.write(data)

      console.log(`Serial ${targetSerialId}: Sent command: ${command}`)

      return {
        serial_id: targetSerialId,
        sent_data: command,
        received_data: '',
        timestamp: Date.now()
      }
    } catch (error) {
      console.error(`Error sending command to serial ${targetSerialId}:`, error)
      throw new SerialDataError(`发送指令失败: ${error instanceof Error ? error.message : '未知错误'}`, targetSerialId)
    }
  }

  /**
   * 发送原始数据
   */
  async sendRawData(hexData: string, serialId?: number): Promise<RawDataResponse> {
    const targetSerialId = this.getTargetSerialId(serialId)
    const port = this.getPort(targetSerialId)

    try {
      const bytes = this.hexStringToBytes(hexData)
      const writer = await this.getWriter(targetSerialId, port)
      await writer.write(bytes)

      console.log(`Serial ${targetSerialId}: Sent raw data: ${hexData}`)

      return {
        serial_id: targetSerialId,
        sent_data: hexData,
        received_data: 'Raw data sent via Web Serial API',
        timestamp: Date.now()
      }
    } catch (error) {
      console.error(`Error sending raw data to serial ${targetSerialId}:`, error)
      throw new SerialDataError(`发送原始数据失败: ${error instanceof Error ? error.message : '未知错误'}`, targetSerialId)
    }
  }

  /**
   * 获取目标串口ID
   */
  private getTargetSerialId(serialId?: number): number {
    const targetSerialId = serialId || this.getFirstConnectedSerialId()
    if (targetSerialId === null) {
      throw new SerialDataError('没有连接的串口')
    }
    return targetSerialId
  }

  /**
   * 获取串口对象
   */
  private getPort(serialId: number): SerialPort {
    const port = this.ports.get(serialId)
    if (!port) {
      throw new SerialDataError(`串口 ${serialId} 未连接`, serialId)
    }
    return port
  }

  /**
   * 获取写入器
   */
  private async getWriter(serialId: number, port: SerialPort): Promise<WritableStreamDefaultWriter> {
    let writer = this.writers.get(serialId)
    if (!writer) {
      writer = port.writable?.getWriter()
      if (!writer) {
        throw new SerialDataError(`串口 ${serialId} 不可写`, serialId)
      }
      this.writers.set(serialId, writer)
    }
    return writer
  }

  /**
   * 将十六进制字符串转换为字节数组
   */
  private hexStringToBytes(hexData: string): Uint8Array {
    const cleanHex = hexData.replace(/\s+/g, '')
    if (cleanHex.length % 2 !== 0) {
      throw new SerialDataError('十六进制数据长度必须为偶数')
    }

    const bytes = new Uint8Array(cleanHex.length / 2)
    for (let i = 0; i < cleanHex.length; i += 2) {
      bytes[i / 2] = parseInt(cleanHex.substr(i, 2), 16)
    }
    return bytes
  }

  // ==================== 数据接收方法 ====================
  
  /**
   * 接收数据 - 等待指定时间内的数据接收
   */
  async receiveData(timeout: number = WebSerialService.DEFAULT_TIMEOUT, serialId?: number): Promise<RawDataResponse> {
    const targetSerialId = this.getTargetSerialId(serialId)
    this.getPort(targetSerialId) // 验证端口存在

    return new Promise((resolve, reject) => {
      let receivedData = ''
      let timeoutId: number

      timeoutId = window.setTimeout(() => {
        this.dataCallbacks.delete(targetSerialId)
        reject(new SerialDataError(`接收数据超时 (${timeout}ms)`, targetSerialId))
      }, timeout)

      const tempCallback = (data: string, serialId: number) => {
        if (serialId === targetSerialId) {
          receivedData += data + '\n'
          clearTimeout(timeoutId)
          this.dataCallbacks.delete(targetSerialId)
          resolve({
            serial_id: targetSerialId,
            sent_data: '',
            received_data: receivedData.trim(),
            timestamp: Date.now()
          })
        }
      }

      this.setDataCallback(targetSerialId, tempCallback)

      // 检查缓冲区数据
      const bufferData = this.dataBuffers.get(targetSerialId)
      if (bufferData && bufferData.trim()) {
        clearTimeout(timeoutId)
        this.dataCallbacks.delete(targetSerialId)
        resolve({
          serial_id: targetSerialId,
          sent_data: '',
          received_data: bufferData.trim(),
          timestamp: Date.now()
        })
      }
    })
  }

  /**
   * 接收指定长度的数据
   */
  async receiveDataWithLength(length: number, timeout: number = WebSerialService.DEFAULT_TIMEOUT, serialId?: number): Promise<RawDataResponse> {
    const targetSerialId = this.getTargetSerialId(serialId)
    this.getPort(targetSerialId) // 验证端口存在

    return new Promise((resolve, reject) => {
      let receivedData = ''
      let timeoutId: number

      timeoutId = window.setTimeout(() => {
        this.dataCallbacks.delete(targetSerialId)
        reject(new SerialDataError(`接收数据超时 (${timeout}ms)`, targetSerialId))
      }, timeout)

      const tempCallback = (data: string, serialId: number) => {
        if (serialId === targetSerialId) {
          receivedData += data
          if (receivedData.length >= length) {
            clearTimeout(timeoutId)
            this.dataCallbacks.delete(targetSerialId)
            resolve({
              serial_id: targetSerialId,
              sent_data: '',
              received_data: receivedData.substring(0, length),
              timestamp: Date.now()
            })
          }
        }
      }

      this.setDataCallback(targetSerialId, tempCallback)

      // 检查缓冲区数据
      const bufferData = this.dataBuffers.get(targetSerialId) || ''
      if (bufferData.length >= length) {
        clearTimeout(timeoutId)
        this.dataCallbacks.delete(targetSerialId)
        resolve({
          serial_id: targetSerialId,
          sent_data: '',
          received_data: bufferData.substring(0, length),
          timestamp: Date.now()
        })
      }
    })
  }

  /**
   * 发送指令并等待响应
   */
  async sendCommandAndWaitResponse(command: string, timeout: number = WebSerialService.DEFAULT_TIMEOUT, serialId?: number): Promise<RawDataResponse> {
    const targetSerialId = this.getTargetSerialId(serialId)

    try {
      const sendResult = await this.sendATCommand(command, targetSerialId)
      const receiveResult = await this.receiveData(timeout, targetSerialId)
      
      return {
        serial_id: targetSerialId,
        sent_data: sendResult.sent_data,
        received_data: receiveResult.received_data,
        timestamp: Date.now()
      }
    } catch (error) {
      console.error(`Error in sendCommandAndWaitResponse:`, error)
      throw new SerialDataError(`发送指令并等待响应失败: ${error instanceof Error ? error.message : '未知错误'}`, targetSerialId)
    }
  }

  // ==================== 实时读取方法 ====================
  
  /**
   * 启动实时数据读取
   */
  async startRealtimeReading(serialId: number): Promise<void> {
    const port = this.getPort(serialId)

    if (this.isReading.get(serialId)) {
      console.warn(`Serial ${serialId} is already reading`)
      return
    }

    await this.startReading(serialId, port)
  }

  /**
   * 停止实时数据读取
   */
  async stopRealtimeReading(serialId: number): Promise<void> {
    this.isReading.set(serialId, false)
    await this.closeReader(serialId)
  }

  /**
   * 启动数据读取循环
   */
  private async startReading(serialId: number, port: SerialPort): Promise<void> {
    if (!port.readable) {
      console.warn(`Serial ${serialId} is not readable`)
      return
    }

    const reader = port.readable.getReader()
    this.readers.set(serialId, reader)
    this.isReading.set(serialId, true)

    console.log(`Started reading from serial ${serialId}`)

    try {
      while (this.isReading.get(serialId)) {
        const { value, done } = await reader.read()
        if (done) break

        const data = new TextDecoder().decode(value)
        this.processReceivedData(serialId, data)
      }
    } catch (error) {
      console.error(`Error reading from serial ${serialId}:`, error)
    } finally {
      this.isReading.set(serialId, false)
      this.readers.delete(serialId)
      this.dataBuffers.delete(serialId)
    }
  }

  /**
   * 处理接收到的数据
   */
  private processReceivedData(serialId: number, data: string): void {
    console.log(`Serial ${serialId} received data:`, data)
    
    // 更新缓冲区
    const currentBuffer = this.dataBuffers.get(serialId) || ''
    const newBuffer = currentBuffer + data
    this.dataBuffers.set(serialId, newBuffer)
    
    // 处理完整消息
    if (newBuffer.endsWith('\r\n')) {
      this.processCompleteMessages(serialId, newBuffer)
      this.dataBuffers.set(serialId, '')
    } else {
      this.scheduleBufferFlush(serialId)
    }
    
    // 防止缓冲区过大
    this.checkBufferSize(serialId, newBuffer)
  }

  /**
   * 处理完整的消息
   */
  private processCompleteMessages(serialId: number, buffer: string): void {
    const lines = buffer.split('\r\n')
    for (let i = 0; i < lines.length - 1; i++) {
      const line = lines[i].trim()
      if (line) {
        this.triggerCallback(serialId, line)
      }
    }
  }

  /**
   * 安排缓冲区刷新
   */
  private scheduleBufferFlush(serialId: number): void {
    // 清除现有定时器
    const existingTimeout = this.dataTimeouts.get(serialId)
    if (existingTimeout) {
      clearTimeout(existingTimeout)
    }
    
    // 设置新的定时器
    const timeoutId = window.setTimeout(() => {
      const currentBuffer = this.dataBuffers.get(serialId) || ''
      const trimmedBuffer = currentBuffer.trim()
      if (trimmedBuffer) {
        this.triggerCallback(serialId, trimmedBuffer)
        this.dataBuffers.set(serialId, '')
      }
      this.dataTimeouts.delete(serialId)
    }, WebSerialService.BUFFER_FLUSH_TIMEOUT)
    
    this.dataTimeouts.set(serialId, timeoutId)
  }

  /**
   * 检查缓冲区大小
   */
  private checkBufferSize(serialId: number, buffer: string): void {
    if (buffer.length > WebSerialService.MAX_BUFFER_SIZE) {
      console.warn(`Serial ${serialId} buffer too large, forcing flush`)
      this.triggerCallback(serialId, buffer)
      this.dataBuffers.set(serialId, '')
    }
  }

  /**
   * 触发回调函数
   */
  private triggerCallback(serialId: number, data: string): void {
    const callback = this.dataCallbacks.get(serialId)
    if (callback) {
      console.log(`Serial ${serialId} calling callback with data:`, data)
      callback(data, serialId)
    } else {
      console.warn(`No callback set for serial ${serialId}`)
    }
  }

  // ==================== 回调管理方法 ====================
  
  /**
   * 设置数据回调函数
   */
  setDataCallback(serialId: number, callback: SerialDataCallback): void {
    console.log(`Setting data callback for serial ${serialId}`)
    this.dataCallbacks.set(serialId, callback)
    console.log(`Data callback set for serial ${serialId}, total callbacks:`, this.dataCallbacks.size)
  }
}

// ==================== 全局实例 ====================

// 创建全局实例
export const webSerialService = new WebSerialService()
