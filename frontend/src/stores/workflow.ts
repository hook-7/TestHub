/**
 * 工作流状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage, ElNotification, ElMessageBox } from 'element-plus'
import WorkflowAPI, {
  type WorkflowDefinition,
  type WorkflowExecution,
  type WorkflowExecutionRequest,
  type UserConfirmationRequest
} from '@/api/workflow'

export const useWorkflowStore = defineStore('workflow', () => {
  // 状态
  const workflows = ref<WorkflowDefinition[]>([])
  const executions = ref<WorkflowExecution[]>([])
  const currentExecution = ref<WorkflowExecution | null>(null)
  const loading = ref(false)
  const executing = ref(false)
  
  // WebSocket连接
  const websocket = ref<WebSocket | null>(null)
  const wsConnected = ref(false)
  const workstationId = ref('WS001')

  // 计算属性
  const runningExecutions = computed(() => 
    (executions.value || []).filter(exec => exec.status === 'running')
  )

  const pausedExecutions = computed(() => 
    (executions.value || []).filter(exec => exec.status === 'paused')
  )

  const recentExecutions = computed(() => 
    (executions.value || [])
      .sort((a, b) => new Date(b.started_at || 0).getTime() - new Date(a.started_at || 0).getTime())
      .slice(0, 10)
  )

  /**
   * 加载工作流列表
   */
  const loadWorkflows = async () => {
    try {
      loading.value = true
      const data = await WorkflowAPI.getWorkflows()
      workflows.value = data || []
    } catch (error) {
      console.error('加载工作流失败:', error)
      ElMessage.error('加载工作流失败')
    } finally {
      loading.value = false
    }
  }

  /**
   * 执行工作流
   */
  const executeWorkflow = async (
    workflowId: string,
    inputVariables: Record<string, any> = {},
    operatorId?: string
  ): Promise<WorkflowExecution | null> => {
    try {
      executing.value = true
      
      const request: WorkflowExecutionRequest = {
        workflow_id: workflowId,
        input_variables: inputVariables,
        operator_id: operatorId,
        workstation_id: workstationId.value
      }
      
      const execution = await WorkflowAPI.executeWorkflow(workflowId, request)
      
      executions.value.unshift(execution)
      currentExecution.value = execution
      
      ElMessage.success('工作流已启动')
      
      // 开始监控执行状态
      monitorExecution(execution.execution_id)
      
      return execution
    } catch (error) {
      console.error('执行工作流失败:', error)
      ElMessage.error('执行工作流失败')
      return null
    } finally {
      executing.value = false
    }
  }

  /**
   * 监控工作流执行
   */
  const monitorExecution = (executionId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const execution = await WorkflowAPI.getExecution(executionId)
        
        // 更新本地状态
        const index = executions.value.findIndex(exec => exec.execution_id === executionId)
        if (index !== -1) {
          executions.value[index] = execution
        }
        
        if (currentExecution.value?.execution_id === executionId) {
          currentExecution.value = execution
        }
        
        // 如果执行完成，停止监控
        if (['completed', 'failed', 'cancelled'].includes(execution.status)) {
          clearInterval(pollInterval)
          
          if (execution.status === 'completed') {
            ElNotification.success({
              title: '工作流执行完成',
              message: `${execution.workflow_name} 已成功完成`,
              duration: 5000
            })
          } else if (execution.status === 'failed') {
            ElNotification.error({
              title: '工作流执行失败',
              message: `${execution.workflow_name} 执行失败: ${execution.error_message}`,
              duration: 0
            })
          }
        }
      } catch (error) {
        console.error('监控执行状态失败:', error)
        clearInterval(pollInterval)
      }
    }, 3000) // 每3秒轮询一次
    
    // 10分钟后停止监控
    setTimeout(() => {
      clearInterval(pollInterval)
    }, 600000)
  }

  /**
   * 初始化WebSocket连接
   */
  const initWebSocket = () => {
    try {
      const wsUrl = `ws://localhost:8000/api/v1/workflow/ws/${workstationId.value}`
      websocket.value = new WebSocket(wsUrl)
      
      websocket.value.onopen = () => {
        wsConnected.value = true
        console.log('工作流WebSocket已连接')
        
        // 发送心跳
        setInterval(() => {
          if (websocket.value?.readyState === WebSocket.OPEN) {
            websocket.value.send(JSON.stringify({ type: 'heartbeat' }))
          }
        }, 30000)
      }
      
      websocket.value.onmessage = (event) => {
        const message = JSON.parse(event.data)
        handleWebSocketMessage(message)
      }
      
      websocket.value.onclose = () => {
        wsConnected.value = false
        console.log('工作流WebSocket连接断开')
        
        // 5秒后重连
        setTimeout(() => {
          if (!wsConnected.value) {
            initWebSocket()
          }
        }, 5000)
      }
      
      websocket.value.onerror = (error) => {
        console.error('工作流WebSocket错误:', error)
        wsConnected.value = false
      }
      
    } catch (error) {
      console.error('初始化WebSocket失败:', error)
    }
  }

  /**
   * 处理WebSocket消息
   */
  const handleWebSocketMessage = (message: any) => {
    console.log('收到WebSocket消息:', message)
    
    if (message.message_type === 'user_confirmation_request') {
      showConfirmationDialog(message)
    } else if (message.message_type === 'workflow_step_update') {
      handleStepUpdate(message)
    }
  }

  /**
   * 显示确认对话框
   */
  const showConfirmationDialog = async (message: any) => {
    const { execution_id, step_id, data } = message
    
    try {
      // 使用Element Plus的确认对话框
      const result = await ElMessageBox({
        title: '工作流确认',
        message: `
          <div>
            <h4>${data.step_name}</h4>
            <p>${data.step_description || ''}</p>
            <div style="background: #f5f7fa; padding: 12px; border-radius: 4px; margin: 12px 0;">
              ${data.message.replace(/\n/g, '<br>')}
            </div>
          </div>
        `,
        dangerouslyUseHTMLString: true,
        showCancelButton: true,
        confirmButtonText: data.options?.[0] || '确认',
        cancelButtonText: data.options?.[1] || '取消',
        type: 'warning'
      })
      
      // 发送确认结果
      const confirmation: UserConfirmationRequest = {
        execution_id,
        step_id,
        confirmed: result === 'confirm',
        selected_option: result === 'confirm' ? data.options?.[0] : data.options?.[1],
        operator_notes: '通过WebSocket确认'
      }
      
      await confirmWorkflowStep(confirmation)
      
    } catch (error) {
      // 用户取消
      const confirmation: UserConfirmationRequest = {
        execution_id,
        step_id,
        confirmed: false,
        operator_notes: '用户取消操作'
      }
      
      await confirmWorkflowStep(confirmation)
    }
  }

  /**
   * 处理步骤更新
   */
  const handleStepUpdate = (message: any) => {
    const { execution_id, data } = message
    
    // 更新执行状态
    const execution = executions.value.find(exec => exec.execution_id === execution_id)
    if (execution) {
      // 这里可以更新步骤状态
      console.log(`步骤更新: ${data.step_name} - ${data.step_status}`)
    }
    
    // 显示步骤完成通知
    if (data.step_status === 'success') {
      ElMessage.success(`步骤完成: ${data.step_name}`)
    } else if (data.step_status === 'failed') {
      ElMessage.error(`步骤失败: ${data.step_name}`)
    }
  }

  /**
   * 确认工作流步骤
   */
  const confirmWorkflowStep = async (confirmation: UserConfirmationRequest) => {
    try {
      await WorkflowAPI.confirmStep(confirmation.execution_id, confirmation)
      
      // 通过WebSocket发送确认
      if (websocket.value?.readyState === WebSocket.OPEN) {
        websocket.value.send(JSON.stringify({
          type: 'user_confirmation',
          data: confirmation
        }))
      }
      
    } catch (error) {
      console.error('确认工作流步骤失败:', error)
      ElMessage.error('确认失败')
    }
  }

  /**
   * 暂停工作流
   */
  const pauseWorkflow = async (executionId: string) => {
    try {
      await WorkflowAPI.pauseWorkflow(executionId)
      
      // 更新本地状态
      const execution = executions.value.find(exec => exec.execution_id === executionId)
      if (execution) {
        execution.status = 'paused'
      }
      
      ElMessage.success('工作流已暂停')
    } catch (error) {
      console.error('暂停工作流失败:', error)
      ElMessage.error('暂停工作流失败')
    }
  }

  /**
   * 恢复工作流
   */
  const resumeWorkflow = async (executionId: string) => {
    try {
      await WorkflowAPI.resumeWorkflow(executionId)
      
      // 更新本地状态
      const execution = executions.value.find(exec => exec.execution_id === executionId)
      if (execution) {
        execution.status = 'running'
      }
      
      ElMessage.success('工作流已恢复')
    } catch (error) {
      console.error('恢复工作流失败:', error)
      ElMessage.error('恢复工作流失败')
    }
  }

  /**
   * 取消工作流
   */
  const cancelWorkflow = async (executionId: string) => {
    try {
      await WorkflowAPI.cancelWorkflow(executionId)
      
      // 更新本地状态
      const execution = executions.value.find(exec => exec.execution_id === executionId)
      if (execution) {
        execution.status = 'cancelled'
        execution.completed_at = new Date().toISOString()
      }
      
      ElMessage.success('工作流已取消')
    } catch (error) {
      console.error('取消工作流失败:', error)
      ElMessage.error('取消工作流失败')
    }
  }

  /**
   * 获取状态文本
   */
  const getStatusText = (status: string): string => {
    const statusMap: Record<string, string> = {
      draft: '草稿',
      ready: '就绪',
      running: '运行中',
      paused: '已暂停',
      completed: '已完成',
      failed: '失败',
      cancelled: '已取消'
    }
    return statusMap[status] || status
  }

  /**
   * 获取状态类型
   */
  const getStatusType = (status: string): string => {
    const typeMap: Record<string, string> = {
      draft: 'info',
      ready: 'primary',
      running: 'warning',
      paused: 'info',
      completed: 'success',
      failed: 'danger',
      cancelled: 'info'
    }
    return typeMap[status] || 'info'
  }

  /**
   * 获取步骤状态文本
   */
  const getStepStatusText = (status: string): string => {
    const statusMap: Record<string, string> = {
      pending: '等待执行',
      running: '执行中',
      success: '成功',
      failed: '失败',
      skipped: '跳过',
      waiting: '等待确认'
    }
    return statusMap[status] || status
  }

  /**
   * 断开WebSocket连接
   */
  const disconnectWebSocket = () => {
    if (websocket.value) {
      websocket.value.close()
      websocket.value = null
      wsConnected.value = false
    }
  }

  return {
    // 状态
    workflows,
    executions,
    currentExecution,
    loading,
    executing,
    wsConnected,
    workstationId,
    
    // 计算属性
    runningExecutions,
    pausedExecutions,
    recentExecutions,
    
    // 方法
    loadWorkflows,
    executeWorkflow,
    pauseWorkflow,
    resumeWorkflow,
    cancelWorkflow,
    confirmWorkflowStep,
    initWebSocket,
    disconnectWebSocket,
    
    // 工具方法
    getStatusText,
    getStatusType,
    getStepStatusText
  }
})