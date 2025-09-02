<template>
  <div class="page-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>串口登录配置</h2>
      <p class="page-description">管理串口登录配置，支持自动连接和登录验证</p>
    </div>

    <!-- 操作工具栏 -->
    <el-card class="toolbar-card">
      <el-row :gutter="16" justify="space-between">
        <el-col :span="12">
          <el-button type="primary" @click="showCreateDialog" :icon="Plus">
            新建配置
          </el-button>
          <el-button 
            type="success" 
            @click="connectWithActive"
            :loading="connecting"
            :disabled="!activeConfig"
            :icon="Connection"
          >
            使用激活配置连接
          </el-button>
        </el-col>
        <el-col :span="12" style="text-align: right;">
          <el-button @click="refreshConfigs" :icon="Refresh" :loading="loading">
            刷新
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 配置列表 -->
    <el-card class="config-list-card">
      <template #header>
        <div class="card-header">
          <h4>配置列表</h4>
          <el-tag v-if="activeConfig" type="success" size="small">
            激活配置: {{ activeConfig.name }}
          </el-tag>
        </div>
      </template>

      <el-table 
        :data="configs" 
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="name" label="配置名称" min-width="120">
          <template #default="{ row }">
            <div class="config-name">
              <span>{{ row.name }}</span>
              <el-tag v-if="row.is_active" type="success" size="small" style="margin-left: 8px;">
                激活中
              </el-tag>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="port" label="串口" min-width="100" />
        
        <el-table-column label="串口参数" min-width="150">
          <template #default="{ row }">
            {{ row.baudrate }}/{{ row.bytesize }}{{ row.parity }}{{ row.stopbits }}
          </template>
        </el-table-column>
        
        <el-table-column prop="auto_connect" label="自动连接" width="80">
          <template #default="{ row }">
            <el-tag :type="row.auto_connect ? 'success' : 'info'" size="small">
              {{ row.auto_connect ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="登录命令" min-width="120">
          <template #default="{ row }">
            <span v-if="row.login_command" class="login-command">
              {{ row.login_command }}
            </span>
            <el-tag v-else type="info" size="small">无</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="updated_at" label="更新时间" width="160">
          <template #default="{ row }">
            {{ formatTime(row.updated_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button 
              size="small" 
              @click="testConfig(row)"
              :loading="testingConfigId === row.id"
              :icon="VideoPlay"
            >
              测试
            </el-button>
            <el-button 
              size="small" 
              type="primary"
              @click="editConfig(row)"
              :icon="Edit"
            >
              编辑
            </el-button>
            <el-dropdown @command="handleDropdownCommand" trigger="click">
              <el-button size="small" :icon="More" />
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item 
                    :command="{action: 'activate', config: row}"
                    :disabled="row.is_active"
                  >
                    激活配置
                  </el-dropdown-item>
                  <el-dropdown-item 
                    :command="{action: 'delete', config: row}"
                    divided
                  >
                    删除配置
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑配置对话框 -->
    <el-dialog
      :title="dialogTitle"
      v-model="showDialog"
      width="600px"
      @close="resetForm"
    >
      <el-form
        ref="configFormRef"
        :model="configForm"
        :rules="formRules"
        label-width="120px"
      >
        <el-form-item label="配置名称" prop="name">
          <el-input v-model="configForm.name" placeholder="请输入配置名称" />
        </el-form-item>
        
        <el-form-item label="串口设备" prop="port">
          <el-select
            v-model="configForm.port"
            placeholder="请选择串口"
            style="width: 100%"
            @focus="loadAvailablePorts"
          >
            <el-option
              v-for="port in availablePorts"
              :key="port.device"
              :label="`${port.device} - ${port.description}`"
              :value="port.device"
            />
          </el-select>
        </el-form-item>
        
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="波特率" prop="baudrate">
              <el-select v-model="configForm.baudrate" style="width: 100%">
                <el-option v-for="rate in baudrateOptions" :key="rate" :label="rate" :value="rate" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="数据位" prop="bytesize">
              <el-select v-model="configForm.bytesize" style="width: 100%">
                <el-option v-for="size in bytesizeOptions" :key="size" :label="size" :value="size" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="校验位" prop="parity">
              <el-select v-model="configForm.parity" style="width: 100%">
                <el-option label="无校验 (N)" value="N" />
                <el-option label="偶校验 (E)" value="E" />
                <el-option label="奇校验 (O)" value="O" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="停止位" prop="stopbits">
              <el-select v-model="configForm.stopbits" style="width: 100%">
                <el-option v-for="bits in stopbitsOptions" :key="bits" :label="bits" :value="bits" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="超时时间(秒)" prop="timeout">
          <el-input-number
            v-model="configForm.timeout"
            :min="0.1"
            :max="60"
            :step="0.1"
            :precision="1"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="自动连接">
          <el-switch v-model="configForm.auto_connect" />
        </el-form-item>
        
        <el-divider content-position="left">登录验证设置</el-divider>
        
        <el-form-item label="登录命令">
          <el-input
            v-model="configForm.login_command"
            placeholder="可选：发送的登录命令，如 AT 或其他指令"
            type="textarea"
            :rows="2"
          />
        </el-form-item>
        
        <el-form-item label="期望响应">
          <el-input
            v-model="configForm.expected_response"
            placeholder="可选：期望的响应内容，用于验证登录是否成功"
            type="textarea"
            :rows="2"
          />
        </el-form-item>
        
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="重试次数" prop="retry_count">
              <el-input-number
                v-model="configForm.retry_count"
                :min="1"
                :max="10"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="重试延迟(秒)" prop="retry_delay">
              <el-input-number
                v-model="configForm.retry_delay"
                :min="0.1"
                :max="10"
                :step="0.1"
                :precision="1"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showDialog = false">取消</el-button>
          <el-button type="primary" @click="testCurrentConfig" :loading="testingCurrent">
            测试配置
          </el-button>
          <el-button type="primary" @click="saveConfig" :loading="saving">
            保存
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 测试结果对话框 -->
    <el-dialog
      title="测试结果"
      v-model="showTestResult"
      width="500px"
    >
      <div class="test-result">
        <div class="result-header">
                      <el-icon :size="24" :color="testResult?.success ? '#67C23A' : '#F56C6C'">
              <SuccessFilled v-if="testResult?.success" />
              <CircleCloseFilled v-else />
            </el-icon>
          <span class="result-message">{{ testResult?.message }}</span>
        </div>
        
        <el-descriptions :column="1" border>
          <el-descriptions-item label="连接耗时">
            {{ testResult?.connection_time?.toFixed(2) }}秒
          </el-descriptions-item>
          <el-descriptions-item label="登录耗时" v-if="testResult?.login_time">
            {{ testResult?.login_time?.toFixed(2) }}秒
          </el-descriptions-item>
          <el-descriptions-item label="设备响应" v-if="testResult?.response_data">
            <el-input
              :model-value="testResult?.response_data"
              type="textarea"
              :rows="3"
              readonly
            />
          </el-descriptions-item>
          <el-descriptions-item label="错误详情" v-if="testResult?.error_details">
            <el-input
              :model-value="testResult?.error_details"
              type="textarea"
              :rows="3"
              readonly
            />
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Plus, 
  Edit, 
  More, 
  Refresh, 
  VideoPlay, 
  Connection,
  SuccessFilled,
  CircleCloseFilled
} from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import * as serialLoginApi from '@/api/serialLogin'
import { serialAPI } from '@/api/serial'

// 响应式数据
const configs = ref<serialLoginApi.SerialLoginConfig[]>([])
const activeConfig = ref<serialLoginApi.SerialLoginConfig | null>(null)
const availablePorts = ref<any[]>([])
const loading = ref(false)
const connecting = ref(false)
const saving = ref(false)
const testingCurrent = ref(false)
const testingConfigId = ref<number | null>(null)

// 对话框相关
const showDialog = ref(false)
const editingConfig = ref<serialLoginApi.SerialLoginConfig | null>(null)
const configFormRef = ref<FormInstance>()

// 测试结果对话框
const showTestResult = ref(false)
const testResult = ref<serialLoginApi.SerialLoginTestResponse | null>(null)

// 表单数据
const configForm = reactive({
  name: '',
  port: '',
  baudrate: 9600 as number,
  bytesize: 8 as number,
  parity: 'N' as string,
  stopbits: 1 as number,
  timeout: 1.0 as number,
  auto_connect: false as boolean,
  login_command: '',
  expected_response: '',
  retry_count: 3 as number,
  retry_delay: 1.0 as number
})

// 选项数据
const baudrateOptions = [9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]
const bytesizeOptions = [5, 6, 7, 8]
const stopbitsOptions = [1, 1.5, 2]

// 表单验证规则
const formRules: FormRules = {
  name: [
    { required: true, message: '请输入配置名称', trigger: 'blur' },
    { min: 1, max: 50, message: '配置名称长度应在 1 到 50 个字符', trigger: 'blur' }
  ],
  port: [
    { required: true, message: '请选择串口设备', trigger: 'change' }
  ],
  baudrate: [
    { required: true, message: '请选择波特率', trigger: 'change' }
  ],
  bytesize: [
    { required: true, message: '请选择数据位', trigger: 'change' }
  ],
  parity: [
    { required: true, message: '请选择校验位', trigger: 'change' }
  ],
  stopbits: [
    { required: true, message: '请选择停止位', trigger: 'change' }
  ],
  timeout: [
    { required: true, message: '请输入超时时间', trigger: 'blur' }
  ],
  retry_count: [
    { required: true, message: '请输入重试次数', trigger: 'blur' }
  ],
  retry_delay: [
    { required: true, message: '请输入重试延迟', trigger: 'blur' }
  ]
}

// 计算属性
const dialogTitle = computed(() => editingConfig.value ? '编辑配置' : '新建配置')

// 方法
const refreshConfigs = async () => {
  loading.value = true
  try {
    const response = await serialLoginApi.getSerialLoginConfigs()
    configs.value = response.data
    
    // 更新激活配置
    activeConfig.value = configs.value.find(config => config.is_active) || null
  } catch (error) {
    console.error('获取配置列表失败:', error)
  } finally {
    loading.value = false
  }
}

const loadAvailablePorts = async () => {
  try {
    const response = await serialAPI.getAvailablePorts()
    availablePorts.value = response
  } catch (error) {
    console.error('获取可用串口失败:', error)
  }
}

const showCreateDialog = () => {
  editingConfig.value = null
  resetForm()
  showDialog.value = true
  loadAvailablePorts()
}

const editConfig = (config: serialLoginApi.SerialLoginConfig) => {
  editingConfig.value = config
  Object.assign(configForm, {
    name: config.name,
    port: config.port,
    baudrate: config.baudrate,
    bytesize: config.bytesize,
    parity: config.parity,
    stopbits: config.stopbits,
    timeout: config.timeout,
    auto_connect: config.auto_connect,
    login_command: config.login_command || '',
    expected_response: config.expected_response || '',
    retry_count: config.retry_count,
    retry_delay: config.retry_delay
  })
  showDialog.value = true
  loadAvailablePorts()
}

const resetForm = () => {
  Object.assign(configForm, {
    name: '',
    port: '',
    baudrate: 9600,
    bytesize: 8,
    parity: 'N',
    stopbits: 1,
    timeout: 1.0,
    auto_connect: false,
    login_command: '',
    expected_response: '',
    retry_count: 3,
    retry_delay: 1.0
  })
  configFormRef.value?.resetFields()
}

const saveConfig = async () => {
  if (!configFormRef.value) return
  
  await configFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    saving.value = true
    try {
      if (editingConfig.value) {
        // 更新配置
        await serialLoginApi.updateSerialLoginConfig(editingConfig.value.id!, configForm)
        ElMessage.success('配置更新成功')
      } else {
        // 创建配置
        await serialLoginApi.createSerialLoginConfig(configForm)
        ElMessage.success('配置创建成功')
      }
      
      showDialog.value = false
      await refreshConfigs()
    } catch (error) {
      console.error('保存配置失败:', error)
    } finally {
      saving.value = false
    }
  })
}

const testConfig = async (config: serialLoginApi.SerialLoginConfig) => {
  testingConfigId.value = config.id!
  try {
    const response = await serialLoginApi.testSerialLoginConfig({
      config_id: config.id
    })
    
    testResult.value = response.data
    showTestResult.value = true
  } catch (error) {
    console.error('测试配置失败:', error)
  } finally {
    testingConfigId.value = null
  }
}

const testCurrentConfig = async () => {
  if (!configFormRef.value) return
  
  await configFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    testingCurrent.value = true
    try {
      const response = await serialLoginApi.testSerialLoginConfig({
        temp_config: {
          name: configForm.name,
          port: configForm.port,
          baudrate: configForm.baudrate,
          bytesize: configForm.bytesize,
          parity: configForm.parity,
          stopbits: configForm.stopbits,
          timeout: configForm.timeout,
          auto_connect: configForm.auto_connect,
          login_command: configForm.login_command || undefined,
          expected_response: configForm.expected_response || undefined,
          retry_count: configForm.retry_count,
          retry_delay: configForm.retry_delay
        }
      })
      
      testResult.value = response.data
      showTestResult.value = true
    } catch (error) {
      console.error('测试配置失败:', error)
    } finally {
      testingCurrent.value = false
    }
  })
}

const handleDropdownCommand = async (command: {action: string, config: serialLoginApi.SerialLoginConfig}) => {
  const { action, config } = command
  
  if (action === 'activate') {
    try {
      await serialLoginApi.activateSerialLoginConfig(config.id!)
      ElMessage.success('配置激活成功')
      await refreshConfigs()
    } catch (error) {
      console.error('激活配置失败:', error)
    }
  } else if (action === 'delete') {
    try {
      await ElMessageBox.confirm(
        `确定要删除配置 "${config.name}" 吗？此操作不可撤销。`,
        '确认删除',
        {
          confirmButtonText: '删除',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )
      
      await serialLoginApi.deleteSerialLoginConfig(config.id!)
      ElMessage.success('配置删除成功')
      await refreshConfigs()
    } catch (error) {
      if (error !== 'cancel') {
        console.error('删除配置失败:', error)
      }
    }
  }
}

const connectWithActive = async () => {
  if (!activeConfig.value) {
    ElMessage.warning('没有激活的配置')
    return
  }
  
  connecting.value = true
  try {
    await serialLoginApi.connectWithActiveConfig()
    ElMessage.success('连接成功')
  } catch (error) {
    console.error('连接失败:', error)
  } finally {
    connecting.value = false
  }
}

const formatTime = (timeStr: string) => {
  return new Date(timeStr).toLocaleString('zh-CN')
}

// 生命周期
onMounted(() => {
  refreshConfigs()
})
</script>

<style scoped>
.page-container {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0 0 8px 0;
  color: #303133;
}

.page-description {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.toolbar-card {
  margin-bottom: 20px;
}

.config-list-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h4 {
  margin: 0;
  color: #303133;
}

.config-name {
  display: flex;
  align-items: center;
}

.login-command {
  font-family: 'Courier New', monospace;
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 12px;
}

.dialog-footer {
  text-align: right;
}

.test-result {
  padding: 20px 0;
}

.result-header {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.result-message {
  margin-left: 12px;
  font-size: 16px;
  font-weight: 500;
}
</style>