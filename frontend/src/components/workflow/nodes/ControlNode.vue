<template>
  <div class="control-node workflow-node">
    <div class="node-header">
      <el-icon class="node-icon"><Operation /></el-icon>
      <span class="node-title">{{ data.name }}</span>
      <div class="node-actions">
        <el-button size="small" @click="$emit('edit', id)" :icon="Edit" />
        <el-button size="small" type="danger" @click="$emit('delete', id)" :icon="Delete" />
      </div>
    </div>
    
    <div class="node-content">
      <div class="config-item">
        <span class="label">类型:</span>
        <span class="value">{{ getControlTypeLabel(data.control_type) }}</span>
      </div>
      
      <div class="config-item" v-if="data.condition">
        <span class="label">条件:</span>
        <code class="value">{{ truncateText(data.condition, 25) }}</code>
      </div>
      
      <div class="config-item" v-if="data.steps?.length">
        <span class="label">子步骤:</span>
        <span class="value">{{ data.steps.length }} 个</span>
      </div>
    </div>

    <Handle type="target" :position="Position.Top" />
    <Handle type="source" :position="Position.Bottom" />
  </div>
</template>

<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'
import { Operation, Edit, Delete } from '@element-plus/icons-vue'

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

const getControlTypeLabel = (type: string) => {
  const labels = {
    if: '条件判断',
    loop: '循环',
    break: '跳出',
    continue: '继续'
  }
  return labels[type as keyof typeof labels] || type
}
</script>

<style scoped>
@import './NodeBase.vue';

.control-node {
  border-color: #909399;
  background: linear-gradient(135deg, #909399, #A6A9AD);
}

.control-node .node-header {
  background: rgba(255, 255, 255, 0.9);
  color: #909399;
}
</style>