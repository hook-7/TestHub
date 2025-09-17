/**
 * 工作流编排Store
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  WorkflowDefinition,
  WorkflowExecution,
  WorkflowTemplate,
  WorkflowStats,
  WorkflowNode,
  WorkflowConnection,
  WorkflowNodeType,
  WorkflowStatus,
  WorkflowNodeStatus
} from '@/types/workflow'
import { workflowAPI, workflowExecutionAPI, workflowTemplateAPI, workflowStatsAPI } from '@/api/workflow'

export const useWorkflowStore = defineStore('workflow', () => {
  // 状态
  const workflows = ref<WorkflowDefinition[]>([])
  const currentWorkflow = ref<WorkflowDefinition | null>(null)
  const executions = ref<WorkflowExecution[]>([])
  const templates = ref<WorkflowTemplate[]>([])
  const stats = ref<WorkflowStats | null>(null)
  
  // 当前执行状态
  const currentExecution = ref<WorkflowExecution | null>(null)
  const isExecuting = ref(false)
  const executionProgress = ref(0)
  
  // 设计器状态
  const selectedNode = ref<WorkflowNode | null>(null)
  const selectedConnection = ref<WorkflowConnection | null>(null)
  const isDesignerDirty = ref(false)
  
  // 计算属性
  const activeWorkflows = computed(() => 
    workflows.value.filter(w => w.status === 'active')
  )
  
  const runningExecutions = computed(() => 
    executions.value.filter(e => e.status === 'running')
  )
  
  const completedExecutions = computed(() => 
    executions.value.filter(e => e.status === 'completed')
  )
  
  const failedExecutions = computed(() => 
    executions.value.filter(e => e.status === 'failed')
  )
  
  // 工作流管理
  const loadWorkflows = async (params: {
    page?: number
    pageSize?: number
    status?: string
    search?: string
  } = {}) => {
    try {
      const response = await workflowAPI.getWorkflows(params)
      workflows.value = response.workflows
      return response
    } catch (error) {
      console.error('加载工作流失败:', error)
      throw error
    }
  }
  
  const loadWorkflow = async (workflowId: string) => {
    try {
      const workflow = await workflowAPI.getWorkflow(workflowId)
      currentWorkflow.value = workflow
      return workflow
    } catch (error) {
      console.error('加载工作流详情失败:', error)
      throw error
    }
  }
  
  const createWorkflow = async (data: {
    name: string
    description?: string
    nodes?: WorkflowNode[]
    connections?: WorkflowConnection[]
  }) => {
    try {
      const workflow = await workflowAPI.createWorkflow({
        ...data,
        nodes: data.nodes || [],
        connections: data.connections || [],
        variables: [],
        settings: {
          autoStart: false,
          maxExecutionTime: 300000, // 5分钟
          retryOnFailure: true,
          maxRetries: 3,
          timeout: 30000, // 30秒
          requireMacAddress: true,
          requireSerialNumber: false
        }
      })
      workflows.value.unshift(workflow)
      return workflow
    } catch (error) {
      console.error('创建工作流失败:', error)
      throw error
    }
  }
  
  const updateWorkflow = async (workflowId: string, data: Partial<WorkflowDefinition>) => {
    try {
      const workflow = await workflowAPI.updateWorkflow(workflowId, data)
      const index = workflows.value.findIndex(w => w.id === workflowId)
      if (index !== -1) {
        workflows.value[index] = workflow
      }
      if (currentWorkflow.value?.id === workflowId) {
        currentWorkflow.value = workflow
      }
      return workflow
    } catch (error) {
      console.error('更新工作流失败:', error)
      throw error
    }
  }
  
  const deleteWorkflow = async (workflowId: string) => {
    try {
      await workflowAPI.deleteWorkflow(workflowId)
      workflows.value = workflows.value.filter(w => w.id !== workflowId)
      if (currentWorkflow.value?.id === workflowId) {
        currentWorkflow.value = null
      }
    } catch (error) {
      console.error('删除工作流失败:', error)
      throw error
    }
  }
  
  const duplicateWorkflow = async (workflowId: string, newName: string) => {
    try {
      const workflow = await workflowAPI.duplicateWorkflow(workflowId, newName)
      workflows.value.unshift(workflow)
      return workflow
    } catch (error) {
      console.error('复制工作流失败:', error)
      throw error
    }
  }
  
  // 工作流执行
  const executeWorkflow = async (data: {
    workflowId: string
    macAddress?: string
    serialNumber?: string
    operator?: string
    workstation?: string
    deviceId?: string
    variables?: Record<string, any>
  }) => {
    try {
      isExecuting.value = true
      const execution = await workflowExecutionAPI.executeWorkflow(data)
      currentExecution.value = execution
      executions.value.unshift(execution)
      return execution
    } catch (error) {
      console.error('执行工作流失败:', error)
      throw error
    } finally {
      isExecuting.value = false
    }
  }
  
  const loadExecutions = async (params: {
    page?: number
    pageSize?: number
    workflowId?: string
    status?: string
  } = {}) => {
    try {
      const response = await workflowExecutionAPI.getExecutions(params)
      executions.value = response.executions
      return response
    } catch (error) {
      console.error('加载执行记录失败:', error)
      throw error
    }
  }
  
  const stopExecution = async (executionId: string) => {
    try {
      await workflowExecutionAPI.stopExecution(executionId)
      const execution = executions.value.find(e => e.id === executionId)
      if (execution) {
        execution.status = 'cancelled'
      }
      if (currentExecution.value?.id === executionId) {
        currentExecution.value.status = 'cancelled'
        isExecuting.value = false
      }
    } catch (error) {
      console.error('停止执行失败:', error)
      throw error
    }
  }
  
  const retryExecution = async (executionId: string) => {
    try {
      const execution = await workflowExecutionAPI.retryExecution(executionId)
      const index = executions.value.findIndex(e => e.id === executionId)
      if (index !== -1) {
        executions.value[index] = execution
      }
      return execution
    } catch (error) {
      console.error('重新执行失败:', error)
      throw error
    }
  }
  
  // 模板管理
  const loadTemplates = async (params: {
    page?: number
    pageSize?: number
    category?: string
    search?: string
  } = {}) => {
    try {
      const response = await workflowTemplateAPI.getTemplates(params)
      templates.value = response.templates
      return response
    } catch (error) {
      console.error('加载模板失败:', error)
      throw error
    }
  }
  
  const createFromTemplate = async (templateId: string, name: string) => {
    try {
      const workflow = await workflowTemplateAPI.createFromTemplate(templateId, name)
      workflows.value.unshift(workflow)
      return workflow
    } catch (error) {
      console.error('从模板创建工作流失败:', error)
      throw error
    }
  }
  
  // 统计信息
  const loadStats = async () => {
    try {
      const statsData = await workflowStatsAPI.getStats()
      stats.value = statsData
      return statsData
    } catch (error) {
      console.error('加载统计信息失败:', error)
      throw error
    }
  }
  
  // 设计器操作
  const selectNode = (node: WorkflowNode | null) => {
    selectedNode.value = node
    selectedConnection.value = null
  }
  
  const selectConnection = (connection: WorkflowConnection | null) => {
    selectedConnection.value = connection
    selectedNode.value = null
  }
  
  const addNode = (node: WorkflowNode) => {
    if (currentWorkflow.value) {
      currentWorkflow.value.nodes.push(node)
      isDesignerDirty.value = true
    }
  }
  
  const updateNode = (nodeId: string, updates: Partial<WorkflowNode>) => {
    if (currentWorkflow.value) {
      const index = currentWorkflow.value.nodes.findIndex(n => n.id === nodeId)
      if (index !== -1) {
        currentWorkflow.value.nodes[index] = { ...currentWorkflow.value.nodes[index], ...updates }
        isDesignerDirty.value = true
      }
    }
  }
  
  const removeNode = (nodeId: string) => {
    if (currentWorkflow.value) {
      currentWorkflow.value.nodes = currentWorkflow.value.nodes.filter(n => n.id !== nodeId)
      currentWorkflow.value.connections = currentWorkflow.value.connections.filter(
        c => c.sourceNodeId !== nodeId && c.targetNodeId !== nodeId
      )
      isDesignerDirty.value = true
    }
  }
  
  const addConnection = (connection: WorkflowConnection) => {
    if (currentWorkflow.value) {
      currentWorkflow.value.connections.push(connection)
      isDesignerDirty.value = true
    }
  }
  
  const removeConnection = (connectionId: string) => {
    if (currentWorkflow.value) {
      currentWorkflow.value.connections = currentWorkflow.value.connections.filter(
        c => c.id !== connectionId
      )
      isDesignerDirty.value = true
    }
  }
  
  const saveWorkflow = async () => {
    if (currentWorkflow.value) {
      try {
        await updateWorkflow(currentWorkflow.value.id, currentWorkflow.value)
        isDesignerDirty.value = false
        return true
      } catch (error) {
        console.error('保存工作流失败:', error)
        throw error
      }
    }
    return false
  }
  
  // 重置状态
  const resetCurrentWorkflow = () => {
    currentWorkflow.value = null
    selectedNode.value = null
    selectedConnection.value = null
    isDesignerDirty.value = false
  }
  
  const resetExecution = () => {
    currentExecution.value = null
    isExecuting.value = false
    executionProgress.value = 0
  }
  
  return {
    // 状态
    workflows,
    currentWorkflow,
    executions,
    templates,
    stats,
    currentExecution,
    isExecuting,
    executionProgress,
    selectedNode,
    selectedConnection,
    isDesignerDirty,
    
    // 计算属性
    activeWorkflows,
    runningExecutions,
    completedExecutions,
    failedExecutions,
    
    // 工作流管理
    loadWorkflows,
    loadWorkflow,
    createWorkflow,
    updateWorkflow,
    deleteWorkflow,
    duplicateWorkflow,
    
    // 工作流执行
    executeWorkflow,
    loadExecutions,
    stopExecution,
    retryExecution,
    
    // 模板管理
    loadTemplates,
    createFromTemplate,
    
    // 统计信息
    loadStats,
    
    // 设计器操作
    selectNode,
    selectConnection,
    addNode,
    updateNode,
    removeNode,
    addConnection,
    removeConnection,
    saveWorkflow,
    
    // 重置状态
    resetCurrentWorkflow,
    resetExecution
  }
})