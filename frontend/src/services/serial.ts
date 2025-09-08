/**
 * 前端串口通信服务
 * 使用 Web Serial API 实现串口通信
 */

import { ElMessage } from 'element-plus'

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

export interface RawDataResponse {
  serial_id: number
  sent_data: string
  received_data: string
  timestamp: number
}

// 串口连接管理器
class SerialConnectionManager {
  private connections: Map<number, SerialPort> = new Map()
  private portConfigs: Map<number, SerialConfig> = new Map()
  private connectedPorts: Map<number, string> = new Map()
  private nextSerialId = 1
  private dataCallbacks: Map<number, (data: string) => void> = new Map()
  private readingTasks: Map<number, ReadableStreamDefaultReader> = new Map()

  // 检查浏览器是否支持 Web Serial API
  isSupported(): boolean {
    return 'serial' in navigator
  }

  // 获取下一个可用的串口ID
  private getNextSerialId(): number {
    return this.nextSerialId++
  }

  // 获取可用串口列表
  async getAvailablePorts(): Promise<SerialPortInfo[]> {
    if (!this.isSupported()) {
      throw new Error('当前浏览器不支持 Web Serial API')
    }

    try {
      // Web Serial API 需要用户交互才能获取端口列表
      // 这里返回一个提示，实际获取需要用户点击按钮
      return []
    } catch (error) {
      console.error('获取串口列表失败:', error)
      throw error
    }
  }

  // 请求用户选择串口
  async requestPort(): Promise<SerialPort> {
    if (!this.isSupported()) {
      throw new Error('当前浏览器不支持 Web Serial API')
    }

    try {
      const port = await navigator.serial.requestPort()
      return port
    } catch (error) {
      if (error.name === 'NotAllowedError') {
        throw new Error('用户取消了串口选择')
      }
      throw error
    }
  }

  // 连接串口
  async connect(config: SerialConfig): Promise<number> {
    if (!this.isSupported()) {
      throw new Error('当前浏览器不支持 Web Serial API')
    }

    try {
      // 请求用户选择串口
      const port = await this.requestPort()
      
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

      // 分配串口ID
      const serialId = this.getNextSerialId()

      // 保存连接信息
      this.connections.set(serialId, port)
      this.portConfigs.set(serialId, config)
      this.connectedPorts.set(serialId, port.getInfo().usbVendorId ? `USB-${port.getInfo().usbVendorId}` : 'Unknown')

      // 启动数据读取
      this.startReading(serialId)

      ElMessage.success(`串口连接成功，分配ID: ${serialId}`)
      return serialId

    } catch (error) {
      console.error('串口连接失败:', error)
      throw error
    }
  }

  // 启动数据读取
  private async startReading(serialId: number) {
    const port = this.connections.get(serialId)
    if (!port) return

    try {
      const reader = port.readable?.getReader()
      if (!reader) return

      this.readingTasks.set(serialId, reader)

      // 持续读取数据
      while (true) {
        try {
          const { value, done } = await reader.read()
          if (done) break

          // 解码数据
          const data = new TextDecoder().decode(value)
          
          // 调用数据回调
          const callback = this.dataCallbacks.get(serialId)
          if (callback) {
            callback(data)
          }
        } catch (error) {
          console.error(`串口 ${serialId} 读取数据失败:`, error)
          break
        }
      }
    } catch (error) {
      console.error(`启动串口 ${serialId} 读取失败:`, error)
    } finally {
      this.readingTasks.delete(serialId)
    }
  }

  // 设置数据回调
  setDataCallback(serialId: number, callback: (data: string) => void) {
    this.dataCallbacks.set(serialId, callback)
  }

  // 发送数据
  async writeData(serialId: number, data: string): Promise<boolean> {
    const port = this.connections.get(serialId)
    if (!port) {
      throw new Error(`串口 ${serialId} 未连接`)
    }

    try {
      const writer = port.writable?.getWriter()
      if (!writer) {
        throw new Error('串口不可写')
      }

      const encoder = new TextEncoder()
      await writer.write(encoder.encode(data))
      writer.releaseLock()

      return true
    } catch (error) {
      console.error(`串口 ${serialId} 写入数据失败:`, error)
      throw error
    }
  }

  // 发送十六进制数据
  async writeHexData(serialId: number, hexData: string): Promise<boolean> {
    const port = this.connections.get(serialId)
    if (!port) {
      throw new Error(`串口 ${serialId} 未连接`)
    }

    try {
      // 清理十六进制字符串
      const cleanHex = hexData.replace(/\s+/g, '')
      
      // 验证十六进制格式
      if (!/^[0-9A-Fa-f]+$/.test(cleanHex)) {
        throw new Error('无效的十六进制数据格式')
      }

      if (cleanHex.length % 2 !== 0) {
        throw new Error('十六进制数据长度必须为偶数')
      }

      // 转换为字节数组
      const bytes = new Uint8Array(cleanHex.length / 2)
      for (let i = 0; i < cleanHex.length; i += 2) {
        bytes[i / 2] = parseInt(cleanHex.substr(i, 2), 16)
      }

      const writer = port.writable?.getWriter()
      if (!writer) {
        throw new Error('串口不可写')
      }

      await writer.write(bytes)
      writer.releaseLock()

      return true
    } catch (error) {
      console.error(`串口 ${serialId} 写入十六进制数据失败:`, error)
      throw error
    }
  }

  // 断开串口连接
  async disconnect(serialId?: number): Promise<boolean> {
    try {
      if (serialId === undefined) {
        // 断开所有连接
        const promises = Array.from(this.connections.keys()).map(id => this.disconnect(id))
        await Promise.all(promises)
        return true
      }

      const port = this.connections.get(serialId)
      if (!port) {
        return false
      }

      // 停止读取任务
      const reader = this.readingTasks.get(serialId)
      if (reader) {
        reader.cancel()
        this.readingTasks.delete(serialId)
      }

      // 关闭串口
      await port.close()

      // 清理连接信息
      this.connections.delete(serialId)
      this.portConfigs.delete(serialId)
      this.connectedPorts.delete(serialId)
      this.dataCallbacks.delete(serialId)

      ElMessage.success(`串口 ${serialId} 断开成功`)
      return true

    } catch (error) {
      console.error(`断开串口 ${serialId} 失败:`, error)
      throw error
    }
  }

  // 获取连接状态
  getConnectionStatus(): SerialConnectionInfo[] {
    const connectedSerials: SerialConnectionInfo[] = []
    
    for (const [serialId, port] of this.connections) {
      const config = this.portConfigs.get(serialId)
      const portName = this.connectedPorts.get(serialId) || 'Unknown'
      
      if (config) {
        connectedSerials.push({
          serial_id: serialId,
          port: portName,
          baudrate: config.baudrate,
          bytesize: config.bytesize,
          parity: config.parity,
          stopbits: config.stopbits,
          timeout: config.timeout,
          is_connected: true
        })
      }
    }

    return connectedSerials
  }

  // 检查串口是否连接
  isConnected(serialId: number): boolean {
    return this.connections.has(serialId)
  }

  // 获取连接信息
  getConnectionInfo(serialId?: number) {
    if (serialId === undefined) {
      return {
        connected_serials: this.getConnectionStatus(),
        total_connections: this.connections.size
      }
    }

    const port = this.connections.get(serialId)
    if (!port) {
      return { connected: false, serial_id: serialId }
    }

    const config = this.portConfigs.get(serialId)
    return {
      connected: true,
      serial_id: serialId,
      port: this.connectedPorts.get(serialId) || 'Unknown',
      baudrate: config?.baudrate || 9600,
      bytesize: config?.bytesize || 8,
      parity: config?.parity || 'N',
      stopbits: config?.stopbits || 1,
      timeout: config?.timeout || 0.5
    }
  }
}

// 创建全局实例
export const serialConnectionManager = new SerialConnectionManager()

// 前端串口API
export const frontendSerialAPI = {
  // 检查浏览器支持
  isSupported(): boolean {
    return serialConnectionManager.isSupported()
  },

  // 获取可用串口列表
  async getAvailablePorts(): Promise<SerialPortInfo[]> {
    return serialConnectionManager.getAvailablePorts()
  },

  // 连接串口
  async connectSerial(config: SerialConfig): Promise<{ serial_id: number; port: string; message: string }> {
    const serialId = await serialConnectionManager.connect(config)
    const portName = serialConnectionManager.connectedPorts.get(serialId) || 'Unknown'
    
    return {
      serial_id: serialId,
      port: portName,
      message: `串口连接成功，分配ID: ${serialId}`
    }
  },

  // 断开串口连接
  async disconnectSerial(serialId?: number): Promise<void> {
    await serialConnectionManager.disconnect(serialId)
  },

  // 获取连接状态
  async getConnectionStatus(): Promise<{ connected_serials: SerialConnectionInfo[]; total_connections: number }> {
    return serialConnectionManager.getConnectionInfo()
  },

  // 发送AT指令
  async sendATCommand(command: string, serialId?: number): Promise<RawDataResponse> {
    if (!serialId) {
      const connectedSerials = serialConnectionManager.getConnectionStatus()
      if (connectedSerials.length === 0) {
        throw new Error('没有连接的串口')
      }
      serialId = connectedSerials[0].serial_id
    }

    if (!serialConnectionManager.isConnected(serialId)) {
      throw new Error(`串口 ${serialId} 未连接`)
    }

    const timestamp = Date.now()
    
    // 发送指令
    await serialConnectionManager.writeData(serialId, command)
    
    // 返回模拟响应（实际响应通过回调处理）
    return {
      serial_id: serialId,
      sent_data: command,
      received_data: '已通过前端串口发送，等待响应...',
      timestamp
    }
  },

  // 发送原始数据
  async sendRawData(data: string, serialId?: number): Promise<RawDataResponse> {
    if (!serialId) {
      const connectedSerials = serialConnectionManager.getConnectionStatus()
      if (connectedSerials.length === 0) {
        throw new Error('没有连接的串口')
      }
      serialId = connectedSerials[0].serial_id
    }

    if (!serialConnectionManager.isConnected(serialId)) {
      throw new Error(`串口 ${serialId} 未连接`)
    }

    const timestamp = Date.now()
    
    // 发送十六进制数据
    await serialConnectionManager.writeHexData(serialId, data)
    
    // 返回模拟响应（实际响应通过回调处理）
    return {
      serial_id: serialId,
      sent_data: data,
      received_data: '已通过前端串口发送，等待响应...',
      timestamp
    }
  },

  // 设置数据回调
  setDataCallback(serialId: number, callback: (data: string) => void) {
    serialConnectionManager.setDataCallback(serialId, callback)
  },

  // 检查串口是否连接
  isSerialConnected(serialId: number): boolean {
    return serialConnectionManager.isConnected(serialId)
  }
}