/**
 * Commands API - 常用指令API
 */

import { api } from './index'

export const InputMode = {
  TEXT_INPUT: "TEXT_INPUT",  // 支持文本输入
  HEX_READ: "HEX_READ",      // 十六进制读取
  TCP_INPUT: "TCP_INPUT"     // 以TCP形式输入
} as const

export type InputModeType = typeof InputMode[keyof typeof InputMode]

export interface SavedCommand {
  id: string
  name: string
  command: string
  description: string
  expected_response: string
  input_mode: InputModeType
  show_notification: boolean
  target_serial_id?: number // 目标串口ID，null表示使用当前选择的串口
  created_at: number // 毫秒时间戳
}

export interface CreateCommandRequest {
  name: string
  command: string
  description?: string
  expected_response?: string
  input_mode?: InputModeType
  show_notification?: boolean
  target_serial_id?: number
}

export interface UpdateCommandRequest {
  name?: string
  command?: string
  description?: string
  expected_response?: string
  input_mode?: InputModeType
  show_notification?: boolean
  target_serial_id?: number
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

