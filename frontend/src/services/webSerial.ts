/**
 * Web Serial API 服务封装
 * 基于浏览器原生 Web Serial API 实现串口通信
 */

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

export interface RawDataResponse {
  serial_id: number
  sent_data: string
  received_data: string
  timestamp: number
}

export type SerialDataCallback = (data: string, serialId: number) => void

export class WebSerialService {
  private ports: Map<number, SerialPort> = new Map()
  private portConfigs: Map<number, SerialConfig> = new Map()
  private dataCallbacks: Map<number, SerialDataCallback> = new Map()
  private readers: Map<number, ReadableStreamDefaultReader> = new Map()
  private writers: Map<number, WritableStreamDefaultWriter> = new Map()
  private isReading: Map<number, boolean> = new Map()
  private dataBuffers: Map<number, string> = new Map() // 数据缓冲区


  constructor() {
    // 检查Web Serial API支持
    if (!this.isSupported()) {
      throw new Error('Web Serial API not supported in this browser. Please use Chrome 89+, Edge 89+, or Opera 76+.')
    }
  }

  /**
   * 检查Web Serial API是否支持
   */
  isSupported(): boolean {
    return 'serial' in navigator
  }

  /**
   * 获取下一个可用的串口ID（从1开始，复用断开的ID）
   */
  private getNextSerialId(): number {
    // 如果没有连接，从1开始
    if (this.ports.size === 0) {
      return 1
    }
    
    // 寻找最小的未使用ID，从1开始
    const usedIds = Array.from(this.ports.keys())
    for (let serialId = 1; serialId <= Math.max(...usedIds) + 1; serialId++) {
      if (!usedIds.includes(serialId)) {
        return serialId
      }
    }
    
    // 理论上不会到达这里，但为了安全起见
    return Math.max(...usedIds) + 1
  }

  /**
   * 获取可用串口列表
   * 注意：Web Serial API需要用户手动选择串口，无法直接枚举
   */
  async getAvailablePorts(): Promise<SerialPortInfo[]> {
    try {
      // 请求用户选择串口
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
        // 用户取消了选择
        return []
      }
      throw error
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

  /**
   * 连接串口
   */
  async connectSerial(config: SerialConfig): Promise<SerialConnectResponse> {
    try {
      // 请求用户选择串口
      const port = await navigator.serial.requestPort()
      
      // 配置串口参数
      const portConfig: SerialPortOpenOptions = {
        baudRate: config.baudrate,
        dataBits: config.bytesize as 7 | 8,
        parity: config.parity as 'none' | 'even' | 'odd',
        stopBits: config.stopbits as 1 | 2,
        flowControl: 'none'
      }

      // 打开串口
      await port.open(portConfig)

      const serialId = this.getNextSerialId()
      
      // 获取实际的端口信息
      const portInfo = port.getInfo()
      const actualPort = `COM${portInfo.usbVendorId}-${portInfo.usbProductId}` || 'Unknown'
      
      // 创建包含实际端口信息的配置
      const actualConfig = {
        ...config,
        port: actualPort
      }

      // 保存连接信息
      this.ports.set(serialId, port)
      this.portConfigs.set(serialId, actualConfig)

      // 不设置默认回调，等待外部设置

      // 异步启动数据读取
      this.startReading(serialId, port).catch(error => {
        console.error(`Error starting reading for serial ${serialId}:`, error)
      })

      console.log(`Serial port connected: ${actualPort} at ${config.baudrate} baud with serial_id ${serialId}`)
      
      return {
        serial_id: serialId,
        port: actualPort,
        message: `串口连接成功！分配ID: ${serialId}`
      }
    } catch (error) {
      console.error('Failed to connect serial port:', error)
      throw new Error(`串口连接失败: ${error instanceof Error ? error.message : '未知错误'}`)
    }
  }

  /**
   * 断开串口连接
   */
  async disconnectSerial(serialId?: number): Promise<boolean> {
    try {
      if (serialId !== undefined) {
        // 断开指定串口
        await this.disconnectSinglePort(serialId)
      } else {
        // 断开所有串口
        const portIds = Array.from(this.ports.keys())
        for (const id of portIds) {
          await this.disconnectSinglePort(id)
        }
      }
      return true
    } catch (error) {
      console.error('Failed to disconnect serial port:', error)
      throw new Error(`断开串口连接失败: ${error instanceof Error ? error.message : '未知错误'}`)
    }
  }

  /**
   * 断开单个串口
   */
  private async disconnectSinglePort(serialId: number): Promise<void> {
    const port = this.ports.get(serialId)
    if (!port) return

    // 停止读取
    this.isReading.set(serialId, false)
    
    // 关闭读取器
    const reader = this.readers.get(serialId)
    if (reader) {
      try {
        await reader.cancel()
      } catch (error) {
        console.warn('Error canceling reader:', error)
      }
      this.readers.delete(serialId)
    }

    // 关闭写入器
    const writer = this.writers.get(serialId)
    if (writer) {
      try {
        await writer.close()
      } catch (error) {
        console.warn('Error closing writer:', error)
      }
      this.writers.delete(serialId)
    }

    // 关闭串口
    try {
      await port.close()
    } catch (error) {
      console.warn('Error closing port:', error)
    }

    // 清理状态
    this.ports.delete(serialId)
    this.portConfigs.delete(serialId)
    this.dataCallbacks.delete(serialId)
    this.isReading.delete(serialId)
    this.dataBuffers.delete(serialId)

    console.log(`Serial port ${serialId} disconnected`)
  }

  /**
   * 获取连接状态
   */
  async getConnectionStatus(): Promise<SerialConnectionStatus> {
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

    return {
      connected_serials: connectedSerials,
      total_connections: connectedSerials.length
    }
  }

  /**
   * 发送AT指令
   */
  async sendATCommand(command: string, serialId?: number): Promise<RawDataResponse> {
    const targetSerialId = serialId || this.getFirstConnectedSerialId()
    if (targetSerialId === null) {
      throw new Error('没有连接的串口')
    }

    const port = this.ports.get(targetSerialId)
    if (!port) {
      throw new Error(`串口 ${targetSerialId} 未连接`)
    }

    try {
      // 获取写入器
      let writer = this.writers.get(targetSerialId)
      if (!writer) {
        writer = port.writable?.getWriter()
        if (!writer) {
          throw new Error(`串口 ${targetSerialId} 不可写`)
        }
        this.writers.set(targetSerialId, writer)
      }

      // 发送指令
      const data = new TextEncoder().encode(command + '\r\n')
      await writer.write(data)

      console.log(`Serial ${targetSerialId}: Sent command: ${command}`)

      return {
        serial_id: targetSerialId,
        sent_data: command,
        received_data: 'Command sent via Web Serial API',
        timestamp: Date.now()
      }
    } catch (error) {
      console.error(`Error sending command to serial ${targetSerialId}:`, error)
      throw new Error(`发送指令失败: ${error instanceof Error ? error.message : '未知错误'}`)
    }
  }

  /**
   * 发送原始数据
   */
  async sendRawData(hexData: string, serialId?: number): Promise<RawDataResponse> {
    const targetSerialId = serialId || this.getFirstConnectedSerialId()
    if (targetSerialId === null) {
      throw new Error('没有连接的串口')
    }

    const port = this.ports.get(targetSerialId)
    if (!port) {
      throw new Error(`串口 ${targetSerialId} 未连接`)
    }

    try {
      // 转换十六进制字符串为字节
      const cleanHex = hexData.replace(/\s+/g, '')
      if (cleanHex.length % 2 !== 0) {
        throw new Error('十六进制数据长度必须为偶数')
      }

      const bytes = new Uint8Array(cleanHex.length / 2)
      for (let i = 0; i < cleanHex.length; i += 2) {
        bytes[i / 2] = parseInt(cleanHex.substr(i, 2), 16)
      }

      // 获取写入器
      let writer = this.writers.get(targetSerialId)
      if (!writer) {
        writer = port.writable?.getWriter()
        if (!writer) {
          throw new Error(`串口 ${targetSerialId} 不可写`)
        }
        this.writers.set(targetSerialId, writer)
      }

      // 发送数据
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
      throw new Error(`发送原始数据失败: ${error instanceof Error ? error.message : '未知错误'}`)
    }
  }

  /**
   * 接收数据 - 等待指定时间内的数据接收
   */
  async receiveData(timeout: number = 5000, serialId?: number): Promise<RawDataResponse> {
    const targetSerialId = serialId || this.getFirstConnectedSerialId()
    if (targetSerialId === null) {
      throw new Error('没有连接的串口')
    }

    const port = this.ports.get(targetSerialId)
    if (!port) {
      throw new Error(`串口 ${targetSerialId} 未连接`)
    }

    return new Promise((resolve, reject) => {
      let receivedData = ''
      let timeoutId: number

      // 设置超时
      timeoutId = window.setTimeout(() => {
        this.dataCallbacks.delete(targetSerialId) // 清理临时回调
        reject(new Error(`接收数据超时 (${timeout}ms)`))
      }, timeout)

      // 设置临时数据回调
      const tempCallback = (data: string, serialId: number) => {
        if (serialId === targetSerialId) {
          receivedData += data + '\n'
          clearTimeout(timeoutId)
          this.dataCallbacks.delete(targetSerialId) // 清理临时回调
          resolve({
            serial_id: targetSerialId,
            sent_data: '',
            received_data: receivedData.trim(),
            timestamp: Date.now()
          })
        }
      }

      // 设置回调
      this.setDataCallback(targetSerialId, tempCallback)

      // 如果已经有数据在缓冲区，立即返回
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
        return
      }
    })
  }

  /**
   * 接收指定长度的数据
   */
  async receiveDataWithLength(length: number, timeout: number = 5000, serialId?: number): Promise<RawDataResponse> {
    const targetSerialId = serialId || this.getFirstConnectedSerialId()
    if (targetSerialId === null) {
      throw new Error('没有连接的串口')
    }

    const port = this.ports.get(targetSerialId)
    if (!port) {
      throw new Error(`串口 ${targetSerialId} 未连接`)
    }

    return new Promise((resolve, reject) => {
      let receivedData = ''
      let timeoutId: number

      // 设置超时
      timeoutId = window.setTimeout(() => {
        this.dataCallbacks.delete(targetSerialId) // 清理临时回调
        reject(new Error(`接收数据超时 (${timeout}ms)`))
      }, timeout)

      // 设置临时数据回调
      const tempCallback = (data: string, serialId: number) => {
        if (serialId === targetSerialId) {
          receivedData += data
          if (receivedData.length >= length) {
            clearTimeout(timeoutId)
            this.dataCallbacks.delete(targetSerialId) // 清理临时回调
            resolve({
              serial_id: targetSerialId,
              sent_data: '',
              received_data: receivedData.substring(0, length),
              timestamp: Date.now()
            })
          }
        }
      }

      // 设置回调
      this.setDataCallback(targetSerialId, tempCallback)

      // 如果缓冲区已经有足够的数据，立即返回
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
        return
      }
    })
  }

  /**
   * 发送指令并等待响应
   */
  async sendCommandAndWaitResponse(command: string, timeout: number = 5000, serialId?: number): Promise<RawDataResponse> {
    const targetSerialId = serialId || this.getFirstConnectedSerialId()
    if (targetSerialId === null) {
      throw new Error('没有连接的串口')
    }

    try {
      // 先发送指令
      const sendResult = await this.sendATCommand(command, targetSerialId)
      
      // 等待响应
      const receiveResult = await this.receiveData(timeout, targetSerialId)
      
      return {
        serial_id: targetSerialId,
        sent_data: sendResult.sent_data,
        received_data: receiveResult.received_data,
        timestamp: Date.now()
      }
    } catch (error) {
      console.error(`Error in sendCommandAndWaitResponse:`, error)
      throw new Error(`发送指令并等待响应失败: ${error instanceof Error ? error.message : '未知错误'}`)
    }
  }

  /**
   * 启动实时数据读取
   */
  async startRealtimeReading(serialId: number): Promise<void> {
    const port = this.ports.get(serialId)
    if (!port) {
      throw new Error(`串口 ${serialId} 未连接`)
    }

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
        console.log(`Serial ${serialId} raw data received:`, data);
        
        // 将数据添加到缓冲区
        const currentBuffer = this.dataBuffers.get(serialId) || ''
        const newBuffer = currentBuffer + data
        this.dataBuffers.set(serialId, newBuffer)
        console.log(`Serial ${serialId} buffer updated:`, newBuffer)
        
        // 检查是否有完整的消息（以换行符结尾）
        const lines = newBuffer.split('\r\n')
        if (lines.length > 1) {
          // 处理完整的行
          for (let i = 0; i < lines.length - 1; i++) {
            const line = lines[i].trim()
            if (line) {
              console.log(`Serial ${serialId} received line:`, line)
              const callback = this.dataCallbacks.get(serialId)
              if (callback) {
                console.log(`Calling callback for serial ${serialId}`)
                callback(line, serialId)
              } else {
                console.warn(`No callback set for serial ${serialId}`)
              }
            }
          }
          
          // 保留最后一个不完整的行
          this.dataBuffers.set(serialId, lines[lines.length - 1])
        } else {
          // 如果没有换行符，检查是否有其他分隔符（如\r）
          const crLines = newBuffer.split('\r')
          if (crLines.length > 1) {
            for (let i = 0; i < crLines.length - 1; i++) {
              const line = crLines[i].trim()
              if (line) {
                console.log(`Serial ${serialId} received line (CR):`, line)
                const callback = this.dataCallbacks.get(serialId)
                if (callback) {
                  console.log(`Calling callback for serial ${serialId}`)
                  callback(line, serialId)
                } else {
                  console.warn(`No callback set for serial ${serialId}`)
                }
              }
            }
            this.dataBuffers.set(serialId, crLines[crLines.length - 1])
          }
        }
        
        // 防止缓冲区无限增长
        if (newBuffer.length > 1000) {
          const callback = this.dataCallbacks.get(serialId)
          if (callback) {
            callback(newBuffer, serialId)
          }
          this.dataBuffers.set(serialId, '')
        }
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
   * 设置数据回调函数
   */
  setDataCallback(serialId: number, callback: SerialDataCallback): void {
    console.log(`Setting data callback for serial ${serialId}`)
    this.dataCallbacks.set(serialId, callback)
    console.log(`Data callback set for serial ${serialId}, total callbacks:`, this.dataCallbacks.size)
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
}

// 创建全局实例
export const webSerialService = new WebSerialService()
