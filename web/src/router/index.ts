import { createRouter, createWebHistory } from 'vue-router'
import SerialConfig from '@/views/SerialConfig.vue'
import Communication from '@/views/Communication.vue'
import Workflow from '@/views/Workflow.vue'
import WorkflowOrchestration from '@/views/WorkflowOrchestration.vue'

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
      meta: { 
        title: '接口配置'
      }
    },
    {
      path: '/communication',
      name: 'Communication',
      component: Communication,
      meta: { 
        title: 'AT指令交互'
      }
    },
    {
      path: '/workflow',
      name: 'Workflow',
      component: Workflow,
      meta: { 
        title: '工作流管理'
      }
    },
    {
      path: '/workflow-orchestration',
      name: 'WorkflowOrchestration',
      component: WorkflowOrchestration,
      meta: { 
        title: '工作流编排'
      }
    }
  ]
})

export default router