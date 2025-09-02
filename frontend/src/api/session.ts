import { api } from './index'

export interface SessionInfo {
  session_id: string
  client_ip: string
  user_agent?: string
  created_at: string
  last_activity: string
  is_active: boolean
}

export interface SessionStatus {
  has_active_session: boolean
  current_session?: SessionInfo
  total_sessions: number
}

export interface SessionResponse {
  session_id: string
  token: string
  expires_in: number
}

export interface CreateSessionRequest {
  client_info?: string
}

export const sessionAPI = {
  // 创建会话（登录）
  async createSession(request: CreateSessionRequest): Promise<SessionResponse> {
    const response = await api.post<SessionResponse>('/session/create', request)
    return response
  },

  // 销毁会话（登出）
  async destroySession(): Promise<void> {
    await api.delete('/session/destroy')
  },

  // 获取会话状态
  async getSessionStatus(): Promise<SessionStatus> {
    const response = await api.get<SessionStatus>('/session/status')
    return response
  },

  // 验证会话
  async validateSession(): Promise<{ valid: boolean }> {
    const response = await api.post<{ valid: boolean }>('/session/validate')
    return response
  },

  // 会话心跳
  async sendHeartbeat(): Promise<{ active: boolean; last_activity: string }> {
    const response = await api.post<{ active: boolean; last_activity: string }>('/session/heartbeat')
    return response
  },

  // 强制清理会话
  async forceCleanupSessions(): Promise<{ cleaned: boolean }> {
    const response = await api.post<{ cleaned: boolean }>('/session/cleanup')
    return response
  }
}