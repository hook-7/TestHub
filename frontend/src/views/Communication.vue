<template>
  <div class="page-container">
    <!-- 状态栏 -->
    <div class="status-bar">
      <div class="status-info">
        <div class="connection-badge" :class="{ connected: connectionStore.isConnected, disconnected: !connectionStore.isConnected }">
          <el-icon class="status-icon">
            <component :is="connectionStore.isConnected ? 'CircleCheckFilled' : 'CircleCloseFilled'" />
          </el-icon>
          <span class="status-text">
            {{ connectionStore.isConnected ? `已连接 (${connectionStore.currentPort})` : '未连接' }}
          </span>
        </div>
      </div>
    </div>

    <el-row :gutter="20">
      <!-- 左侧：AT指令操作面板 -->
      <el-col :span="12">
        <el-card class="command-card">
          <template #header>
            <div class="card-header">
              <h3 class="card-title">
                <el-icon class="title-icon"><Operation /></el-icon>
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
                @contextmenu.prevent="handleCommandRightClick($event, cmd)"
                :disabled="!connectionStore.isConnected"
                :title="cmd.description"
              >
                {{ cmd.name }}
                <el-icon 
                  class="delete-icon" 
                  @click.stop="deleteCommand(cmd)"
                  :title="`删除指令: ${cmd.name}`"
                >
                  <Delete />
                </el-icon>
              </el-button>
              
              <!-- 当没有常用指令时显示提示 -->
              <div v-if="savedCommands.length === 0" class="no-commands-hint">
                <el-text type="info" size="small">
                  暂无常用指令，点击"添加指令"来创建您的第一个常用指令
                </el-text>
              </div>
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
        <el-card class="log-card">
          <template #header>
            <div class="card-header">
              <h3 class="card-title">
                <el-icon class="title-icon"><ChatDotSquare /></el-icon>
                通信日志
              </h3>
              <div class="header-actions">
                <el-button @click="clearLogs" size="small" type="danger" plain>
                  <el-icon><Delete /></el-icon>
                  清空日志
                </el-button>
                <el-button @click="exportLogs" size="small" type="primary" plain>
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
import { Delete } from '@element-plus/icons-vue'
import { useConnectionStore } from '@/stores/connection'
import { useCommunicationStore } from '@/stores/communication'
import { useSessionStore } from '@/stores/session'
import type { CommunicationLog } from '@/stores/communication'
import * as commandsAPI from '@/api/commands'

const router = useRouter()
const connectionStore = useConnectionStore()
const communicationStore = useCommunicationStore()
const sessionStore = useSessionStore()

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

// 常用指令现在完全由用户自定义

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
  // 应用用户设置的控制选项（自动添加终止符等）
  commandLoading.value = true
  try {
    const formattedCommand = formatCommand(command)
    await communicationStore.sendATCommand(formattedCommand)
    ElMessage.success('指令发送成功')
    // 同时更新输入框显示（显示原始指令，不显示终止符）
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

// API相关方法
const loadSavedCommands = async () => {
  try {
    const response = await commandsAPI.getAllCommands()
    // 转换API返回的数据格式以兼容现有组件
    savedCommands.value = response.commands.map(cmd => ({
      id: cmd.id,
      name: cmd.name,
      command: cmd.command,
      description: cmd.description,
      createdAt: cmd.created_at // API返回毫秒时间戳
    }))
  } catch (error) {
    console.error('Failed to load saved commands:', error)
    ElMessage.error('加载常用指令失败')
    // 出错时也初始化为空数组
    savedCommands.value = []
  }
}

const addNewCommand = async () => {
  if (!newCommand.name.trim() || !newCommand.command.trim()) {
    ElMessage.error('请填写指令名称和内容')
    return
  }
  
  try {
    const createRequest: commandsAPI.CreateCommandRequest = {
      name: newCommand.name.trim(),
      command: newCommand.command.trim(),
      description: newCommand.description.trim()
    }
    
    const createdCommand = await commandsAPI.createCommand(createRequest)
    
    // 转换为前端格式并添加到列表开头
    const command: SavedCommand = {
      id: createdCommand.id,
      name: createdCommand.name,
      command: createdCommand.command,
      description: createdCommand.description,
      createdAt: createdCommand.created_at
    }
    
    savedCommands.value.unshift(command)
    
    // 清空表单并关闭弹窗
    newCommand.name = ''
    newCommand.command = ''
    newCommand.description = ''
    showAddCommand.value = false
    
    ElMessage.success('常用指令添加成功')
  } catch (error: any) {
    console.error('Failed to create command:', error)
    ElMessage.error(error.message || '创建指令失败')
  }
}

const handleCloseAddCommand = () => {
  // 清空表单
  newCommand.name = ''
  newCommand.command = ''
  newCommand.description = ''
  showAddCommand.value = false
}

const deleteCommand = async (cmd: SavedCommand) => {
  try {
    await ElMessageBox.confirm(`确定要删除指令 "${cmd.name}" 吗？`, '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    
    await commandsAPI.deleteCommand(cmd.id)
    
    // 从本地列表中移除
    const index = savedCommands.value.findIndex(c => c.id === cmd.id)
    if (index !== -1) {
      savedCommands.value.splice(index, 1)
    }
    
    ElMessage.success('指令删除成功')
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('Failed to delete command:', error)
      ElMessage.error(error.message || '删除指令失败')
    }
  }
}

const handleCommandRightClick = (_event: MouseEvent, cmd: SavedCommand) => {
  // 右键点击指令时，显示上下文菜单或执行特定操作
  console.log('Right clicked command:', cmd.name)
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
onMounted(async () => {
  // 初始化会话管理
  await sessionStore.init()
  
  // 检查登录状态
  if (!sessionStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    router.push('/serial-config')
    return
  }
  
  if (!connectionStore.isConnected) {
    ElMessage.warning('请先连接串口')
    router.push('/serial-config')
    return
  }
  
  // 加载保存的指令
  await loadSavedCommands()
})
</script>

<style scoped>
.page-container {
  padding: 24px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  min-height: calc(100vh - 70px);
}

.status-bar {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(248, 250, 252, 0.9) 100%);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 16px 24px;
  margin-bottom: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.status-info {
  display: flex;
  justify-content: center;
  align-items: center;
}

.connection-badge {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  border-radius: 12px;
  font-weight: 600;
  font-size: 16px;
  transition: all 0.3s ease;
}

.connection-badge.connected {
  background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
  color: #155724;
  border: 1px solid #c3e6cb;
  box-shadow: 0 4px 12px rgba(21, 87, 36, 0.1);
}

.connection-badge.disconnected {
  background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
  color: #721c24;
  border: 1px solid #f5c6cb;
  box-shadow: 0 4px 12px rgba(114, 28, 36, 0.1);
}

.status-icon {
  font-size: 18px;
}

.status-text {
  font-weight: 600;
}

.command-card, .log-card {
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.95);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #374151;
}

.title-icon {
  font-size: 20px;
  color: #667eea;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.quick-commands {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
  min-height: 40px;
}

.quick-commands .el-button {
  border-radius: 8px;
  transition: all 0.3s ease;
}

.quick-commands .el-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.no-commands-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 20px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 8px;
  border: 2px dashed #e2e8f0;
}

.log-container {
  height: 500px;
  overflow-y: auto;
  padding: 16px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.log-item {
  margin-bottom: 16px;
  padding: 16px;
  border-radius: 12px;
  border-left: 4px solid;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease;
}

.log-item:hover {
  transform: translateX(4px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.log-item.sent {
  background: linear-gradient(135deg, rgba(64, 158, 255, 0.1) 0%, rgba(64, 158, 255, 0.05) 100%);
  border-left-color: #409eff;
  border-left-width: 4px;
}

.log-item.received.success {
  background: linear-gradient(135deg, rgba(103, 194, 58, 0.1) 0%, rgba(103, 194, 58, 0.05) 100%);
  border-left-color: #67c23a;
  border-left-width: 4px;
}

.log-item.received.error {
  background: linear-gradient(135deg, rgba(245, 108, 108, 0.1) 0%, rgba(245, 108, 108, 0.05) 100%);
  border-left-color: #f56c6c;
  border-left-width: 4px;
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
  font-family: 'Fira Code', 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 13px;
  background: linear-gradient(135deg, rgba(0, 0, 0, 0.03) 0%, rgba(0, 0, 0, 0.06) 100%);
  padding: 12px;
  border-radius: 8px;
  word-break: break-all;
  border: 1px solid rgba(0, 0, 0, 0.06);
  line-height: 1.5;
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

/* 删除按钮样式 */
.quick-commands .el-button {
  position: relative;
}

.quick-commands .delete-icon {
  position: absolute;
  top: -8px;
  right: -8px;
  background: #f56c6c;
  color: white;
  border-radius: 50%;
  width: 16px;
  height: 16px;
  font-size: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
  cursor: pointer;
  z-index: 1;
}

.quick-commands .el-button:hover .delete-icon {
  opacity: 1;
}

.delete-icon:hover {
  background: #f34040 !important;
  transform: scale(1.1);
}
</style>