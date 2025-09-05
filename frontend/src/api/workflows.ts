/**
 * Workflows API - 批量作业工作流API
 */

import { api } from './index'

export interface WorkflowStepCreate {
  command_id: string
  step_order: number
  delay_ms?: number
  retry_count?: number
  timeout_ms?: number
}

export interface WorkflowStep {
  id: string
  workflow_id: string
  command_id: string
  step_order: number
  delay_ms: number
  retry_count: number
  timeout_ms: number
  created_at: number
  command_name?: string
  command_content?: string
  command_description?: string
}

export interface CreateWorkflowRequest {
  name: string
  description?: string
  steps: WorkflowStepCreate[]
}

export interface UpdateWorkflowRequest {
  name?: string
  description?: string
  steps?: WorkflowStepCreate[]
}

export interface BatchWorkflow {
  id: string
  name: string
  description: string
  created_at: number
  steps: WorkflowStep[]
}

export interface WorkflowsListResponse {
  workflows: BatchWorkflow[]
  total: number
}

export interface StepExecutionStatus {
  id: string
  step_id: string
  status: string
  started_at?: number
  finished_at?: number
  command_sent?: string
  response_received?: string
  retry_attempt: number
  error_message?: string
  created_at: number
  step_order?: number
  command_name?: string
  command_content?: string
}

export interface WorkflowExecutionStatus {
  id: string
  workflow_id: string
  workflow_name?: string
  status: string
  started_at?: number
  finished_at?: number
  total_steps: number
  completed_steps: number
  error_message?: string
  created_at: number
  steps: StepExecutionStatus[]
}

export interface ExecuteWorkflowRequest {
  workflow_id: string
}

export interface ExecuteWorkflowResponse {
  execution_id: string
  workflow_id: string
  workflow_name: string
  status: string
  total_steps: number
}

export interface APIResponse<T = any> {
  code: number
  msg: string
  data: T
}

/**
 * 获取所有工作流
 */
export const getAllWorkflows = async (): Promise<WorkflowsListResponse> => {
  const response = await api.get<WorkflowsListResponse>('/workflows/')
  return response
}

/**
 * 根据ID获取工作流详情
 */
export const getWorkflowById = async (id: string): Promise<BatchWorkflow> => {
  const response = await api.get<BatchWorkflow>(`/workflows/${id}`)
  return response
}

/**
 * 创建新工作流
 */
export const createWorkflow = async (data: CreateWorkflowRequest): Promise<BatchWorkflow> => {
  const response = await api.post<BatchWorkflow>('/workflows/', data)
  return response
}

/**
 * 更新工作流
 */
export const updateWorkflow = async (id: string, data: UpdateWorkflowRequest): Promise<BatchWorkflow> => {
  const response = await api.put<BatchWorkflow>(`/workflows/${id}`, data)
  return response
}

/**
 * 删除工作流
 */
export const deleteWorkflow = async (id: string): Promise<void> => {
  await api.delete(`/workflows/${id}`)
}

/**
 * 执行工作流
 */
export const executeWorkflow = async (data: ExecuteWorkflowRequest): Promise<ExecuteWorkflowResponse> => {
  const response = await api.post<ExecuteWorkflowResponse>('/workflows/execute', data)
  return response
}

/**
 * 获取工作流执行状态
 */
export const getExecutionStatus = async (executionId: string): Promise<WorkflowExecutionStatus> => {
  const response = await api.get<WorkflowExecutionStatus>(`/workflows/execution/${executionId}`)
  return response
}

/**
 * 取消工作流执行
 */
export const cancelExecution = async (executionId: string): Promise<void> => {
  await api.post(`/workflows/execution/${executionId}/cancel`)
}