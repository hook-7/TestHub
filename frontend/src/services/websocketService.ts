/**
 * WebSocket服务
 * 处理工作流相关的实时通信
 */

import { ElMessage, ElMessageBox } from 'element-plus'
import { useWorkflowStore } from '@/stores/workflow'

export interface WebSocketMessage {
  type: string
  [key: string]: any
}

export interface WorkflowConfirmMessage {
  type: 'workflow_confirm'
  execution_id: string
  step_id: string
  message: string
  options: string[]
  timeout?: number
  timestamp: string
}

export interface WorkflowLogMessage {
  type: 'workflow_log'
  execution_id: string
  step_id: string
  level: string
  message: string
  data?: any
  timestamp: string
}

export interface WorkflowStatusMessage {
  type: 'workflow_status'
  execution_id: string
  status: string
  current_step?: string
  message: string
  timestamp: string
}

export class WorkflowWebSocketService {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 3000
  private isConnecting = false
  private messageHandlers: Map<string, Function[]> = new Map()
  private clientId: string

  constructor() {
    this.clientId = `workflow_client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  /**
   * 连接WebSocket
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.isConnecting) {
        reject(new Error('Already connecting'))
        return
      }

      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        resolve()
        return
      }

      this.isConnecting = true
      
      // 构建WebSocket URL
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${protocol}//${window.location.host}/api/v1/ws/terminal/${this.clientId}`

      try {
        this.ws = new WebSocket(wsUrl)

        this.ws.onopen = () => {
          console.log('WorkflowWebSocket connected')
          this.isConnecting = false
          this.reconnectAttempts = 0
          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data)
            this.handleMessage(message)
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error)
          }
        }

        this.ws.onclose = (event) => {
          console.log('WorkflowWebSocket disconnected:', event.code, event.reason)
          this.isConnecting = false
          this.ws = null
          
          // 自动重连
          if (this.reconnectAttempts < this.maxReconnectAttempts) {
            setTimeout(() => {
              this.reconnectAttempts++
              console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
              this.connect().catch(console.error)
            }, this.reconnectDelay)
          }
        }

        this.ws.onerror = (error) => {
          console.error('WorkflowWebSocket error:', error)
          this.isConnecting = false
          reject(error)
        }

      } catch (error) {
        this.isConnecting = false
        reject(error)
      }
    })
  }

  /**
   * 断开连接
   */
  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.reconnectAttempts = this.maxReconnectAttempts // 阻止自动重连
  }

  /**
   * 发送消息
   */
  send(message: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    } else {
      console.error('WebSocket is not connected')
    }
  }

  /**
   * 处理接收到的消息
   */
  private handleMessage(message: WebSocketMessage) {
    console.log('Received WebSocket message:', message)

    // 调用注册的处理器
    const handlers = this.messageHandlers.get(message.type) || []
    handlers.forEach(handler => {
      try {
        handler(message)
      } catch (error) {
        console.error(`Error in message handler for ${message.type}:`, error)
      }
    })

    // 处理工作流相关消息
    switch (message.type) {
      case 'workflow_confirm':
        this.handleWorkflowConfirm(message as WorkflowConfirmMessage)
        break
      case 'workflow_log':
        this.handleWorkflowLog(message as WorkflowLogMessage)
        break
      case 'workflow_status':
        this.handleWorkflowStatus(message as WorkflowStatusMessage)
        break
    }
  }

  /**
   * 处理工作流确认消息
   */
  private async handleWorkflowConfirm(message: WorkflowConfirmMessage) {
    try {
      const result = await ElMessageBox.confirm(
        message.message,
        '工作流确认',
        {
          distinguishCancelAndClose: true,
          confirmButtonText: message.options[0] || '确认',
          cancelButtonText: message.options[1] || '取消',
          type: 'info'
        }
      )

      // 发送确认响应
      this.send({
        type: 'workflow_confirm_response',
        execution_id: message.execution_id,
        action: result === 'confirm' ? (message.options[0] || '确认') : (message.options[1] || '取消')
      })

    } catch (action) {
      // 用户取消或关闭
      const cancelAction = message.options[1] || '取消'
      this.send({
        type: 'workflow_confirm_response',
        execution_id: message.execution_id,
        action: cancelAction
      })
    }
  }

  /**
   * 处理工作流日志消息
   */
  private handleWorkflowLog(message: WorkflowLogMessage) {
    const workflowStore = useWorkflowStore()
    
    // 更新执行日志
    const execution = workflowStore.executions.find(e => e.id === message.execution_id)
    if (execution) {
      execution.logs.push({
        timestamp: message.timestamp,
        step_id: message.step_id,
        level: message.level,
        message: message.message,
        data: message.data
      })
    }

    // 显示重要日志消息
    if (message.level === 'ERROR') {
      ElMessage.error(`工作流错误: ${message.message}`)
    } else if (message.level === 'WARNING') {
      ElMessage.warning(`工作流警告: ${message.message}`)
    }
  }

  /**
   * 处理工作流状态消息
   */
  private handleWorkflowStatus(message: WorkflowStatusMessage) {
    const workflowStore = useWorkflowStore()
    
    // 更新执行状态
    const execution = workflowStore.executions.find(e => e.id === message.execution_id)
    if (execution) {
      execution.status = message.status as any
      execution.current_step = message.current_step
    }

    // 显示状态变化消息
    if (message.status === 'completed') {
      ElMessage.success(`工作流执行完成: ${message.message}`)
    } else if (message.status === 'failed') {
      ElMessage.error(`工作流执行失败: ${message.message}`)
    }
  }

  /**
   * 注册消息处理器
   */
  onMessage(type: string, handler: Function) {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, [])
    }
    this.messageHandlers.get(type)!.push(handler)
  }

  /**
   * 移除消息处理器
   */
  offMessage(type: string, handler: Function) {
    const handlers = this.messageHandlers.get(type)
    if (handlers) {
      const index = handlers.indexOf(handler)
      if (index >= 0) {
        handlers.splice(index, 1)
      }
    }
  }

  /**
   * 获取连接状态
   */
  get isConnected() {
    return this.ws?.readyState === WebSocket.OPEN
  }
}

// 全局WebSocket服务实例
export const workflowWebSocketService = new WorkflowWebSocketService()

// 自动连接（在应用启动时）
export const initWorkflowWebSocket = async () => {
  try {
    await workflowWebSocketService.connect()
    console.log('Workflow WebSocket service initialized')
  } catch (error) {
    console.error('Failed to initialize Workflow WebSocket service:', error)
  }
}