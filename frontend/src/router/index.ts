import { createRouter, createWebHistory } from 'vue-router'
import { useSessionStore } from '@/stores/session'
import SerialConfig from '@/views/SerialConfig.vue'
import SerialLoginConfig from '@/views/SerialLoginConfig.vue'
import Communication from '@/views/Communication.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/serial-login-config'
    },
    {
      path: '/serial-config',
      name: 'SerialConfig',
      component: SerialConfig,
      meta: { title: '串口配置' }
    },
    {
      path: '/serial-login-config',
      name: 'SerialLoginConfig',
      component: SerialLoginConfig,
      meta: { title: '串口登录配置' }
    },
    {
      path: '/communication',
      name: 'Communication',
      component: Communication,
      meta: { title: 'AT指令交互', requiresAuth: true }
    }
  ]
})

// 路由守卫
router.beforeEach((to, _from, next) => {
  const sessionStore = useSessionStore()
  
  // 检查是否需要认证
  if (to.meta.requiresAuth && !sessionStore.isLoggedIn) {
    // 未登录，重定向到串口配置页面
    next('/serial-config')
  } else {
    next()
  }
})

export default router