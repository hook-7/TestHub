<template>
  <div class="workflow-editor">
    <div class="editor-header">
      <el-breadcrumb>
        <el-breadcrumb-item>工作流管理</el-breadcrumb-item>
        <el-breadcrumb-item>{{ isEditing ? '编辑工作流' : '新建工作流' }}</el-breadcrumb-item>
      </el-breadcrumb>
      
      <div class="header-actions">
        <el-button @click="$router.push('/workflow')">返回</el-button>
        <el-button type="primary" @click="saveWorkflow" :loading="workflowStore.isLoading">
          {{ isEditing ? '保存' : '创建' }}
        </el-button>
      </div>
    </div>

    <div class="editor-content">
      <!-- 基本信息 -->
      <el-card class="info-card">
        <template #header>
          <span>基本信息</span>
        </template>
        
        <el-form :model="workflowStore.editorWorkflow" label-width="100px">
          <el-form-item label="工作流名称" required>
            <el-input 
              v-model="workflowStore.editorWorkflow.name" 
              placeholder="请输入工作流名称"
              maxlength="50"
              show-word-limit
            />
          </el-form-item>
          
          <el-form-item label="描述">
            <el-input 
              v-model="workflowStore.editorWorkflow.description" 
              type="textarea" 
              placeholder="请输入工作流描述"
              :rows="3"
              maxlength="200"
              show-word-limit
            />
          </el-form-item>
          
          <el-form-item label="初始变量">
            <div class="variables-editor">
              <div 
                v-for="(value, key) in workflowStore.editorWorkflow.variables" 
                :key="key"
                class="variable-item"
              >
                <el-input v-model="variableKeys[key]" placeholder="变量名" style="width: 120px" />
                <span>=</span>
                <el-input v-model="workflowStore.editorWorkflow.variables[key]" placeholder="变量值" />
                <el-button 
                  type="danger" 
                  size="small" 
                  @click="removeVariable(key)"
                  :icon="Delete"
                />
              </div>
              
              <el-button type="primary" size="small" @click="addVariable" :icon="Plus">
                添加变量
              </el-button>
            </div>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 步骤编辑器 -->
      <el-card class="steps-card">
        <template #header>
          <div class="steps-header">
            <span>工作流步骤</span>
            <el-button type="primary" size="small" @click="showAddStepDialog" :icon="Plus">
              添加步骤
            </el-button>
          </div>
        </template>
        
        <div class="steps-container">
          <div v-if="workflowStore.editorWorkflow.steps.length === 0" class="empty-steps">
            <el-empty description="暂无步骤，点击上方按钮添加步骤" />
          </div>
          
          <div v-else class="steps-list">
            <div 
              v-for="(step, index) in workflowStore.editorWorkflow.steps" 
              :key="step.id"
              class="step-item"
              :class="{ active: selectedStepId === step.id }"
              @click="selectStep(step.id)"
            >
              <div class="step-header">
                <div class="step-info">
                  <span class="step-index">{{ index + 1 }}</span>
                  <span class="step-type">{{ getStepTypeLabel(step.type) }}</span>
                  <span class="step-name">{{ step.name }}</span>
                </div>
                
                <div class="step-actions">
                  <el-button 
                    size="small" 
                    @click.stop="editStep(step)"
                    :icon="Edit"
                  />
                  <el-button 
                    size="small" 
                    @click.stop="moveStepUp(index)"
                    :disabled="index === 0"
                    :icon="ArrowUp"
                  />
                  <el-button 
                    size="small" 
                    @click.stop="moveStepDown(index)"
                    :disabled="index === workflowStore.editorWorkflow.steps.length - 1"
                    :icon="ArrowDown"
                  />
                  <el-button 
                    type="danger" 
                    size="small" 
                    @click.stop="removeStep(step.id)"
                    :icon="Delete"
                  />
                </div>
              </div>
              
              <div class="step-description">
                {{ step.description || '无描述' }}
              </div>
              
              <div class="step-config">
                {{ getStepConfigSummary(step) }}
              </div>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 添加步骤对话框 -->
    <el-dialog 
      v-model="addStepDialogVisible" 
      title="添加步骤" 
      width="600px"
      :close-on-click-modal="false"
    >
      <StepEditor 
        v-if="addStepDialogVisible"
        :step="editingStep" 
        @save="handleStepSave" 
        @cancel="handleStepCancel" 
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, Edit, ArrowUp, ArrowDown } from '@element-plus/icons-vue'
import { useWorkflowStore } from '@/stores/workflow'
import StepEditor from '@/components/workflow/StepEditor.vue'
import type { WorkflowStep } from '@/api/workflow'

const router = useRouter()
const route = useRoute()
const workflowStore = useWorkflowStore()

// 状态
const selectedStepId = ref<string>('')
const addStepDialogVisible = ref(false)
const editingStep = ref<WorkflowStep | null>(null)
const variableKeys = reactive<Record<string, string>>({})

// 计算属性
const isEditing = computed(() => !!route.params.id)

// 步骤类型标签映射
const stepTypeLabels = {
  send: '发送指令',
  expect: '期望回复',
  assign: '变量赋值',
  confirm: '用户确认',
  control: '逻辑控制'
}

// 方法
const getStepTypeLabel = (type: string) => {
  return stepTypeLabels[type as keyof typeof stepTypeLabels] || type
}

const getStepConfigSummary = (step: WorkflowStep) => {
  switch (step.type) {
    case 'send':
      return `指令: ${step.command || ''}`
    case 'expect':
      return `期望: ${step.pattern || ''} (${step.expect_type || 'string'})`
    case 'assign':
      return `${step.variable || ''} = ${step.expression || ''}`
    case 'confirm':
      return `消息: ${step.message || ''}`
    case 'control':
      return `${step.control_type || ''}: ${step.condition || ''}`
    default:
      return ''
  }
}

const selectStep = (stepId: string) => {
  selectedStepId.value = stepId
}

const showAddStepDialog = () => {
  editingStep.value = null
  addStepDialogVisible.value = true
}

const editStep = (step: WorkflowStep) => {
  editingStep.value = { ...step }
  addStepDialogVisible.value = true
}

const handleStepSave = (step: WorkflowStep) => {
  if (editingStep.value) {
    // 更新步骤
    workflowStore.updateStep(step.id, step)
  } else {
    // 添加新步骤
    workflowStore.addStep(step)
  }
  
  addStepDialogVisible.value = false
  editingStep.value = null
}

const handleStepCancel = () => {
  addStepDialogVisible.value = false
  editingStep.value = null
}

const removeStep = async (stepId: string) => {
  try {
    await ElMessageBox.confirm('确定要删除这个步骤吗？', '确认删除', {
      type: 'warning'
    })
    
    workflowStore.removeStep(stepId)
    if (selectedStepId.value === stepId) {
      selectedStepId.value = ''
    }
  } catch {
    // 用户取消
  }
}

const moveStepUp = (index: number) => {
  if (index > 0) {
    workflowStore.moveStep(index, index - 1)
  }
}

const moveStepDown = (index: number) => {
  if (index < workflowStore.editorWorkflow.steps.length - 1) {
    workflowStore.moveStep(index, index + 1)
  }
}

const addVariable = () => {
  const key = `variable_${Object.keys(workflowStore.editorWorkflow.variables).length + 1}`
  workflowStore.editorWorkflow.variables[key] = ''
  variableKeys[key] = key
}

const removeVariable = (key: string) => {
  delete workflowStore.editorWorkflow.variables[key]
  delete variableKeys[key]
}

const saveWorkflow = async () => {
  if (!workflowStore.editorWorkflow.name.trim()) {
    ElMessage.error('请输入工作流名称')
    return
  }
  
  if (workflowStore.editorWorkflow.steps.length === 0) {
    ElMessage.error('请至少添加一个步骤')
    return
  }

  try {
    const workflowData = {
      name: workflowStore.editorWorkflow.name,
      description: workflowStore.editorWorkflow.description,
      variables: workflowStore.editorWorkflow.variables,
      steps: workflowStore.editorWorkflow.steps.map(step => ({
        ...step,
        // 确保所有步骤都有必要的字段
      }))
    }

    if (isEditing.value) {
      await workflowStore.updateWorkflow(route.params.id as string, workflowData)
    } else {
      await workflowStore.createWorkflow(workflowData)
    }
    
    router.push('/workflow')
  } catch (error) {
    // 错误已在store中处理
  }
}

// 生命周期
onMounted(async () => {
  if (isEditing.value) {
    try {
      const workflow = await workflowStore.getWorkflow(route.params.id as string)
      workflowStore.loadWorkflowToEditor(workflow)
      
      // 初始化变量键映射
      for (const key in workflow.variables) {
        variableKeys[key] = key
      }
    } catch (error) {
      ElMessage.error('加载工作流失败')
      router.push('/workflow')
    }
  } else {
    workflowStore.resetEditor()
  }
})
</script>

<style scoped>
.workflow-editor {
  padding: 20px;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.editor-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow: hidden;
}

.info-card {
  flex-shrink: 0;
}

.steps-card {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.steps-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.steps-container {
  flex: 1;
  overflow-y: auto;
}

.empty-steps {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
}

.steps-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.step-item {
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  padding: 15px;
  cursor: pointer;
  transition: all 0.2s;
}

.step-item:hover {
  border-color: var(--el-color-primary);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.step-item.active {
  border-color: var(--el-color-primary);
  background-color: var(--el-color-primary-light-9);
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.step-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.step-index {
  background: var(--el-color-primary);
  color: white;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
}

.step-type {
  background: var(--el-color-info-light-8);
  color: var(--el-color-info);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.step-name {
  font-weight: 500;
}

.step-actions {
  display: flex;
  gap: 5px;
}

.step-description {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  margin-bottom: 5px;
}

.step-config {
  color: var(--el-text-color-regular);
  font-size: 13px;
  font-family: 'Courier New', monospace;
  background: var(--el-fill-color-lighter);
  padding: 8px;
  border-radius: 4px;
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
</style>