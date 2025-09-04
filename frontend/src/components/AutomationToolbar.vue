<template>
  <div class="automation-toolbar">
    <!-- 快速操作按钮 -->
    <div class="quick-actions">
      <el-button-group>
        <el-button 
          v-for="template in quickTemplates" 
          :key="template.template_id"
          :type="getButtonType(template.command_type)"
          size="small"
          @click="executeQuickCommand(template)"
          :loading="isExecuting(template.template_id)"
        >
          <el-icon>
            <component :is="getCommandIcon(template.command_type)" />
          </el-icon>
          {{ template.name }}
        </el-button>
      </el-button-group>
      
      <!-- 更多命令按钮 -->
      <el-dropdown @command="handleDropdownCommand" trigger="click">
        <el-button type="primary" size="small">
          更多命令
          <el-icon class="el-icon--right"><ArrowDown /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item 
              v-for="template in otherTemplates" 
              :key="template.template_id"
              :command="template.template_id"
            >
              <el-icon>
                <component :is="getCommandIcon(template.command_type)" />
              </el-icon>
              {{ template.name }}
            </el-dropdown-item>
            <el-dropdown-item divided command="custom">
              <el-icon><Plus /></el-icon>
              自定义命令
            </el-dropdown-item>
            <el-dropdown-item command="history">
              <el-icon><Document /></el-icon>
              命令历史
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>

    <!-- 状态指示器 -->
    <div class="status-indicators" v-if="showStatus">
      <el-badge :value="pendingCount" :hidden="pendingCount === 0" type="warning">
        <el-button size="small" circle @click="$emit('showPending')">
          <el-icon><Clock /></el-icon>
        </el-button>
      </el-badge>
      
      <el-badge :value="executingCount" :hidden="executingCount === 0" type="primary">
        <el-button size="small" circle @click="$emit('showExecuting')">
          <el-icon><Loading /></el-icon>
        </el-button>
      </el-badge>
    </div>

    <!-- 参数输入对话框 -->
    <el-dialog
      v-model="showParameterDialog"
      :title="`执行命令: ${selectedTemplate?.name}`"
      width="600px"
      destroy-on-close
    >
      <div v-if="selectedTemplate">
        <el-alert
          :title="selectedTemplate.description"
          type="info"
          show-icon
          :closable="false"
          style="margin-bottom: 20px"
        />
        
        <el-form :model="commandParameters" label-width="120px" ref="parameterFormRef">
          <div v-for="(schema, paramName) in selectedTemplate.parameters_schema" :key="paramName">
            <el-form-item 
              :label="schema.description || paramName"
              :required="schema.required"
            >
              <!-- 字符串输入 -->
              <el-input
                v-if="schema.type === 'string'"
                v-model="commandParameters[paramName]"
                :placeholder="`请输入${schema.description || paramName}`"
              />
              
              <!-- 数字输入 -->
              <el-input-number
                v-else-if="schema.type === 'number'"
                v-model="commandParameters[paramName]"
                controls-position="right"
                style="width: 100%"
              />
              
              <!-- 布尔值选择 -->
              <el-switch
                v-else-if="schema.type === 'boolean'"
                v-model="commandParameters[paramName]"
                :active-text="schema.description || '是'"
                inactive-text="否"
              />
              
              <!-- 对象/其他类型 -->
              <el-input
                v-else
                v-model="commandParameters[paramName]"
                type="textarea"
                rows="3"
                :placeholder="`请输入JSON格式的${schema.description || paramName}`"
              />
            </el-form-item>
          </div>
        </el-form>
      </div>
      
      <template #footer>
        <el-button @click="showParameterDialog = false">取消</el-button>
        <el-button type="primary" @click="executeWithParameters" :loading="executing">
          执行命令
        </el-button>
      </template>
    </el-dialog>

    <!-- 确认弹窗 -->
    <AutomationConfirmDialog
      v-model="showConfirmDialog"
      :command="pendingCommand"
      :title="confirmTitle"
      :risk-warnings="currentRiskWarnings"
      @confirm="handleCommandConfirm"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  ElButton, ElButtonGroup, ElDropdown, ElDropdownMenu, ElDropdownItem,
  ElBadge, ElIcon, ElDialog, ElAlert, ElDescriptions, ElDescriptionsItem,
  ElTag, ElTable, ElTableColumn, ElForm, ElFormItem, ElInput,
  ElInputNumber, ElSwitch, ElMessage
} from 'element-plus'
import {
  ArrowDown, Plus, Document, Clock, Loading, Check, Close, CircleClose,
  Setting, Monitor, Operation, Tools
} from '@element-plus/icons-vue'
import { useAutomationStore } from '@/stores/automation'
import AutomationConfirmDialog from './AutomationConfirmDialog.vue'
import type { AutomationCommand, CommandTemplate } from '@/api/automation'

interface Props {
  showStatus?: boolean
  quickTemplateIds?: string[]
  workstationId?: string
  operatorId?: string
}

interface Emits {
  (e: 'showPending'): void
  (e: 'showExecuting'): void
  (e: 'showHistory'): void
  (e: 'commandCreated', command: AutomationCommand): void
}

const props = withDefaults(defineProps<Props>(), {
  showStatus: true,
  quickTemplateIds: () => ['clear_cache', 'backup_data']
})

const emit = defineEmits<Emits>()

const automationStore = useAutomationStore()

// 响应式数据
const showParameterDialog = ref(false)
const showConfirmDialog = ref(false)
const selectedTemplate = ref<CommandTemplate | null>(null)
const pendingCommand = ref<AutomationCommand | null>(null)
const commandParameters = ref<Record<string, any>>({})
const parameterFormRef = ref()
const executingTemplates = ref<Set<string>>(new Set())

// 计算属性
const {
  templates,
  pendingCommands,
  executingCommands,
  executing,
  loadTemplates,
  executeTemplate,
  confirmCommand
} = automationStore

const quickTemplates = computed(() => 
  templates.value.filter(t => props.quickTemplateIds.includes(t.template_id))
)

const otherTemplates = computed(() => 
  templates.value.filter(t => !props.quickTemplateIds.includes(t.template_id))
)

const pendingCount = computed(() => pendingCommands.value.length)
const executingCount = computed(() => executingCommands.value.length)

const confirmTitle = computed(() => {
  if (!pendingCommand.value) return '命令确认'
  return `确认执行: ${selectedTemplate.value?.name || '未知命令'}`
})

const currentRiskWarnings = computed(() => {
  if (!selectedTemplate.value) return []
  
  const warnings: string[] = []
  
  // 根据命令类型添加风险提示
  if (selectedTemplate.value.command_type === 'system') {
    warnings.push('系统命令可能影响设备运行状态')
  }
  if (selectedTemplate.value.command_type === 'device') {
    warnings.push('设备命令将直接控制硬件设备')
  }
  if (selectedTemplate.value.command_type === 'maintenance') {
    warnings.push('维护命令可能需要较长时间执行')
  }
  
  return warnings
})

/**
 * 快速执行命令
 */
const executeQuickCommand = async (template: CommandTemplate) => {
  selectedTemplate.value = template
  
  // 检查是否需要参数
  const hasParameters = Object.keys(template.parameters_schema).length > 0
  
  if (hasParameters) {
    // 显示参数输入对话框
    resetParameters()
    showParameterDialog.value = true
  } else {
    // 直接执行
    await executeCommand(template.template_id, {})
  }
}

/**
 * 处理下拉菜单命令
 */
const handleDropdownCommand = (command: string) => {
  if (command === 'custom') {
    emit('showHistory')
  } else if (command === 'history') {
    emit('showHistory')
  } else {
    const template = templates.value.find(t => t.template_id === command)
    if (template) {
      executeQuickCommand(template)
    }
  }
}

/**
 * 使用参数执行命令
 */
const executeWithParameters = async () => {
  if (!selectedTemplate.value) return
  
  try {
    // 验证必需参数
    for (const [paramName, schema] of Object.entries(selectedTemplate.value.parameters_schema)) {
      if (schema.required && !commandParameters.value[paramName]) {
        ElMessage.error(`请填写必需参数: ${schema.description || paramName}`)
        return
      }
    }
    
    await executeCommand(selectedTemplate.value.template_id, commandParameters.value)
    showParameterDialog.value = false
  } catch (error) {
    ElMessage.error('执行命令失败')
  }
}

/**
 * 执行命令
 */
const executeCommand = async (templateId: string, parameters: Record<string, any>) => {
  try {
    executingTemplates.value.add(templateId)
    
    const command = await executeTemplate(
      templateId,
      parameters,
      props.operatorId,
      props.workstationId
    )
    
    if (command) {
      emit('commandCreated', command)
      
      // 如果需要确认，显示确认弹窗
      if (command.status === 'pending') {
        pendingCommand.value = command
        showConfirmDialog.value = true
      }
    }
  } finally {
    executingTemplates.value.delete(templateId)
  }
}

/**
 * 处理命令确认
 */
const handleCommandConfirm = async (commandId: string, confirmed: boolean, notes?: string) => {
  await confirmCommand(commandId, confirmed, notes)
  pendingCommand.value = null
}

/**
 * 重置参数表单
 */
const resetParameters = () => {
  commandParameters.value = {}
  
  // 设置默认值
  if (selectedTemplate.value) {
    for (const [paramName, schema] of Object.entries(selectedTemplate.value.parameters_schema)) {
      if (schema.default !== undefined) {
        commandParameters.value[paramName] = schema.default
      }
    }
  }
}

/**
 * 检查模板是否正在执行
 */
const isExecuting = (templateId: string) => {
  return executingTemplates.value.has(templateId)
}

/**
 * 获取按钮类型
 */
const getButtonType = (commandType: string) => {
  const typeMap: Record<string, string> = {
    system: 'primary',
    device: 'success',
    test: 'warning',
    maintenance: 'info'
  }
  return typeMap[commandType] || 'default'
}

/**
 * 获取命令图标
 */
const getCommandIcon = (commandType: string) => {
  const iconMap: Record<string, any> = {
    system: Setting,
    device: Monitor,
    test: Operation,
    maintenance: Tools
  }
  return iconMap[commandType] || Setting
}

/**
 * 获取命令类型文本
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

/**
 * 格式化日期时间
 */
const formatDateTime = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

// 生命周期
onMounted(async () => {
  await loadTemplates()
})
</script>

<style scoped>
.automation-toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.quick-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.status-indicators {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .automation-toolbar {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .quick-actions {
    justify-content: center;
  }
  
  .status-indicators {
    justify-content: center;
  }
}

/* 按钮组样式优化 */
:deep(.el-button-group) {
  .el-button {
    border-radius: 0;
  }
  
  .el-button:first-child {
    border-top-left-radius: 6px;
    border-bottom-left-radius: 6px;
  }
  
  .el-button:last-child {
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
  }
}

/* 下拉菜单样式 */
:deep(.el-dropdown-menu__item) {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>