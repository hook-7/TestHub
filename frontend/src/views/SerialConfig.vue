<template>
  <div class="page-container">
    <!-- 会话状态卡片 -->
    <el-card class="session-card">
      <template #header>
        <div class="card-header">
          <h4>
            <el-icon><User /></el-icon>
            连接状态
          </h4>
          <el-button 
            v-if="sessionStore.isLoggedIn"
            type="danger" 
            @click="logout"
            :loading="sessionStore.isLoading"
            size="small"
          >
            <el-icon><SwitchButton /></el-icon>
            登出
          </el-button>
          <el-button 
            v-else
            type="primary" 
            @click="login"
            :loading="sessionStore.isLoading"
            size="small"
          >
            <el-icon><Connection /></el-icon>
            登录
          </el-button>
        </div>
      </template>

      <div class="session-status">
        <el-row :gutter="16">
          <el-col :span="12">
            <div class="status-item">
              <span class="label">登录状态:</span>
              <el-tag 
                :type="sessionStore.isLoggedIn ? 'success' : 'info'"
                size="small"
              >
                {{ sessionStore.isLoggedIn ? '已登录' : '未登录' }}
              </el-tag>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="status-item">
              <span class="label">会话状态:</span>
              <el-tag 
                :type="sessionStore.hasActiveSession ? 'success' : 'warning'"
                size="small"
              >
                {{ sessionStore.hasActiveSession ? '有活跃会话' : '无活跃会话' }}
              </el-tag>
            </div>
          </el-col>
        </el-row>
        
        <div v-if="sessionStore.currentSession" class="session-info">
          <el-descriptions :column="2" size="small" border>
            <el-descriptions-item label="会话ID">
              {{ sessionStore.currentSession.session_id.substring(0, 8) }}...
            </el-descriptions-item>
            <el-descriptions-item label="客户端IP">
              {{ sessionStore.currentSession.client_ip }}
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">
              {{ formatTime(sessionStore.currentSession.created_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="最后活动">
              {{ formatTime(sessionStore.currentSession.last_activity) }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
    </el-card>

    <!-- 串口配置卡片 -->
    <el-card>
      <template #header>
        <div class="card-header">
          <h3>
            <el-icon><Setting /></el-icon>
            串口配置
          </h3>
          <div class="header-actions">
            <el-button 
              type="primary" 
              @click="loadPorts"
              :loading="loading"
              size="small"
            >
              <el-icon><Refresh /></el-icon>
              刷新端口
            </el-button>
            <el-button 
              v-if="sessionStore.hasActiveSession && !sessionStore.isLoggedIn"
              type="warning" 
              @click="forceCleanup"
              size="small"
            >
              <el-icon><Delete /></el-icon>
              强制清理
            </el-button>
          </div>
        </div>
      </template>

      <el-form 
        ref="formRef"
        :model="form" 
        :rules="rules"
        label-width="100px"
        size="large"
      >
        <!-- 串口选择 -->
        <div class="form-row">
          <el-form-item label="串口" prop="port">
            <el-select 
              v-model="form.port" 
              placeholder="选择串口"
              style="width: 100%"
              @focus="loadPorts"
            >
              <el-option
                v-for="port in connectionStore.availablePorts"
                :key="port.device"
                :label="`${port.device} - ${port.description}`"
                :value="port.device"
              >
                <div style="display: flex; justify-content: space-between;">
                  <span>{{ port.device }}</span>
                  <span style="color: var(--el-text-color-secondary); font-size: 12px;">
                    {{ port.description }}
                  </span>
                </div>
              </el-option>
            </el-select>
          </el-form-item>
          
          <el-form-item>
            <el-button 
              @click="autoDetect"
              :loading="autoDetecting"
              type="success"
              plain
            >
              <el-icon><Search /></el-icon>
              自动检测
            </el-button>
          </el-form-item>
        </div>

        <!-- 串口参数 -->
        <div class="form-row">
          <el-form-item label="波特率" prop="baudrate">
            <el-select v-model="form.baudrate">
              <el-option label="9600" :value="9600" />
              <el-option label="19200" :value="19200" />
              <el-option label="38400" :value="38400" />
              <el-option label="57600" :value="57600" />
              <el-option label="115200" :value="115200" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="数据位" prop="bytesize">
            <el-select v-model="form.bytesize">
              <el-option label="7" :value="7" />
              <el-option label="8" :value="8" />
            </el-select>
          </el-form-item>
        </div>

        <div class="form-row">
          <el-form-item label="校验位" prop="parity">
            <el-select v-model="form.parity">
              <el-option label="无校验 (N)" value="N" />
              <el-option label="偶校验 (E)" value="E" />
              <el-option label="奇校验 (O)" value="O" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="停止位" prop="stopbits">
            <el-select v-model="form.stopbits">
              <el-option label="1" :value="1" />
              <el-option label="2" :value="2" />
            </el-select>
          </el-form-item>
        </div>

        <el-form-item label="超时(秒)" prop="timeout">
          <el-input-number 
            v-model="form.timeout"
            :min="0.1"
            :max="10"
            :step="0.1"
            :precision="1"
            style="width: 100%"
          />
        </el-form-item>

        <!-- 操作按钮 -->
        <el-form-item>
          <div style="display: flex; gap: 16px;">
            <el-button 
              type="primary" 
              @click="connect"
              :loading="connecting"
              :disabled="connectionStore.isConnected || !sessionStore.isLoggedIn"
              size="large"
            >
              <el-icon><Connection /></el-icon>
              连接串口
            </el-button>
            
            <el-button 
              type="danger" 
              @click="disconnect"
              :loading="disconnecting"
              :disabled="!connectionStore.isConnected || !sessionStore.isLoggedIn"
              size="large"
            >
              <el-icon><Close /></el-icon>
              断开连接
            </el-button>
            
            <el-button 
              @click="testConnection"
              :disabled="!connectionStore.isConnected || !sessionStore.isLoggedIn"
              size="large"
            >
              <el-icon><CircleCheck /></el-icon>
              测试连接
            </el-button>
            
            <el-button 
              @click="goToCommunication"
              type="success"
              :disabled="!connectionStore.isConnected || !sessionStore.isLoggedIn"
              size="large"
            >
              <el-icon><Message /></el-icon>
              通信测试
            </el-button>
          </div>
          
          <!-- 未登录提示 -->
          <div v-if="!sessionStore.isLoggedIn" class="login-hint">
            <el-alert
              title="请先登录后再进行串口操作"
              type="warning"
              :closable="false"
              show-icon
            />
          </div>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 连接状态 -->
    <el-card style="margin-top: 20px;" v-if="connectionStore.isConnected">
      <template #header>
        <h3>
          <el-icon><InfoFilled /></el-icon>
          连接信息
        </h3>
      </template>
      
      <el-descriptions :column="2" border>
        <el-descriptions-item label="端口">{{ connectionStore.status.port }}</el-descriptions-item>
        <el-descriptions-item label="波特率">{{ connectionStore.status.baudrate }}</el-descriptions-item>
        <el-descriptions-item label="数据位">{{ connectionStore.status.bytesize }}</el-descriptions-item>
        <el-descriptions-item label="校验位">{{ connectionStore.status.parity }}</el-descriptions-item>
        <el-descriptions-item label="停止位">{{ connectionStore.status.stopbits }}</el-descriptions-item>
        <el-descriptions-item label="超时">{{ connectionStore.status.timeout }}s</el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { useConnectionStore } from '@/stores/connection'
import { useCommunicationStore } from '@/stores/communication'
import { useSessionStore } from '@/stores/session'

const router = useRouter()
const connectionStore = useConnectionStore()
const communicationStore = useCommunicationStore()
const sessionStore = useSessionStore()

// 表单引用
const formRef = ref<FormInstance>()

// 状态
const loading = ref(false)
const connecting = ref(false)
const disconnecting = ref(false)
const autoDetecting = ref(false)

// 表单数据
const form = reactive({
  port: '',
  baudrate: 9600,
  bytesize: 8,
  parity: 'N',
  stopbits: 1,
  timeout: 1.0,
})

// 表单验证规则
const rules: FormRules = {
  port: [
    { required: true, message: '请选择串口', trigger: 'change' }
  ],
  baudrate: [
    { required: true, message: '请选择波特率', trigger: 'change' }
  ],
}

// 方法
const loadPorts = async () => {
  loading.value = true
  try {
    await connectionStore.loadAvailablePorts()
  } finally {
    loading.value = false
  }
}

const autoDetect = async () => {
  autoDetecting.value = true
  try {
    const detectedPort = await connectionStore.autoDetectPort()
    if (detectedPort) {
      form.port = detectedPort
      ElMessage.success(`自动检测到串口: ${detectedPort}`)
    } else {
      ElMessage.warning('未检测到可用串口')
    }
  } finally {
    autoDetecting.value = false
  }
}

const connect = async () => {
  if (!formRef.value) return
  
  const valid = await formRef.value.validate()
  if (!valid) return
  
  connecting.value = true
  try {
    const success = await connectionStore.connect(form)
    if (success) {
      ElMessage.success('串口连接成功')
    }
  } finally {
    connecting.value = false
  }
}

const disconnect = async () => {
  disconnecting.value = true
  try {
    const success = await connectionStore.disconnect()
    if (success) {
      ElMessage.success('串口断开成功')
    }
  } finally {
    disconnecting.value = false
  }
}

const testConnection = async () => {
  try {
    // 简单的指令测试
    await communicationStore.sendATCommand('AT\r\n')
    ElMessage.success('连接测试成功')
  } catch (error) {
    ElMessage.warning('连接测试失败，请检查设备连接')
  }
}

const goToCommunication = () => {
  router.push('/communication')
}

// 会话管理方法
const login = async () => {
  try {
    const success = await sessionStore.login()
    if (success) {
      // 登录成功后刷新会话状态
      await sessionStore.refreshSessionStatus()
    }
  } catch (error) {
    console.error('Login failed:', error)
  }
}

const logout = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要登出吗？登出后将无法进行串口操作。',
      '确认登出',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    await sessionStore.logout()
    // 登出后刷新会话状态
    await sessionStore.refreshSessionStatus()
  } catch (error) {
    // 用户取消操作
    if (error !== 'cancel') {
      console.error('Logout failed:', error)
    }
  }
}

const forceCleanup = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要强制清理所有会话吗？这将断开其他客户端的连接。',
      '强制清理会话',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    const success = await sessionStore.forceCleanup()
    if (success) {
      // 清理成功后可以尝试登录
      await login()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Force cleanup failed:', error)
    }
  }
}

// 格式化时间
const formatTime = (timeStr: string) => {
  return new Date(timeStr).toLocaleString()
}

// 生命周期
onMounted(async () => {
  // 初始化会话管理
  await sessionStore.init()
  
  loadPorts()
  connectionStore.checkStatus()
})
</script>

<style scoped>
.page-container {
  max-width: 800px;
}

.session-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.session-status {
  margin-top: 16px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.status-item .label {
  font-weight: 500;
  color: var(--el-text-color-regular);
}

.session-info {
  margin-top: 16px;
}

.login-hint {
  margin-top: 16px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }
  
  .card-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .header-actions {
    justify-content: center;
  }
}
</style>