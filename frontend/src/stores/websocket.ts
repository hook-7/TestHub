import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { WebSocketClient, WSMessageType, type WSResponseMessage, type WSErrorMessage } from '@/services/websocket'

export const useWebSocketStore = defineStore('websocket', () => {
  // 状态
  const client = ref<WebSocketClient | null>(null)
  const isConnected = ref(false)
  const connectionStatus = ref<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected')
  const lastMessage = ref<WSResponseMessage | WSErrorMessage | null>(null)
  const messageHistory = ref<(WSResponseMessage | WSErrorMessage)[]>([])

  // 响应监听器机制 - 避免多个命令冲突
  const responseListeners = ref<Map<string, (message: any) => void>>(new Map())

  // 计算属性
  const connectionStatusText = computed(() => {
    switch (connectionStatus.value) {
      case 'disconnected':
        return '未连接'
      case 'connecting':
        return '连接中...'
      case 'connected':
        return '已连接'
      case 'error':
        return '连接错误'
      default:
        return '未知状态'
    }
  })

  const connectionStatusColor = computed(() => {
    switch (connectionStatus.value) {
      case 'disconnected':
        return 'info'
      case 'connecting':
        return 'warning'
      case 'connected':
        return 'success'
      case 'error':
        return 'danger'
      default:
        return 'info'
    }
  })

  // 操作
  const initializeClient = (clientId?: string) => {
    if (client.value) {
      client.value.disconnect()
    }
    
    client.value = new WebSocketClient(clientId)
    
    // 设置连接状态变化回调
    client.value.onConnectionChange((connected: boolean) => {
      isConnected.value = connected
      connectionStatus.value = connected ? 'connected' : 'disconnected'
    })

    // 设置消息回调
    client.value.onMessage((message: WSResponseMessage | WSErrorMessage) => {
      lastMessage.value = message
      messageHistory.value.push(message)
      
      // 限制历史消息数量，避免内存泄漏
      if (messageHistory.value.length > 1000) {
        messageHistory.value = messageHistory.value.slice(-500)
      }

      // 触发所有响应监听器 - 每个命令都有独立的监听器
      responseListeners.value.forEach((listener) => {
        listener(message)
      })
    })
  }

  const connect = async (): Promise<boolean> => {
    if (!client.value) {
      initializeClient()
    }

    // 如果已经连接，直接返回
    if (isConnected.value) {
      return true
    }

    connectionStatus.value = 'connecting'
    
    try {
      const success = await client.value!.connect()
      if (success) {
        connectionStatus.value = 'connected'
        isConnected.value = true
        return true
      } else {
        connectionStatus.value = 'error'
        return false
      }
    } catch (error) {
      console.error('WebSocket连接错误:', error)
      connectionStatus.value = 'error'
      return false
    }
  }

  const disconnect = () => {
    if (client.value) {
      client.value.disconnect()
      connectionStatus.value = 'disconnected'
      isConnected.value = false
    }
  }

  const sendCommand = async (command: string, serialId?: number, args: string[] = []): Promise<boolean> => {
    if (!client.value || !isConnected.value) {
      ElMessage.error('WebSocket未连接，请先连接')
      return false
    }

    try {
      const success = await client.value.sendCommand(command, serialId, args)
      if (!success) {
        ElMessage.error('命令发送失败')
      }
      return success
    } catch (error) {
      console.error('发送命令错误:', error)
      ElMessage.error('发送命令时发生错误')
      return false
    }
  }

  // 带重试机制的命令发送方法 - 只负责发送，不等待响应
  const sendCommandWithRetry = async (command: string, serialId?: number, args: string[] = [], maxRetries: number = 3): Promise<boolean> => {
    if (!client.value || !isConnected.value) {
      ElMessage.error('WebSocket未连接，请先连接')
      return false
    }

    let lastError: Error | null = null
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        console.log(`发送命令尝试 ${attempt}/${maxRetries}: ${command}`)
        
        const success = await client.value.sendCommand(command, serialId, args)
        if (!success) {
          throw new Error('命令发送失败')
        }

        console.log(`命令 ${command} 发送成功 (尝试 ${attempt})`)
        return true
        
      } catch (error) {
        lastError = error as Error
        console.warn(`命令发送失败 (尝试 ${attempt}/${maxRetries}):`, error)
        
        if (attempt < maxRetries) {
          console.log(`等待 1 秒后重试...`)
          await new Promise(resolve => setTimeout(resolve, 1000))
        }
      }
    }

    // 所有重试都失败了
    console.error(`命令发送失败，已重试 ${maxRetries} 次:`, lastError)
    ElMessage.error(`命令发送失败，已重试 ${maxRetries} 次`)
    return false
  }


  const clearMessageHistory = () => {
    messageHistory.value = []
    lastMessage.value = null
  }

  const getMessagesByType = (type: WSMessageType) => {
    return messageHistory.value.filter(msg => msg.type === type)
  }

  const getMessagesBySerialId = (serialId: number) => {
    return messageHistory.value.filter(msg => msg.serial_id === serialId)
  }

  // 添加响应监听器
  const addResponseListener = (commandId: string, listener: (message: any) => void) => {
    responseListeners.value.set(commandId, listener)
  }

  // 移除响应监听器
  const removeResponseListener = (commandId: string) => {
    responseListeners.value.delete(commandId)
  }

  return {
    // 状态
    client,
    isConnected,
    connectionStatus,
    lastMessage,
    messageHistory,
    
    // 计算属性
    connectionStatusText,
    connectionStatusColor,
    
    // 操作
    initializeClient,
    connect,
    disconnect,
    sendCommand,
    sendCommandWithRetry,
    clearMessageHistory,
    getMessagesByType,
    getMessagesBySerialId,
    addResponseListener,
    removeResponseListener,
  }
})
