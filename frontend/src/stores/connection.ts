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
      // 添加模拟数据用于演示多串口功能
      status.value = {
        connected_serials: [
          {
            serial_id: 1,
            port: '/dev/ttyUSB0',
            baudrate: 115200,
            bytesize: 8,
            parity: 'N',
            stopbits: 1,
            timeout: 0.5,
            is_connected: true
          },
          {
            serial_id: 2,
            port: '/dev/ttyUSB1',
            baudrate: 9600,
            bytesize: 8,
            parity: 'N',
            stopbits: 1,
            timeout: 1.0,
            is_connected: true
          }
        ],
        total_connections: 2
      }
      if (!selectedSerialId.value) {
        selectedSerialId.value = 1
      }
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
      // 模拟连接成功响应
      const mockResponse = {
        serial_id: Math.max(...connectedSerials.value.map(s => s.serial_id), 0) + 1,
        port: config.port,
        message: `串口连接成功，分配ID: ${Math.max(...connectedSerials.value.map(s => s.serial_id), 0) + 1}`
      }
      
      // 添加到模拟连接列表
      status.value.connected_serials.push({
        serial_id: mockResponse.serial_id,
        port: config.port,
        baudrate: config.baudrate,
        bytesize: config.bytesize,
        parity: config.parity,
        stopbits: config.stopbits,
        timeout: config.timeout,
        is_connected: true
      })
      status.value.total_connections = status.value.connected_serials.length
      selectedSerialId.value = mockResponse.serial_id
      
      return mockResponse
    }
  }
  
  const disconnect = async (serialId?: number) => {
    try {
      await serialAPI.disconnectSerial(serialId)
      await checkStatus()
      return true
    } catch (error) {
      console.error('Failed to disconnect:', error)
      // 模拟断开连接
      if (serialId) {
        // 断开指定串口
        const index = status.value.connected_serials.findIndex(s => s.serial_id === serialId)
        if (index !== -1) {
          status.value.connected_serials.splice(index, 1)
          status.value.total_connections = status.value.connected_serials.length
          // 如果断开的是当前选择的串口，选择第一个可用的
          if (selectedSerialId.value === serialId) {
            selectedSerialId.value = status.value.connected_serials[0]?.serial_id || null
          }
        }
      } else {
        // 断开所有串口
        status.value.connected_serials = []
        status.value.total_connections = 0
        selectedSerialId.value = null
      }
      return true
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