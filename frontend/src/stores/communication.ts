import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { RawDataResponse } from '@/api/serial'
import { serialAPI } from '@/api/serial'
import { ElMessage } from 'element-plus'
import { WebSocketClient, WSMessageType } from '@/services/websocket'
import type { WSResponseMessage, WSErrorMessage, WSNotificationMessage } from '@/services/websocket'

export interface CommunicationLog {
  id: string
  timestamp: number
  type: 'at' | 'raw'
  direction: 'sent' | 'received'
  data: string
  description: string
  success?: boolean
}

export const useCommunicationStore = defineStore('communication', () => {
  // 状态
  const logs = ref<CommunicationLog[]>([])
  const maxLogs = ref(1000) // 最大日志条数

  // WebSocket相关状态
  const wsClient = ref<WebSocketClient | null>(null)
  const wsConnected = ref(false)

  // 通知对话框状态
  const showNotificationDialog = ref(false)
  const currentNotification = ref<WSNotificationMessage | null>(null)

  // 计算属性
  const logCount = computed(() => logs.value.length)
  const isRealTimeConnected = computed(() => wsConnected.value)

  // 初始化WebSocket
  const initializeWebSocket = async () => {
    if (wsClient.value) return

    try {
      wsClient.value = new WebSocketClient()
      
      // 设置消息回调
      wsClient.value.onMessage((message: WSResponseMessage | WSErrorMessage | WSNotificationMessage) => {
        handleWebSocketMessage(message)
      })

      // 设置连接状态回调
      wsClient.value.onConnectionChange((connected: boolean) => {
        wsConnected.value = connected
        addLog({
          type: 'at',
          direction: 'received',
          description: connected ? 'WebSocket连接已建立' : 'WebSocket连接已断开',
          data: `连接状态: ${connected ? '已连接' : '已断开'}`,
          success: connected
        })
      })

      // 连接WebSocket
      const connected = await wsClient.value.connect()
      if (!connected) {
        ElMessage.error('WebSocket连接失败，请检查后端服务')
        throw new Error('WebSocket连接失败')
      }
    } catch (error) {
      console.error('初始化WebSocket失败:', error)
      ElMessage.error('WebSocket初始化失败，请检查后端服务')
      throw error
    }
  }

  // 处理WebSocket消息
  const handleWebSocketMessage = (message: WSResponseMessage | WSErrorMessage | WSNotificationMessage) => {
    const isError = message.type === WSMessageType.ERROR

    // 处理通知消息
    if (message.type === WSMessageType.NOTIFICATION) {
      const notificationMsg = message as WSNotificationMessage
      
      // 记录通知日志
      addLog({
        type: 'at',
        direction: 'received',
        description: `系统通知: ${notificationMsg.title}`,
        data: notificationMsg.message,
        success: notificationMsg.level !== 'error'
      })

      // 显示通知对话框
      currentNotification.value = notificationMsg
      showNotificationDialog.value = true

      return
    }

    if (message.type === WSMessageType.AUTO_AT) {
      addLog({
        type: 'at',
        direction: 'sent',
        description: isError ? '命令执行错误' : '命令执行结果',
        data: (message as WSResponseMessage).message,
        success: !isError
      })
      addLog({
        type: 'at',
        direction: 'received',
        description: isError ? '命令执行错误' : '命令执行结果',
        data: (message as WSResponseMessage).data?.received_data,
        success: !isError
      })
      return
    }

    addLog({
      type: 'at',
      direction: 'received',
      description: isError ? '命令执行错误' : '命令执行结果',
      data: isError ? (message as WSErrorMessage).error : (message as WSResponseMessage).message,
      success: !isError
    })

  }

  // 断开WebSocket
  const disconnectWebSocket = () => {
    if (wsClient.value) {
      wsClient.value.disconnect()
      wsClient.value = null
      wsConnected.value = false
    }
  }

  // 处理通知确认
  const handleNotificationConfirm = (notification: WSNotificationMessage) => {
    // 记录用户确认日志
    addLog({
      type: 'at',
      direction: 'sent',
      description: `用户确认通知: ${notification.title}`,
      data: `已确认消息: ${notification.message}`,
      success: true
    })

    // 如果需要，可以发送确认消息到后端
    if (wsClient.value && wsClient.value.isConnected() && notification.id) {
      const confirmMessage = {
        type: 'notification_confirm',
        notification_id: notification.id,
        timestamp: new Date().toISOString()
      }
      
      try {
        wsClient.value.sendCommand('NOTIFICATION_CONFIRM', [JSON.stringify(confirmMessage)])
      } catch (error) {
        console.error('发送通知确认失败:', error)
      }
    }
  }

  // 关闭通知对话框
  const closeNotificationDialog = () => {
    showNotificationDialog.value = false
    currentNotification.value = null
  }
  
  // 操作
  const addLog = (log: Omit<CommunicationLog, 'id' | 'timestamp'>) => {
    const newLog: CommunicationLog = {
      ...log,
      id: Date.now().toString() + Math.random().toString(36).substring(2, 11),
      timestamp: Date.now(),
    }
    
    logs.value.unshift(newLog)
    
    // 限制日志数量
    if (logs.value.length > maxLogs.value) {
      logs.value = logs.value.slice(0, maxLogs.value)
    }
  }
  
  const clearLogs = () => {
    logs.value = []
  }
  
  const sendATCommand = async (command: string): Promise<RawDataResponse> => {
    try {
      // 记录发送的指令
      addLog({
        type: 'at',
        direction: 'sent',
        data: command,
        description: '发送实时指令',
        success: true
      })

      // 确保WebSocket连接
      if (!wsClient.value || !wsClient.value.isConnected()) {
        await initializeWebSocket()
      }

      // 使用WebSocket发送指令
      if (wsClient.value && wsClient.value.isConnected()) {
        const success = await wsClient.value.sendCommand(command)
        if (!success) {
          throw new Error('WebSocket发送失败')
        }
        
        // WebSocket模式下，响应通过回调处理，这里只返回成功状态
        return { 
          sent_data: command,
          received_data: '已通过WebSocket发送，等待响应...',
          timestamp: Date.now()
        }
      } else {
        throw new Error('WebSocket连接失败')
      }
    } catch (error) {
      addLog({
        type: 'at',
        direction: 'received',
        data: error instanceof Error ? error.message : '未知错误',
        description: '指令发送失败',
        success: false,
      })
      throw error
    }
  }
  
  const sendRawData = async (data: string): Promise<RawDataResponse> => {
    try {
      addLog({
        type: 'raw',
        direction: 'sent',
        data: data,
        description: '发送原始数据',
      })
      
      // 使用REST API发送原始16进制数据，确保与后端处理逻辑一致
      const result = await serialAPI.sendRawData(data)
      
      // 记录接收到的数据
      addLog({
        type: 'raw',
        direction: 'received',
        data: result.received_data,
        description: '接收原始数据响应',
        success: true,
      })
      
      return result
    } catch (error) {
      addLog({
        type: 'raw',
        direction: 'received',
        data: error instanceof Error ? error.message : '未知错误',
        description: '原始数据通信失败',
        success: false,
      })
      throw error
    }
  }
  
  return {
    // 状态
    logs,
    maxLogs,
    wsConnected,
    showNotificationDialog,
    currentNotification,
    
    // 计算属性
    logCount,
    isRealTimeConnected,
    
    // 操作
    addLog,
    clearLogs,
    sendATCommand,
    sendRawData,
    initializeWebSocket,
    disconnectWebSocket,
    handleNotificationConfirm,
    closeNotificationDialog
  }
})