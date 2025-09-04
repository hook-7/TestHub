/**
 * 工作流管理API接口
 */

import { api } from './index'

// 工作流相关类型定义
export interface WorkflowStep {
  id: string
  name: string
  type: 'send' | 'expect' | 'assign' | 'confirm' | 'control'
  description?: string
  [key: string]: any
}

export interface WorkflowDefinition {
  id?: string
  name: string
  description?: string
  version: string
  variables: Record<string, any>
  steps: WorkflowStep[]
  created_at?: string
  updated_at?: string
}

export interface WorkflowExecution {
  id: string
  workflow_id: string
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled'
  current_step?: string
  variables: Record<string, any>
  logs: WorkflowLog[]
  started_at?: string
  completed_at?: string
  error_message?: string
}

export interface WorkflowLog {
  timestamp: string
  step_id: string
  level: string
  message: string
  data?: Record<string, any>
}

export interface WorkflowCreateRequest {
  name: string
  description?: string
  variables?: Record<string, any>
  steps: Array<Record<string, any>>
}

export interface WorkflowExecuteRequest {
  variables?: Record<string, any>
  session_id?: string
}

export interface WorkflowConfirmRequest {
  execution_id: string
  action: string
}

/**
 * 工作流管理API
 */
export const workflowApi = {
  /**
   * 创建工作流
   */
  async createWorkflow(data: WorkflowCreateRequest) {
    return api.post<WorkflowDefinition>('/workflow/', data)
  },

  /**
   * 获取工作流列表
   */
  async listWorkflows() {
    return api.get<{workflows: WorkflowDefinition[], total: number}>('/workflow/')
  },

  /**
   * 获取工作流详情
   */
  async getWorkflow(workflowId: string) {
    return api.get<WorkflowDefinition>(`/workflow/${workflowId}`)
  },

  /**
   * 更新工作流
   */
  async updateWorkflow(workflowId: string, data: Partial<WorkflowCreateRequest>) {
    return api.put<WorkflowDefinition>(`/workflow/${workflowId}`, data)
  },

  /**
   * 删除工作流
   */
  async deleteWorkflow(workflowId: string) {
    return api.delete(`/workflow/${workflowId}`)
  },

  /**
   * 执行工作流
   */
  async executeWorkflow(workflowId: string, data: WorkflowExecuteRequest) {
    return api.post<{execution_id: string, status: string, message: string}>(`/workflow/${workflowId}/execute`, data)
  },

  /**
   * 获取执行状态
   */
  async getExecutionStatus(executionId: string) {
    return api.get<WorkflowExecution>(`/workflow/execution/${executionId}`)
  },

  /**
   * 确认工作流步骤
   */
  async confirmWorkflowStep(data: WorkflowConfirmRequest) {
    return api.post(`/workflow/execution/${data.execution_id}/confirm`, data)
  },

  /**
   * 取消工作流执行
   */
  async cancelExecution(executionId: string) {
    return api.post(`/workflow/execution/${executionId}/cancel`)
  },

  /**
   * 获取执行列表
   */
  async listExecutions(status?: string, limit: number = 50) {
    const params = new URLSearchParams()
    if (status) params.append('status', status)
    params.append('limit', limit.toString())
    
    return api.get<{executions: WorkflowExecution[], total: number}>(`/workflow/executions?${params}`)
  }
}