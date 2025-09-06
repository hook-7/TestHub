<template>
  <div class="page-container">
    <!-- 多串口功能提示 -->
    <el-alert
      title="多串口支持"
      type="info"
      :closable="false"
      style="margin-bottom: 20px;"
    >
      <template #default>
        <p>✨ 支持同时连接多个串口设备，每个串口分配唯一ID (按连接顺序递增)</p>
        <p>🔗 可以为常用指令指定特定的目标串口，或使用当前选择的串口</p>
        <p>📊 通信日志会显示每个操作关联的串口信息</p>
      </template>
    </el-alert>

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
                v-for="port in availableUnconnectedPorts"
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
              <el-option
                v-if="availableUnconnectedPorts.length === 0"
                disabled
                label="暂无可用串口 (所有串口已连接或无串口设备)"
                value=""
              />
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
              size="large"
            >
              <el-icon><Connection /></el-icon>
              {{ connectionStore.isConnected ? '连接新串口' : '连接串口' }}
            </el-button>
            
            <el-button 
              type="danger" 
              @click="disconnectAll"
              :loading="disconnectingAll"
              :disabled="!connectionStore.isConnected"
              size="large"
            >
              <el-icon><Close /></el-icon>
              断开连接
            </el-button>
            
            <el-button 
              @click="testConnection"
              :disabled="!connectionStore.isConnected"
              size="large"
            >
              <el-icon><CircleCheck /></el-icon>
              测试连接
            </el-button>
            
            <el-button 
              @click="goToCommunication"
              type="success"
              :disabled="!connectionStore.isConnected"
              size="large"
            >
              <el-icon><Message /></el-icon>
              通信测试
            </el-button>
            
            <el-button 
              @click="connectMultiplePorts"
              type="info"
              :loading="connectingMultiple"
              size="large"
              v-if="availableUnconnectedPorts.length >= 2"
            >
              <el-icon><Connection /></el-icon>
              快速连接多个串口
            </el-button>
          </div>
          

        </el-form-item>
      </el-form>
    </el-card>

    <!-- 已连接串口列表 -->
    <el-card style="margin-top: 20px;" v-if="connectionStore.isConnected">
      <template #header>
        <div class="card-header">
          <h3>
            <el-icon><InfoFilled /></el-icon>
            已连接串口 ({{ connectionStore.connectedSerials.length }})
          </h3>
          <div class="header-actions">
            <el-button 
              type="success" 
              size="small" 
              @click="loadPorts"
              :loading="loading"
            >
              <el-icon><Refresh /></el-icon>
              刷新端口
            </el-button>
            <el-button 
              type="danger" 
              size="small" 
              @click="disconnectAll"
              :loading="disconnectingAll"
            >
              <el-icon><Close /></el-icon>
              断开所有
            </el-button>
          </div>
        </div>
      </template>
      
      <div class="connected-serials">
        <div 
          v-for="serial in connectionStore.connectedSerials" 
          :key="serial.serial_id"
          class="serial-card"
          :class="{ active: connectionStore.selectedSerialId === serial.serial_id }"
          @click="connectionStore.selectSerial(serial.serial_id)"
        >
          <div class="serial-header">
            <div class="serial-info">
              <div class="serial-id">串口 #{{ serial.serial_id }}</div>
              <div class="serial-port">{{ serial.port }}</div>
            </div>
            <div class="serial-actions">
              <el-tag 
                v-if="connectionStore.selectedSerialId === serial.serial_id" 
                type="success" 
                size="small"
              >
                当前选择
              </el-tag>
              <el-button 
                type="danger" 
                size="small" 
                @click.stop="disconnectSerial(serial.serial_id)"
                :loading="disconnectingSerials[serial.serial_id]"
              >
                <el-icon><Close /></el-icon>
                断开
              </el-button>
            </div>
          </div>
          
          <el-descriptions :column="3" size="small" class="serial-details">
            <el-descriptions-item label="波特率">{{ serial.baudrate }}</el-descriptions-item>
            <el-descriptions-item label="数据位">{{ serial.bytesize }}</el-descriptions-item>
            <el-descriptions-item label="校验位">{{ serial.parity }}</el-descriptions-item>
            <el-descriptions-item label="停止位">{{ serial.stopbits }}</el-descriptions-item>
            <el-descriptions-item label="超时">{{ serial.timeout }}s</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag type="success" size="small">已连接</el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { useConnectionStore } from '@/stores/connection'
import { useCommunicationStore } from '@/stores/communication'

const router = useRouter()
const connectionStore = useConnectionStore()
const communicationStore = useCommunicationStore()

// 表单引用
const formRef = ref<FormInstance>()

// 计算属性 - 过滤掉已连接的串口
const availableUnconnectedPorts = computed(() => {
  const connectedPorts = connectionStore.connectedSerials.map(s => s.port)
  return connectionStore.availablePorts.filter(port => !connectedPorts.includes(port.device))
})

// 状态
const loading = ref(false)
const connecting = ref(false)
const disconnecting = ref(false)
const disconnectingAll = ref(false)
const disconnectingSerials = ref<Record<number, boolean>>({})
const autoDetecting = ref(false)
const connectingMultiple = ref(false)


const form = reactive({
  port: '',
  baudrate: 115200,  
  bytesize: 8,
  parity: 'E',
  stopbits: 1,
  timeout: 0.5,  
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
  
  // 检查是否已经连接了相同的串口
  const existingSerial = connectionStore.connectedSerials.find(s => s.port === form.port)
  if (existingSerial) {
    ElMessage.warning(`串口 ${form.port} 已经连接 (ID: ${existingSerial.serial_id})`)
    return
  }
  
  connecting.value = true
  try {
    const response = await connectionStore.connect(form)
    ElMessage.success(`串口连接成功！分配ID: ${response.serial_id}`)
    // 连接成功后清空端口选择，保持其他配置参数
    form.port = ''
    // 刷新端口列表以更新可用端口
    await loadPorts()
  } catch (error: any) {
    ElMessage.error(error.message || '串口连接失败')
  } finally {
    connecting.value = false
  }
}

const disconnectSerial = async (serialId: number) => {
  disconnectingSerials.value[serialId] = true
  try {
    const success = await connectionStore.disconnect(serialId)
    if (success) {
      ElMessage.success(`串口 ${serialId} 断开成功`)
      // 刷新端口列表以更新可用端口
      await loadPorts()
    }
  } catch (error: any) {
    ElMessage.error(error.message || '串口断开失败')
  } finally {
    disconnectingSerials.value[serialId] = false
  }
}

const disconnectAll = async () => {
  disconnectingAll.value = true
  try {
    const success = await connectionStore.disconnect()
    if (success) {
      ElMessage.success('所有串口断开成功')
      // 刷新端口列表以更新可用端口
      await loadPorts()
    }
  } catch (error: any) {
    ElMessage.error(error.message || '断开串口失败')
  } finally {
    disconnectingAll.value = false
  }
}

const testConnection = async () => {
  try {
    // 简单的指令测试，使用当前选择的串口
    await communicationStore.sendATCommand('AT\r\n', connectionStore.selectedSerialId || undefined)
    ElMessage.success('连接测试成功')
  } catch (error) {
    ElMessage.warning('连接测试失败，请检查设备连接')
  }
}

const goToCommunication = () => {
  router.push('/communication')
}

const connectMultiplePorts = async () => {
  const portsToConnect = availableUnconnectedPorts.value.slice(0, 3) // 最多连接3个串口
  const portNames = portsToConnect.map(p => p.device).join(', ')
  
  try {
    await ElMessageBox.confirm(
      `将使用当前配置连接以下串口：\n${portNames}\n\n确定继续吗？`,
      '批量连接串口',
      {
        confirmButtonText: '确定连接',
        cancelButtonText: '取消',
        type: 'info',
      }
    )
  } catch {
    return // 用户取消
  }
  
  connectingMultiple.value = true
  try {
    let successCount = 0
    
    for (const port of portsToConnect) {
      try {
        const config = {
          port: port.device,
          baudrate: form.baudrate,
          bytesize: form.bytesize,
          parity: form.parity,
          stopbits: form.stopbits,
          timeout: form.timeout
        }
        
        const response = await connectionStore.connect(config)
        successCount++
        ElMessage.success(`串口 ${port.device} 连接成功 (ID: ${response.serial_id})`)
        
        // 短暂延迟避免连接过快
        await new Promise(resolve => setTimeout(resolve, 500))
      } catch (error: any) {
        ElMessage.error(`串口 ${port.device} 连接失败: ${error.message}`)
      }
    }
    
    if (successCount > 0) {
      ElMessage.success(`成功连接 ${successCount} 个串口`)
      // 刷新端口列表
      await loadPorts()
    }
  } catch (error: any) {
    ElMessage.error('批量连接串口失败')
  } finally {
    connectingMultiple.value = false
  }
}





// 生命周期
onMounted(() => {
  loadPorts()
  connectionStore.checkStatus()
})
</script>

<style scoped>
.page-container {
  max-width: 800px;
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

/* 多串口连接列表样式 */
.connected-serials {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.serial-card {
  border: 2px solid #e0e6ed;
  border-radius: 12px;
  padding: 16px;
  background: #f8f9fa;
  cursor: pointer;
  transition: all 0.3s ease;
}

.serial-card:hover {
  border-color: #409eff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
}

.serial-card.active {
  border-color: #409eff;
  background: #f0f8ff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.2);
}

.serial-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.serial-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.serial-id {
  font-weight: 600;
  color: #409eff;
  font-size: 16px;
}

.serial-port {
  color: #666;
  font-size: 14px;
  font-family: monospace;
}

.serial-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.serial-details {
  margin-top: 8px;
}

@media (max-width: 768px) {
  .serial-header {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .serial-actions {
    justify-content: space-between;
  }
}
</style>