<template>
  <div class="expect-node workflow-node">
    <div class="node-header">
      <el-icon class="node-icon"><Search /></el-icon>
      <span class="node-title">{{ data.name }}</span>
      <div class="node-actions">
        <el-button size="small" @click="$emit('edit', id)" :icon="Edit" />
        <el-button size="small" type="danger" @click="$emit('delete', id)" :icon="Delete" />
      </div>
    </div>
    
    <div class="node-content">
      <div class="config-item">
        <span class="label">类型:</span>
        <span class="value">{{ data.expect_type || 'string' }}</span>
      </div>
      
      <div class="config-item">
        <span class="label">模式:</span>
        <code class="value">{{ data.pattern || '未配置' }}</code>
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
import { Search, Edit, Delete } from '@element-plus/icons-vue'

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

.expect-node {
  border-color: #409EFF;
  background: linear-gradient(135deg, #409EFF, #66B1FF);
}

.expect-node .node-header {
  background: rgba(255, 255, 255, 0.9);
  color: #409EFF;
}
</style>