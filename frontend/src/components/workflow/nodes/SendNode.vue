<template>
  <div class="send-node workflow-node">
    <div class="node-header">
      <el-icon class="node-icon"><Promotion /></el-icon>
      <span class="node-title">{{ data.name }}</span>
      <div class="node-actions">
        <el-button size="small" @click="$emit('edit', id)" :icon="Edit" />
        <el-button size="small" type="danger" @click="$emit('delete', id)" :icon="Delete" />
      </div>
    </div>
    
    <div class="node-content">
      <div class="config-item">
        <span class="label">指令:</span>
        <code class="value">{{ data.command || '未配置' }}</code>
      </div>
      
      <div class="config-item" v-if="data.delay">
        <span class="label">延迟:</span>
        <span class="value">{{ data.delay }}秒</span>
      </div>
    </div>

    <Handle type="target" :position="Position.Top" />
    <Handle type="source" :position="Position.Bottom" />
  </div>
</template>

<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'
import { Promotion, Edit, Delete } from '@element-plus/icons-vue'

interface Props {
  data: any
  id: string
}

defineProps<Props>()
defineEmits<{
  edit: [nodeId: string]
  delete: [nodeId: string]
}>()
</script>

<style scoped>
@import './NodeBase.vue';

.send-node {
  border-color: #67C23A;
  background: linear-gradient(135deg, #67C23A, #85CE61);
}

.send-node .node-header {
  background: rgba(255, 255, 255, 0.9);
  color: #67C23A;
}
</style>