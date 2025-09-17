/**
 * 工作流模板相关的Pinia store
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  WorkflowTemplate,
  WorkflowExecution,
  WorkflowStats,
  CreateWorkflowTemplateRequest,
  UpdateWorkflowTemplateRequest,
  ExecuteWorkflowRequest
} from '@/types/workflow-template'
import {
  getWorkflowTemplates,
  getWorkflowTemplate,
  createWorkflowTemplate,
  updateWorkflowTemplate,
  deleteWorkflowTemplate,
  executeWorkflow,
  getWorkflowExecutions,
  getWorkflowExecution,
  stopWorkflowExecution,
  getWorkflowStats
} from '@/api/workflow-template'

export const useWorkflowTemplateStore = defineStore('workflowTemplate', () => {
  // 状态
  const templates = ref<WorkflowTemplate[]>([])
  const executions = ref<WorkflowExecution[]>([])
  const stats = ref<WorkflowStats>({
    total_templates: 0,
    active_templates: 0,
    total_executions: 0,
    successful_executions: 0,
    failed_executions: 0,
    running_executions: 0,
    success_rate: 0
  })
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 计算属性
  const activeTemplates = computed(() => 
    templates.value.filter(t => t.status === 'active')
  )

  const runningExecutions = computed(() => 
    executions.value.filter(e => e.status === 'running')
  )

  // 获取工作流模板列表
  const loadTemplates = async (params?: {
    page?: number
    size?: number
    category?: string
    status?: string
  }) => {
    try {
      loading.value = true
      error.value = null
      const response = await getWorkflowTemplates(params)
      templates.value = response.data.templates
      return response.data
    } catch (err: any) {
      error.value = err.message || '获取模板列表失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 获取工作流模板详情
  const loadTemplate = async (templateId: string) => {
    try {
      loading.value = true
      error.value = null
      const response = await getWorkflowTemplate(templateId)
      return response.data
    } catch (err: any) {
      error.value = err.message || '获取模板详情失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 创建工作流模板
  const createTemplate = async (data: CreateWorkflowTemplateRequest) => {
    try {
      loading.value = true
      error.value = null
      const response = await createWorkflowTemplate(data)
      templates.value.unshift(response.data)
      return response.data
    } catch (err: any) {
      error.value = err.message || '创建模板失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 更新工作流模板
  const updateTemplate = async (templateId: string, data: UpdateWorkflowTemplateRequest) => {
    try {
      loading.value = true
      error.value = null
      const response = await updateWorkflowTemplate(templateId, data)
      const index = templates.value.findIndex(t => t.id === templateId)
      if (index !== -1) {
        templates.value[index] = response.data
      }
      return response.data
    } catch (err: any) {
      error.value = err.message || '更新模板失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 删除工作流模板
  const deleteTemplate = async (templateId: string) => {
    try {
      loading.value = true
      error.value = null
      await deleteWorkflowTemplate(templateId)
      templates.value = templates.value.filter(t => t.id !== templateId)
    } catch (err: any) {
      error.value = err.message || '删除模板失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 执行工作流
  const executeTemplate = async (data: ExecuteWorkflowRequest) => {
    try {
      loading.value = true
      error.value = null
      const response = await executeWorkflow(data)
      executions.value.unshift(response.data)
      return response.data
    } catch (err: any) {
      error.value = err.message || '执行工作流失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 获取工作流执行列表
  const loadExecutions = async (params?: {
    page?: number
    size?: number
    template_id?: string
    status?: string
  }) => {
    try {
      loading.value = true
      error.value = null
      const response = await getWorkflowExecutions(params)
      executions.value = response.data.executions
      return response.data
    } catch (err: any) {
      error.value = err.message || '获取执行列表失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 获取工作流执行详情
  const loadExecution = async (executionId: string) => {
    try {
      loading.value = true
      error.value = null
      const response = await getWorkflowExecution(executionId)
      return response.data
    } catch (err: any) {
      error.value = err.message || '获取执行详情失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 停止工作流执行
  const stopExecution = async (executionId: string) => {
    try {
      loading.value = true
      error.value = null
      await stopWorkflowExecution(executionId)
      const execution = executions.value.find(e => e.id === executionId)
      if (execution) {
        execution.status = 'cancelled'
      }
    } catch (err: any) {
      error.value = err.message || '停止执行失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 获取统计信息
  const loadStats = async () => {
    try {
      loading.value = true
      error.value = null
      const response = await getWorkflowStats()
      stats.value = response.data
      return response.data
    } catch (err: any) {
      error.value = err.message || '获取统计信息失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 刷新执行状态
  const refreshExecution = async (executionId: string) => {
    try {
      const response = await getWorkflowExecution(executionId)
      const index = executions.value.findIndex(e => e.id === executionId)
      if (index !== -1) {
        executions.value[index] = response.data
      }
      return response.data
    } catch (err: any) {
      error.value = err.message || '刷新执行状态失败'
      throw err
    }
  }

  return {
    // 状态
    templates,
    executions,
    stats,
    loading,
    error,
    
    // 计算属性
    activeTemplates,
    runningExecutions,
    
    // 方法
    loadTemplates,
    loadTemplate,
    createTemplate,
    updateTemplate,
    deleteTemplate,
    executeTemplate,
    loadExecutions,
    loadExecution,
    stopExecution,
    loadStats,
    refreshExecution
  }
})