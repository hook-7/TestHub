<template>
  <div class="serial-test-page">
    <el-card class="test-card">
      <template #header>
        <div class="card-header">
          <h3>
            <el-icon><Setting /></el-icon>
            Web Serial API 测试页面
          </h3>
        </div>
      </template>

      <div class="test-content">
        <!-- 兼容性检查 -->
        <div class="test-section">
          <h4>浏览器兼容性检查</h4>
          <el-alert
            :title="compatibilityMessage"
            :type="isWebSerialSupported ? 'success' : 'warning'"
            :closable="false"
            show-icon
          />
        </div>

        <!-- 串口连接测试 -->
        <div class="test-section" v-if="isWebSerialSupported">
          <h4>串口连接测试</h4>
          <el-button 
            type="primary" 
            @click="testConnect"
            :loading="connecting"
            :disabled="!isWebSerialSupported"
          >
            <el-icon><Connection /></el-icon>
            测试连接串口
          </el-button>
          
          <div v-if="connectionResult" class="result-display">
            <el-alert
              :title="connectionResult.success ? '连接成功' : '连接失败'"
              :type="connectionResult.success ? 'success' : 'error'"
              :closable="false"
              show-icon
            >
              <template #default>
                <p>{{ connectionResult.message }}</p>
                <pre v-if="connectionResult.details">{{ connectionResult.details }}</pre>
              </template>
            </el-alert>
          </div>
        </div>

        <!-- 指令发送测试 -->
        <div class="test-section" v-if="isConnected">
          <h4>指令发送测试</h4>
          <el-input
            v-model="testCommand"
            placeholder="输入测试指令，例如: AT+GMR"
            style="margin-bottom: 12px;"
          />
          <el-button 
            type="primary" 
            @click="testSendCommand"
            :loading="sending"
          >
            <el-icon><Position /></el-icon>
            发送指令
          </el-button>
          
          <div v-if="commandResult" class="result-display">
            <el-alert
              :title="commandResult.success ? '指令发送成功' : '指令发送失败'"
              :type="commandResult.success ? 'success' : 'error'"
              :closable="false"
              show-icon
            >
              <template #default>
                <p>{{ commandResult.message }}</p>
                <pre v-if="commandResult.details">{{ commandResult.details }}</pre>
              </template>
            </el-alert>
          </div>
        </div>

        <!-- 断开连接 -->
        <div class="test-section" v-if="isConnected">
          <h4>断开连接</h4>
          <el-button 
            type="danger" 
            @click="testDisconnect"
            :loading="disconnecting"
          >
            <el-icon><Close /></el-icon>
            断开串口连接
          </el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Setting, Connection, Position, Close } from '@element-plus/icons-vue'
import { webSerialService } from '@/services/webSerial'
import { useConnectionStore } from '@/stores/connection'

const connectionStore = useConnectionStore()

// 状态
const isWebSerialSupported = ref(false)
const compatibilityMessage = ref('')
const connecting = ref(false)
const sending = ref(false)
const disconnecting = ref(false)
const testCommand = ref('AT+GMR')
const connectionResult = ref<{
  success: boolean
  message: string
  details?: string
} | null>(null)
const commandResult = ref<{
  success: boolean
  message: string
  details?: string
} | null>(null)

// 计算属性
const isConnected = computed(() => connectionStore.isConnected)

// 检查Web Serial API支持
const checkWebSerialSupport = () => {
  try {
    isWebSerialSupported.value = webSerialService.isSupported()
    if (!isWebSerialSupported.value) {
      compatibilityMessage.value = '当前浏览器不支持Web Serial API'
    } else {
      compatibilityMessage.value = 'Web Serial API支持正常'
    }
  } catch (error) {
    isWebSerialSupported.value = false
    compatibilityMessage.value = 'Web Serial API检查失败'
    console.error('Web Serial API check failed:', error)
  }
}

// 测试连接串口
const testConnect = async () => {
  if (!isWebSerialSupported.value) {
    ElMessage.error('当前浏览器不支持Web Serial API')
    return
  }

  connecting.value = true
  connectionResult.value = null

  try {
    const config = {
      port: 'test-port',
      baudrate: 115200,
      bytesize: 8,
      parity: 'none',
      stopbits: 1,
      timeout: 0.5
    }

    const response = await webSerialService.connectSerial(config)
    
    connectionResult.value = {
      success: true,
      message: `串口连接成功！分配ID: ${response.serial_id}`,
      details: JSON.stringify(response, null, 2)
    }

    ElMessage.success('串口连接测试成功')
  } catch (error: any) {
    connectionResult.value = {
      success: false,
      message: `串口连接失败: ${error.message}`,
      details: error.stack
    }

    ElMessage.error('串口连接测试失败')
  } finally {
    connecting.value = false
  }
}

// 测试发送指令
const testSendCommand = async () => {
  if (!isConnected.value) {
    ElMessage.error('请先连接串口')
    return
  }

  sending.value = true
  commandResult.value = null

  try {
    const response = await webSerialService.sendATCommand(testCommand.value)
    
    commandResult.value = {
      success: true,
      message: `指令发送成功`,
      details: JSON.stringify(response, null, 2)
    }

    ElMessage.success('指令发送测试成功')
  } catch (error: any) {
    commandResult.value = {
      success: false,
      message: `指令发送失败: ${error.message}`,
      details: error.stack
    }

    ElMessage.error('指令发送测试失败')
  } finally {
    sending.value = false
  }
}

// 测试断开连接
const testDisconnect = async () => {
  disconnecting.value = true

  try {
    await webSerialService.disconnectSerial()
    
    ElMessage.success('串口断开测试成功')
  } catch (error: any) {
    ElMessage.error(`串口断开测试失败: ${error.message}`)
  } finally {
    disconnecting.value = false
  }
}

// 生命周期
onMounted(() => {
  checkWebSerialSupport()
})
</script>

<style scoped>
.serial-test-page {
  padding: 24px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: 100vh;
}

.test-card {
  max-width: 800px;
  margin: 0 auto;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.test-content {
  padding: 20px 0;
}

.test-section {
  margin-bottom: 32px;
  padding: 20px;
  background: #fafbfc;
  border-radius: 12px;
  border: 1px solid var(--el-border-color-lighter);
}

.test-section h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.test-section h4::before {
  content: '';
  width: 4px;
  height: 16px;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  border-radius: 2px;
}

.result-display {
  margin-top: 16px;
}

.result-display pre {
  background: #f8f9fa;
  padding: 12px;
  border-radius: 8px;
  border: 1px solid #e9ecef;
  font-size: 12px;
  color: #495057;
  white-space: pre-wrap;
  word-break: break-all;
  margin-top: 8px;
}

.el-button {
  margin-right: 12px;
  margin-bottom: 8px;
}

.el-input {
  margin-bottom: 12px;
}
</style>
