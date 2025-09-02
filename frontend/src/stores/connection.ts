import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { serialAPI, type SerialConnectionStatus, type SerialPortInfo } from '@/api/serial'

export const useConnectionStore = defineStore('connection', () => {
  // 状态
  const status = ref<SerialConnectionStatus>({
    connected: false
  })
  
  const availablePorts = ref<SerialPortInfo[]>([])
  
  // 计算属性
  const isConnected = computed(() => status.value.connected)
  const currentPort = computed(() => status.value.port || '')
  
  // 操作
  const checkStatus = async () => {
    try {
      status.value = await serialAPI.getConnectionStatus()
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
  
  const connect = async (config: any) => {
    try {
      await serialAPI.connectSerial(config)
      await checkStatus()
      return true
    } catch (error) {
      console.error('Failed to connect:', error)
      return false
    }
  }

  const connectWithLogin = async (config: any) => {
    try {
      const response = await serialAPI.connectSerialAndLogin(config)
      await checkStatus()
      return response
    } catch (error) {
      console.error('Failed to connect with login:', error)
      throw error
    }
  }
  
  const disconnect = async () => {
    try {
      await serialAPI.disconnectSerial()
      await checkStatus()
      return true
    } catch (error) {
      console.error('Failed to disconnect:', error)
      return false
    }
  }
  
  return {
    // 状态
    status,
    availablePorts,
    
    // 计算属性
    isConnected,
    currentPort,
    
    // 操作
    checkStatus,
    loadAvailablePorts,
    autoDetectPort,
    connect,
    connectWithLogin,
    disconnect,
  }
})