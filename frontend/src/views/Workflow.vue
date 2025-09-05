<template>
  <div class="workflow-container">
    <div class="page-content">
      <el-card class="content-card">
        <div class="empty-state">
          <div class="empty-icon">
            <el-icon><Operation /></el-icon>
          </div>
          <h3 class="empty-title">工作流页面</h3>
          <p class="empty-description">这是一个空的工作流页面，您可以在这里添加工作流相关功能。</p>
          <el-button type="primary" size="large" class="empty-action">
            <el-icon><Plus /></el-icon>
            开始创建
          </el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Operation, Plus } from '@element-plus/icons-vue'
</script>

<style scoped>
.workflow-container {
  height: 100%;
  background: linear-gradient(135deg, #f5f7fa 0%, #f8fafc 100%);
}

.page-content {
  height: 100%;
  padding: 32px;
  overflow: auto;
}

.content-card {
  max-width: 1200px;
  margin: 0 auto;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 40px;
  text-align: center;
}

.empty-icon {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #409eff 0%, #667eea 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24px;
  box-shadow: 0 8px 24px rgba(64, 158, 255, 0.3);
}

.empty-icon .el-icon {
  font-size: 36px;
  color: white;
}

.empty-title {
  margin: 0 0 12px 0;
  font-size: 24px;
  font-weight: 600;
  color: #1a202c;
}

.empty-description {
  margin: 0 0 32px 0;
  font-size: 16px;
  color: #64748b;
  line-height: 1.6;
  max-width: 400px;
}

.empty-action {
  padding: 12px 24px;
  font-size: 16px;
  font-weight: 500;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
  transition: all 0.3s ease;
}

.empty-action:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(64, 158, 255, 0.4);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-content {
    padding: 20px;
  }
  
  .empty-state {
    padding: 60px 20px;
  }
  
  .empty-icon {
    width: 60px;
    height: 60px;
  }
  
  .empty-icon .el-icon {
    font-size: 28px;
  }
  
  .empty-title {
    font-size: 20px;
  }
  
  .empty-description {
    font-size: 14px;
  }
}
</style>
