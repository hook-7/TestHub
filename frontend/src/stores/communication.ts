import { defineStore } from 'pinia'
import { ref } from 'vue'
import { serialAPI, type ReadRegistersResponse, type WriteResponse, type RawDataResponse } from '@/api/serial'

export interface CommunicationLog {
  id: string
  timestamp: number
  type: 'read' | 'write' | 'raw'
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
  
  const readRegisters = async (request: any): Promise<ReadRegistersResponse | null> => {
    try {
      addLog({
        type: 'read',
        direction: 'sent',
        data: JSON.stringify(request),
        description: `读取从站${request.slave_id}地址${request.start_addr}开始${request.count}个寄存器`,
      })
      
      const result = await serialAPI.readRegisters(request)
      
      addLog({
        type: 'read',
        direction: 'received',
        data: JSON.stringify(result),
        description: `读取成功，获得${result.registers.length}个寄存器值`,
        success: true,
      })
      
      return result
    } catch (error) {
      addLog({
        type: 'read',
        direction: 'received',
        data: error instanceof Error ? error.message : '未知错误',
        description: '读取失败',
        success: false,
      })
      throw error
    }
  }
  
  const writeRegister = async (request: any): Promise<WriteResponse> => {
    try {
      addLog({
        type: 'write',
        direction: 'sent',
        data: JSON.stringify(request),
        description: `写入从站${request.slave_id}地址${request.addr}值${request.value}`,
      })
      
      const result = await serialAPI.writeRegister(request)
      
      addLog({
        type: 'write',
        direction: 'received',
        data: JSON.stringify(result),
        description: result.success ? '写入成功' : '写入失败',
        success: result.success,
      })
      
      return result
    } catch (error) {
      addLog({
        type: 'write',
        direction: 'received',
        data: error instanceof Error ? error.message : '未知错误',
        description: '写入失败',
        success: false,
      })
      throw error
    }
  }
  
  const writeRegisters = async (request: any): Promise<WriteResponse> => {
    try {
      addLog({
        type: 'write',
        direction: 'sent',
        data: JSON.stringify(request),
        description: `批量写入从站${request.slave_id}地址${request.start_addr}开始${request.values.length}个寄存器`,
      })
      
      const result = await serialAPI.writeRegisters(request)
      
      addLog({
        type: 'write',
        direction: 'received',
        data: JSON.stringify(result),
        description: result.success ? '批量写入成功' : '批量写入失败',
        success: result.success,
      })
      
      return result
    } catch (error) {
      addLog({
        type: 'write',
        direction: 'received',
        data: error instanceof Error ? error.message : '未知错误',
        description: '批量写入失败',
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
      
      const result = await serialAPI.sendRawData({ data })
      
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
    readRegisters,
    writeRegister,
    writeRegisters,
    sendRawData,
  }
})