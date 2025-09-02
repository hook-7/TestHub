<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="login-header">
          <el-icon class="login-icon" size="40">
            <Connection />
          </el-icon>
          <h2 class="login-title">Industrial HMI 登录</h2>
          <p class="login-subtitle">串口通信管理系统</p>
        </div>
      </template>

      <!-- 会话状态显示 -->
      <div v-if="sessionStore.sessionStatus" class="session-status-info">
        <el-alert
          v-if="sessionStore.hasActiveSession && !sessionStore.isLoggedIn"
          title="检测到活跃会话"
          description="系统中已有其他客户端连接，请等待其主动退出或会话超时后再试"
          type="warning"
          :closable="false"
          show-icon
        />
        
        <!-- 显示当前活跃会话的详细信息 -->
        <div v-if="sessionStore.currentSession && !sessionStore.isLoggedIn" class="active-session-details">
          <el-card class="session-detail-card">
            <template #header>
              <h4>
                <el-icon><Monitor /></el-icon>
                当前活跃会话信息
              </h4>
            </template>
            <el-descriptions :column="1" size="small" border>
              <el-descriptions-item label="会话ID">
                <el-tag type="info" size="small">
                  {{ sessionStore.currentSession.session_id.substring(0, 12) }}...
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="客户端IP">
                <span class="ip-address">{{ sessionStore.currentSession.client_ip }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="用户代理">
                <span class="user-agent">{{ sessionStore.currentSession.user_agent || '未知' }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="创建时间">
                <span class="time-info">{{ formatTime(sessionStore.currentSession.created_at) }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="最后活动">
                <span class="time-info">{{ formatTime(sessionStore.currentSession.last_activity) }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="会话状态">
                <el-tag :type="sessionStore.currentSession.is_active ? 'success' : 'danger'" size="small">
                  {{ sessionStore.currentSession.is_active ? '活跃' : '非活跃' }}
                </el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </el-card>
        </div>
      </div>

      <!-- 登录表单 -->
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
        size="large"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="用户名（可选）"
            prefix-icon="User"
            clearable
          />
        </el-form-item>

        <el-form-item prop="clientInfo">
          <el-input
            v-model="loginForm.clientInfo"
            placeholder="客户端标识（可选）"
            prefix-icon="Monitor"
            clearable
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="sessionStore.isLoading"
            @click="handleLogin"
            class="login-btn"
            :disabled="sessionStore.hasActiveSession && !sessionStore.isLoggedIn"
          >
            <el-icon><Connection /></el-icon>
            {{ sessionStore.hasActiveSession && !sessionStore.isLoggedIn ? '系统忙碌中' : '登录系统' }}
          </el-button>
        </el-form-item>

        <!-- 等待提示 -->
        <el-form-item v-if="sessionStore.hasActiveSession && !sessionStore.isLoggedIn">
          <div class="waiting-hint">
            <el-alert
              title="系统正在被其他客户端使用"
              description="为保证系统安全，同一时间只允许一个客户端连接。请等待当前用户退出或会话超时。"
              type="info"
              :closable="false"
              show-icon
            />
          </div>
        </el-form-item>
      </el-form>

      <!-- 系统信息 -->
      <div class="system-info">
        <el-divider>系统信息</el-divider>
        <div class="info-grid">
          <div class="info-item">
            <el-icon><Monitor /></el-icon>
            <span>工业串口通信</span>
          </div>
          <div class="info-item">
            <el-icon><Connection /></el-icon>
            <span>会话管理</span>
          </div>
          <div class="info-item">
            <el-icon><Setting /></el-icon>
            <span>设备配置</span>
          </div>
          <div class="info-item">
            <el-icon><ChatLineRound /></el-icon>
            <span>AT指令交互</span>
          </div>
        </div>
      </div>


    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import {
  Connection,
  Monitor,
  Setting,
  ChatLineRound
} from '@element-plus/icons-vue'
import { useSessionStore } from '@/stores/session'

const router = useRouter()
const sessionStore = useSessionStore()

// 表单引用
const loginFormRef = ref<FormInstance>()

// 状态（移除了forceCleaningUp）

// 登录表单数据
const loginForm = reactive({
  username: '',
  clientInfo: navigator.userAgent || 'Unknown Client'
})

// 表单验证规则
const loginRules: FormRules = {
  // 暂时不设置必填规则，保持灵活性
}

// 处理登录
const handleLogin = async () => {
  try {
    const success = await sessionStore.login(loginForm.clientInfo)
    if (success) {
      ElMessage.success('登录成功')
      // 立即跳转，不延迟
      await router.push('/serial-config')
    }
  } catch (error) {
    console.error('Login failed:', error)
    ElMessage.error('登录失败，请稍后再试')
  }
}



// 格式化时间
const formatTime = (timeStr: string) => {
  return new Date(timeStr).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 生命周期
onMounted(async () => {
  // 如果已经登录，直接跳转
  if (sessionStore.isLoggedIn) {
    await router.push('/serial-config')
    return
  }
  
  // 只刷新会话状态，不重复初始化
  await sessionStore.refreshSessionStatus()
})
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-card {
  width: 100%;
  max-width: 450px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border-radius: 12px;
  overflow: hidden;
}

.login-header {
  text-align: center;
  padding: 20px 0 10px;
}

.login-icon {
  color: #409eff;
  margin-bottom: 10px;
}

.login-title {
  margin: 0 0 5px;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.login-subtitle {
  margin: 0;
  font-size: 14px;
  color: #909399;
}

.session-status-info {
  margin-bottom: 20px;
}

.login-form {
  padding: 0 20px;
}

.login-btn {
  width: 100%;
  margin-bottom: 10px;
}

.waiting-hint {
  width: 100%;
  margin: 10px 0;
}

.system-info {
  margin: 20px 0 0;
  padding: 0 20px 10px;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
  margin-top: 15px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #606266;
}

.info-item .el-icon {
  color: #409eff;
}

.active-session-details {
  margin: 15px 0;
}

.session-detail-card {
  margin-top: 15px;
}

.session-detail-card .el-card__header {
  padding: 12px 16px;
}

.session-detail-card .el-card__body {
  padding: 16px;
}

.ip-address {
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
  color: #606266;
}

.user-agent {
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
  word-break: break-all;
}

.time-info {
  font-size: 13px;
  color: #606266;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .login-container {
    padding: 10px;
  }
  
  .login-card {
    max-width: 100%;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
    gap: 10px;
  }
}

/* 动画效果 */
.login-card {
  animation: slideIn 0.5s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
