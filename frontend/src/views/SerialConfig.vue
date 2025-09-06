<template>
  <div class="serial-config-page">

    <!-- 左右布局容器 -->
    <div class="main-layout">
      <!-- 左侧：串口配置 -->
      <div class="left-panel">
        <el-card class="config-card">
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
            class="config-form"
          >
            <!-- 串口选择 -->
            <div class="form-section">
              <h4 class="section-title">
                <el-icon><Connection /></el-icon>
                串口选择
              </h4>
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
            </div>

            <!-- 串口参数 -->
            <div class="form-section">
              <h4 class="section-title">
                <el-icon><Setting /></el-icon>
                通信参数
              </h4>
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
            </div>

            <!-- 操作按钮 -->
            <div class="form-section">
              <h4 class="section-title">
                <el-icon><Operation /></el-icon>
                操作控制
              </h4>
              <div class="action-buttons">
                <el-button 
                  type="primary" 
                  @click="connect"
                  :loading="connecting"
                  size="large"
                  class="action-btn primary"
                >
                  <el-icon><Connection /></el-icon>
                  {{ connectionStore.isConnected ? '连接新串口' : '连接串口' }}
                </el-button>
              </div>
            </div>
          </el-form>
        </el-card>
      </div>

      <!-- 右侧：已连接串口列表 -->
      <div class="right-panel">
        <el-card class="connected-card">
          <template #header>
            <div class="card-header">
              <h3>
                <el-icon><InfoFilled /></el-icon>
                已连接串口
                <el-badge :value="connectionStore.connectedSerials.length" class="connection-badge" />
              </h3>
              <div class="header-actions">
                <el-button 
                  type="success" 
                  size="small" 
                  @click="loadPorts"
                  :loading="loading"
                >
                  <el-icon><Refresh /></el-icon>
                  刷新
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
          
          <div class="connected-serials" v-if="connectionStore.isConnected">
            <div 
              v-for="serial in connectionStore.connectedSerials" 
              :key="serial.serial_id"
              class="serial-card"
              :class="{ active: connectionStore.selectedSerialId === serial.serial_id }"
              @click="connectionStore.selectSerial(serial.serial_id)"
            >
              <div class="serial-header">
                <div class="serial-info">
                  <div class="serial-id">
                    <el-icon><Monitor /></el-icon>
                    串口 #{{ serial.serial_id }}
                  </div>
                  <div class="serial-port">{{ serial.port }}</div>
                </div>
                <div class="serial-actions">
                  <el-tag 
                    v-if="connectionStore.selectedSerialId === serial.serial_id" 
                    type="success" 
                    size="small"
                    class="selected-tag"
                  >
                    <el-icon><Check /></el-icon>
                    当前选择
                  </el-tag>
                  <el-button 
                    type="danger" 
                    size="small" 
                    @click.stop="disconnectSerial(serial.serial_id)"
                    :loading="disconnectingSerials[serial.serial_id]"
                    class="disconnect-btn"
                  >
                    <el-icon><Close /></el-icon>
                    断开
                  </el-button>
                </div>
              </div>
              
              <div class="serial-details">
                <div class="detail-grid">
                  <div class="detail-item">
                    <span class="detail-label">波特率</span>
                    <span class="detail-value">{{ serial.baudrate }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">数据位</span>
                    <span class="detail-value">{{ serial.bytesize }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">校验位</span>
                    <span class="detail-value">{{ serial.parity }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">停止位</span>
                    <span class="detail-value">{{ serial.stopbits }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">超时</span>
                    <span class="detail-value">{{ serial.timeout }}s</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">状态</span>
                    <el-tag type="success" size="small" class="status-tag">
                      <el-icon><CircleCheck /></el-icon>
                      已连接
                    </el-tag>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 无连接状态提示 -->
          <div v-else class="no-connection-hint">
            <el-empty description="暂无已连接串口">
              <el-button type="primary" @click="goToCommunication" :disabled="!connectionStore.isConnected">
                前往通信页面
              </el-button>
            </el-empty>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { 
  Setting, 
  Refresh, 
  Search, 
  Connection, 
  Close, 
  CircleCheck, 
  Message, 
  InfoFilled, 
  Monitor, 
  Operation, 
  Check 
} from '@element-plus/icons-vue'
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
/* 页面整体样式 */
.serial-config-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding: 24px;
}

/* 页面标题 */
.page-header {
  text-align: center;
  margin-bottom: 32px;
  color: #2c3e50;
}

.page-title {
  font-size: 32px;
  font-weight: 700;
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.page-subtitle {
  font-size: 16px;
  color: #7f8c8d;
  margin: 0;
}

/* 主布局容器 */
.main-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

/* 左侧面板 */
.left-panel {
  display: flex;
  flex-direction: column;
}

/* 右侧面板 */
.right-panel {
  display: flex;
  flex-direction: column;
}

/* 卡片样式 */
.config-card,
.connected-card {
  border-radius: 16px;
  border: none;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  background: white;
  height: fit-content;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-bottom: 1px solid var(--el-border-color-light);
}

.card-header h3 {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--el-text-color-primary);
}

.connection-badge {
  margin-left: 8px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

/* 表单样式 */
.config-form {
  padding: 24px;
}

.form-section {
  margin-bottom: 24px;
  padding: 20px;
  background: #fafbfc;
  border-radius: 12px;
  border: 1px solid var(--el-border-color-lighter);
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 16px 0;
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--el-text-color-primary);
  padding-bottom: 8px;
  border-bottom: 2px solid var(--el-color-primary-light-8);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.form-row:last-child {
  margin-bottom: 0;
}

/* 操作按钮样式 */
.action-buttons {
  display: flex;
  justify-content: center;
  gap: 12px;
}

.action-btn {
  border-radius: 8px;
  font-weight: 500;
  padding: 12px 16px;
  transition: all 0.3s ease;
}

.action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

.action-btn.primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
}

.action-btn.danger {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
  border: none;
  color: white;
}

.action-btn.test {
  background: linear-gradient(135deg, #4ecdc4 0%, #44a08d 100%);
  border: none;
  color: white;
}

.action-btn.success {
  background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%);
  border: none;
  color: white;
}

.action-btn.info {
  background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
  border: none;
  color: white;
}

/* 已连接串口列表样式 */
.connected-serials {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px;
  max-height: 600px;
  overflow-y: auto;
}

.connected-serials::-webkit-scrollbar {
  width: 4px;
}

.connected-serials::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 2px;
}

.connected-serials::-webkit-scrollbar-thumb {
  background: #bdbdbd;
  border-radius: 2px;
}

.connected-serials::-webkit-scrollbar-thumb:hover {
  background: #9e9e9e;
}

.serial-card {
  border: 2px solid var(--el-border-color-light);
  border-radius: 12px;
  padding: 16px;
  background: white;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.serial-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  transform: scaleX(0);
  transition: transform 0.3s ease;
}

.serial-card:hover {
  border-color: var(--el-color-primary);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.15);
  transform: translateY(-2px);
}

.serial-card:hover::before {
  transform: scaleX(1);
}

.serial-card.active {
  border-color: var(--el-color-primary);
  background: linear-gradient(135deg, #f0f8ff 0%, #e6f3ff 100%);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.2);
}

.serial-card.active::before {
  transform: scaleX(1);
}

.serial-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.serial-info {
  flex: 1;
}

.serial-id {
  font-weight: 600;
  color: var(--el-color-primary);
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.serial-port {
  color: var(--el-text-color-secondary);
  font-size: 14px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  background: var(--el-fill-color-light);
  padding: 4px 8px;
  border-radius: 4px;
  display: inline-block;
}

.serial-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.selected-tag {
  display: flex;
  align-items: center;
  gap: 4px;
  font-weight: 500;
}

.disconnect-btn {
  border-radius: 6px;
  font-weight: 500;
}

/* 串口详情样式 */
.serial-details {
  margin-top: 12px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 10px;
  background: var(--el-fill-color-lighter);
  border-radius: 6px;
  border: 1px solid var(--el-border-color-lighter);
}

.detail-label {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.detail-value {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.status-tag {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 无连接状态提示 */
.no-connection-hint {
  padding: 40px 20px;
  text-align: center;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .main-layout {
    grid-template-columns: 1fr;
    gap: 20px;
  }
  
  .action-buttons {
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  }
}

@media (max-width: 768px) {
  .serial-config-page {
    padding: 16px;
  }
  
  .page-title {
    font-size: 24px;
  }
  
  .form-row {
    grid-template-columns: 1fr;
  }
  
  .action-buttons {
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
  
  .serial-header {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .serial-actions {
    justify-content: space-between;
  }
  
  .detail-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .config-form {
    padding: 16px;
  }
  
  .form-section {
    padding: 16px;
  }
  
  .serial-card {
    padding: 12px;
  }
}
</style>