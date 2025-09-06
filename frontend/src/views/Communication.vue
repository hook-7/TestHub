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
            {{ connectionStore.isConnected ? `已连接 ${connectionStore.connectedSerials.length} 个串口` : '未连接' }}
          </span>
        </div>
        
        <!-- 串口选择器 -->
        <div v-if="connectionStore.isConnected" class="serial-selector">
          <el-select 
            v-model="connectionStore.selectedSerialId" 
            placeholder="选择串口"
            size="small"
            style="width: 200px;"
            @change="onSerialChange"
          >
            <el-option
              v-for="serial in connectionStore.connectedSerials"
              :key="serial.serial_id"
              :label="`串口 #${serial.serial_id} (${serial.port})`"
              :value="serial.serial_id"
            />
          </el-select>
        </div>
        
        <!-- WebSocket连接状态 -->
        <div class="realtime-badge" :class="{ connected: communicationStore.isRealTimeConnected, disconnected: !communicationStore.isRealTimeConnected }">
          <el-icon class="status-icon">
            <span v-if="communicationStore.isRealTimeConnected" class="connected-icon">●</span>
            <span v-else class="disconnected-icon">●</span>
          </el-icon>
          <span class="status-text">
            WebSocket {{ communicationStore.isRealTimeConnected ? '已连接' : '连接中' }}
          </span>
        </div>
      </div>
    </div>

    <el-row :gutter="20" class="main-row">
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
          <div class="form-section">
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

          <!-- 原始数据发送 -->
          <el-divider>原始数据发送</el-divider>
          <el-form :model="rawForm" label-width="80px">
            <el-form-item label="十六进制">
              <el-input
                v-model="rawForm.data"
                placeholder="输入十六进制数据，例如: 41 54 0D 0A (不区分大小写，可用空格分隔)"
                style="font-family: monospace;"
                @keyup.enter="sendRawData"
                @input="formatHexInput"
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

          <!-- 常用指令快捷按钮 -->
          <div class="commands-section">
            <div class="command-header">
              <h4 class="command-title">常用指令</h4>
              <div class="command-actions">
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
              <div
                v-for="cmd in savedCommands"
                :key="cmd.id"
                class="quick-command-btn"
                @click="sendQuickCommand(cmd)"
                @contextmenu.prevent="handleCommandRightClick($event, cmd)"
                :class="{ disabled: !connectionStore.isConnected }"
                :title="cmd.description"
              >
                <div class="command-content">
                  <div class="quick-command-name">
                    {{ cmd.name }}
                    <el-tag v-if="cmd.send_as_hex" size="small" type="warning" style="margin-left: 8px;">
                      16进制
                    </el-tag>
                    <el-tag v-if="cmd.target_serial_id" size="small" type="info" style="margin-left: 8px;">
                      串口#{{ cmd.target_serial_id }}
                    </el-tag>
                  </div>
                  <div class="quick-command-text">{{ cmd.command }}</div>
                  <div v-if="cmd.expected_response" class="quick-command-expected">
                    期望: {{ cmd.expected_response }}
                  </div>
                </div>
                <div class="command-actions">
                  <el-icon
                    class="edit-icon"
                    @click.stop="openEditCommand(cmd)"
                    :title="`编辑指令: ${cmd.name}`"
                  >
                    <Edit />
                  </el-icon>
                  <el-icon
                    class="delete-icon"
                    @click.stop="deleteCommand(cmd)"
                    :title="`删除指令: ${cmd.name}`"
                  >
                    <Delete />
                  </el-icon>
                </div>
              </div>
              
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
          </div>
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
                <el-button @click="clearLogs" size="small" type="danger" plain class="clear-logs-btn">
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
                  <el-tag v-if="log.serial_id" size="small" type="info" style="margin-left: 8px;">
                    串口#{{ log.serial_id }}
                  </el-tag>
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
        <el-form-item label="期望返回值">
          <el-input
            v-model="newCommand.expected_response"
            placeholder="指令执行后的期望返回值（可选）"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="发送方式">
          <el-radio-group v-model="newCommand.send_as_hex">
            <el-radio :value="false">文本发送</el-radio>
            <el-radio :value="true">16进制发送</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="目标串口">
          <el-select v-model="newCommand.target_serial_id" placeholder="选择目标串口（可选）" clearable>
            <el-option
              v-for="serial in connectionStore.connectedSerials"
              :key="serial.serial_id"
              :label="`串口 #${serial.serial_id} (${serial.port})`"
              :value="serial.serial_id"
            />
          </el-select>
          <div style="font-size: 12px; color: #666; margin-top: 4px;">
            不选择则使用当前选择的串口
          </div>
        </el-form-item>
        <el-form-item label="通知设置">
          <el-checkbox v-model="newCommand.show_notification">
            执行后弹出通知
          </el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showAddCommand = false">取消</el-button>
          <el-button type="primary" @click="addNewCommand">确定</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 编辑指令对话框 -->
    <el-dialog
      v-model="showEditCommand"
      title="编辑常用指令"
      width="500px"
      :before-close="handleCloseEditCommand"
    >
      <el-form :model="editCommand" label-width="80px">
        <el-form-item label="指令名称" required>
          <el-input
            v-model="editCommand.name"
            placeholder="例如: 查询版本"
            maxlength="20"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="指令内容" required>
          <el-input
            v-model="editCommand.command"
            placeholder="例如: AT+GMR"
            style="font-family: monospace;"
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="editCommand.description"
            placeholder="指令说明（可选）"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="期望返回值">
          <el-input
            v-model="editCommand.expected_response"
            placeholder="指令执行后的期望返回值（可选）"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="发送方式">
          <el-radio-group v-model="editCommand.send_as_hex">
            <el-radio :value="false">文本发送</el-radio>
            <el-radio :value="true">16进制发送</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="目标串口">
          <el-select v-model="editCommand.target_serial_id" placeholder="选择目标串口（可选）" clearable>
            <el-option
              v-for="serial in connectionStore.connectedSerials"
              :key="serial.serial_id"
              :label="`串口 #${serial.serial_id} (${serial.port})`"
              :value="serial.serial_id"
            />
          </el-select>
          <div style="font-size: 12px; color: #666; margin-top: 4px;">
            不选择则使用当前选择的串口
          </div>
        </el-form-item>
        <el-form-item label="通知设置">
          <el-checkbox v-model="editCommand.show_notification">
            执行后弹出通知
          </el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleCloseEditCommand">取消</el-button>
          <el-button type="primary" @click="updateCommand">确定</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Download, Edit } from '@element-plus/icons-vue'
import { useConnectionStore } from '@/stores/connection'
import { useCommunicationStore } from '@/stores/communication'
import type { CommunicationLog } from '@/stores/communication'
import * as commandsAPI from '@/api/commands'

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
const showEditCommand = ref(false)
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
  expected_response: '',
  send_as_hex: false,
  show_notification: false,
  target_serial_id: undefined as number | undefined,
})

// 编辑指令表单
const editCommand = reactive({
  id: '',
  name: '',
  command: '',
  description: '',
  expected_response: '',
  send_as_hex: false,
  show_notification: false,
  target_serial_id: undefined as number | undefined,
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
  expected_response: string
  send_as_hex: boolean
  show_notification: boolean
  target_serial_id?: number
  createdAt: number
}

// 保存的指令列表
const savedCommands = ref<SavedCommand[]>([])

// 常用指令现在完全由用户自定义

// 方法
const formatCommand = (command: string) => {
  // 前端完全控制指令格式
  let formattedCommand = command.trim()
  
  // 首先处理转义字符：将文本形式的 \r\n 转换为真实控制字符
  formattedCommand = formattedCommand
    .replace(/\\r\\n/g, '\r\n')  // \r\n -> 真实的CRLF
    .replace(/\\r/g, '\r')       // \r -> 真实的CR  
    .replace(/\\n/g, '\n')       // \n -> 真实的LF
  
  // 如果启用自动添加终止符且指令中没有真实的控制字符
  const hasRealLineEnding = formattedCommand.includes('\r') || formattedCommand.includes('\n')
  if (commandForm.autoAddCRLF && commandForm.lineEnding && !hasRealLineEnding) {
    formattedCommand += commandForm.lineEnding
  }
  
  return formattedCommand
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
  
  if (!connectionStore.selectedSerialId) {
    ElMessage.error('请先选择一个串口')
    return
  }
  
  commandLoading.value = true
  try {
    const formattedCommand = formatCommand(commandForm.command)
    await communicationStore.sendATCommand(formattedCommand, connectionStore.selectedSerialId)
    ElMessage.success(`指令发送成功 (串口 #${connectionStore.selectedSerialId})`)
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

const sendQuickCommand = async (cmd: SavedCommand) => {
  // 确定要使用的串口ID
  const targetSerialId = cmd.target_serial_id || connectionStore.selectedSerialId
  
  if (!targetSerialId) {
    ElMessage.error('请先选择一个串口或为指令设置目标串口')
    return
  }
  
  commandLoading.value = true
  try {
    if (cmd.send_as_hex) {
      // 16进制发送
      await communicationStore.sendRawData(cmd.command, targetSerialId)
      ElMessage.success(`16进制指令发送成功 (串口 #${targetSerialId})`)
    } else {
      // 文本发送
      const formattedCommand = formatCommand(cmd.command)
      await communicationStore.sendATCommand(formattedCommand, targetSerialId)
      ElMessage.success(`指令发送成功 (串口 #${targetSerialId})`)
    }
    
    // 同时更新输入框显示（显示原始指令，不显示终止符）
    const cleanCommand = cmd.command.replace(/\r\n|\r|\n/g, '')
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
  
  if (!connectionStore.selectedSerialId) {
    ElMessage.error('请先选择一个串口')
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
      
      ElMessage.info(`发送第${i + 1}/${commands.length}个指令: ${command} (串口 #${connectionStore.selectedSerialId})`)
      
      try {
        await communicationStore.sendATCommand(formattedCommand, connectionStore.selectedSerialId)
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
      expected_response: cmd.expected_response,
      send_as_hex: cmd.send_as_hex,
      show_notification: cmd.show_notification,
      target_serial_id: cmd.target_serial_id,
      createdAt: cmd.created_at // API返回毫秒时间戳
    }))
  } catch (error) {
    console.error('Failed to load saved commands:', error)
    ElMessage.warning('无法连接到后端，使用示例指令演示多串口功能')
    // 提供示例指令数据来演示多串口功能
    savedCommands.value = [
      {
        id: '1',
        name: '设置MAC',
        command: 'AT+MAC=026501123456',
        description: '设置设备MAC地址',
        expected_response: 'OK',
        send_as_hex: false,
        show_notification: false,
        target_serial_id: 1, // 指定串口1
        createdAt: Date.now()
      },
      {
        id: '2',
        name: '获取MAC',
        command: 'AT+MAC?',
        description: '查询设备MAC地址',
        expected_response: '+MAC:026501123456',
        send_as_hex: false,
        show_notification: true,
        target_serial_id: 1, // 使用当前选择的串口
        createdAt: Date.now()
      },
      {
        id: '3',
        name: '查询版本',
        command: 'AT+GMR',
        description: '查询固件版本信息',
        expected_response: 'AT version:1.0.0',
        send_as_hex: false,
        show_notification: false,
        target_serial_id: 2, // 指定串口2（演示：如果串口2不存在会复用ID）
        createdAt: Date.now()
      },
      {
        id: '4',
        name: '重启设备',
        command: 'AT+RST',
        description: '重启设备',
        expected_response: 'OK',
        send_as_hex: false,
        show_notification: true,
        target_serial_id: 2,
        createdAt: Date.now()
      },
      {
        id: '5',
        name: '发送16进制',
        command: '41540D0A',
        description: '发送AT\\r\\n的16进制格式',
        expected_response: '4F4B0D0A',
        send_as_hex: true,
        show_notification: false,
        target_serial_id: 1,
        createdAt: Date.now()
      }
    ]
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
      description: newCommand.description.trim(),
      expected_response: newCommand.expected_response.trim(),
      send_as_hex: newCommand.send_as_hex,
      show_notification: newCommand.show_notification,
      target_serial_id: newCommand.target_serial_id
    }
    
    const createdCommand = await commandsAPI.createCommand(createRequest)
    
    // 转换为前端格式并添加到列表开头
    const command: SavedCommand = {
      id: createdCommand.id,
      name: createdCommand.name,
      command: createdCommand.command,
      description: createdCommand.description,
      expected_response: createdCommand.expected_response,
      send_as_hex: createdCommand.send_as_hex,
      show_notification: createdCommand.show_notification,
      target_serial_id: createdCommand.target_serial_id,
      createdAt: createdCommand.created_at
    }
    
    savedCommands.value.unshift(command)
    
    // 清空表单并关闭弹窗
    newCommand.name = ''
    newCommand.command = ''
    newCommand.description = ''
    newCommand.expected_response = ''
    newCommand.send_as_hex = false
    newCommand.show_notification = false
    newCommand.target_serial_id = undefined
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
  newCommand.expected_response = ''
  newCommand.send_as_hex = false
  newCommand.show_notification = false
  newCommand.target_serial_id = undefined
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

const openEditCommand = (cmd: SavedCommand) => {
  // 填充编辑表单
  editCommand.id = cmd.id
  editCommand.name = cmd.name
  editCommand.command = cmd.command
  editCommand.description = cmd.description
  editCommand.expected_response = cmd.expected_response
  editCommand.send_as_hex = cmd.send_as_hex
  editCommand.show_notification = cmd.show_notification
  editCommand.target_serial_id = cmd.target_serial_id
  showEditCommand.value = true
}

const updateCommand = async () => {
  if (!editCommand.name.trim() || !editCommand.command.trim()) {
    ElMessage.error('请填写指令名称和内容')
    return
  }

  try {
    const updateRequest: commandsAPI.UpdateCommandRequest = {
      name: editCommand.name.trim(),
      command: editCommand.command.trim(),
      description: editCommand.description.trim(),
      expected_response: editCommand.expected_response.trim(),
      send_as_hex: editCommand.send_as_hex,
      show_notification: editCommand.show_notification,
      target_serial_id: editCommand.target_serial_id
    }

    const updatedCommand = await commandsAPI.updateCommand(editCommand.id, updateRequest)

    // 更新本地列表中的指令
    const index = savedCommands.value.findIndex(c => c.id === editCommand.id)
    if (index !== -1) {
      savedCommands.value[index] = {
        id: updatedCommand.id,
        name: updatedCommand.name,
        command: updatedCommand.command,
        description: updatedCommand.description,
        expected_response: updatedCommand.expected_response,
        send_as_hex: updatedCommand.send_as_hex,
        show_notification: updatedCommand.show_notification,
        target_serial_id: updatedCommand.target_serial_id,
        createdAt: updatedCommand.created_at
      }
    }

    // 清空表单并关闭弹窗
    editCommand.id = ''
    editCommand.name = ''
    editCommand.command = ''
    editCommand.description = ''
    editCommand.expected_response = ''
    editCommand.send_as_hex = false
    editCommand.show_notification = false
    editCommand.target_serial_id = undefined
    showEditCommand.value = false

    ElMessage.success('常用指令修改成功')
  } catch (error: any) {
    console.error('Failed to update command:', error)
    ElMessage.error(error.message || '修改指令失败')
  }
}

const handleCloseEditCommand = () => {
  // 清空表单
  editCommand.id = ''
  editCommand.name = ''
  editCommand.command = ''
  editCommand.description = ''
  editCommand.expected_response = ''
  editCommand.send_as_hex = false
  editCommand.show_notification = false
  editCommand.target_serial_id = undefined
  showEditCommand.value = false
}

const handleCommandRightClick = (_event: MouseEvent, cmd: SavedCommand) => {
  // 右键点击指令时，显示上下文菜单或执行特定操作
  // TODO: 实现右键菜单功能，可以快速编辑或删除指令
  console.log('Right click on command:', cmd.name)
}

const sendRawData = async () => {
  if (!rawForm.data.trim()) {
    ElMessage.error('请输入十六进制数据')
    return
  }
  
  if (!connectionStore.selectedSerialId) {
    ElMessage.error('请先选择一个串口')
    return
  }
  
  // 验证16进制格式
  const hexPattern = /^[0-9A-Fa-f\s]+$/
  const cleanData = rawForm.data.replace(/\s+/g, '')
  
  if (!hexPattern.test(rawForm.data)) {
    ElMessage.error('请输入有效的十六进制数据（只能包含0-9, A-F字符和空格）')
    return
  }
  
  if (cleanData.length % 2 !== 0) {
    ElMessage.error('十六进制数据长度必须为偶数（每个字节需要2个字符）')
    return
  }
  
  rawLoading.value = true
  try {
    await communicationStore.sendRawData(rawForm.data, connectionStore.selectedSerialId)
    ElMessage.success(`原始数据发送成功 (串口 #${connectionStore.selectedSerialId})`)
  } catch (error) {
    console.error('Send raw data error:', error)
  } finally {
    rawLoading.value = false
  }
}

// 格式化16进制输入
const formatHexInput = (value: string) => {
  // 移除非16进制字符，保留空格
  const cleaned = value.replace(/[^0-9A-Fa-f\s]/g, '')
  rawForm.data = cleaned.toUpperCase()
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
    
    // 构建CSV内容
    const csvContent = [
      ['时间', '方向', '描述', '数据', '状态'].join(','),
      ...logs.map(log => [
        `"${log.时间}"`,
        `"${log.方向}"`, 
        `"${log.描述}"`,
        `"${log.数据?.replace(/"/g, '""') || ''}"`,  // 处理数据中的引号
        `"${log.状态}"`
      ].join(','))
    ].join('\n')
    
    // 添加 BOM 以确保中文正确显示
    const BOM = '\uFEFF'
    const csvWithBOM = BOM + csvContent
    
    // 创建 Blob 对象
    const blob = new Blob([csvWithBOM], { 
      type: 'text/csv;charset=utf-8;' 
    })
    
    // 下载文件
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', `通信日志_${new Date().toISOString().slice(0, 10)}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    // 清理URL对象
    URL.revokeObjectURL(url)
    
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

const onSerialChange = (serialId: number) => {
  ElMessage.info(`切换到串口 #${serialId}`)
}

// 生命周期
onMounted(async () => {
  // 初始化通信状态
  
  if (!connectionStore.isConnected) {
    ElMessage.warning('请先连接串口')
    router.push('/serial-config')
    return
  }
  
  // 加载保存的指令
  await loadSavedCommands()
  
  // 初始化WebSocket连接
  try {
    await communicationStore.initializeWebSocket()
  } catch (error) {
    console.error('WebSocket初始化失败:', error)
    ElMessage.error('实时连接初始化失败')
  }
})


</script>

<style scoped>
.page-container {
  padding: 20px;
  background: #ffffff;
  height: calc(100vh - 70px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.status-bar {
  background: #ffffff;
  border: 1px solid #e0e6ed;
  border-radius: 16px;
  padding: 20px 28px;
  margin-bottom: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.status-info {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.serial-selector {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: #f0f8ff;
  border: 2px solid #409eff;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 500;
  color: #409eff;
}

.connection-badge {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  border-radius: 12px;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.connection-badge:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.connection-badge.connected {
  background: #f0f9f0;
  color: #2e7d32;
  border: 2px solid #4caf50;
}

.connection-badge.disconnected {
  background: #fef7f7;
  color: #c62828;
  border: 2px solid #f44336;
}

.realtime-badge {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  border-radius: 12px;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.realtime-badge:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.realtime-badge.connected {
  background: #f3f5ff;
  color: #1976d2;
  border: 2px solid #2196f3;
}

.realtime-badge.disconnected {
  background: #fffbf0;
  color: #f57c00;
  border: 2px solid #ff9800;
}

.connected-icon {
  color: #52c41a;
  font-size: 12px;
}

.disconnected-icon {
  color: #faad14;
  font-size: 12px;
}

.status-icon {
  font-size: 18px;
}

.status-text {
  font-weight: 600;
}

.main-row {
  flex: 1;
  height: 100%;
  margin: 0 -10px;
}

.main-row .el-col {
  height: 100%;
  padding: 0 10px;
}

.command-card {
  height: 100%;
  background: #ffffff;
  border: 1px solid #e0e6ed;
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
}

.command-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.18);
}

.log-card {
  height: 100%;
  background: #ffffff;
  border: 1px solid #e0e6ed;
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
}

.logs-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.18);
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

.form-section {
  flex-shrink: 0;
  margin-bottom: 20px;
}

.commands-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.quick-commands {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 16px;
  min-height: 40px;
  flex: 1;
  overflow-y: auto;
  padding-right: 8px;
}

.quick-commands::-webkit-scrollbar {
  width: 6px;
}

.quick-commands::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 3px;
}

.quick-commands::-webkit-scrollbar-thumb {
  background: #bdbdbd;
  border-radius: 3px;
}

.quick-commands::-webkit-scrollbar-thumb:hover {
  background: #9e9e9e;
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
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, 0.05);
  min-height: 0;
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


/* Element Plus 组件样式覆盖 */
:deep(.el-card) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

:deep(.el-card__header) {
  background: #f8f9fa;
  border-bottom: 1px solid #e0e6ed;
  font-weight: 600;
  font-size: 16px;
  color: #2d3748;
  flex-shrink: 0;
}

:deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 20px;
}

:deep(.el-button--primary) {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  border: none;
  border-radius: 12px;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.3);
  color: #ffffff !important;
}

:deep(.el-button--primary:hover) {
  background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.4);
  color: #ffffff !important;
}

:deep(.el-button--danger),
:deep(.clear-logs-btn) {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  border: none;
  border-radius: 12px;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: 0 4px 16px rgba(239, 68, 68, 0.3);
  color: #ffffff !important;
}

:deep(.el-button--danger:hover),
:deep(.clear-logs-btn:hover) {
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(239, 68, 68, 0.4);
  color: #ffffff !important;
}

:deep(.el-input__wrapper) {
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  border: 1px solid #d0d7de;
  transition: all 0.3s ease;
}

:deep(.el-input__wrapper:hover) {
  border-color: #1976d2;
  box-shadow: 0 2px 8px rgba(25, 118, 210, 0.15);
}

:deep(.el-input__wrapper.is-focus) {
  border-color: #1976d2;
  box-shadow: 0 0 0 3px rgba(25, 118, 210, 0.1);
}

:deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background: #1976d2;
  border-color: #1976d2;
}

/* 确保所有按钮文字颜色清晰 */
:deep(.el-button) {
  font-weight: 600;
}

/* 只对特定按钮应用flex布局 */
:deep(.el-input-group__append .el-button),
:deep(.header-actions .el-button),
:deep(.clear-logs-btn) {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

:deep(.el-button--primary),
:deep(.el-button--danger),
:deep(.el-button--success),
:deep(.el-button--warning),
:deep(.el-button--info) {
  color: #ffffff !important;
}

:deep(.el-button--primary:hover),
:deep(.el-button--danger:hover),
:deep(.el-button--success:hover),
:deep(.el-button--warning:hover),
:deep(.el-button--info:hover) {
  color: #ffffff !important;
}

:deep(.el-button--primary:active),
:deep(.el-button--danger:active),
:deep(.el-button--success:active),
:deep(.el-button--warning:active),
:deep(.el-button--info:active) {
  color: #ffffff !important;
}

/* 输入框追加按钮特殊处理 */
:deep(.el-input-group__append .el-button) {
  color: #ffffff !important;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 0 16px;
  min-height: 32px;
}

:deep(.el-input-group__append .el-button:hover) {
  color: #ffffff !important;
}

:deep(.el-input-group__append .el-button .el-icon) {
  display: flex;
  align-items: center;
  justify-content: center;
}

:deep(.el-dialog) {
  border-radius: 16px;
  overflow: hidden;
  backdrop-filter: blur(20px);
  background: rgba(255, 255, 255, 0.95);
}

:deep(.el-dialog__header) {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
  border-bottom: 2px solid rgba(102, 126, 234, 0.1);
}

/* 通信日志区域美化 */
.logs-container {
  height: 500px;
  overflow-y: auto;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 16px;
  margin-top: 20px;
  border: 1px solid #e9ecef;
}

.logs-container::-webkit-scrollbar {
  width: 8px;
}

.logs-container::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 4px;
}

.logs-container::-webkit-scrollbar-thumb {
  background: #bdbdbd;
  border-radius: 4px;
}

.logs-container::-webkit-scrollbar-thumb:hover {
  background: #9e9e9e;
}

.log-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 16px 20px;
  margin-bottom: 12px;
  border-radius: 16px;
  background: #ffffff;
  border: 1px solid #e0e6ed;
  border-left: 4px solid transparent;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.log-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.log-item.sent {
  border-left-color: #1976d2;
  background: #f8fbff;
}

.log-item.received {
  border-left-color: #2e7d32;
  background: #f1f8e9;
}

.log-item.failed {
  border-left-color: #d32f2f;
  background: #fef7f7;
}

.log-direction {
  font-size: 11px;
  padding: 6px 12px;
  border-radius: 20px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  min-width: 50px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.log-direction.sent {
  background: #1976d2;
  color: white;
}

.log-direction.received {
  background: #2e7d32;
  color: white;
}

.log-direction.failed {
  background: #d32f2f;
  color: white;
}

.log-data {
  font-family: 'SF Mono', 'Monaco', 'Cascadia Code', 'Roboto Mono', monospace;
  font-size: 13px;
  color: #2d3748;
  word-break: break-all;
  background: rgba(0, 0, 0, 0.03);
  padding: 12px 16px;
  border-radius: 10px;
  white-space: pre-wrap;
  border: 1px solid rgba(0, 0, 0, 0.06);
  line-height: 1.4;
}

/* 常用指令区域美化 */
.quick-commands {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-height: 300px;
  overflow-y: auto;
  padding: 8px 4px 8px 0;
}

.quick-commands::-webkit-scrollbar {
  width: 6px;
}

.quick-commands::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 3px;
}

.quick-commands::-webkit-scrollbar-thumb {
  background: #bdbdbd;
  border-radius: 3px;
}

.quick-commands::-webkit-scrollbar-thumb:hover {
  background: #9e9e9e;
}

.quick-command-btn {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  text-align: left;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  background: linear-gradient(135deg, #ffffff 0%, #f9fafb 100%);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  position: relative;
  overflow: hidden;
  min-height: 80px;
}

.command-content {
  flex: 1;
  min-width: 0;
  margin-right: 16px;
}

.command-actions {
  display: flex;
  gap: 8px;
  margin-left: 12px;
  flex-shrink: 0;
}

.quick-command-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #3b82f6, #8b5cf6, #06b6d4);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.3s ease;
}

.quick-command-btn:hover {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-color: #3b82f6;
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(59, 130, 246, 0.25);
}

.quick-command-btn:hover::before {
  transform: scaleX(1);
}

.quick-command-btn:active {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.2);
}

.quick-command-btn.disabled {
  opacity: 0.6;
  cursor: not-allowed;
  pointer-events: none;
}

.quick-command-btn.disabled:hover {
  transform: none;
  background: linear-gradient(135deg, #ffffff 0%, #f9fafb 100%);
  border-color: #e5e7eb;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
}

.quick-command-name {
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 8px;
  font-size: 16px;
  letter-spacing: -0.01em;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.quick-command-text {
  font-size: 13px;
  color: #6b7280;
  font-family: 'SF Mono', 'Monaco', 'Cascadia Code', 'Roboto Mono', monospace;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  padding: 10px 14px;
  border-radius: 8px;
  display: inline-block;
  border: 1px solid #e2e8f0;
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.05);
  transition: all 0.2s ease;
  margin-bottom: 6px;
  font-weight: 500;
  line-height: 1.5;
}

.quick-command-expected {
  font-size: 12px;
  color: #059669;
  font-family: 'SF Mono', 'Monaco', 'Cascadia Code', 'Roboto Mono', monospace;
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
  padding: 6px 12px;
  border-radius: 6px;
  display: inline-block;
  border: 1px solid #bbf7d0;
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.03);
  margin-top: 6px;
  border-left: 3px solid #10b981;
  font-weight: 500;
}

.quick-command-btn:hover .quick-command-text {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  border-color: #93c5fd;
  color: #1e40af;
}

.edit-icon,
.delete-icon {
  opacity: 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  padding: 8px;
  border-radius: 12px;
  font-size: 16px;
  border: 1px solid transparent;
}

.edit-icon {
  color: #3b82f6;
  background: rgba(59, 130, 246, 0.08);
  border-color: rgba(59, 130, 246, 0.2);
}

.delete-icon {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.08);
  border-color: rgba(239, 68, 68, 0.2);
}

.quick-command-btn:hover .edit-icon,
.quick-command-btn:hover .delete-icon {
  opacity: 1;
}

.edit-icon:hover {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(37, 99, 235, 0.1) 100%);
  transform: scale(1.1);
  border-color: rgba(59, 130, 246, 0.3);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.25);
}

.delete-icon:hover {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(220, 38, 38, 0.1) 100%);
  transform: scale(1.1) rotate(5deg);
  border-color: rgba(239, 68, 68, 0.3);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.25);
}

.command-controls {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  padding: 8px 0;
}

.command-controls .el-button {
  font-size: 12px;
  padding: 4px 12px;
}

.no-logs {
  text-align: center;
  color: #a0aec0;
  padding: 60px 20px;
  font-size: 16px;
}

.no-logs .el-icon {
  font-size: 64px;
  margin-bottom: 20px;
  opacity: 0.3;
  background: linear-gradient(45deg, #94a3b8, #64748b);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* 常用指令区域布局 */
.command-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 16px;
  padding: 16px 0;
  border-bottom: 1px solid #f1f5f9;
}

.command-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 8px;
}

.command-title::before {
  content: '';
  width: 4px;
  height: 20px;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  border-radius: 2px;
}

.command-actions {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.command-actions .el-button {
  font-size: 13px;
  padding: 8px 16px;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.command-actions .el-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* 修复小按钮的内部对齐 */
:deep(.el-button--small) {
  padding: 5px 11px;
  font-size: 12px;
  border-radius: 8px;
}

:deep(.el-button--small .el-icon) {
  margin-right: 4px;
}

/* 修复按钮组间距 */
.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}


</style>