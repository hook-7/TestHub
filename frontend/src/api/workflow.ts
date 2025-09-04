/**
 * 工作流自动化API接口
 */
import { api } from './index'

// 类型定义
export interface WorkflowStep {
  step_id: string
  name: string
  step_type: 'serial_send' | 'wait_response' | 'user_confirm' | 'set_variable' | 'condition' | 'delay' | 'log'
  description?: string
  serial_command?: string
  expected_response?: string
  response_timeout?: number
  confirm_message?: string
  confirm_options?: string[]
  variable_name?: string
  variable_value?: string
  variable_source?: string
  condition_expression?: string
  true_next_step?: string
  false_next_step?: string
  delay_seconds?: number
  retry_count?: number
  next_step_id?: string
  status: 'pending' | 'running' | 'success' | 'failed' | 'skipped' | 'waiting'
  execution_result?: any
  error_message?: string
  executed_at?: string
}

export interface WorkflowDefinition {
  workflow_id: string
  name: string
  description?: string
  version: string
  steps: WorkflowStep[]
  start_step_id: string
  variables: Record<string, any>
  timeout_seconds?: number
  auto_save_results: boolean
  created_by?: string
  created_at: string
  updated_at: string
}

export interface WorkflowExecution {
  execution_id: string
  workflow_id: string
  workflow_name: string
  status: 'draft' | 'ready' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled'
  current_step_id?: string
  variables: Record<string, any>
  step_results: Record<string, any>
  started_by?: string
  workstation_id?: string
  started_at?: string
  completed_at?: string
  error_message?: string
  failed_step_id?: string
}

export interface WorkflowExecutionRequest {
  workflow_id: string
  input_variables?: Record<string, any>
  operator_id?: string
  workstation_id?: string
}

export interface UserConfirmationRequest {
  execution_id: string
  step_id: string
  confirmed: boolean
  user_input?: string
  selected_option?: string
  operator_notes?: string
}

/**
 * 工作流API类
 */
export class WorkflowAPI {
  /**
   * 获取工作流列表
   */
  static async getWorkflows() {
    return api.get<WorkflowDefinition[]>('/workflow/workflows')
  }

  /**
   * 获取工作流定义
   */
  static async getWorkflow(workflowId: string) {
    return api.get<WorkflowDefinition>(`/workflow/workflows/${workflowId}`)
  }

  /**
   * 执行工作流
   */
  static async executeWorkflow(workflowId: string, request: WorkflowExecutionRequest) {
    return api.post<WorkflowExecution>(`/workflow/workflows/${workflowId}/execute`, request)
  }

  /**
   * 获取执行实例
   */
  static async getExecution(executionId: string) {
    return api.get<WorkflowExecution>(`/workflow/executions/${executionId}`)
  }

  /**
   * 确认工作流步骤
   */
  static async confirmStep(executionId: string, confirmation: UserConfirmationRequest) {
    return api.post(`/workflow/executions/${executionId}/confirm`, confirmation)
  }

  /**
   * 暂停工作流
   */
  static async pauseWorkflow(executionId: string) {
    return api.post(`/workflow/executions/${executionId}/pause`)
  }

  /**
   * 恢复工作流
   */
  static async resumeWorkflow(executionId: string) {
    return api.post(`/workflow/executions/${executionId}/resume`)
  }

  /**
   * 取消工作流
   */
  static async cancelWorkflow(executionId: string) {
    return api.post(`/workflow/executions/${executionId}/cancel`)
  }
}

export default WorkflowAPI