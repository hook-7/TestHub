import { createRouter, createWebHistory } from 'vue-router'
import SerialConfig from '@/views/SerialConfig.vue'
import Communication from '@/views/Communication.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/serial-config'
    },
    {
      path: '/serial-config',
      name: 'SerialConfig',
      component: SerialConfig,
      meta: { title: '串口配置' }
    },
    {
      path: '/communication',
      name: 'Communication',
      component: Communication,
      meta: { title: '通信测试' }
    }
  ]
})

export default router