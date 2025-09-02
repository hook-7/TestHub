<template>
  <div class="page-container">
    <!-- 导航栏 -->
    <el-card style="margin-bottom: 20px;">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <el-button @click="$router.push('/serial-config')">
          <el-icon><ArrowLeft /></el-icon>
          返回配置
        </el-button>
        
        <div class="status-indicator" :class="{ connected: connectionStore.isConnected, disconnected: !connectionStore.isConnected }">
          <el-icon>
            <component :is="connectionStore.isConnected ? 'CircleCheckFilled' : 'CircleCloseFilled'" />
          </el-icon>
          {{ connectionStore.isConnected ? `已连接 (${connectionStore.currentPort})` : '未连接' }}
        </div>
      </div>
    </el-card>

    <el-row :gutter="20">
      <!-- 左侧：AT指令操作面板 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>
                <el-icon><Operation /></el-icon>
                指令交互
              </h3>
            </div>
          </template>

          <!-- 指令输入区 -->
          <el-form :model="commandForm" label-width="80px">
            <el-form-item label="指令内容">
              <el-input
                v-model="commandForm.command"
                placeholder="输入指令内容，例如: AT+GMR 或任何自定义指令"
                style="font-family: monospace;"
                @keyup.enter="sendCommand"
              >
                <template #append>
                  <el-button 
                    type="primary" 
                    @click="sendCommand"
                    :disabled="!connectionStore.isConnected"
                    :loading="commandLoading"
                  >
                    <el-icon><Position /></el-icon>
                    发送
                  </el-button>
                </template>
              </el-input>
            </el-form-item>
            
            <!-- 指令控制选项 -->
            <el-form-item label="控制选项">
              <div class="command-controls">
                <el-checkbox v-model="commandForm.autoAddCRLF" size="small">
                  自动添加\r\n
                </el-checkbox>
                <el-select v-model="commandForm.lineEnding" size="small" style="width: 120px; margin-left: 12px;">
                  <el-option label="\r\n (CRLF)" value="\r\n" />
                  <el-option label="\r (CR)" value="\r" />
                  <el-option label="\n (LF)" value="\n" />
                  <el-option label="无终止符" value="" />
                </el-select>
                <el-button 
                  size="small" 
                  @click="clearCommandInput" 
                  style="margin-left: 12px;"
                >
                  清空
                </el-button>
              </div>
            </el-form-item>
          </el-form>

          <!-- 常用指令快捷按钮 -->
          <div style="margin-top: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
              <h4 style="margin: 0;">常用指令</h4>
              <div>
                <el-button size="small" @click="showAddCommand = true">
                  <el-icon><Plus /></el-icon>
                  添加指令
                </el-button>
                <el-button size="small" @click="showHistory = !showHistory">
                  <el-icon><Clock /></el-icon>
                  历史记录
                </el-button>
                <el-button size="small" @click="showBatchSend = !showBatchSend">
                  <el-icon><List /></el-icon>
                  批量发送
                </el-button>
              </div>
            </div>
            <div class="quick-commands">
              <el-button 
                v-for="cmd in savedCommands" 
                :key="cmd.id"
                size="small"
                @click="sendQuickCommand(cmd.command)"
                :disabled="!connectionStore.isConnected"
                :title="cmd.description"
              >
                {{ cmd.name }}
              </el-button>
            </div>
          </div>

          <!-- 历史记录 -->
          <el-collapse-transition>
            <div v-show="showHistory" style="margin-top: 16px;">
              <h4>指令历史</h4>
              <div class="history-commands">
                <el-tag 
                  v-for="(cmd, index) in commandHistory" 
                  :key="index"
                  size="small"
                  style="margin: 2px; cursor: pointer;"
                  @click="commandForm.command = cmd"
                  :title="`点击填入: ${cmd}`"
                >
                  {{ cmd }}
                </el-tag>
                <el-button v-if="commandHistory.length > 0" size="small" @click="clearHistory">
                  清空历史
                </el-button>
              </div>
            </div>
          </el-collapse-transition>

          <!-- 批量发送 -->
          <el-collapse-transition>
            <div v-show="showBatchSend" style="margin-top: 16px;">
              <h4>批量发送</h4>
              <el-input
                v-model="batchCommands"
                type="textarea"
                :rows="4"
                placeholder="每行一个指令，例如:&#10;AT&#10;AT+GMR&#10;AT+CSQ"
                style="font-family: monospace;"
              />
              <div style="margin-top: 8px;">
                <el-button 
                  type="primary" 
                  size="small"
                  @click="sendBatchCommands"
                  :disabled="!connectionStore.isConnected"
                  :loading="batchLoading"
                >
                  批量发送
                </el-button>
                <el-input-number 
                  v-model="batchDelay"
                  :min="100"
                  :max="10000"
                  :step="100"
                  size="small"
                  style="width: 120px; margin-left: 8px;"
                />
                <span style="margin-left: 4px; font-size: 12px; color: #666;">ms间隔</span>
              </div>
            </div>
          </el-collapse-transition>

          <!-- 原始数据发送 -->
          <el-divider>原始数据发送</el-divider>
          <el-form :model="rawForm" label-width="80px">
            <el-form-item label="十六进制">
              <el-input
                v-model="rawForm.data"
                placeholder="输入十六进制数据，例如: 41 54 0D 0A"
                style="font-family: monospace;"
                @keyup.enter="sendRawData"
              >
                <template #append>
                  <el-button 
                    type="primary" 
                    @click="sendRawData"
                    :disabled="!connectionStore.isConnected"
                    :loading="rawLoading"
                  >
                    <el-icon><Position /></el-icon>
                    发送
                  </el-button>
                </template>
              </el-input>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 右侧：通信日志 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>
                <el-icon><ChatDotSquare /></el-icon>
                通信日志
              </h3>
              <div>
                <el-button @click="clearLogs" size="small">
                  <el-icon><Delete /></el-icon>
                  清空日志
                </el-button>
                <el-button @click="exportLogs" size="small" style="margin-left: 8px;">
                  <el-icon><Download /></el-icon>
                  导出日志
                </el-button>
              </div>
            </div>
          </template>

          <div class="log-container">
            <div 
              v-for="log in communicationStore.logs" 
              :key="log.id"
              class="log-item"
              :class="[
                log.direction,
                log.direction === 'received' ? (log.success ? 'success' : 'error') : ''
              ]"
            >
              <div class="log-header">
                <span>
                  <el-icon>
                    <component :is="getLogIcon(log)" />
                  </el-icon>
                  {{ log.description }}
                </span>
                <span class="log-timestamp">
                  {{ formatTime(log.timestamp) }}
                </span>
              </div>
              <div class="log-data">{{ log.data }}</div>
            </div>
            
            <div v-if="communicationStore.logs.length === 0" class="empty-logs">
              <el-empty description="暂无通信日志" />
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 添加指令对话框 -->
    <el-dialog
      v-model="showAddCommand"
      title="添加常用指令"
      width="500px"
      :before-close="handleCloseAddCommand"
    >
      <el-form :model="newCommand" label-width="80px">
        <el-form-item label="指令名称" required>
          <el-input
            v-model="newCommand.name"
            placeholder="例如: 查询版本"
            maxlength="20"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="指令内容" required>
          <el-input
            v-model="newCommand.command"
            placeholder="例如: AT+GMR"
            style="font-family: monospace;"
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="newCommand.description"
            placeholder="指令说明（可选）"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showAddCommand = false">取消</el-button>
          <el-button type="primary" @click="addNewCommand">确定</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useConnectionStore } from '@/stores/connection'
import { useCommunicationStore } from '@/stores/communication'
import type { CommunicationLog } from '@/stores/communication'

const router = useRouter()
const connectionStore = useConnectionStore()
const communicationStore = useCommunicationStore()

// 状态
const commandLoading = ref(false)
const rawLoading = ref(false)
const batchLoading = ref(false)
const showHistory = ref(false)
const showBatchSend = ref(false)
const showAddCommand = ref(false)
const commandHistory = ref<string[]>([])
const batchCommands = ref('')
const batchDelay = ref(1000)

// 表单数据
const commandForm = reactive({
  command: '',
  autoAddCRLF: true,
  lineEnding: '\r\n',
})

// 新指令表单
const newCommand = reactive({
  name: '',
  command: '',
  description: '',
})

const rawForm = reactive({
  data: '',
})

// 保存的指令接口
interface SavedCommand {
  id: string
  name: string
  command: string
  description: string
  createdAt: number
}

// 保存的指令列表
const savedCommands = ref<SavedCommand[]>([])

// 默认常用指令
const defaultCommands: SavedCommand[] = [
  { id: '1', name: 'AT', command: 'AT\r\n', description: '测试连接', createdAt: Date.now() },
  { id: '2', name: 'GMR', command: 'AT+GMR\r\n', description: '查询固件版本', createdAt: Date.now() },
  { id: '3', name: 'CGMI', command: 'AT+CGMI\r\n', description: '查询制造商', createdAt: Date.now() },
  { id: '4', name: 'CGMM', command: 'AT+CGMM\r\n', description: '查询模块型号', createdAt: Date.now() },
  { id: '5', name: 'CGMR', command: 'AT+CGMR\r\n', description: '查询软件版本', createdAt: Date.now() },
  { id: '6', name: 'CGSN', command: 'AT+CGSN\r\n', description: '查询IMEI', createdAt: Date.now() },
  { id: '7', name: 'CIMI', command: 'AT+CIMI\r\n', description: '查询IMSI', createdAt: Date.now() },
  { id: '8', name: 'CCID', command: 'AT+CCID\r\n', description: '查询ICCID', createdAt: Date.now() },
  { id: '9', name: 'CSQ', command: 'AT+CSQ\r\n', description: '查询信号强度', createdAt: Date.now() },
  { id: '10', name: 'CREG', command: 'AT+CREG?\r\n', description: '查询网络注册状态', createdAt: Date.now() },
  { id: '11', name: 'CGATT', command: 'AT+CGATT?\r\n', description: '查询GPRS附着状态', createdAt: Date.now() },
  { id: '12', name: 'COPS', command: 'AT+COPS?\r\n', description: '查询运营商', createdAt: Date.now() },
  { id: '13', name: 'CFUN?', command: 'AT+CFUN?\r\n', description: '查询功能状态', createdAt: Date.now() },
  { id: '14', name: 'CFUN=1', command: 'AT+CFUN=1\r\n', description: '启用全功能', createdAt: Date.now() },
  { id: '15', name: 'CFUN=0', command: 'AT+CFUN=0\r\n', description: '关闭射频', createdAt: Date.now() },
  { id: '16', name: 'ATZ', command: 'ATZ\r\n', description: '重置设备', createdAt: Date.now() },
]

// 方法
const formatCommand = (command: string) => {
  // 前端完全控制指令格式
  let formattedCommand = command.trim()
  
  // 如果启用自动添加终止符且指令中没有终止符
  if (commandForm.autoAddCRLF && commandForm.lineEnding && !hasLineEnding(formattedCommand)) {
    formattedCommand += commandForm.lineEnding
  }
  
  return formattedCommand
}

const hasLineEnding = (command: string) => {
  return command.includes('\r') || command.includes('\n')
}

const addToHistory = (command: string) => {
  const cleanCommand = command.replace(/\r\n|\r|\n/g, '')
  if (cleanCommand && !commandHistory.value.includes(cleanCommand)) {
    commandHistory.value.unshift(cleanCommand)
    // 限制历史记录数量
    if (commandHistory.value.length > 20) {
      commandHistory.value = commandHistory.value.slice(0, 20)
    }
  }
}

const clearHistory = () => {
  commandHistory.value = []
}

const sendCommand = async () => {
  if (!commandForm.command.trim()) {
    ElMessage.error('请输入指令内容')
    return
  }
  
  commandLoading.value = true
  try {
    const formattedCommand = formatCommand(commandForm.command)
    await communicationStore.sendATCommand(formattedCommand)
    ElMessage.success('指令发送成功')
    // 添加到历史记录
    addToHistory(commandForm.command)
  } catch (error) {
    console.error('Send command error:', error)
  } finally {
    commandLoading.value = false
  }
}

const clearCommandInput = () => {
  commandForm.command = ''
}

const sendQuickCommand = async (command: string) => {
  // 直接发送预设的完整格式指令，不经过formatCommand处理
  commandLoading.value = true
  try {
    await communicationStore.sendATCommand(command)
    ElMessage.success('指令发送成功')
    // 同时更新输入框显示（去掉终止符显示）
    const cleanCommand = command.replace(/\r\n|\r|\n/g, '')
    commandForm.command = cleanCommand
    // 添加到历史记录
    addToHistory(cleanCommand)
  } catch (error) {
    console.error('Send command error:', error)
  } finally {
    commandLoading.value = false
  }
}

const sendBatchCommands = async () => {
  if (!batchCommands.value.trim()) {
    ElMessage.error('请输入要批量发送的指令')
    return
  }
  
  const commands = batchCommands.value
    .split('\n')
    .map(cmd => cmd.trim())
    .filter(cmd => cmd.length > 0)
  
  if (commands.length === 0) {
    ElMessage.error('没有有效的指令')
    return
  }
  
  batchLoading.value = true
  
  try {
    for (let i = 0; i < commands.length; i++) {
      const command = commands[i]
      const formattedCommand = formatCommand(command)
      
      ElMessage.info(`发送第${i + 1}/${commands.length}个指令: ${command}`)
      
      try {
        await communicationStore.sendATCommand(formattedCommand)
        addToHistory(command)
      } catch (error) {
        console.error(`Command ${i + 1} failed:`, error)
        ElMessage.error(`第${i + 1}个指令发送失败: ${command}`)
      }
      
      // 如果不是最后一个指令，等待指定间隔
      if (i < commands.length - 1) {
        await new Promise(resolve => setTimeout(resolve, batchDelay.value))
      }
    }
    
    ElMessage.success(`批量发送完成，共发送${commands.length}个指令`)
  } catch (error) {
    console.error('Batch send error:', error)
    ElMessage.error('批量发送过程中出现错误')
  } finally {
    batchLoading.value = false
  }
}

// 浏览器存储相关方法
const STORAGE_KEY = 'saved_commands'

const loadSavedCommands = () => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      const parsed = JSON.parse(stored)
      savedCommands.value = parsed
    } else {
      // 首次使用，加载默认指令
      savedCommands.value = [...defaultCommands]
      saveCommandsToStorage()
    }
  } catch (error) {
    console.error('Failed to load saved commands:', error)
    savedCommands.value = [...defaultCommands]
  }
}

const saveCommandsToStorage = () => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(savedCommands.value))
  } catch (error) {
    console.error('Failed to save commands:', error)
    ElMessage.error('保存指令失败')
  }
}

const addNewCommand = () => {
  if (!newCommand.name.trim() || !newCommand.command.trim()) {
    ElMessage.error('请填写指令名称和内容')
    return
  }
  
  // 检查名称是否重复
  if (savedCommands.value.some(cmd => cmd.name === newCommand.name.trim())) {
    ElMessage.error('指令名称已存在')
    return
  }
  
  const command: SavedCommand = {
    id: Date.now().toString(),
    name: newCommand.name.trim(),
    command: newCommand.command.trim(),
    description: newCommand.description.trim(),
    createdAt: Date.now(),
  }
  
  savedCommands.value.unshift(command)
  saveCommandsToStorage()
  
  // 清空表单
  newCommand.name = ''
  newCommand.command = ''
  newCommand.description = ''
  showAddCommand.value = false
  
  ElMessage.success('指令添加成功')
}

const handleCloseAddCommand = () => {
  // 清空表单
  newCommand.name = ''
  newCommand.command = ''
  newCommand.description = ''
  showAddCommand.value = false
}

const sendRawData = async () => {
  if (!rawForm.data.trim()) {
    ElMessage.error('请输入十六进制数据')
    return
  }
  
  rawLoading.value = true
  try {
    await communicationStore.sendRawData(rawForm.data)
    ElMessage.success('原始数据发送成功')
  } catch (error) {
    console.error('Send raw data error:', error)
  } finally {
    rawLoading.value = false
  }
}

const clearLogs = async () => {
  try {
    await ElMessageBox.confirm('确定要清空所有通信日志吗？', '确认操作', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    communicationStore.clearLogs()
    ElMessage.success('日志已清空')
  } catch {
    // 用户取消
  }
}

const exportLogs = () => {
  try {
    const logs = communicationStore.logs.map(log => ({
      时间: new Date(log.timestamp).toLocaleString(),
      方向: log.direction === 'sent' ? '发送' : '接收',
      描述: log.description,
      数据: log.data,
      状态: log.success ? '成功' : '失败'
    }))
    
    const csvContent = [
      ['时间', '方向', '描述', '数据', '状态'].join(','),
      ...logs.map(log => [
        `"${log.时间}"`,
        `"${log.方向}"`, 
        `"${log.描述}"`,
        `"${log.数据}"`,
        `"${log.状态}"`
      ].join(','))
    ].join('\n')
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', `通信日志_${new Date().toISOString().slice(0, 10)}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    ElMessage.success('日志导出成功')
  } catch (error) {
    console.error('Export logs error:', error)
    ElMessage.error('日志导出失败')
  }
}

const getLogIcon = (log: CommunicationLog) => {
  if (log.direction === 'sent') {
    return 'Top'
  } else {
    return log.success ? 'Bottom' : 'CloseBold'
  }
}

const formatTime = (timestamp: number) => {
  return new Date(timestamp).toLocaleTimeString()
}

// 生命周期
onMounted(() => {
  if (!connectionStore.isConnected) {
    ElMessage.warning('请先连接串口')
    router.push('/serial-config')
  }
  // 加载保存的指令
  loadSavedCommands()
})
</script>

<style scoped>
.page-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 6px;
  font-weight: 500;
}

.status-indicator.connected {
  background-color: var(--el-color-success-light-9);
  color: var(--el-color-success);
}

.status-indicator.disconnected {
  background-color: var(--el-color-error-light-9);
  color: var(--el-color-error);
}

.quick-commands {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.log-container {
  height: 500px;
  overflow-y: auto;
  padding: 10px;
  background-color: var(--el-bg-color-page);
  border-radius: 8px;
}

.log-item {
  margin-bottom: 12px;
  padding: 12px;
  border-radius: 8px;
  border-left: 4px solid;
}

.log-item.sent {
  background-color: var(--el-color-primary-light-9);
  border-left-color: var(--el-color-primary);
}

.log-item.received.success {
  background-color: var(--el-color-success-light-9);
  border-left-color: var(--el-color-success);
}

.log-item.received.error {
  background-color: var(--el-color-error-light-9);
  border-left-color: var(--el-color-error);
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  font-weight: 500;
}

.log-timestamp {
  font-size: 12px;
  opacity: 0.7;
}

.log-data {
  font-family: monospace;
  font-size: 14px;
  background-color: rgba(0, 0, 0, 0.05);
  padding: 8px;
  border-radius: 4px;
  word-break: break-all;
}

.empty-logs {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.el-divider {
  margin: 24px 0 16px 0;
}

.command-controls {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.history-commands {
  max-height: 120px;
  overflow-y: auto;
  padding: 8px;
  background-color: var(--el-bg-color-page);
  border-radius: 4px;
  border: 1px solid var(--el-border-color-light);
}
</style>