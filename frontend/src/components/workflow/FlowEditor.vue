<template>
  <div class="flow-editor">
    <VueFlow
      v-model:nodes="nodes"
      v-model:edges="edges"
      class="vue-flow"
      :default-viewport="{ zoom: 1 }"
      :min-zoom="0.2"
      :max-zoom="4"
      @nodes-change="onNodesChange"
      @edges-change="onEdgesChange"
      @connect="onConnect"
      @node-click="onNodeClick"
    >
      <Background pattern-color="#aaa" :gap="20" />
      <Controls />
      <MiniMap />

      <!-- 自定义节点 -->
      <template #node-send="{ data, id }">
        <SendNode :data="data" :id="id" @edit="editNode" @delete="deleteNode" />
      </template>
      
      <template #node-expect="{ data, id }">
        <ExpectNode :data="data" :id="id" @edit="editNode" @delete="deleteNode" />
      </template>
      
      <template #node-assign="{ data, id }">
        <AssignNode :data="data" :id="id" @edit="editNode" @delete="deleteNode" />
      </template>
      
      <template #node-confirm="{ data, id }">
        <ConfirmNode :data="data" :id="id" @edit="editNode" @delete="deleteNode" />
      </template>
      
      <template #node-control="{ data, id }">
        <ControlNode :data="data" :id="id" @edit="editNode" @delete="deleteNode" />
      </template>
    </VueFlow>

    <!-- 工具栏 -->
    <div class="toolbar">
      <el-button-group>
        <el-button 
          v-for="nodeType in nodeTypes" 
          :key="nodeType.type"
          @click="addNode(nodeType.type)"
          size="small"
        >
          <el-icon><component :is="nodeType.icon" /></el-icon>
          {{ nodeType.label }}
        </el-button>
      </el-button-group>
    </div>

    <!-- 节点编辑对话框 -->
    <el-dialog 
      v-model="editDialogVisible" 
      :title="`编辑${getNodeTypeLabel(editingNode?.type)}步骤`"
      width="600px"
      :close-on-click-modal="false"
    >
      <StepEditor 
        v-if="editDialogVisible && editingNode"
        :step="editingNode.data" 
        @save="handleNodeSave" 
        @cancel="handleNodeCancel" 
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { VueFlow, useVueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import { 
  Position, 
  type Node, 
  type Edge,
  type Connection,
  MarkerType
} from '@vue-flow/core'
import { ElMessage } from 'element-plus'
import { 
  Promotion, 
  Search, 
  Edit, 
  QuestionFilled, 
  Operation 
} from '@element-plus/icons-vue'

// 导入自定义节点组件
import SendNode from './nodes/SendNode.vue'
import ExpectNode from './nodes/ExpectNode.vue'
import AssignNode from './nodes/AssignNode.vue'
import ConfirmNode from './nodes/ConfirmNode.vue'
import ControlNode from './nodes/ControlNode.vue'
import StepEditor from './StepEditor.vue'
import type { WorkflowStep } from '@/api/workflow'

interface Props {
  steps: WorkflowStep[]
}

const props = defineProps<Props>()
const emit = defineEmits<{
  update: [steps: WorkflowStep[]]
}>()

// Vue Flow
const { addNodes, addEdges, removeNodes, removeEdges } = useVueFlow()

// 状态
const nodes = ref<Node[]>([])
const edges = ref<Edge[]>([])
const editDialogVisible = ref(false)
const editingNode = ref<Node | null>(null)

// 节点类型配置
const nodeTypes = [
  { type: 'send', label: '发送指令', icon: 'Promotion' },
  { type: 'expect', label: '期望回复', icon: 'Search' },
  { type: 'assign', label: '变量赋值', icon: 'Edit' },
  { type: 'confirm', label: '用户确认', icon: 'QuestionFilled' },
  { type: 'control', label: '逻辑控制', icon: 'Operation' }
]

// 方法
const getNodeTypeLabel = (type?: string) => {
  const nodeType = nodeTypes.find(nt => nt.type === type)
  return nodeType?.label || type
}

const generateNodeId = () => {
  return `node_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

const addNode = (type: string) => {
  const id = generateNodeId()
  const position = {
    x: Math.random() * 400 + 100,
    y: Math.random() * 300 + 100
  }

  // 创建默认步骤数据
  const defaultStep: Partial<WorkflowStep> = {
    id,
    name: `${getNodeTypeLabel(type)}${nodes.value.length + 1}`,
    type: type as any,
    description: ''
  }

  // 根据类型添加默认配置
  if (type === 'send') {
    Object.assign(defaultStep, { command: '', delay: 0 })
  } else if (type === 'expect') {
    Object.assign(defaultStep, { expect_type: 'string', pattern: '', timeout: 10 })
  } else if (type === 'assign') {
    Object.assign(defaultStep, { variable: '', expression: '' })
  } else if (type === 'confirm') {
    Object.assign(defaultStep, { message: '', options: ['确认', '取消'] })
  } else if (type === 'control') {
    Object.assign(defaultStep, { control_type: 'if', condition: '', steps: [] })
  }

  const newNode: Node = {
    id,
    type,
    position,
    data: defaultStep,
    sourcePosition: Position.Bottom,
    targetPosition: Position.Top
  }

  addNodes([newNode])
  
  // 立即编辑新节点
  editNode(id)
}

const editNode = (nodeId: string) => {
  const node = nodes.value.find(n => n.id === nodeId)
  if (node) {
    editingNode.value = node
    editDialogVisible.value = true
  }
}

const deleteNode = (nodeId: string) => {
  removeNodes([nodeId])
  // 同时删除相关的边
  const relatedEdges = edges.value.filter(e => e.source === nodeId || e.target === nodeId)
  if (relatedEdges.length > 0) {
    removeEdges(relatedEdges.map(e => e.id))
  }
}

const handleNodeSave = (stepData: WorkflowStep) => {
  if (editingNode.value) {
    editingNode.value.data = stepData
    editDialogVisible.value = false
    editingNode.value = null
    
    // 触发更新
    updateStepsFromNodes()
  }
}

const handleNodeCancel = () => {
  editDialogVisible.value = false
  editingNode.value = null
}

const onNodesChange = (changes: any[]) => {
  // 处理节点变化
  updateStepsFromNodes()
}

const onEdgesChange = (changes: any[]) => {
  // 处理边变化
}

const onConnect = (connection: Connection) => {
  // 创建新连接
  const newEdge: Edge = {
    id: `edge_${Date.now()}`,
    source: connection.source!,
    target: connection.target!,
    markerEnd: {
      type: MarkerType.ArrowClosed
    }
  }
  
  addEdges([newEdge])
}

const onNodeClick = (event: any) => {
  // 节点点击事件
}

const updateStepsFromNodes = () => {
  // 根据节点顺序更新步骤
  const sortedNodes = [...nodes.value].sort((a, b) => a.position.y - b.position.y)
  const steps = sortedNodes.map(node => node.data as WorkflowStep)
  emit('update', steps)
}

const loadStepsToNodes = () => {
  // 将步骤转换为节点
  const newNodes: Node[] = props.steps.map((step, index) => ({
    id: step.id,
    type: step.type,
    position: { x: 200, y: index * 120 + 50 },
    data: step,
    sourcePosition: Position.Bottom,
    targetPosition: Position.Top
  }))

  // 创建连接边
  const newEdges: Edge[] = []
  for (let i = 0; i < newNodes.length - 1; i++) {
    newEdges.push({
      id: `edge_${i}`,
      source: newNodes[i].id,
      target: newNodes[i + 1].id,
      markerEnd: {
        type: MarkerType.ArrowClosed
      }
    })
  }

  nodes.value = newNodes
  edges.value = newEdges
}

// 监听步骤变化
watch(() => props.steps, () => {
  loadStepsToNodes()
}, { immediate: true })

// 生命周期
onMounted(() => {
  loadStepsToNodes()
})
</script>

<style scoped>
.flow-editor {
  position: relative;
  width: 100%;
  height: 500px;
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  overflow: hidden;
}

.vue-flow {
  width: 100%;
  height: 100%;
}

.toolbar {
  position: absolute;
  top: 10px;
  left: 10px;
  z-index: 1000;
  background: white;
  border-radius: 6px;
  padding: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

:deep(.vue-flow__node) {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

:deep(.vue-flow__edge) {
  stroke-width: 2;
}

:deep(.vue-flow__edge.selected) {
  stroke: var(--el-color-primary);
}
</style>