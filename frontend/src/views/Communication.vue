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
                AT指令交互
              </h3>
            </div>
          </template>

          <!-- AT指令输入区 -->
          <el-form :model="atForm" label-width="80px">
            <el-form-item label="AT指令">
              <el-input
                v-model="atForm.command"
                placeholder="输入AT指令，例如: AT+GMR"
                style="font-family: monospace;"
                @keyup.enter="sendATCommand"
              >
                <template #append>
                  <el-button 
                    type="primary" 
                    @click="sendATCommand"
                    :disabled="!connectionStore.isConnected"
                    :loading="atLoading"
                  >
                    <el-icon><Position /></el-icon>
                    发送
                  </el-button>
                </template>
              </el-input>
            </el-form-item>
          </el-form>

          <!-- 常用AT指令快捷按钮 -->
          <div style="margin-top: 20px;">
            <h4>常用AT指令</h4>
            <div class="quick-commands">
              <el-button 
                v-for="cmd in quickCommands" 
                :key="cmd.command"
                size="small"
                @click="sendQuickCommand(cmd.command)"
                :disabled="!connectionStore.isConnected"
                :title="cmd.description"
              >
                {{ cmd.command }}
              </el-button>
            </div>
          </div>

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
const atLoading = ref(false)
const rawLoading = ref(false)

// 表单数据
const atForm = reactive({
  command: '',
})

const rawForm = reactive({
  data: '',
})

// 常用AT指令
const quickCommands = [
  { command: 'AT', description: '测试连接' },
  { command: 'AT+GMR', description: '查询固件版本' },
  { command: 'AT+CGMI', description: '查询制造商' },
  { command: 'AT+CGMM', description: '查询模块型号' },
  { command: 'AT+CGMR', description: '查询软件版本' },
  { command: 'AT+CGSN', description: '查询IMEI' },
  { command: 'AT+CIMI', description: '查询IMSI' },
  { command: 'AT+CCID', description: '查询ICCID' },
  { command: 'AT+CSQ', description: '查询信号强度' },
  { command: 'AT+CREG?', description: '查询网络注册状态' },
  { command: 'AT+CGATT?', description: '查询GPRS附着状态' },
  { command: 'AT+COPS?', description: '查询运营商' },
]

// 方法
const sendATCommand = async () => {
  if (!atForm.command.trim()) {
    ElMessage.error('请输入AT指令')
    return
  }
  
  atLoading.value = true
  try {
    const result = await communicationStore.sendATCommand(atForm.command)
    ElMessage.success('AT指令发送成功')
    // 清空输入框或保留，根据用户习惯
    // atForm.command = ''
  } catch (error) {
    console.error('Send AT command error:', error)
  } finally {
    atLoading.value = false
  }
}

const sendQuickCommand = async (command: string) => {
  atForm.command = command
  await sendATCommand()
}

const sendRawData = async () => {
  if (!rawForm.data.trim()) {
    ElMessage.error('请输入十六进制数据')
    return
  }
  
  rawLoading.value = true
  try {
    const result = await communicationStore.sendRawData(rawForm.data)
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
</style>