# 自动化命令工具模块

## 概述

自动化命令工具模块提供了一套完整的自动化命令执行系统，支持命令模板、参数化执行、用户确认和状态监控等功能。

## 功能特性

### 🚀 核心功能
- **命令模板管理**: 预定义常用命令模板，支持参数化配置
- **确认机制**: 支持需要用户确认的危险操作
- **状态监控**: 实时跟踪命令执行状态
- **历史记录**: 完整的命令执行历史和结果记录
- **优先级管理**: 支持不同优先级的命令调度

### 🛡️ 安全特性
- **操作确认**: 危险操作需要用户明确确认
- **操作日志**: 记录操作员、时间、工位等关键信息
- **超时控制**: 防止命令长时间占用资源
- **状态追踪**: 实时监控命令执行状态

## 使用方式

### 1. 快速执行预定义命令

在自动化控制页面 (`/automation`) 中，可以通过点击模板卡片快速执行预定义命令：

- **清理缓存**: 系统命令，无需确认
- **备份数据**: 维护命令，需要确认
- **重启设备**: 设备命令，需要确认
- **执行测试序列**: 测试命令，需要确认

### 2. 嵌入式工具栏

`AutomationToolbar` 组件可以嵌入到其他页面中，提供快速操作：

```vue
<template>
  <div>
    <!-- 其他内容 -->
    <AutomationToolbar
      :show-status="true"
      :quick-template-ids="['clear_cache', 'backup_data']"
      :workstation-id="currentWorkstation"
      :operator-id="currentOperator"
      @command-created="handleCommandCreated"
    />
  </div>
</template>
```

### 3. 自定义命令

支持创建自定义命令，包括：
- 命令名称和描述
- 命令类型（系统/设备/测试/维护）
- 优先级设置
- 参数配置
- 确认要求

## API 接口

### 后端 API

基础路径: `/api/v1/automation`

#### 命令管理
- `POST /commands` - 创建命令
- `GET /commands` - 获取命令列表
- `GET /commands/{command_id}` - 获取单个命令
- `POST /commands/{command_id}/confirm` - 确认命令执行
- `DELETE /commands/{command_id}` - 取消命令

#### 模板管理
- `GET /templates` - 获取模板列表
- `GET /templates/{template_id}` - 获取单个模板
- `POST /templates/{template_id}/execute` - 执行模板命令

### 前端 API

使用 `AutomationAPI` 类进行接口调用：

```typescript
import AutomationAPI from '@/api/automation'

// 创建命令
const command = await AutomationAPI.createCommand({
  command_name: '重启设备',
  command_type: 'device',
  parameters: { device_id: 'DEV001' },
  requires_confirmation: true
})

// 执行模板
const command = await AutomationAPI.executeTemplateCommand(
  'restart_device',
  { device_id: 'DEV001', force: false }
)
```

## 状态管理

使用 Pinia store (`useAutomationStore`) 管理状态：

```typescript
import { useAutomationStore } from '@/stores/automation'

const automationStore = useAutomationStore()

// 加载模板
await automationStore.loadTemplates()

// 执行命令
const command = await automationStore.executeTemplate('backup_data', {})

// 监控状态
console.log('等待确认的命令:', automationStore.pendingCommands)
console.log('正在执行的命令:', automationStore.executingCommands)
```

## 命令类型

### 系统命令 (system)
- 影响系统运行状态的命令
- 示例: 清理缓存、重启服务

### 设备命令 (device)  
- 直接控制硬件设备的命令
- 示例: 重启设备、设备校准

### 测试命令 (test)
- 执行自动化测试的命令
- 示例: 运行测试序列、质量检测

### 维护命令 (maintenance)
- 系统维护相关的命令
- 示例: 备份数据、清理日志

## 确认流程

对于需要确认的命令，执行流程如下：

1. **创建命令**: 状态为 `pending`
2. **显示确认弹窗**: 用户查看命令详情和风险提示
3. **用户确认**: 选择确认执行或取消
4. **执行命令**: 状态变为 `executing`
5. **完成执行**: 状态变为 `success` 或 `failed`

## 扩展开发

### 添加新的命令模板

在 `AutomationService` 的 `_init_default_templates` 方法中添加：

```python
CommandTemplate(
    template_id="custom_command",
    name="自定义命令",
    command_type=CommandType.SYSTEM,
    description="这是一个自定义命令",
    parameters_schema={
        "param1": {"type": "string", "required": True, "description": "参数1"},
        "param2": {"type": "boolean", "required": False, "default": False}
    },
    requires_confirmation=True
)
```

### 实现具体命令逻辑

在 `AutomationService` 的 `_execute_command_sync` 方法中添加具体的执行逻辑。

## 注意事项

1. **权限控制**: 确保只有授权用户可以执行危险命令
2. **日志记录**: 所有命令执行都会记录详细日志
3. **错误处理**: 命令执行失败时会记录错误信息
4. **资源管理**: 注意命令执行的资源占用和超时控制
5. **并发控制**: 避免同时执行冲突的命令

## 测试地址

前端页面: http://192.168.100.3:3000/automation
API文档: http://192.168.100.3:8000/api/v1/docs