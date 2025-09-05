<template>
  <div class="page-container">
    <!-- 状态栏 -->
    <div class="status-bar">
      <div class="status-info">
        <div class="connection-badge" :class="{ connected: connectionStore.isConnected, disconnected: !connectionStore.isConnected }">
          <el-icon class="status-icon">
            <component :is="connectionStore.isConnected ? 'CircleCheckFilled' : 'CircleCloseFilled'" />
          </el-icon>
          <span class="status-text">
            {{ connectionStore.isConnected ? `已连接 (${connectionStore.currentPort})` : '未连接' }}
          </span>
        </div>
        
        <!-- WebSocket连接状态 -->
        <div class="realtime-badge" :class="{ connected: communicationStore.isRealTimeConnected, disconnected: !communicationStore.isRealTimeConnected }">
          <el-icon class="status-icon">
            <span v-if="communicationStore.isRealTimeConnected" class="connected-icon">●</span>
            <span v-else class="disconnected-icon">●</span>
          </el-icon>
          <span class="status-text">
            WebSocket {{ communicationStore.isRealTimeConnected ? '已连接' : '连接中' }}
          </span>
        </div>
      </div>
    </div>

    <el-row :gutter="20" class="main-row">
      <!-- 左侧：AT指令操作面板 -->
      <el-col :span="12">
        <el-card class="command-card">
          <template #header>
            <div class="card-header">
              <h3 class="card-title">
                <el-icon class="title-icon"><Operation /></el-icon>
                指令交互
              </h3>
            </div>
          </template>

          <!-- 指令输入区 -->
          <div class="form-section">
            <el-form :model="commandForm" label-width="80px">
              <el-form-item label="指令内容">
                <el-input
                v-model="commandForm.command"
                placeholder="输入指令内容，例如: AT+GMR 或任何自定义指令"
                style="font-family: monospace;"
                @keyup.enter="sendCommand"
              >
                <template #append>
                  <el-button 
                    type="primary" 
                    @click="sendCommand"
                    :disabled="!connectionStore.isConnected"
                    :loading="commandLoading"
                  >
                    <el-icon><Position /></el-icon>
                    发送
                  </el-button>
                </template>
              </el-input>
            </el-form-item>
            
            <!-- 指令控制选项 -->
            <el-form-item label="控制选项">
              <div class="command-controls">
                <el-checkbox v-model="commandForm.autoAddCRLF" size="small">
                  自动添加\r\n
                </el-checkbox>
                <el-select v-model="commandForm.lineEnding" size="small" style="width: 120px; margin-left: 12px;">
                  <el-option label="\r\n (CRLF)" value="\r\n" />
                  <el-option label="\r (CR)" value="\r" />
                  <el-option label="\n (LF)" value="\n" />
                  <el-option label="无终止符" value="" />
                </el-select>
                <el-button 
                  size="small" 
                  @click="clearCommandInput" 
                  style="margin-left: 12px;"
                >
                  清空
                </el-button>
              </div>
            </el-form-item>
          </el-form>

          <!-- 原始数据发送 -->
          <el-divider>原始数据发送</el-divider>
          <el-form :model="rawForm" label-width="80px">
            <el-form-item label="十六进制">
              <el-input
                v-model="rawForm.data"
                placeholder="输入十六进制数据，例如: 41 54 0D 0A (不区分大小写，可用空格分隔)"
                style="font-family: monospace;"
                @keyup.enter="sendRawData"
                @input="formatHexInput"
              >
                <template #append>
                  <el-button 
                    type="primary" 
                    @click="sendRawData"
                    :disabled="!connectionStore.isConnected"
                    :loading="rawLoading"
                  >
                    <el-icon><Position /></el-icon>
                    发送
                  </el-button>
                </template>
              </el-input>
            </el-form-item>
          </el-form>

          <!-- 常用指令快捷按钮 -->
          <div class="commands-section">
            <div class="command-header">
              <h4 class="command-title">常用指令</h4>
              <div class="command-actions">
                <el-button size="small" @click="showAddCommand = true">
                  <el-icon><Plus /></el-icon>
                  添加指令
                </el-button>
                <el-button size="small" @click="showHistory = !showHistory">
                  <el-icon><Clock /></el-icon>
                  历史记录
                </el-button>
                <el-button size="small" @click="showBatchSend = !showBatchSend">
                  <el-icon><List /></el-icon>
                  批量发送
                </el-button>
                <el-button size="small" @click="showWorkflowManager = !showWorkflowManager">
                  <el-icon><Operation /></el-icon>
                  流水作业
                </el-button>
              </div>
            </div>
            <div class="quick-commands">
              <div
                v-for="cmd in savedCommands"
                :key="cmd.id"
                class="quick-command-btn"
                @click="sendQuickCommand(cmd.command)"
                @contextmenu.prevent="handleCommandRightClick($event, cmd)"
                :class="{ disabled: !connectionStore.isConnected }"
                :title="cmd.description"
              >
                <div class="command-content">
                  <div class="quick-command-name">{{ cmd.name }}</div>
                  <div class="quick-command-text">{{ cmd.command }}</div>
                  <div v-if="cmd.expected_response" class="quick-command-expected">
                    期望: {{ cmd.expected_response }}
                  </div>
                </div>
                <div class="command-actions">
                  <el-icon
                    class="edit-icon"
                    @click.stop="openEditCommand(cmd)"
                    :title="`编辑指令: ${cmd.name}`"
                  >
                    <Edit />
                  </el-icon>
                  <el-icon
                    class="delete-icon"
                    @click.stop="deleteCommand(cmd)"
                    :title="`删除指令: ${cmd.name}`"
                  >
                    <Delete />
                  </el-icon>
                </div>
              </div>
              
              <!-- 当没有常用指令时显示提示 -->
              <div v-if="savedCommands.length === 0" class="no-commands-hint">
                <el-text type="info" size="small">
                  暂无常用指令，点击"添加指令"来创建您的第一个常用指令
                </el-text>
              </div>
            </div>
          </div>

          <!-- 历史记录 -->
          <el-collapse-transition>
            <div v-show="showHistory" style="margin-top: 16px;">
              <h4>指令历史</h4>
              <div class="history-commands">
                <el-tag 
                  v-for="(cmd, index) in commandHistory" 
                  :key="index"
                  size="small"
                  style="margin: 2px; cursor: pointer;"
                  @click="commandForm.command = cmd"
                  :title="`点击填入: ${cmd}`"
                >
                  {{ cmd }}
                </el-tag>
                <el-button v-if="commandHistory.length > 0" size="small" @click="clearHistory">
                  清空历史
                </el-button>
              </div>
            </div>
          </el-collapse-transition>

          <!-- 批量发送 -->
          <el-collapse-transition>
            <div v-show="showBatchSend" style="margin-top: 16px;">
              <h4>批量发送</h4>
              <el-input
                v-model="batchCommands"
                type="textarea"
                :rows="4"
                placeholder="每行一个指令，例如:&#10;AT&#10;AT+GMR&#10;AT+CSQ"
                style="font-family: monospace;"
              />
              <div style="margin-top: 8px;">
                <el-button 
                  type="primary" 
                  size="small"
                  @click="sendBatchCommands"
                  :disabled="!connectionStore.isConnected"
                  :loading="batchLoading"
                >
                  批量发送
                </el-button>
                <el-input-number 
                  v-model="batchDelay"
                  :min="100"
                  :max="10000"
                  :step="100"
                  size="small"
                  style="width: 120px; margin-left: 8px;"
                />
                <span style="margin-left: 4px; font-size: 12px; color: #666;">ms间隔</span>
              </div>
            </div>
          </el-collapse-transition>

          <!-- 流水作业管理 -->
          <el-collapse-transition>
            <div v-show="showWorkflowManager" style="margin-top: 16px;">
              <div class="workflow-header">
                <h4>流水作业管理</h4>
                <el-button 
                  type="primary" 
                  size="small"
                  @click="openCreateWorkflow"
                >
                  <el-icon><Plus /></el-icon>
                  创建工作流
                </el-button>
              </div>
              
              <div class="workflow-list">
                <div
                  v-for="workflow in workflows"
                  :key="workflow.id"
                  class="workflow-item"
                >
                  <div class="workflow-info">
                    <div class="workflow-name">{{ workflow.name }}</div>
                    <div class="workflow-description">{{ workflow.description || '无描述' }}</div>
                    <div class="workflow-steps-count">{{ workflow.steps.length }} 个步骤</div>
                  </div>
                  <div class="workflow-actions">
                    <el-button
                      size="small"
                      type="success"
                      @click="executeWorkflow(workflow)"
                      :disabled="!connectionStore.isConnected"
                      title="执行工作流"
                    >
                      <el-icon><VideoPlay /></el-icon>
                      执行
                    </el-button>
                    <el-button
                      size="small"
                      @click="openEditWorkflow(workflow)"
                      title="编辑工作流"
                    >
                      <el-icon><Edit /></el-icon>
                      编辑
                    </el-button>
                    <el-button
                      size="small"
                      type="danger"
                      @click="deleteWorkflow(workflow)"
                      title="删除工作流"
                    >
                      <el-icon><Delete /></el-icon>
                      删除
                    </el-button>
                  </div>
                </div>
                
                <div v-if="workflows.length === 0" class="no-workflows-hint">
                  <el-text type="info" size="small">
                    暂无工作流，点击"创建工作流"来创建您的第一个流水作业
                  </el-text>
                </div>
              </div>
            </div>
          </el-collapse-transition>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：通信日志 -->
      <el-col :span="12">
        <el-card class="log-card">
          <template #header>
            <div class="card-header">
              <h3 class="card-title">
                <el-icon class="title-icon"><ChatDotSquare /></el-icon>
                通信日志
              </h3>
              <div class="header-actions">
                <el-button @click="clearLogs" size="small" type="danger" plain class="clear-logs-btn">
                  <el-icon><Delete /></el-icon>
                  清空日志
                </el-button>
                <el-button @click="exportLogs" size="small" type="primary" plain>
                  <el-icon><Download /></el-icon>
                  导出日志
                </el-button>
              </div>
            </div>
          </template>

          <div class="log-container">
            <div 
              v-for="log in communicationStore.logs" 
              :key="log.id"
              class="log-item"
              :class="[
                log.direction,
                log.direction === 'received' ? (log.success ? 'success' : 'error') : ''
              ]"
            >
              <div class="log-header">
                <span>
                  <el-icon>
                    <component :is="getLogIcon(log)" />
                  </el-icon>
                  {{ log.description }}
                </span>
                <span class="log-timestamp">
                  {{ formatTime(log.timestamp) }}
                </span>
              </div>
              <div class="log-data">{{ log.data }}</div>
            </div>
            
            <div v-if="communicationStore.logs.length === 0" class="empty-logs">
              <el-empty description="暂无通信日志" />
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 添加指令对话框 -->
    <el-dialog
      v-model="showAddCommand"
      title="添加常用指令"
      width="500px"
      :before-close="handleCloseAddCommand"
    >
      <el-form :model="newCommand" label-width="80px">
        <el-form-item label="指令名称" required>
          <el-input
            v-model="newCommand.name"
            placeholder="例如: 查询版本"
            maxlength="20"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="指令内容" required>
          <el-input
            v-model="newCommand.command"
            placeholder="例如: AT+GMR"
            style="font-family: monospace;"
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="newCommand.description"
            placeholder="指令说明（可选）"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="期望返回值">
          <el-input
            v-model="newCommand.expected_response"
            placeholder="指令执行后的期望返回值（可选）"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showAddCommand = false">取消</el-button>
          <el-button type="primary" @click="addNewCommand">确定</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 编辑指令对话框 -->
    <el-dialog
      v-model="showEditCommand"
      title="编辑常用指令"
      width="500px"
      :before-close="handleCloseEditCommand"
    >
      <el-form :model="editCommand" label-width="80px">
        <el-form-item label="指令名称" required>
          <el-input
            v-model="editCommand.name"
            placeholder="例如: 查询版本"
            maxlength="20"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="指令内容" required>
          <el-input
            v-model="editCommand.command"
            placeholder="例如: AT+GMR"
            style="font-family: monospace;"
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="editCommand.description"
            placeholder="指令说明（可选）"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="期望返回值">
          <el-input
            v-model="editCommand.expected_response"
            placeholder="指令执行后的期望返回值（可选）"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleCloseEditCommand">取消</el-button>
          <el-button type="primary" @click="updateCommand">确定</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 创建工作流对话框 -->
    <el-dialog
      v-model="showCreateWorkflow"
      title="创建流水作业"
      width="800px"
    >
      <el-form :model="newWorkflow" label-width="80px">
        <el-form-item label="名称" required>
          <el-input
            v-model="newWorkflow.name"
            placeholder="请输入工作流名称"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="newWorkflow.description"
            type="textarea"
            placeholder="请输入工作流描述（可选）"
            maxlength="500"
            show-word-limit
            :rows="2"
          />
        </el-form-item>
        <el-form-item label="步骤">
          <div class="workflow-steps">
            <div
              v-for="(step, index) in newWorkflow.steps"
              :key="index"
              class="workflow-step"
            >
              <div class="step-header">
                <span class="step-number">步骤 {{ step.step_order }}</span>
                <div class="step-actions">
                  <el-button
                    size="small"
                    @click="moveStepUp(index, false)"
                    :disabled="index === 0"
                    title="上移"
                  >
                    <el-icon><ArrowUp /></el-icon>
                  </el-button>
                  <el-button
                    size="small"
                    @click="moveStepDown(index, false)"
                    :disabled="index === newWorkflow.steps.length - 1"
                    title="下移"
                  >
                    <el-icon><ArrowDown /></el-icon>
                  </el-button>
                  <el-button
                    size="small"
                    type="danger"
                    @click="removeWorkflowStep(index, false)"
                    title="删除"
                  >
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
              </div>
              <el-row :gutter="16">
                <el-col :span="12">
                  <el-form-item label="指令" size="small">
                    <el-select
                      v-model="step.command_id"
                      placeholder="选择指令"
                      style="width: 100%"
                    >
                      <el-option
                        v-for="cmd in savedCommands"
                        :key="cmd.id"
                        :label="`${cmd.name} (${cmd.command})`"
                        :value="cmd.id"
                      />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="4">
                  <el-form-item label="延迟(ms)" size="small">
                    <el-input-number
                      v-model="step.delay_ms"
                      :min="0"
                      :max="60000"
                      :step="100"
                      style="width: 100%"
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="4">
                  <el-form-item label="重试次数" size="small">
                    <el-input-number
                      v-model="step.retry_count"
                      :min="0"
                      :max="10"
                      style="width: 100%"
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="4">
                  <el-form-item label="超时(ms)" size="small">
                    <el-input-number
                      v-model="step.timeout_ms"
                      :min="100"
                      :max="60000"
                      :step="100"
                      style="width: 100%"
                    />
                  </el-form-item>
                </el-col>
              </el-row>
            </div>
            <el-button
              type="dashed"
              @click="addWorkflowStep(false)"
              style="width: 100%; margin-top: 16px;"
            >
              <el-icon><Plus /></el-icon>
              添加步骤
            </el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showCreateWorkflow = false">取消</el-button>
          <el-button type="primary" @click="createWorkflow">创建</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 编辑工作流对话框 -->
    <el-dialog
      v-model="showEditWorkflow"
      title="编辑流水作业"
      width="800px"
    >
      <el-form :model="editWorkflow" label-width="80px">
        <el-form-item label="名称" required>
          <el-input
            v-model="editWorkflow.name"
            placeholder="请输入工作流名称"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="editWorkflow.description"
            type="textarea"
            placeholder="请输入工作流描述（可选）"
            maxlength="500"
            show-word-limit
            :rows="2"
          />
        </el-form-item>
        <el-form-item label="步骤">
          <div class="workflow-steps">
            <div
              v-for="(step, index) in editWorkflow.steps"
              :key="index"
              class="workflow-step"
            >
              <div class="step-header">
                <span class="step-number">步骤 {{ step.step_order }}</span>
                <div class="step-actions">
                  <el-button
                    size="small"
                    @click="moveStepUp(index, true)"
                    :disabled="index === 0"
                    title="上移"
                  >
                    <el-icon><ArrowUp /></el-icon>
                  </el-button>
                  <el-button
                    size="small"
                    @click="moveStepDown(index, true)"
                    :disabled="index === editWorkflow.steps.length - 1"
                    title="下移"
                  >
                    <el-icon><ArrowDown /></el-icon>
                  </el-button>
                  <el-button
                    size="small"
                    type="danger"
                    @click="removeWorkflowStep(index, true)"
                    title="删除"
                  >
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
              </div>
              <el-row :gutter="16">
                <el-col :span="12">
                  <el-form-item label="指令" size="small">
                    <el-select
                      v-model="step.command_id"
                      placeholder="选择指令"
                      style="width: 100%"
                    >
                      <el-option
                        v-for="cmd in savedCommands"
                        :key="cmd.id"
                        :label="`${cmd.name} (${cmd.command})`"
                        :value="cmd.id"
                      />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="4">
                  <el-form-item label="延迟(ms)" size="small">
                    <el-input-number
                      v-model="step.delay_ms"
                      :min="0"
                      :max="60000"
                      :step="100"
                      style="width: 100%"
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="4">
                  <el-form-item label="重试次数" size="small">
                    <el-input-number
                      v-model="step.retry_count"
                      :min="0"
                      :max="10"
                      style="width: 100%"
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="4">
                  <el-form-item label="超时(ms)" size="small">
                    <el-input-number
                      v-model="step.timeout_ms"
                      :min="100"
                      :max="60000"
                      :step="100"
                      style="width: 100%"
                    />
                  </el-form-item>
                </el-col>
              </el-row>
            </div>
            <el-button
              type="dashed"
              @click="addWorkflowStep(true)"
              style="width: 100%; margin-top: 16px;"
            >
              <el-icon><Plus /></el-icon>
              添加步骤
            </el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showEditWorkflow = false">取消</el-button>
          <el-button type="primary" @click="updateWorkflowData">保存</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 执行状态对话框 -->
    <el-dialog
      v-model="showExecutionStatus"
      title="工作流执行状态"
      width="800px"
      :before-close="closeExecutionStatus"
    >
      <div v-if="currentExecution" class="execution-status">
        <div class="execution-header">
          <h3>{{ currentExecution.workflow_name }}</h3>
          <el-tag 
            :type="currentExecution.status === 'completed' ? 'success' : 
                   currentExecution.status === 'failed' ? 'danger' :
                   currentExecution.status === 'running' ? 'warning' : 'info'"
          >
            {{ currentExecution.status === 'pending' ? '准备中' :
               currentExecution.status === 'running' ? '执行中' :
               currentExecution.status === 'completed' ? '已完成' :
               currentExecution.status === 'failed' ? '执行失败' :
               currentExecution.status === 'cancelled' ? '已取消' : currentExecution.status }}
          </el-tag>
        </div>
        
        <div class="execution-progress">
          <el-progress
            :percentage="getExecutionProgress()"
            :status="currentExecution.status === 'completed' ? 'success' : 
                     currentExecution.status === 'failed' ? 'exception' : undefined"
          />
          <div class="progress-text">
            {{ currentExecution.completed_steps }} / {{ currentExecution.total_steps }} 步骤已完成
          </div>
        </div>

        <div v-if="currentExecution.error_message" class="error-message">
          <el-alert
            :title="currentExecution.error_message"
            type="error"
            :closable="false"
          />
        </div>

        <div class="execution-steps">
          <h4>执行详情</h4>
          <div
            v-for="step in currentExecution.steps"
            :key="step.id"
            class="execution-step"
          >
            <div class="step-info">
              <el-tag
                size="small"
                :type="getStepStatusColor(step.status)"
              >
                步骤 {{ step.step_order }}
              </el-tag>
              <span class="step-command">{{ step.command_name }}: {{ step.command_content }}</span>
            </div>
            <div v-if="step.response_received" class="step-response">
              <strong>响应:</strong> {{ step.response_received }}
            </div>
            <div v-if="step.error_message" class="step-error">
              <strong>错误:</strong> {{ step.error_message }}
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button
            v-if="currentExecution && ['pending', 'running'].includes(currentExecution.status)"
            type="danger"
            @click="cancelWorkflowExecution"
          >
            取消执行
          </el-button>
          <el-button @click="closeExecutionStatus">关闭</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown, ArrowUp, Delete, Download, Edit, Operation, Plus, VideoPlay } from '@element-plus/icons-vue'
import { useConnectionStore } from '@/stores/connection'
import { useCommunicationStore } from '@/stores/communication'
import { useSessionStore } from '@/stores/session'
import type { CommunicationLog } from '@/stores/communication'
import * as commandsAPI from '@/api/commands'
import * as workflowsAPI from '@/api/workflows'
import type { BatchWorkflow, WorkflowExecutionStatus } from '@/api/workflows'

const router = useRouter()
const connectionStore = useConnectionStore()
const communicationStore = useCommunicationStore()
const sessionStore = useSessionStore()

// 状态
const commandLoading = ref(false)
const rawLoading = ref(false)
const batchLoading = ref(false)
const showHistory = ref(false)
const showBatchSend = ref(false)
const showAddCommand = ref(false)
const showEditCommand = ref(false)
const showWorkflowManager = ref(false)
const showCreateWorkflow = ref(false)
const showEditWorkflow = ref(false)
const showExecutionStatus = ref(false)
const commandHistory = ref<string[]>([])
const batchCommands = ref('')
const batchDelay = ref(1000)

// 表单数据
const commandForm = reactive({
  command: '',
  autoAddCRLF: true,
  lineEnding: '\r\n',
})

// 新指令表单
const newCommand = reactive({
  name: '',
  command: '',
  description: '',
  expected_response: '',
})

// 编辑指令表单
const editCommand = reactive({
  id: '',
  name: '',
  command: '',
  description: '',
  expected_response: '',
})

const rawForm = reactive({
  data: '',
})

// 保存的指令接口
interface SavedCommand {
  id: string
  name: string
  command: string
  description: string
  expected_response: string
  createdAt: number
}

// 保存的指令列表
const savedCommands = ref<SavedCommand[]>([])

// 工作流相关数据
const workflows = ref<BatchWorkflow[]>([])
const currentExecution = ref<WorkflowExecutionStatus | null>(null)
const executionTimer = ref<number | null>(null)

// 新建工作流表单
const newWorkflow = reactive({
  name: '',
  description: '',
  steps: [] as Array<{
    command_id: string
    step_order: number
    delay_ms: number
    retry_count: number
    timeout_ms: number
  }>
})

// 编辑工作流表单
const editWorkflow = reactive({
  id: '',
  name: '',
  description: '',
  steps: [] as Array<{
    command_id: string
    step_order: number
    delay_ms: number
    retry_count: number
    timeout_ms: number
  }>
})

// 常用指令现在完全由用户自定义

// 方法
const formatCommand = (command: string) => {
  // 前端完全控制指令格式
  let formattedCommand = command.trim()
  
  // 首先处理转义字符：将文本形式的 \r\n 转换为真实控制字符
  formattedCommand = formattedCommand
    .replace(/\\r\\n/g, '\r\n')  // \r\n -> 真实的CRLF
    .replace(/\\r/g, '\r')       // \r -> 真实的CR  
    .replace(/\\n/g, '\n')       // \n -> 真实的LF
  
  // 如果启用自动添加终止符且指令中没有真实的控制字符
  const hasRealLineEnding = formattedCommand.includes('\r') || formattedCommand.includes('\n')
  if (commandForm.autoAddCRLF && commandForm.lineEnding && !hasRealLineEnding) {
    formattedCommand += commandForm.lineEnding
  }
  
  return formattedCommand
}



const addToHistory = (command: string) => {
  const cleanCommand = command.replace(/\r\n|\r|\n/g, '')
  if (cleanCommand && !commandHistory.value.includes(cleanCommand)) {
    commandHistory.value.unshift(cleanCommand)
    // 限制历史记录数量
    if (commandHistory.value.length > 20) {
      commandHistory.value = commandHistory.value.slice(0, 20)
    }
  }
}

const clearHistory = () => {
  commandHistory.value = []
}

const sendCommand = async () => {
  if (!commandForm.command.trim()) {
    ElMessage.error('请输入指令内容')
    return
  }
  
  commandLoading.value = true
  try {
    const formattedCommand = formatCommand(commandForm.command)
    await communicationStore.sendATCommand(formattedCommand)
    ElMessage.success('指令发送成功')
    // 添加到历史记录
    addToHistory(commandForm.command)
  } catch (error) {
    console.error('Send command error:', error)
  } finally {
    commandLoading.value = false
  }
}

const clearCommandInput = () => {
  commandForm.command = ''
}

const sendQuickCommand = async (command: string) => {
  // 应用用户设置的控制选项（自动添加终止符等）
  commandLoading.value = true
  try {
    const formattedCommand = formatCommand(command)
    await communicationStore.sendATCommand(formattedCommand)
    ElMessage.success('指令发送成功')
    // 同时更新输入框显示（显示原始指令，不显示终止符）
    const cleanCommand = command.replace(/\r\n|\r|\n/g, '')
    commandForm.command = cleanCommand
    // 添加到历史记录
    addToHistory(cleanCommand)
  } catch (error) {
    console.error('Send command error:', error)
  } finally {
    commandLoading.value = false
  }
}

const sendBatchCommands = async () => {
  if (!batchCommands.value.trim()) {
    ElMessage.error('请输入要批量发送的指令')
    return
  }
  
  const commands = batchCommands.value
    .split('\n')
    .map(cmd => cmd.trim())
    .filter(cmd => cmd.length > 0)
  
  if (commands.length === 0) {
    ElMessage.error('没有有效的指令')
    return
  }
  
  batchLoading.value = true
  
  try {
    for (let i = 0; i < commands.length; i++) {
      const command = commands[i]
      const formattedCommand = formatCommand(command)
      
      ElMessage.info(`发送第${i + 1}/${commands.length}个指令: ${command}`)
      
      try {
        await communicationStore.sendATCommand(formattedCommand)
        addToHistory(command)
      } catch (error) {
        console.error(`Command ${i + 1} failed:`, error)
        ElMessage.error(`第${i + 1}个指令发送失败: ${command}`)
      }
      
      // 如果不是最后一个指令，等待指定间隔
      if (i < commands.length - 1) {
        await new Promise(resolve => setTimeout(resolve, batchDelay.value))
      }
    }
    
    ElMessage.success(`批量发送完成，共发送${commands.length}个指令`)
  } catch (error) {
    console.error('Batch send error:', error)
    ElMessage.error('批量发送过程中出现错误')
  } finally {
    batchLoading.value = false
  }
}

// API相关方法
const loadSavedCommands = async () => {
  try {
    const response = await commandsAPI.getAllCommands()
    // 转换API返回的数据格式以兼容现有组件
    savedCommands.value = response.commands.map(cmd => ({
      id: cmd.id,
      name: cmd.name,
      command: cmd.command,
      description: cmd.description,
      expected_response: cmd.expected_response,
      createdAt: cmd.created_at // API返回毫秒时间戳
    }))
  } catch (error) {
    console.error('Failed to load saved commands:', error)
    ElMessage.error('加载常用指令失败')
    // 出错时也初始化为空数组
    savedCommands.value = []
  }
}

const addNewCommand = async () => {
  if (!newCommand.name.trim() || !newCommand.command.trim()) {
    ElMessage.error('请填写指令名称和内容')
    return
  }
  
  try {
    const createRequest: commandsAPI.CreateCommandRequest = {
      name: newCommand.name.trim(),
      command: newCommand.command.trim(),
      description: newCommand.description.trim(),
      expected_response: newCommand.expected_response.trim()
    }
    
    const createdCommand = await commandsAPI.createCommand(createRequest)
    
    // 转换为前端格式并添加到列表开头
    const command: SavedCommand = {
      id: createdCommand.id,
      name: createdCommand.name,
      command: createdCommand.command,
      description: createdCommand.description,
      expected_response: createdCommand.expected_response,
      createdAt: createdCommand.created_at
    }
    
    savedCommands.value.unshift(command)
    
    // 清空表单并关闭弹窗
    newCommand.name = ''
    newCommand.command = ''
    newCommand.description = ''
    newCommand.expected_response = ''
    showAddCommand.value = false
    
    ElMessage.success('常用指令添加成功')
  } catch (error: any) {
    console.error('Failed to create command:', error)
    ElMessage.error(error.message || '创建指令失败')
  }
}

const handleCloseAddCommand = () => {
  // 清空表单
  newCommand.name = ''
  newCommand.command = ''
  newCommand.description = ''
  newCommand.expected_response = ''
  showAddCommand.value = false
}

const deleteCommand = async (cmd: SavedCommand) => {
  try {
    await ElMessageBox.confirm(`确定要删除指令 "${cmd.name}" 吗？`, '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    
    await commandsAPI.deleteCommand(cmd.id)
    
    // 从本地列表中移除
    const index = savedCommands.value.findIndex(c => c.id === cmd.id)
    if (index !== -1) {
      savedCommands.value.splice(index, 1)
    }
    
    ElMessage.success('指令删除成功')
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('Failed to delete command:', error)
      ElMessage.error(error.message || '删除指令失败')
    }
  }
}

const openEditCommand = (cmd: SavedCommand) => {
  // 填充编辑表单
  editCommand.id = cmd.id
  editCommand.name = cmd.name
  editCommand.command = cmd.command
  editCommand.description = cmd.description
  editCommand.expected_response = cmd.expected_response
  showEditCommand.value = true
}

const updateCommand = async () => {
  if (!editCommand.name.trim() || !editCommand.command.trim()) {
    ElMessage.error('请填写指令名称和内容')
    return
  }

  try {
    const updateRequest: commandsAPI.UpdateCommandRequest = {
      name: editCommand.name.trim(),
      command: editCommand.command.trim(),
      description: editCommand.description.trim(),
      expected_response: editCommand.expected_response.trim()
    }

    const updatedCommand = await commandsAPI.updateCommand(editCommand.id, updateRequest)

    // 更新本地列表中的指令
    const index = savedCommands.value.findIndex(c => c.id === editCommand.id)
    if (index !== -1) {
      savedCommands.value[index] = {
        id: updatedCommand.id,
        name: updatedCommand.name,
        command: updatedCommand.command,
        description: updatedCommand.description,
        expected_response: updatedCommand.expected_response,
        createdAt: updatedCommand.created_at
      }
    }

    // 清空表单并关闭弹窗
    editCommand.id = ''
    editCommand.name = ''
    editCommand.command = ''
    editCommand.description = ''
    editCommand.expected_response = ''
    showEditCommand.value = false

    ElMessage.success('常用指令修改成功')
  } catch (error: any) {
    console.error('Failed to update command:', error)
    ElMessage.error(error.message || '修改指令失败')
  }
}

const handleCloseEditCommand = () => {
  // 清空表单
  editCommand.id = ''
  editCommand.name = ''
  editCommand.command = ''
  editCommand.description = ''
  editCommand.expected_response = ''
  showEditCommand.value = false
}

const handleCommandRightClick = (_event: MouseEvent, cmd: SavedCommand) => {
  // 右键点击指令时，显示上下文菜单或执行特定操作
  // TODO: 实现右键菜单功能，可以快速编辑或删除指令
  console.log('Right click on command:', cmd.name)
}

const sendRawData = async () => {
  if (!rawForm.data.trim()) {
    ElMessage.error('请输入十六进制数据')
    return
  }
  
  // 验证16进制格式
  const hexPattern = /^[0-9A-Fa-f\s]+$/
  const cleanData = rawForm.data.replace(/\s+/g, '')
  
  if (!hexPattern.test(rawForm.data)) {
    ElMessage.error('请输入有效的十六进制数据（只能包含0-9, A-F字符和空格）')
    return
  }
  
  if (cleanData.length % 2 !== 0) {
    ElMessage.error('十六进制数据长度必须为偶数（每个字节需要2个字符）')
    return
  }
  
  rawLoading.value = true
  try {
    await communicationStore.sendRawData(rawForm.data)
    ElMessage.success('原始数据发送成功')
  } catch (error) {
    console.error('Send raw data error:', error)
  } finally {
    rawLoading.value = false
  }
}

// 格式化16进制输入
const formatHexInput = (value: string) => {
  // 移除非16进制字符，保留空格
  const cleaned = value.replace(/[^0-9A-Fa-f\s]/g, '')
  rawForm.data = cleaned.toUpperCase()
}

const clearLogs = async () => {
  try {
    await ElMessageBox.confirm('确定要清空所有通信日志吗？', '确认操作', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    communicationStore.clearLogs()
    ElMessage.success('日志已清空')
  } catch {
    // 用户取消
  }
}

const exportLogs = () => {
  try {
    const logs = communicationStore.logs.map(log => ({
      时间: new Date(log.timestamp).toLocaleString(),
      方向: log.direction === 'sent' ? '发送' : '接收',
      描述: log.description,
      数据: log.data,
      状态: log.success ? '成功' : '失败'
    }))
    
    // 构建CSV内容
    const csvContent = [
      ['时间', '方向', '描述', '数据', '状态'].join(','),
      ...logs.map(log => [
        `"${log.时间}"`,
        `"${log.方向}"`, 
        `"${log.描述}"`,
        `"${log.数据?.replace(/"/g, '""') || ''}"`,  // 处理数据中的引号
        `"${log.状态}"`
      ].join(','))
    ].join('\n')
    
    // 添加 BOM 以确保中文正确显示
    const BOM = '\uFEFF'
    const csvWithBOM = BOM + csvContent
    
    // 创建 Blob 对象
    const blob = new Blob([csvWithBOM], { 
      type: 'text/csv;charset=utf-8;' 
    })
    
    // 下载文件
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', `通信日志_${new Date().toISOString().slice(0, 10)}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    // 清理URL对象
    URL.revokeObjectURL(url)
    
    ElMessage.success('日志导出成功')
  } catch (error) {
    console.error('Export logs error:', error)
    ElMessage.error('日志导出失败')
  }
}

const getLogIcon = (log: CommunicationLog) => {
  if (log.direction === 'sent') {
    return 'Top'
  } else {
    return log.success ? 'Bottom' : 'CloseBold'
  }
}

const formatTime = (timestamp: number) => {
  return new Date(timestamp).toLocaleTimeString()
}

// 工作流相关方法
const loadWorkflows = async () => {
  try {
    const response = await workflowsAPI.getAllWorkflows()
    workflows.value = response.workflows
  } catch (error: any) {
    console.error('Failed to load workflows:', error)
    ElMessage.error('加载工作流失败')
  }
}

const openCreateWorkflow = () => {
  // 重置表单
  newWorkflow.name = ''
  newWorkflow.description = ''
  newWorkflow.steps = []
  showCreateWorkflow.value = true
}

const openEditWorkflow = (workflow: BatchWorkflow) => {
  editWorkflow.id = workflow.id
  editWorkflow.name = workflow.name
  editWorkflow.description = workflow.description
  editWorkflow.steps = workflow.steps.map(step => ({
    command_id: step.command_id,
    step_order: step.step_order,
    delay_ms: step.delay_ms,
    retry_count: step.retry_count,
    timeout_ms: step.timeout_ms
  }))
  showEditWorkflow.value = true
}

const addWorkflowStep = (isEdit = false) => {
  const steps = isEdit ? editWorkflow.steps : newWorkflow.steps
  const newOrder = steps.length > 0 ? Math.max(...steps.map(s => s.step_order)) + 1 : 1
  
  steps.push({
    command_id: '',
    step_order: newOrder,
    delay_ms: 1000,
    retry_count: 0,
    timeout_ms: 5000
  })
}

const removeWorkflowStep = (index: number, isEdit = false) => {
  const steps = isEdit ? editWorkflow.steps : newWorkflow.steps
  steps.splice(index, 1)
  // 重新排序
  steps.forEach((step, idx) => {
    step.step_order = idx + 1
  })
}

const moveStepUp = (index: number, isEdit = false) => {
  const steps = isEdit ? editWorkflow.steps : newWorkflow.steps
  if (index > 0) {
    [steps[index], steps[index - 1]] = [steps[index - 1], steps[index]]
    // 重新排序
    steps.forEach((step, idx) => {
      step.step_order = idx + 1
    })
  }
}

const moveStepDown = (index: number, isEdit = false) => {
  const steps = isEdit ? editWorkflow.steps : newWorkflow.steps
  if (index < steps.length - 1) {
    [steps[index], steps[index + 1]] = [steps[index + 1], steps[index]]
    // 重新排序
    steps.forEach((step, idx) => {
      step.step_order = idx + 1
    })
  }
}

const createWorkflow = async () => {
  try {
    if (!newWorkflow.name.trim()) {
      ElMessage.error('请输入工作流名称')
      return
    }
    
    if (newWorkflow.steps.length === 0) {
      ElMessage.error('请添加至少一个步骤')
      return
    }
    
    // 验证所有步骤都有选择指令
    for (const step of newWorkflow.steps) {
      if (!step.command_id) {
        ElMessage.error(`步骤 ${step.step_order} 未选择指令`)
        return
      }
    }
    
    const request = {
      name: newWorkflow.name.trim(),
      description: newWorkflow.description.trim(),
      steps: newWorkflow.steps
    }
    
    await workflowsAPI.createWorkflow(request)
    await loadWorkflows()
    
    showCreateWorkflow.value = false
    ElMessage.success('工作流创建成功')
  } catch (error: any) {
    console.error('Failed to create workflow:', error)
    ElMessage.error(error.message || '创建工作流失败')
  }
}

const updateWorkflowData = async () => {
  try {
    if (!editWorkflow.name.trim()) {
      ElMessage.error('请输入工作流名称')
      return
    }
    
    if (editWorkflow.steps.length === 0) {
      ElMessage.error('请添加至少一个步骤')
      return
    }
    
    // 验证所有步骤都有选择指令
    for (const step of editWorkflow.steps) {
      if (!step.command_id) {
        ElMessage.error(`步骤 ${step.step_order} 未选择指令`)
        return
      }
    }
    
    const request = {
      name: editWorkflow.name.trim(),
      description: editWorkflow.description.trim(),
      steps: editWorkflow.steps
    }
    
    await workflowsAPI.updateWorkflow(editWorkflow.id, request)
    await loadWorkflows()
    
    showEditWorkflow.value = false
    ElMessage.success('工作流更新成功')
  } catch (error: any) {
    console.error('Failed to update workflow:', error)
    ElMessage.error(error.message || '更新工作流失败')
  }
}

const deleteWorkflow = async (workflow: BatchWorkflow) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除工作流 "${workflow.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    await workflowsAPI.deleteWorkflow(workflow.id)
    await loadWorkflows()
    
    ElMessage.success('工作流删除成功')
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('Failed to delete workflow:', error)
      ElMessage.error(error.message || '删除工作流失败')
    }
  }
}

const executeWorkflow = async (workflow: BatchWorkflow) => {
  try {
    if (!connectionStore.isConnected) {
      ElMessage.error('请先连接串口')
      return
    }
    
    const response = await workflowsAPI.executeWorkflow({
      workflow_id: workflow.id
    })
    
    currentExecution.value = {
      id: response.execution_id,
      workflow_id: response.workflow_id,
      workflow_name: response.workflow_name,
      status: response.status,
      started_at: undefined,
      finished_at: undefined,
      total_steps: response.total_steps,
      completed_steps: 0,
      error_message: undefined,
      created_at: Date.now(),
      steps: []
    }
    
    showExecutionStatus.value = true
    
    // 开始轮询执行状态
    startExecutionPolling(response.execution_id)
    
    ElMessage.success('工作流执行已启动')
  } catch (error: any) {
    console.error('Failed to execute workflow:', error)
    ElMessage.error(error.message || '执行工作流失败')
  }
}

const startExecutionPolling = (executionId: string) => {
  if (executionTimer.value) {
    clearInterval(executionTimer.value)
  }
  
  executionTimer.value = setInterval(async () => {
    try {
      const status = await workflowsAPI.getExecutionStatus(executionId)
      currentExecution.value = status
      
      // 如果执行完成或失败，停止轮询
      if (['completed', 'failed', 'cancelled'].includes(status.status)) {
        if (executionTimer.value) {
          clearInterval(executionTimer.value)
          executionTimer.value = null
        }
      }
    } catch (error) {
      console.error('Failed to get execution status:', error)
      // 继续轮询，可能是临时网络问题
    }
  }, 1000)
}

const cancelWorkflowExecution = async () => {
  try {
    if (!currentExecution.value) return
    
    await workflowsAPI.cancelExecution(currentExecution.value.id)
    
    if (executionTimer.value) {
      clearInterval(executionTimer.value)
      executionTimer.value = null
    }
    
    ElMessage.success('工作流执行已取消')
  } catch (error: any) {
    console.error('Failed to cancel execution:', error)
    ElMessage.error(error.message || '取消执行失败')
  }
}

const closeExecutionStatus = () => {
  showExecutionStatus.value = false
  currentExecution.value = null
  
  if (executionTimer.value) {
    clearInterval(executionTimer.value)
    executionTimer.value = null
  }
}

const getStepStatusColor = (status: string) => {
  switch (status) {
    case 'completed': return 'success'
    case 'failed': return 'danger'
    case 'running': return 'warning'
    case 'pending': return 'info'
    default: return 'info'
  }
}

const getExecutionProgress = () => {
  if (!currentExecution.value) return 0
  return (currentExecution.value.completed_steps / currentExecution.value.total_steps) * 100
}

// 生命周期
onMounted(async () => {
  // 初始化会话管理
  await sessionStore.init()
  
  // 检查登录状态
  if (!sessionStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    router.push('/serial-config')
    return
  }
  
  if (!connectionStore.isConnected) {
    ElMessage.warning('请先连接串口')
    router.push('/serial-config')
    return
  }
  
  // 加载保存的指令
  await loadSavedCommands()
  
  // 加载工作流
  await loadWorkflows()
  
  // 初始化WebSocket连接
  try {
    await communicationStore.initializeWebSocket()
  } catch (error) {
    console.error('WebSocket初始化失败:', error)
    ElMessage.error('实时连接初始化失败')
  }
})


</script>

<style scoped>
.page-container {
  padding: 20px;
  background: #ffffff;
  height: calc(100vh - 70px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.status-bar {
  background: #ffffff;
  border: 1px solid #e0e6ed;
  border-radius: 16px;
  padding: 20px 28px;
  margin-bottom: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.status-info {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.connection-badge {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  border-radius: 12px;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.connection-badge:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.connection-badge.connected {
  background: #f0f9f0;
  color: #2e7d32;
  border: 2px solid #4caf50;
}

.connection-badge.disconnected {
  background: #fef7f7;
  color: #c62828;
  border: 2px solid #f44336;
}

.realtime-badge {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  border-radius: 12px;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.realtime-badge:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.realtime-badge.connected {
  background: #f3f5ff;
  color: #1976d2;
  border: 2px solid #2196f3;
}

.realtime-badge.disconnected {
  background: #fffbf0;
  color: #f57c00;
  border: 2px solid #ff9800;
}

.connected-icon {
  color: #52c41a;
  font-size: 12px;
}

.disconnected-icon {
  color: #faad14;
  font-size: 12px;
}

.status-icon {
  font-size: 18px;
}

.status-text {
  font-weight: 600;
}

.main-row {
  flex: 1;
  height: 100%;
  margin: 0 -10px;
}

.main-row .el-col {
  height: 100%;
  padding: 0 10px;
}

.command-card {
  height: 100%;
  background: #ffffff;
  border: 1px solid #e0e6ed;
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
}

.command-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.18);
}

.log-card {
  height: 100%;
  background: #ffffff;
  border: 1px solid #e0e6ed;
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
}

.logs-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.18);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #374151;
}

.title-icon {
  font-size: 20px;
  color: #667eea;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.form-section {
  flex-shrink: 0;
  margin-bottom: 20px;
}

.commands-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.quick-commands {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 16px;
  min-height: 40px;
  flex: 1;
  overflow-y: auto;
  padding-right: 8px;
}

.quick-commands::-webkit-scrollbar {
  width: 6px;
}

.quick-commands::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 3px;
}

.quick-commands::-webkit-scrollbar-thumb {
  background: #bdbdbd;
  border-radius: 3px;
}

.quick-commands::-webkit-scrollbar-thumb:hover {
  background: #9e9e9e;
}

.no-commands-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 20px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 8px;
  border: 2px dashed #e2e8f0;
}

.log-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, 0.05);
  min-height: 0;
}

.log-item {
  margin-bottom: 16px;
  padding: 16px;
  border-radius: 12px;
  border-left: 4px solid;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease;
}

.log-item:hover {
  transform: translateX(4px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.log-item.sent {
  background: linear-gradient(135deg, rgba(64, 158, 255, 0.1) 0%, rgba(64, 158, 255, 0.05) 100%);
  border-left-color: #409eff;
  border-left-width: 4px;
}

.log-item.received.success {
  background: linear-gradient(135deg, rgba(103, 194, 58, 0.1) 0%, rgba(103, 194, 58, 0.05) 100%);
  border-left-color: #67c23a;
  border-left-width: 4px;
}

.log-item.received.error {
  background: linear-gradient(135deg, rgba(245, 108, 108, 0.1) 0%, rgba(245, 108, 108, 0.05) 100%);
  border-left-color: #f56c6c;
  border-left-width: 4px;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  font-weight: 500;
}

.log-timestamp {
  font-size: 12px;
  opacity: 0.7;
}

.log-data {
  font-family: 'Fira Code', 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 13px;
  background: linear-gradient(135deg, rgba(0, 0, 0, 0.03) 0%, rgba(0, 0, 0, 0.06) 100%);
  padding: 12px;
  border-radius: 8px;
  word-break: break-all;
  border: 1px solid rgba(0, 0, 0, 0.06);
  line-height: 1.5;
}

.empty-logs {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.el-divider {
  margin: 24px 0 16px 0;
}

.command-controls {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.history-commands {
  max-height: 120px;
  overflow-y: auto;
  padding: 8px;
  background-color: var(--el-bg-color-page);
  border-radius: 4px;
  border: 1px solid var(--el-border-color-light);
}


/* Element Plus 组件样式覆盖 */
:deep(.el-card) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

:deep(.el-card__header) {
  background: #f8f9fa;
  border-bottom: 1px solid #e0e6ed;
  font-weight: 600;
  font-size: 16px;
  color: #2d3748;
  flex-shrink: 0;
}

:deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 20px;
}

:deep(.el-button--primary) {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  border: none;
  border-radius: 12px;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.3);
  color: #ffffff !important;
}

:deep(.el-button--primary:hover) {
  background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.4);
  color: #ffffff !important;
}

:deep(.el-button--danger),
:deep(.clear-logs-btn) {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  border: none;
  border-radius: 12px;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: 0 4px 16px rgba(239, 68, 68, 0.3);
  color: #ffffff !important;
}

:deep(.el-button--danger:hover),
:deep(.clear-logs-btn:hover) {
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(239, 68, 68, 0.4);
  color: #ffffff !important;
}

:deep(.el-input__wrapper) {
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  border: 1px solid #d0d7de;
  transition: all 0.3s ease;
}

:deep(.el-input__wrapper:hover) {
  border-color: #1976d2;
  box-shadow: 0 2px 8px rgba(25, 118, 210, 0.15);
}

:deep(.el-input__wrapper.is-focus) {
  border-color: #1976d2;
  box-shadow: 0 0 0 3px rgba(25, 118, 210, 0.1);
}

:deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background: #1976d2;
  border-color: #1976d2;
}

/* 确保所有按钮文字颜色清晰 */
:deep(.el-button) {
  font-weight: 600;
}

/* 只对特定按钮应用flex布局 */
:deep(.el-input-group__append .el-button),
:deep(.header-actions .el-button),
:deep(.clear-logs-btn) {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

:deep(.el-button--primary),
:deep(.el-button--danger),
:deep(.el-button--success),
:deep(.el-button--warning),
:deep(.el-button--info) {
  color: #ffffff !important;
}

:deep(.el-button--primary:hover),
:deep(.el-button--danger:hover),
:deep(.el-button--success:hover),
:deep(.el-button--warning:hover),
:deep(.el-button--info:hover) {
  color: #ffffff !important;
}

:deep(.el-button--primary:active),
:deep(.el-button--danger:active),
:deep(.el-button--success:active),
:deep(.el-button--warning:active),
:deep(.el-button--info:active) {
  color: #ffffff !important;
}

/* 输入框追加按钮特殊处理 */
:deep(.el-input-group__append .el-button) {
  color: #ffffff !important;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 0 16px;
  min-height: 32px;
}

:deep(.el-input-group__append .el-button:hover) {
  color: #ffffff !important;
}

:deep(.el-input-group__append .el-button .el-icon) {
  display: flex;
  align-items: center;
  justify-content: center;
}

:deep(.el-dialog) {
  border-radius: 16px;
  overflow: hidden;
  backdrop-filter: blur(20px);
  background: rgba(255, 255, 255, 0.95);
}

:deep(.el-dialog__header) {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
  border-bottom: 2px solid rgba(102, 126, 234, 0.1);
}

/* 通信日志区域美化 */
.logs-container {
  height: 500px;
  overflow-y: auto;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 16px;
  margin-top: 20px;
  border: 1px solid #e9ecef;
}

.logs-container::-webkit-scrollbar {
  width: 8px;
}

.logs-container::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 4px;
}

.logs-container::-webkit-scrollbar-thumb {
  background: #bdbdbd;
  border-radius: 4px;
}

.logs-container::-webkit-scrollbar-thumb:hover {
  background: #9e9e9e;
}

.log-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 16px 20px;
  margin-bottom: 12px;
  border-radius: 16px;
  background: #ffffff;
  border: 1px solid #e0e6ed;
  border-left: 4px solid transparent;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.log-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.log-item.sent {
  border-left-color: #1976d2;
  background: #f8fbff;
}

.log-item.received {
  border-left-color: #2e7d32;
  background: #f1f8e9;
}

.log-item.failed {
  border-left-color: #d32f2f;
  background: #fef7f7;
}

.log-direction {
  font-size: 11px;
  padding: 6px 12px;
  border-radius: 20px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  min-width: 50px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.log-direction.sent {
  background: #1976d2;
  color: white;
}

.log-direction.received {
  background: #2e7d32;
  color: white;
}

.log-direction.failed {
  background: #d32f2f;
  color: white;
}

.log-data {
  font-family: 'SF Mono', 'Monaco', 'Cascadia Code', 'Roboto Mono', monospace;
  font-size: 13px;
  color: #2d3748;
  word-break: break-all;
  background: rgba(0, 0, 0, 0.03);
  padding: 12px 16px;
  border-radius: 10px;
  white-space: pre-wrap;
  border: 1px solid rgba(0, 0, 0, 0.06);
  line-height: 1.4;
}

/* 常用指令区域美化 */
.quick-commands {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 240px;
  overflow-y: auto;
  padding-right: 8px;
}

.quick-commands::-webkit-scrollbar {
  width: 6px;
}

.quick-commands::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 3px;
}

.quick-commands::-webkit-scrollbar-thumb {
  background: #bdbdbd;
  border-radius: 3px;
}

.quick-commands::-webkit-scrollbar-thumb:hover {
  background: #9e9e9e;
}

.quick-command-btn {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  text-align: left;
  border: 2px solid #e5e7eb;
  border-radius: 16px;
  background: linear-gradient(135deg, #ffffff 0%, #f9fafb 100%);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  position: relative;
  overflow: hidden;
}

.command-content {
  flex: 1;
  min-width: 0;
}

.command-actions {
  display: flex;
  gap: 8px;
  margin-left: 12px;
}

.quick-command-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #3b82f6, #8b5cf6, #06b6d4);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.3s ease;
}

.quick-command-btn:hover {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-color: #3b82f6;
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(59, 130, 246, 0.25);
}

.quick-command-btn:hover::before {
  transform: scaleX(1);
}

.quick-command-btn:active {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.2);
}

.quick-command-btn.disabled {
  opacity: 0.6;
  cursor: not-allowed;
  pointer-events: none;
}

.quick-command-btn.disabled:hover {
  transform: none;
  background: linear-gradient(135deg, #ffffff 0%, #f9fafb 100%);
  border-color: #e5e7eb;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
}

.quick-command-name {
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 6px;
  font-size: 15px;
  letter-spacing: -0.01em;
}

.quick-command-text {
  font-size: 13px;
  color: #6b7280;
  font-family: 'SF Mono', 'Monaco', 'Cascadia Code', 'Roboto Mono', monospace;
  background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
  padding: 8px 12px;
  border-radius: 8px;
  display: inline-block;
  border: 1px solid #d1d5db;
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.05);
  transition: all 0.2s ease;
}

.quick-command-expected {
  font-size: 12px;
  color: #059669;
  font-family: 'SF Mono', 'Monaco', 'Cascadia Code', 'Roboto Mono', monospace;
  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
  padding: 6px 10px;
  border-radius: 6px;
  display: inline-block;
  border: 1px solid #a7f3d0;
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.03);
  margin-top: 6px;
  font-weight: 500;
}

.quick-command-btn:hover .quick-command-text {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  border-color: #93c5fd;
  color: #1e40af;
}

.edit-icon,
.delete-icon {
  opacity: 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  padding: 8px;
  border-radius: 12px;
  font-size: 16px;
  border: 1px solid transparent;
}

.edit-icon {
  color: #3b82f6;
  background: rgba(59, 130, 246, 0.08);
  border-color: rgba(59, 130, 246, 0.2);
}

.delete-icon {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.08);
  border-color: rgba(239, 68, 68, 0.2);
}

.quick-command-btn:hover .edit-icon,
.quick-command-btn:hover .delete-icon {
  opacity: 1;
}

.edit-icon:hover {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(37, 99, 235, 0.1) 100%);
  transform: scale(1.1);
  border-color: rgba(59, 130, 246, 0.3);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.25);
}

.delete-icon:hover {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(220, 38, 38, 0.1) 100%);
  transform: scale(1.1) rotate(5deg);
  border-color: rgba(239, 68, 68, 0.3);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.25);
}

.command-controls {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  padding: 8px 0;
}

.command-controls .el-button {
  font-size: 12px;
  padding: 4px 12px;
}

.no-logs {
  text-align: center;
  color: #a0aec0;
  padding: 60px 20px;
  font-size: 16px;
}

.no-logs .el-icon {
  font-size: 64px;
  margin-bottom: 20px;
  opacity: 0.3;
  background: linear-gradient(45deg, #94a3b8, #64748b);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* 常用指令区域布局 */
.command-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}

.command-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #374151;
}

.command-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.command-actions .el-button {
  font-size: 13px;
}

/* 修复小按钮的内部对齐 */
:deep(.el-button--small) {
  padding: 5px 11px;
  font-size: 12px;
  border-radius: 8px;
}

:deep(.el-button--small .el-icon) {
  margin-right: 4px;
}

/* 修复按钮组间距 */
.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

/* 工作流管理样式 */
.workflow-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.workflow-header h4 {
  margin: 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.workflow-list {
  max-height: 300px;
  overflow-y: auto;
}

.workflow-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  margin-bottom: 8px;
  background: #ffffff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.workflow-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.workflow-info {
  flex: 1;
  margin-right: 16px;
}

.workflow-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.workflow-description {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.workflow-steps-count {
  font-size: 12px;
  color: #67c23a;
}

.workflow-actions {
  display: flex;
  gap: 8px;
}

.no-workflows-hint {
  text-align: center;
  padding: 32px;
  color: #909399;
}

/* 工作流步骤样式 */
.workflow-steps {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  background: #fafafa;
}

.workflow-step {
  background: #ffffff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.workflow-step:last-child {
  margin-bottom: 0;
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.step-number {
  font-size: 14px;
  font-weight: 600;
  color: #409eff;
}

.step-actions {
  display: flex;
  gap: 4px;
}

/* 执行状态样式 */
.execution-status {
  padding: 16px 0;
}

.execution-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.execution-header h3 {
  margin: 0;
  color: #303133;
}

.execution-progress {
  margin-bottom: 24px;
}

.progress-text {
  text-align: center;
  margin-top: 8px;
  font-size: 14px;
  color: #606266;
}

.error-message {
  margin-bottom: 24px;
}

.execution-steps {
  max-height: 300px;
  overflow-y: auto;
}

.execution-steps h4 {
  margin: 0 0 16px 0;
  color: #303133;
  font-size: 16px;
}

.execution-step {
  padding: 12px;
  margin-bottom: 8px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #e4e7ed;
}

.step-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.step-command {
  font-size: 14px;
  color: #303133;
}

.step-response,
.step-error {
  font-size: 12px;
  margin-top: 4px;
  padding: 8px;
  border-radius: 4px;
}

.step-response {
  background: #f0f9ff;
  color: #1d4ed8;
}

.step-error {
  background: #fef2f2;
  color: #dc2626;
}


</style>