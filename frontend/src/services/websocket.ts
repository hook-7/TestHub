/**
 * WebSocket客户端服务
 * 用于实时指令交互
 */

import { ElMessage } from 'element-plus'

// WebSocket消息类型
export enum WSMessageType {
  COMMAND = 'command',
  RESPONSE = 'response',
  ERROR = 'error', 
  INFO = 'info',
  CONNECT = 'connect',
  DISCONNECT = 'disconnect'
}

// WebSocket消息接口
export interface WSCommandMessage {
  type: WSMessageType.COMMAND
  command: string
  args?: string[]
  timestamp?: string
}

export interface WSResponseMessage {
  type: WSMessageType
  message: string
  data?: any
  timestamp: string
  success: boolean
}

export interface WSErrorMessage {
  type: WSMessageType.ERROR
  error: string
  code: number
  timestamp: string
}

// WebSocket客户端类
export class WebSocketClient {
  private ws: WebSocket | null = null
  private clientId: string
  private url: string
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private isConnecting = false
  private isManualDisconnect = false

  // 事件回调
  private onMessageCallback?: (message: WSResponseMessage | WSErrorMessage) => void
  private onConnectionChangeCallback?: (connected: boolean) => void

  constructor(clientId?: string) {
    this.clientId = clientId || this.generateClientId()
    this.url = `ws://localhost:8000/api/v1/terminal/ws/terminal/${this.clientId}`
  }

  private generateClientId(): string {
    return `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  /**
   * 连接WebSocket
   */
  async connect(): Promise<boolean> {
    if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
      return true
    }

    this.isConnecting = true
    this.isManualDisconnect = false

    try {
      this.ws = new WebSocket(this.url)

      this.ws.onopen = () => {
        console.log('WebSocket连接成功')
        this.isConnecting = false
        this.reconnectAttempts = 0
        this.onConnectionChangeCallback?.(true)
        ElMessage.success('实时连接已建立')
      }

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          console.log('收到WebSocket消息:', message)
          this.handleMessage(message)
        } catch (error) {
          console.error('解析WebSocket消息失败:', error)
        }
      }

      this.ws.onclose = (event) => {
        console.log('WebSocket连接关闭:', event.code, event.reason)
        this.isConnecting = false
        this.onConnectionChangeCallback?.(false)
        
        if (!this.isManualDisconnect && event.code !== 1000) {
          this.reconnect()
        }
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket连接错误:', error)
        this.isConnecting = false
        this.onConnectionChangeCallback?.(false)
      }

      return true
    } catch (error) {
      console.error('创建WebSocket连接失败:', error)
      this.isConnecting = false
      this.onConnectionChangeCallback?.(false)
      return false
    }
  }

  /**
   * 断开连接
   */
  disconnect() {
    this.isManualDisconnect = true
    if (this.ws) {
      this.ws.close(1000, '手动断开')
      this.ws = null
    }
    this.onConnectionChangeCallback?.(false)
  }

  /**
   * 重新连接
   */
  private async reconnect() {
    if (this.isManualDisconnect || this.reconnectAttempts >= this.maxReconnectAttempts) {
      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        ElMessage.error('WebSocket重连失败，请检查网络连接')
      }
      return
    }

    this.reconnectAttempts++
    console.log(`尝试重连 WebSocket (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)

    setTimeout(() => {
      this.connect()
    }, this.reconnectDelay * this.reconnectAttempts)
  }

  /**
   * 发送命令
   */
  async sendCommand(command: string, args: string[] = []): Promise<boolean> {
    if (!this.isConnected()) {
      ElMessage.error('WebSocket未连接，正在尝试重连...')
      await this.connect()
      if (!this.isConnected()) {
        return false
      }
    }

    try {
      const message: WSCommandMessage = {
        type: WSMessageType.COMMAND,
        command: command, 
        args,
        timestamp: new Date().toISOString()
      }

      this.ws!.send(JSON.stringify(message))
      console.log('发送WebSocket命令:', message)
      return true
    } catch (error) {
      console.error('发送WebSocket命令失败:', error)
      ElMessage.error('发送命令失败')
      return false
    }
  }

  /**
   * 处理接收到的消息
   */
  private handleMessage(message: any) {
    if (this.onMessageCallback) {
      this.onMessageCallback(message)
    }

    // 根据消息类型显示不同的提示
    switch (message.type) {
      case WSMessageType.ERROR:
        ElMessage.error(message.error || '命令执行失败')
        break
      case WSMessageType.INFO:
        if (message.message && !message.message.includes('欢迎')) {
          ElMessage.info(message.message)
        }
        break
    }
  }

  /**
   * 检查连接状态
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }

  /**
   * 获取连接状态
   */
  getConnectionState(): string {
    if (!this.ws) return 'CLOSED'
    
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING: return 'CONNECTING'
      case WebSocket.OPEN: return 'OPEN'
      case WebSocket.CLOSING: return 'CLOSING'
      case WebSocket.CLOSED: return 'CLOSED'
      default: return 'UNKNOWN'
    }
  }

  /**
   * 设置消息回调
   */
  onMessage(callback: (message: WSResponseMessage | WSErrorMessage) => void) {
    this.onMessageCallback = callback
  }

  /**
   * 设置连接状态变化回调
   */
  onConnectionChange(callback: (connected: boolean) => void) {
    this.onConnectionChangeCallback = callback
  }

  /**
   * 获取客户端ID
   */
  getClientId(): string {
    return this.clientId
  }
}
