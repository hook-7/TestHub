<template>
  <div class="workflow-list">
    <div class="page-header">
      <h2>工作流管理</h2>
      <div class="header-actions">
        <el-button type="primary" @click="$router.push('/workflow/create')" :icon="Plus">
          新建工作流
        </el-button>
        <el-button @click="loadWorkflows" :loading="workflowStore.isLoading" :icon="Refresh">
          刷新
        </el-button>
      </div>
    </div>

    <div class="content-container">
      <!-- 工作流列表 -->
      <el-card class="workflows-card">
        <template #header>
          <span>工作流定义 ({{ workflowStore.workflows.length }})</span>
        </template>

        <div v-if="workflowStore.workflows.length === 0" class="empty-state">
          <el-empty description="暂无工作流，点击右上角按钮创建新工作流" />
        </div>

        <div v-else class="workflows-grid">
          <div 
            v-for="workflow in workflowStore.workflows" 
            :key="workflow.id"
            class="workflow-card"
          >
            <div class="card-header">
              <h4>{{ workflow.name }}</h4>
              <div class="card-actions">
                <el-button 
                  size="small" 
                  @click="executeWorkflow(workflow.id!)"
                  :icon="VideoPlay"
                  type="success"
                >
                  执行
                </el-button>
                <el-button 
                  size="small" 
                  @click="editWorkflow(workflow.id!)"
                  :icon="Edit"
                >
                  编辑
                </el-button>
                <el-button 
                  size="small" 
                  type="danger"
                  @click="deleteWorkflow(workflow.id!)"
                  :icon="Delete"
                >
                  删除
                </el-button>
              </div>
            </div>

            <div class="card-content">
              <p class="description">{{ workflow.description || '无描述' }}</p>
              
              <div class="workflow-stats">
                <el-tag size="small">{{ workflow.steps.length }} 个步骤</el-tag>
                <el-tag size="small" type="info">
                  {{ Object.keys(workflow.variables).length }} 个变量
                </el-tag>
                <el-tag size="small" type="warning">v{{ workflow.version }}</el-tag>
              </div>

              <div class="workflow-meta">
                <span class="meta-item">
                  创建: {{ formatDate(workflow.created_at) }}
                </span>
                <span class="meta-item" v-if="workflow.updated_at !== workflow.created_at">
                  更新: {{ formatDate(workflow.updated_at) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 执行历史 -->
      <el-card class="executions-card">
        <template #header>
          <div class="executions-header">
            <span>执行历史 ({{ workflowStore.executions.length }})</span>
            <div class="execution-filters">
              <el-select 
                v-model="statusFilter" 
                placeholder="按状态筛选"
                clearable
                size="small"
                style="width: 120px"
                @change="filterExecutions"
              >
                <el-option label="运行中" value="running" />
                <el-option label="暂停" value="paused" />
                <el-option label="已完成" value="completed" />
                <el-option label="失败" value="failed" />
                <el-option label="已取消" value="cancelled" />
              </el-select>
            </div>
          </div>
        </template>

        <div v-if="filteredExecutions.length === 0" class="empty-state">
          <el-empty description="暂无执行记录" />
        </div>

        <el-table v-else :data="filteredExecutions" stripe>
          <el-table-column prop="id" label="执行ID" width="200" show-overflow-tooltip />
          <el-table-column label="工作流" width="150">
            <template #default="{ row }">
              {{ getWorkflowName(row.workflow_id) }}
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusTagType(row.status)">
                {{ getStatusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="current_step" label="当前步骤" width="150" show-overflow-tooltip />
          <el-table-column prop="started_at" label="开始时间" width="160">
            <template #default="{ row }">
              {{ formatDate(row.started_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="completed_at" label="完成时间" width="160">
            <template #default="{ row }">
              {{ row.completed_at ? formatDate(row.completed_at) : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150">
            <template #default="{ row }">
              <el-button 
                size="small" 
                @click="viewExecution(row.id)"
                :icon="View"
              >
                查看
              </el-button>
              <el-button 
                v-if="row.status === 'running' || row.status === 'paused'"
                size="small" 
                type="danger"
                @click="cancelExecution(row.id)"
                :icon="Close"
              >
                取消
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 执行对话框 -->
    <el-dialog 
      v-model="executeDialogVisible" 
      title="执行工作流" 
      width="500px"
    >
      <el-form :model="executeForm" label-width="100px">
        <el-form-item label="会话ID">
          <el-input v-model="executeForm.session_id" placeholder="关联的会话ID（可选）" />
        </el-form-item>
        
        <el-form-item label="执行变量">
          <div class="variables-editor">
            <div 
              v-for="(value, key) in executeForm.variables" 
              :key="key"
              class="variable-item"
            >
              <el-input v-model="executeVariableKeys[key]" placeholder="变量名" style="width: 120px" />
              <span>=</span>
              <el-input v-model="executeForm.variables[key]" placeholder="变量值" />
              <el-button 
                type="danger" 
                size="small" 
                @click="removeExecuteVariable(key)"
                :icon="Delete"
              />
            </div>
            
            <el-button type="primary" size="small" @click="addExecuteVariable" :icon="Plus">
              添加变量
            </el-button>
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="executeDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmExecute" :loading="workflowStore.isLoading">
          开始执行
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Plus, Refresh, Edit, Delete, VideoPlay, View, Close 
} from '@element-plus/icons-vue'
import { useWorkflowStore } from '@/stores/workflow'

const router = useRouter()
const workflowStore = useWorkflowStore()

// 状态
const statusFilter = ref('')
const executeDialogVisible = ref(false)
const executingWorkflowId = ref('')

const executeForm = reactive({
  session_id: '',
  variables: {} as Record<string, any>
})

const executeVariableKeys = reactive<Record<string, string>>({})

// 计算属性
const filteredExecutions = computed(() => {
  if (!statusFilter.value) {
    return workflowStore.executions
  }
  return workflowStore.executions.filter(e => e.status === statusFilter.value)
})

// 方法
const loadWorkflows = async () => {
  await workflowStore.loadWorkflows()
  await workflowStore.loadExecutions()
}

const editWorkflow = (workflowId: string) => {
  router.push(`/workflow/edit/${workflowId}`)
}

const executeWorkflow = (workflowId: string) => {
  executingWorkflowId.value = workflowId
  executeForm.session_id = ''
  executeForm.variables = {}
  executeDialogVisible.value = true
}

const confirmExecute = async () => {
  try {
    await workflowStore.executeWorkflow(executingWorkflowId.value, executeForm)
    executeDialogVisible.value = false
    
    // 刷新执行列表
    await workflowStore.loadExecutions()
  } catch (error) {
    // 错误已在store中处理
  }
}

const deleteWorkflow = async (workflowId: string) => {
  try {
    await ElMessageBox.confirm(
      '删除后无法恢复，确定要删除这个工作流吗？', 
      '确认删除', 
      {
        type: 'warning'
      }
    )
    
    await workflowStore.deleteWorkflow(workflowId)
  } catch {
    // 用户取消
  }
}

const viewExecution = (executionId: string) => {
  router.push(`/workflow/execution/${executionId}`)
}

const cancelExecution = async (executionId: string) => {
  try {
    await ElMessageBox.confirm('确定要取消这个执行吗？', '确认取消', {
      type: 'warning'
    })
    
    await workflowStore.cancelExecution(executionId)
    await workflowStore.loadExecutions()
  } catch {
    // 用户取消
  }
}

const filterExecutions = () => {
  // 筛选逻辑已在computed中处理
}

const addExecuteVariable = () => {
  const key = `var_${Object.keys(executeForm.variables).length + 1}`
  executeForm.variables[key] = ''
  executeVariableKeys[key] = key
}

const removeExecuteVariable = (key: string) => {
  delete executeForm.variables[key]
  delete executeVariableKeys[key]
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

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

// 生命周期
onMounted(() => {
  loadWorkflows()
})
</script>

<style scoped>
.workflow-list {
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

.content-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow: hidden;
}

.workflows-card {
  flex-shrink: 0;
  max-height: 50%;
}

.executions-card {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.executions-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
}

.workflows-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 16px;
  max-height: 400px;
  overflow-y: auto;
}

.workflow-card {
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  padding: 16px;
  transition: all 0.2s;
}

.workflow-card:hover {
  border-color: var(--el-color-primary);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.card-header h4 {
  margin: 0;
  color: var(--el-text-color-primary);
}

.card-actions {
  display: flex;
  gap: 5px;
}

.card-content .description {
  color: var(--el-text-color-secondary);
  margin: 0 0 12px 0;
  font-size: 14px;
  line-height: 1.4;
}

.workflow-stats {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.workflow-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.meta-item {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

.variables-editor {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.variable-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

:deep(.el-card__body) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

:deep(.el-table) {
  flex: 1;
}
</style>