<template>
  <div class="automation-control">
    <el-card class="header-card">
      <template #header>
        <div class="card-header">
          <span>自动化命令控制</span>
          <el-button 
            type="primary" 
            @click="showCreateDialog = true"
            :loading="executing"
          >
            <el-icon><Plus /></el-icon>
            创建命令
          </el-button>
        </div>
      </template>
      
      <!-- 快速模板执行 -->
      <div class="template-section">
        <h4>快速执行模板</h4>
        <el-row :gutter="16">
          <el-col :span="6" v-for="template in templates" :key="template.template_id">
            <el-card 
              class="template-card" 
              shadow="hover"
              @click="executeQuickTemplate(template)"
            >
              <div class="template-content">
                <div class="template-header">
                  <el-tag :type="getTemplateTypeColor(template.command_type)" size="small">
                    {{ getCommandTypeText(template.command_type) }}
                  </el-tag>
                  <el-icon v-if="template.requires_confirmation" class="confirm-icon">
                    <Warning />
                  </el-icon>
                </div>
                <div class="template-name">{{ template.name }}</div>
                <div class="template-desc">{{ template.description }}</div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </el-card>

    <!-- 命令状态监控 -->
    <el-row :gutter="16" class="status-cards">
      <el-col :span="6">
        <el-card class="status-card pending">
          <el-statistic title="等待确认" :value="pendingCommands.length" />
          <template #suffix>
            <el-icon class="status-icon"><Clock /></el-icon>
          </template>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="status-card executing">
          <el-statistic title="执行中" :value="executingCommands.length" />
          <template #suffix>
            <el-icon class="status-icon"><Loading /></el-icon>
          </template>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="status-card">
          <el-statistic title="总命令数" :value="commands.length" />
          <template #suffix>
            <el-icon class="status-icon"><Document /></el-icon>
          </template>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="status-card">
          <el-button type="primary" @click="loadCommands()" :loading="loading">
            <el-icon><Refresh /></el-icon>
            刷新状态
          </el-button>
        </el-card>
      </el-col>
    </el-row>

    <!-- 命令列表 -->
    <el-card class="command-list-card">
      <template #header>
        <div class="card-header">
          <span>命令历史</span>
          <div class="filter-controls">
            <el-select v-model="filterStatus" placeholder="状态筛选" clearable @change="loadCommands()">
              <el-option label="等待确认" value="pending" />
              <el-option label="执行中" value="executing" />
              <el-option label="执行成功" value="success" />
              <el-option label="执行失败" value="failed" />
              <el-option label="已取消" value="cancelled" />
            </el-select>
          </div>
        </div>
      </template>
      
      <el-table 
        :data="recentCommands" 
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="command_id" label="命令ID" width="280" show-overflow-tooltip />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="execution_time" label="执行时间" width="100">
          <template #default="{ row }">
            {{ row.execution_time ? `${row.execution_time.toFixed(2)}s` : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button 
              v-if="row.status === 'pending'" 
              size="small" 
              type="success"
              @click="confirmCommand(row.command_id, true)"
            >
              确认
            </el-button>
            <el-button 
              v-if="['pending', 'executing'].includes(row.status)" 
              size="small" 
              type="danger"
              @click="cancelCommand(row.command_id)"
            >
              取消
            </el-button>
            <el-button 
              size="small"
              @click="refreshCommand(row.command_id)"
            >
              刷新
            </el-button>
            <el-button 
              size="small"
              @click="showCommandDetail(row)"
            >
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建命令对话框 -->
    <el-dialog 
      v-model="showCreateDialog" 
      title="创建自动化命令" 
      width="600px"
      destroy-on-close
    >
      <el-form :model="newCommand" label-width="120px" ref="createFormRef">
        <el-form-item label="命令名称" required>
          <el-input v-model="newCommand.command_name" placeholder="请输入命令名称" />
        </el-form-item>
        
        <el-form-item label="命令类型" required>
          <el-select v-model="newCommand.command_type" placeholder="选择命令类型">
            <el-option label="系统命令" value="system" />
            <el-option label="设备命令" value="device" />
            <el-option label="测试命令" value="test" />
            <el-option label="维护命令" value="maintenance" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="优先级">
          <el-select v-model="newCommand.priority" placeholder="选择优先级">
            <el-option label="低" value="low" />
            <el-option label="普通" value="normal" />
            <el-option label="高" value="high" />
            <el-option label="紧急" value="urgent" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="需要确认">
          <el-switch v-model="newCommand.requires_confirmation" />
        </el-form-item>
        
        <el-form-item label="超时时间">
          <el-input-number 
            v-model="newCommand.timeout_seconds" 
            :min="1" 
            :max="3600"
            controls-position="right"
          />
          <span style="margin-left: 8px">秒</span>
        </el-form-item>
        
        <el-form-item label="命令描述">
          <el-input 
            v-model="newCommand.description" 
            type="textarea" 
            rows="3"
            placeholder="请输入命令描述"
          />
        </el-form-item>
        
        <el-form-item label="命令参数">
          <el-input 
            v-model="parametersJson" 
            type="textarea" 
            rows="4"
            placeholder='请输入JSON格式的参数，例如: {"device_id": "DEV001"}'
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreateCommand" :loading="executing">
          创建命令
        </el-button>
      </template>
    </el-dialog>

    <!-- 命令详情对话框 -->
    <el-dialog 
      v-model="showDetailDialog" 
      title="命令详情" 
      width="800px"
    >
      <div v-if="selectedCommand" class="command-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="命令ID">
            {{ selectedCommand.command_id }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(selectedCommand.status)">
              {{ getStatusText(selectedCommand.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatDateTime(selectedCommand.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="更新时间">
            {{ formatDateTime(selectedCommand.updated_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="执行时间" v-if="selectedCommand.execution_time">
            {{ selectedCommand.execution_time.toFixed(2) }}秒
          </el-descriptions-item>
        </el-descriptions>
        
        <div v-if="selectedCommand.result" class="result-section">
          <h4>执行结果</h4>
          <el-input 
            :model-value="JSON.stringify(selectedCommand.result, null, 2)"
            type="textarea"
            rows="6"
            readonly
          />
        </div>
        
        <div v-if="selectedCommand.error_message" class="error-section">
          <h4>错误信息</h4>
          <el-alert 
            :title="selectedCommand.error_message"
            type="error"
            show-icon
            :closable="false"
          />
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { 
  ElCard, ElButton, ElRow, ElCol, ElTable, ElTableColumn, 
  ElTag, ElDialog, ElForm, ElFormItem, ElInput, ElSelect, 
  ElOption, ElSwitch, ElInputNumber, ElMessage, ElMessageBox,
  ElStatistic, ElIcon, ElDescriptions, ElDescriptionsItem,
  ElAlert
} from 'element-plus'
import { 
  Plus, Clock, Loading, Document, Refresh, Warning 
} from '@element-plus/icons-vue'
import { useAutomationStore } from '@/stores/automation'
import type { AutomationCommand, CommandTemplate, AutomationCommandRequest } from '@/api/automation'

const automationStore = useAutomationStore()

// 响应式数据
const showCreateDialog = ref(false)
const showDetailDialog = ref(false)
const selectedCommand = ref<AutomationCommand | null>(null)
const filterStatus = ref('')
const parametersJson = ref('')
const createFormRef = ref()

// 新命令表单
const newCommand = reactive<AutomationCommandRequest>({
  command_name: '',
  command_type: 'system',
  priority: 'normal',
  requires_confirmation: true,
  timeout_seconds: 30,
  description: '',
  parameters: {}
})

// 计算属性和方法从store中解构
const {
  commands,
  templates,
  loading,
  executing,
  pendingCommands,
  executingCommands,
  recentCommands,
  loadTemplates,
  loadCommands,
  createCommand,
  executeTemplate,
  confirmCommand,
  cancelCommand,
  refreshCommand,
  getStatusText,
  getStatusType,
  getCommandTypeText
} = automationStore

/**
 * 快速执行模板
 */
const executeQuickTemplate = async (template: CommandTemplate) => {
  // 如果模板需要参数，显示参数输入对话框
  if (Object.keys(template.parameters_schema).length > 0) {
    await showTemplateParametersDialog(template)
  } else {
    // 直接执行
    await executeTemplate(template.template_id, {})
  }
}

/**
 * 显示模板参数输入对话框
 */
const showTemplateParametersDialog = async (template: CommandTemplate) => {
  try {
    const { value: formData } = await ElMessageBox.prompt(
      `请输入 "${template.name}" 的参数 (JSON格式)`,
      '参数输入',
      {
        confirmButtonText: '执行',
        cancelButtonText: '取消',
        inputPlaceholder: '{"param1": "value1", "param2": "value2"}',
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
    
    const parameters = JSON.parse(formData || '{}')
    await executeTemplate(template.template_id, parameters)
  } catch {
    // 用户取消
  }
}

/**
 * 处理创建命令
 */
const handleCreateCommand = async () => {
  try {
    // 解析参数JSON
    if (parametersJson.value.trim()) {
      newCommand.parameters = JSON.parse(parametersJson.value)
    }
    
    await createCommand(newCommand)
    showCreateDialog.value = false
    resetCreateForm()
  } catch (error) {
    ElMessage.error('参数格式错误，请检查JSON格式')
  }
}

/**
 * 重置创建表单
 */
const resetCreateForm = () => {
  Object.assign(newCommand, {
    command_name: '',
    command_type: 'system',
    priority: 'normal',
    requires_confirmation: true,
    timeout_seconds: 30,
    description: '',
    parameters: {}
  })
  parametersJson.value = ''
}

/**
 * 显示命令详情
 */
const showCommandDetail = (command: AutomationCommand) => {
  selectedCommand.value = command
  showDetailDialog.value = true
}

/**
 * 获取模板类型颜色
 */
const getTemplateTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    system: 'primary',
    device: 'success',
    test: 'warning',
    maintenance: 'info'
  }
  return colorMap[type] || 'primary'
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
  await loadCommands()
})
</script>

<style scoped>
.automation-control {
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

.template-section {
  margin-top: 16px;
}

.template-section h4 {
  margin-bottom: 16px;
  color: #303133;
}

.template-card {
  cursor: pointer;
  transition: all 0.3s;
  height: 120px;
}

.template-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.template-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.template-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.confirm-icon {
  color: #f56c6c;
}

.template-name {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 4px;
  color: #303133;
}

.template-desc {
  font-size: 12px;
  color: #909399;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.status-cards {
  margin-bottom: 20px;
}

.status-card {
  text-align: center;
}

.status-card.pending {
  border-left: 4px solid #e6a23c;
}

.status-card.executing {
  border-left: 4px solid #409eff;
}

.status-icon {
  font-size: 20px;
  margin-left: 8px;
}

.command-list-card {
  margin-bottom: 20px;
}

.filter-controls {
  display: flex;
  gap: 12px;
  align-items: center;
}

.command-detail {
  padding: 16px 0;
}

.result-section,
.error-section {
  margin-top: 20px;
}

.result-section h4,
.error-section h4 {
  margin-bottom: 12px;
  color: #303133;
}

/* 确认弹窗样式 */
:deep(.automation-confirm-dialog) {
  .el-message-box__header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
  }
  
  .el-message-box__title {
    color: white;
  }
  
  .el-message-box__headerbtn .el-message-box__close {
    color: white;
  }
}
</style>