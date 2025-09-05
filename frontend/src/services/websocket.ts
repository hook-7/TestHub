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
  DISCONNECT = 'disconnect',
  AUTO_AT = "auto_at",
  NOTIFICATION = "notification"
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

export interface WSNotificationMessage {
  type: WSMessageType.NOTIFICATION
  title: string
  message: string
  level: 'info' | 'warning' | 'error' | 'success'
  requireConfirm: boolean
  timestamp: string
  id?: string
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
  private onMessageCallback?: (message: WSResponseMessage | WSErrorMessage | WSNotificationMessage) => void
  private onConnectionChangeCallback?: (connected: boolean) => void

  constructor(clientId?: string) {
    this.clientId = clientId || this.generateClientId()
    this.url = this.buildWebSocketUrl()
  }

  /**
   * 构建WebSocket URL
   */
  private buildWebSocketUrl(): string {
    const { hostname, port, protocol } = window.location
    
    // 判断是否为HTTPS环境
    const isHttps = protocol === 'https:'
    const wsProtocol = isHttps ? 'wss' : 'ws'
    
    // 构建完整URL
    let wsUrl = `${wsProtocol}://${hostname}`
    
    // 端口处理
    const isDevelopment = process.env.NODE_ENV === 'development' || hostname === 'localhost' || hostname === '127.0.0.1'
    
    if (isDevelopment) {
      // 开发环境：使用当前前端端口，通过 Vite 代理转发到后端
      wsUrl += port ? `:${port}` : ''
      wsUrl += `/api/v1/ws/terminal/${this.clientId}`
    } else {
      // 生产环境：根据部署方式决定
      // 如果前后端同域部署或通过反向代理，使用相对路径
      if (port && !['80', '443'].includes(port)) {
        wsUrl += `:${port}`
      }
      wsUrl += `/api/v1/ws/terminal/${this.clientId}`
    }
    

    return wsUrl
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

        this.isConnecting = false
        this.reconnectAttempts = 0
        this.onConnectionChangeCallback?.(true)
        ElMessage.success('实时连接已建立')
      }

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)

          this.handleMessage(message)
        } catch (error) {
          console.error('解析WebSocket消息失败:', error)
        }
      }

      this.ws.onclose = (event) => {

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
  onMessage(callback: (message: WSResponseMessage | WSErrorMessage | WSNotificationMessage) => void) {
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
