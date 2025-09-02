/**
 * 终端状态管理
 * 使用Pinia管理WebSocket终端的状态
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { WebSocketClient, type WSMessage } from '@/api/websocket'

export interface TerminalMessage {
  id: string
  type: 'command' | 'response' | 'error' | 'info' | 'system'
  content: string
  timestamp: Date
  success?: boolean
}

export const useTerminalStore = defineStore('terminal', () => {
  // 状态
  const messages = ref<TerminalMessage[]>([])
  const isConnected = ref(false)
  const isConnecting = ref(false)
  const currentCommand = ref('')
  const commandHistory = ref<string[]>([])
  const historyIndex = ref(-1)
  
  // WebSocket客户端实例
  let wsClient: WebSocketClient | null = null

  // 计算属性
  const connectionStatus = computed(() => {
    if (isConnecting.value) return 'connecting'
    if (isConnected.value) return 'connected'
    return 'disconnected'
  })

  // 生成消息ID
  const generateMessageId = (): string => {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  // 添加消息
  const addMessage = (message: Omit<TerminalMessage, 'id'>): void => {
    messages.value.push({
      id: generateMessageId(),
      ...message
    })
    
    // 限制消息数量，避免内存溢出
    if (messages.value.length > 1000) {
      messages.value.splice(0, messages.value.length - 1000)
    }
  }

  // 清空消息
  const clearMessages = (): void => {
    messages.value = []
  }

  // 连接WebSocket
  const connect = async (): Promise<void> => {
    if (isConnected.value || isConnecting.value) {
      return
    }

    try {
      isConnecting.value = true
      
      // 创建WebSocket客户端
      wsClient = new WebSocketClient()

      // 设置事件监听器
      wsClient.on('connect', (_message: WSMessage) => {
        isConnected.value = true
        isConnecting.value = false
        addMessage({
          type: 'system',
          content: '✅ WebSocket连接成功',
          timestamp: new Date()
        })
      })

      wsClient.on('disconnect', (_message: WSMessage) => {
        isConnected.value = false
        isConnecting.value = false
        addMessage({
          type: 'system',
          content: '❌ WebSocket连接断开',
          timestamp: new Date()
        })
      })

      wsClient.on('error', (message: WSMessage) => {
        isConnecting.value = false
        addMessage({
          type: 'error',
          content: `❌ 错误: ${message.error || message.message}`,
          timestamp: new Date(),
          success: false
        })
      })

      wsClient.on('response', (message: WSMessage) => {
        addMessage({
          type: 'response',
          content: message.message || '',
          timestamp: new Date(message.timestamp),
          success: message.success
        })
      })

      wsClient.on('info', (message: WSMessage) => {
        addMessage({
          type: 'info',
          content: message.message || '',
          timestamp: new Date(message.timestamp),
          success: true
        })
      })

      // 建立连接
      await wsClient.connect()

    } catch (error) {
      isConnecting.value = false
      console.error('WebSocket连接失败:', error)
      addMessage({
        type: 'error',
        content: `❌ 连接失败: ${error}`,
        timestamp: new Date(),
        success: false
      })
    }
  }

  // 断开连接
  const disconnect = (): void => {
    if (wsClient) {
      wsClient.disconnect()
      wsClient = null
    }
    isConnected.value = false
    isConnecting.value = false
  }

  // 发送命令
  const sendCommand = (command: string): void => {
    if (!command.trim()) return

    // 添加命令到历史记录
    if (commandHistory.value[commandHistory.value.length - 1] !== command.trim()) {
      commandHistory.value.push(command.trim())
      
      // 限制历史记录数量
      if (commandHistory.value.length > 100) {
        commandHistory.value.splice(0, commandHistory.value.length - 100)
      }
    }
    historyIndex.value = commandHistory.value.length

    // 显示命令
    addMessage({
      type: 'command',
      content: `$ ${command.trim()}`,
      timestamp: new Date()
    })

    // 发送命令
    if (wsClient && wsClient.isConnected) {
      wsClient.sendCommand(command.trim())
    } else {
      addMessage({
        type: 'error',
        content: '❌ WebSocket未连接',
        timestamp: new Date(),
        success: false
      })
    }

    // 清空当前命令
    currentCommand.value = ''
  }

  // 获取历史命令 (向上)
  const getPreviousCommand = (): string => {
    if (commandHistory.value.length === 0) return ''
    
    if (historyIndex.value > 0) {
      historyIndex.value--
    } else {
      historyIndex.value = 0
    }
    
    return commandHistory.value[historyIndex.value] || ''
  }

  // 获取历史命令 (向下)
  const getNextCommand = (): string => {
    if (commandHistory.value.length === 0) return ''
    
    if (historyIndex.value < commandHistory.value.length - 1) {
      historyIndex.value++
      return commandHistory.value[historyIndex.value] || ''
    } else {
      historyIndex.value = commandHistory.value.length
      return ''
    }
  }

  // 设置当前命令
  const setCurrentCommand = (command: string): void => {
    currentCommand.value = command
  }

  return {
    // 状态
    messages,
    isConnected,
    isConnecting,
    currentCommand,
    commandHistory,
    connectionStatus,
    
    // 方法
    connect,
    disconnect,
    sendCommand,
    addMessage,
    clearMessages,
    getPreviousCommand,
    getNextCommand,
    setCurrentCommand
  }
})