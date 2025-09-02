<template>
  <div class="terminal-container">
    <div class="terminal-header">
      <div class="terminal-title">
        <el-icon><Monitor /></el-icon>
        <span>Industrial HMI Terminal</span>
      </div>
      <div class="terminal-controls">
        <el-tag 
          :type="connectionStatusType" 
          size="small"
          class="status-tag"
        >
          {{ connectionStatusText }}
        </el-tag>
        <el-button 
          v-if="!isConnected" 
          @click="handleConnect"
          :loading="isConnecting"
          size="small"
          type="primary"
        >
          {{ isConnecting ? '连接中...' : '连接' }}
        </el-button>
        <el-button 
          v-else
          @click="handleDisconnect"
          size="small"
          type="danger"
        >
          断开
        </el-button>
        <el-button 
          @click="handleClear"
          size="small"
        >
          清屏
        </el-button>
      </div>
    </div>

    <div 
      class="terminal-content"
      ref="terminalContentRef"
      @click="focusInput"
    >
      <div class="terminal-messages">
        <div 
          v-for="message in messages" 
          :key="message.id"
          :class="getMessageClass(message)"
          class="terminal-message"
        >
          <span class="message-timestamp">{{ formatTimestamp(message.timestamp) }}</span>
          <pre class="message-content">{{ message.content }}</pre>
        </div>
      </div>

      <div class="terminal-input-line" v-if="isConnected">
        <span class="terminal-prompt">$</span>
        <input
          ref="commandInputRef"
          v-model="currentCommand"
          @keydown="handleKeyDown"
          @keyup="handleKeyUp"
          class="terminal-input"
          placeholder="输入命令..."
          autocomplete="off"
          spellcheck="false"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onUnmounted, watch } from 'vue'
import { ElButton, ElTag, ElIcon, ElMessage } from 'element-plus'
import { Monitor } from '@element-plus/icons-vue'
import { useTerminalStore } from '@/stores/terminal'

// Store
const terminalStore = useTerminalStore()

// Refs
const terminalContentRef = ref<HTMLElement>()
const commandInputRef = ref<HTMLInputElement>()

// 计算属性
const messages = computed(() => terminalStore.messages)
const isConnected = computed(() => terminalStore.isConnected)
const isConnecting = computed(() => terminalStore.isConnecting)
const currentCommand = computed({
  get: () => terminalStore.currentCommand,
  set: (value: string) => terminalStore.setCurrentCommand(value)
})

const connectionStatusType = computed(() => {
  switch (terminalStore.connectionStatus) {
    case 'connected': return 'success'
    case 'connecting': return 'warning'
    default: return 'danger'
  }
})

const connectionStatusText = computed(() => {
  switch (terminalStore.connectionStatus) {
    case 'connected': return '已连接'
    case 'connecting': return '连接中'
    default: return '未连接'
  }
})

// 方法
const handleConnect = async () => {
  try {
    await terminalStore.connect()
    ElMessage.success('WebSocket连接成功')
    // 连接成功后聚焦输入框
    nextTick(() => {
      focusInput()
    })
  } catch (error) {
    ElMessage.error('WebSocket连接失败')
  }
}

const handleDisconnect = () => {
  terminalStore.disconnect()
  ElMessage.info('WebSocket连接已断开')
}

const handleClear = () => {
  terminalStore.clearMessages()
}

const handleKeyDown = (event: KeyboardEvent) => {
  switch (event.key) {
    case 'Enter':
      if (currentCommand.value.trim()) {
        terminalStore.sendCommand(currentCommand.value)
        // 滚动到底部
        nextTick(() => {
          scrollToBottom()
        })
      }
      event.preventDefault()
      break

    case 'ArrowUp':
      event.preventDefault()
      const prevCommand = terminalStore.getPreviousCommand()
      if (prevCommand !== undefined) {
        currentCommand.value = prevCommand
      }
      break

    case 'ArrowDown':
      event.preventDefault()
      const nextCommand = terminalStore.getNextCommand()
      currentCommand.value = nextCommand
      break

    case 'Tab':
      event.preventDefault()
      // 这里可以添加命令自动补全功能
      break

    case 'c':
      if (event.ctrlKey) {
        // Ctrl+C 清空当前命令
        event.preventDefault()
        currentCommand.value = ''
      }
      break

    case 'l':
      if (event.ctrlKey) {
        // Ctrl+L 清屏
        event.preventDefault()
        handleClear()
      }
      break
  }
}

const handleKeyUp = (_event: KeyboardEvent) => {
  // 处理按键释放事件（如果需要）
}

const focusInput = () => {
  if (commandInputRef.value && isConnected.value) {
    commandInputRef.value.focus()
  }
}

const scrollToBottom = () => {
  if (terminalContentRef.value) {
    terminalContentRef.value.scrollTop = terminalContentRef.value.scrollHeight
  }
}

const getMessageClass = (message: any) => {
  return {
    'message-command': message.type === 'command',
    'message-response': message.type === 'response',
    'message-error': message.type === 'error',
    'message-info': message.type === 'info',
    'message-system': message.type === 'system',
    'message-success': message.success === true,
    'message-failed': message.success === false
  }
}

const formatTimestamp = (timestamp: Date) => {
  return timestamp.toLocaleTimeString('zh-CN', { 
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 监听消息变化，自动滚动到底部
watch(messages, () => {
  nextTick(() => {
    scrollToBottom()
  })
}, { deep: true })

// 生命周期
onMounted(() => {
  // 自动连接
  handleConnect()
  
  // 聚焦输入框
  nextTick(() => {
    focusInput()
  })
})

onUnmounted(() => {
  // 组件销毁时断开连接
  terminalStore.disconnect()
})
</script>

<style scoped>
.terminal-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #1e1e1e;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.terminal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background-color: #2d2d2d;
  border-bottom: 1px solid #404040;
}

.terminal-title {
  display: flex;
  align-items: center;
  color: #ffffff;
  font-weight: 600;
  gap: 8px;
}

.terminal-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-tag {
  margin-right: 8px;
}

.terminal-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background-color: #1e1e1e;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 14px;
  line-height: 1.5;
  cursor: text;
}

.terminal-messages {
  margin-bottom: 16px;
}

.terminal-message {
  margin-bottom: 8px;
  word-wrap: break-word;
}

.message-timestamp {
  color: #666666;
  font-size: 12px;
  margin-right: 8px;
}

.message-content {
  display: inline;
  margin: 0;
  font-family: inherit;
  white-space: pre-wrap;
  word-break: break-word;
}

.message-command .message-content {
  color: #4CAF50;
  font-weight: 600;
}

.message-response .message-content {
  color: #ffffff;
}

.message-error .message-content {
  color: #f56565;
}

.message-info .message-content {
  color: #63b3ed;
}

.message-system .message-content {
  color: #fbb6ce;
  font-style: italic;
}

.message-failed .message-content {
  color: #f56565;
}

.terminal-input-line {
  display: flex;
  align-items: center;
  color: #ffffff;
}

.terminal-prompt {
  color: #4CAF50;
  margin-right: 8px;
  font-weight: 600;
}

.terminal-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: #ffffff;
  font-family: inherit;
  font-size: inherit;
  line-height: inherit;
}

.terminal-input::placeholder {
  color: #666666;
}

/* 滚动条样式 */
.terminal-content::-webkit-scrollbar {
  width: 6px;
}

.terminal-content::-webkit-scrollbar-track {
  background: #2d2d2d;
}

.terminal-content::-webkit-scrollbar-thumb {
  background: #555555;
  border-radius: 3px;
}

.terminal-content::-webkit-scrollbar-thumb:hover {
  background: #777777;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .terminal-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .terminal-controls {
    justify-content: center;
  }
  
  .terminal-content {
    padding: 12px;
    font-size: 13px;
  }
}
</style>