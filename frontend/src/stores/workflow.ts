/**
 * 工作流状态管理
 */

import { defineStore } from 'pinia'
import { ref, reactive, computed } from 'vue'
import { workflowApi, type WorkflowDefinition, type WorkflowExecution, type WorkflowStep } from '@/api/workflow'
import { ElMessage } from 'element-plus'

export const useWorkflowStore = defineStore('workflow', () => {
  // 状态
  const workflows = ref<WorkflowDefinition[]>([])
  const currentWorkflow = ref<WorkflowDefinition | null>(null)
  const executions = ref<WorkflowExecution[]>([])
  const currentExecution = ref<WorkflowExecution | null>(null)
  const isLoading = ref(false)

  // 工作流编辑器状态
  const editorWorkflow = reactive<{
    name: string
    description: string
    variables: Record<string, any>
    steps: WorkflowStep[]
  }>({
    name: '',
    description: '',
    variables: {},
    steps: []
  })

  // 计算属性
  const runningExecutions = computed(() => 
    executions.value.filter(e => e.status === 'running' || e.status === 'paused')
  )

  const completedExecutions = computed(() => 
    executions.value.filter(e => e.status === 'completed' || e.status === 'failed' || e.status === 'cancelled')
  )

  // 工作流管理方法
  const loadWorkflows = async () => {
    try {
      isLoading.value = true
      const response = await workflowApi.listWorkflows()
      workflows.value = response.data.workflows
    } catch (error: any) {
      ElMessage.error(`加载工作流失败: ${error.response?.data?.msg || error.message}`)
    } finally {
      isLoading.value = false
    }
  }

  const createWorkflow = async (workflowData: any) => {
    try {
      isLoading.value = true
      const response = await workflowApi.createWorkflow(workflowData)
      workflows.value.push(response.data)
      ElMessage.success('工作流创建成功')
      return response.data
    } catch (error: any) {
      ElMessage.error(`创建工作流失败: ${error.response?.data?.msg || error.message}`)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  const updateWorkflow = async (workflowId: string, updateData: any) => {
    try {
      isLoading.value = true
      const response = await workflowApi.updateWorkflow(workflowId, updateData)
      const index = workflows.value.findIndex(w => w.id === workflowId)
      if (index >= 0) {
        workflows.value[index] = response.data
      }
      ElMessage.success('工作流更新成功')
      return response.data
    } catch (error: any) {
      ElMessage.error(`更新工作流失败: ${error.response?.data?.msg || error.message}`)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  const deleteWorkflow = async (workflowId: string) => {
    try {
      await workflowApi.deleteWorkflow(workflowId)
      workflows.value = workflows.value.filter(w => w.id !== workflowId)
      ElMessage.success('工作流删除成功')
    } catch (error: any) {
      ElMessage.error(`删除工作流失败: ${error.response?.data?.msg || error.message}`)
      throw error
    }
  }

  const getWorkflow = async (workflowId: string) => {
    try {
      const response = await workflowApi.getWorkflow(workflowId)
      currentWorkflow.value = response.data
      return response.data
    } catch (error: any) {
      ElMessage.error(`获取工作流失败: ${error.response?.data?.msg || error.message}`)
      throw error
    }
  }

  // 工作流执行方法
  const executeWorkflow = async (workflowId: string, executeData: any = {}) => {
    try {
      const response = await workflowApi.executeWorkflow(workflowId, executeData)
      ElMessage.success('工作流开始执行')
      
      // 开始监控执行状态
      startExecutionMonitoring(response.data.execution_id)
      
      return response.data
    } catch (error: any) {
      ElMessage.error(`执行工作流失败: ${error.response?.data?.msg || error.message}`)
      throw error
    }
  }

  const getExecutionStatus = async (executionId: string) => {
    try {
      const response = await workflowApi.getExecutionStatus(executionId)
      
      // 更新执行列表
      const index = executions.value.findIndex(e => e.id === executionId)
      if (index >= 0) {
        executions.value[index] = response.data
      } else {
        executions.value.push(response.data)
      }
      
      // 更新当前执行
      if (currentExecution.value?.id === executionId) {
        currentExecution.value = response.data
      }
      
      return response.data
    } catch (error: any) {
      console.error(`获取执行状态失败: ${error.response?.data?.msg || error.message}`)
      throw error
    }
  }

  const confirmWorkflowStep = async (executionId: string, action: string) => {
    try {
      await workflowApi.confirmWorkflowStep({ execution_id: executionId, action })
      ElMessage.success(`确认操作成功: ${action}`)
    } catch (error: any) {
      ElMessage.error(`确认操作失败: ${error.response?.data?.msg || error.message}`)
      throw error
    }
  }

  const cancelExecution = async (executionId: string) => {
    try {
      await workflowApi.cancelExecution(executionId)
      ElMessage.success('工作流执行已取消')
    } catch (error: any) {
      ElMessage.error(`取消执行失败: ${error.response?.data?.msg || error.message}`)
      throw error
    }
  }

  const loadExecutions = async () => {
    try {
      const response = await workflowApi.listExecutions()
      executions.value = response.data.executions
    } catch (error: any) {
      ElMessage.error(`加载执行列表失败: ${error.response?.data?.msg || error.message}`)
    }
  }

  // 执行监控
  const executionMonitors = new Map<string, NodeJS.Timeout>()

  const startExecutionMonitoring = (executionId: string) => {
    // 停止已有的监控
    if (executionMonitors.has(executionId)) {
      clearInterval(executionMonitors.get(executionId)!)
    }

    // 开始新的监控
    const timer = setInterval(async () => {
      try {
        const execution = await getExecutionStatus(executionId)
        
        // 如果执行完成，停止监控
        if (['completed', 'failed', 'cancelled'].includes(execution.status)) {
          stopExecutionMonitoring(executionId)
        }
      } catch (error) {
        console.error('监控执行状态失败:', error)
        stopExecutionMonitoring(executionId)
      }
    }, 2000)

    executionMonitors.set(executionId, timer)
  }

  const stopExecutionMonitoring = (executionId: string) => {
    if (executionMonitors.has(executionId)) {
      clearInterval(executionMonitors.get(executionId)!)
      executionMonitors.delete(executionId)
    }
  }

  // 编辑器方法
  const resetEditor = () => {
    editorWorkflow.name = ''
    editorWorkflow.description = ''
    editorWorkflow.variables = {}
    editorWorkflow.steps = []
  }

  const loadWorkflowToEditor = (workflow: WorkflowDefinition) => {
    editorWorkflow.name = workflow.name
    editorWorkflow.description = workflow.description || ''
    editorWorkflow.variables = { ...workflow.variables }
    editorWorkflow.steps = [...workflow.steps]
  }

  const addStep = (step: WorkflowStep) => {
    editorWorkflow.steps.push(step)
  }

  const removeStep = (stepId: string) => {
    const index = editorWorkflow.steps.findIndex(s => s.id === stepId)
    if (index >= 0) {
      editorWorkflow.steps.splice(index, 1)
    }
  }

  const updateStep = (stepId: string, stepData: Partial<WorkflowStep>) => {
    const index = editorWorkflow.steps.findIndex(s => s.id === stepId)
    if (index >= 0) {
      editorWorkflow.steps[index] = { ...editorWorkflow.steps[index], ...stepData }
    }
  }

  const moveStep = (fromIndex: number, toIndex: number) => {
    const step = editorWorkflow.steps.splice(fromIndex, 1)[0]
    editorWorkflow.steps.splice(toIndex, 0, step)
  }

  // 清理方法
  const cleanup = () => {
    // 清理所有监控器
    for (const [executionId] of executionMonitors) {
      stopExecutionMonitoring(executionId)
    }
  }

  return {
    // 状态
    workflows,
    currentWorkflow,
    executions,
    currentExecution,
    isLoading,
    editorWorkflow,
    
    // 计算属性
    runningExecutions,
    completedExecutions,
    
    // 方法
    loadWorkflows,
    createWorkflow,
    updateWorkflow,
    deleteWorkflow,
    getWorkflow,
    executeWorkflow,
    getExecutionStatus,
    confirmWorkflowStep,
    cancelExecution,
    loadExecutions,
    startExecutionMonitoring,
    stopExecutionMonitoring,
    resetEditor,
    loadWorkflowToEditor,
    addStep,
    removeStep,
    updateStep,
    moveStep,
    cleanup
  }
})