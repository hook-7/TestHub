<template>
  <div class="interface-config-page">

    <!-- 左右布局容器 -->
    <div class="main-layout">
      <!-- 左侧：接口配置 -->
      <div class="left-panel">
        <el-card class="config-card">
          <template #header>
            <div class="card-header">
              <h3>
                <el-icon><Setting /></el-icon>
                接口配置
              </h3>
              <div class="header-actions">
                <!-- 接口配置不需要刷新按钮，连接时会自动选择设备 -->
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

            <!-- 接口类型选择 -->
            <div class="form-section">
              <h4 class="section-title">
                <el-icon><Connection /></el-icon>
                接口类型
              </h4>
              <el-radio-group v-model="interfaceType" @change="onInterfaceTypeChange" class="interface-type-group">
                <el-radio-button value="serial">
                  <el-icon><Monitor /></el-icon>
                  串口连接
                </el-radio-button>
                <el-radio-button value="tcp">
                  <el-icon><Link /></el-icon>
                  TCP连接
                </el-radio-button>
              </el-radio-group>
            </div>

            <!-- 串口参数 -->
            <div v-if="interfaceType === 'serial'" class="form-section">
              <h4 class="section-title">
                <el-icon><Setting /></el-icon>
                串口参数
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

            <!-- TCP连接参数 -->
            <div v-if="interfaceType === 'tcp'" class="form-section">
              <h4 class="section-title">
                <el-icon><Link /></el-icon>
                TCP连接参数
              </h4>
              <div class="form-row">
                <el-form-item label="IP地址" prop="tcpHost">
                  <el-input
                    v-model="tcpForm.host"
                    placeholder="请输入IP地址，例如: 192.168.1.100"
                    style="font-family: monospace;"
                  />
                </el-form-item>
                
                <el-form-item label="端口号" prop="tcpPort">
                  <el-input-number
                    v-model="tcpForm.port"
                    :min="1"
                    :max="65535"
                    placeholder="请输入端口号"
                    style="width: 100%"
                  />
                </el-form-item>
              </div>

              <el-form-item label="连接超时(秒)" prop="tcpTimeout">
                <el-input-number 
                  v-model="tcpForm.timeout"
                  :min="1"
                  :max="30"
                  :step="1"
                  style="width: 100%"
                />
              </el-form-item>

              <el-form-item label="自动重连" prop="tcpAutoReconnect">
                <el-switch 
                  v-model="tcpForm.autoReconnect"
                  active-text="启用"
                  inactive-text="禁用"
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
                  v-if="interfaceType === 'serial'"
                  type="primary" 
                  @click="() => connectSerial().catch(console.error)"
                  :loading="connecting"
                  :disabled="!isWebSerialSupported"
                  size="large"
                  class="action-btn primary"
                >
                  <el-icon><Connection /></el-icon>
                  {{ connectionStore.isConnected ? '连接新串口' : '连接串口' }}
                </el-button>
                
                <el-button 
                  v-if="interfaceType === 'tcp'"
                  type="primary" 
                  @click="() => connectTcp().catch(console.error)"
                  :loading="tcpConnecting"
                  size="large"
                  class="action-btn primary"
                >
                  <el-icon><Link /></el-icon>
                  {{ tcpConnected ? '连接新TCP' : '连接TCP' }}
                </el-button>
              </div>
            </div>
          </el-form>
        </el-card>
      </div>

      <!-- 右侧：已连接接口列表 -->
      <div class="right-panel">
        <el-card class="connected-card">
          <template #header>
            <div class="card-header">
              <h3>
                <el-icon><InfoFilled /></el-icon>
                已连接接口
                <el-badge :value="totalConnectedCount" class="connection-badge" />
              </h3>
              <div class="header-actions">
                <el-button 
                  type="danger" 
                  size="small" 
                  @click="disconnectAll"
                  :loading="disconnectingAll"
                  :disabled="totalConnectedCount === 0"
                >
                  <el-icon><Close /></el-icon>
                  断开所有 ({{ totalConnectedCount }})
                </el-button>
              </div>
            </div>
          </template>
          
          <div class="connected-interfaces" v-if="totalConnectedCount > 0">
            <!-- 串口连接列表 -->
            <div 
              v-for="serial in connectionStore.connectedSerials" 
              :key="`serial-${serial.serial_id}`"
              class="interface-card serial-card"
              :class="{ active: connectionStore.selectedSerialId === serial.serial_id }"
              @click="selectSerial(serial.serial_id)"
            >
              <div class="interface-header">
                <div class="interface-info">
                  <div class="interface-id">
                    <el-icon><Monitor /></el-icon>
                    串口 #{{ serial.serial_id }}
                  </div>
                  <div class="interface-address">{{ serial.port }}</div>
                </div>
                <div class="interface-actions">
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
              
              <div class="interface-details">
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

            <!-- TCP连接列表 -->
            <div 
              v-for="tcp in connectedTcpConnections" 
              :key="`tcp-${tcp.id}`"
              class="interface-card tcp-card"
              :class="{ active: selectedTcpId === tcp.id }"
              @click="selectTcp(tcp.id)"
            >
              <div class="interface-header">
                <div class="interface-info">
                  <div class="interface-id">
                    <el-icon><Link /></el-icon>
                    TCP #{{ tcp.id }}
                  </div>
                  <div class="interface-address">{{ tcp.host }}:{{ tcp.port }}</div>
                </div>
                <div class="interface-actions">
                  <el-tag 
                    v-if="selectedTcpId === tcp.id" 
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
                    @click.stop="disconnectTcp(tcp.id)"
                    :loading="disconnectingTcp[tcp.id]"
                    class="disconnect-btn"
                  >
                    <el-icon><Close /></el-icon>
                    断开
                  </el-button>
                </div>
              </div>
              
              <div class="interface-details">
                <div class="detail-grid">
                  <div class="detail-item">
                    <span class="detail-label">IP地址</span>
                    <span class="detail-value">{{ tcp.host }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">端口</span>
                    <span class="detail-value">{{ tcp.port }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">超时</span>
                    <span class="detail-value">{{ tcp.timeout }}s</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">重连</span>
                    <span class="detail-value">{{ tcp.auto_reconnect ? '启用' : '禁用' }}</span>
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
            <el-empty description="暂无已连接接口">
              <el-button type="primary" @click="() => router.push('/communication')" :disabled="totalConnectedCount === 0">
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
  Check,
  Link
} from '@element-plus/icons-vue'
import { useConnectionStore } from '@/stores/connection'
import { webSerialService } from '@/services/webSerial'
import * as tcpAPI from '@/api/tcp'
import type { TcpConnection, TcpConnectionConfig } from '@/api/tcp'


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

// 接口类型
const interfaceType = ref<'serial' | 'tcp'>('serial')

// 计算属性 - 已连接串口数量
const connectedCount = computed(() => connectionStore.connectedSerials.length)

// TCP连接相关状态
const tcpConnected = ref(false)
const tcpConnecting = ref(false)
const selectedTcpId = ref<string | null>(null)
const disconnectingTcp = ref<Record<string, boolean>>({})
const connectedTcpConnections = ref<TcpConnection[]>([])

// 总连接数量
const totalConnectedCount = computed(() => connectedCount.value + connectedTcpConnections.value.length)

// 状态
const connecting = ref(false)
const disconnectingAll = ref(false)
const disconnectingSerials = ref<Record<number, boolean>>({})


const form = reactive({
  baudrate: 9600,  
  bytesize: 8,
  parity: 'none',
  stopbits: 1,
  timeout: 0.5,  
})

// TCP连接表单
const tcpForm = reactive({
  host: '192.168.1.100',
  port: 8080,
  timeout: 5,
  autoReconnect: true
})

// 表单验证规则
const rules: FormRules = {
  baudrate: [
    { required: true, message: '请选择波特率', trigger: 'change' }
  ],
  tcpHost: [
    { required: true, message: '请输入IP地址', trigger: 'blur' },
    { pattern: /^(\d{1,3}\.){3}\d{1,3}$/, message: '请输入有效的IP地址', trigger: 'blur' }
  ],
  tcpPort: [
    { required: true, message: '请输入端口号', trigger: 'blur' },
    { type: 'number', min: 1, max: 65535, message: '端口号范围为1-65535', trigger: 'blur' }
  ]
}

// 方法

// 接口类型切换
const onInterfaceTypeChange = (type: 'serial' | 'tcp') => {
  interfaceType.value = type
  console.log('接口类型切换为:', type)
}

// 串口连接方法
const connectSerial = async () => {
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
        port: 'user-selected', // 这个值不会真正使用，只是满足接口要求
        bytesize: form.bytesize as 7 | 8,
        parity: form.parity as 'none' | 'even' | 'odd',
        stopbits: form.stopbits as 1 | 2
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

// TCP连接方法
const connectTcp = async () => {
  if (!formRef.value) {
    ElMessage.error('表单引用不存在')
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
    
    tcpConnecting.value = true
    try {
      // 创建TCP连接配置
      const config: TcpConnectionConfig = {
        host: tcpForm.host,
        port: tcpForm.port,
        timeout: tcpForm.timeout,
        auto_reconnect: tcpForm.autoReconnect
      }
      
      // 调用后端API建立TCP连接
      const newTcpConnection = await tcpAPI.createTcpConnection(config)
      
      // 添加到本地连接列表
      connectedTcpConnections.value.push(newTcpConnection)
      tcpConnected.value = true
      selectedTcpId.value = newTcpConnection.id
      
      ElMessage.success(`TCP连接成功！连接到 ${tcpForm.host}:${tcpForm.port}`)
      
    } catch (error: any) {
      console.error('TCP connection error:', error)
      ElMessage.error(error.response?.data?.msg || error.message || 'TCP连接失败')
    } finally {
      tcpConnecting.value = false
    }
  } catch (error: any) {
    console.error('Unexpected error in TCP connect:', error)
    ElMessage.error('TCP连接过程中发生错误')
    tcpConnecting.value = false
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

// TCP断开连接
const disconnectTcp = async (tcpId: string) => {
  disconnectingTcp.value[tcpId] = true
  try {
    // 调用后端API断开TCP连接
    await tcpAPI.disconnectTcp(tcpId)
    
    // 从本地列表中移除
    const index = connectedTcpConnections.value.findIndex(tcp => tcp.id === tcpId)
    if (index !== -1) {
      connectedTcpConnections.value.splice(index, 1)
      if (selectedTcpId.value === tcpId) {
        selectedTcpId.value = null
      }
      ElMessage.success(`TCP连接 ${tcpId} 断开成功`)
    } else {
      ElMessage.error(`TCP连接 ${tcpId} 不存在`)
    }
  } catch (error: any) {
    console.error('Disconnect TCP error:', error)
    ElMessage.error(error.response?.data?.msg || error.message || `TCP连接 ${tcpId} 断开失败`)
  } finally {
    disconnectingTcp.value[tcpId] = false
  }
}

// 选择串口
const selectSerial = (serialId: number) => {
  connectionStore.selectSerial(serialId)
  selectedTcpId.value = null // 取消TCP选择
  ElMessage.info(`切换到串口 #${serialId}`)
}

// 选择TCP连接
const selectTcp = (tcpId: string) => {
  selectedTcpId.value = tcpId
  connectionStore.selectedSerialId = null // 取消串口选择
  ElMessage.info(`切换到TCP连接 #${tcpId}`)
}

const disconnectAll = async () => {
  // 检查是否有连接的接口
  if (totalConnectedCount.value === 0) {
    ElMessage.info('当前没有已连接的接口')
    return
  }
  
  const totalCount = totalConnectedCount.value
  disconnectingAll.value = true
  
  try {
    // 断开所有串口
    if (connectionStore.connectedSerials.length > 0) {
      const success = await connectionStore.disconnect()
      if (!success) {
        ElMessage.error('断开串口失败')
      }
    }
    
    // 断开所有TCP连接
    if (connectedTcpConnections.value.length > 0) {
      try {
        await tcpAPI.disconnectAllTcp()
        connectedTcpConnections.value = []
        selectedTcpId.value = null
        tcpConnected.value = false
      } catch (error: any) {
        console.error('Disconnect all TCP error:', error)
        ElMessage.warning('部分TCP连接断开失败')
      }
    }
    
    ElMessage.success(`成功断开所有接口 (共${totalCount}个)`)
  } catch (error: any) {
    console.error('Disconnect all error:', error)
    ElMessage.error(error.message || '断开所有接口失败')
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

// 同步TCP连接状态
const syncTcpState = async () => {
  try {
    const response = await tcpAPI.getTcpConnections()
    connectedTcpConnections.value = response.connections
    tcpConnected.value = response.connections.length > 0
  } catch (error) {
    console.error('TCP state sync failed:', error)
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
  
  // 同步TCP连接状态
  await syncTcpState()
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
.interface-config-page {
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

/* 接口类型选择器样式 */
.interface-type-group {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.interface-type-group :deep(.el-radio-button__inner) {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.interface-type-group :deep(.el-radio-button__inner:hover) {
  background: linear-gradient(135deg, #f0f8ff 0%, #e6f3ff 100%);
  border-color: #409eff;
}

.interface-type-group :deep(.el-radio-button.is-active .el-radio-button__inner) {
  background: linear-gradient(135deg, #409eff 0%, #1976d2 100%);
  border-color: #409eff;
  color: white;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

/* 已连接接口列表样式 */
.connected-interfaces {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px;
  max-height: 600px;
  overflow-y: auto;
}

.connected-interfaces::-webkit-scrollbar {
  width: 4px;
}

.connected-interfaces::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 2px;
}

.connected-interfaces::-webkit-scrollbar-thumb {
  background: #bdbdbd;
  border-radius: 2px;
}

.connected-interfaces::-webkit-scrollbar-thumb:hover {
  background: #9e9e9e;
}

/* 接口卡片通用样式 */
.interface-card {
  border: 2px solid var(--el-border-color-light);
  border-radius: 12px;
  padding: 16px;
  background: white;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.interface-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  transform: scaleX(0);
  transition: transform 0.3s ease;
}

.interface-card:hover {
  border-color: var(--el-color-primary);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.15);
  transform: translateY(-2px);
}

.interface-card:hover::before {
  transform: scaleX(1);
}

.interface-card.active {
  border-color: var(--el-color-primary);
  background: linear-gradient(135deg, #f0f8ff 0%, #e6f3ff 100%);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.2);
}

.interface-card.active::before {
  transform: scaleX(1);
}

/* 串口卡片特殊样式 */
.serial-card::before {
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
}

/* TCP卡片特殊样式 */
.tcp-card::before {
  background: linear-gradient(90deg, #4ecdc4 0%, #44a08d 100%);
}

/* 接口头部样式 */
.interface-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.interface-info {
  flex: 1;
}

.interface-id {
  font-weight: 600;
  color: var(--el-color-primary);
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.interface-address {
  color: var(--el-text-color-secondary);
  font-size: 14px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  background: var(--el-fill-color-light);
  padding: 4px 8px;
  border-radius: 4px;
  display: inline-block;
}

.interface-actions {
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

/* 接口详情样式 */
.interface-details {
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
  
  .interface-header {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .interface-actions {
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