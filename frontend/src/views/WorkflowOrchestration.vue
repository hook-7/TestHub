<template>
  <div class="workflow-orchestration-container">
    <div class="page-content">
      <el-card class="content-card">
        <template #header>
          <div class="card-header">
            <div class="header-content">
              <el-icon class="header-icon"><Operation /></el-icon>
              <div class="header-text">
                <h3 class="page-title">工作流编排</h3>
                <p class="page-description">设计和管理自动化测试工作流程</p>
              </div>
            </div>
          </div>
        </template>
        
        <div class="orchestration-content">
          <!-- 空状态提示 -->
          <div class="empty-state">
            <div class="empty-icon">
              <el-icon><Operation /></el-icon>
            </div>
            <h4 class="empty-title">工作流编排功能</h4>
            <p class="empty-description">
              此功能正在开发中，将提供可视化的工作流设计器，让您能够：
            </p>
            <ul class="feature-list">
              <li>拖拽式创建工作流节点</li>
              <li>配置测试步骤和条件分支</li>
              <li>设置循环和并行执行</li>
              <li>管理工作流模板和版本</li>
              <li>监控工作流执行状态</li>
            </ul>
            <div class="action-buttons">
              <el-button type="primary" size="large" disabled>
                <el-icon><Plus /></el-icon>
                创建工作流
              </el-button>
              <el-button type="info" size="large" disabled>
                <el-icon><Document /></el-icon>
                导入模板
              </el-button>
            </div>
          </div>

          <!-- 功能预览卡片 -->
          <div class="preview-section">
            <el-divider content-position="left">
              <span class="divider-text">功能预览</span>
            </el-divider>
            
            <div class="preview-cards">
              <div class="preview-card">
                <div class="card-icon">
                  <el-icon><Grid /></el-icon>
                </div>
                <h5 class="card-title">可视化设计器</h5>
                <p class="card-description">拖拽式界面，直观设计测试流程</p>
              </div>
              
              <div class="preview-card">
                <div class="card-icon">
                  <el-icon><Connection /></el-icon>
                </div>
                <h5 class="card-title">节点连接</h5>
                <p class="card-description">灵活连接测试步骤，支持条件分支</p>
              </div>
              
              <div class="preview-card">
                <div class="card-icon">
                  <el-icon><Timer /></el-icon>
                </div>
                <h5 class="card-title">定时执行</h5>
                <p class="card-description">支持定时触发和事件驱动执行</p>
              </div>
              
              <div class="preview-card">
                <div class="card-icon">
                  <el-icon><Monitor /></el-icon>
                </div>
                <h5 class="card-title">实时监控</h5>
                <p class="card-description">实时查看工作流执行状态和结果</p>
              </div>
            </div>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { 
  Operation, 
  Plus, 
  Document, 
  Grid, 
  Connection, 
  Timer, 
  Monitor 
} from '@element-plus/icons-vue'
</script>

<style scoped>
.workflow-orchestration-container {
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

/* 卡片头部 */
.card-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px;
}

.header-icon {
  font-size: 32px;
  background: rgba(255, 255, 255, 0.2);
  padding: 16px;
  border-radius: 12px;
  backdrop-filter: blur(10px);
}

.header-text {
  flex: 1;
}

.page-title {
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 700;
  color: white;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.page-description {
  margin: 0;
  font-size: 16px;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 400;
}

/* 编排内容 */
.orchestration-content {
  padding: 40px;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 16px;
  border: 2px dashed #cbd5e1;
  margin-bottom: 40px;
}

.empty-icon {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 24px;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
}

.empty-icon .el-icon {
  font-size: 40px;
  color: white;
}

.empty-title {
  margin: 0 0 16px 0;
  font-size: 24px;
  font-weight: 600;
  color: #1a202c;
}

.empty-description {
  margin: 0 0 24px 0;
  font-size: 16px;
  color: #64748b;
  line-height: 1.6;
}

.feature-list {
  text-align: left;
  max-width: 400px;
  margin: 0 auto 32px;
  padding: 0;
  list-style: none;
}

.feature-list li {
  padding: 8px 0;
  color: #374151;
  font-size: 15px;
  position: relative;
  padding-left: 24px;
}

.feature-list li::before {
  content: '✓';
  position: absolute;
  left: 0;
  color: #10b981;
  font-weight: bold;
  font-size: 16px;
}

.action-buttons {
  display: flex;
  gap: 16px;
  justify-content: center;
  flex-wrap: wrap;
}

.action-buttons .el-button {
  padding: 12px 24px;
  font-size: 16px;
  font-weight: 500;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.action-buttons .el-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 预览区域 */
.preview-section {
  margin-top: 40px;
}

.divider-text {
  font-weight: 600;
  color: #1a202c;
  font-size: 16px;
}

.preview-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 24px;
  margin-top: 24px;
}

.preview-card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.preview-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  border-color: #667eea;
}

.card-icon {
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
}

.card-icon .el-icon {
  font-size: 28px;
  color: white;
}

.card-title {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: #1a202c;
}

.card-description {
  margin: 0;
  font-size: 14px;
  color: #64748b;
  line-height: 1.5;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-content {
    padding: 20px;
  }
  
  .orchestration-content {
    padding: 24px 16px;
  }
  
  .header-content {
    flex-direction: column;
    text-align: center;
    gap: 12px;
    padding: 20px;
  }
  
  .header-icon {
    font-size: 28px;
    padding: 12px;
  }
  
  .page-title {
    font-size: 24px;
  }
  
  .page-description {
    font-size: 14px;
  }
  
  .empty-state {
    padding: 40px 16px;
  }
  
  .empty-icon {
    width: 60px;
    height: 60px;
  }
  
  .empty-icon .el-icon {
    font-size: 30px;
  }
  
  .empty-title {
    font-size: 20px;
  }
  
  .empty-description {
    font-size: 14px;
  }
  
  .action-buttons {
    flex-direction: column;
    align-items: center;
  }
  
  .action-buttons .el-button {
    width: 200px;
  }
  
  .preview-cards {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .preview-card {
    padding: 20px;
  }
  
  .card-icon {
    width: 50px;
    height: 50px;
  }
  
  .card-icon .el-icon {
    font-size: 24px;
  }
  
  .card-title {
    font-size: 16px;
  }
  
  .card-description {
    font-size: 13px;
  }
}

@media (max-width: 480px) {
  .page-content {
    padding: 16px;
  }
  
  .orchestration-content {
    padding: 20px 12px;
  }
  
  .header-content {
    padding: 16px;
  }
  
  .header-icon {
    font-size: 24px;
    padding: 10px;
  }
  
  .page-title {
    font-size: 20px;
  }
  
  .page-description {
    font-size: 13px;
  }
  
  .empty-state {
    padding: 30px 12px;
  }
  
  .empty-icon {
    width: 50px;
    height: 50px;
  }
  
  .empty-icon .el-icon {
    font-size: 24px;
  }
  
  .empty-title {
    font-size: 18px;
  }
  
  .empty-description {
    font-size: 13px;
  }
  
  .feature-list {
    max-width: 100%;
  }
  
  .feature-list li {
    font-size: 14px;
  }
  
  .action-buttons .el-button {
    width: 100%;
    max-width: 200px;
  }
  
  .preview-card {
    padding: 16px;
  }
  
  .card-icon {
    width: 45px;
    height: 45px;
  }
  
  .card-icon .el-icon {
    font-size: 20px;
  }
  
  .card-title {
    font-size: 15px;
  }
  
  .card-description {
    font-size: 12px;
  }
}
</style>
