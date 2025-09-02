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
  
  // 心跳相关状态
  const heartbeatInterval = ref<number | null>(null)
  const heartbeatIntervalMs = 25 * 1000 // 25秒
  const lastHeartbeat = ref<Date | null>(null)
  const isHeartbeatActive = ref(false)

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

      // 移除重复提示，由调用方处理
      return true

    } catch (error: any) {
      console.error('Login failed:', error)
      ElMessage.error(error.response?.data?.msg || '登录失败')
      return false
    } finally {
      isLoading.value = false
    }
  }

  // 登出
  const logout = async (): Promise<void> => {
    // 停止心跳
    stopHeartbeat()
    
    try {
      if (sessionId.value) {
        await sessionAPI.destroySession()
      }
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
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

      // 移除重复提示，由调用方处理
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

  // 开始心跳
  const startHeartbeat = () => {
    if (heartbeatInterval.value || !isLoggedIn.value) {
      return
    }
    
    console.log('Starting heartbeat...')
    isHeartbeatActive.value = true
    
    heartbeatInterval.value = window.setInterval(async () => {
      if (!isLoggedIn.value || !sessionId.value) {
        stopHeartbeat()
        return
      }
      
      try {
        const result = await sessionAPI.sendHeartbeat()
        lastHeartbeat.value = new Date()
        console.log('Heartbeat sent successfully', result.last_activity)
      } catch (error: any) {
        console.error('Heartbeat failed:', error)
        
        // 如果心跳失败且返回401，说明会话已过期
        if (error.response?.status === 401) {
          ElMessage.warning('会话已过期，请重新登录')
          await logout()
        }
      }
    }, heartbeatIntervalMs)
    
    // 立即发送一次心跳
    setTimeout(async () => {
      if (isLoggedIn.value) {
        try {
          await sessionAPI.sendHeartbeat()
          lastHeartbeat.value = new Date()
        } catch (error) {
          console.error('Initial heartbeat failed:', error)
        }
      }
    }, 1000)
  }
  
  // 停止心跳
  const stopHeartbeat = () => {
    if (heartbeatInterval.value) {
      console.log('Stopping heartbeat...')
      clearInterval(heartbeatInterval.value)
      heartbeatInterval.value = null
      isHeartbeatActive.value = false
      lastHeartbeat.value = null
    }
  }

  // 初始化
  const init = async () => {
    restoreSession()
    await refreshSessionStatus()
    
    if (isLoggedIn.value) {
      // 快速启动心跳，不额外验证（心跳本身就是验证）
      startHeartbeat()
    }
  }

  return {
    // 状态
    sessionId,
    sessionToken,
    isLoggedIn,
    sessionStatus,
    isLoading,
    
    // 心跳状态
    lastHeartbeat,
    isHeartbeatActive,
    
    // 计算属性
    hasActiveSession,
    currentSession,
    
    // 方法
    login,
    logout,
    validateSession,
    refreshSessionStatus,
    forceCleanup,
    init,
    
    // 心跳方法
    startHeartbeat,
    stopHeartbeat
  }
})

// 扩展Window接口
declare global {
  interface Window {
    sessionId?: string
  }
}