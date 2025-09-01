<template>
  <div id="app">
    <el-container class="layout-container">
      <!-- Header -->
      <el-header class="header">
        <div class="header-content">
          <h1 class="title">
            <el-icon><Connection /></el-icon>
            Industrial HMI
          </h1>
          <div class="connection-status">
            <el-tag 
              :type="connectionStore.isConnected ? 'success' : 'danger'"
              size="large"
            >
              <el-icon>
                <component :is="connectionStore.isConnected ? 'CircleCheckFilled' : 'CircleCloseFilled'" />
              </el-icon>
              {{ connectionStore.isConnected ? '已连接' : '未连接' }}
            </el-tag>
          </div>
        </div>
      </el-header>

      <!-- Main Content -->
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useConnectionStore } from '@/stores/connection'

const connectionStore = useConnectionStore()

onMounted(() => {
  // 初始化时检查连接状态
  connectionStore.checkStatus()
})
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.main-content {
  background-color: #f5f7fa;
  padding: 20px;
}
</style>