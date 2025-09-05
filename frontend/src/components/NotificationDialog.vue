<template>
  <el-dialog
    v-model="visible"
    :title="notification?.title || '通知'"
    width="480px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :show-close="!notification?.requireConfirm"
    @close="handleClose"
  >
    <div class="notification-content">
      <!-- 通知图标 -->
      <div class="notification-icon" :class="`icon-${notification?.level || 'info'}`">
        <el-icon size="24">
          <InfoFilled v-if="notification?.level === 'info'" />
          <WarningFilled v-else-if="notification?.level === 'warning'" />
          <CircleCloseFilled v-else-if="notification?.level === 'error'" />
          <CircleCheckFilled v-else-if="notification?.level === 'success'" />
          <InfoFilled v-else />
        </el-icon>
      </div>

      <!-- 通知消息 -->
      <div class="notification-message">
        <p>{{ notification?.message }}</p>
      </div>
    </div>

    <!-- 底部按钮 -->
    <template #footer>
      <div class="dialog-footer">
        <el-button 
          v-if="!notification?.requireConfirm" 
          @click="handleClose"
        >
          关闭
        </el-button>
        <el-button 
          v-if="notification?.requireConfirm" 
          type="primary" 
          @click="handleConfirm"
        >
          确认
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { 
  InfoFilled, 
  WarningFilled, 
  CircleCloseFilled, 
  CircleCheckFilled 
} from '@element-plus/icons-vue'
import type { WSNotificationMessage } from '@/services/websocket'

interface Props {
  modelValue: boolean
  notification: WSNotificationMessage | null
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'confirm', notification: WSNotificationMessage): void
  (e: 'close', notification: WSNotificationMessage | null): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const visible = ref(false)

// 监听modelValue变化
watch(() => props.modelValue, (newValue) => {
  visible.value = newValue
})

// 监听visible变化
watch(visible, (newValue) => {
  emit('update:modelValue', newValue)
})

const handleConfirm = () => {
  if (props.notification) {
    emit('confirm', props.notification)
  }
  handleClose()
}

const handleClose = () => {
  visible.value = false
  emit('close', props.notification)
}
</script>

<style scoped>
.notification-content {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 8px 0;
}

.notification-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
}

.icon-info {
  background-color: var(--el-color-info-light-9);
  color: var(--el-color-info);
}

.icon-warning {
  background-color: var(--el-color-warning-light-9);
  color: var(--el-color-warning);
}

.icon-error {
  background-color: var(--el-color-danger-light-9);
  color: var(--el-color-danger);
}

.icon-success {
  background-color: var(--el-color-success-light-9);
  color: var(--el-color-success);
}

.notification-message {
  flex: 1;
  line-height: 1.6;
  color: var(--el-text-color-primary);
}

.notification-message p {
  margin: 0;
  word-break: break-word;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

:deep(.el-dialog__header) {
  padding: 20px 20px 10px 20px;
}

:deep(.el-dialog__body) {
  padding: 10px 20px 20px 20px;
}

:deep(.el-dialog__footer) {
  padding: 0 20px 20px 20px;
}
</style>