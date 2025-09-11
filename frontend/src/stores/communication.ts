import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { webSerialService, type RawDataResponse } from '@/services/webSerial'

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

  // Web Serial API相关状态
  const isRealTimeConnected = ref(false)

  // 计算属性
  const isWebSerialConnected = computed(() => isRealTimeConnected.value)

  // 初始化Web Serial API
  const initializeWebSerial = async () => {
    try {
      // 检查Web Serial API支持
      if (!webSerialService.isSupported()) {
        throw new Error('Web Serial API不支持，请使用Chrome 89+、Edge 89+或Opera 76+')
      }

      // 获取已连接的串口并设置数据回调
      const connectedSerials = webSerialService.getConnectedSerials()
      console.log('Initializing Web Serial API with connected serials:', connectedSerials)
      
      for (const serial of connectedSerials) {
        console.log(`Setting data callback for serial ${serial.serial_id}`)
        webSerialService.setDataCallback(serial.serial_id, (data: string, serialId: number) => {
          console.log(`Data callback triggered for serial ${serialId}:`, data)
          addLog({
            type: 'at',
            direction: 'received',
            description: `接收数据 (串口#${serialId})`,
            data: data,
            success: true,
            serial_id: serialId
          })
        })
      }

      isRealTimeConnected.value = connectedSerials.length > 0
      
      if (isRealTimeConnected.value) {
        addLog({
          type: 'at',
          direction: 'received',
          description: 'Web Serial API已初始化',
          data: `已连接 ${connectedSerials.length} 个串口`,
          success: true
        })
      }
    } catch (error) {
      console.error('初始化Web Serial API失败:', error)
      ElMessage.error('Web Serial API初始化失败')
      throw error
    }
  }

  // 设置串口数据回调（用于新连接的串口）
  const setSerialDataCallback = (serialId: number) => {
    console.log(`Setting data callback for serial ${serialId}`)
    webSerialService.setDataCallback(serialId, (data: string, serialId: number) => {
      console.log(`Data callback triggered for serial ${serialId}:`, data)
      addLog({
        type: 'at',
        direction: 'received',
        description: `接收数据 (串口#${serialId})`,
        data: data,
        success: true,
        serial_id: serialId
      })
    })
  }

  // 断开Web Serial API
  const disconnectWebSerial = () => {
    isRealTimeConnected.value = false
    addLog({
      type: 'at',
      direction: 'received',
      description: 'Web Serial API已断开',
      data: '所有串口连接已断开',
      success: false
    })
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
      // 使用Web Serial API发送指令
      const result = await webSerialService.sendATCommand(command, serialId)
      
      // 只记录一次发送日志
      addLog({
        type: 'at',
        direction: 'sent',
        data: result.sent_data,
        description: `发送指令 (串口#${result.serial_id})`,
        success: true,
        serial_id: result.serial_id
      })
      
      return result
    } catch (error) {
      console.error('发送AT指令失败:', error)
      
      // 记录发送失败
      addLog({
        type: 'at',
        direction: 'sent',
        data: command,
        description: `发送失败: ${error instanceof Error ? error.message : '未知错误'}`,
        success: false,
        serial_id: serialId
      })
      
      throw error
    }
  }
  
  const sendRawData = async (data: string, serialId?: number): Promise<RawDataResponse> => {
    try {
      // 使用Web Serial API发送原始数据
      const result = await webSerialService.sendRawData(data, serialId)
      
      // 只记录一次发送日志
      addLog({
        type: 'raw',
        direction: 'sent',
        data: result.sent_data,
        description: `发送原始数据 (串口#${result.serial_id})`,
        success: true,
        serial_id: result.serial_id
      })
      
      return result
    } catch (error) {
      console.error('发送原始数据失败:', error)
      
      // 记录发送失败
      addLog({
        type: 'raw',
        direction: 'sent',
        data: data,
        description: `发送失败: ${error instanceof Error ? error.message : '未知错误'}`,
        success: false,
        serial_id: serialId
      })
      
      throw error
    }
  }
  
  return {
    // 状态
    logs,
    maxLogs,
    isRealTimeConnected,
    
    // 计算属性
    isWebSerialConnected,
    
    // 操作
    addLog,
    clearLogs,
    sendATCommand,
    sendRawData,
    initializeWebSerial,
    disconnectWebSerial,
    setSerialDataCallback
  }
})