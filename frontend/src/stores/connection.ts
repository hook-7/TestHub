import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { serialAPI, type SerialConnectionStatus, type SerialPortInfo, type SerialConfig } from '@/api/serial'
import { frontendSerialAPI } from '@/services/serial'

export const useConnectionStore = defineStore('connection', () => {
  // 状态
  const status = ref<SerialConnectionStatus>({
    connected_serials: [],
    total_connections: 0
  })
  
  const availablePorts = ref<SerialPortInfo[]>([])
  const selectedSerialId = ref<number | null>(null) // 当前选择的串口ID
  
  // 前端串口相关状态
  const useFrontendSerial = ref(false) // 是否使用前端串口
  const frontendSerialSupported = ref(false) // 浏览器是否支持Web Serial API
  
  // 计算属性
  const isConnected = computed(() => status.value.total_connections > 0)
  const connectedSerials = computed(() => status.value.connected_serials)
  
  // 检查前端串口支持
  const checkFrontendSerialSupport = () => {
    frontendSerialSupported.value = frontendSerialAPI.isSupported()
    return frontendSerialSupported.value
  }
  
  // 切换到前端串口模式
  const switchToFrontendSerial = () => {
    if (!checkFrontendSerialSupport()) {
      throw new Error('当前浏览器不支持 Web Serial API')
    }
    useFrontendSerial.value = true
  }
  
  // 切换到后端串口模式
  const switchToBackendSerial = () => {
    useFrontendSerial.value = false
  }
  
  // 操作
  const checkStatus = async () => {
    try {
      console.log('Checking connection status...')
      
      if (useFrontendSerial.value) {
        // 使用前端串口
        const newStatus = await frontendSerialAPI.getConnectionStatus()
        console.log('Received frontend status:', newStatus)
        status.value = newStatus
      } else {
        // 使用后端串口
        const newStatus = await serialAPI.getConnectionStatus()
        console.log('Received backend status from API:', newStatus)
        status.value = newStatus
      }
      
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
      if (useFrontendSerial.value) {
        // 前端串口模式下，端口列表需要用户交互获取
        availablePorts.value = []
      } else {
        availablePorts.value = await serialAPI.getAvailablePorts()
      }
    } catch (error) {
      console.error('Failed to load available ports:', error)
      // 清空端口列表，避免显示错误数据
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
      let response
      
      if (useFrontendSerial.value) {
        // 使用前端串口连接
        response = await frontendSerialAPI.connectSerial(config)
      } else {
        // 使用后端串口连接
        response = await serialAPI.connectSerial(config)
      }
      
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
      
      if (useFrontendSerial.value) {
        // 使用前端串口断开
        await frontendSerialAPI.disconnectSerial(serialId)
      } else {
        // 使用后端串口断开
        await serialAPI.disconnectSerial(serialId)
      }
      
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
    useFrontendSerial,
    frontendSerialSupported,
    
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
    checkFrontendSerialSupport,
    switchToFrontendSerial,
    switchToBackendSerial,
  }
})