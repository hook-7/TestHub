/**
 * 工作流模板相关的类型定义
 */

// 工作流模板状态
export enum WorkflowTemplateStatus {
  DRAFT = 'draft',       // 草稿
  ACTIVE = 'active',     // 活跃
  INACTIVE = 'inactive'  // 非活跃
}

// 工作流步骤
export interface WorkflowStep {
  step_id: string
  step_name: string
  command_id: string
  command_name: string
  command: string
  expected_response: string
  timeout: number
  retry_count: number
  delay_before: number
  delay_after: number
  required: boolean
  description: string
  order: number
}

// 工作流模板
export interface WorkflowTemplate {
  id: string
  name: string
  description: string
  category: string
  version: string
  status: WorkflowTemplateStatus
  steps: WorkflowStep[]
  created_at: number
  updated_at: number
  created_by: string
}

// 工作流执行实例
export interface WorkflowExecution {
  id: string
  template_id: string
  template_name: string
  status: string
  mac_address: string
  serial_number: string
  operator: string
  workstation: string
  device_id: string
  input_data: Record<string, any>
  current_step: number
  total_steps: number
  progress: number
  step_results: Array<{
    step_id: string
    step_name: string
    command: string
    status: string
    response: string
    execution_time: string
    duration_ms: number
  }>
  start_time?: number
  end_time?: number
  error_message?: string
  created_at: number
}

// 创建工作流模板请求
export interface CreateWorkflowTemplateRequest {
  name: string
  description: string
  category: string
  command_ids: string[]
}

// 更新工作流模板请求
export interface UpdateWorkflowTemplateRequest {
  name?: string
  description?: string
  category?: string
  status?: WorkflowTemplateStatus
  command_ids?: string[]
}

// 执行工作流请求
export interface ExecuteWorkflowRequest {
  template_id: string
  mac_address: string
  serial_number: string
  operator: string
  workstation: string
  device_id: string
  input_data: Record<string, any>
}

// 工作流模板列表响应
export interface WorkflowTemplateListResponse {
  templates: WorkflowTemplate[]
  total: number
}

// 工作流执行列表响应
export interface WorkflowExecutionListResponse {
  executions: WorkflowExecution[]
  total: number
}

// 工作流统计信息
export interface WorkflowStats {
  total_templates: number
  active_templates: number
  total_executions: number
  successful_executions: number
  failed_executions: number
  running_executions: number
  success_rate: number
}