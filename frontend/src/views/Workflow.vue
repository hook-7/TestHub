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

          <!-- MAC地址输入区域 -->
          <div v-else class="input-section">
            <el-form :model="form" label-width="120px" class="mac-form">
              <el-form-item label="MAC地址" required>
                <el-input
                  v-model="form.macAddress"
                  placeholder="请输入MAC地址，如：026501123456"
                  clearable
                  :disabled="isExecuting"
                  class="mac-input"
                >
                  <template #prepend>
                    <el-icon><Link /></el-icon>
                  </template>
                </el-input>
              </el-form-item>
              
              <el-form-item>
                <el-button 
                  type="primary" 
                  :loading="isExecuting"
                  :disabled="!form.macAddress || isExecuting"
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
                  <div v-if="log.response" class="log-response">
                    <strong>响应:</strong> {{ log.response }}
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
  Clock
} from '@element-plus/icons-vue'
import { serialAPI } from '@/api/serial'
import { getAllCommands, type SavedCommand } from '@/api/commands'
import { testResultsAPI, type SaveTestResultRequest } from '@/api/testResults'

// 命令数据 - 从常用命令接口动态获取
const cmds = ref<SavedCommand[]>([])

// 硬编码的测试项（已注释，现在从API获取）
/*
const cmds = ref<SavedCommand[]>([
	{
		"id": "1",
		"name": "设置MAC",
		"command": "AT+MAC=026501123456",
		"description": "",
		"created_at": 1725431941000,
		"expected_response": "",
		"send_as_hex": false,
		"show_notification": false,
		"target_serial_id": 1
	},
	{
		"id": "2",
		"name": "获取MAC",
		"command": "AT+MAC?",
		"description": "123",
		"created_at": 1725431958000,
		"expected_response": "",
		"send_as_hex": false,
		"show_notification": false,
		"target_serial_id": 1
	},
	{
		"id": "4c1eae2c-49e4-431c-a271-81fc7c5dcd54",
		"name": "测试 Eeprom",
		"command": "Eeprom",
		"description": "",
		"created_at": 1725583346000,
		"expected_response": "EEPROM Test OK\r\n",
		"send_as_hex": false,
		"show_notification": false,
		"target_serial_id": 1
	},
	{
		"id": "4c1eae2c-49e4-431c-a271-81fc7c5dcd55",
		"name": "测试LED1",
		"command": "ON1",
		"description": "LED1 是否亮灯?",
		"created_at": 1725583346000,
		"expected_response": "LED1OK\r\n",
		"send_as_hex": false,
		"show_notification": true,
		"target_serial_id": 1
	},
	{
		"id": "4c1eae2c-49e4-431c-a271-81fc7c5dcd56",
		"name": "测试LED2",
		"command": "ON2",
		"description": "LED2 是否亮灯?",
		"created_at": 1725583346000,
		"expected_response": "LED2OK\r\n",
		"send_as_hex": false,
		"show_notification": true,
		"target_serial_id": 1
	},
	{
		"id": "4c1eae2c-49e4-431c-a271-81fc7c5dcd57",
		"name": "测试LED3",
		"command": "ON1",
		"description": "LED3 是否亮灯?",
		"created_at": 1725583346000,
		"expected_response": "LED3OK\r\n",
		"send_as_hex": false,
		"show_notification": true,
		"target_serial_id": 1
	},
	{
		"id": "4c1eae2c-49e4-431c-a271-81fc7c5dcd58",
		"name": "测试 DPLCA",
		"command": "DPLCA",
		"description": "",
		"created_at": 1725583346000,
		"expected_response": "",
		"send_as_hex": false,
		"show_notification": false,
		"target_serial_id": 1
	},
	{
		"id": "4c1eae2c-49e4-431c-a271-81fc7c5dcd59",
		"name": "测试 S485B",
		"command": "S485B",
		"description": "",
		"created_at": 1725583346000,
		"expected_response": "485BOK\r\n",
		"send_as_hex": false,
		"show_notification": false,
		"target_serial_id": 2
	}
])
*/

// 表单数据
const form = ref({
  macAddress: ''
})

// 加载状态
const isLoadingCommands = ref(false)

// 执行状态
const isExecuting = ref(false)
const currentStepIndex = ref(-1)
const executionLogs = ref<ExecutionLog[]>([])
const shouldStop = ref(false)

// 测试结果状态
const testResult = ref<TestResult | null>(null)

// 执行日志接口
interface ExecutionLog {
  name: string
  command: string
  response?: string
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
  return command.replace(/026501123456/g, macAddress)
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
    status: 'running',
    timestamp: Date.now()
  }

  let userChoice: boolean | undefined = undefined

  try {
    // 替换MAC地址
    const finalCommand = replaceMacAddress(cmd.command, form.value.macAddress)
    


    // 使用HTTP请求发送命令
    const response = await serialAPI.sendATCommand(
      finalCommand, 
      cmd.target_serial_id
    )
    
    log.response = response.received_data
    log.status = 'success'
    
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
      isOk = actualResponse.includes(expectedResponse.trim())
      reason = isOk ? 'expected_match' : 'expected_mismatch'
    } else {
      // 没有预期响应，只要有响应就算OK
      isOk = actualResponse.length > 0
      reason = isOk ? 'has_response' : 'no_response'
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
      operator: '操作员', // 可以从用户输入或其他地方获取
      workstation: '工位1', // 可以从配置或其他地方获取
      device_id: '设备001' // 可以从配置或其他地方获取
    }
    
    // 调用API保存
    await testResultsAPI.saveTestResult(saveRequest)
    console.log('测试结果已保存到后端')
    
  } catch (error) {
    console.error('保存测试结果失败:', error)
    ElMessage.error('保存测试结果失败: ' + (error instanceof Error ? error.message : '未知错误'))
  }
}

// 执行工作流
const executeWorkflow = async () => {
  if (!form.value.macAddress.trim()) {
    ElMessage.warning('请输入MAC地址')
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
    showTestResultSummary()
    console.log(testResult.value);
    
    
  } catch (error) {
    ElMessage.error('工作流执行失败: ' + (error instanceof Error ? error.message : '未知错误'))
  } finally {
    isExecuting.value = false
  }
}

// 显示测试结果摘要
const showTestResultSummary = () => {
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
  
  ElMessageBox.alert(
    `${resultIcon} ${resultTitle}！\n\n` +
    `MAC地址: ${testResult.value.macAddress}\n` +
    `总测试数: ${totalTests}\n` +
    `通过: ${passedTests}\n` +
    `失败: ${failedTests}\n` +
    `跳过: ${skippedTests}\n` +
    `耗时: ${duration}秒`,
    resultTitle,
    {
      confirmButtonText: '确定',
      type: resultType
    }
  )
}

// 停止执行
const stopExecution = () => {
  shouldStop.value = true
  ElMessage.info('正在停止执行...')
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

// 组件挂载时加载命令
onMounted(() => {
  loadCommands()
})

</script>

<style scoped>
.workflow-container {
  height: 100%;
  background: linear-gradient(135deg, #f5f7fa 0%, #f8fafc 100%);
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
.empty-section {
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

.mac-form {
  max-width: 600px;
  margin: 0 auto;
}

.mac-input {
  font-family: 'Courier New', monospace;
  font-size: 16px;
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
}
</style>
