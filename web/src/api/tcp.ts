/**
 * TCP连接相关API
 */

import { api } from './index'

// TCP连接配置
export interface TcpConnectionConfig {
  host: string
  port: number
  timeout: number
  auto_reconnect: boolean
}

// TCP连接
export interface TcpConnection {
  id: string
  host: string
  port: number
  timeout: number
  auto_reconnect: boolean
  connected: boolean
  created_at: string
  last_activity?: string
}

// TCP命令请求
export interface TcpCommandRequest {
  connection_id: string
  command: string
  auto_add_crlf: boolean
}

// TCP命令响应
export interface TcpCommandResponse {
  success: boolean
  response: string
  timestamp: string
}

// TCP连接列表响应
export interface TcpConnectionsListResponse {
  connections: TcpConnection[]
  total: number
}

/**
 * 创建TCP连接
 */
export async function createTcpConnection(config: TcpConnectionConfig): Promise<TcpConnection> {
  const response = await api.post('/tcp/connect', config)
  return response.data.data
}

/**
 * 获取所有TCP连接
 */
export async function getTcpConnections(): Promise<TcpConnectionsListResponse> {
  const response = await api.get('/tcp/connections')
  return response.data.data
}

/**
 * 获取指定TCP连接
 */
export async function getTcpConnection(connectionId: string): Promise<TcpConnection> {
  const response = await api.get(`/tcp/connections/${connectionId}`)
  return response.data.data
}

/**
 * 断开TCP连接
 */
export async function disconnectTcp(connectionId: string): Promise<void> {
  await api.delete(`/tcp/connections/${connectionId}`)
}

/**
 * 断开所有TCP连接
 */
export async function disconnectAllTcp(): Promise<{ disconnected_count: number }> {
  const response = await api.delete('/tcp/connections')
  return response.data.data
}

/**
 * 发送TCP命令
 */
export async function sendTcpCommand(request: TcpCommandRequest): Promise<TcpCommandResponse> {
  const response = await api.post('/tcp/send-command', request)
  return response.data.data
}

/**
 * 检查TCP连接健康状态
 */
export async function checkTcpConnectionHealth(connectionId: string): Promise<boolean> {
  const response = await api.get(`/tcp/connections/${connectionId}/health`)
  return response.data.data
}