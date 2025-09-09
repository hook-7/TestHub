import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { webSerialService, type SerialConnectionStatus, type SerialPortInfo, type SerialConfig } from '@/services/webSerial'

export const useConnectionStore = defineStore('connection', () => {
  // 状态
  const status = ref<SerialConnectionStatus>({
    connected_serials: [],
    total_connections: 0
  })
  
  const availablePorts = ref<SerialPortInfo[]>([])
  const selectedSerialId = ref<number | null>(null) // 当前选择的串口ID
  
  // 计算属性
  const isConnected = computed(() => status.value.total_connections > 0)
  const connectedSerials = computed(() => status.value.connected_serials)
  
  // 操作
  const checkStatus = async () => {
    try {
      console.log('Checking connection status...')
      const newStatus = await webSerialService.getConnectionStatus()
      console.log('Received status from Web Serial API:', newStatus)
      status.value = newStatus
      console.log('Updated local status:', status.value)
      
      // 如果当前选择的串口已断开，自动选择第一个可用串口
      if (selectedSerialId.value !== null && !connectedSerials.value.find(s => s.serial_id === selectedSerialId.value)) {
        selectedSerialId.value = connectedSerials.value[0]?.serial_id || null
      }
      // 如果有连接但没有选择串口，自动选择第一个
      if (selectedSerialId.value === null && connectedSerials.value.length > 0) {
        selectedSerialId.value = connectedSerials.value[0].serial_id
      }
    } catch (error) {
      console.error('Failed to check connection status:', error)
      // 清空状态，避免显示错误数据
      status.value = {
        connected_serials: [],
        total_connections: 0
      }
      selectedSerialId.value = null
    }
  }
  
  const loadAvailablePorts = async () => {
    try {
      availablePorts.value = await webSerialService.getAvailablePorts()
    } catch (error) {
      console.error('Failed to load available ports:', error)
      // 清空端口列表，避免显示错误数据
      availablePorts.value = []
    }
  }
  
  const autoDetectPort = async (): Promise<string | null> => {
    try {
      return await webSerialService.autoDetectPort()
    } catch (error) {
      console.error('Failed to auto detect port:', error)
      return null
    }
  }
  
  const connect = async (config: SerialConfig) => {
    try {
      const response = await webSerialService.connectSerial(config)
      // 先更新状态，再选择串口
      await checkStatus()
      // 自动选择新连接的串口
      selectedSerialId.value = response.serial_id
      return response
    } catch (error) {
      console.error('Failed to connect:', error)
      // 抛出错误，让调用者处理
      throw error
    }
  }
  
  const disconnect = async (serialId?: number) => {
    try {
      console.log('Disconnecting serial:', serialId)
      await webSerialService.disconnectSerial(serialId)
      console.log('Disconnect API call completed, checking status...')
      // 更新状态
      await checkStatus()
      console.log('Status check completed, current connections:', status.value.connected_serials.length)
      return true
    } catch (error) {
      console.error('Failed to disconnect:', error)
      // 抛出错误，让调用者处理
      throw error
    }
  }
  
  const selectSerial = (serialId: number) => {
    if (connectedSerials.value.find(s => s.serial_id === serialId)) {
      selectedSerialId.value = serialId
    }
  }
  
  return {
    // 状态
    status,
    availablePorts,
    selectedSerialId,
    
    // 计算属性
    isConnected,
    connectedSerials,
    
    // 操作
    checkStatus,
    loadAvailablePorts,
    autoDetectPort,
    connect,
    disconnect,
    selectSerial,
  }
})