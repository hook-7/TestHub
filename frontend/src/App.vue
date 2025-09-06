<template>
  <div id="app">
    <el-container class="layout-container">
      <!-- Header -->
      <el-header class="header">
        <div class="header-content">
          <div class="header-left">
            <div class="logo-section">
              <div class="logo-icon">
                <el-icon><Connection /></el-icon>
              </div>
              <div class="logo-text">
                <h1 class="app-title">Industrial HMI</h1>
                <p class="app-subtitle">工业串口通信管理系统</p>
              </div>
            </div>
          </div>
          
          <div class="header-right">
            <!-- 连接状态 -->
            <div class="status-section">
              <div class="status-item">
                <span class="status-label">连接状态</span>
                <el-tag 
                  :type="connectionStore.isConnected ? 'success' : 'danger'"
                  size="default"
                  class="status-tag"
                >
                  <el-icon>
                    <component :is="connectionStore.isConnected ? 'CircleCheckFilled' : 'CircleCloseFilled'" />
                  </el-icon>
                  {{ connectionStore.isConnected ? '已连接' : '未连接' }}
                </el-tag>
              </div>
            </div>
          </div>
        </div>
      </el-header>

      <!-- Content Container -->
      <el-container class="content-container">
        <!-- Sidebar -->
        <el-aside class="sidebar" width="200px">
          <el-menu 
            :default-active="$route.path" 
            mode="vertical" 
            router
            class="sidebar-menu"
          >
            <el-menu-item index="/serial-config">
              <el-icon><Setting /></el-icon>
              <span>串口配置</span>
            </el-menu-item>
            <el-menu-item index="/communication">
              <el-icon><ChatLineRound /></el-icon>
              <span>AT指令交互</span>
            </el-menu-item>
            <el-menu-item index="/workflow">
              <el-icon><Operation /></el-icon>
              <span>工作流管理</span>
            </el-menu-item>
          </el-menu>
        </el-aside>

        <!-- Main Content -->
        <el-main class="main-content">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { 
  Connection, 
  Setting, 
  ChatLineRound,
  Operation
} from '@element-plus/icons-vue'
import { useConnectionStore } from '@/stores/connection'

const connectionStore = useConnectionStore()

onMounted(async () => {
  // 初始化时检查连接状态（异步执行，不阻塞界面）
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
  box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.15);
  backdrop-filter: blur(10px);
  z-index: 1000;
  height: 70px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 24px;
}

.header-left {
  display: flex;
  align-items: center;
  flex: 1;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  width: 40px;
  height: 40px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
}

.logo-icon .el-icon {
  font-size: 24px;
  color: white;
}

.logo-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.app-title {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: white;
  line-height: 1;
}

.app-subtitle {
  margin: 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.8);
  font-weight: 400;
  line-height: 1;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.status-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.status-item {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.status-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.7);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-tag {
  font-weight: 500;
  padding: 6px 12px;
  border-radius: 6px;
}

.content-container {
  flex: 1;
  height: calc(100vh - 70px); /* 减去header高度 */
  overflow: hidden; /* 防止整体滚动 */
}

.sidebar {
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  border-right: 1px solid #e2e8f0;
  box-shadow: 2px 0 12px rgba(0, 0, 0, 0.08);
  overflow: hidden; /* 确保侧边栏不会滚动 */
  display: flex;
  flex-direction: column;
}

.sidebar-menu {
  flex: 1;
  border-right: none;
  background: transparent;
  overflow: hidden;
  height: auto !important; /* 覆盖默认高度 */
  --el-menu-item-height: auto; /* 允许自定义高度 */
}

.sidebar-menu .el-menu-item {
  display: flex !important;
  align-items: center;
  gap: 12px;
  font-size: 15px;
  font-weight: 500;
  padding: 18px 20px !important;
  margin: 10px 16px;
  border-radius: 12px;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  position: relative;
  overflow: hidden;
  height: auto !important;
}

.sidebar-menu .el-menu-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(64, 158, 255, 0.1) 0%, rgba(103, 58, 183, 0.1) 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
  border-radius: 12px;
}

.sidebar-menu .el-menu-item:hover {
  background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
  color: #1976d2;
  transform: translateX(4px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
}

.sidebar-menu .el-menu-item:hover::before {
  opacity: 1;
}

.sidebar-menu .el-menu-item.is-active {
  background: linear-gradient(135deg, #409eff 0%, #667eea 100%);
  color: white;
  box-shadow: 0 6px 20px rgba(64, 158, 255, 0.4);
  transform: translateX(6px);
}

.sidebar-menu .el-menu-item.is-active .el-icon {
  color: white;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
}

.sidebar-menu .el-menu-item .el-icon {
  font-size: 18px;
  transition: all 0.3s ease;
}

.sidebar-menu .el-menu-item:hover .el-icon {
  transform: scale(1.1);
}

.main-content {
  background: linear-gradient(135deg, #f5f7fa 0%, #f8fafc 100%);
  padding: 0;
  overflow: auto;
  height: 100%;
  position: relative;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .header-content {
    max-width: 100%;
    padding: 0 16px;
  }
  
  .status-section {
    gap: 12px;
  }
  
  .header-right {
    gap: 16px;
  }
}

@media (max-width: 768px) {
  .header-content {
    padding: 0 12px;
  }
  
  .logo-section {
    gap: 8px;
  }
  
  .logo-icon {
    width: 32px;
    height: 32px;
  }
  
  .logo-icon .el-icon {
    font-size: 20px;
  }
  
  .app-title {
    font-size: 18px;
  }
  
  .app-subtitle {
    display: none;
  }
  
  .status-section {
    flex-direction: column;
    gap: 8px;
  }
  
  .status-item {
    align-items: center;
  }
  
  .header-right {
    gap: 12px;
  }
  
  .sidebar {
    width: 60px !important;
    min-width: 60px !important;
  }
  
  .sidebar-menu .el-menu-item {
    padding: 16px 8px;
    justify-content: center;
    margin: 8px 4px;
  }
  
  .sidebar-menu .el-menu-item span {
    display: none;
  }
  
  .sidebar-menu .el-menu-item .el-icon {
    margin-right: 0;
  }
}
</style>