<template>
  <div class="workflow-execution">
    <div class="page-header">
      <el-breadcrumb>
        <el-breadcrumb-item @click="$router.push('/workflow')">工作流管理</el-breadcrumb-item>
        <el-breadcrumb-item>执行监控</el-breadcrumb-item>
      </el-breadcrumb>
      
      <div class="header-actions">
        <el-button @click="$router.push('/workflow')">返回</el-button>
        <el-button 
          v-if="execution && ['running', 'paused'].includes(execution.status)"
          type="danger" 
          @click="cancelExecution"
          :icon="Close"
        >
          取消执行
        </el-button>
      </div>
    </div>

    <div v-if="!execution" class="loading-state">
      <el-skeleton :rows="5" animated />
    </div>

    <div v-else class="execution-content">
      <!-- 执行信息 -->
      <el-card class="execution-info">
        <template #header>
          <span>执行信息</span>
        </template>
        
        <el-descriptions :column="2" border>
          <el-descriptions-item label="执行ID">
            {{ execution.id }}
          </el-descriptions-item>
          <el-descriptions-item label="工作流">
            {{ getWorkflowName(execution.workflow_id) }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusTagType(execution.status)">
              {{ getStatusLabel(execution.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="当前步骤">
            {{ execution.current_step || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="开始时间">
            {{ formatDate(execution.started_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="完成时间">
            {{ execution.completed_at ? formatDate(execution.completed_at) : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="错误信息" v-if="execution.error_message">
            <el-text type="danger">{{ execution.error_message }}</el-text>
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <div class="execution-details">
        <!-- 变量状态 -->
        <el-card class="variables-card">
          <template #header>
            <span>变量状态</span>
          </template>
          
          <div v-if="Object.keys(execution.variables).length === 0" class="empty-variables">
            <el-empty description="暂无变量" />
          </div>
          
          <el-table v-else :data="variableTableData" size="small">
            <el-table-column prop="name" label="变量名" width="150" />
            <el-table-column prop="value" label="当前值" show-overflow-tooltip>
              <template #default="{ row }">
                <code>{{ formatVariableValue(row.value) }}</code>
              </template>
            </el-table-column>
            <el-table-column prop="type" label="类型" width="80" />
          </el-table>
        </el-card>

        <!-- 执行日志 -->
        <el-card class="logs-card">
          <template #header>
            <div class="logs-header">
              <span>执行日志 ({{ execution.logs.length }})</span>
              <div class="log-filters">
                <el-select 
                  v-model="logLevelFilter" 
                  placeholder="日志级别"
                  clearable
                  size="small"
                  style="width: 100px"
                >
                  <el-option label="INFO" value="INFO" />
                  <el-option label="WARNING" value="WARNING" />
                  <el-option label="ERROR" value="ERROR" />
                </el-select>
                <el-button 
                  size="small" 
                  @click="scrollToBottom"
                  :icon="Bottom"
                >
                  底部
                </el-button>
                <el-button 
                  size="small" 
                  @click="clearLogs"
                  :icon="Delete"
                >
                  清空
                </el-button>
              </div>
            </div>
          </template>
          
          <div class="logs-container" ref="logsContainer">
            <div v-if="filteredLogs.length === 0" class="empty-logs">
              <el-empty description="暂无日志" />
            </div>
            
            <div v-else class="logs-list">
              <div 
                v-for="(log, index) in filteredLogs" 
                :key="index"
                class="log-item"
                :class="[`log-${log.level.toLowerCase()}`]"
              >
                <div class="log-header">
                  <span class="log-time">{{ formatTime(log.timestamp) }}</span>
                  <el-tag :type="getLogTagType(log.level)" size="small">
                    {{ log.level }}
                  </el-tag>
                  <span class="log-step">{{ log.step_id }}</span>
                </div>
                <div class="log-message">{{ log.message }}</div>
                <div v-if="log.data" class="log-data">
                  <pre>{{ JSON.stringify(log.data, null, 2) }}</pre>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 确认对话框 -->
    <el-dialog 
      v-model="confirmDialogVisible" 
      :title="confirmData.message"
      width="400px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <p>{{ confirmData.message }}</p>
      
      <template #footer>
        <div class="confirm-actions">
          <el-button 
            v-for="option in confirmData.options" 
            :key="option"
            :type="option === '确认' ? 'primary' : 'default'"
            @click="handleConfirm(option)"
          >
            {{ option }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Close, Bottom, Delete, View 
} from '@element-plus/icons-vue'
import { useWorkflowStore } from '@/stores/workflow'
import type { WorkflowExecution, WorkflowLog } from '@/api/workflow'

const router = useRouter()
const route = useRoute()
const workflowStore = useWorkflowStore()

// 状态
const execution = ref<WorkflowExecution | null>(null)
const logLevelFilter = ref('')
const logsContainer = ref<HTMLElement>()
const confirmDialogVisible = ref(false)
const confirmData = reactive({
  execution_id: '',
  message: '',
  options: [] as string[]
})

// 计算属性
const filteredLogs = computed(() => {
  if (!execution.value || !logLevelFilter.value) {
    return execution.value?.logs || []
  }
  return execution.value.logs.filter(log => log.level === logLevelFilter.value)
})

const variableTableData = computed(() => {
  if (!execution.value) return []
  
  return Object.entries(execution.value.variables).map(([name, value]) => ({
    name,
    value,
    type: typeof value
  }))
})

// 方法
const loadExecution = async () => {
  const executionId = route.params.id as string
  try {
    execution.value = await workflowStore.getExecutionStatus(executionId)
    workflowStore.currentExecution = execution.value
    
    // 如果正在运行，开始监控
    if (['running', 'paused'].includes(execution.value.status)) {
      workflowStore.startExecutionMonitoring(executionId)
    }
  } catch (error) {
    ElMessage.error('加载执行信息失败')
    router.push('/workflow')
  }
}

const cancelExecution = async () => {
  if (!execution.value) return
  
  try {
    await ElMessageBox.confirm('确定要取消这个执行吗？', '确认取消', {
      type: 'warning'
    })
    
    await workflowStore.cancelExecution(execution.value.id)
    await loadExecution()
  } catch {
    // 用户取消
  }
}

const scrollToBottom = () => {
  if (logsContainer.value) {
    nextTick(() => {
      logsContainer.value!.scrollTop = logsContainer.value!.scrollHeight
    })
  }
}

const clearLogs = () => {
  // 这里只是清空显示，不影响实际日志
  logLevelFilter.value = 'NONE' // 设置一个不存在的级别来隐藏所有日志
  setTimeout(() => {
    logLevelFilter.value = ''
  }, 100)
}

const handleConfirm = async (action: string) => {
  try {
    await workflowStore.confirmWorkflowStep(confirmData.execution_id, action)
    confirmDialogVisible.value = false
  } catch (error) {
    // 错误已在store中处理
  }
}

// 工具方法
const getWorkflowName = (workflowId: string) => {
  const workflow = workflowStore.workflows.find(w => w.id === workflowId)
  return workflow?.name || workflowId
}

const getStatusLabel = (status: string) => {
  const labels = {
    pending: '等待中',
    running: '运行中',
    paused: '已暂停',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return labels[status as keyof typeof labels] || status
}

const getStatusTagType = (status: string) => {
  const types = {
    pending: '',
    running: 'warning',
    paused: 'info',
    completed: 'success',
    failed: 'danger',
    cancelled: 'info'
  }
  return types[status as keyof typeof types] || ''
}

const getLogTagType = (level: string) => {
  const types = {
    INFO: 'success',
    WARNING: 'warning',
    ERROR: 'danger'
  }
  return types[level as keyof typeof types] || ''
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

const formatTime = (dateStr: string) => {
  return new Date(dateStr).toLocaleTimeString('zh-CN')
}

const formatVariableValue = (value: any) => {
  if (typeof value === 'string') {
    return `"${value}"`
  } else if (typeof value === 'object') {
    return JSON.stringify(value)
  }
  return String(value)
}

// WebSocket消息处理
const handleWebSocketMessage = (message: any) => {
  if (message.type === 'workflow_log' && message.execution_id === execution.value?.id) {
    // 添加新日志
    execution.value.logs.push(message)
    
    // 自动滚动到底部
    nextTick(() => {
      scrollToBottom()
    })
  } else if (message.type === 'workflow_confirm' && message.execution_id === execution.value?.id) {
    // 显示确认对话框
    confirmData.execution_id = message.execution_id
    confirmData.message = message.message
    confirmData.options = message.options
    confirmDialogVisible.value = true
  } else if (message.type === 'workflow_status' && message.execution_id === execution.value?.id) {
    // 更新执行状态
    if (execution.value) {
      execution.value.status = message.status
      execution.value.current_step = message.current_step
    }
  }
}

// 生命周期
onMounted(async () => {
  await workflowStore.loadWorkflows()
  await loadExecution()
  
  // 注册WebSocket消息监听
  // TODO: 实现WebSocket监听
})

onUnmounted(() => {
  if (execution.value) {
    workflowStore.stopExecutionMonitoring(execution.value.id)
  }
})
</script>

<style scoped>
.workflow-execution {
  padding: 20px;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.loading-state {
  flex: 1;
  padding: 20px;
}

.execution-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow: hidden;
}

.execution-info {
  flex-shrink: 0;
}

.execution-details {
  flex: 1;
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 20px;
  overflow: hidden;
}

.variables-card {
  display: flex;
  flex-direction: column;
}

.logs-card {
  display: flex;
  flex-direction: column;
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.log-filters {
  display: flex;
  gap: 10px;
  align-items: center;
}

.empty-variables, .empty-logs {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 150px;
}

.logs-container {
  flex: 1;
  overflow-y: auto;
  max-height: 500px;
}

.logs-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.log-item {
  padding: 10px;
  border-radius: 6px;
  border-left: 3px solid;
}

.log-item.log-info {
  border-left-color: var(--el-color-success);
  background-color: var(--el-color-success-light-9);
}

.log-item.log-warning {
  border-left-color: var(--el-color-warning);
  background-color: var(--el-color-warning-light-9);
}

.log-item.log-error {
  border-left-color: var(--el-color-danger);
  background-color: var(--el-color-danger-light-9);
}

.log-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 5px;
}

.log-time {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  font-family: 'Courier New', monospace;
}

.log-step {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

.log-message {
  font-size: 14px;
  line-height: 1.4;
}

.log-data {
  margin-top: 8px;
  background: var(--el-fill-color-darker);
  border-radius: 4px;
  padding: 8px;
}

.log-data pre {
  margin: 0;
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.confirm-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
}

:deep(.el-card__body) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

:deep(.el-table) {
  flex: 1;
}

code {
  background: var(--el-fill-color-light);
  padding: 2px 4px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
}
</style>