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
                <!-- 串口配置不需要刷新按钮，连接时会自动选择设备 -->
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
                    <el-option label="无校验" value="none" />
                    <el-option label="偶校验" value="even" />
                    <el-option label="奇校验" value="odd" />
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
                  @click="() => connect().catch(console.error)"
                  :loading="connecting"
                  :disabled="!isWebSerialSupported"
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
                <el-badge :value="connectedCount" class="connection-badge" />
              </h3>
              <div class="header-actions">
                <el-button 
                  type="danger" 
                  size="small" 
                  @click="disconnectAll"
                  :loading="disconnectingAll"
                  :disabled="connectedCount === 0"
                >
                  <el-icon><Close /></el-icon>
                  断开所有 ({{ connectedCount }})
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
              <el-button type="primary" @click="() => router.push('/communication')" :disabled="!connectionStore.isConnected">
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
import { ref, reactive, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { 
  Setting, 
  Connection, 
  Close, 
  CircleCheck, 
  InfoFilled, 
  Monitor, 
  Operation, 
  Check 
} from '@element-plus/icons-vue'
import { useConnectionStore } from '@/stores/connection'
import { webSerialService } from '@/services/webSerial'


const router = useRouter()
const connectionStore = useConnectionStore()

// 浏览器兼容性检查
const isWebSerialSupported = ref(false)
const compatibilityMessage = ref('')

// 检查Web Serial API支持
const checkWebSerialSupport = () => {
  try {
    isWebSerialSupported.value = webSerialService.isSupported()
    if (!isWebSerialSupported.value) {
      compatibilityMessage.value = '当前浏览器不支持Web Serial API，请使用Chrome 89+、Edge 89+或Opera 76+'
    } else {
      compatibilityMessage.value = 'Web Serial API支持正常'
    }
  } catch (error) {
    isWebSerialSupported.value = false
    compatibilityMessage.value = 'Web Serial API检查失败'
    console.error('Web Serial API check failed:', error)
  }
}

// 表单引用
const formRef = ref<FormInstance>()

// 计算属性 - 已连接串口数量
const connectedCount = computed(() => connectionStore.connectedSerials.length)

// 状态
const connecting = ref(false)
const disconnectingAll = ref(false)
const disconnectingSerials = ref<Record<number, boolean>>({})


const form = reactive({
  baudrate: 9600,  
  bytesize: 8 as 7 | 8,
  parity: 'none' as 'none' | 'even' | 'odd',
  stopbits: 1 as 1 | 2,
  timeout: 0.5,  
})

// 表单验证规则
const rules: FormRules = {
  baudrate: [
    { required: true, message: '请选择波特率', trigger: 'change' }
  ],
}

// 方法


const connect = async () => {
  if (!formRef.value) {
    ElMessage.error('表单引用不存在')
    return
  }
  
  // 检查Web Serial API支持
  if (!isWebSerialSupported.value) {
    ElMessage.error('当前浏览器不支持Web Serial API，无法连接串口')
    return
  }
  
  try {
    // 执行表单验证
    let valid = false
    try {
      valid = await formRef.value.validate()
    } catch (validationError) {
      ElMessage.warning('表单验证失败，请检查输入')
      return
    }
    
    if (!valid) {
      ElMessage.warning('请检查表单输入')
      return
    }
    
    connecting.value = true
    try {
      // 设置一个临时的端口标识，实际连接时会弹出设备选择对话框
      const configWithPort = {
        ...form,
        port: 'user-selected' // 这个值不会真正使用，只是满足接口要求
      }
      
      const response = await connectionStore.connect(configWithPort)
      ElMessage.success(`串口连接成功！分配ID: ${response.serial_id}`)
      
      // 强制刷新状态
      await syncState()
      
    } catch (error: any) {
      console.error('Connection error:', error)
      ElMessage.error(error.message || '串口连接失败')
    } finally {
      connecting.value = false
    }
  } catch (error: any) {
    console.error('Unexpected error in connect:', error)
    ElMessage.error('连接过程中发生错误')
    connecting.value = false
  }
}

const disconnectSerial = async (serialId: number) => {
  disconnectingSerials.value[serialId] = true
  try {
    const success = await connectionStore.disconnect(serialId)
    if (success) {
      ElMessage.success(`串口 ${serialId} 断开成功`)
      // 不需要手动调用loadPorts，状态监听器会自动处理
    } else {
      ElMessage.error(`串口 ${serialId} 断开失败`)
    }
  } catch (error: any) {
    console.error('Disconnect serial error:', error)
    ElMessage.error(error.message || `串口 ${serialId} 断开失败`)
  } finally {
    disconnectingSerials.value[serialId] = false
  }
}

const disconnectAll = async () => {
  // 检查是否有连接的串口
  if (connectionStore.connectedSerials.length === 0) {
    ElMessage.info('当前没有已连接的串口')
    return
  }
  
  const connectedCount = connectionStore.connectedSerials.length
  disconnectingAll.value = true
  
  try {
    const success = await connectionStore.disconnect()
    if (success) {
      ElMessage.success(`成功断开所有串口 (共${connectedCount}个)`)
      // 不需要手动调用loadPorts，状态监听器会自动处理
    } else {
      ElMessage.error('断开所有串口失败')
    }
  } catch (error: any) {
    console.error('Disconnect all error:', error)
    ElMessage.error(error.message || '断开所有串口失败')
  } finally {
    disconnectingAll.value = false
  }
}






// 状态同步检查
const syncState = async () => {
  try {
    await connectionStore.checkStatus()
  } catch (error) {
    console.error('State sync failed:', error)
  }
}

// 生命周期
onMounted(async () => {
  // 首先检查Web Serial API支持
  checkWebSerialSupport()
  
  // 如果支持Web Serial API，则执行状态同步
  if (isWebSerialSupported.value) {
    // 确保按顺序执行，避免竞态条件
    await syncState()
  } else {
    // 如果不支持，显示提示信息
    ElMessage.warning(compatibilityMessage.value)
  }
})

// 监听连接状态变化，确保UI同步
watch(
  () => connectionStore.connectedSerials,
  (newSerials, oldSerials) => {
    console.log('Connection state changed:', {
      old: oldSerials?.length || 0,
      new: newSerials.length,
      oldSerials: oldSerials?.map(s => s.serial_id),
      newSerials: newSerials.map(s => s.serial_id)
    })
  },
  { deep: true, immediate: false }
)

// 组件卸载时清理
onUnmounted(() => {
  // 清理工作（如果需要）
})
</script>

<style scoped>
/* 页面整体样式 */
.serial-config-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding: 24px;
}

/* 连接信息提示样式 */
.connection-info {
  margin-bottom: 16px;
}

.connection-info .el-alert {
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
}

.connection-info .el-alert ul {
  margin: 8px 0;
  padding-left: 20px;
}

.connection-info .el-alert li {
  margin: 4px 0;
  font-weight: 500;
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

.connection-badge :deep(.el-badge__content) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: 2px solid #ffffff;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
  font-weight: 600;
  font-size: 12px;
  min-width: 20px;
  height: 20px;
  line-height: 16px;
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
  margin-bottom: 16px;
}

/* 已选择串口信息样式 */
.selected-port-info {
  margin-top: 16px;
}

.selected-port-info .el-alert {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(103, 194, 58, 0.15);
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