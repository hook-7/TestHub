/**
 * 工作流编排相关的类型定义
 */

// 工作流节点类型
export enum WorkflowNodeType {
  START = 'start',           // 开始节点
  END = 'end',              // 结束节点
  COMMAND = 'command',      // 命令执行节点
  CONDITION = 'condition',  // 条件判断节点
  LOOP = 'loop',           // 循环节点
  PARALLEL = 'parallel',   // 并行执行节点
  DELAY = 'delay',         // 延迟节点
  NOTIFICATION = 'notification' // 通知节点
}

// 工作流节点状态
export enum WorkflowNodeStatus {
  PENDING = 'pending',     // 等待执行
  RUNNING = 'running',     // 执行中
  SUCCESS = 'success',     // 执行成功
  FAILED = 'failed',       // 执行失败
  SKIPPED = 'skipped',     // 跳过执行
  CANCELLED = 'cancelled'  // 取消执行
}

// 工作流状态
export enum WorkflowStatus {
  DRAFT = 'draft',         // 草稿
  ACTIVE = 'active',       // 激活
  INACTIVE = 'inactive',   // 未激活
  RUNNING = 'running',     // 运行中
  COMPLETED = 'completed', // 已完成
  FAILED = 'failed',       // 失败
  CANCELLED = 'cancelled'  // 已取消
}

// 工作流节点基础接口
export interface WorkflowNode {
  id: string
  type: WorkflowNodeType
  name: string
  description?: string
  position: { x: number; y: number }
  status: WorkflowNodeStatus
  config: WorkflowNodeConfig
  createdAt: number
  updatedAt: number
}

// 工作流节点配置
export interface WorkflowNodeConfig {
  // 命令节点配置
  commandId?: string        // 关联的命令ID
  command?: string          // 直接命令内容
  expectedResponse?: string // 期望响应
  timeout?: number         // 超时时间(ms)
  retryCount?: number      // 重试次数
  
  // 条件节点配置
  condition?: string       // 条件表达式
  trueNext?: string        // 条件为真时的下一个节点ID
  falseNext?: string       // 条件为假时的下一个节点ID
  
  // 循环节点配置
  loopCount?: number       // 循环次数
  loopCondition?: string   // 循环条件
  loopNext?: string        // 循环内的下一个节点ID
  loopEnd?: string         // 循环结束后的下一个节点ID
  
  // 并行节点配置
  parallelNodes?: string[] // 并行执行的节点ID列表
  
  // 延迟节点配置
  delayTime?: number       // 延迟时间(ms)
  
  // 通知节点配置
  notificationTitle?: string // 通知标题
  notificationMessage?: string // 通知内容
  notificationType?: 'info' | 'warning' | 'error' | 'success' // 通知类型
}

// 工作流连接
export interface WorkflowConnection {
  id: string
  sourceNodeId: string
  targetNodeId: string
  label?: string
  condition?: string
  createdAt: number
}

// 工作流定义
export interface WorkflowDefinition {
  id: string
  name: string
  description?: string
  version: string
  status: WorkflowStatus
  nodes: WorkflowNode[]
  connections: WorkflowConnection[]
  variables: WorkflowVariable[]
  settings: WorkflowSettings
  createdAt: number
  updatedAt: number
  createdBy?: string
}

// 工作流变量
export interface WorkflowVariable {
  id: string
  name: string
  type: 'string' | 'number' | 'boolean' | 'object'
  value: any
  description?: string
  isRequired: boolean
}

// 工作流设置
export interface WorkflowSettings {
  autoStart: boolean           // 自动开始
  maxExecutionTime: number     // 最大执行时间(ms)
  retryOnFailure: boolean      // 失败时重试
  maxRetries: number          // 最大重试次数
  parallelExecution: boolean   // 允许并行执行
  timeout: number             // 全局超时时间(ms)
}

// 工作流执行实例
export interface WorkflowExecution {
  id: string
  workflowId: string
  workflowName: string
  status: WorkflowStatus
  startTime: number
  endTime?: number
  currentNodeId?: string
  variables: Record<string, any>
  logs: WorkflowExecutionLog[]
  result?: WorkflowExecutionResult
  error?: string
  createdAt: number
}

// 工作流执行日志
export interface WorkflowExecutionLog {
  id: string
  nodeId: string
  nodeName: string
  nodeType: WorkflowNodeType
  status: WorkflowNodeStatus
  message: string
  data?: any
  timestamp: number
  duration?: number
}

// 工作流执行结果
export interface WorkflowExecutionResult {
  success: boolean
  totalNodes: number
  executedNodes: number
  successNodes: number
  failedNodes: number
  skippedNodes: number
  duration: number
  variables: Record<string, any>
}

// 工作流模板
export interface WorkflowTemplate {
  id: string
  name: string
  description?: string
  category: string
  tags: string[]
  workflow: WorkflowDefinition
  isPublic: boolean
  downloadCount: number
  rating: number
  createdAt: number
  updatedAt: number
  createdBy?: string
}

// 工作流统计
export interface WorkflowStats {
  totalWorkflows: number
  activeWorkflows: number
  totalExecutions: number
  successExecutions: number
  failedExecutions: number
  averageExecutionTime: number
  mostUsedTemplates: WorkflowTemplate[]
}

// 工作流创建请求
export interface CreateWorkflowRequest {
  name: string
  description?: string
  nodes: Omit<WorkflowNode, 'id' | 'createdAt' | 'updatedAt'>[]
  connections: Omit<WorkflowConnection, 'id' | 'createdAt'>[]
  variables?: Omit<WorkflowVariable, 'id'>[]
  settings?: Partial<WorkflowSettings>
}

// 工作流更新请求
export interface UpdateWorkflowRequest {
  name?: string
  description?: string
  nodes?: Omit<WorkflowNode, 'id' | 'createdAt' | 'updatedAt'>[]
  connections?: Omit<WorkflowConnection, 'id' | 'createdAt'>[]
  variables?: Omit<WorkflowVariable, 'id'>[]
  settings?: Partial<WorkflowSettings>
  status?: WorkflowStatus
}

// 工作流执行请求
export interface ExecuteWorkflowRequest {
  workflowId: string
  variables?: Record<string, any>
  macAddress?: string
  operator?: string
  workstation?: string
  deviceId?: string
}

// 工作流列表响应
export interface WorkflowListResponse {
  workflows: WorkflowDefinition[]
  total: number
  page: number
  pageSize: number
}

// 工作流执行列表响应
export interface WorkflowExecutionListResponse {
  executions: WorkflowExecution[]
  total: number
  page: number
  pageSize: number
}

// 工作流模板列表响应
export interface WorkflowTemplateListResponse {
  templates: WorkflowTemplate[]
  total: number
  page: number
  pageSize: number
}