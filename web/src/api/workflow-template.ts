/**
 * 工作流模板相关的API调用
 */

import { request } from '@/utils/request'
import type {
  WorkflowTemplate,
  WorkflowExecution,
  WorkflowStats,
  CreateWorkflowTemplateRequest,
  UpdateWorkflowTemplateRequest,
  ExecuteWorkflowRequest,
  WorkflowTemplateListResponse,
  WorkflowExecutionListResponse
} from '@/types/workflow-template'

// 获取工作流模板列表
export function getWorkflowTemplates(params?: {
  page?: number
  size?: number
  category?: string
  status?: string
}) {
  return request<WorkflowTemplateListResponse>({
    url: '/api/v1/workflow-templates/templates',
    method: 'GET',
    params
  })
}

// 获取工作流模板详情
export function getWorkflowTemplate(templateId: string) {
  return request<WorkflowTemplate>({
    url: `/api/v1/workflow-templates/templates/${templateId}`,
    method: 'GET'
  })
}

// 创建工作流模板
export function createWorkflowTemplate(data: CreateWorkflowTemplateRequest) {
  return request<WorkflowTemplate>({
    url: '/api/v1/workflow-templates/templates',
    method: 'POST',
    data
  })
}

// 更新工作流模板
export function updateWorkflowTemplate(templateId: string, data: UpdateWorkflowTemplateRequest) {
  return request<WorkflowTemplate>({
    url: `/api/v1/workflow-templates/templates/${templateId}`,
    method: 'PUT',
    data
  })
}

// 删除工作流模板
export function deleteWorkflowTemplate(templateId: string) {
  return request({
    url: `/api/v1/workflow-templates/templates/${templateId}`,
    method: 'DELETE'
  })
}

// 执行工作流
export function executeWorkflow(data: ExecuteWorkflowRequest) {
  return request<WorkflowExecution>({
    url: '/api/v1/workflow-templates/execute',
    method: 'POST',
    data
  })
}

// 获取工作流执行列表
export function getWorkflowExecutions(params?: {
  page?: number
  size?: number
  template_id?: string
  status?: string
}) {
  return request<WorkflowExecutionListResponse>({
    url: '/api/v1/workflow-templates/executions',
    method: 'GET',
    params
  })
}

// 获取工作流执行详情
export function getWorkflowExecution(executionId: string) {
  return request<WorkflowExecution>({
    url: `/api/v1/workflow-templates/executions/${executionId}`,
    method: 'GET'
  })
}

// 停止工作流执行
export function stopWorkflowExecution(executionId: string) {
  return request({
    url: `/api/v1/workflow-templates/executions/${executionId}/stop`,
    method: 'POST'
  })
}

// 获取工作流统计信息
export function getWorkflowStats() {
  return request<WorkflowStats>({
    url: '/api/v1/workflow-templates/stats',
    method: 'GET'
  })
}