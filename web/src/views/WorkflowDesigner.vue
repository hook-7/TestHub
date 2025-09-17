<template>
  <div class="workflow-designer-container">
    <!-- 顶部工具栏 -->
    <div class="designer-toolbar">
      <div class="toolbar-left">
        <el-button @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <el-button @click="saveWorkflow" :loading="isSaving">
          <el-icon><Check /></el-icon>
          保存
        </el-button>
        <el-button @click="executeWorkflow" :loading="isExecuting">
          <el-icon><VideoPlay /></el-icon>
          执行
        </el-button>
      </div>
      <div class="toolbar-center">
        <h2 class="workflow-title">{{ workflow?.name || '未命名工作流' }}</h2>
        <el-tag :type="getStatusType(workflow?.status)" size="small">
          {{ getStatusText(workflow?.status) }}
        </el-tag>
      </div>
      <div class="toolbar-right">
        <el-button @click="showSettings = true">
          <el-icon><Setting /></el-icon>
          设置
        </el-button>
        <el-button @click="showNodePalette = !showNodePalette">
          <el-icon><Grid /></el-icon>
          {{ showNodePalette ? '隐藏' : '显示' }}节点面板
        </el-button>
      </div>
    </div>

    <div class="designer-content">
      <!-- 节点面板 -->
      <div v-if="showNodePalette" class="node-palette">
        <div class="palette-header">
          <h3>节点库</h3>
          <el-button type="text" @click="showNodePalette = false">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
        <div class="palette-content">
          <div class="node-category">
            <h4>基础节点</h4>
            <div class="node-list">
              <div 
                v-for="nodeType in basicNodeTypes" 
                :key="nodeType.type"
                class="palette-node"
                :class="nodeType.type"
                draggable="true"
                @dragstart="handleDragStart($event, nodeType)"
              >
                <el-icon>
                  <component :is="nodeType.icon" />
                </el-icon>
                <span>{{ nodeType.name }}</span>
              </div>
            </div>
          </div>
          
          <div class="node-category">
            <h4>命令节点</h4>
            <div class="node-list">
              <div 
                v-for="command in availableCommands" 
                :key="command.id"
                class="palette-node command"
                draggable="true"
                @dragstart="handleCommandDragStart($event, command)"
              >
                <el-icon><Command /></el-icon>
                <span>{{ command.name }}</span>
              </div>
            </div>
          </div>
          
          <div class="node-category">
            <h4>工作流节点</h4>
            <div class="node-list">
              <div 
                v-for="wf in availableWorkflows" 
                :key="wf.id"
                class="palette-node workflow"
                draggable="true"
                @dragstart="handleWorkflowDragStart($event, wf)"
              >
                <el-icon><Workflow /></el-icon>
                <span>{{ wf.name }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 画布区域 -->
      <div class="canvas-container">
        <div 
          ref="canvasRef"
          class="canvas"
          @drop="handleDrop"
          @dragover="handleDragOver"
          @click="handleCanvasClick"
        >
          <!-- 网格背景 -->
          <div class="grid-background"></div>
          
          <!-- 节点 -->
          <div
            v-for="node in workflow?.nodes || []"
            :key="node.id"
            class="workflow-node"
            :class="[node.type, { selected: selectedNode?.id === node.id }]"
            :style="{ left: node.position.x + 'px', top: node.position.y + 'px' }"
            @click.stop="selectNode(node)"
            @mousedown="startDrag(node, $event)"
          >
            <div class="node-header">
              <el-icon class="node-icon">
                <component :is="getNodeIcon(node.type)" />
              </el-icon>
              <span class="node-name">{{ node.name }}</span>
              <el-button 
                type="text" 
                size="small" 
                class="node-delete"
                @click.stop="deleteNode(node.id)"
              >
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
            <div class="node-content">
              <div v-if="node.type === 'command' && node.config.commandId" class="node-command">
                {{ getCommandName(node.config.commandId) }}
              </div>
              <div v-else-if="node.type === 'workflow' && node.config.workflowId" class="node-workflow">
                {{ getWorkflowName(node.config.workflowId) }}
              </div>
              <div v-else class="node-description">
                {{ node.description || '点击配置' }}
              </div>
            </div>
            
            <!-- 连接点 -->
            <div class="connection-points">
              <div 
                class="connection-point input"
                @mousedown.stop="startConnection(node.id, 'input', $event)"
              ></div>
              <div 
                class="connection-point output"
                @mousedown.stop="startConnection(node.id, 'output', $event)"
              ></div>
            </div>
          </div>

          <!-- 连接线 -->
          <svg class="connections-svg">
            <defs>
              <marker
                id="arrowhead"
                markerWidth="10"
                markerHeight="7"
                refX="9"
                refY="3.5"
                orient="auto"
              >
                <polygon points="0 0, 10 3.5, 0 7" fill="#667eea" />
              </marker>
            </defs>
            <path
              v-for="connection in workflow?.connections || []"
              :key="connection.id"
              :d="getConnectionPath(connection)"
              stroke="#667eea"
              stroke-width="2"
              fill="none"
              marker-end="url(#arrowhead)"
              class="connection-line"
              @click="selectConnection(connection)"
            />
          </svg>
        </div>
      </div>

      <!-- 属性面板 -->
      <div v-if="selectedNode" class="properties-panel">
        <div class="panel-header">
          <h3>节点属性</h3>
          <el-button type="text" @click="selectedNode = null">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
        <div class="panel-content">
          <el-form :model="nodeForm" label-width="80px">
            <el-form-item label="名称">
              <el-input v-model="nodeForm.name" @change="updateNode" />
            </el-form-item>
            <el-form-item label="描述">
              <el-input
                v-model="nodeForm.description"
                type="textarea"
                :rows="2"
                @change="updateNode"
              />
            </el-form-item>
            
            <!-- 命令节点配置 -->
            <div v-if="selectedNode?.type === 'command'">
              <el-form-item label="命令">
                <el-select
                  v-model="nodeForm.config.commandId"
                  placeholder="选择命令"
                  @change="updateNode"
                >
                  <el-option
                    v-for="command in availableCommands"
                    :key="command.id"
                    :label="command.name"
                    :value="command.id"
                  />
                </el-select>
              </el-form-item>
            </div>
            
            <!-- 工作流节点配置 -->
            <div v-if="selectedNode?.type === 'workflow'">
              <el-form-item label="工作流">
                <el-select
                  v-model="nodeForm.config.workflowId"
                  placeholder="选择工作流"
                  @change="updateNode"
                >
                  <el-option
                    v-for="wf in availableWorkflows"
                    :key="wf.id"
                    :label="wf.name"
                    :value="wf.id"
                  />
                </el-select>
              </el-form-item>
            </div>
            
            <!-- 条件节点配置 -->
            <div v-if="selectedNode?.type === 'condition'">
              <el-form-item label="条件">
                <el-input
                  v-model="nodeForm.config.condition"
                  placeholder="输入条件表达式"
                  @change="updateNode"
                />
              </el-form-item>
            </div>
            
            <!-- 延迟节点配置 -->
            <div v-if="selectedNode?.type === 'delay'">
              <el-form-item label="延迟时间">
                <el-input-number
                  v-model="nodeForm.config.delayTime"
                  :min="0"
                  :max="60000"
                  placeholder="毫秒"
                  @change="updateNode"
                />
              </el-form-item>
            </div>
            
            <!-- 通知节点配置 -->
            <div v-if="selectedNode?.type === 'notification'">
              <el-form-item label="标题">
                <el-input
                  v-model="nodeForm.config.notificationTitle"
                  @change="updateNode"
                />
              </el-form-item>
              <el-form-item label="内容">
                <el-input
                  v-model="nodeForm.config.notificationMessage"
                  type="textarea"
                  :rows="2"
                  @change="updateNode"
                />
              </el-form-item>
              <el-form-item label="类型">
                <el-select
                  v-model="nodeForm.config.notificationType"
                  @change="updateNode"
                >
                  <el-option label="信息" value="info" />
                  <el-option label="警告" value="warning" />
                  <el-option label="错误" value="error" />
                  <el-option label="成功" value="success" />
                </el-select>
              </el-form-item>
            </div>
          </el-form>
        </div>
      </div>
    </div>

    <!-- 执行对话框 -->
    <el-dialog
      v-model="showExecuteDialog"
      title="执行工作流"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="executeForm" label-width="100px">
        <el-form-item label="MAC地址" required>
          <el-input v-model="executeForm.macAddress" placeholder="请输入MAC地址" />
        </el-form-item>
        <el-form-item label="SN序列号">
          <el-input v-model="executeForm.serialNumber" placeholder="请输入SN序列号" />
        </el-form-item>
        <el-form-item label="操作员">
          <el-input v-model="executeForm.operator" placeholder="请输入操作员" />
        </el-form-item>
        <el-form-item label="工位">
          <el-input v-model="executeForm.workstation" placeholder="请输入工位" />
        </el-form-item>
        <el-form-item label="设备ID">
          <el-input v-model="executeForm.deviceId" placeholder="请输入设备ID" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showExecuteDialog = false">取消</el-button>
        <el-button type="primary" @click="handleExecuteWorkflow" :loading="isExecuting">
          开始执行
        </el-button>
      </template>
    </el-dialog>

    <!-- 设置对话框 -->
    <el-dialog
      v-model="showSettings"
      title="工作流设置"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form :model="settingsForm" label-width="120px">
        <el-form-item label="工作流名称">
          <el-input v-model="settingsForm.name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="settingsForm.description"
            type="textarea"
            :rows="3"
          />
        </el-form-item>
        <el-form-item label="需要MAC地址">
          <el-switch v-model="settingsForm.requireMacAddress" />
        </el-form-item>
        <el-form-item label="需要SN序列号">
          <el-switch v-model="settingsForm.requireSerialNumber" />
        </el-form-item>
        <el-form-item label="最大执行时间">
          <el-input-number
            v-model="settingsForm.maxExecutionTime"
            :min="1000"
            :max="3600000"
            :step="1000"
          />
          <span style="margin-left: 8px; color: #64748b;">毫秒</span>
        </el-form-item>
        <el-form-item label="失败时重试">
          <el-switch v-model="settingsForm.retryOnFailure" />
        </el-form-item>
        <el-form-item v-if="settingsForm.retryOnFailure" label="最大重试次数">
          <el-input-number
            v-model="settingsForm.maxRetries"
            :min="1"
            :max="10"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSettings = false">取消</el-button>
        <el-button type="primary" @click="handleSaveSettings">保存设置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft,
  Check,
  VideoPlay,
  Setting,
  Grid,
  Close,
  Command,
  Workflow,
  Condition,
  Clock,
  Bell,
  PlayCircle,
  Plus,
  Minus
} from '@element-plus/icons-vue'
import { useWorkflowStore } from '@/stores/workflow'
import { getAllCommands } from '@/api/commands'
import type { 
  WorkflowDefinition, 
  WorkflowNode, 
  WorkflowConnection, 
  WorkflowNodeType,
  WorkflowNodeConfig,
  SavedCommand
} from '@/types/workflow'

const route = useRoute()
const router = useRouter()
const workflowStore = useWorkflowStore()

// 响应式数据
const workflow = ref<WorkflowDefinition | null>(null)
const selectedNode = ref<WorkflowNode | null>(null)
const selectedConnection = ref<WorkflowConnection | null>(null)
const isSaving = ref(false)
const isExecuting = ref(false)
const showNodePalette = ref(true)
const showExecuteDialog = ref(false)
const showSettings = ref(false)

// 画布引用
const canvasRef = ref<HTMLElement>()

// 拖拽状态
const isDragging = ref(false)
const dragNode = ref<WorkflowNode | null>(null)
const dragOffset = ref({ x: 0, y: 0 })

// 连接状态
const isConnecting = ref(false)
const connectionStart = ref<{ nodeId: string; type: string } | null>(null)

// 表单数据
const nodeForm = ref({
  name: '',
  description: '',
  config: {} as WorkflowNodeConfig
})

const executeForm = ref({
  macAddress: '',
  serialNumber: '',
  operator: '',
  workstation: '',
  deviceId: ''
})

const settingsForm = ref({
  name: '',
  description: '',
  requireMacAddress: true,
  requireSerialNumber: false,
  maxExecutionTime: 300000,
  retryOnFailure: true,
  maxRetries: 3
})

// 可用命令和工作流
const availableCommands = ref<SavedCommand[]>([])
const availableWorkflows = ref<WorkflowDefinition[]>([])

// 基础节点类型
const basicNodeTypes = [
  { type: 'start', name: '开始', icon: PlayCircle },
  { type: 'end', name: '结束', icon: PlayCircle },
  { type: 'condition', name: '条件判断', icon: Condition },
  { type: 'delay', name: '延迟', icon: Clock },
  { type: 'notification', name: '通知', icon: Bell }
]

// 计算属性
const workflowId = computed(() => route.params.id as string)

// 方法
const loadWorkflow = async () => {
  try {
    if (workflowId.value) {
      await workflowStore.loadWorkflow(workflowId.value)
      workflow.value = workflowStore.currentWorkflow
      if (workflow.value) {
        settingsForm.value = {
          name: workflow.value.name,
          description: workflow.value.description || '',
          requireMacAddress: workflow.value.settings?.requireMacAddress || true,
          requireSerialNumber: workflow.value.settings?.requireSerialNumber || false,
          maxExecutionTime: workflow.value.settings?.maxExecutionTime || 300000,
          retryOnFailure: workflow.value.settings?.retryOnFailure || true,
          maxRetries: workflow.value.settings?.maxRetries || 3
        }
      }
    }
  } catch (error) {
    console.error('加载工作流失败:', error)
    ElMessage.error('加载工作流失败')
  }
}

const loadCommands = async () => {
  try {
    const response = await getAllCommands()
    availableCommands.value = response.commands
  } catch (error) {
    console.error('加载命令失败:', error)
  }
}

const loadWorkflows = async () => {
  try {
    await workflowStore.loadWorkflows()
    availableWorkflows.value = workflowStore.workflows.filter(w => w.id !== workflowId.value)
  } catch (error) {
    console.error('加载工作流失败:', error)
  }
}

const goBack = () => {
  router.push('/workflow-orchestration')
}

const saveWorkflow = async () => {
  if (!workflow.value) return
  
  try {
    isSaving.value = true
    await workflowStore.updateWorkflow(workflow.value.id, workflow.value)
    ElMessage.success('工作流保存成功')
  } catch (error) {
    console.error('保存工作流失败:', error)
    ElMessage.error('保存工作流失败')
  } finally {
    isSaving.value = false
  }
}

const executeWorkflow = () => {
  if (!workflow.value) return
  showExecuteDialog.value = true
}

const handleExecuteWorkflow = async () => {
  if (!workflow.value) return
  
  if (!executeForm.value.macAddress.trim()) {
    ElMessage.warning('请输入MAC地址')
    return
  }

  try {
    isExecuting.value = true
    await workflowStore.executeWorkflow({
      workflowId: workflow.value.id,
      macAddress: executeForm.value.macAddress,
      serialNumber: executeForm.value.serialNumber,
      operator: executeForm.value.operator,
      workstation: executeForm.value.workstation,
      deviceId: executeForm.value.deviceId
    })
    
    ElMessage.success('工作流执行已开始')
    showExecuteDialog.value = false
    executeForm.value = {
      macAddress: '',
      serialNumber: '',
      operator: '',
      workstation: '',
      deviceId: ''
    }
  } catch (error) {
    console.error('执行工作流失败:', error)
    ElMessage.error('执行工作流失败')
  } finally {
    isExecuting.value = false
  }
}

const handleSaveSettings = async () => {
  if (!workflow.value) return
  
  try {
    await workflowStore.updateWorkflow(workflow.value.id, {
      name: settingsForm.value.name,
      description: settingsForm.value.description,
      settings: {
        ...workflow.value.settings,
        requireMacAddress: settingsForm.value.requireMacAddress,
        requireSerialNumber: settingsForm.value.requireSerialNumber,
        maxExecutionTime: settingsForm.value.maxExecutionTime,
        retryOnFailure: settingsForm.value.retryOnFailure,
        maxRetries: settingsForm.value.maxRetries
      }
    })
    
    ElMessage.success('设置保存成功')
    showSettings.value = false
    await loadWorkflow()
  } catch (error) {
    console.error('保存设置失败:', error)
    ElMessage.error('保存设置失败')
  }
}

// 节点操作
const selectNode = (node: WorkflowNode) => {
  selectedNode.value = node
  selectedConnection.value = null
  nodeForm.value = {
    name: node.name,
    description: node.description || '',
    config: { ...node.config }
  }
}

const selectConnection = (connection: WorkflowConnection) => {
  selectedConnection.value = connection
  selectedNode.value = null
}

const handleCanvasClick = () => {
  selectedNode.value = null
  selectedConnection.value = null
}

const deleteNode = async (nodeId: string) => {
  try {
    await ElMessageBox.confirm('确定要删除这个节点吗？', '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    if (workflow.value) {
      workflow.value.nodes = workflow.value.nodes.filter(n => n.id !== nodeId)
      workflow.value.connections = workflow.value.connections.filter(
        c => c.sourceNodeId !== nodeId && c.targetNodeId !== nodeId
      )
      selectedNode.value = null
    }
  } catch (error) {
    // 用户取消删除
  }
}

const updateNode = () => {
  if (!selectedNode.value || !workflow.value) return
  
  const nodeIndex = workflow.value.nodes.findIndex(n => n.id === selectedNode.value!.id)
  if (nodeIndex !== -1) {
    workflow.value.nodes[nodeIndex] = {
      ...workflow.value.nodes[nodeIndex],
      name: nodeForm.value.name,
      description: nodeForm.value.description,
      config: { ...nodeForm.value.config }
    }
    selectedNode.value = workflow.value.nodes[nodeIndex]
  }
}

// 拖拽操作
const handleDragStart = (event: DragEvent, nodeType: any) => {
  if (!event.dataTransfer) return
  
  event.dataTransfer.setData('application/json', JSON.stringify({
    type: 'node',
    nodeType: nodeType.type
  }))
}

const handleCommandDragStart = (event: DragEvent, command: SavedCommand) => {
  if (!event.dataTransfer) return
  
  event.dataTransfer.setData('application/json', JSON.stringify({
    type: 'command',
    commandId: command.id
  }))
}

const handleWorkflowDragStart = (event: DragEvent, workflow: WorkflowDefinition) => {
  if (!event.dataTransfer) return
  
  event.dataTransfer.setData('application/json', JSON.stringify({
    type: 'workflow',
    workflowId: workflow.id
  }))
}

const handleDragOver = (event: DragEvent) => {
  event.preventDefault()
}

const handleDrop = (event: DragEvent) => {
  event.preventDefault()
  
  if (!event.dataTransfer || !workflow.value) return
  
  try {
    const data = JSON.parse(event.dataTransfer.getData('application/json'))
    const rect = canvasRef.value?.getBoundingClientRect()
    if (!rect) return
    
    const x = event.clientX - rect.left
    const y = event.clientY - rect.top
    
    const newNode: WorkflowNode = {
      id: generateId(),
      type: data.type === 'node' ? data.nodeType : data.type,
      name: getDefaultNodeName(data),
      description: '',
      position: { x, y },
      status: 'pending',
      config: getDefaultNodeConfig(data),
      createdAt: Date.now(),
      updatedAt: Date.now()
    }
    
    workflow.value.nodes.push(newNode)
  } catch (error) {
    console.error('处理拖拽失败:', error)
  }
}

const startDrag = (node: WorkflowNode, event: MouseEvent) => {
  isDragging.value = true
  dragNode.value = node
  
  const rect = canvasRef.value?.getBoundingClientRect()
  if (!rect) return
  
  dragOffset.value = {
    x: event.clientX - rect.left - node.position.x,
    y: event.clientY - rect.top - node.position.y
  }
  
  document.addEventListener('mousemove', handleDragMove)
  document.addEventListener('mouseup', handleDragEnd)
}

const handleDragMove = (event: MouseEvent) => {
  if (!isDragging.value || !dragNode.value || !workflow.value) return
  
  const rect = canvasRef.value?.getBoundingClientRect()
  if (!rect) return
  
  const x = event.clientX - rect.left - dragOffset.value.x
  const y = event.clientY - rect.top - dragOffset.value.y
  
  const nodeIndex = workflow.value.nodes.findIndex(n => n.id === dragNode.value!.id)
  if (nodeIndex !== -1) {
    workflow.value.nodes[nodeIndex].position = { x, y }
  }
}

const handleDragEnd = () => {
  isDragging.value = false
  dragNode.value = null
  dragOffset.value = { x: 0, y: 0 }
  
  document.removeEventListener('mousemove', handleDragMove)
  document.removeEventListener('mouseup', handleDragEnd)
}

// 连接操作
const startConnection = (nodeId: string, type: string, event: MouseEvent) => {
  isConnecting.value = true
  connectionStart.value = { nodeId, type }
  
  document.addEventListener('mousemove', handleConnectionMove)
  document.addEventListener('mouseup', handleConnectionEnd)
}

const handleConnectionMove = (event: MouseEvent) => {
  // 实现连接线绘制逻辑
}

const handleConnectionEnd = (event: MouseEvent) => {
  isConnecting.value = false
  connectionStart.value = null
  
  document.removeEventListener('mousemove', handleConnectionMove)
  document.removeEventListener('mouseup', handleConnectionEnd)
}

// 工具函数
const generateId = () => {
  return 'node_' + Math.random().toString(36).substr(2, 9)
}

const getDefaultNodeName = (data: any) => {
  switch (data.type) {
    case 'node':
      return basicNodeTypes.find(t => t.type === data.nodeType)?.name || '节点'
    case 'command':
      return availableCommands.value.find(c => c.id === data.commandId)?.name || '命令'
    case 'workflow':
      return availableWorkflows.value.find(w => w.id === data.workflowId)?.name || '工作流'
    default:
      return '节点'
  }
}

const getDefaultNodeConfig = (data: any): WorkflowNodeConfig => {
  switch (data.type) {
    case 'command':
      return { commandId: data.commandId }
    case 'workflow':
      return { workflowId: data.workflowId }
    case 'condition':
      return { condition: '' }
    case 'delay':
      return { delayTime: 1000 }
    case 'notification':
      return { 
        notificationTitle: '通知',
        notificationMessage: '',
        notificationType: 'info'
      }
    default:
      return {}
  }
}

const getNodeIcon = (type: WorkflowNodeType) => {
  switch (type) {
    case 'start': return PlayCircle
    case 'end': return PlayCircle
    case 'command': return Command
    case 'workflow': return Workflow
    case 'condition': return Condition
    case 'delay': return Clock
    case 'notification': return Bell
    default: return Command
  }
}

const getCommandName = (commandId: string) => {
  const command = availableCommands.value.find(c => c.id === commandId)
  return command?.name || '未知命令'
}

const getWorkflowName = (workflowId: string) => {
  const workflow = availableWorkflows.value.find(w => w.id === workflowId)
  return workflow?.name || '未知工作流'
}

const getConnectionPath = (connection: WorkflowConnection) => {
  const sourceNode = workflow.value?.nodes.find(n => n.id === connection.sourceNodeId)
  const targetNode = workflow.value?.nodes.find(n => n.id === connection.targetNodeId)
  
  if (!sourceNode || !targetNode) return ''
  
  const startX = sourceNode.position.x + 100
  const startY = sourceNode.position.y + 50
  const endX = targetNode.position.x
  const endY = targetNode.position.y + 50
  
  return `M ${startX} ${startY} L ${endX} ${endY}`
}

const getStatusType = (status?: string) => {
  switch (status) {
    case 'active': return 'success'
    case 'draft': return 'info'
    case 'inactive': return 'warning'
    case 'running': return 'primary'
    case 'completed': return 'success'
    case 'failed': return 'danger'
    case 'cancelled': return 'info'
    default: return 'info'
  }
}

const getStatusText = (status?: string) => {
  switch (status) {
    case 'active': return '激活'
    case 'draft': return '草稿'
    case 'inactive': return '未激活'
    case 'running': return '运行中'
    case 'completed': return '已完成'
    case 'failed': return '失败'
    case 'cancelled': return '已取消'
    default: return '未知'
  }
}

// 监听选中节点变化
watch(selectedNode, (newNode) => {
  if (newNode) {
    nodeForm.value = {
      name: newNode.name,
      description: newNode.description || '',
      config: { ...newNode.config }
    }
  }
})

// 组件挂载
onMounted(async () => {
  await loadWorkflow()
  await loadCommands()
  await loadWorkflows()
})
</script>

<style scoped>
.workflow-designer-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f8fafc;
}

.designer-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: white;
  border-bottom: 1px solid #e2e8f0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.06);
}

.toolbar-left,
.toolbar-right {
  display: flex;
  gap: 8px;
  align-items: center;
}

.toolbar-center {
  display: flex;
  align-items: center;
  gap: 12px;
}

.workflow-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1a202c;
}

.designer-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.node-palette {
  width: 280px;
  background: white;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
}

.palette-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e2e8f0;
}

.palette-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1a202c;
}

.palette-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.node-category {
  margin-bottom: 24px;
}

.node-category h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.node-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.palette-node {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  cursor: grab;
  transition: all 0.2s ease;
  font-size: 14px;
  color: #374151;
}

.palette-node:hover {
  background: #f1f5f9;
  border-color: #667eea;
  transform: translateY(-1px);
}

.palette-node:active {
  cursor: grabbing;
}

.palette-node.start {
  background: #f0fdf4;
  border-color: #22c55e;
  color: #16a34a;
}

.palette-node.end {
  background: #fef2f2;
  border-color: #ef4444;
  color: #dc2626;
}

.palette-node.command {
  background: #f0f9ff;
  border-color: #3b82f6;
  color: #2563eb;
}

.palette-node.workflow {
  background: #faf5ff;
  border-color: #8b5cf6;
  color: #7c3aed;
}

.palette-node.condition {
  background: #fffbeb;
  border-color: #f59e0b;
  color: #d97706;
}

.palette-node.delay {
  background: #f1f5f9;
  border-color: #64748b;
  color: #475569;
}

.palette-node.notification {
  background: #fef3c7;
  border-color: #f59e0b;
  color: #d97706;
}

.canvas-container {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.canvas {
  width: 100%;
  height: 100%;
  position: relative;
  background: #fafbfc;
  cursor: grab;
}

.canvas:active {
  cursor: grabbing;
}

.grid-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: 
    linear-gradient(rgba(0, 0, 0, 0.1) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 0, 0, 0.1) 1px, transparent 1px);
  background-size: 20px 20px;
  pointer-events: none;
}

.workflow-node {
  position: absolute;
  width: 200px;
  background: white;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: move;
  transition: all 0.2s ease;
  user-select: none;
}

.workflow-node:hover {
  border-color: #667eea;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.workflow-node.selected {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.workflow-node.start {
  border-color: #22c55e;
}

.workflow-node.end {
  border-color: #ef4444;
}

.workflow-node.command {
  border-color: #3b82f6;
}

.workflow-node.workflow {
  border-color: #8b5cf6;
}

.workflow-node.condition {
  border-color: #f59e0b;
}

.workflow-node.delay {
  border-color: #64748b;
}

.workflow-node.notification {
  border-color: #f59e0b;
}

.node-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-bottom: 1px solid #e2e8f0;
  background: #f8fafc;
  border-radius: 6px 6px 0 0;
}

.node-icon {
  font-size: 16px;
  color: #667eea;
}

.node-name {
  flex: 1;
  font-size: 14px;
  font-weight: 600;
  color: #1a202c;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.node-delete {
  padding: 4px;
  color: #94a3b8;
  opacity: 0;
  transition: all 0.2s ease;
}

.workflow-node:hover .node-delete {
  opacity: 1;
}

.node-delete:hover {
  color: #ef4444;
}

.node-content {
  padding: 12px 16px;
  font-size: 12px;
  color: #64748b;
  line-height: 1.4;
}

.node-command,
.node-workflow {
  font-weight: 500;
  color: #374151;
}

.connection-points {
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  transform: translateY(-50%);
  pointer-events: none;
}

.connection-point {
  position: absolute;
  width: 12px;
  height: 12px;
  background: #667eea;
  border: 2px solid white;
  border-radius: 50%;
  pointer-events: all;
  cursor: crosshair;
  transition: all 0.2s ease;
}

.connection-point:hover {
  background: #5a67d8;
  transform: scale(1.2);
}

.connection-point.input {
  left: -6px;
}

.connection-point.output {
  right: -6px;
}

.connections-svg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.connection-line {
  pointer-events: all;
  cursor: pointer;
  transition: all 0.2s ease;
}

.connection-line:hover {
  stroke: #5a67d8;
  stroke-width: 3;
}

.properties-panel {
  width: 320px;
  background: white;
  border-left: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e2e8f0;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1a202c;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .node-palette {
    width: 240px;
  }
  
  .properties-panel {
    width: 280px;
  }
}

@media (max-width: 768px) {
  .designer-content {
    flex-direction: column;
  }
  
  .node-palette {
    width: 100%;
    height: 200px;
    border-right: none;
    border-bottom: 1px solid #e2e8f0;
  }
  
  .properties-panel {
    width: 100%;
    height: 300px;
    border-left: none;
    border-top: 1px solid #e2e8f0;
  }
  
  .workflow-node {
    width: 160px;
  }
  
  .node-header {
    padding: 8px 12px;
  }
  
  .node-content {
    padding: 8px 12px;
  }
}
</style>