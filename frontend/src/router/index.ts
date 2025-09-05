import { createRouter, createWebHistory } from 'vue-router'
import { ElMessage } from 'element-plus'
import Login from '@/views/Login.vue'
import SerialConfig from '@/views/SerialConfig.vue'
import Communication from '@/views/Communication.vue'
import Workflow from '@/views/Workflow.vue'
import { useSessionStore } from '@/stores/session'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/login'
    },
    {
      path: '/login',
      name: 'Login',
      component: Login,
      meta: { 
        title: '登录',
        requiresAuth: false 
      }
    },
    {
      path: '/serial-config',
      name: 'SerialConfig',
      component: SerialConfig,
      meta: { 
        title: '串口配置',
        requiresAuth: true
      }
    },
    {
      path: '/communication',
      name: 'Communication',
      component: Communication,
      meta: { 
        title: 'AT指令交互',
        requiresAuth: true
      }
    },
    {
      path: '/workflow',
      name: 'Workflow',
      component: Workflow,
      meta: { 
        title: '工作流管理',
        requiresAuth: true
      }
    }
  ]
})

// 路由守卫
router.beforeEach(async (to, _from, next) => {
  const sessionStore = useSessionStore()
  
  // 只在完全未初始化时才初始化
  if (!sessionStore.sessionId && !sessionStore.isLoggedIn && !sessionStore.sessionStatus) {
    await sessionStore.init()
  }
  
  // 检查路由是否需要认证
  const requiresAuth = to.meta.requiresAuth !== false
  
  if (requiresAuth) {
    // 需要认证的页面
    if (!sessionStore.isLoggedIn) {
      ElMessage.warning('请先登录')
      next('/login')
      return
    }
    
    // 只有在会话可能过期时才验证（减少不必要的API调用）
    if (!sessionStore.isHeartbeatActive) {
      const isValid = await sessionStore.validateSession()
      if (!isValid) {
        ElMessage.error('会话已过期，请重新登录')
        next('/login')
        return
      }
    }
  } else {
    // 不需要认证的页面（如登录页）
    if (to.path === '/login' && sessionStore.isLoggedIn) {
      // 如果已经登录，重定向到主页
      next('/serial-config')
      return
    }
  }
  
  next()
})

export default router