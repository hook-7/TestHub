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
      <!-- 左侧：操作面板 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>
                <el-icon><Operation /></el-icon>
                通信操作
              </h3>
            </div>
          </template>

          <el-tabs v-model="activeTab" type="border-card">
            <!-- 读取寄存器 -->
            <el-tab-pane label="读取寄存器" name="read">
              <el-form :model="readForm" label-width="100px">
                <el-form-item label="从站ID">
                  <el-input-number v-model="readForm.slave_id" :min="1" :max="247" />
                </el-form-item>
                <el-form-item label="起始地址">
                  <el-input-number v-model="readForm.start_addr" :min="0" :max="65535" />
                </el-form-item>
                <el-form-item label="数量">
                  <el-input-number v-model="readForm.count" :min="1" :max="125" />
                </el-form-item>
                <el-form-item label="功能码">
                  <el-select v-model="readForm.function_code">
                    <el-option label="03 - 保持寄存器" :value="3" />
                    <el-option label="04 - 输入寄存器" :value="4" />
                  </el-select>
                </el-form-item>
                <el-form-item>
                  <el-button 
                    type="primary" 
                    @click="readRegisters"
                    :disabled="!connectionStore.isConnected"
                    :loading="readLoading"
                  >
                    <el-icon><View /></el-icon>
                    读取
                  </el-button>
                </el-form-item>
              </el-form>
            </el-tab-pane>

            <!-- 写入寄存器 -->
            <el-tab-pane label="写入寄存器" name="write">
              <el-form :model="writeForm" label-width="100px">
                <el-form-item label="从站ID">
                  <el-input-number v-model="writeForm.slave_id" :min="1" :max="247" />
                </el-form-item>
                <el-form-item label="寄存器地址">
                  <el-input-number v-model="writeForm.addr" :min="0" :max="65535" />
                </el-form-item>
                <el-form-item label="寄存器值">
                  <el-input-number v-model="writeForm.value" :min="0" :max="65535" />
                </el-form-item>
                <el-form-item>
                  <el-button 
                    type="primary" 
                    @click="writeRegister"
                    :disabled="!connectionStore.isConnected"
                    :loading="writeLoading"
                  >
                    <el-icon><Edit /></el-icon>
                    写入
                  </el-button>
                </el-form-item>
              </el-form>
            </el-tab-pane>

            <!-- 批量写入 -->
            <el-tab-pane label="批量写入" name="batch-write">
              <el-form :model="batchWriteForm" label-width="100px">
                <el-form-item label="从站ID">
                  <el-input-number v-model="batchWriteForm.slave_id" :min="1" :max="247" />
                </el-form-item>
                <el-form-item label="起始地址">
                  <el-input-number v-model="batchWriteForm.start_addr" :min="0" :max="65535" />
                </el-form-item>
                <el-form-item label="寄存器值">
                  <el-input
                    v-model="batchWriteForm.valuesText"
                    type="textarea"
                    :rows="3"
                    placeholder="输入寄存器值，用逗号分隔，例如: 100,200,300"
                  />
                </el-form-item>
                <el-form-item>
                  <el-button 
                    type="primary" 
                    @click="writeBatchRegisters"
                    :disabled="!connectionStore.isConnected"
                    :loading="batchWriteLoading"
                  >
                    <el-icon><DocumentAdd /></el-icon>
                    批量写入
                  </el-button>
                </el-form-item>
              </el-form>
            </el-tab-pane>

            <!-- 原始数据 -->
            <el-tab-pane label="原始数据" name="raw">
              <el-form :model="rawForm" label-width="100px">
                <el-form-item label="十六进制数据">
                  <el-input
                    v-model="rawForm.data"
                    placeholder="输入十六进制数据，例如: 01 03 00 00 00 01 84 0A"
                    style="font-family: monospace;"
                  />
                </el-form-item>
                <el-form-item>
                  <el-button 
                    type="primary" 
                    @click="sendRawData"
                    :disabled="!connectionStore.isConnected"
                    :loading="rawLoading"
                  >
                    <el-icon><Position /></el-icon>
                    发送
                  </el-button>
                </el-form-item>
              </el-form>
            </el-tab-pane>
          </el-tabs>
        </el-card>

        <!-- 寄存器数据显示 -->
        <el-card style="margin-top: 20px;" v-if="registerData.length > 0">
          <template #header>
            <h3>
              <el-icon><DataBoard /></el-icon>
              寄存器数据
            </h3>
          </template>
          
          <el-table :data="registerData" size="small" border>
            <el-table-column prop="address" label="地址" width="100" />
            <el-table-column prop="value" label="值" width="100" />
            <el-table-column label="十六进制" width="120">
              <template #default="{ row }">
                <code>0x{{ row.value.toString(16).toUpperCase().padStart(4, '0') }}</code>
              </template>
            </el-table-column>
            <el-table-column label="二进制">
              <template #default="{ row }">
                <code>{{ row.value.toString(2).padStart(16, '0') }}</code>
              </template>
            </el-table-column>
          </el-table>
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
              <el-button @click="clearLogs" size="small">
                <el-icon><Delete /></el-icon>
                清空日志
              </el-button>
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
const activeTab = ref('read')
const readLoading = ref(false)
const writeLoading = ref(false)
const batchWriteLoading = ref(false)
const rawLoading = ref(false)
const registerData = ref<any[]>([])

// 表单数据
const readForm = reactive({
  slave_id: 1,
  start_addr: 0,
  count: 10,
  function_code: 3,
})

const writeForm = reactive({
  slave_id: 1,
  addr: 0,
  value: 0,
})

const batchWriteForm = reactive({
  slave_id: 1,
  start_addr: 0,
  valuesText: '',
})

const rawForm = reactive({
  data: '',
})

// 方法
const readRegisters = async () => {
  readLoading.value = true
  try {
    const result = await communicationStore.readRegisters(readForm)
    if (result) {
      registerData.value = result.registers
      ElMessage.success(`成功读取${result.registers.length}个寄存器`)
    }
  } catch (error) {
    console.error('Read registers error:', error)
  } finally {
    readLoading.value = false
  }
}

const writeRegister = async () => {
  writeLoading.value = true
  try {
    const result = await communicationStore.writeRegister(writeForm)
    if (result.success) {
      ElMessage.success('寄存器写入成功')
    } else {
      ElMessage.error(result.message)
    }
  } catch (error) {
    console.error('Write register error:', error)
  } finally {
    writeLoading.value = false
  }
}

const writeBatchRegisters = async () => {
  if (!batchWriteForm.valuesText.trim()) {
    ElMessage.error('请输入寄存器值')
    return
  }
  
  try {
    const values = batchWriteForm.valuesText
      .split(',')
      .map(v => parseInt(v.trim()))
      .filter(v => !isNaN(v) && v >= 0 && v <= 65535)
    
    if (values.length === 0) {
      ElMessage.error('请输入有效的寄存器值')
      return
    }
    
    batchWriteLoading.value = true
    
    const result = await communicationStore.writeRegisters({
      slave_id: batchWriteForm.slave_id,
      start_addr: batchWriteForm.start_addr,
      values,
    })
    
    if (result.success) {
      ElMessage.success(`成功写入${values.length}个寄存器`)
    } else {
      ElMessage.error(result.message)
    }
  } catch (error) {
    console.error('Batch write error:', error)
  } finally {
    batchWriteLoading.value = false
  }
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
.log-container {
  height: 500px;
  overflow-y: auto;
  padding: 10px;
  background-color: var(--el-bg-color-page);
  border-radius: 8px;
}

.empty-logs {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.el-input-number {
  width: 100%;
}

.el-select {
  width: 100%;
}
</style>