# 🔄 工作流自动化系统 - 完整实现

## 🎯 系统概述

**全新的工作流自动化系统**，完全替代之前的简单命令工具，提供：

✅ **步骤化流程定义** - 每个步骤定义串口输入和期望输出  
✅ **变量引用系统** - 支持 `${variable_name}` 格式动态变量  
✅ **WebSocket实时确认** - 通过WS协议发送确认框给用户  
✅ **串口通信集成** - 直接集成AT指令发送和回复验证  
✅ **可视化执行监控** - 实时显示工作流执行状态和进度  

---

## 🏗️ 系统架构

### 后端模块 (FastAPI)
```
backend/app/
├── schemas/workflow.py          # 工作流数据模型
├── services/workflow_engine.py  # 工作流执行引擎
└── api/v1/endpoints/workflow.py # REST API + WebSocket
```

### 前端模块 (Vue3 + Element Plus)
```
frontend/src/
├── api/workflow.ts              # API接口封装
├── stores/workflow.ts           # Pinia状态管理
└── views/WorkflowControl.vue    # 工作流控制页面
```

---

## 🔧 核心功能

### 📋 工作流步骤类型

| 类型 | 图标 | 说明 | 配置示例 |
|------|------|------|----------|
| **serial_send** | 📡 | 发送串口指令 | `AT+GMR` → 期望 `.*OK.*` |
| **user_confirm** | ❓ | 用户确认 | WebSocket弹窗确认 |
| **set_variable** | 🔧 | 设置变量 | `device_info = ${response}` |
| **delay** | ⏱️ | 延时等待 | 等待15秒 |
| **log** | 📝 | 记录日志 | 保存执行结果 |
| **condition** | 🔀 | 条件判断 | 根据结果分支执行 |

### 🔧 变量系统

**动态变量引用**:
```bash
# 串口指令中使用变量
"AT+CFUN?"                    # 固定指令
"设备 ${device_id} 查询"       # 变量引用
"AT+COPS=1,2,\"${network}\""  # 复杂参数

# 确认消息中使用变量  
"设备信息: ${device_info}\n\n是否继续测试？"

# 日志记录中使用变量
"测试完成 - 设备: ${device_model}, 操作员: ${operator}, 时间: ${current_time}"
```

**特殊变量**:
- `${current_time}` - 当前时间戳
- `${device_info}` - 从串口回复中提取
- `${user_input}` - 用户确认时的输入

### 🌐 WebSocket确认机制

**自动确认流程**:
1. 工作流执行到 `user_confirm` 步骤
2. 系统通过WebSocket发送确认请求到前端
3. 前端自动弹出确认对话框，显示详细信息
4. 用户确认后，结果通过WebSocket返回
5. 工作流根据确认结果继续或停止执行

**消息格式**:
```json
{
  "message_type": "user_confirmation_request",
  "execution_id": "exec_123",
  "step_id": "step_3",
  "data": {
    "message": "设备信息: ESP32_DevKit_V1\n\n是否继续测试？",
    "options": ["继续", "停止"],
    "step_name": "用户确认设备信息"
  }
}
```

---

## 📋 预定义工作流

### 1. 🧪 AT指令测试流程 (`at_command_test`)

**流程步骤**:
```
📡 发送AT → 📡 获取设备信息 → ❓ 用户确认 → 📝 记录结果
```

**详细步骤**:
1. **发送AT测试指令** - 验证设备连接
2. **获取设备信息** - `AT+GMR` 查询版本，保存到 `${device_info}`
3. **用户确认设备信息** - WebSocket弹窗显示设备信息
4. **记录测试结果** - 保存测试完成日志

### 2. 🔄 设备重启流程 (`device_restart`)

**流程步骤**:
```
📡 检查状态 → ❓ 确认重启 → 📡 执行重启 → ⏱️ 等待 → 📡 验证 → 📝 记录
```

**详细步骤**:
1. **检查设备状态** - `AT+CFUN?` 获取当前状态
2. **用户确认重启** - 显示状态和风险提示
3. **执行重启命令** - `AT+CFUN=1,1` 重启设备
4. **等待重启完成** - 延时15秒
5. **验证重启结果** - `AT` 测试连接
6. **记录重启结果** - 保存操作日志

---

## 🚀 使用方式

### 1. 主控制页面
```
访问: http://192.168.100.3:3000/workflow
功能: 完整的工作流管理和执行监控
```

### 2. 通信页面集成
```
位置: http://192.168.100.3:3000/communication
功能: 快速工作流按钮，一键启动常用流程
```

### 3. API编程调用
```typescript
import { useWorkflowStore } from '@/stores/workflow'

const workflowStore = useWorkflowStore()

// 执行工作流
await workflowStore.executeWorkflow('at_command_test', {
  device_id: 'ESP32_001',
  operator: '张工程师'
})

// 监控状态
console.log('运行中:', workflowStore.runningExecutions)
console.log('已暂停:', workflowStore.pausedExecutions)
```

### 4. WebSocket实时交互
```typescript
// 初始化连接
workflowStore.initWebSocket()

// 系统会自动处理确认请求
// 用户确认后工作流自动继续执行
```

---

## 🔒 安全特性

### 🛡️ 执行安全
- **步骤验证**: 每个串口指令都有期望回复验证
- **超时控制**: 防止步骤无限等待
- **重试机制**: 支持失败步骤重试
- **用户确认**: 关键操作必须通过WebSocket确认

### 📝 完整审计
- **操作记录**: 记录每个步骤的输入输出
- **用户追踪**: 记录操作员ID和工位信息  
- **时间戳**: 精确的执行时间
- **变量历史**: 完整的变量变更记录

---

## 🎨 用户界面

### 主控制页面特性
- 🎯 **工作流模板卡片** - 可视化选择和执行
- 📊 **状态统计面板** - 运行中/暂停/完成数量
- 📋 **执行历史列表** - 详细的执行记录
- 🌐 **WebSocket状态** - 实时连接状态显示
- 🔧 **步骤详情查看** - 时间线形式展示流程

### 通信页面集成
- 🚀 **快速工作流按钮** - AT测试、设备重启
- 🎨 **渐变色设计** - 美观的视觉效果
- ⚡ **一键启动** - 无需参数的快速执行

### WebSocket确认弹窗
- 📱 **自动弹出** - 工作流执行到确认步骤时
- ℹ️ **详细信息** - 步骤名称、描述、变量内容
- 🔘 **多选项支持** - 继续/停止/重新执行等
- ✍️ **操作员备注** - 记录确认理由

---

## 🧪 测试验证

### 功能演示
运行演示脚本验证了完整功能：
- ✅ 工作流创建和执行
- ✅ 串口指令发送和回复验证
- ✅ 变量解析和传递
- ✅ 用户确认流程
- ✅ 实时状态监控

### 测试工具
- **`工作流系统最终测试.html`** - 网页版API测试工具
- **演示脚本** - 命令行完整功能演示
- **API文档** - http://localhost:8000/api/v1/docs

---

## 🔧 自定义扩展

### 添加新工作流
在 `workflow_engine.py` 中添加新的工作流定义：

```python
custom_workflow = WorkflowDefinition(
    workflow_id="production_test",
    name="生产测试流程",
    description="完整的生产线测试流程",
    steps=[
        WorkflowStep(
            step_id="test_1",
            name="初始化设备",
            step_type=StepType.SERIAL_SEND,
            serial_command="AT+CFUN=1",
            expected_response="OK",
            next_step_id="test_2"
        ),
        WorkflowStep(
            step_id="test_2",
            name="确认测试参数",
            step_type=StepType.USER_CONFIRM,
            confirm_message="设备已初始化\n\n测试参数:\n- 产品SN: ${product_sn}\n- 测试模式: ${test_mode}\n\n确认开始测试？",
            confirm_options=["开始测试", "修改参数", "取消"],
            next_step_id="test_3"
        )
        # 更多步骤...
    ],
    start_step_id="test_1",
    variables={"product_sn": "", "test_mode": "standard"}
)
```

### 扩展步骤类型
可以在 `WorkflowEngine._execute_step()` 中添加新的步骤类型。

---

## 🚨 已解决的问题

### ✅ Element Plus图标
- **VideoStop** → **Close**
- **TestTube** → **Operation**
- 所有图标都已验证存在

### ✅ API导入格式
- 统一使用 `import { api } from './index'`
- 修复所有API调用格式

### ✅ 响应数据处理
- 适配现有API拦截器
- 移除冗余的 `response.code` 检查

### ✅ Undefined错误
- 添加安全检查 `?.length || 0`
- 计算属性默认值处理

---

## 🎉 系统状态: 完全可用

**工作流自动化系统现在完全就绪！**

### 🚀 立即使用
1. **访问工作流页面**: `http://192.168.100.3:3000/workflow`
2. **在通信页面使用**: 顶部快速工作流按钮
3. **测试功能**: 打开 `工作流系统最终测试.html`

### 📋 核心优势
- **更强大**: 步骤化流程 vs 简单命令
- **更灵活**: 变量系统 + 条件分支
- **更安全**: WebSocket确认 + 步骤验证  
- **更直观**: 可视化监控 + 时间线展示

### 🔧 完全符合需求
✅ **定义每个步骤输入什么到串口**  
✅ **要求串口回复什么内容**  
✅ **支持变量引用**  
✅ **通过WebSocket发送确认框给用户确认**  

**这正是你需要的工作流效果！** 🎊