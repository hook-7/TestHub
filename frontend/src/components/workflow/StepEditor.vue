<template>
  <div class="step-editor">
    <el-form :model="stepForm" label-width="100px" ref="formRef">
      <el-form-item label="步骤类型" required>
        <el-select 
          v-model="stepForm.type" 
          placeholder="请选择步骤类型"
          @change="handleTypeChange"
        >
          <el-option 
            v-for="type in stepTypes" 
            :key="type.value" 
            :label="type.label" 
            :value="type.value"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="步骤名称" required>
        <el-input 
          v-model="stepForm.name" 
          placeholder="请输入步骤名称"
          maxlength="50"
        />
      </el-form-item>

      <el-form-item label="描述">
        <el-input 
          v-model="stepForm.description" 
          type="textarea" 
          placeholder="请输入步骤描述"
          :rows="2"
        />
      </el-form-item>

      <!-- 发送步骤配置 -->
      <template v-if="stepForm.type === 'send'">
        <el-form-item label="发送指令" required>
          <el-input 
            v-model="stepForm.command" 
            placeholder="请输入要发送的指令，支持 ${variable} 变量占位符"
            type="textarea"
            :rows="3"
          />
        </el-form-item>
        
        <el-form-item label="串口名称">
          <el-input 
            v-model="stepForm.port" 
            placeholder="留空使用默认串口"
          />
        </el-form-item>
        
        <el-form-item label="延迟时间(秒)">
          <el-input-number 
            v-model="stepForm.delay" 
            :min="0" 
            :step="0.1"
            placeholder="发送后延迟时间"
          />
        </el-form-item>
      </template>

      <!-- 期望步骤配置 -->
      <template v-if="stepForm.type === 'expect'">
        <el-form-item label="匹配类型" required>
          <el-select v-model="stepForm.expect_type" placeholder="选择匹配类型">
            <el-option label="字符串匹配" value="string" />
            <el-option label="正则匹配" value="regex" />
            <el-option label="超时处理" value="timeout" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="匹配模式" required>
          <el-input 
            v-model="stepForm.pattern" 
            placeholder="字符串或正则表达式"
            type="textarea"
            :rows="2"
          />
        </el-form-item>
        
        <el-form-item label="超时时间(秒)">
          <el-input-number 
            v-model="stepForm.timeout" 
            :min="1" 
            placeholder="超时时间"
          />
        </el-form-item>
        
        <el-form-item label="超时处理" v-if="stepForm.expect_type === 'timeout'">
          <el-input 
            v-model="stepForm.on_timeout" 
            placeholder="超时时的处理表达式"
            type="textarea"
            :rows="2"
          />
        </el-form-item>
      </template>

      <!-- 赋值步骤配置 -->
      <template v-if="stepForm.type === 'assign'">
        <el-form-item label="变量名" required>
          <el-input 
            v-model="stepForm.variable" 
            placeholder="变量名"
          />
        </el-form-item>
        
        <el-form-item label="赋值表达式" required>
          <el-input 
            v-model="stepForm.expression" 
            placeholder="支持正则提取和逻辑运算，如: re.search('ID=(\\d+)', reply).group(1)"
            type="textarea"
            :rows="3"
          />
        </el-form-item>
      </template>

      <!-- 确认步骤配置 -->
      <template v-if="stepForm.type === 'confirm'">
        <el-form-item label="确认消息" required>
          <el-input 
            v-model="stepForm.message" 
            placeholder="向用户显示的确认消息"
            type="textarea"
            :rows="2"
          />
        </el-form-item>
        
        <el-form-item label="操作选项">
          <div class="options-editor">
            <div 
              v-for="(option, index) in stepForm.options" 
              :key="index"
              class="option-item"
            >
              <el-input 
                v-model="stepForm.options[index]" 
                placeholder="选项文本"
              />
              <el-button 
                type="danger" 
                size="small" 
                @click="removeOption(index)"
                :icon="Delete"
              />
            </div>
            
            <el-button type="primary" size="small" @click="addOption" :icon="Plus">
              添加选项
            </el-button>
          </div>
        </el-form-item>
        
        <el-form-item label="超时时间(秒)">
          <el-input-number 
            v-model="stepForm.timeout" 
            :min="1" 
            placeholder="确认超时时间，留空为无限等待"
          />
        </el-form-item>
      </template>

      <!-- 控制步骤配置 -->
      <template v-if="stepForm.type === 'control'">
        <el-form-item label="控制类型" required>
          <el-select v-model="stepForm.control_type" placeholder="选择控制类型">
            <el-option label="条件判断(IF)" value="if" />
            <el-option label="循环(LOOP)" value="loop" />
            <el-option label="跳出(BREAK)" value="break" />
            <el-option label="继续(CONTINUE)" value="continue" />
          </el-select>
        </el-form-item>
        
        <el-form-item 
          label="条件表达式" 
          v-if="stepForm.control_type === 'if' || stepForm.control_type === 'loop'"
          required
        >
          <el-input 
            v-model="stepForm.condition" 
            placeholder="如: voltage > 200 and status == 'OK'"
            type="textarea"
            :rows="2"
          />
        </el-form-item>
        
        <el-form-item label="子步骤" v-if="stepForm.control_type === 'if' || stepForm.control_type === 'loop'">
          <el-alert 
            title="子步骤配置暂不支持在此编辑器中配置，请使用高级编辑器" 
            type="info" 
            show-icon 
            :closable="false"
          />
        </el-form-item>
      </template>
    </el-form>

    <div class="dialog-footer">
      <el-button @click="$emit('cancel')">取消</el-button>
      <el-button type="primary" @click="handleSave">保存</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'
import type { WorkflowStep } from '@/api/workflow'

interface Props {
  step?: WorkflowStep | null
}

const props = defineProps<Props>()
const emit = defineEmits<{
  save: [step: WorkflowStep]
  cancel: []
}>()

// 步骤类型选项
const stepTypes = [
  { label: '发送指令', value: 'send' },
  { label: '期望回复', value: 'expect' },
  { label: '变量赋值', value: 'assign' },
  { label: '用户确认', value: 'confirm' },
  { label: '逻辑控制', value: 'control' }
]

// 表单数据
const stepForm = reactive<any>({
  id: '',
  name: '',
  type: 'send',
  description: '',
  // 发送步骤
  command: '',
  port: '',
  delay: 0,
  // 期望步骤
  expect_type: 'string',
  pattern: '',
  timeout: 10,
  on_timeout: '',
  // 赋值步骤
  variable: '',
  expression: '',
  // 确认步骤
  message: '',
  options: ['确认', '取消'],
  // 控制步骤
  control_type: 'if',
  condition: '',
  steps: []
})

const formRef = ref()

// 方法
const handleTypeChange = () => {
  // 重置特定字段
  stepForm.command = ''
  stepForm.pattern = ''
  stepForm.variable = ''
  stepForm.expression = ''
  stepForm.message = ''
  stepForm.condition = ''
}

const addOption = () => {
  stepForm.options.push('新选项')
}

const removeOption = (index: number) => {
  if (stepForm.options.length > 1) {
    stepForm.options.splice(index, 1)
  }
}

const generateStepId = () => {
  return `step_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

const handleSave = () => {
  // 验证必填字段
  if (!stepForm.name.trim()) {
    ElMessage.error('请输入步骤名称')
    return
  }

  if (!stepForm.type) {
    ElMessage.error('请选择步骤类型')
    return
  }

  // 根据步骤类型验证特定字段
  if (stepForm.type === 'send' && !stepForm.command.trim()) {
    ElMessage.error('请输入发送指令')
    return
  }

  if (stepForm.type === 'expect' && !stepForm.pattern.trim()) {
    ElMessage.error('请输入匹配模式')
    return
  }

  if (stepForm.type === 'assign') {
    if (!stepForm.variable.trim()) {
      ElMessage.error('请输入变量名')
      return
    }
    if (!stepForm.expression.trim()) {
      ElMessage.error('请输入赋值表达式')
      return
    }
  }

  if (stepForm.type === 'confirm' && !stepForm.message.trim()) {
    ElMessage.error('请输入确认消息')
    return
  }

  if (stepForm.type === 'control') {
    if (['if', 'loop'].includes(stepForm.control_type) && !stepForm.condition.trim()) {
      ElMessage.error('请输入条件表达式')
      return
    }
  }

  // 构建步骤对象
  const step: WorkflowStep = {
    id: stepForm.id || generateStepId(),
    name: stepForm.name,
    type: stepForm.type,
    description: stepForm.description
  }

  // 添加特定字段
  if (stepForm.type === 'send') {
    Object.assign(step, {
      command: stepForm.command,
      port: stepForm.port || undefined,
      delay: stepForm.delay || 0
    })
  } else if (stepForm.type === 'expect') {
    Object.assign(step, {
      expect_type: stepForm.expect_type,
      pattern: stepForm.pattern,
      timeout: stepForm.timeout,
      on_timeout: stepForm.on_timeout || undefined
    })
  } else if (stepForm.type === 'assign') {
    Object.assign(step, {
      variable: stepForm.variable,
      expression: stepForm.expression
    })
  } else if (stepForm.type === 'confirm') {
    Object.assign(step, {
      message: stepForm.message,
      options: stepForm.options,
      timeout: stepForm.timeout || undefined
    })
  } else if (stepForm.type === 'control') {
    Object.assign(step, {
      control_type: stepForm.control_type,
      condition: stepForm.condition || undefined,
      steps: stepForm.steps || []
    })
  }

  emit('save', step)
}

// 初始化
onMounted(() => {
  if (props.step) {
    // 编辑模式，加载现有步骤数据
    Object.assign(stepForm, props.step)
    
    // 确保options是数组
    if (stepForm.type === 'confirm' && !Array.isArray(stepForm.options)) {
      stepForm.options = ['确认', '取消']
    }
  } else {
    // 新建模式，生成新ID
    stepForm.id = generateStepId()
  }
})
</script>

<style scoped>
.step-editor {
  padding: 20px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--el-border-color);
}

.options-editor {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.option-item {
  display: flex;
  gap: 10px;
  align-items: center;
}

:deep(.el-textarea__inner) {
  font-family: 'Courier New', monospace;
  font-size: 13px;
}
</style>