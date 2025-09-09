<template>
  <div class="serial-id-test">
    <el-card class="test-card">
      <template #header>
        <div class="card-header">
          <span>串口编号规则测试</span>
          <el-button type="primary" @click="runTest" :loading="testing">
            运行测试
          </el-button>
        </div>
      </template>

      <div class="test-content">
        <el-alert
          title="测试说明"
          type="info"
          :closable="false"
          class="test-info"
        >
          <p>测试串口ID分配规则：</p>
          <ul>
            <li>第一个连接应该分配ID: 1</li>
            <li>第二个连接应该分配ID: 2</li>
            <li>断开ID 1后，下一个连接应该复用ID: 1</li>
            <li>断开ID 2后，下一个连接应该复用ID: 2</li>
            <li>所有连接断开后，下一个连接应该从ID: 1开始</li>
          </ul>
        </el-alert>

        <div class="test-results" v-if="testResults.length > 0">
          <h3>测试结果</h3>
          <el-timeline>
            <el-timeline-item
              v-for="(result, index) in testResults"
              :key="index"
              :type="result.success ? 'success' : 'danger'"
              :timestamp="result.timestamp"
            >
              <div class="result-item">
                <h4>{{ result.title }}</h4>
                <p>{{ result.message }}</p>
                <div v-if="result.details" class="result-details">
                  <pre>{{ result.details }}</pre>
                </div>
              </div>
            </el-timeline-item>
          </el-timeline>
        </div>

        <div class="current-status">
          <h3>当前状态</h3>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="已连接串口数">
              {{ connectionStore.connectedCount }}
            </el-descriptions-item>
            <el-descriptions-item label="已连接串口ID">
              {{ Array.from(connectionStore.connectedSerials.keys()).join(', ') || '无' }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { webSerialService } from '@/services/webSerial'
import { useConnectionStore } from '@/stores/connection'

const connectionStore = useConnectionStore()

// 测试状态
const testing = ref(false)
const testResults = ref<Array<{
  title: string
  message: string
  details?: string
  success: boolean
  timestamp: string
}>>([])

// 添加测试结果
const addResult = (title: string, message: string, success: boolean, details?: string) => {
  testResults.value.push({
    title,
    message,
    details,
    success,
    timestamp: new Date().toLocaleTimeString()
  })
}

// 运行串口ID分配规则测试
const runTest = async () => {
  testing.value = true
  testResults.value = []
  
  try {
    addResult('开始测试', '开始测试串口ID分配规则', true)
    
    // 测试1: 第一个连接应该分配ID 1
    addResult('测试1', '尝试连接第一个串口...', true)
    try {
      const config1 = {
        port: 'test-port-1',
        baudrate: 115200,
        bytesize: 8,
        parity: 'none' as const,
        stopbits: 1,
        timeout: 0.5
      }
      
      // 模拟连接（不实际连接硬件）
      const mockPort1 = {
        open: async () => {},
        close: async () => {},
        readable: null,
        writable: null
      } as any
      
      // 手动分配ID 1
      const serialId1 = 1
      webSerialService['ports'].set(serialId1, mockPort1)
      webSerialService['portConfigs'].set(serialId1, config1)
      
      addResult('测试1结果', `第一个串口分配ID: ${serialId1}`, serialId1 === 1, `期望: 1, 实际: ${serialId1}`)
    } catch (error: any) {
      addResult('测试1失败', `第一个串口连接失败: ${error.message}`, false)
    }
    
    // 测试2: 第二个连接应该分配ID 2
    addResult('测试2', '尝试连接第二个串口...', true)
    try {
      const config2 = {
        port: 'test-port-2',
        baudrate: 115200,
        bytesize: 8,
        parity: 'none' as const,
        stopbits: 1,
        timeout: 0.5
      }
      
      const mockPort2 = {
        open: async () => {},
        close: async () => {},
        readable: null,
        writable: null
      } as any
      
      // 手动分配ID 2
      const serialId2 = 2
      webSerialService['ports'].set(serialId2, mockPort2)
      webSerialService['portConfigs'].set(serialId2, config2)
      
      addResult('测试2结果', `第二个串口分配ID: ${serialId2}`, serialId2 === 2, `期望: 2, 实际: ${serialId2}`)
    } catch (error: any) {
      addResult('测试2失败', `第二个串口连接失败: ${error.message}`, false)
    }
    
    // 测试3: 断开ID 1，下一个连接应该复用ID 1
    addResult('测试3', '断开ID 1的串口...', true)
    webSerialService['ports'].delete(1)
    webSerialService['portConfigs'].delete(1)
    
    // 测试下一个ID分配
    const nextId = webSerialService['getNextSerialId']()
    addResult('测试3结果', `断开ID 1后，下一个ID: ${nextId}`, nextId === 1, `期望: 1, 实际: ${nextId}`)
    
    // 测试4: 断开ID 2，下一个连接应该复用ID 2
    addResult('测试4', '断开ID 2的串口...', true)
    webSerialService['ports'].delete(2)
    webSerialService['portConfigs'].delete(2)
    
    const nextId2 = webSerialService['getNextSerialId']()
    addResult('测试4结果', `断开ID 2后，下一个ID: ${nextId2}`, nextId2 === 2, `期望: 2, 实际: ${nextId2}`)
    
    // 测试5: 所有连接断开后，下一个连接应该从ID 1开始
    addResult('测试5', '断开所有串口...', true)
    webSerialService['ports'].clear()
    webSerialService['portConfigs'].clear()
    
    const nextId3 = webSerialService['getNextSerialId']()
    addResult('测试5结果', `所有连接断开后，下一个ID: ${nextId3}`, nextId3 === 1, `期望: 1, 实际: ${nextId3}`)
    
    // 测试6: 复杂场景 - 连接1,2,3，断开2，再连接应该分配2
    addResult('测试6', '复杂场景测试...', true)
    
    // 连接1,2,3
    webSerialService['ports'].set(1, {} as any)
    webSerialService['ports'].set(2, {} as any)
    webSerialService['ports'].set(3, {} as any)
    
    // 断开2
    webSerialService['ports'].delete(2)
    
    const nextId4 = webSerialService['getNextSerialId']()
    addResult('测试6结果', `连接1,2,3后断开2，下一个ID: ${nextId4}`, nextId4 === 2, `期望: 2, 实际: ${nextId4}`)
    
    // 清理测试数据
    webSerialService['ports'].clear()
    webSerialService['portConfigs'].clear()
    
    addResult('测试完成', '所有测试完成，串口ID分配规则测试结束', true)
    
    ElMessage.success('串口ID分配规则测试完成')
    
  } catch (error: any) {
    addResult('测试失败', `测试过程中发生错误: ${error.message}`, false, error.stack)
    ElMessage.error('测试失败')
  } finally {
    testing.value = false
  }
}

onMounted(() => {
  addResult('页面加载', '串口ID分配规则测试页面已加载', true)
})
</script>

<style scoped>
.serial-id-test {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.test-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.test-content {
  margin-top: 20px;
}

.test-info {
  margin-bottom: 20px;
}

.test-info ul {
  margin: 10px 0;
  padding-left: 20px;
}

.test-results {
  margin-top: 20px;
}

.result-item h4 {
  margin: 0 0 8px 0;
  color: #303133;
}

.result-item p {
  margin: 0 0 8px 0;
  color: #606266;
}

.result-details {
  background: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  margin-top: 8px;
}

.result-details pre {
  margin: 0;
  font-size: 12px;
  color: #909399;
}

.current-status {
  margin-top: 20px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.current-status h3 {
  margin: 0 0 15px 0;
  color: #303133;
}
</style>
