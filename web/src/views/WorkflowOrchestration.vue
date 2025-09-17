<template>
  <div class="workflow-orchestration-container">
    <div class="page-content">
      <!-- 顶部工具栏 -->
      <div class="toolbar">
        <div class="toolbar-left">
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon>
            创建工作流
          </el-button>
          <el-button @click="showTemplateDialog = true">
            <el-icon><Document /></el-icon>
            从模板创建
          </el-button>
          <el-button @click="loadWorkflows">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
        <div class="toolbar-right">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索工作流..."
            style="width: 200px"
            clearable
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
      </div>

      <!-- 工作流列表 -->
      <div class="workflow-list">
        <el-card v-for="workflow in filteredWorkflows" :key="workflow.id" class="workflow-card" shadow="hover">
          <template #header>
            <div class="workflow-header">
              <div class="workflow-info">
                <h3 class="workflow-name">{{ workflow.name }}</h3>
                <p class="workflow-description">{{ workflow.description || '暂无描述' }}</p>
              </div>
              <div class="workflow-actions">
                <el-tag :type="getStatusType(workflow.status)" size="small">
                  {{ getStatusText(workflow.status) }}
                </el-tag>
                <el-dropdown @command="handleWorkflowAction">
                  <el-button type="text" size="small">
                    <el-icon><MoreFilled /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item :command="{ action: 'edit', workflow }">
                        <el-icon><Edit /></el-icon>
                        编辑
                      </el-dropdown-item>
                      <el-dropdown-item :command="{ action: 'execute', workflow }">
                        <el-icon><VideoPlay /></el-icon>
                        执行
                      </el-dropdown-item>
                      <el-dropdown-item :command="{ action: 'duplicate', workflow }">
                        <el-icon><CopyDocument /></el-icon>
                        复制
                      </el-dropdown-item>
                      <el-dropdown-item :command="{ action: 'delete', workflow }" divided>
                        <el-icon><Delete /></el-icon>
                        删除
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>
          </template>
          
          <div class="workflow-content">
            <div class="workflow-stats">
              <div class="stat-item">
                <span class="stat-label">节点数:</span>
                <span class="stat-value">{{ workflow.nodes.length }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">连接数:</span>
                <span class="stat-value">{{ workflow.connections.length }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">版本:</span>
                <span class="stat-value">{{ workflow.version }}</span>
              </div>
            </div>
            
            <div class="workflow-nodes">
              <div class="nodes-preview">
                <div 
                  v-for="node in workflow.nodes.slice(0, 5)" 
                  :key="node.id"
                  class="node-preview"
                  :class="node.type"
                >
                  <el-icon>
                    <component :is="getNodeIcon(node.type)" />
                  </el-icon>
                  <span>{{ node.name }}</span>
                </div>
                <div v-if="workflow.nodes.length > 5" class="more-nodes">
                  +{{ workflow.nodes.length - 5 }} 更多
                </div>
              </div>
            </div>
            
            <div class="workflow-footer">
              <div class="workflow-meta">
                <span class="created-time">
                  创建于 {{ formatTime(workflow.createdAt) }}
                </span>
                <span class="updated-time">
                  更新于 {{ formatTime(workflow.updatedAt) }}
                </span>
              </div>
              <div class="workflow-buttons">
                <el-button size="small" @click="editWorkflow(workflow)">
                  <el-icon><Edit /></el-icon>
                  编辑
                </el-button>
                <el-button size="small" type="primary" @click="executeWorkflow(workflow)">
                  <el-icon><VideoPlay /></el-icon>
                  执行
                </el-button>
              </div>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 空状态 -->
      <div v-if="workflows.length === 0 && !isLoading" class="empty-state">
        <div class="empty-icon">
          <el-icon><Operation /></el-icon>
        </div>
        <h4 class="empty-title">暂无工作流</h4>
        <p class="empty-description">创建您第一个工作流，开始自动化测试流程设计</p>
        <div class="empty-actions">
          <el-button type="primary" size="large" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon>
            创建工作流
          </el-button>
          <el-button size="large" @click="showTemplateDialog = true">
            <el-icon><Document /></el-icon>
            从模板创建
          </el-button>
        </div>
      </div>

      <!-- 加载状态 -->
      <div v-if="isLoading" class="loading-state">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>加载中...</span>
      </div>
    </div>

    <!-- 创建工作流对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      title="创建工作流"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="createForm" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="createForm.name" placeholder="请输入工作流名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="createForm.description"
            type="textarea"
            placeholder="请输入工作流描述"
            :rows="3"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreateWorkflow" :loading="isCreating">
          创建
        </el-button>
      </template>
    </el-dialog>

    <!-- 执行工作流对话框 -->
    <el-dialog
      v-model="showExecuteDialog"
      title="执行工作流"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="executeForm" label-width="100px">
        <el-form-item label="MAC地址" required>
          <el-input v-model="executeForm.macAddress" placeholder="请输入MAC地址" />
        </el-form-item>
        <el-form-item label="SN序列号">
          <el-input v-model="executeForm.serialNumber" placeholder="请输入SN序列号" />
        </el-form-item>
        <el-form-item label="操作员">
          <el-input v-model="executeForm.operator" placeholder="请输入操作员" />
        </el-form-item>
        <el-form-item label="工位">
          <el-input v-model="executeForm.workstation" placeholder="请输入工位" />
        </el-form-item>
        <el-form-item label="设备ID">
          <el-input v-model="executeForm.deviceId" placeholder="请输入设备ID" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showExecuteDialog = false">取消</el-button>
        <el-button type="primary" @click="handleExecuteWorkflow" :loading="isExecuting">
          开始执行
        </el-button>
      </template>
    </el-dialog>

    <!-- 模板选择对话框 -->
    <el-dialog
      v-model="showTemplateDialog"
      title="从模板创建"
      width="800px"
      :close-on-click-modal="false"
    >
      <div class="template-list">
        <el-card v-for="template in templates" :key="template.id" class="template-card" shadow="hover">
          <div class="template-content">
            <div class="template-info">
              <h4 class="template-name">{{ template.name }}</h4>
              <p class="template-description">{{ template.description || '暂无描述' }}</p>
              <div class="template-meta">
                <el-tag size="small">{{ template.category }}</el-tag>
                <span class="template-stats">
                  <el-icon><Download /></el-icon>
                  {{ template.downloadCount }} 次下载
                </span>
              </div>
            </div>
            <div class="template-actions">
              <el-button size="small" @click="createFromTemplate(template)">
                使用此模板
              </el-button>
            </div>
          </div>
        </el-card>
      </div>
      <template #footer>
        <el-button @click="showTemplateDialog = false">取消</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import { 
  Operation, 
  Plus, 
  Document, 
  Refresh,
  Search,
  MoreFilled,
  Edit,
  VideoPlay,
  CopyDocument,
  Delete,
  Download,
  Loading,
  PlayCircle,
  Command,
  Workflow,
  Condition,
  Clock,
  Bell
} from '@element-plus/icons-vue'
import { useWorkflowStore } from '@/stores/workflow'
import type { WorkflowDefinition, WorkflowTemplate, WorkflowNodeType } from '@/types/workflow'

const router = useRouter()
const workflowStore = useWorkflowStore()

// 响应式数据
const workflows = computed(() => workflowStore.workflows)
const templates = computed(() => workflowStore.templates)
const isLoading = ref(false)
const isCreating = ref(false)
const isExecuting = ref(false)

// 对话框状态
const showCreateDialog = ref(false)
const showExecuteDialog = ref(false)
const showTemplateDialog = ref(false)

// 搜索
const searchKeyword = ref('')

// 表单数据
const createForm = ref({
  name: '',
  description: ''
})

const executeForm = ref({
  macAddress: '',
  serialNumber: '',
  operator: '',
  workstation: '',
  deviceId: ''
})

const currentWorkflow = ref<WorkflowDefinition | null>(null)

// 计算属性
const filteredWorkflows = computed(() => {
  if (!searchKeyword.value) {
    return workflows.value
  }
  return workflows.value.filter(workflow => 
    workflow.name.toLowerCase().includes(searchKeyword.value.toLowerCase()) ||
    workflow.description?.toLowerCase().includes(searchKeyword.value.toLowerCase())
  )
})

// 方法
const loadWorkflows = async () => {
  try {
    isLoading.value = true
    await workflowStore.loadWorkflows()
  } catch (error) {
    console.error('加载工作流失败:', error)
    ElMessage.error('加载工作流失败')
  } finally {
    isLoading.value = false
  }
}

const loadTemplates = async () => {
  try {
    await workflowStore.loadTemplates()
  } catch (error) {
    console.error('加载模板失败:', error)
    ElMessage.error('加载模板失败')
  }
}

const handleSearch = () => {
  // 搜索逻辑已在计算属性中处理
}

const handleCreateWorkflow = async () => {
  if (!createForm.value.name.trim()) {
    ElMessage.warning('请输入工作流名称')
    return
  }

  try {
    isCreating.value = true
    const workflow = await workflowStore.createWorkflow({
      name: createForm.value.name,
      description: createForm.value.description
    })
    
    ElMessage.success('工作流创建成功')
    showCreateDialog.value = false
    createForm.value = { name: '', description: '' }
    
    // 跳转到工作流设计器
    router.push(`/workflow-designer/${workflow.id}`)
  } catch (error) {
    console.error('创建工作流失败:', error)
    ElMessage.error('创建工作流失败')
  } finally {
    isCreating.value = false
  }
}

const handleExecuteWorkflow = async () => {
  if (!currentWorkflow.value) return
  
  if (!executeForm.value.macAddress.trim()) {
    ElMessage.warning('请输入MAC地址')
    return
  }

  try {
    isExecuting.value = true
    await workflowStore.executeWorkflow({
      workflowId: currentWorkflow.value.id,
      macAddress: executeForm.value.macAddress,
      serialNumber: executeForm.value.serialNumber,
      operator: executeForm.value.operator,
      workstation: executeForm.value.workstation,
      deviceId: executeForm.value.deviceId
    })
    
    ElMessage.success('工作流执行已开始')
    showExecuteDialog.value = false
    executeForm.value = {
      macAddress: '',
      serialNumber: '',
      operator: '',
      workstation: '',
      deviceId: ''
    }
  } catch (error) {
    console.error('执行工作流失败:', error)
    ElMessage.error('执行工作流失败')
  } finally {
    isExecuting.value = false
  }
}

const editWorkflow = (workflow: WorkflowDefinition) => {
  router.push(`/workflow-designer/${workflow.id}`)
}

const executeWorkflow = (workflow: WorkflowDefinition) => {
  currentWorkflow.value = workflow
  showExecuteDialog.value = true
}

const createFromTemplate = async (template: WorkflowTemplate) => {
  try {
    const workflow = await workflowStore.createFromTemplate(template.id, `${template.name} - 副本`)
    ElMessage.success('从模板创建工作流成功')
    showTemplateDialog.value = false
    router.push(`/workflow-designer/${workflow.id}`)
  } catch (error) {
    console.error('从模板创建工作流失败:', error)
    ElMessage.error('从模板创建工作流失败')
  }
}

const handleWorkflowAction = async (command: { action: string; workflow: WorkflowDefinition }) => {
  const { action, workflow } = command
  
  switch (action) {
    case 'edit':
      editWorkflow(workflow)
      break
    case 'execute':
      executeWorkflow(workflow)
      break
    case 'duplicate':
      try {
        await workflowStore.duplicateWorkflow(workflow.id, `${workflow.name} - 副本`)
        ElMessage.success('工作流复制成功')
      } catch (error) {
        console.error('复制工作流失败:', error)
        ElMessage.error('复制工作流失败')
      }
      break
    case 'delete':
      try {
        await ElMessageBox.confirm(
          `确定要删除工作流 "${workflow.name}" 吗？此操作不可恢复。`,
          '确认删除',
          {
            confirmButtonText: '删除',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        await workflowStore.deleteWorkflow(workflow.id)
        ElMessage.success('工作流删除成功')
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除工作流失败:', error)
          ElMessage.error('删除工作流失败')
        }
      }
      break
  }
}

const getStatusType = (status: string) => {
  switch (status) {
    case 'active': return 'success'
    case 'draft': return 'info'
    case 'inactive': return 'warning'
    case 'running': return 'primary'
    case 'completed': return 'success'
    case 'failed': return 'danger'
    case 'cancelled': return 'info'
    default: return 'info'
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'active': return '激活'
    case 'draft': return '草稿'
    case 'inactive': return '未激活'
    case 'running': return '运行中'
    case 'completed': return '已完成'
    case 'failed': return '失败'
    case 'cancelled': return '已取消'
    default: return '未知'
  }
}

const getNodeIcon = (type: WorkflowNodeType) => {
  switch (type) {
    case 'start': return PlayCircle
    case 'end': return PlayCircle
    case 'command': return Command
    case 'workflow': return Workflow
    case 'condition': return Condition
    case 'delay': return Clock
    case 'notification': return Bell
    default: return Command
  }
}

const formatTime = (timestamp: number) => {
  return new Date(timestamp).toLocaleString('zh-CN')
}

// 组件挂载
onMounted(async () => {
  await loadWorkflows()
  await loadTemplates()
})
</script>

<style scoped>
.workflow-orchestration-container {
  height: 100%;
  background: linear-gradient(135deg, #f5f7fa 0%, #f8fafc 100%);
}

.page-content {
  height: 100%;
  padding: 24px;
  overflow: auto;
}

/* 工具栏 */
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 16px 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #e2e8f0;
}

.toolbar-left {
  display: flex;
  gap: 12px;
  align-items: center;
}

.toolbar-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

/* 工作流列表 */
.workflow-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.workflow-card {
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  transition: all 0.3s ease;
  overflow: hidden;
}

.workflow-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  border-color: #667eea;
}

.workflow-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 0;
}

.workflow-info {
  flex: 1;
  min-width: 0;
}

.workflow-name {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: #1a202c;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.workflow-description {
  margin: 0;
  font-size: 14px;
  color: #64748b;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.workflow-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.workflow-content {
  padding: 16px 0;
}

.workflow-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-label {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
}

.stat-value {
  font-size: 16px;
  font-weight: 600;
  color: #1a202c;
}

.workflow-nodes {
  margin-bottom: 16px;
}

.nodes-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.node-preview {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  font-size: 12px;
  color: #374151;
  transition: all 0.2s ease;
}

.node-preview:hover {
  background: #f8fafc;
  border-color: #667eea;
}

.node-preview.start {
  background: #f0fdf4;
  border-color: #22c55e;
  color: #16a34a;
}

.node-preview.end {
  background: #fef2f2;
  border-color: #ef4444;
  color: #dc2626;
}

.node-preview.command {
  background: #f0f9ff;
  border-color: #3b82f6;
  color: #2563eb;
}

.node-preview.workflow {
  background: #faf5ff;
  border-color: #8b5cf6;
  color: #7c3aed;
}

.node-preview.condition {
  background: #fffbeb;
  border-color: #f59e0b;
  color: #d97706;
}

.node-preview.delay {
  background: #f1f5f9;
  border-color: #64748b;
  color: #475569;
}

.node-preview.notification {
  background: #fef3c7;
  border-color: #f59e0b;
  color: #d97706;
}

.more-nodes {
  padding: 6px 12px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  font-size: 12px;
  color: #64748b;
}

.workflow-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid #e2e8f0;
}

.workflow-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.created-time,
.updated-time {
  font-size: 12px;
  color: #94a3b8;
}

.workflow-buttons {
  display: flex;
  gap: 8px;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 80px 20px;
  background: white;
  border-radius: 16px;
  border: 2px dashed #cbd5e1;
  margin: 40px 0;
}

.empty-icon {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 24px;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
}

.empty-icon .el-icon {
  font-size: 40px;
  color: white;
}

.empty-title {
  margin: 0 0 16px 0;
  font-size: 24px;
  font-weight: 600;
  color: #1a202c;
}

.empty-description {
  margin: 0 0 32px 0;
  font-size: 16px;
  color: #64748b;
  line-height: 1.6;
}

.empty-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
  flex-wrap: wrap;
}

.empty-actions .el-button {
  padding: 12px 24px;
  font-size: 16px;
  font-weight: 500;
  border-radius: 8px;
  transition: all 0.3s ease;
}

/* 加载状态 */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: #64748b;
  font-size: 16px;
  gap: 16px;
}

.loading-state .el-icon {
  font-size: 32px;
}

/* 模板列表 */
.template-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  max-height: 400px;
  overflow-y: auto;
}

.template-card {
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  transition: all 0.3s ease;
}

.template-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  border-color: #667eea;
}

.template-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 16px;
}

.template-info {
  flex: 1;
  min-width: 0;
}

.template-name {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1a202c;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.template-description {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #64748b;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.template-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.template-stats {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #94a3b8;
}

.template-actions {
  flex-shrink: 0;
  margin-left: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-content {
    padding: 16px;
  }
  
  .toolbar {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .toolbar-left,
  .toolbar-right {
    justify-content: center;
  }
  
  .workflow-list {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .workflow-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .workflow-actions {
    justify-content: flex-end;
  }
  
  .workflow-stats {
    flex-direction: column;
    gap: 8px;
  }
  
  .workflow-footer {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .workflow-buttons {
    justify-content: center;
  }
  
  .empty-actions {
    flex-direction: column;
    align-items: center;
  }
  
  .empty-actions .el-button {
    width: 200px;
  }
  
  .template-list {
    grid-template-columns: 1fr;
  }
  
  .template-content {
    flex-direction: column;
    gap: 12px;
  }
  
  .template-actions {
    margin-left: 0;
    align-self: flex-end;
  }
}

@media (max-width: 480px) {
  .page-content {
    padding: 12px;
  }
  
  .toolbar {
    padding: 12px 16px;
  }
  
  .workflow-card {
    margin: 0;
  }
  
  .workflow-name {
    font-size: 16px;
  }
  
  .workflow-description {
    font-size: 13px;
  }
  
  .stat-value {
    font-size: 14px;
  }
  
  .node-preview {
    font-size: 11px;
    padding: 4px 8px;
  }
  
  .empty-state {
    padding: 60px 16px;
  }
  
  .empty-icon {
    width: 60px;
    height: 60px;
  }
  
  .empty-icon .el-icon {
    font-size: 30px;
  }
  
  .empty-title {
    font-size: 20px;
  }
  
  .empty-description {
    font-size: 14px;
  }
  
  .empty-actions .el-button {
    width: 100%;
    max-width: 200px;
  }
}
</style>
