<template>
  <div class="api-test">
    <h2>API测试页面</h2>
    
    <el-card>
      <template #header>
        <span>工作流API测试</span>
      </template>
      
      <div class="test-section">
        <h3>1. 测试工作流列表</h3>
        <el-button @click="testWorkflowList" :loading="loading">测试工作流列表</el-button>
        <div v-if="workflowResult" class="result">
          <pre>{{ JSON.stringify(workflowResult, null, 2) }}</pre>
        </div>
      </div>
      
      <div class="test-section">
        <h3>2. 测试执行列表</h3>
        <el-button @click="testExecutionList" :loading="loading">测试执行列表</el-button>
        <div v-if="executionResult" class="result">
          <pre>{{ JSON.stringify(executionResult, null, 2) }}</pre>
        </div>
      </div>
      
      <div class="test-section">
        <h3>3. 测试创建工作流</h3>
        <el-button @click="testCreateWorkflow" :loading="loading">测试创建工作流</el-button>
        <div v-if="createResult" class="result">
          <pre>{{ JSON.stringify(createResult, null, 2) }}</pre>
        </div>
      </div>
      
      <div class="test-section">
        <h3>4. 原始API调用测试</h3>
        <el-button @click="testRawApi" :loading="loading">测试原始API</el-button>
        <div v-if="rawResult" class="result">
          <pre>{{ JSON.stringify(rawResult, null, 2) }}</pre>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { workflowApi } from '@/api/workflow'
import axios from 'axios'

const loading = ref(false)
const workflowResult = ref(null)
const executionResult = ref(null)
const createResult = ref(null)
const rawResult = ref(null)

const testWorkflowList = async () => {
  loading.value = true
  try {
    console.log('开始测试工作流列表...')
    const result = await workflowApi.listWorkflows()
    console.log('工作流列表结果:', result)
    workflowResult.value = result
  } catch (error) {
    console.error('工作流列表测试失败:', error)
    workflowResult.value = { error: error.message, details: error }
  } finally {
    loading.value = false
  }
}

const testExecutionList = async () => {
  loading.value = true
  try {
    console.log('开始测试执行列表...')
    const result = await workflowApi.listExecutions()
    console.log('执行列表结果:', result)
    executionResult.value = result
  } catch (error) {
    console.error('执行列表测试失败:', error)
    executionResult.value = { error: error.message, details: error }
  } finally {
    loading.value = false
  }
}

const testCreateWorkflow = async () => {
  loading.value = true
  try {
    console.log('开始测试创建工作流...')
    const testData = {
      name: '前端测试工作流',
      description: '用于测试的工作流',
      steps: []
    }
    const result = await workflowApi.createWorkflow(testData)
    console.log('创建工作流结果:', result)
    createResult.value = result
  } catch (error) {
    console.error('创建工作流测试失败:', error)
    createResult.value = { error: error.message, details: error }
  } finally {
    loading.value = false
  }
}

const testRawApi = async () => {
  loading.value = true
  try {
    console.log('开始测试原始API...')
    
    // 直接使用axios测试，绕过拦截器
    const response = await axios.get('/api/v1/workflow/', {
      timeout: 5000
    })
    
    console.log('原始API响应:', response.data)
    rawResult.value = {
      status: response.status,
      data: response.data,
      headers: response.headers
    }
  } catch (error) {
    console.error('原始API测试失败:', error)
    rawResult.value = { 
      error: error.message, 
      response: error.response?.data,
      status: error.response?.status 
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.api-test {
  padding: 20px;
}

.test-section {
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--el-border-color);
}

.test-section:last-child {
  border-bottom: none;
}

.result {
  margin-top: 15px;
  max-height: 300px;
  overflow-y: auto;
}

.result pre {
  background: var(--el-fill-color-light);
  padding: 15px;
  border-radius: 6px;
  font-size: 12px;
  line-height: 1.5;
}
</style>