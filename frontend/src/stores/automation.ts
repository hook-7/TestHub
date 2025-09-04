/**
 * 自动化命令状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AutomationAPI, { 
  type AutomationCommand, 
  type CommandTemplate, 
  type AutomationCommandRequest,
  type CommandListParams 
} from '@/api/automation'

export const useAutomationStore = defineStore('automation', () => {
  // 状态
  const commands = ref<AutomationCommand[]>([])
  const templates = ref<CommandTemplate[]>([])
  const currentCommand = ref<AutomationCommand | null>(null)
  const loading = ref(false)
  const executing = ref(false)

  // 计算属性
  const pendingCommands = computed(() => 
    commands.value.filter(cmd => cmd.status === 'pending')
  )

  const executingCommands = computed(() => 
    commands.value.filter(cmd => cmd.status === 'executing')
  )

  const recentCommands = computed(() => 
    commands.value
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      .slice(0, 10)
  )

  /**
   * 加载命令模板
   */
  const loadTemplates = async () => {
    try {
      loading.value = true
      const data = await AutomationAPI.getTemplates()
      templates.value = data || []
    } catch (error) {
      console.error('加载模板失败:', error)
      ElMessage.error('加载模板失败')
    } finally {
      loading.value = false
    }
  }

  /**
   * 加载命令列表
   */
  const loadCommands = async (params?: CommandListParams) => {
    try {
      loading.value = true
      const data = await AutomationAPI.getCommands(params)
      commands.value = data?.commands || []
    } catch (error) {
      console.error('加载命令列表失败:', error)
      ElMessage.error('加载命令列表失败')
    } finally {
      loading.value = false
    }
  }

  /**
   * 创建自动化命令
   */
  const createCommand = async (request: AutomationCommandRequest): Promise<AutomationCommand | null> => {
    try {
      executing.value = true
      const command = await AutomationAPI.createCommand(request)
      commands.value.unshift(command)
      currentCommand.value = command
      
      ElMessage.success('命令创建成功')
      
      // 如果需要确认，显示确认弹窗
      if (request.requires_confirmation && command.status === 'pending') {
        await showConfirmationDialog(command)
      }
      
      return command
    } catch (error) {
      console.error('创建命令失败:', error)
      ElMessage.error('创建命令失败')
      return null
    } finally {
      executing.value = false
    }
  }

  /**
   * 根据模板执行命令
   */
  const executeTemplate = async (
    templateId: string, 
    parameters: Record<string, any>,
    operatorId?: string,
    workstationId?: string
  ): Promise<AutomationCommand | null> => {
    try {
      executing.value = true
      const command = await AutomationAPI.executeTemplateCommand(
        templateId, 
        parameters, 
        operatorId, 
        workstationId
      )
      
      commands.value.unshift(command)
      currentCommand.value = command
      
      ElMessage.success('命令创建成功')
      
      // 如果需要确认，显示确认弹窗
      const template = templates.value.find(t => t.template_id === templateId)
      if (template?.requires_confirmation && command.status === 'pending') {
        await showConfirmationDialog(command)
      }
      
      return command
    } catch (error) {
      console.error('执行模板命令失败:', error)
      ElMessage.error('执行模板命令失败')
      return null
    } finally {
      executing.value = false
    }
  }

  /**
   * 显示确认弹窗
   */
  const showConfirmationDialog = async (command: AutomationCommand): Promise<boolean> => {
    try {
      await ElMessageBox.confirm(
        `确定要执行命令吗？`,
        '命令确认',
        {
          confirmButtonText: '确认执行',
          cancelButtonText: '取消',
          type: 'warning',
          customClass: 'automation-confirm-dialog',
          beforeClose: (action, instance, done) => {
            if (action === 'confirm') {
              confirmCommand(command.command_id, true)
            } else {
              confirmCommand(command.command_id, false)
            }
            done()
          }
        }
      )
      return true
    } catch (error) {
      // 用户取消
      await confirmCommand(command.command_id, false)
      return false
    }
  }

  /**
   * 确认命令执行
   */
  const confirmCommand = async (commandId: string, confirmed: boolean, notes?: string) => {
    try {
      const command = await AutomationAPI.confirmCommand(commandId, {
        command_id: commandId,
        confirmed,
        operator_notes: notes
      })
      
      // 更新本地命令状态
      const index = commands.value.findIndex(cmd => cmd.command_id === commandId)
      if (index !== -1) {
        commands.value[index] = command
      }
      
      if (currentCommand.value?.command_id === commandId) {
        currentCommand.value = command
      }
      
      if (confirmed) {
        ElMessage.success('命令已确认执行')
        // 开始轮询检查执行状态
        pollCommandStatus(commandId)
      } else {
        ElMessage.info('命令已取消')
      }
    } catch (error) {
      console.error('确认命令失败:', error)
      ElMessage.error('确认命令失败')
    }
  }

  /**
   * 轮询命令执行状态
   */
  const pollCommandStatus = async (commandId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const command = await AutomationAPI.getCommand(commandId)
        
        // 更新本地状态
        const index = commands.value.findIndex(cmd => cmd.command_id === commandId)
        if (index !== -1) {
          commands.value[index] = command
        }
        
        if (currentCommand.value?.command_id === commandId) {
          currentCommand.value = command
        }
        
        // 如果命令完成，停止轮询
        if (['success', 'failed', 'cancelled'].includes(command.status)) {
          clearInterval(pollInterval)
          
          if (command.status === 'success') {
            ElMessage.success('命令执行成功')
          } else if (command.status === 'failed') {
            ElMessage.error(`命令执行失败: ${command.error_message}`)
          }
        }
      } catch (error) {
        console.error('轮询命令状态失败:', error)
        clearInterval(pollInterval)
      }
    }, 2000) // 每2秒轮询一次
    
    // 30秒后停止轮询
    setTimeout(() => {
      clearInterval(pollInterval)
    }, 30000)
  }

  /**
   * 取消命令
   */
  const cancelCommand = async (commandId: string) => {
    try {
      const command = await AutomationAPI.cancelCommand(commandId)
      
      // 更新本地状态
      const index = commands.value.findIndex(cmd => cmd.command_id === commandId)
      if (index !== -1) {
        commands.value[index] = command
      }
      
      if (currentCommand.value?.command_id === commandId) {
        currentCommand.value = command
      }
      
      ElMessage.success('命令已取消')
    } catch (error) {
      console.error('取消命令失败:', error)
      ElMessage.error('取消命令失败')
    }
  }

  /**
   * 刷新命令状态
   */
  const refreshCommand = async (commandId: string) => {
    try {
      const command = await AutomationAPI.getCommand(commandId)
      
      // 更新本地状态
      const index = commands.value.findIndex(cmd => cmd.command_id === commandId)
      if (index !== -1) {
        commands.value[index] = command
      }
      
      if (currentCommand.value?.command_id === commandId) {
        currentCommand.value = command
      }
    } catch (error) {
      console.error('刷新命令状态失败:', error)
    }
  }

  /**
   * 获取状态显示文本
   */
  const getStatusText = (status: string): string => {
    const statusMap: Record<string, string> = {
      pending: '等待确认',
      confirmed: '已确认',
      executing: '执行中',
      success: '执行成功',
      failed: '执行失败',
      cancelled: '已取消'
    }
    return statusMap[status] || status
  }

  /**
   * 获取状态颜色类型
   */
  const getStatusType = (status: string): string => {
    const typeMap: Record<string, string> = {
      pending: 'warning',
      confirmed: 'info',
      executing: 'primary',
      success: 'success',
      failed: 'danger',
      cancelled: 'info'
    }
    return typeMap[status] || 'info'
  }

  /**
   * 获取命令类型显示文本
   */
  const getCommandTypeText = (type: string): string => {
    const typeMap: Record<string, string> = {
      system: '系统命令',
      device: '设备命令',
      test: '测试命令',
      maintenance: '维护命令'
    }
    return typeMap[type] || type
  }

  return {
    // 状态
    commands,
    templates,
    currentCommand,
    loading,
    executing,
    
    // 计算属性
    pendingCommands,
    executingCommands,
    recentCommands,
    
    // 方法
    loadTemplates,
    loadCommands,
    createCommand,
    executeTemplate,
    confirmCommand,
    cancelCommand,
    refreshCommand,
    
    // 工具方法
    getStatusText,
    getStatusType,
    getCommandTypeText
  }
})