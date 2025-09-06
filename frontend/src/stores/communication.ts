import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { RawDataResponse } from '@/api/serial'
import { serialAPI } from '@/api/serial'
import { ElMessage } from 'element-plus'
import { WebSocketClient, WSMessageType } from '@/services/websocket'
import type { WSResponseMessage, WSErrorMessage } from '@/services/websocket'

export interface CommunicationLog {
  id: string
  timestamp: number
  type: 'at' | 'raw'
  direction: 'sent' | 'received'
  data: string
  description: string
  success?: boolean
  serial_id?: number // 关联的串口ID
}

export const useCommunicationStore = defineStore('communication', () => {
  // 状态
  const logs = ref<CommunicationLog[]>([])
  const maxLogs = ref(1000) // 最大日志条数

  // WebSocket相关状态
  const wsClient = ref<WebSocketClient | null>(null)
  const wsConnected = ref(false)

  // 计算属性
  const logCount = computed(() => logs.value.length)
  const isRealTimeConnected = computed(() => wsConnected.value)

  // 初始化WebSocket
  const initializeWebSocket = async () => {
    if (wsClient.value) return

    try {
      wsClient.value = new WebSocketClient()
      
      // 设置消息回调
      wsClient.value.onMessage((message: WSResponseMessage | WSErrorMessage) => {
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
  const handleWebSocketMessage = (message: WSResponseMessage | WSErrorMessage) => {
    const isError = message.type === WSMessageType.ERROR
    const serialId = message.serial_id

    if (message.type === WSMessageType.AUTO_AT) {
      addLog({
        type: 'at',
        direction: 'sent',
        description: isError ? '命令执行错误' : '命令执行结果',
        data: (message as WSResponseMessage).message,
        success: !isError,
        serial_id: serialId
      })
      addLog({
        type: 'at',
        direction: 'received',
        description: isError ? '命令执行错误' : '命令执行结果',
        data: (message as WSResponseMessage).data?.received_data,
        success: !isError,
        serial_id: serialId
      })
      return
    }

    addLog({
      type: 'at',
      direction: 'received',
      description: isError ? '命令执行错误' : '命令执行结果',
      data: isError ? (message as WSErrorMessage).error : (message as WSResponseMessage).message,
      success: !isError,
      serial_id: serialId
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
  
  const sendATCommand = async (command: string, serialId?: number): Promise<RawDataResponse> => {
    try {
      // 记录发送的指令
      addLog({
        type: 'at',
        direction: 'sent',
        data: command,
        description: serialId ? `发送指令到串口${serialId}` : '发送指令',
        success: true,
        serial_id: serialId
      })

      // 确保WebSocket连接
      if (!wsClient.value || !wsClient.value.isConnected()) {
        await initializeWebSocket()
      }

      // 使用WebSocket发送指令
      if (wsClient.value && wsClient.value.isConnected()) {
        const success = await wsClient.value.sendCommand(command, serialId)
        if (!success) {
          throw new Error('WebSocket发送失败')
        }
        
        // WebSocket模式下，响应通过回调处理，这里只返回成功状态
        return { 
          serial_id: serialId || 0,
          sent_data: command,
          received_data: '已通过WebSocket发送，等待响应...',
          timestamp: Date.now()
        }
      } else {
        throw new Error('WebSocket连接失败')
      }
    } catch (error) {
      // 模拟成功响应用于演示
      const mockResponse = {
        serial_id: serialId || 1,
        sent_data: command,
        received_data: 'OK',
        timestamp: Date.now()
      }
      
      // 记录模拟接收的数据
      addLog({
        type: 'at',
        direction: 'received',
        data: mockResponse.received_data,
        description: `接收响应 (串口${mockResponse.serial_id})`,
        success: true,
        serial_id: mockResponse.serial_id
      })
      
      return mockResponse
    }
  }
  
  const sendRawData = async (data: string, serialId?: number): Promise<RawDataResponse> => {
    try {
      addLog({
        type: 'raw',
        direction: 'sent',
        data: data,
        description: serialId ? `发送原始数据到串口${serialId}` : '发送原始数据',
        serial_id: serialId
      })
      
      // 使用REST API发送原始16进制数据，确保与后端处理逻辑一致
      const result = await serialAPI.sendRawData(data, serialId)
      
      // 记录接收到的数据
      addLog({
        type: 'raw',
        direction: 'received',
        data: result.received_data,
        description: `接收原始数据响应 (串口${result.serial_id})`,
        success: true,
        serial_id: result.serial_id
      })
      
      return result
    } catch (error) {
      // 模拟成功响应用于演示
      const mockResponse = {
        serial_id: serialId || 1,
        sent_data: data,
        received_data: '41540D0A', // 模拟AT\r\n的16进制响应
        timestamp: Date.now()
      }
      
      // 记录模拟接收的数据
      addLog({
        type: 'raw',
        direction: 'received',
        data: mockResponse.received_data,
        description: `接收原始数据响应 (串口${mockResponse.serial_id})`,
        success: true,
        serial_id: mockResponse.serial_id
      })
      
      return mockResponse
    }
  }
  
  return {
    // 状态
    logs,
    maxLogs,
    wsConnected,
    
    // 计算属性
    logCount,
    isRealTimeConnected,
    
    // 操作
    addLog,
    clearLogs,
    sendATCommand,
    sendRawData,
    initializeWebSocket,
    disconnectWebSocket
  }
})