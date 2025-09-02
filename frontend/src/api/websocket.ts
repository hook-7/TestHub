/**
 * WebSocket API 客户端
 * 处理与后端的WebSocket通信
 */

export interface WSMessage {
  type: 'command' | 'response' | 'error' | 'info' | 'connect' | 'disconnect'
  message?: string
  command?: string
  args?: string[]
  data?: any
  timestamp: string
  success?: boolean
  error?: string
  code?: number
}

export interface WSCommandMessage {
  type: 'command'
  command: string
  args?: string[]
  timestamp?: string
}

export interface WSResponseMessage {
  type: 'response' | 'error' | 'info'
  message: string
  data?: any
  timestamp: string
  success: boolean
}

export class WebSocketClient {
  private ws: WebSocket | null = null
  private clientId: string
  private baseUrl: string
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectInterval = 1000
  private listeners: Map<string, ((message: WSMessage) => void)[]> = new Map()

  constructor(clientId?: string) {
    this.clientId = clientId || this.generateClientId()
    // 根据当前页面协议确定WebSocket协议
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    this.baseUrl = `${protocol}//${host}/api/v1/terminal/ws/terminal/${this.clientId}`
  }

  private generateClientId(): string {
    return `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  /**
   * 连接WebSocket
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.baseUrl)

        this.ws.onopen = () => {
          console.log('WebSocket连接已建立')
          this.reconnectAttempts = 0
          this.emit('connect', {
            type: 'connect',
            message: 'WebSocket连接成功',
            timestamp: new Date().toISOString()
          })
          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            const message: WSMessage = JSON.parse(event.data)
            console.log('收到WebSocket消息:', message)
            this.emit('message', message)
            this.emit(message.type, message)
          } catch (error) {
            console.error('解析WebSocket消息失败:', error)
          }
        }

        this.ws.onclose = (event) => {
          console.log('WebSocket连接已关闭:', event.code, event.reason)
          this.emit('disconnect', {
            type: 'disconnect',
            message: `连接已关闭: ${event.reason}`,
            timestamp: new Date().toISOString()
          })
          this.handleReconnect()
        }

        this.ws.onerror = (error) => {
          console.error('WebSocket错误:', error)
          this.emit('error', {
            type: 'error',
            message: 'WebSocket连接错误',
            timestamp: new Date().toISOString(),
            error: 'Connection error'
          })
          reject(error)
        }

      } catch (error) {
        reject(error)
      }
    })
  }

  /**
   * 断开WebSocket连接
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  /**
   * 发送命令
   */
  sendCommand(command: string): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.error('WebSocket未连接')
      this.emit('error', {
        type: 'error',
        message: 'WebSocket未连接',
        timestamp: new Date().toISOString(),
        error: 'Not connected'
      })
      return
    }

    const message: WSCommandMessage = {
      type: 'command',
      command: command.trim(),
      timestamp: new Date().toISOString()
    }

    try {
      this.ws.send(JSON.stringify(message))
      console.log('发送命令:', message)
    } catch (error) {
      console.error('发送命令失败:', error)
      this.emit('error', {
        type: 'error',
        message: '发送命令失败',
        timestamp: new Date().toISOString(),
        error: String(error)
      })
    }
  }

  /**
   * 添加事件监听器
   */
  on(event: string, callback: (message: WSMessage) => void): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, [])
    }
    this.listeners.get(event)!.push(callback)
  }

  /**
   * 移除事件监听器
   */
  off(event: string, callback?: (message: WSMessage) => void): void {
    if (!this.listeners.has(event)) return

    if (callback) {
      const callbacks = this.listeners.get(event)!
      const index = callbacks.indexOf(callback)
      if (index > -1) {
        callbacks.splice(index, 1)
      }
    } else {
      this.listeners.delete(event)
    }
  }

  /**
   * 触发事件
   */
  private emit(event: string, message: WSMessage): void {
    const callbacks = this.listeners.get(event) || []
    callbacks.forEach(callback => {
      try {
        callback(message)
      } catch (error) {
        console.error('事件回调执行失败:', error)
      }
    })
  }

  /**
   * 处理重连
   */
  private handleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('达到最大重连次数，停止重连')
      this.emit('error', {
        type: 'error',
        message: '连接失败，请检查网络或刷新页面重试',
        timestamp: new Date().toISOString(),
        error: 'Max reconnect attempts reached'
      })
      return
    }

    this.reconnectAttempts++
    console.log(`尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)

    setTimeout(() => {
      this.connect().catch(error => {
        console.error('重连失败:', error)
      })
    }, this.reconnectInterval * this.reconnectAttempts)
  }

  /**
   * 获取连接状态
   */
  get isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN
  }

  /**
   * 获取客户端ID
   */
  get id(): string {
    return this.clientId
  }
}