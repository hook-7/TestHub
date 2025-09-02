import { createRouter, createWebHistory } from 'vue-router'
import SerialConfig from '@/views/SerialConfig.vue'
import Communication from '@/views/Communication.vue'
import TerminalView from '@/views/TerminalView.vue'

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
      meta: { title: 'AT指令交互' }
    },
    {
      path: '/terminal',
      name: 'Terminal',
      component: TerminalView,
      meta: { title: '命令行终端' }
    }
  ]
})

export default router