<template>
  <div class="workflow-control">
    <el-card class="header-card">
      <template #header>
        <div class="card-header">
          <span>🔄 工作流自动化控制</span>
          <div class="header-actions">
            <el-tag :type="wsConnected ? 'success' : 'danger'" class="ws-status">
              <el-icon>
                <component :is="wsConnected ? 'Connection' : 'Disconnect'" />
              </el-icon>
              {{ wsConnected ? 'WebSocket已连接' : 'WebSocket未连接' }}
            </el-tag>
            <el-button type="primary" @click="initWebSocket" v-if="!wsConnected">
              连接WebSocket
            </el-button>
          </div>
        </div>
      </template>
      
      <!-- 工作流模板选择 -->
      <div class="workflow-templates">
        <h4>📋 可用工作流模板</h4>
        <el-row :gutter="16">
          <el-col :span="8" v-for="workflow in workflows" :key="workflow.workflow_id">
            <el-card 
              class="workflow-card" 
              shadow="hover"
              @click="showWorkflowDetail(workflow)"
            >
              <div class="workflow-content">
                <div class="workflow-header">
                  <h3>{{ workflow.name }}</h3>
                  <el-tag size="small">{{ workflow.steps?.length || 0 }}步骤</el-tag>
                </div>
                <p class="workflow-desc">{{ workflow.description }}</p>
                <div class="workflow-actions">
                  <el-button 
                    type="primary" 
                    size="small"
                    @click.stop="executeWorkflowWithParams(workflow.workflow_id)"
                    :loading="executing"
                  >
                    <el-icon><VideoPlay /></el-icon>
                    执行工作流
                  </el-button>
                  <el-button 
                    size="small"
                    @click.stop="showWorkflowSteps(workflow)"
                  >
                    <el-icon><View /></el-icon>
                    查看步骤
                  </el-button>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </el-card>

    <!-- 执行状态监控 -->
    <el-row :gutter="16" class="status-cards">
      <el-col :span="6">
        <el-card class="status-card running">
          <el-statistic 
            title="运行中" 
            :value="runningExecutions?.length || 0"
            :value-style="{ color: '#409EFF' }"
          />
          <template #suffix>
            <el-icon class="status-icon"><Loading /></el-icon>
          </template>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="status-card paused">
          <el-statistic 
            title="已暂停" 
            :value="pausedExecutions?.length || 0"
            :value-style="{ color: '#E6A23C' }"
          />
          <template #suffix>
            <el-icon class="status-icon"><VideoPause /></el-icon>
          </template>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="status-card">
          <el-statistic 
            title="总执行数" 
            :value="executions?.length || 0"
          />
          <template #suffix>
            <el-icon class="status-icon"><Document /></el-icon>
          </template>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="status-card">
          <el-button type="primary" @click="loadWorkflows()" :loading="loading">
            <el-icon><Refresh /></el-icon>
            刷新状态
          </el-button>
        </el-card>
      </el-col>
    </el-row>

    <!-- 执行历史 -->
    <el-card class="execution-list-card">
      <template #header>
        <div class="card-header">
          <span>📊 执行历史</span>
        </div>
      </template>
      
      <el-table 
        :data="recentExecutions" 
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="execution_id" label="执行ID" width="280" show-overflow-tooltip />
        <el-table-column prop="workflow_name" label="工作流名称" width="200" />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="current_step_id" label="当前步骤" width="150" />
        <el-table-column prop="started_at" label="开始时间" width="180">
          <template #default="{ row }">
            {{ row.started_at ? formatDateTime(row.started_at) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250">
          <template #default="{ row }">
            <el-button 
              v-if="row.status === 'running'" 
              size="small" 
              type="warning"
              @click="pauseWorkflow(row.execution_id)"
            >
              <el-icon><VideoPause /></el-icon>
              暂停
            </el-button>
            <el-button 
              v-if="row.status === 'paused'" 
              size="small" 
              type="success"
              @click="resumeWorkflow(row.execution_id)"
            >
              <el-icon><VideoPlay /></el-icon>
              恢复
            </el-button>
            <el-button 
              v-if="['running', 'paused'].includes(row.status)" 
              size="small" 
              type="danger"
              @click="cancelWorkflow(row.execution_id)"
            >
              <el-icon><Close /></el-icon>
              取消
            </el-button>
            <el-button 
              size="small"
              @click="showExecutionDetail(row)"
            >
              <el-icon><View /></el-icon>
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 工作流详情对话框 -->
    <el-dialog 
      v-model="showDetailDialog" 
      title="工作流详情" 
      width="900px"
      destroy-on-close
    >
      <div v-if="selectedWorkflow" class="workflow-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="工作流ID">
            {{ selectedWorkflow.workflow_id }}
          </el-descriptions-item>
          <el-descriptions-item label="工作流名称">
            {{ selectedWorkflow.name }}
          </el-descriptions-item>
          <el-descriptions-item label="版本">
            {{ selectedWorkflow.version }}
          </el-descriptions-item>
          <el-descriptions-item label="步骤数量">
            {{ selectedWorkflow.steps?.length || 0 }}
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">
            {{ selectedWorkflow.description }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>

    <!-- 工作流步骤对话框 -->
    <el-dialog 
      v-model="showStepsDialog" 
      title="工作流步骤" 
      width="1000px"
      destroy-on-close
    >
      <div v-if="selectedWorkflow" class="workflow-steps">
        <el-timeline>
          <el-timeline-item 
            v-for="(step, index) in selectedWorkflow.steps" 
            :key="step.step_id"
            :type="getStepTimelineType(step, index)"
          >
            <div class="step-content">
              <div class="step-header">
                <h4>{{ step.name }}</h4>
                <el-tag :type="getStepTypeColor(step.step_type)" size="small">
                  {{ getStepTypeText(step.step_type) }}
                </el-tag>
              </div>
              <p class="step-desc">{{ step.description }}</p>
              
              <!-- 步骤配置详情 -->
              <div class="step-config" v-if="hasStepConfig(step)">
                <el-descriptions size="small" :column="1" border>
                  <el-descriptions-item 
                    v-if="step.serial_command" 
                    label="串口指令"
                  >
                    <code>{{ step.serial_command }}</code>
                  </el-descriptions-item>
                  <el-descriptions-item 
                    v-if="step.expected_response" 
                    label="期望回复"
                  >
                    <code>{{ step.expected_response }}</code>
                  </el-descriptions-item>
                  <el-descriptions-item 
                    v-if="step.confirm_message" 
                    label="确认消息"
                  >
                    {{ step.confirm_message }}
                  </el-descriptions-item>
                  <el-descriptions-item 
                    v-if="step.variable_name" 
                    label="变量操作"
                  >
                    {{ step.variable_name }} = {{ step.variable_value }}
                  </el-descriptions-item>
                  <el-descriptions-item 
                    v-if="step.delay_seconds" 
                    label="延时"
                  >
                    {{ step.delay_seconds }}秒
                  </el-descriptions-item>
                </el-descriptions>
              </div>
            </div>
          </el-timeline-item>
        </el-timeline>
      </div>
    </el-dialog>

    <!-- 执行详情对话框 -->
    <el-dialog 
      v-model="showExecutionDialog" 
      title="执行详情" 
      width="1000px"
      destroy-on-close
    >
      <div v-if="selectedExecution" class="execution-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="执行ID">
            {{ selectedExecution.execution_id }}
          </el-descriptions-item>
          <el-descriptions-item label="工作流名称">
            {{ selectedExecution.workflow_name }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(selectedExecution.status)">
              {{ getStatusText(selectedExecution.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="当前步骤">
            {{ selectedExecution.current_step_id || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="开始时间">
            {{ selectedExecution.started_at ? formatDateTime(selectedExecution.started_at) : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="完成时间">
            {{ selectedExecution.completed_at ? formatDateTime(selectedExecution.completed_at) : '-' }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 变量状态 -->
        <div class="variables-section" v-if="selectedExecution.variables">
          <h4>🔧 运行时变量</h4>
          <el-table :data="getVariablesList(selectedExecution.variables)" size="small">
            <el-table-column prop="name" label="变量名" width="200" />
            <el-table-column prop="value" label="当前值" />
          </el-table>
        </div>

        <!-- 步骤执行结果 -->
        <div class="step-results-section" v-if="selectedExecution.step_results">
          <h4>📝 步骤执行结果</h4>
          <el-collapse>
            <el-collapse-item 
              v-for="(result, stepId) in selectedExecution.step_results" 
              :key="stepId"
              :title="`步骤: ${stepId}`"
            >
              <pre>{{ JSON.stringify(result, null, 2) }}</pre>
            </el-collapse-item>
          </el-collapse>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import {
  ElCard, ElButton, ElRow, ElCol, ElTable, ElTableColumn,
  ElTag, ElDialog, ElDescriptions, ElDescriptionsItem,
  ElStatistic, ElIcon, ElTimeline, ElTimelineItem,
  ElCollapse, ElCollapseItem, ElMessageBox
} from 'element-plus'
import {
  VideoPlay, VideoPause, Close, View, Loading, Document, 
  Refresh, Connection, Disconnect
} from '@element-plus/icons-vue'
import { useWorkflowStore } from '@/stores/workflow'
import type { WorkflowDefinition, WorkflowExecution } from '@/api/workflow'

const workflowStore = useWorkflowStore()

// 响应式数据
const showDetailDialog = ref(false)
const showStepsDialog = ref(false)
const showExecutionDialog = ref(false)
const selectedWorkflow = ref<WorkflowDefinition | null>(null)
const selectedExecution = ref<WorkflowExecution | null>(null)

// 从store中解构
const {
  workflows,
  executions,
  currentExecution,
  loading,
  executing,
  wsConnected,
  runningExecutions,
  pausedExecutions,
  recentExecutions,
  loadWorkflows,
  executeWorkflow,
  pauseWorkflow,
  resumeWorkflow,
  cancelWorkflow,
  initWebSocket,
  disconnectWebSocket,
  getStatusText,
  getStatusType,
  getStepStatusText
} = workflowStore

/**
 * 显示工作流详情
 */
const showWorkflowDetail = (workflow: WorkflowDefinition) => {
  selectedWorkflow.value = workflow
  showDetailDialog.value = true
}

/**
 * 显示工作流步骤
 */
const showWorkflowSteps = (workflow: WorkflowDefinition) => {
  selectedWorkflow.value = workflow
  showStepsDialog.value = true
}

/**
 * 显示执行详情
 */
const showExecutionDetail = (execution: WorkflowExecution) => {
  selectedExecution.value = execution
  showExecutionDialog.value = true
}

/**
 * 执行工作流（带参数输入）
 */
const executeWorkflowWithParams = async (workflowId: string) => {
  const workflow = workflows.value?.find(wf => wf.workflow_id === workflowId)
  if (!workflow) return

  try {
    // 如果工作流有预定义变量，显示输入对话框
    const hasVariables = workflow.variables && Object.keys(workflow.variables).length > 0
    
    if (hasVariables) {
      const { value: inputData } = await ElMessageBox.prompt(
        `请输入 "${workflow.name}" 的初始变量 (JSON格式)`,
        '参数输入',
        {
          confirmButtonText: '开始执行',
          cancelButtonText: '取消',
          inputPlaceholder: JSON.stringify(workflow.variables, null, 2),
          inputType: 'textarea',
          inputValidator: (value) => {
            try {
              JSON.parse(value || '{}')
              return true
            } catch {
              return '请输入有效的JSON格式'
            }
          }
        }
      )
      
      const inputVariables = JSON.parse(inputData || '{}')
      await executeWorkflow(workflowId, inputVariables, 'WEB_USER')
    } else {
      await executeWorkflow(workflowId, {}, 'WEB_USER')
    }
  } catch {
    // 用户取消
  }
}

/**
 * 获取步骤类型文本
 */
const getStepTypeText = (stepType: string): string => {
  const typeMap: Record<string, string> = {
    serial_send: '串口发送',
    wait_response: '等待回复',
    user_confirm: '用户确认',
    set_variable: '设置变量',
    condition: '条件判断',
    delay: '延时等待',
    log: '记录日志'
  }
  return typeMap[stepType] || stepType
}

/**
 * 获取步骤类型颜色
 */
const getStepTypeColor = (stepType: string): string => {
  const colorMap: Record<string, string> = {
    serial_send: 'primary',
    wait_response: 'info',
    user_confirm: 'warning',
    set_variable: 'success',
    condition: 'danger',
    delay: 'info',
    log: 'primary'
  }
  return colorMap[stepType] || 'primary'
}

/**
 * 获取时间线类型
 */
const getStepTimelineType = (step: any, index: number): string => {
  if (index === 0) return 'primary'
  if (step.step_type === 'user_confirm') return 'warning'
  if (step.step_type === 'serial_send') return 'success'
  return 'info'
}

/**
 * 检查步骤是否有配置
 */
const hasStepConfig = (step: any): boolean => {
  return !!(step.serial_command || step.expected_response || step.confirm_message || 
           step.variable_name || step.delay_seconds)
}

/**
 * 获取变量列表
 */
const getVariablesList = (variables: Record<string, any>) => {
  return Object.entries(variables).map(([name, value]) => ({
    name,
    value: typeof value === 'object' ? JSON.stringify(value) : String(value)
  }))
}

/**
 * 格式化日期时间
 */
const formatDateTime = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

// 生命周期
onMounted(async () => {
  await loadWorkflows()
  initWebSocket()
})

onUnmounted(() => {
  disconnectWebSocket()
})
</script>

<style scoped>
.workflow-control {
  padding: 20px;
}

.header-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ws-status {
  display: flex;
  align-items: center;
  gap: 4px;
}

.workflow-templates h4 {
  margin-bottom: 16px;
  color: #303133;
}

.workflow-card {
  cursor: pointer;
  transition: all 0.3s;
  height: 180px;
}

.workflow-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.workflow-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.workflow-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.workflow-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.workflow-desc {
  flex: 1;
  margin: 8px 0;
  color: #606266;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.workflow-actions {
  display: flex;
  gap: 8px;
  margin-top: auto;
}

.status-cards {
  margin-bottom: 20px;
}

.status-card {
  text-align: center;
}

.status-card.running {
  border-left: 4px solid #409eff;
}

.status-card.paused {
  border-left: 4px solid #e6a23c;
}

.status-icon {
  font-size: 20px;
  margin-left: 8px;
}

.execution-list-card {
  margin-bottom: 20px;
}

.workflow-detail,
.execution-detail {
  padding: 16px 0;
}

.workflow-steps {
  padding: 16px 0;
}

.step-content {
  padding: 12px;
  background: #f9f9f9;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.step-header h4 {
  margin: 0;
  font-size: 14px;
  color: #303133;
}

.step-desc {
  margin: 8px 0;
  color: #606266;
  font-size: 13px;
}

.step-config {
  margin-top: 12px;
}

.variables-section,
.step-results-section {
  margin-top: 20px;
}

.variables-section h4,
.step-results-section h4 {
  margin-bottom: 12px;
  color: #303133;
}

pre {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  font-size: 12px;
  overflow-x: auto;
}

code {
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
}
</style>