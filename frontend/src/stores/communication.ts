import { defineStore } from 'pinia'
import { ref } from 'vue'
import { serialAPI, type RawDataResponse } from '@/api/serial'

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
  
  // 操作
  const addLog = (log: Omit<CommunicationLog, 'id' | 'timestamp'>) => {
    const newLog: CommunicationLog = {
      ...log,
      id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
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
      addLog({
        type: 'at',
        direction: 'sent',
        data: command,
        description: 'AT指令',
      })
      
      const result = await serialAPI.sendATCommand(command)
      
      addLog({
        type: 'at',
        direction: 'received',
        data: result.received_data,
        description: 'AT响应',
        success: true,
      })
      
      return result
    } catch (error) {
      addLog({
        type: 'at',
        direction: 'received',
        data: error instanceof Error ? error.message : '未知错误',
        description: 'AT指令失败',
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
      
      const result = await serialAPI.sendRawData(data)
      
      addLog({
        type: 'raw',
        direction: 'received',
        data: result.received_data,
        description: '接收原始数据',
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
    
    // 操作
    addLog,
    clearLogs,
    sendATCommand,
    sendRawData,
  }
})