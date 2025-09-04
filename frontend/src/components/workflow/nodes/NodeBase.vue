<template>
  <!-- 这是一个样式基础文件，用于定义通用节点样式 -->
</template>

<style>
.workflow-node {
  min-width: 200px;
  max-width: 280px;
  border: 2px solid;
  border-radius: 8px;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: all 0.2s;
}

.workflow-node:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.workflow-node.selected {
  border-width: 3px;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.node-header {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.9);
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  gap: 8px;
}

.node-icon {
  font-size: 16px;
}

.node-title {
  flex: 1;
  font-weight: 500;
  font-size: 14px;
}

.node-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

.workflow-node:hover .node-actions {
  opacity: 1;
}

.node-content {
  padding: 12px;
  background: rgba(255, 255, 255, 0.95);
}

.config-item {
  display: flex;
  align-items: flex-start;
  margin-bottom: 6px;
  gap: 8px;
}

.config-item:last-child {
  margin-bottom: 0;
}

.config-item .label {
  font-size: 12px;
  color: #666;
  min-width: 40px;
  font-weight: 500;
}

.config-item .value {
  flex: 1;
  font-size: 12px;
  line-height: 1.4;
  word-break: break-all;
}

.config-item code.value {
  background: rgba(0, 0, 0, 0.05);
  padding: 2px 4px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
}
</style>