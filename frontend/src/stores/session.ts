import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { sessionAPI, type SessionResponse, type SessionStatus } from '@/api/session'

export const useSessionStore = defineStore('session', () => {
  // 状态
  const sessionId = ref<string | null>(null)
  const sessionToken = ref<string | null>(null)
  const isLoggedIn = ref(false)
  const sessionStatus = ref<SessionStatus | null>(null)
  const isLoading = ref(false)
  const heartbeatInterval = ref<number | null>(null)
  const heartbeatWs = ref<WebSocket | null>(null)

  // 计算属性
  const hasActiveSession = computed(() => {
    return sessionStatus.value?.has_active_session || false
  })

  const currentSession = computed(() => {
    return sessionStatus.value?.current_session
  })

  // 从localStorage恢复会话
  const restoreSession = () => {
    const storedSessionId = localStorage.getItem('sessionId')
    const storedToken = localStorage.getItem('sessionToken')
    
    if (storedSessionId && storedToken) {
      sessionId.value = storedSessionId
      sessionToken.value = storedToken
      isLoggedIn.value = true
      
      // 设置axios请求头
      setAuthHeader(storedSessionId)
    }
  }

  // 设置认证请求头
  const setAuthHeader = (sessionIdValue: string) => {
    // 这里需要在api/index.ts中设置拦截器
    if (typeof window !== 'undefined') {
      window.sessionId = sessionIdValue
    }
  }

  // 清除认证请求头
  const clearAuthHeader = () => {
    if (typeof window !== 'undefined') {
      delete window.sessionId
    }
  }

  // 创建会话（登录）
  const login = async (clientInfo?: string): Promise<boolean> => {
    try {
      isLoading.value = true
      
      // 检查是否已有活跃会话
      await refreshSessionStatus()
      if (hasActiveSession.value && !isLoggedIn.value) {
        ElMessage.error('已有其他客户端连接中，请稍后再试')
        return false
      }

      const response: SessionResponse = await sessionAPI.createSession({
        client_info: clientInfo || navigator.userAgent
      })

      // 保存会话信息
      sessionId.value = response.session_id
      sessionToken.value = response.token
      isLoggedIn.value = true

      // 保存到localStorage
      localStorage.setItem('sessionId', response.session_id)
      localStorage.setItem('sessionToken', response.token)

      // 设置请求头
      setAuthHeader(response.session_id)

      // 启动心跳
      startHeartbeat()

      ElMessage.success('登录成功')
      return true

    } catch (error: any) {
      console.error('Login failed:', error)
      ElMessage.error(error.response?.data?.msg || '登录失败')
      return false
    } finally {
      isLoading.value = false
    }
  }

  // 通过串口配置登录
  const loginWithSerial = async (config: any): Promise<boolean> => {
    try {
      isLoading.value = true
      
      // 检查是否已有活跃会话
      await refreshSessionStatus()
      if (hasActiveSession.value && !isLoggedIn.value) {
        const activeSession = currentSession.value
        ElMessage.error(`已有其他客户端连接中（IP: ${activeSession?.client_ip}），请断开其他连接后重试`)
        return false
      }

      // 导入连接store
      const { useConnectionStore } = await import('@/stores/connection')
      const connectionStore = useConnectionStore()
      
      // 使用连接store的新方法
      const response = await connectionStore.connectWithLogin(config)

      // 保存会话信息
      sessionId.value = response.session_id
      sessionToken.value = response.token
      isLoggedIn.value = true

      // 保存到localStorage
      localStorage.setItem('sessionId', response.session_id)
      localStorage.setItem('sessionToken', response.token)

      // 设置请求头
      setAuthHeader(response.session_id)

      // 启动心跳
      startHeartbeat()

      ElMessage.success('串口连接并登录成功')
      return true

    } catch (error: any) {
      console.error('Serial login failed:', error)
      ElMessage.error(error.response?.data?.msg || '串口连接登录失败')
      return false
    } finally {
      isLoading.value = false
    }
  }

  // 启动WebSocket心跳
  const startHeartbeat = () => {
    if (!sessionId.value) return
    
    stopHeartbeat() // 确保没有重复连接
    
    try {
      // 建立WebSocket连接
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const host = window.location.host
      const wsUrl = `${protocol}//${host}/api/v1/terminal/ws/heartbeat/${sessionId.value}`
      heartbeatWs.value = new WebSocket(wsUrl)
      
      heartbeatWs.value.onopen = () => {
        console.log('WebSocket心跳连接已建立')
        
        // 启动心跳定时器
        heartbeatInterval.value = setInterval(() => {
          if (heartbeatWs.value && heartbeatWs.value.readyState === WebSocket.OPEN) {
            heartbeatWs.value.send(JSON.stringify({
              type: 'heartbeat',
              timestamp: new Date().toISOString()
            }))
          }
        }, 20000) // 每20秒发送一次心跳
      }
      
      heartbeatWs.value.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'heartbeat_ack' && data.success) {
            console.log('心跳响应成功')
          }
        } catch (error) {
          console.error('心跳响应解析失败:', error)
        }
      }
      
      heartbeatWs.value.onclose = (event) => {
        console.log('WebSocket心跳连接关闭:', event.code, event.reason)
        if (event.code === 4001) {
          // 会话无效，执行登出
          logout()
        }
      }
      
      heartbeatWs.value.onerror = (error) => {
        console.error('WebSocket心跳连接错误:', error)
      }
      
    } catch (error) {
      console.error('启动WebSocket心跳失败:', error)
      // 回退到HTTP心跳
      startHttpHeartbeat()
    }
  }

  // HTTP心跳备用方案
  const startHttpHeartbeat = () => {
    if (heartbeatInterval.value) {
      clearInterval(heartbeatInterval.value)
    }
    
    heartbeatInterval.value = setInterval(async () => {
      try {
        await sessionAPI.updateHeartbeat()
      } catch (error) {
        console.error('HTTP心跳失败:', error)
        // 心跳失败，可能会话已过期，执行登出
        await logout()
      }
    }, 20000) // 每20秒发送一次心跳
  }

  // 停止心跳
  const stopHeartbeat = () => {
    // 停止定时器
    if (heartbeatInterval.value) {
      clearInterval(heartbeatInterval.value)
      heartbeatInterval.value = null
    }
    
    // 关闭WebSocket连接
    if (heartbeatWs.value) {
      heartbeatWs.value.close()
      heartbeatWs.value = null
    }
  }

  // 登出
  const logout = async (): Promise<void> => {
    try {
      if (sessionId.value) {
        await sessionAPI.destroySession()
      }
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      // 停止心跳
      stopHeartbeat()
      
      // 清除本地状态
      sessionId.value = null
      sessionToken.value = null
      isLoggedIn.value = false
      sessionStatus.value = null

      // 清除localStorage
      localStorage.removeItem('sessionId')
      localStorage.removeItem('sessionToken')

      // 清除请求头
      clearAuthHeader()

      ElMessage.success('已登出')
    }
  }

  // 验证会话
  const validateSession = async (): Promise<boolean> => {
    if (!sessionId.value) {
      return false
    }

    try {
      const result = await sessionAPI.validateSession()
      if (!result.valid) {
        // 会话无效，清除本地状态
        await logout()
        return false
      }
      return true
    } catch (error) {
      console.error('Session validation failed:', error)
      await logout()
      return false
    }
  }

  // 刷新会话状态
  const refreshSessionStatus = async (): Promise<void> => {
    try {
      sessionStatus.value = await sessionAPI.getSessionStatus()
    } catch (error) {
      console.error('Failed to get session status:', error)
    }
  }

  // 强制清理会话（管理员功能）
  const forceCleanup = async (): Promise<boolean> => {
    try {
      const result = await sessionAPI.forceCleanupSessions()
      if (result.cleaned) {
        ElMessage.success('会话清理成功')
        await refreshSessionStatus()
        return true
      }
      return false
    } catch (error) {
      console.error('Force cleanup failed:', error)
      ElMessage.error('会话清理失败')
      return false
    }
  }

  // 初始化
  const init = async () => {
    restoreSession()
    await refreshSessionStatus()
    
    if (isLoggedIn.value) {
      // 验证已存储的会话
      const isValid = await validateSession()
      if (isValid) {
        // 如果会话有效，启动心跳
        startHeartbeat()
      } else {
        ElMessage.warning('会话已过期，请重新登录')
      }
    }
  }

  return {
    // 状态
    sessionId,
    sessionToken,
    isLoggedIn,
    sessionStatus,
    isLoading,
    
    // 计算属性
    hasActiveSession,
    currentSession,
    
    // 方法
    login,
    loginWithSerial,
    logout,
    validateSession,
    refreshSessionStatus,
    forceCleanup,
    startHeartbeat,
    stopHeartbeat,
    init
  }
})

// 扩展Window接口
declare global {
  interface Window {
    sessionId?: string
  }
}