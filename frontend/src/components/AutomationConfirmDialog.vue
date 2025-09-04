<template>
  <el-dialog
    v-model="visible"
    :title="title"
    width="500px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    destroy-on-close
    class="automation-confirm-dialog"
  >
    <div class="confirm-content">
      <!-- 命令信息 -->
      <div class="command-info">
        <el-alert
          :title="commandInfo.title"
          :description="commandInfo.description"
          type="warning"
          show-icon
          :closable="false"
        />
      </div>

      <!-- 详细信息 -->
      <div class="detail-info" v-if="command">
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="命令名称">
            {{ command.command_name || '未知命令' }}
          </el-descriptions-item>
          <el-descriptions-item label="命令类型">
            <el-tag :type="getCommandTypeColor(command.command_type)" size="small">
              {{ getCommandTypeText(command.command_type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="优先级" v-if="command.priority">
            <el-tag :type="getPriorityColor(command.priority)" size="small">
              {{ getPriorityText(command.priority) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatDateTime(command.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="超时时间" v-if="command.timeout_seconds">
            {{ command.timeout_seconds }}秒
          </el-descriptions-item>
        </el-descriptions>

        <!-- 参数信息 -->
        <div v-if="command.parameters && Object.keys(command.parameters).length > 0" class="parameters-section">
          <h4>命令参数</h4>
          <el-table :data="parametersList" size="small" border>
            <el-table-column prop="key" label="参数名" width="150" />
            <el-table-column prop="value" label="参数值" />
          </el-table>
        </div>
      </div>

      <!-- 风险提示 -->
      <div class="risk-warning" v-if="showRiskWarning">
        <el-alert
          title="注意事项"
          type="error"
          show-icon
          :closable="false"
        >
          <template #default>
            <ul class="risk-list">
              <li v-for="risk in riskWarnings" :key="risk">{{ risk }}</li>
            </ul>
          </template>
        </el-alert>
      </div>

      <!-- 操作员备注 -->
      <div class="operator-notes">
        <el-form-item label="操作员备注">
          <el-input
            v-model="operatorNotes"
            type="textarea"
            rows="3"
            placeholder="请输入操作备注（可选）"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleCancel" :disabled="confirming">
          <el-icon><Close /></el-icon>
          取消
        </el-button>
        <el-button 
          type="danger" 
          @click="handleConfirm(false)"
          :disabled="confirming"
        >
          <el-icon><CircleClose /></el-icon>
          拒绝执行
        </el-button>
        <el-button 
          type="primary" 
          @click="handleConfirm(true)"
          :loading="confirming"
        >
          <el-icon><Check /></el-icon>
          确认执行
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  ElDialog, ElAlert, ElDescriptions, ElDescriptionsItem,
  ElTag, ElTable, ElTableColumn, ElFormItem, ElInput,
  ElButton, ElIcon
} from 'element-plus'
import { Close, CircleClose, Check } from '@element-plus/icons-vue'
import type { AutomationCommand } from '@/api/automation'

interface Props {
  modelValue: boolean
  command: AutomationCommand | null
  title?: string
  riskWarnings?: string[]
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'confirm', commandId: string, confirmed: boolean, notes?: string): void
}

const props = withDefaults(defineProps<Props>(), {
  title: '命令执行确认',
  riskWarnings: () => []
})

const emit = defineEmits<Emits>()

// 响应式数据
const visible = ref(false)
const confirming = ref(false)
const operatorNotes = ref('')

// 计算属性
const commandInfo = computed(() => {
  if (!props.command) {
    return {
      title: '未知命令',
      description: '命令信息不可用'
    }
  }

  const typeText = getCommandTypeText(props.command.command_type)
  return {
    title: `即将执行 ${typeText}`,
    description: props.command.description || `执行命令: ${props.command.command_name || '未知命令'}`
  }
})

const parametersList = computed(() => {
  if (!props.command?.parameters) return []
  
  return Object.entries(props.command.parameters).map(([key, value]) => ({
    key,
    value: typeof value === 'object' ? JSON.stringify(value) : String(value)
  }))
})

const showRiskWarning = computed(() => {
  return props.riskWarnings && props.riskWarnings.length > 0
})

// 监听props变化
watch(
  () => props.modelValue,
  (newVal) => {
    visible.value = newVal
    if (newVal) {
      operatorNotes.value = ''
      confirming.value = false
    }
  },
  { immediate: true }
)

watch(visible, (newVal) => {
  if (!newVal) {
    emit('update:modelValue', false)
  }
})

/**
 * 处理确认
 */
const handleConfirm = async (confirmed: boolean) => {
  if (!props.command) return

  try {
    confirming.value = true
    emit('confirm', props.command.command_id, confirmed, operatorNotes.value)
    visible.value = false
  } finally {
    confirming.value = false
  }
}

/**
 * 处理取消
 */
const handleCancel = () => {
  visible.value = false
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
 * 获取命令类型颜色
 */
const getCommandTypeColor = (type: string): string => {
  const colorMap: Record<string, string> = {
    system: 'primary',
    device: 'success',
    test: 'warning',
    maintenance: 'info'
  }
  return colorMap[type] || 'primary'
}

/**
 * 获取优先级文本
 */
const getPriorityText = (priority: string): string => {
  const priorityMap: Record<string, string> = {
    low: '低',
    normal: '普通',
    high: '高',
    urgent: '紧急'
  }
  return priorityMap[priority] || priority
}

/**
 * 获取优先级颜色
 */
const getPriorityColor = (priority: string): string => {
  const colorMap: Record<string, string> = {
    low: 'info',
    normal: 'primary',
    high: 'warning',
    urgent: 'danger'
  }
  return colorMap[priority] || 'primary'
}

/**
 * 格式化日期时间
 */
const formatDateTime = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}
</script>

<style scoped>
.confirm-content {
  padding: 16px 0;
}

.command-info {
  margin-bottom: 20px;
}

.detail-info {
  margin-bottom: 20px;
}

.parameters-section {
  margin-top: 16px;
}

.parameters-section h4 {
  margin-bottom: 12px;
  color: #303133;
  font-size: 14px;
}

.risk-warning {
  margin-bottom: 20px;
}

.risk-list {
  margin: 0;
  padding-left: 20px;
}

.risk-list li {
  margin-bottom: 4px;
  color: #f56c6c;
}

.operator-notes {
  margin-bottom: 16px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 对话框样式自定义 */
:deep(.automation-confirm-dialog) {
  .el-dialog__header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 16px 20px;
    margin: 0;
  }
  
  .el-dialog__title {
    color: white;
    font-weight: 600;
  }
  
  .el-dialog__headerbtn .el-dialog__close {
    color: white;
  }
  
  .el-dialog__body {
    padding: 20px;
  }
  
  .el-dialog__footer {
    padding: 16px 20px;
    border-top: 1px solid #ebeef5;
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  :deep(.automation-confirm-dialog) {
    width: 90% !important;
    margin: 5vh auto;
  }
}
</style>