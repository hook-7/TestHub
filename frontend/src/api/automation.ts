/**
 * 自动化命令API接口
 */
import { api } from './index'

// 类型定义
export interface AutomationCommand {
  command_id: string
  status: 'pending' | 'confirmed' | 'executing' | 'success' | 'failed' | 'cancelled'
  result?: any
  error_message?: string
  execution_time?: number
  created_at: string
  updated_at: string
}

export interface AutomationCommandRequest {
  command_name: string
  command_type: 'system' | 'device' | 'test' | 'maintenance'
  priority?: 'low' | 'normal' | 'high' | 'urgent'
  parameters?: Record<string, any>
  requires_confirmation?: boolean
  timeout_seconds?: number
  description?: string
  operator_id?: string
  workstation_id?: string
}

export interface CommandConfirmation {
  command_id: string
  confirmed: boolean
  operator_notes?: string
}

export interface CommandTemplate {
  template_id: string
  name: string
  command_type: 'system' | 'device' | 'test' | 'maintenance'
  description: string
  parameters_schema: Record<string, any>
  requires_confirmation: boolean
  is_active: boolean
}

export interface CommandListParams {
  status?: string
  command_type?: string
  page?: number
  page_size?: number
}

export interface CommandListResponse {
  commands: AutomationCommand[]
  total: number
  page: number
  page_size: number
}

/**
 * 自动化命令API类
 */
export class AutomationAPI {
  /**
   * 创建自动化命令
   */
  static async createCommand(request: AutomationCommandRequest) {
    return api.post<AutomationCommand>('/automation/commands', request)
  }

  /**
   * 确认命令执行
   */
  static async confirmCommand(commandId: string, confirmation: CommandConfirmation) {
    return api.post<AutomationCommand>(`/automation/commands/${commandId}/confirm`, confirmation)
  }

  /**
   * 获取单个命令信息
   */
  static async getCommand(commandId: string) {
    return api.get<AutomationCommand>(`/automation/commands/${commandId}`)
  }

  /**
   * 获取命令列表
   */
  static async getCommands(params?: CommandListParams) {
    const queryParams = new URLSearchParams()
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          queryParams.append(key, String(value))
        }
      })
    }
    const url = queryParams.toString() ? `/automation/commands?${queryParams}` : '/automation/commands'
    return api.get<CommandListResponse>(url)
  }

  /**
   * 取消命令执行
   */
  static async cancelCommand(commandId: string) {
    return api.delete<AutomationCommand>(`/automation/commands/${commandId}`)
  }

  /**
   * 获取命令模板列表
   */
  static async getTemplates() {
    return api.get<CommandTemplate[]>('/automation/templates')
  }

  /**
   * 获取单个命令模板
   */
  static async getTemplate(templateId: string) {
    return api.get<CommandTemplate>(`/automation/templates/${templateId}`)
  }

  /**
   * 根据模板执行命令
   */
  static async executeTemplateCommand(
    templateId: string, 
    parameters: Record<string, any>,
    operatorId?: string,
    workstationId?: string
  ) {
    const queryParams = new URLSearchParams()
    if (operatorId) queryParams.append('operator_id', operatorId)
    if (workstationId) queryParams.append('workstation_id', workstationId)
    
    const url = queryParams.toString() 
      ? `/automation/templates/${templateId}/execute?${queryParams}`
      : `/automation/templates/${templateId}/execute`
    
    return api.post<AutomationCommand>(url, parameters)
  }
}

export default AutomationAPI