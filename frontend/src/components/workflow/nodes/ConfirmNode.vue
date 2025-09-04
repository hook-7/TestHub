<template>
  <div class="confirm-node workflow-node">
    <div class="node-header">
      <el-icon class="node-icon"><QuestionFilled /></el-icon>
      <span class="node-title">{{ data.name }}</span>
      <div class="node-actions">
        <el-button size="small" @click="$emit('edit', id)" :icon="Edit" />
        <el-button size="small" type="danger" @click="$emit('delete', id)" :icon="Delete" />
      </div>
    </div>
    
    <div class="node-content">
      <div class="config-item">
        <span class="label">消息:</span>
        <span class="value">{{ truncateText(data.message || '未配置', 25) }}</span>
      </div>
      
      <div class="config-item">
        <span class="label">选项:</span>
        <span class="value">{{ (data.options || []).join(', ') }}</span>
      </div>
      
      <div class="config-item" v-if="data.timeout">
        <span class="label">超时:</span>
        <span class="value">{{ data.timeout }}秒</span>
      </div>
    </div>

    <Handle type="target" :position="Position.Top" />
    <Handle type="source" :position="Position.Bottom" />
  </div>
</template>

<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'
import { QuestionFilled, Edit, Delete } from '@element-plus/icons-vue'

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

.confirm-node {
  border-color: #F56C6C;
  background: linear-gradient(135deg, #F56C6C, #F78989);
}

.confirm-node .node-header {
  background: rgba(255, 255, 255, 0.9);
  color: #F56C6C;
}
</style>