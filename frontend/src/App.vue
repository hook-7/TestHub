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
                <Connection />
              </el-icon>
              {{ connectionStore.isConnected ? '已连接' : '未连接' }}
            </el-tag>
          </div>
        </div>
      </el-header>

      <!-- Navigation -->
      <div class="navigation">
        <el-menu 
          :default-active="$route.path" 
          mode="horizontal" 
          router
          class="nav-menu"
        >
          <el-menu-item index="/serial-config">
            <el-icon><Setting /></el-icon>
            <span>串口配置</span>
          </el-menu-item>
          <el-menu-item index="/communication">
            <el-icon><ChatLineRound /></el-icon>
            <span>AT指令交互</span>
          </el-menu-item>
        </el-menu>
      </div>

      <!-- Main Content -->
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { 
  Connection, 
  Setting, 
  ChatLineRound
} from '@element-plus/icons-vue'
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

.navigation {
  background: white;
  border-bottom: 1px solid #e4e7ed;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.nav-menu {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  border-bottom: none;
}

.nav-menu .el-menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 500;
}

.nav-menu .el-menu-item:hover {
  background-color: #f5f7fa;
}

.nav-menu .el-menu-item.is-active {
  background-color: #ecf5ff;
  color: #409eff;
}

.main-content {
  background-color: #f5f7fa;
  padding: 0;
  overflow: auto;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header-content {
    padding: 0 12px;
  }
  
  .title {
    font-size: 20px;
  }
  
  .nav-menu {
    padding: 0 12px;
  }
  
  .nav-menu .el-menu-item {
    font-size: 14px;
  }
  
  .nav-menu .el-menu-item span {
    display: none;
  }
}
</style>