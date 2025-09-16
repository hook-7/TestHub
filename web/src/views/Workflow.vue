<template>
  <div class="workflow-container">
    <div class="page-content">
      <el-card class="content-card">
        <template #header>
          <div class="card-header">
            <h3 class="page-title">工作流执行</h3>
            <p class="page-description">输入MAC地址，系统将自动遍历执行预设命令</p>
          </div>
        </template>
        
        <div class="workflow-content">
          <!-- 导出按钮区域 -->
          <div class="export-section">
            <el-button 
              type="success" 
              size="default"
              @click="exportAllReports"
              :loading="isExporting"
              class="export-all-btn"
            >
              <el-icon><Download /></el-icon>
              导出全部测试结果
            </el-button>
          </div>

          <!-- 加载状态提示 -->
          <div v-if="isLoadingCommands" class="loading-section">
            <el-alert
              title="正在加载测试命令..."
              type="info"
              :closable="false"
              show-icon
            >
              <template #default>
                <div style="display: flex; align-items: center; gap: 8px;">
                  <el-icon class="is-loading"><Loading /></el-icon>
                  从服务器加载测试命令配置
                </div>
              </template>
            </el-alert>
          </div>

          <!-- 无命令提示 -->
          <div v-else-if="cmds.length === 0" class="empty-section">
            <el-alert
              title="暂无测试命令"
              type="warning"
              :closable="false"
              show-icon
            >
              <template #default>
                请先在"串口通信"页面添加测试命令，或检查服务器连接状态
              </template>
            </el-alert>
          </div>

          <!-- 串口连接状态提示 -->
          <div v-else-if="!isSerialConnected" class="serial-status-section">
            <el-alert
              title="串口未连接"
              type="warning"
              :closable="false"
              show-icon
            >
              <template #default>
                <div style="display: flex; align-items: center; justify-content: space-between;">
                  <span>请先在"串口配置"页面连接串口设备，然后才能执行工作流</span>
                  <el-button 
                    type="primary" 
                    size="small" 
                    @click="refreshSerialStatus"
                    style="margin-left: 16px;"
                  >
                    <el-icon><RefreshLeft /></el-icon>
                    刷新状态
                  </el-button>
                </div>
              </template>
            </el-alert>
          </div>

          <!-- MAC地址输入区域 -->
          <div v-else class="input-section">
            <el-form :model="form" label-width="120px" class="mac-form">
              <el-form-item label="MAC地址" required>
                <el-input
                  ref="macAddressInputRef"
                  v-model="form.macAddress"
                  placeholder="请输入MAC地址，如：026501123456 或 mac:026501123456"
                  clearable
                  :disabled="isExecuting"
                  class="mac-input"
                  @input="handleMacInput"
                  @keydown.enter.prevent
                >
                  <template #prepend>
                    <el-icon><Link /></el-icon>
                  </template>
                </el-input>
              </el-form-item>
              
              <el-form-item label="自动执行">
                <el-switch
                  v-model="autoExecuteEnabled"
                  active-text="启用"
                  inactive-text="禁用"
                  :disabled="isExecuting"
                />
                <span class="form-help-text">
                  启用后，输入mac:格式的地址将自动执行工作流
                </span>
              </el-form-item>
              
              <!-- 重试配置选项 -->
              <el-form-item label="重试配置">
                <div class="retry-config">
                  <el-input-number
                    v-model="retryConfig.maxRetries"
                    :min="1"
                    :max="10"
                    :disabled="isExecuting"
                    controls-position="right"
                    size="small"
                    style="width: 120px;"
                  />
                  <span class="config-label">最大重试次数</span>
                  
                  <el-input-number
                    v-model="retryConfig.responseTimeout"
                    :min="1000"
                    :max="30000"
                    :step="1000"
                    :disabled="isExecuting"
                    controls-position="right"
                    size="small"
                    style="width: 120px; margin-left: 20px;"
                  />
                  <span class="config-label">响应超时(ms)</span>
                </div>
              </el-form-item>
              
              <el-form-item>
                <el-button 
                  type="primary" 
                  :loading="isExecuting"
                  :disabled="!form.macAddress || isExecuting || !isSerialConnected"
                  @click="executeWorkflow"
                  class="execute-btn"
                >
                  <el-icon><VideoPlay /></el-icon>
                  {{ isExecuting ? '执行中...' : '开始执行工作流' }}
                </el-button>
                
                <el-button 
                  v-if="isExecuting"
                  type="danger"
                  @click="stopExecution"
                  class="stop-btn"
                >
                  <el-icon><VideoPause /></el-icon>
                  停止执行
                </el-button>
              </el-form-item>
            </el-form>
          </div>

          <!-- 执行进度区域 -->
          <div v-if="isExecuting || executionLogs.length > 0" class="progress-section">
            <el-divider content-position="left">
              <span class="divider-text">执行进度</span>
            </el-divider>
            
            <div class="progress-content">
              <el-progress 
                :percentage="progressPercentage" 
                :status="progressStatus"
                :stroke-width="8"
                class="progress-bar"
              />
              
              <div class="progress-info">
                <span class="current-step">{{ currentStepText }}</span>
                <span class="step-count">{{ currentStepIndex + 1 }} / {{ cmds.length }}</span>
              </div>
            </div>
          </div>

          <!-- 测试结果摘要区域 -->
          <div v-if="testResult" class="test-result-section">
            <el-divider content-position="left">
              <span class="divider-text" :class="getResultStatusClass()">
                {{ getResultStatusText() }}
              </span>
            </el-divider>
            
            <div class="test-result-summary" :class="getResultStatusClass()">
              <div class="summary-cards">
                <div class="summary-card total">
                  <div class="card-number">{{ testResult.totalTests }}</div>
                  <div class="card-label">总测试数</div>
                </div>
                <div class="summary-card passed">
                  <div class="card-number">{{ testResult.passedTests }}</div>
                  <div class="card-label">通过</div>
                </div>
                <div class="summary-card failed">
                  <div class="card-number">{{ testResult.failedTests }}</div>
                  <div class="card-label">失败</div>
                </div>
                <div class="summary-card skipped">
                  <div class="card-number">{{ testResult.skippedTests }}</div>
                  <div class="card-label">跳过</div>
                </div>
              </div>
              
              <div class="test-details">
                <div class="detail-item">
                  <strong>MAC地址:</strong> {{ testResult.macAddress }}
                </div>
                <div class="detail-item">
                  <strong>开始时间:</strong> {{ new Date(testResult.startTime).toLocaleString() }}
                </div>
                <div v-if="testResult.endTime" class="detail-item">
                  <strong>结束时间:</strong> {{ new Date(testResult.endTime).toLocaleString() }}
                </div>
                <div v-if="testResult.endTime" class="detail-item">
                  <strong>耗时:</strong> {{ ((testResult.endTime - testResult.startTime) / 1000).toFixed(1) }}秒
                </div>
              </div>
            </div>
          </div>

          <!-- 执行日志区域 -->
          <div v-if="executionLogs.length > 0" class="logs-section">
            <el-divider content-position="left">
              <span class="divider-text">执行日志</span>
            </el-divider>
            
            <div class="logs-container">
              <div 
                v-for="(log, index) in executionLogs" 
                :key="index"
                class="log-item"
                :class="log.status"
              >
                <div class="log-header">
                  <el-icon class="log-icon">
                    <component :is="getLogIcon(log.status)" />
                  </el-icon>
                  <span class="log-name">{{ log.name }}</span>
                  <span class="log-time">{{ formatTime(log.timestamp) }}</span>
                </div>
                <div class="log-content">
                  <div class="log-command">
                    <strong>命令:</strong> {{ log.command }}
                  </div>
                  <div v-if="log.expectedResponse" class="log-expected">
                    <strong>期望响应:</strong> {{ log.expectedResponse }}
                  </div>
                  <div v-if="log.response" class="log-response">
                    <strong>实际响应:</strong> {{ log.response }}
                  </div>
                  <div v-if="log.error" class="log-error">
                    <strong>错误:</strong> {{ log.error }}
                  </div>
                  <div v-if="log.userChoice !== undefined" class="log-user-choice">
                    <strong>用户选择:</strong> 
                    <span :class="log.userChoice ? 'choice-success' : 'choice-failure'">
                      {{ log.userChoice ? '测试成功' : '测试失败' }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-card>

          <!-- 写入SN卡片 -->
          <div v-if="cmds.length > 0" class="sn-card-section">
            <el-card class="sn-card" shadow="hover">
              <template #header>
                <div class="sn-card-header">
                  <div class="sn-header-content">
                    <el-icon class="sn-icon"><Edit /></el-icon>
                    <div class="sn-title-section">
                      <h3 class="sn-title">写入SN序列号</h3>
                      <p class="sn-description">输入SN序列号，系统将自动写入设备</p>
                    </div>
                  </div>
                </div>
              </template>
              
              <div class="sn-content">
                <el-form :model="snForm" label-width="120px" class="sn-form">
                  <el-form-item label="SN序列号" required>
                    <el-input
                      v-model="snForm.serialNumber"
                      placeholder="请输入SN序列号，如：25990000001 或 S/N:25990000001MAC:0265010002BC"
                      clearable
                      :disabled="isExecuting"
                      class="sn-input"
                      maxlength="100"
                      show-word-limit
                      @input="handleSNInput"
                      @keydown.enter.prevent
                    >
                      <template #prepend>
                        <el-icon><Key /></el-icon>
                      </template>
                    </el-input>
                  </el-form-item>
                  
                  <el-form-item>
                    <div class="sn-button-group">
                      <el-button 
                        type="success" 
                        :loading="isWritingSN"
                        :disabled="!snForm.serialNumber || isExecuting || !isSerialConnected"
                        @click="writeSerialNumber"
                        class="write-sn-btn"
                        size="large"
                      >
                        <el-icon><Edit /></el-icon>
                        {{ isWritingSN ? '写入中...' : '写入SN序列号' }}
                      </el-button>
                      
                      <el-button 
                        v-if="snForm.serialNumber"
                        type="info"
                        @click="snForm.serialNumber = ''"
                        class="clear-sn-btn"
                        size="large"
                        plain
                      >
                        <el-icon><RefreshLeft /></el-icon>
                        清空
                      </el-button>
                    </div>
                  </el-form-item>
                </el-form>
              </div>
            </el-card>
          </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Link, 
  VideoPlay, 
  VideoPause, 
  Check, 
  Close, 
  Warning, 
  Loading,
  Clock,
  Edit,
  Key,
  RefreshLeft,
  Download
} from '@element-plus/icons-vue'
import { webSerialService } from '@/services/webSerial'
import { useConnectionStore } from '@/stores/connection'
import { useCommunicationStore } from '@/stores/communication'
import { getAllCommands, type SavedCommand } from '@/api/commands'
import { testResultsAPI, type SaveTestResultRequest } from '@/api/testResults'
import router from '@/router'

// 连接store
const connectionStore = useConnectionStore()
// 通信store
const communicationStore = useCommunicationStore()

// 命令数据 - 从常用命令接口动态获取
const cmds = ref<SavedCommand[]>([])

// 表单数据
const form = ref({
  macAddress: ''
})

// 自动执行设置
const autoExecuteEnabled = ref(true)

// SN表单数据
const snForm = ref({
  serialNumber: ''
})

// 重试配置
const retryConfig = ref({
  maxRetries: 3,        // 最大重试次数
  responseTimeout: 5000 // 响应超时时间(ms)
})

// 加载状态
const isLoadingCommands = ref(false)

// SN写入状态
const isWritingSN = ref(false)

// 导出状态
const isExporting = ref(false)

// 执行状态
const isExecuting = ref(false)
const currentStepIndex = ref(-1)
const executionLogs = ref<ExecutionLog[]>([])
const shouldStop = ref(false)

// 输入框引用
const macAddressInputRef = ref()

// 测试结果状态
const testResult = ref<TestResult | null>(null)

// 执行日志接口
interface ExecutionLog {
  name: string
  command: string
  response?: string
  expectedResponse?: string // 期望的返回值
  error?: string
  status: 'pending' | 'running' | 'success' | 'error' | 'skipped'
  timestamp: number
  userChoice?: boolean // 用户选择结果，仅在有通知时使用
}

// 测试结果接口
interface TestResult {
  macAddress: string
  testItems: TestItemResult[]
  startTime: number
  endTime?: number
  totalTests: number
  passedTests: number
  failedTests: number
  skippedTests: number
}

// 单个测试项结果接口
interface TestItemResult {
  id: string
  name: string
  command: string
  expectedResponse: string
  actualResponse?: string
  isOk: boolean
  reason: string // 'expected_match' | 'user_confirmed' | 'user_rejected' | 'error' | 'skipped'
  timestamp: number
  hasNotification: boolean
  userChoice?: boolean // 用户选择结果，仅在有通知时使用
}

// 计算属性
const isSerialConnected = computed(() => {
  return connectionStore.isConnected
})

const progressPercentage = computed(() => {
  if (cmds.value.length === 0) return 0
  const percentage = Math.round(((currentStepIndex.value + 1) / cmds.value.length) * 100)
  return Math.min(percentage, 100) // 确保不超过100%
})

const progressStatus = computed(() => {
  if (executionLogs.value.some(log => log.status === 'error')) return 'exception'
  if (currentStepIndex.value >= cmds.value.length - 1 && !isExecuting.value) return 'success'
  return '' // 默认状态，不使用'active'
})

const currentStepText = computed(() => {
  if (currentStepIndex.value < 0) return '准备开始'
  if (currentStepIndex.value >= cmds.value.length) return '执行完成'
  return `正在执行: ${cmds.value[currentStepIndex.value].name}`
})

// 方法
const getLogIcon = (status: string) => {
  switch (status) {
    case 'pending': return Clock
    case 'running': return Loading
    case 'success': return Check
    case 'error': return Close
    case 'skipped': return Warning
    default: return Clock
  }
}

const formatTime = (timestamp: number) => {
  return new Date(timestamp).toLocaleTimeString()
}

// 加载常用命令
const loadCommands = async () => {
  try {
    isLoadingCommands.value = true
    const response = await getAllCommands()
    cmds.value = response.commands
    console.log(`已加载 ${response.commands.length} 个测试命令`)
  } catch (error) {
    console.error('加载命令失败:', error)
    ElMessage.error('加载测试命令失败: ' + (error instanceof Error ? error.message : '未知错误'))
  } finally {
    isLoadingCommands.value = false
  }
}

// 替换命令中的MAC地址占位符
const replaceMacAddress = (command: string, macAddress: string) => {
  // 先截断到第一个"%"符号
  const truncatedCommand = command.split('%')[0]
  // 然后替换MAC地址占位符
  return truncatedCommand.replace(/\$\{mac\}/g, macAddress)
}

// 期望响应匹配工具函数
const matchesExpectedResponse = (actualResponse: string, expectedResponse: string): boolean => {
  if (!actualResponse || !expectedResponse) return false
  
  // 标准化处理：去除首尾空白，统一换行符
  const normalizedActual = actualResponse.trim().replace(/\r\n/g, '\n').replace(/\r/g, '\n')
  const normalizedExpected = expectedResponse.trim().replace(/\r\n/g, '\n').replace(/\r/g, '\n')
  
  // 精确匹配
  if (normalizedActual === normalizedExpected) return true
  
  // 包含匹配
  if (normalizedActual.includes(normalizedExpected)) return true
  
  return false
}

// 正则表达式匹配函数
const matchesExpectedResponseRegex = (actualResponse: string, expectedResponse: string): boolean => {
  if (!actualResponse || !expectedResponse) return false
  
  try {
    // 标准化处理
    const normalizedActual = actualResponse.trim().replace(/\r\n/g, '\n').replace(/\r/g, '\n')
    const normalizedExpected = expectedResponse.trim().replace(/\r\n/g, '\n').replace(/\r/g, '\n')
    
    // 尝试作为正则表达式匹配
    const regex = new RegExp(normalizedExpected, 'i') // 不区分大小写
    return regex.test(normalizedActual)
  } catch (error) {
    // 如果正则表达式无效，返回false
    console.warn('正则表达式匹配失败:', error)
    return false
  }
}

// 带重试机制的命令发送和响应等待
const sendCommandWithRetryAndWait = async (command: string, cmd: SavedCommand, maxRetries: number = 3, responseTimeout: number = 5000): Promise<any> => {
  let lastError: Error | null = null
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      console.log(`发送命令尝试 ${attempt}/${maxRetries}: ${command}`)
      
      // 检查串口连接状态
      if (!connectionStore.isConnected) {
        throw new Error('没有连接的串口')
      }
      
      // 检查特定串口是否连接
      if (cmd.target_serial_id && !webSerialService.isSerialConnected(cmd.target_serial_id)) {
        throw new Error(`串口 ${cmd.target_serial_id} 未连接`)
      }

      // 使用Web Serial API发送命令并等待响应
      const response = await webSerialService.sendCommandAndWaitResponse(
        command, 
        responseTimeout,
        cmd.target_serial_id
      )
      
      if (response && response.received_data) {
        console.log(`命令 ${command} 发送成功并收到响应 (尝试 ${attempt})`)
        
        // 检查期望响应匹配
        if (cmd.expected_response && cmd.expected_response.trim()) {
          const matchesExpected = matchesExpectedResponse(response.received_data, cmd.expected_response) || 
                                 matchesExpectedResponseRegex(response.received_data, cmd.expected_response)
          
          if (matchesExpected) {
            console.log('期望响应匹配成功')
            return {
              ...response,
              matchesExpected: true
            }
          } else {
            console.warn(`期望响应匹配失败 (尝试 ${attempt}/${maxRetries})`)
            console.warn('期望:', cmd.expected_response)
            console.warn('实际:', response.received_data)
            
            // 如果不是最后一次尝试，继续重试
            if (attempt < maxRetries) {
              lastError = new Error(`期望响应匹配失败: 期望 "${cmd.expected_response}", 实际 "${response.received_data}"`)
              continue
            } else {
              // 最后一次尝试，返回不匹配的结果
              return {
                ...response,
                matchesExpected: false
              }
            }
          }
        } else {
          // 没有期望响应，只要有响应就算成功
          return {
            ...response,
            matchesExpected: true
          }
        }
      } else {
        // 没有收到响应，继续重试
        console.warn(`命令发送后 ${responseTimeout}ms 内未收到响应 (尝试 ${attempt}/${maxRetries})`)
        lastError = new Error(`命令发送后 ${responseTimeout}ms 内未收到响应`)
      }
      
    } catch (error) {
      lastError = error as Error
      console.warn(`命令发送失败 (尝试 ${attempt}/${maxRetries}):`, error)
    }
    
    // 如果不是最后一次尝试，等待后继续重试
    if (attempt < maxRetries) {
      console.log(`等待 1 秒后重试...`)
      await new Promise(resolve => setTimeout(resolve, 1000))
    }
  }

  // 所有重试都失败了
  console.error(`命令发送失败，已重试 ${maxRetries} 次:`, lastError)
  throw lastError || new Error('命令发送失败')
}

// 显示通知对话框
const showNotificationDialog = async (description: string): Promise<boolean> => {
  try {
    await ElMessageBox.confirm(
      description,
      '测试结果确认',
      {
        confirmButtonText: '测试成功',
        cancelButtonText: '测试失败',
        type: 'warning',
        showClose: false,
        closeOnClickModal: false,
        closeOnPressEscape: false,
        distinguishCancelAndClose: true
      }
    )
    return true // 用户选择"测试成功"
  } catch {
    return false // 用户选择"测试失败"
  }
}


// 执行单个命令
const executeCommand = async (cmd: SavedCommand): Promise<ExecutionLog> => {
  const log: ExecutionLog = {
    name: cmd.name,
    command: cmd.command,
    expectedResponse: cmd.expected_response || '', // 添加期望返回值
    status: 'running',
    timestamp: Date.now()
  }

  let userChoice: boolean | undefined = undefined

  try {
    // 替换MAC地址
    const finalCommand = replaceMacAddress(cmd.command, form.value.macAddress)
    console.log('finalCommand', finalCommand);
    
    // 使用带重试机制的命令发送和响应等待
    const response = await sendCommandWithRetryAndWait(finalCommand, cmd, retryConfig.value.maxRetries, retryConfig.value.responseTimeout)
    
    // 手动添加发送日志到通信store
    communicationStore.addLog({
      type: 'at',
      direction: 'sent',
      data: finalCommand,
      description: `发送指令 (串口#${cmd.target_serial_id})`,
      success: true,
      serial_id: cmd.target_serial_id
    })
    
    // 手动添加接收日志到通信store
    if (response.received_data && response.received_data.trim()) {
      communicationStore.addLog({
        type: 'at',
        direction: 'received',
        data: response.received_data,
        description: `接收响应 (串口#${cmd.target_serial_id})`,
        success: true,
        serial_id: cmd.target_serial_id
      })
    }
    
    log.response = response.received_data
    log.status = 'success'
    
    // 检查是否匹配期望响应
    if (response.matchesExpected === false) {
      console.warn('响应不匹配期望值:', {
        expected: cmd.expected_response,
        actual: response.received_data
      })
    } else {
      console.log('响应匹配期望值:', {
        expected: cmd.expected_response,
        actual: response.received_data
      })
    }
    
  } catch (error) {
    log.error = error instanceof Error ? error.message : '未知错误'
    log.status = 'error'
  }
      // 如果需要显示通知，先弹出确认对话框
  if (cmd.show_notification && cmd.description) {
      userChoice = await showNotificationDialog(cmd.description)
      // 用户的选择直接决定测试结果，不再跳过
      // 这里我们继续执行命令，但会在测试结果中记录用户的选择
    }

  // 将用户选择结果存储在log中，供后续使用
  ;(log as any).userChoice = userChoice

  return log
}

// 创建测试项结果
const createTestItemResult = (cmd: SavedCommand, log: ExecutionLog): TestItemResult => {
  const actualResponse = log.response || ''
  const expectedResponse = cmd.expected_response || ''
  
  let isOk = false
  let reason = ''
  let userChoice: boolean | undefined = undefined

  if (log.status === 'skipped') {
    isOk = false
    reason = 'skipped'
  } else if (log.status === 'error') {
    isOk = false
    reason = 'error'
  } else if (cmd.show_notification && cmd.description) {
    // 有通知的测试项，根据用户选择决定成功/失败
    userChoice = (log as any).userChoice
    if (userChoice !== undefined) {
      isOk = userChoice
      reason = userChoice ? 'user_confirmed_success' : 'user_confirmed_failure'
    } else {
      // 如果没有获取到用户选择，默认为失败
      isOk = false
      reason = 'user_choice_missing'
    }
  } else {
    // 没有通知的测试项，比较预期响应
    if (expectedResponse) {
      // 使用与sendCommandWithRetryAndWait相同的匹配逻辑
      isOk = matchesExpectedResponse(actualResponse, expectedResponse) || 
             matchesExpectedResponseRegex(actualResponse, expectedResponse)
      reason = isOk ? 'expected_match' : 'expected_mismatch'
      console.log('期望响应检查:', {
        expected: expectedResponse,
        actual: actualResponse,
        isOk: isOk,
        reason: reason
      })
    } else {
      // 没有预期响应，只要有响应就算OK
      isOk = actualResponse.length > 0
      reason = isOk ? 'has_response' : 'no_response'
      console.log('无期望响应检查:', {
        actual: actualResponse,
        isOk: isOk,
        reason: reason
      })
    }
  }

  return {
    id: cmd.id,
    name: cmd.name,
    command: cmd.command,
    expectedResponse,
    actualResponse,
    isOk,
    reason,
    timestamp: log.timestamp,
    hasNotification: cmd.show_notification || false,
    userChoice
  }
}

// 更新测试结果统计
const updateTestResultStats = (testResult: TestResult) => {
  testResult.passedTests = testResult.testItems.filter(item => item.isOk).length
  testResult.failedTests = testResult.testItems.filter(item => !item.isOk && item.reason !== 'skipped').length
  testResult.skippedTests = testResult.testItems.filter(item => item.reason === 'skipped').length
}

// 保存测试结果到后端
const saveTestResultToBackend = async () => {
  if (!testResult.value) return
  
  try {
    // 转换测试项结果为API格式
    const testItems = testResult.value.testItems.map(item => ({
      id: item.id,
      name: item.name,
      command: item.command,
      expected_response: item.expectedResponse,
      actual_response: item.actualResponse,
      is_ok: item.isOk,
      reason: item.reason,
      timestamp: item.timestamp,
      has_notification: item.hasNotification,
      user_choice: item.userChoice
    }))
    
    // 构建保存请求
    const saveRequest: SaveTestResultRequest = {
      mac_address: testResult.value.macAddress,
      test_items: testItems,
      start_time: testResult.value.startTime,
      end_time: testResult.value.endTime,
      total_tests: testResult.value.totalTests,
      passed_tests: testResult.value.passedTests,
      failed_tests: testResult.value.failedTests,
      skipped_tests: testResult.value.skippedTests,
      operator: '操作员', 
      workstation: '工位1', 
      device_id: '设备001' 
    }
    
    // 调用API保存
    await testResultsAPI.saveTestResult(saveRequest)
    console.log('测试结果已保存到后端')
    
  } catch (error) {
    console.error('保存测试结果失败:', error)
    ElMessage.error('保存测试结果失败: ' + (error instanceof Error ? error.message : '未知错误'))
  }
}

// 检查串口连接状态
const checkSerialConnection = () => {
  if (!connectionStore.isConnected) {
    ElMessage.error('没有连接的串口，请先在串口配置页面连接串口设备')
    return false
  }
  return true
}

// 刷新串口连接状态
const refreshSerialStatus = async () => {
  try {
    // 使用 connectionStore 检查状态
    await connectionStore.checkStatus()
    const connectedSerials = connectionStore.connectedSerials
    console.log('当前连接的串口:', connectedSerials)
    if (connectedSerials.length > 0) {
      ElMessage.success(`检测到 ${connectedSerials.length} 个已连接的串口`)
    } else {
      ElMessage.warning('没有检测到已连接的串口')
    }
  } catch (error) {
    console.error('刷新串口状态失败:', error)
    ElMessage.error('刷新串口状态失败')
  }
}

// 执行工作流
const executeWorkflow = async () => {
  if (!form.value.macAddress.trim()) {
    ElMessage.warning('请输入MAC地址')
    return
  }

  // 检查串口连接状态
  if (!checkSerialConnection()) {
    return
  }

  // 重置状态
  isExecuting.value = true
  currentStepIndex.value = -1
  executionLogs.value = []
  shouldStop.value = false

  // 初始化测试结果
  testResult.value = {
    macAddress: form.value.macAddress,
    testItems: [],
    startTime: Date.now(),
    totalTests: cmds.value.length,
    passedTests: 0,
    failedTests: 0,
    skippedTests: 0
  }

  try {
    // 遍历执行命令
    for (let i = 0; i < cmds.value.length; i++) {
      // 检查是否需要停止
      if (shouldStop.value) {
        ElMessage.info('执行已停止')
        break
      }

      currentStepIndex.value = i
      const cmd = cmds.value[i]
      
      // 创建日志条目
      const log = await executeCommand(cmd)
      executionLogs.value.push(log)

      // 创建测试项结果
      const testItemResult = createTestItemResult(cmd, log)
      testResult.value.testItems.push(testItemResult)

      // 如果命令执行失败且不是用户取消，可以选择是否继续
      if (log.status === 'error') {
        const continueExecution = await ElMessageBox.confirm(
          `命令 "${cmd.name}" 执行失败，是否继续执行后续命令？`,
          '执行错误',
          {
            confirmButtonText: '继续',
            cancelButtonText: '停止',
            type: 'warning'
          }
        ).catch(() => false)
        
        if (!continueExecution) {
          break
        }
      }

      // 添加延迟，避免命令执行过快
      await new Promise(resolve => setTimeout(resolve, 100))
    }

    // 执行完成
    currentStepIndex.value = cmds.value.length - 1 
    testResult.value.endTime = Date.now()
    updateTestResultStats(testResult.value)
    
    ElMessage.success('工作流执行完成')
    
    // 保存测试结果到后端
    await saveTestResultToBackend()
    
    // 显示测试结果摘要
    await showTestResultSummary()
    console.log(testResult.value);
    
    // 清空MAC地址
    form.value.macAddress = ""
    
    
  } catch (error) {
    ElMessage.error('工作流执行失败: ' + (error instanceof Error ? error.message : '未知错误'))
  } finally {
    isExecuting.value = false
  }
}

// 显示测试结果摘要
const showTestResultSummary = async () => {
  if (!testResult.value) return
  
  const { totalTests, passedTests, failedTests, skippedTests } = testResult.value
  const duration = testResult.value.endTime ? 
    ((testResult.value.endTime - testResult.value.startTime) / 1000).toFixed(1) : 0
  
  // 判断测试结果状态
  const hasFailures = failedTests > 0
  const isSuccess = !hasFailures && passedTests > 0
  
  const resultType = isSuccess ? 'success' : 'error'
  const resultTitle = isSuccess ? '测试成功' : '测试失败'
  const resultIcon = isSuccess ? '✅' : '❌'
  
  try {
    await ElMessageBox.alert(
      `${resultIcon} ${resultTitle}！<br/><br/>` +
      `MAC地址: ${testResult.value.macAddress}<br/>` +
      `总测试数: ${totalTests}<br/>` +
      `通过: ${passedTests}<br/>` +
      `失败: ${failedTests}<br/>` +
      `跳过: ${skippedTests}<br/>` +
      `耗时: ${duration}秒`,
      resultTitle,
      {
        confirmButtonText: '确定',
        type: resultType,
        dangerouslyUseHTMLString: true
      }
    )
    
    // 用户点击确定后，聚焦到MAC地址输入框
    setTimeout(() => {
      if (macAddressInputRef.value) {
        macAddressInputRef.value.focus()
      }
    }, 100)
  } catch (error) {
    // 用户可能按ESC或其他方式关闭对话框，也聚焦到输入框
    setTimeout(() => {
      if (macAddressInputRef.value) {
        macAddressInputRef.value.focus()
      }
    }, 100)
  }
}

// 停止执行
const stopExecution = () => {
  shouldStop.value = true
  ElMessage.info('正在停止执行...')
}

// 写入SN序列号
const writeSerialNumber = async () => {
  if (!snForm.value.serialNumber.trim()) {
    ElMessage.warning('请输入SN序列号')
    return
  }

  // 检查串口连接状态
  if (!checkSerialConnection()) {
    return
  }

  try {
    isWritingSN.value = true
    
    // 检查并提取SN，如果输入包含S/N:格式（忽略大小写）
    let actualSN = snForm.value.serialNumber
    if (actualSN.toLowerCase().includes('s/n:')) {
      console.log('Extracting SN from S/N: format')
      const snStart = actualSN.toLowerCase().indexOf('s/n:') + 4
      const extractedSN = actualSN.substring(snStart, snStart + 11)
      
      if (/^\d{11}$/.test(extractedSN)) {
        actualSN = extractedSN
        console.log('Extracted SN:', actualSN)
        // 更新输入框显示提取的SN
        snForm.value.serialNumber = actualSN
      } else {
        console.log('Invalid SN format, using original value')
      }
    }
    
    // 将SN转换为小端序的16进制字符串，然后每个字节+33
    const snToLittleEndian = (sn: string) => {
      // 确保SN长度为12位（6字节）
      const paddedSN = sn.padStart(12, '0')
      const bytes = []
      
      // 先按字节分割
      for (let i = 0; i < paddedSN.length; i += 2) {
        const byteValue = parseInt(paddedSN.substr(i, 2), 16)
        bytes.push(byteValue)
      }
      
      // 转换为小端序（字节顺序反转）
      bytes.reverse()
      
      // 然后每个字节+33（0x33）
      const adjustedBytes = bytes.map(byteValue => {
        const adjustedValue = (byteValue + 0x33) & 0xFF
        return adjustedValue.toString(16).padStart(2, '0').toUpperCase()
      })
      
      return adjustedBytes.join('')
    }
    
    // 计算校验和 - 和取低位字节
    const calculateChecksum = (hexString: string) => {
      let sum = 0
      for (let i = 0; i < hexString.length; i += 2) {
        sum += parseInt(hexString.substr(i, 2), 16)
      }
      // 和取低位字节（只取最低8位）
      return (sum & 0xFF).toString(16).padStart(2, '0').toUpperCase()
    }
    
    // 构建协议数据
    const snLittleEndian = snToLittleEndian(actualSN)
    const protocolData = `02AAAAAAAAAAAA68040C34C033444444${snLittleEndian}`
    const checksum = calculateChecksum(protocolData)
    const finalCommand = protocolData + checksum + '03'
    console.log(finalCommand);
    
    // 检查串口连接状态
    if (!webSerialService.isSerialConnected(1)) {
      throw new Error('串口 1 未连接')
    }

    // 发送16进制命令到串口（假设使用串口ID 1）
    await webSerialService.sendRawData(finalCommand, 1)
    
    // 手动添加发送日志到通信store
    communicationStore.addLog({
      type: 'raw',
      direction: 'sent',
      data: finalCommand,
      description: `发送原始数据 (串口#1)`,
      success: true,
      serial_id: 1
    })
    
    // 等待响应
    const receiveResponse = await webSerialService.receiveData(3000, 1)
    
    // 手动添加接收日志到通信store
    if (receiveResponse.received_data && receiveResponse.received_data.trim()) {
      communicationStore.addLog({
        type: 'raw',
        direction: 'received',
        data: receiveResponse.received_data,
        description: `接收响应 (串口#1)`,
        success: true,
        serial_id: 1
      })
    }
    verify_response_sn(receiveResponse.received_data, actualSN)
    if(verify_response_sn(receiveResponse.received_data, actualSN)){
      ElMessage.success(`SN序列号写入成功: ${actualSN}`)
    }else{
      ElMessage.error(`SN序列号写入失败: ${actualSN}`)
    }
    console.log('SN写入响应:', receiveResponse.received_data)
    
    
  } catch (error) {
    console.error('写入SN失败:', error)
    ElMessage.error('写入SN失败: ' + (error instanceof Error ? error.message : '未知错误'))
  } finally {
    isWritingSN.value = false
  }
}


const verify_response_sn = (hex_sn: string, input_sn: string) => {
  const paddedSN = input_sn.padStart(12, '0')
  const hex_sn_header = hex_sn.substring(0, hex_sn.length - 4)
  const sum_hex = hex_sn.substring(hex_sn.length - 4)
  const sn = hex_sn.substring(2, 14)

  const reversed_sn = reversing_sn(sn)
  const checksum = checksum_sn(hex_sn_header)+"03"
  if(checksum === sum_hex && reversed_sn === paddedSN){
    return true
  }

  return false
}


const reversing_sn = (sn: string) => {
    let reversed_sn = ''
    for (let i = 0; i < sn.length; i += 2) {
        const byte = sn.substring(i, i + 2)
        reversed_sn = byte + reversed_sn
    }
    return reversed_sn
}

const checksum_sn = (hexString: string) => {
    let sum = 0
    for (let i = 0; i < hexString.length; i += 2) {
      sum += parseInt(hexString.substring(i, i + 2), 16)
    }

    return (sum & 0xFF).toString(16).padStart(2, '0').toUpperCase()
  }

// 处理SN输入，检测S/N:格式并自动发送
let snInputTimer: NodeJS.Timeout | null = null
const handleSNInput = (value: string) => {
  console.log('SN input value:', value)
  
  // 清除之前的定时器
  if (snInputTimer) {
    clearTimeout(snInputTimer)
  }
  
  // 检查是否包含 S/N: 格式（忽略大小写）
  if (value.toLowerCase().includes('s/n:')) {
    console.log('Found S/N: pattern')
    
    // 使用防抖，延迟处理避免频繁触发
    snInputTimer = setTimeout(async () => {
      console.log('Processing SN extraction...')
      
      try {
        await writeSerialNumber()
        // 发送完成后清空输入框
        snForm.value.serialNumber = ''
      } catch (error) {
        console.error('自动发送SN失败:', error)
      }
    }, 200) // 缩短防抖时间到200ms
  }
}

// 检查是否可以执行工作流
const canExecuteWorkflow = (): boolean => {
  // 检查是否已经在执行
  if (isExecuting.value) {
    ElMessage.warning('工作流正在执行中，请等待完成')
    return false
  }
  
  // 检查是否有可用的命令
  if (cmds.value.length === 0) {
    ElMessage.warning('没有可用的测试命令')
    return false
  }
  
  // 检查串口连接状态
  if (!connectionStore.isConnected) {
    ElMessage.warning('串口未连接，请先连接串口设备')
    return false
  }
  
  return true
}

// 处理MAC地址输入，检测mac:格式并自动替换
let macInputTimer: NodeJS.Timeout | null = null
const handleMacInput = (value: string) => {
  // 清除之前的定时器
  if (macInputTimer) {
    clearTimeout(macInputTimer)
  }
  
  // 检查是否以 mac: 开头
  if (value.toLowerCase().startsWith('mac:')) {
    // 使用防抖，延迟处理避免频繁触发
    macInputTimer = setTimeout(() => {
      // 提取mac:后面的部分
      const extractedMac = value.replace(/^mac:/i, '')
      // 更新MAC地址值
      form.value.macAddress = extractedMac
      console.log('extractedMac', extractedMac);
      
      // 检查是否可以执行工作流
      if (canExecuteWorkflow()) {
        if (autoExecuteEnabled.value) {
          // 自动执行模式：直接执行
          executeWorkflow()
        } else {
          // 手动确认模式：询问用户
          ElMessageBox.confirm(
            `检测到MAC地址: ${extractedMac}\n是否要自动执行工作流？`,
            '自动执行确认',
            {
              confirmButtonText: '执行',
              cancelButtonText: '稍后',
              type: 'info'
            }
          ).then(() => {
            executeWorkflow()
          }).catch(() => {
            // 用户取消，不做任何操作
          })
        }
      }
    }, 500) // 500ms防抖
  }
}

// 获取测试结果状态文本
const getResultStatusText = () => {
  if (!testResult.value) return '测试结果'
  
  const { passedTests, failedTests } = testResult.value
  const hasFailures = failedTests > 0
  const isSuccess = !hasFailures && passedTests > 0
  
  if (isSuccess) {
    return '✅ 测试成功'
  } else if (hasFailures) {
    return '❌ 测试失败'
  } else {
    return '测试结果'
  }
}

// 获取测试结果状态样式类
const getResultStatusClass = () => {
  if (!testResult.value) return ''
  
  const { passedTests, failedTests } = testResult.value
  const hasFailures = failedTests > 0
  const isSuccess = !hasFailures && passedTests > 0
  
  if (isSuccess) {
    return 'test-success'
  } else if (hasFailures) {
    return 'test-failed'
  } else {
    return ''
  }
}

// 导出所有测试报告
const exportAllReports = async () => {
  try {
    isExporting.value = true
    
    // 获取测试结果数据
    const response = await testResultsAPI.getTestResults({ page_size: 10000 })
    const testResults = response.results
    
    // 生成CSV内容
    const csvContent = generateCSV(testResults)
    
    // 创建Blob并下载，添加BOM以支持Excel正确显示中文
    const BOM = '\uFEFF'
    const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    
    // 生成文件名
    const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-')
    link.download = `test_results_list_${timestamp}.csv`
    
    // 触发下载
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    // 清理URL对象
    window.URL.revokeObjectURL(url)
    
    ElMessage.success(`测试结果导出成功，共导出 ${testResults.length} 条记录`)
    
  } catch (error) {
    console.error('导出测试报告失败:', error)
    ElMessage.error('导出测试报告失败: ' + (error instanceof Error ? error.message : '未知错误'))
  } finally {
    isExporting.value = false
  }
}

// 生成CSV内容
const generateCSV = (data: any[]) => {
  if (!data || data.length === 0) {
    return '测试结果ID,MAC地址,开始时间,结束时间,总测试数,通过数,失败数,跳过数,通过率(%),操作员,工位,设备ID,创建时间,测试状态,耗时(秒)\n暂无数据,,,,,,,,,,,,,数据库中暂无测试结果数据,'
  }
  
  // CSV头部
  const headers = [
    '测试结果ID',
    'MAC地址', 
    '开始时间',
    '结束时间',
    '总测试数',
    '通过数',
    '失败数',
    '跳过数',
    '通过率(%)',
    '操作员',
    '工位',
    '设备ID',
    '创建时间',
    '测试状态',
    '耗时(秒)'
  ]
  
  // 转义CSV字段的函数
  const escapeCSVField = (field: any) => {
    if (field === null || field === undefined) {
      return ''
    }
    const str = String(field)
    // 如果包含逗号、引号或换行符，需要用引号包围并转义引号
    if (str.includes(',') || str.includes('"') || str.includes('\n') || str.includes('\r')) {
      return `"${str.replace(/"/g, '""')}"`
    }
    return str
  }
  
  // 生成CSV行
  const rows = data.map(item => [
    escapeCSVField(item.id),
    escapeCSVField(item.mac_address),
    escapeCSVField(item.start_time ? new Date(item.start_time).toLocaleString('zh-CN') : ''),
    escapeCSVField(item.end_time ? new Date(item.end_time).toLocaleString('zh-CN') : ''),
    escapeCSVField(item.total_tests || 0),
    escapeCSVField(item.passed_tests || 0),
    escapeCSVField(item.failed_tests || 0),
    escapeCSVField(item.skipped_tests || 0),
    escapeCSVField(item.pass_rate || 0),
    escapeCSVField(item.operator),
    escapeCSVField(item.workstation),
    escapeCSVField(item.device_id),
    escapeCSVField(item.created_at ? new Date(item.created_at).toLocaleString('zh-CN') : ''),
    escapeCSVField(item.test_status),
    escapeCSVField(item.duration || 0)
  ])
  
  // 组合CSV内容
  const csvLines = [headers.map(escapeCSVField).join(','), ...rows.map(row => row.join(','))]
  return csvLines.join('\n')
}

// 组件挂载时加载命令和初始化Web Serial API
onMounted(async () => {
  await loadCommands()
  
  if (!connectionStore.isConnected) {
    ElMessage.warning('请先连接串口')
    router.push('/serial-config')
    return
  }
  
  // 自动选择第一个已连接的串口
  if (!connectionStore.selectedSerialId && connectionStore.connectedSerials.length > 0) {
    connectionStore.selectSerial(connectionStore.connectedSerials[0].serial_id)
  }
  

  
  // 初始化Web Serial API（设置数据接收回调）
  try {
    await communicationStore.initializeWebSerial()
    console.log('Web Serial API initialized successfully')
  } catch (error) {
    console.error('Web Serial API初始化失败:', error)
    ElMessage.error('Web Serial API初始化失败')
  }
})

</script>

<style scoped>
.workflow-container {
  height: 100%;
  background: linear-gradient(135deg, #f5f7fa 0%, #f8fafc 100%);
}

.export-section {
  margin-bottom: 20px;
  text-align: center;
  padding: 16px 0;
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
  border-radius: 8px;
  border: 1px solid #bbf7d0;
}

.export-all-btn {
  padding: 12px 32px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 8px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(103, 194, 58, 0.3);
  min-width: 200px;
}

.export-all-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(103, 194, 58, 0.4);
}

.export-all-btn:active {
  transform: translateY(0);
}

.page-content {
  height: 100%;
  padding: 32px;
  overflow: auto;
}

.content-card {
  max-width: 1200px;
  margin: 0 auto;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

/* 卡片头部 */
.card-header {
  text-align: center;
}

/* 加载和空状态样式 */
.loading-section,
.empty-section,
.serial-status-section {
  margin: 20px 0;
  padding: 0 20px;
}

.loading-section .el-alert {
  background: #f0f9ff;
  border: 1px solid #bfdbfe;
}

.empty-section .el-alert {
  background: #fffbeb;
  border: 1px solid #fed7aa;
}

.page-title {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: #1a202c;
}

.page-description {
  margin: 0;
  font-size: 14px;
  color: #64748b;
}

/* 工作流内容 */
.workflow-content {
  padding: 24px;
}

/* 输入区域 */
.input-section {
  margin-bottom: 32px;
}

/* SN卡片区域 */
.sn-card-section {
  margin-top: 32px;
  max-width: 1200px;
  margin-left: auto;
  margin-right: auto;
}

.sn-card {
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  overflow: hidden;
}

.sn-card:hover {
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
}

.sn-card-header {
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
  border-bottom: 1px solid #bbf7d0;
  padding: 0;
}

.sn-header-content {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 24px;
}

.sn-icon {
  color: #16a34a;
  font-size: 24px;
  background: white;
  padding: 12px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(22, 163, 74, 0.15);
}

.sn-title-section {
  flex: 1;
}

.sn-title {
  margin: 0 0 4px 0;
  font-size: 20px;
  font-weight: 600;
  color: #1a202c;
}

.sn-description {
  margin: 0;
  font-size: 14px;
  color: #64748b;
}

.sn-content {
  padding: 24px;
  background: #fafbfc;
}

.sn-form {
  max-width: 600px;
  margin: 0 auto;
}

.sn-input {
  font-family: 'Courier New', monospace;
  font-size: 16px;
  font-weight: 500;
}

.sn-input :deep(.el-input__inner) {
  background: white;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.sn-input :deep(.el-input__inner):focus {
  border-color: #67c23a;
  box-shadow: 0 0 0 3px rgba(103, 194, 58, 0.1);
}

.sn-input :deep(.el-input-group__prepend) {
  background: #f0fdf4;
  border: 2px solid #e2e8f0;
  border-right: none;
  border-radius: 8px 0 0 8px;
  color: #16a34a;
  font-weight: 600;
}

.sn-button-group {
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
}

.write-sn-btn {
  padding: 12px 32px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 8px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(103, 194, 58, 0.3);
  min-width: 160px;
}

.write-sn-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(103, 194, 58, 0.4);
}

.write-sn-btn:active {
  transform: translateY(0);
}

.clear-sn-btn {
  padding: 12px 24px;
  font-size: 16px;
  font-weight: 500;
  border-radius: 8px;
  transition: all 0.3s ease;
  min-width: 100px;
}

.clear-sn-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.mac-form {
  max-width: 600px;
  margin: 0 auto;
}

.mac-input {
  font-family: 'Courier New', monospace;
  font-size: 16px;
}

.form-help-text {
  margin-left: 10px;
  font-size: 12px;
  color: #909399;
}

.execute-btn, .stop-btn {
  margin-right: 12px;
  padding: 12px 24px;
  font-size: 16px;
  font-weight: 500;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.execute-btn {
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.execute-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(64, 158, 255, 0.4);
}

.stop-btn {
  box-shadow: 0 4px 12px rgba(245, 108, 108, 0.3);
}

.stop-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(245, 108, 108, 0.4);
}

/* 进度区域 */
.progress-section {
  margin-bottom: 32px;
}

.divider-text {
  font-weight: 600;
  color: #1a202c;
}

.progress-content {
  padding: 20px 0;
}

.progress-bar {
  margin-bottom: 16px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  color: #64748b;
}

.current-step {
  font-weight: 500;
  color: #1a202c;
}

.step-count {
  background: #f1f5f9;
  padding: 4px 12px;
  border-radius: 12px;
  font-weight: 500;
}

/* 测试结果区域 */
.test-result-section {
  margin-top: 32px;
}

.test-result-summary {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 20px;
  transition: all 0.3s ease;
}

/* 测试成功状态 */
.test-result-summary.test-success {
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
  border: 2px solid #22c55e;
  box-shadow: 0 4px 12px rgba(34, 197, 94, 0.15);
}

.test-result-summary.test-success .divider-text {
  color: #16a34a;
  font-weight: 700;
}

/* 测试失败状态 */
.test-result-summary.test-failed {
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  border: 2px solid #ef4444;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.15);
}

.test-result-summary.test-failed .divider-text {
  color: #dc2626;
  font-weight: 700;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.summary-card {
  text-align: center;
  padding: 16px;
  border-radius: 8px;
  background: white;
  border: 1px solid #e2e8f0;
  transition: all 0.3s ease;
}

.summary-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.summary-card.total {
  border-left: 4px solid #409eff;
}

.summary-card.passed {
  border-left: 4px solid #67c23a;
}

.summary-card.failed {
  border-left: 4px solid #f56c6c;
}

.summary-card.skipped {
  border-left: 4px solid #e6a23c;
}

.card-number {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 4px;
}

.summary-card.total .card-number {
  color: #409eff;
}

.summary-card.passed .card-number {
  color: #67c23a;
}

.summary-card.failed .card-number {
  color: #f56c6c;
}

.summary-card.skipped .card-number {
  color: #e6a23c;
}

.card-label {
  font-size: 14px;
  color: #64748b;
  font-weight: 500;
}

.test-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.detail-item {
  font-size: 14px;
  color: #374151;
  padding: 8px 12px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
}

.detail-item strong {
  color: #1a202c;
  margin-right: 8px;
}

/* 日志区域 */
.logs-section {
  margin-top: 32px;
}

.logs-container {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #fafbfc;
}

.log-item {
  padding: 16px;
  border-bottom: 1px solid #e2e8f0;
  transition: all 0.3s ease;
}

.log-item:last-child {
  border-bottom: none;
}

.log-item:hover {
  background: #f8fafc;
}

.log-item.success {
  border-left: 4px solid #67c23a;
}

.log-item.error {
  border-left: 4px solid #f56c6c;
}

.log-item.skipped {
  border-left: 4px solid #e6a23c;
}

.log-item.running {
  border-left: 4px solid #409eff;
  background: #f0f9ff;
}

.log-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.log-icon {
  margin-right: 8px;
  font-size: 16px;
}

.log-item.success .log-icon {
  color: #67c23a;
}

.log-item.error .log-icon {
  color: #f56c6c;
}

.log-item.skipped .log-icon {
  color: #e6a23c;
}

.log-item.running .log-icon {
  color: #409eff;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.log-name {
  font-weight: 600;
  color: #1a202c;
  flex: 1;
}

.log-time {
  font-size: 12px;
  color: #94a3b8;
  background: #f1f5f9;
  padding: 2px 8px;
  border-radius: 4px;
}

.log-content {
  margin-left: 24px;
  font-size: 14px;
  line-height: 1.6;
}

.log-command {
  margin-bottom: 4px;
  color: #374151;
}

.log-expected {
  margin-bottom: 4px;
  color: #7c3aed;
  font-family: 'Courier New', monospace;
  background: #faf5ff;
  padding: 4px 8px;
  border-radius: 4px;
  border-left: 3px solid #8b5cf6;
}

.log-response {
  margin-bottom: 4px;
  color: #059669;
  font-family: 'Courier New', monospace;
  background: #f0fdf4;
  padding: 4px 8px;
  border-radius: 4px;
  border-left: 3px solid #10b981;
}

.log-error {
  color: #dc2626;
  font-family: 'Courier New', monospace;
  background: #fef2f2;
  padding: 4px 8px;
  border-radius: 4px;
  border-left: 3px solid #ef4444;
}

.log-user-choice {
  margin-top: 8px;
  padding: 4px 8px;
  background: #f8fafc;
  border-radius: 4px;
  border-left: 3px solid #e2e8f0;
}

.choice-success {
  color: #059669;
  font-weight: 600;
}

.choice-failure {
  color: #dc2626;
  font-weight: 600;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-content {
    padding: 20px;
  }
  
  .workflow-content {
    padding: 16px;
  }
  
  .mac-form {
    max-width: 100%;
  }
  
  .execute-btn, .stop-btn {
    width: 100%;
    margin-right: 0;
    margin-bottom: 8px;
  }
  
  .progress-info {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .log-content {
    margin-left: 0;
  }
  
  .logs-container {
    max-height: 300px;
  }
  
  /* SN卡片响应式 */
  .sn-card-section {
    margin-top: 24px;
  }
  
  .sn-header-content {
    flex-direction: column;
    text-align: center;
    gap: 12px;
    padding: 16px 20px;
  }
  
  .sn-icon {
    font-size: 20px;
    padding: 10px;
  }
  
  .sn-title {
    font-size: 18px;
  }
  
  .sn-description {
    font-size: 13px;
  }
  
  .sn-content {
    padding: 20px 16px;
  }
  
  .sn-form {
    max-width: 100%;
  }
  
  .sn-button-group {
    flex-direction: column;
    width: 100%;
  }
  
  .write-sn-btn, .clear-sn-btn {
    width: 100%;
    margin: 0;
  }
}

/* 重试配置样式 */
.retry-config {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.config-label {
  font-size: 14px;
  color: #606266;
  white-space: nowrap;
}

@media (max-width: 480px) {
  .page-title {
    font-size: 20px;
  }
  
  .page-description {
    font-size: 12px;
  }
  
  .execute-btn, .stop-btn {
    padding: 10px 20px;
    font-size: 14px;
  }
  
  /* SN卡片小屏幕优化 */
  .sn-header-content {
    padding: 12px 16px;
  }
  
  .sn-icon {
    font-size: 18px;
    padding: 8px;
  }
  
  .sn-title {
    font-size: 16px;
  }
  
  .sn-description {
    font-size: 12px;
  }
  
  .sn-content {
    padding: 16px 12px;
  }
  
  .write-sn-btn, .clear-sn-btn {
    padding: 10px 20px;
    font-size: 14px;
  }
}
</style>
