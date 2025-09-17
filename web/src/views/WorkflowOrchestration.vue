<template>
  <div class="workflow-orchestration">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1>工作流编排</h1>
      <p>基于Command对象的工作流模板系统 - 选择模板，输入参数，一键执行</p>
    </div>

    <!-- 工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          创建模板
        </el-button>
        <el-button @click="loadTemplates">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button @click="loadStats">
          <el-icon><DataAnalysis /></el-icon>
          统计
        </el-button>
      </div>
      <div class="toolbar-right">
        <el-select v-model="categoryFilter" placeholder="选择分类" clearable style="width: 150px; margin-right: 10px;">
          <el-option label="全部" value="" />
          <el-option label="测试" value="test" />
          <el-option label="生产" value="production" />
          <el-option label="调试" value="debug" />
        </el-select>
        <el-input
          v-model="searchQuery"
          placeholder="搜索模板..."
          style="width: 300px"
          clearable
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
    </div>

    <!-- 统计信息 -->
    <div v-if="stats.total_templates > 0" class="stats-cards">
      <div class="stat-card">
        <div class="stat-value">{{ stats.total_templates }}</div>
        <div class="stat-label">总模板数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.active_templates }}</div>
        <div class="stat-label">活跃模板</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.total_executions }}</div>
        <div class="stat-label">总执行数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.success_rate.toFixed(1) }}%</div>
        <div class="stat-label">成功率</div>
      </div>
    </div>

    <!-- 工作流模板列表 -->
    <div class="template-list">
      <div v-if="loading" class="loading">
        <el-icon class="is-loading"><Loading /></el-icon>
        加载中...
      </div>
      
      <div v-else-if="filteredTemplates.length === 0" class="empty">
        <el-empty description="暂无工作流模板">
          <el-button type="primary" @click="showCreateDialog = true">
            创建模板
          </el-button>
        </el-empty>
      </div>
      
      <div v-else class="template-grid">
        <div
          v-for="template in filteredTemplates"
          :key="template.id"
          class="template-card"
        >
          <div class="template-header">
            <h3>{{ template.name }}</h3>
            <div class="template-badges">
              <el-tag :type="getStatusType(template.status)" size="small">
                {{ getStatusText(template.status) }}
              </el-tag>
              <el-tag size="small" type="info">{{ template.category }}</el-tag>
            </div>
          </div>
          
          <div class="template-content">
            <p class="template-description">{{ template.description || '暂无描述' }}</p>
            
            <div class="template-steps">
              <div class="steps-header">
                <span>工作流步骤 ({{ template.steps.length }})</span>
              </div>
              <div class="steps-list">
                <div
                  v-for="(step, index) in template.steps.slice(0, 3)"
                  :key="step.step_id"
                  class="step-item"
                >
                  <div class="step-number">{{ index + 1 }}</div>
                  <div class="step-info">
                    <div class="step-name">{{ step.step_name }}</div>
                    <div class="step-command">{{ step.command }}</div>
                  </div>
                </div>
                <div v-if="template.steps.length > 3" class="step-item more">
                  <div class="step-number">...</div>
                  <div class="step-info">
                    <div class="step-name">还有 {{ template.steps.length - 3 }} 个步骤</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div class="template-footer">
            <div class="template-meta">
              <span>版本: {{ template.version }}</span>
              <span>创建时间: {{ formatTime(template.created_at) }}</span>
            </div>
            
            <div class="template-actions">
              <el-button size="small" @click="editTemplate(template)">
                <el-icon><Edit /></el-icon>
                编辑
              </el-button>
              <el-button size="small" type="primary" @click="executeTemplate(template)">
                <el-icon><Play /></el-icon>
                执行
              </el-button>
              <el-button size="small" @click="viewExecutions(template)">
                <el-icon><View /></el-icon>
                历史
              </el-button>
              <el-button size="small" type="danger" @click="deleteTemplate(template)">
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建模板对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      title="创建工作流模板"
      width="800px"
      :before-close="handleCreateClose"
    >
      <el-form :model="createForm" :rules="createRules" ref="createFormRef" label-width="100px">
        <el-form-item label="模板名称" prop="name">
          <el-input v-model="createForm.name" placeholder="请输入模板名称" />
        </el-form-item>
        <el-form-item label="模板描述" prop="description">
          <el-textarea v-model="createForm.description" placeholder="请输入模板描述" />
        </el-form-item>
        <el-form-item label="分类" prop="category">
          <el-select v-model="createForm.category" placeholder="请选择分类">
            <el-option label="测试" value="test" />
            <el-option label="生产" value="production" />
            <el-option label="调试" value="debug" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="选择命令" prop="command_ids">
          <div class="command-selection">
            <div v-if="commandsLoading" class="loading">
              <el-icon class="is-loading"><Loading /></el-icon>
              加载命令中...
            </div>
            <div v-else class="command-list">
              <el-checkbox-group v-model="createForm.command_ids">
                <div
                  v-for="command in availableCommands"
                  :key="command.id"
                  class="command-item"
                >
                  <el-checkbox :label="command.id">
                    <div class="command-info">
                      <div class="command-name">{{ command.name }}</div>
                      <div class="command-desc">{{ command.description || command.command }}</div>
                    </div>
                  </el-checkbox>
                </div>
              </el-checkbox-group>
            </div>
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="creating">
          创建
        </el-button>
      </template>
    </el-dialog>

    <!-- 执行工作流对话框 -->
    <el-dialog
      v-model="showExecuteDialog"
      title="执行工作流"
      width="600px"
      :before-close="handleExecuteClose"
    >
      <div v-if="selectedTemplate" class="execute-info">
        <h4>{{ selectedTemplate.name }}</h4>
        <p>{{ selectedTemplate.description }}</p>
        <div class="steps-preview">
          <div
            v-for="(step, index) in selectedTemplate.steps"
            :key="step.step_id"
            class="step-preview"
          >
            <div class="step-number">{{ index + 1 }}</div>
            <div class="step-name">{{ step.step_name }}</div>
          </div>
        </div>
      </div>
      
      <el-form :model="executeForm" :rules="executeRules" ref="executeFormRef" label-width="100px">
        <el-form-item label="MAC地址" prop="macAddress">
          <el-input v-model="executeForm.macAddress" placeholder="请输入MAC地址" />
        </el-form-item>
        <el-form-item label="序列号" prop="serialNumber">
          <el-input v-model="executeForm.serialNumber" placeholder="请输入序列号" />
        </el-form-item>
        <el-form-item label="操作员" prop="operator">
          <el-input v-model="executeForm.operator" placeholder="请输入操作员" />
        </el-form-item>
        <el-form-item label="工位" prop="workstation">
          <el-input v-model="executeForm.workstation" placeholder="请输入工位" />
        </el-form-item>
        <el-form-item label="设备ID" prop="deviceId">
          <el-input v-model="executeForm.deviceId" placeholder="请输入设备ID" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showExecuteDialog = false">取消</el-button>
        <el-button type="primary" @click="handleExecute" :loading="executing">
          执行
        </el-button>
      </template>
    </el-dialog>

    <!-- 执行历史对话框 -->
    <el-dialog
      v-model="showHistoryDialog"
      title="执行历史"
      width="1000px"
      :before-close="handleHistoryClose"
    >
      <div v-if="selectedTemplate" class="history-header">
        <h4>{{ selectedTemplate.name }} - 执行历史</h4>
      </div>
      
      <div v-if="executionsLoading" class="loading">
        <el-icon class="is-loading"><Loading /></el-icon>
        加载执行历史中...
      </div>
      
      <div v-else-if="executions.length === 0" class="empty">
        <el-empty description="暂无执行记录" />
      </div>
      
      <div v-else class="execution-list">
        <div
          v-for="execution in executions"
          :key="execution.id"
          class="execution-item"
        >
          <div class="execution-header">
            <div class="execution-info">
              <span class="execution-id">#{{ execution.id }}</span>
              <el-tag :type="getExecutionStatusType(execution.status)" size="small">
                {{ getExecutionStatusText(execution.status) }}
              </el-tag>
            </div>
            <div class="execution-meta">
              <span>{{ execution.operator }} - {{ execution.workstation }}</span>
              <span>{{ formatTime(execution.created_at) }}</span>
            </div>
          </div>
          
          <div class="execution-details">
            <div class="execution-params">
              <span><strong>MAC:</strong> {{ execution.mac_address }}</span>
              <span><strong>SN:</strong> {{ execution.serial_number }}</span>
              <span><strong>设备ID:</strong> {{ execution.device_id }}</span>
            </div>
            
            <div v-if="execution.status === 'running'" class="execution-progress">
              <el-progress 
                :percentage="execution.progress" 
                :format="() => `${execution.current_step}/${execution.total_steps}`"
              />
            </div>
            
            <div v-if="execution.step_results.length > 0" class="execution-steps">
              <div
                v-for="(result, index) in execution.step_results"
                :key="index"
                class="step-result"
              >
                <div class="step-result-header">
                  <span class="step-name">{{ result.step_name }}</span>
                  <el-tag :type="result.status === 'success' ? 'success' : 'danger'" size="small">
                    {{ result.status === 'success' ? '成功' : '失败' }}
                  </el-tag>
                </div>
                <div v-if="result.response" class="step-response">
                  {{ result.response }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="showHistoryDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, DataAnalysis, Search, Loading, Edit, Play, View, Delete } from '@element-plus/icons-vue'
import { useWorkflowTemplateStore } from '@/stores/workflow-template'
import { useCommandStore } from '@/stores/command'
import type { WorkflowTemplate, WorkflowExecution } from '@/types/workflow-template'
import type { SavedCommand } from '@/types/command'

// 使用 stores
const workflowTemplateStore = useWorkflowTemplateStore()
const commandStore = useCommandStore()

// 响应式数据
const loading = ref(false)
const commandsLoading = ref(false)
const executionsLoading = ref(false)
const creating = ref(false)
const executing = ref(false)

const searchQuery = ref('')
const categoryFilter = ref('')

const showCreateDialog = ref(false)
const showExecuteDialog = ref(false)
const showHistoryDialog = ref(false)

const selectedTemplate = ref<WorkflowTemplate | null>(null)
const availableCommands = ref<SavedCommand[]>([])
const executions = ref<WorkflowExecution[]>([])

// 表单数据
const createForm = ref({
  name: '',
  description: '',
  category: 'test',
  command_ids: [] as string[]
})

const executeForm = ref({
  macAddress: '',
  serialNumber: '',
  operator: '',
  workstation: '',
  deviceId: ''
})

// 表单验证规则
const createRules = {
  name: [
    { required: true, message: '请输入模板名称', trigger: 'blur' }
  ],
  category: [
    { required: true, message: '请选择分类', trigger: 'change' }
  ],
  command_ids: [
    { required: true, message: '请选择至少一个命令', trigger: 'change' }
  ]
}

const executeRules = {
  macAddress: [
    { required: true, message: '请输入MAC地址', trigger: 'blur' }
  ],
  serialNumber: [
    { required: true, message: '请输入序列号', trigger: 'blur' }
  ],
  operator: [
    { required: true, message: '请输入操作员', trigger: 'blur' }
  ],
  workstation: [
    { required: true, message: '请输入工位', trigger: 'blur' }
  ],
  deviceId: [
    { required: true, message: '请输入设备ID', trigger: 'blur' }
  ]
}

// 计算属性
const templates = computed(() => workflowTemplateStore.templates)
const stats = computed(() => workflowTemplateStore.stats)

const filteredTemplates = computed(() => {
  let filtered = templates.value

  // 按分类筛选
  if (categoryFilter.value) {
    filtered = filtered.filter(t => t.category === categoryFilter.value)
  }

  // 按搜索关键词筛选
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(t => 
      t.name.toLowerCase().includes(query) ||
      t.description.toLowerCase().includes(query) ||
      t.category.toLowerCase().includes(query)
    )
  }

  return filtered
})

// 方法
const loadTemplates = async () => {
  try {
    loading.value = true
    await workflowTemplateStore.loadTemplates()
  } catch (error) {
    ElMessage.error('加载模板失败')
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  try {
    await workflowTemplateStore.loadStats()
  } catch (error) {
    ElMessage.error('加载统计信息失败')
  }
}

const loadCommands = async () => {
  try {
    commandsLoading.value = true
    await commandStore.loadCommands()
    availableCommands.value = commandStore.commands
  } catch (error) {
    ElMessage.error('加载命令失败')
  } finally {
    commandsLoading.value = false
  }
}

const loadExecutions = async (templateId: string) => {
  try {
    executionsLoading.value = true
    await workflowTemplateStore.loadExecutions({ template_id: templateId })
    executions.value = workflowTemplateStore.executions
  } catch (error) {
    ElMessage.error('加载执行历史失败')
  } finally {
    executionsLoading.value = false
  }
}

const getStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    'active': 'success',
    'inactive': 'info',
    'draft': 'warning'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'active': '活跃',
    'inactive': '非活跃',
    'draft': '草稿'
  }
  return statusMap[status] || status
}

const getExecutionStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    'completed': 'success',
    'running': 'warning',
    'failed': 'danger',
    'cancelled': 'info',
    'pending': 'info'
  }
  return statusMap[status] || 'info'
}

const getExecutionStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'completed': '已完成',
    'running': '执行中',
    'failed': '失败',
    'cancelled': '已取消',
    'pending': '等待中'
  }
  return statusMap[status] || status
}

const formatTime = (timestamp: number) => {
  return new Date(timestamp).toLocaleString()
}

const editTemplate = (template: WorkflowTemplate) => {
  ElMessage.info('编辑功能开发中...')
}

const executeTemplate = (template: WorkflowTemplate) => {
  selectedTemplate.value = template
  executeForm.value = {
    macAddress: '',
    serialNumber: '',
    operator: '',
    workstation: '',
    deviceId: ''
  }
  showExecuteDialog.value = true
}

const viewExecutions = async (template: WorkflowTemplate) => {
  selectedTemplate.value = template
  await loadExecutions(template.id)
  showHistoryDialog.value = true
}

const deleteTemplate = async (template: WorkflowTemplate) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除模板 "${template.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await workflowTemplateStore.deleteTemplate(template.id)
    ElMessage.success('删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleCreate = async () => {
  try {
    creating.value = true
    await workflowTemplateStore.createTemplate(createForm.value)
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    createForm.value = {
      name: '',
      description: '',
      category: 'test',
      command_ids: []
    }
  } catch (error) {
    ElMessage.error('创建失败')
  } finally {
    creating.value = false
  }
}

const handleExecute = async () => {
  try {
    executing.value = true
    const execution = await workflowTemplateStore.executeTemplate({
      template_id: selectedTemplate.value!.id,
      mac_address: executeForm.value.macAddress,
      serial_number: executeForm.value.serialNumber,
      operator: executeForm.value.operator,
      workstation: executeForm.value.workstation,
      device_id: executeForm.value.deviceId,
      input_data: {}
    })
    
    ElMessage.success('工作流已开始执行')
    showExecuteDialog.value = false
    
    // 可以在这里跳转到执行详情页面或显示执行状态
    console.log('执行实例:', execution)
  } catch (error) {
    ElMessage.error('执行失败')
  } finally {
    executing.value = false
  }
}

const handleCreateClose = () => {
  createForm.value = {
    name: '',
    description: '',
    category: 'test',
    command_ids: []
  }
  showCreateDialog.value = false
}

const handleExecuteClose = () => {
  selectedTemplate.value = null
  showExecuteDialog.value = false
}

const handleHistoryClose = () => {
  selectedTemplate.value = null
  executions.value = []
  showHistoryDialog.value = false
}

// 生命周期
onMounted(async () => {
  await Promise.all([
    loadTemplates(),
    loadStats(),
    loadCommands()
  ])
})
</script>

<style scoped>
.workflow-orchestration {
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.page-header p {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.toolbar-left {
  display: flex;
  gap: 12px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  padding: 20px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.stat-value {
  font-size: 32px;
  font-weight: 600;
  color: #409eff;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #606266;
}

.template-list {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  min-height: 400px;
}

.loading, .empty {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 400px;
  color: #909399;
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
  padding: 20px;
}

.template-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 20px;
  transition: all 0.3s;
  background: #fff;
}

.template-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.template-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.template-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  flex: 1;
}

.template-badges {
  display: flex;
  gap: 8px;
}

.template-content {
  margin-bottom: 16px;
}

.template-description {
  margin: 0 0 16px 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
}

.template-steps {
  border-top: 1px solid #f0f0f0;
  padding-top: 16px;
}

.steps-header {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
}

.steps-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  background: #f8f9fa;
  border-radius: 4px;
}

.step-item.more {
  background: #e9ecef;
  color: #6c757d;
}

.step-number {
  width: 24px;
  height: 24px;
  background: #409eff;
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.step-info {
  flex: 1;
  min-width: 0;
}

.step-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 2px;
}

.step-command {
  font-size: 12px;
  color: #909399;
  font-family: 'Courier New', monospace;
  word-break: break-all;
}

.template-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.template-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: #909399;
}

.template-actions {
  display: flex;
  gap: 8px;
}

.command-selection {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 12px;
}

.command-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.command-item {
  padding: 8px;
  border: 1px solid #f0f0f0;
  border-radius: 4px;
  transition: all 0.3s;
}

.command-item:hover {
  background: #f8f9fa;
}

.command-info {
  margin-left: 8px;
}

.command-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.command-desc {
  font-size: 12px;
  color: #909399;
  font-family: 'Courier New', monospace;
}

.execute-info {
  margin-bottom: 20px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 4px;
}

.execute-info h4 {
  margin: 0 0 8px 0;
  color: #303133;
}

.execute-info p {
  margin: 0 0 16px 0;
  color: #606266;
  font-size: 14px;
}

.steps-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.step-preview {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: #e1f3d8;
  border-radius: 16px;
  font-size: 12px;
}

.step-preview .step-number {
  width: 20px;
  height: 20px;
  background: #67c23a;
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 600;
}

.history-header {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e4e7ed;
}

.history-header h4 {
  margin: 0;
  color: #303133;
}

.execution-list {
  max-height: 500px;
  overflow-y: auto;
}

.execution-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  background: #fff;
}

.execution-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.execution-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.execution-id {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: #909399;
}

.execution-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  font-size: 12px;
  color: #909399;
}

.execution-details {
  margin-top: 12px;
}

.execution-params {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
  font-size: 12px;
  color: #606266;
}

.execution-progress {
  margin-bottom: 12px;
}

.execution-steps {
  margin-top: 12px;
}

.step-result {
  padding: 8px;
  background: #f8f9fa;
  border-radius: 4px;
  margin-bottom: 8px;
}

.step-result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.step-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.step-response {
  font-size: 12px;
  color: #606266;
  font-family: 'Courier New', monospace;
  background: #fff;
  padding: 4px 8px;
  border-radius: 2px;
  margin-top: 4px;
}
</style>