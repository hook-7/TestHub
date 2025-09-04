<template>
  <div class="assign-node workflow-node">
    <div class="node-header">
      <el-icon class="node-icon"><Edit /></el-icon>
      <span class="node-title">{{ data.name }}</span>
      <div class="node-actions">
        <el-button size="small" @click="$emit('edit', id)" :icon="Edit" />
        <el-button size="small" type="danger" @click="$emit('delete', id)" :icon="Delete" />
      </div>
    </div>
    
    <div class="node-content">
      <div class="config-item">
        <span class="label">变量:</span>
        <code class="value">{{ data.variable || '未配置' }}</code>
      </div>
      
      <div class="config-item">
        <span class="label">表达式:</span>
        <code class="value">{{ truncateText(data.expression || '未配置', 30) }}</code>
      </div>
    </div>

    <Handle type="target" :position="Position.Top" />
    <Handle type="source" :position="Position.Bottom" />
  </div>
</template>

<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'
import { Edit, Delete } from '@element-plus/icons-vue'

interface Props {
  data: any
  id: string
}

defineProps<Props>()
defineEmits<{
  edit: [nodeId: string]
  delete: [nodeId: string]
}>()

const truncateText = (text: string, maxLength: number) => {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}
</script>

<style scoped>
@import './NodeBase.vue';

.assign-node {
  border-color: #E6A23C;
  background: linear-gradient(135deg, #E6A23C, #ELB563);
}

.assign-node .node-header {
  background: rgba(255, 255, 255, 0.9);
  color: #E6A23C;
}
</style>