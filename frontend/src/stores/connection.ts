import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { serialAPI, type SerialConnectionStatus, type SerialPortInfo, type SerialConnectionInfo, type SerialConfig } from '@/api/serial'

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
  const currentSerial = computed(() => {
    if (selectedSerialId.value !== null) {
      return connectedSerials.value.find(s => s.serial_id === selectedSerialId.value)
    }
    return connectedSerials.value[0] || null
  })
  const currentPort = computed(() => currentSerial.value?.port || '')
  
  // 操作
  const checkStatus = async () => {
    try {
      status.value = await serialAPI.getConnectionStatus()
      // 如果当前选择的串口已断开，自动选择第一个可用串口
      if (selectedSerialId.value !== null && !connectedSerials.value.find(s => s.serial_id === selectedSerialId.value)) {
        selectedSerialId.value = connectedSerials.value[0]?.serial_id || null
      }
    } catch (error) {
      console.error('Failed to check connection status:', error)
    }
  }
  
  const loadAvailablePorts = async () => {
    try {
      availablePorts.value = await serialAPI.getAvailablePorts()
    } catch (error) {
      console.error('Failed to load available ports:', error)
      availablePorts.value = []
    }
  }
  
  const autoDetectPort = async (): Promise<string | null> => {
    try {
      return await serialAPI.autoDetectPort()
    } catch (error) {
      console.error('Failed to auto detect port:', error)
      return null
    }
  }
  
  const connect = async (config: SerialConfig) => {
    try {
      const response = await serialAPI.connectSerial(config)
      await checkStatus()
      // 自动选择新连接的串口
      selectedSerialId.value = response.serial_id
      return response
    } catch (error) {
      console.error('Failed to connect:', error)
      throw error
    }
  }
  
  const disconnect = async (serialId?: number) => {
    try {
      await serialAPI.disconnectSerial(serialId)
      await checkStatus()
      return true
    } catch (error) {
      console.error('Failed to disconnect:', error)
      return false
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
    currentSerial,
    currentPort,
    
    // 操作
    checkStatus,
    loadAvailablePorts,
    autoDetectPort,
    connect,
    disconnect,
    selectSerial,
  }
})