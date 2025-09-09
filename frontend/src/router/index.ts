import { createRouter, createWebHistory } from 'vue-router'
import SerialConfig from '@/views/SerialConfig.vue'
import Communication from '@/views/Communication.vue'
import Workflow from '@/views/Workflow.vue'
import WorkflowOrchestration from '@/views/WorkflowOrchestration.vue'
import SerialTest from '@/views/SerialTest.vue'
import SerialIdTest from '@/views/SerialIdTest.vue'

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
        title: '串口配置'
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
    },
    {
      path: '/serial-test',
      name: 'SerialTest',
      component: SerialTest,
      meta: { 
        title: '串口测试'
      }
    },
    {
      path: '/serial-id-test',
      name: 'SerialIdTest',
      component: SerialIdTest,
      meta: { 
        title: '串口ID测试'
      }
    }
  ]
})

export default router