/**
 * 工作流编排API
 */

import { api } from './index'
import type {
  WorkflowDefinition,
  WorkflowExecution,
  WorkflowTemplate,
  WorkflowStats,
  CreateWorkflowRequest,
  UpdateWorkflowRequest,
  ExecuteWorkflowRequest,
  WorkflowListResponse,
  WorkflowExecutionListResponse,
  WorkflowTemplateListResponse
} from '@/types/workflow'

/**
 * 工作流管理API
 */
export class WorkflowAPI {
  /**
   * 获取工作流列表
   */
  static async getWorkflows(params: {
    page?: number
    pageSize?: number
    status?: string
    search?: string
  } = {}): Promise<WorkflowListResponse> {
    const response = await api.get('/workflows/', { params })
    return response
  }

  /**
   * 获取工作流详情
   */
  static async getWorkflow(workflowId: string): Promise<WorkflowDefinition> {
    const response = await api.get(`/workflows/${workflowId}`)
    return response
  }

  /**
   * 创建工作流
   */
  static async createWorkflow(data: CreateWorkflowRequest): Promise<WorkflowDefinition> {
    const response = await api.post('/workflows/', data)
    return response
  }

  /**
   * 更新工作流
   */
  static async updateWorkflow(workflowId: string, data: UpdateWorkflowRequest): Promise<WorkflowDefinition> {
    const response = await api.put(`/workflows/${workflowId}`, data)
    return response
  }

  /**
   * 删除工作流
   */
  static async deleteWorkflow(workflowId: string): Promise<void> {
    await api.delete(`/workflows/${workflowId}`)
  }

  /**
   * 复制工作流
   */
  static async duplicateWorkflow(workflowId: string, newName: string): Promise<WorkflowDefinition> {
    const response = await api.post(`/workflows/${workflowId}/duplicate`, { name: newName })
    return response
  }

  /**
   * 导出工作流
   */
  static async exportWorkflow(workflowId: string): Promise<Blob> {
    const response = await api.get(`/workflows/${workflowId}/export`, {
      responseType: 'blob'
    })
    return response
  }

  /**
   * 导入工作流
   */
  static async importWorkflow(file: File): Promise<WorkflowDefinition> {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post('/workflows/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response
  }
}

/**
 * 工作流执行API
 */
export class WorkflowExecutionAPI {
  /**
   * 执行工作流
   */
  static async executeWorkflow(data: ExecuteWorkflowRequest): Promise<WorkflowExecution> {
    const response = await api.post('/workflows/execute', data)
    return response
  }

  /**
   * 获取执行实例列表
   */
  static async getExecutions(params: {
    page?: number
    pageSize?: number
    workflowId?: string
    status?: string
    startDate?: string
    endDate?: string
  } = {}): Promise<WorkflowExecutionListResponse> {
    const response = await api.get('/workflows/executions/', { params })
    return response
  }

  /**
   * 获取执行实例详情
   */
  static async getExecution(executionId: string): Promise<WorkflowExecution> {
    const response = await api.get(`/workflows/executions/${executionId}`)
    return response
  }

  /**
   * 停止执行
   */
  static async stopExecution(executionId: string): Promise<void> {
    await api.post(`/workflows/executions/${executionId}/stop`)
  }

  /**
   * 重新执行
   */
  static async retryExecution(executionId: string): Promise<WorkflowExecution> {
    const response = await api.post(`/workflows/executions/${executionId}/retry`)
    return response
  }

  /**
   * 删除执行记录
   */
  static async deleteExecution(executionId: string): Promise<void> {
    await api.delete(`/workflows/executions/${executionId}`)
  }
}

/**
 * 工作流模板API
 */
export class WorkflowTemplateAPI {
  /**
   * 获取模板列表
   */
  static async getTemplates(params: {
    page?: number
    pageSize?: number
    category?: string
    search?: string
    isPublic?: boolean
  } = {}): Promise<WorkflowTemplateListResponse> {
    const response = await api.get('/workflows/templates/', { params })
    return response
  }

  /**
   * 获取模板详情
   */
  static async getTemplate(templateId: string): Promise<WorkflowTemplate> {
    const response = await api.get(`/workflows/templates/${templateId}`)
    return response
  }

  /**
   * 创建模板
   */
  static async createTemplate(data: {
    name: string
    description?: string
    category: string
    tags: string[]
    workflowId: string
    isPublic: boolean
  }): Promise<WorkflowTemplate> {
    const response = await api.post('/workflows/templates/', data)
    return response
  }

  /**
   * 更新模板
   */
  static async updateTemplate(templateId: string, data: Partial<WorkflowTemplate>): Promise<WorkflowTemplate> {
    const response = await api.put(`/workflows/templates/${templateId}`, data)
    return response
  }

  /**
   * 删除模板
   */
  static async deleteTemplate(templateId: string): Promise<void> {
    await api.delete(`/workflows/templates/${templateId}`)
  }

  /**
   * 从模板创建工作流
   */
  static async createFromTemplate(templateId: string, name: string): Promise<WorkflowDefinition> {
    const response = await api.post(`/workflows/templates/${templateId}/create`, { name })
    return response
  }

  /**
   * 下载模板
   */
  static async downloadTemplate(templateId: string): Promise<Blob> {
    const response = await api.get(`/workflows/templates/${templateId}/download`, {
      responseType: 'blob'
    })
    return response
  }
}

/**
 * 工作流统计API
 */
export class WorkflowStatsAPI {
  /**
   * 获取工作流统计信息
   */
  static async getStats(): Promise<WorkflowStats> {
    const response = await api.get('/workflows/stats')
    return response
  }

  /**
   * 获取工作流执行统计
   */
  static async getExecutionStats(params: {
    workflowId?: string
    startDate?: string
    endDate?: string
  } = {}): Promise<any> {
    const response = await api.get('/workflows/stats/executions', { params })
    return response
  }
}

// 导出API实例
export const workflowAPI = WorkflowAPI
export const workflowExecutionAPI = WorkflowExecutionAPI
export const workflowTemplateAPI = WorkflowTemplateAPI
export const workflowStatsAPI = WorkflowStatsAPI