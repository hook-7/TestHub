<template>
  <div class="terminal-view">
    <div class="page-header">
      <h1>命令行终端</h1>
      <p>通过WebSocket与后端进行实时命令行交互</p>
    </div>
    
    <div class="terminal-wrapper">
      <Terminal />
    </div>
    
    <div class="help-section">
      <el-collapse>
        <el-collapse-item title="快捷键说明" name="shortcuts">
          <div class="help-content">
            <ul>
              <li><kbd>Enter</kbd> - 执行命令</li>
              <li><kbd>↑</kbd>/<kbd>↓</kbd> - 浏览命令历史</li>
              <li><kbd>Ctrl+C</kbd> - 清空当前输入</li>
              <li><kbd>Ctrl+L</kbd> - 清屏</li>
              <li><kbd>Tab</kbd> - 命令自动补全（待实现）</li>
            </ul>
          </div>
        </el-collapse-item>
        
        <el-collapse-item title="常用命令" name="commands">
          <div class="help-content">
            <ul>
              <li><code>help</code> - 显示帮助信息</li>
              <li><code>system</code> - 显示系统信息</li>
              <li><code>status</code> - 显示系统状态</li>
              <li><code>version</code> - 显示版本信息</li>
              <li><code>ls [path]</code> - 列出目录内容</li>
              <li><code>pwd</code> - 显示当前目录</li>
              <li><code>ping [host]</code> - 网络连通性测试</li>
              <li><code>date</code> - 显示当前时间</li>
              <li><code>clear</code> - 清屏</li>
            </ul>
          </div>
        </el-collapse-item>
        
        <el-collapse-item title="安全说明" name="security">
          <div class="help-content">
            <p>为了系统安全，以下命令被禁止执行：</p>
            <ul>
              <li>文件删除命令：<code>rm</code>, <code>del</code></li>
              <li>格式化命令：<code>format</code>, <code>mkfs</code></li>
              <li>磁盘操作：<code>fdisk</code>, <code>dd</code></li>
            </ul>
            <p>所有命令执行都有10秒超时限制。</p>
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ElCollapse, ElCollapseItem } from 'element-plus'
import Terminal from '@/components/Terminal.vue'
</script>

<style scoped>
.terminal-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  padding: 20px;
  background-color: #f5f5f5;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h1 {
  color: #303133;
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 600;
}

.page-header p {
  color: #606266;
  margin: 0;
  font-size: 16px;
}

.terminal-wrapper {
  flex: 1;
  min-height: 500px;
  margin-bottom: 20px;
}

.help-section {
  background: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.help-content {
  padding: 8px 0;
}

.help-content ul {
  margin: 0;
  padding-left: 20px;
}

.help-content li {
  margin-bottom: 8px;
  line-height: 1.5;
}

.help-content code {
  background-color: #f1f2f6;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  color: #e83e8c;
}

.help-content kbd {
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 3px;
  padding: 2px 6px;
  font-family: inherit;
  font-size: 12px;
  color: #495057;
  box-shadow: 0 1px 1px rgba(0, 0, 0, 0.075);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .terminal-view {
    padding: 12px;
  }
  
  .page-header h1 {
    font-size: 24px;
  }
  
  .page-header p {
    font-size: 14px;
  }
  
  .terminal-wrapper {
    min-height: 400px;
  }
}
</style>