/**
 * Commands API - 常用指令API
 */

import { api } from './index'

export interface SavedCommand {
  id: string
  name: string
  command: string
  description: string
  expected_response: string
  created_at: number // 毫秒时间戳
}

export interface CreateCommandRequest {
  name: string
  command: string
  description?: string
  expected_response?: string
}

export interface UpdateCommandRequest {
  name?: string
  command?: string
  description?: string
  expected_response?: string
}

export interface CommandsListResponse {
  commands: SavedCommand[]
  total: number
}

export interface APIResponse<T = any> {
  code: number
  msg: string
  data: T
}

/**
 * 获取所有常用指令
 */
export const getAllCommands = async (): Promise<CommandsListResponse> => {
  const response = await api.get<CommandsListResponse>('/commands/')
  // 由于拦截器已经处理了错误检查和数据提取，这里直接返回
  return response
}

/**
 * 创建新指令
 */
export const createCommand = async (data: CreateCommandRequest): Promise<SavedCommand> => {
  const response = await api.post<SavedCommand>('/commands/', data)
  // 由于拦截器已经处理了错误检查和数据提取，这里直接返回
  return response
}

/**
 * 根据ID获取指令详情
 */
export const getCommandById = async (id: string): Promise<SavedCommand> => {
  const response = await api.get<SavedCommand>(`/commands/${id}`)
  // 由于拦截器已经处理了错误检查和数据提取，这里直接返回
  return response
}

/**
 * 更新指令
 */
export const updateCommand = async (id: string, data: UpdateCommandRequest): Promise<SavedCommand> => {
  const response = await api.put<SavedCommand>(`/commands/${id}`, data)
  // 由于拦截器已经处理了错误检查和数据提取，这里直接返回
  return response
}

/**
 * 删除指令
 */
export const deleteCommand = async (id: string): Promise<void> => {
  await api.delete(`/commands/${id}`)
  // 由于拦截器已经处理了错误检查，这里无需额外处理
}

/**
 * 获取指令总数
 */
export const getCommandsCount = async (): Promise<number> => {
  const response = await api.get<number>('/commands/count/total')
  // 由于拦截器已经处理了错误检查和数据提取，这里直接返回
  return response
}
