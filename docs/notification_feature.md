# WebSocket 通知消息功能

## 功能概述

新增的通知消息功能允许后端通过 WebSocket 向前端发送需要用户确认的通知消息。这些消息会以对话框的形式显示，用户可以选择确认或关闭。

## 消息类型

### WSNotificationMessage 接口

```typescript
interface WSNotificationMessage {
  type: WSMessageType.NOTIFICATION
  title: string                    // 通知标题
  message: string                  // 通知内容
  level: 'info' | 'warning' | 'error' | 'success'  // 通知级别
  requireConfirm: boolean          // 是否需要用户确认
  timestamp: string               // 时间戳
  id?: string                     // 通知ID（可选，用于确认回调）
}
```

### 通知级别说明

- `info`: 信息提示（蓝色图标）
- `warning`: 警告信息（黄色图标）  
- `error`: 错误信息（红色图标）
- `success`: 成功信息（绿色图标）

## 前端实现

### 1. 消息处理

在 `handleWebSocketMessage` 函数中新增了对 `NOTIFICATION` 类型消息的处理：

```typescript
// 处理通知消息
if (message.type === WSMessageType.NOTIFICATION) {
  const notificationMsg = message as WSNotificationMessage
  
  // 记录通知日志
  addLog({
    type: 'at',
    direction: 'received',
    description: `系统通知: ${notificationMsg.title}`,
    data: notificationMsg.message,
    success: notificationMsg.level !== 'error'
  })

  // 显示通知对话框
  currentNotification.value = notificationMsg
  showNotificationDialog.value = true

  return
}
```

### 2. 通知对话框组件

新增了 `NotificationDialog.vue` 组件，具有以下特性：

- 根据通知级别显示不同颜色的图标
- 支持需要确认和不需要确认两种模式
- 美观的 UI 设计，符合 Element Plus 风格
- 响应式布局

### 3. 用户确认处理

当用户确认通知时，会：

1. 记录确认日志到通信日志中
2. 向后端发送确认消息（如果通知包含 ID）
3. 关闭对话框

## 后端发送示例

### Python WebSocket 发送

```python
import json
from datetime import datetime

# 创建通知消息
notification = {
    "type": "notification",
    "title": "设备警告",
    "message": "检测到温度异常，请检查散热系统",
    "level": "warning",
    "requireConfirm": True,
    "timestamp": datetime.now().isoformat(),
    "id": "warning_001"
}

# 发送到WebSocket客户端
await websocket.send(json.dumps(notification))
```

### 不同类型的通知示例

```python
# 信息通知（不需要确认）
info_notification = {
    "type": "notification",
    "title": "系统信息",
    "message": "设备连接状态正常",
    "level": "info",
    "requireConfirm": False,
    "timestamp": datetime.now().isoformat()
}

# 错误通知（需要确认）
error_notification = {
    "type": "notification", 
    "title": "系统错误",
    "message": "设备通信失败，请检查连接",
    "level": "error",
    "requireConfirm": True,
    "timestamp": datetime.now().isoformat(),
    "id": "error_001"
}

# 成功通知（需要确认）
success_notification = {
    "type": "notification",
    "title": "操作成功", 
    "message": "设备校准完成",
    "level": "success",
    "requireConfirm": True,
    "timestamp": datetime.now().isoformat(),
    "id": "success_001"
}
```

## 确认回调

当用户确认通知时，前端会发送确认消息到后端：

```json
{
  "type": "command",
  "command": "NOTIFICATION_CONFIRM",
  "args": ["{\"type\":\"notification_confirm\",\"notification_id\":\"warning_001\",\"timestamp\":\"2024-01-01T12:00:00.000Z\"}"],
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

## 测试

使用提供的测试脚本 `backend/test_notification.py` 来测试通知功能：

```bash
cd backend
uv run test_notification.py
```

确保：
1. 后端 WebSocket 服务正在运行
2. 前端应用已打开并连接到 WebSocket  
3. 前端页面在 Communication 页面

## 使用场景

这个功能适用于：

- 设备状态异常警告
- 操作完成确认
- 系统错误通知
- 重要信息提醒
- 需要用户干预的情况

## 注意事项

1. 通知消息会同时记录在通信日志中
2. 需要确认的通知会阻止用户操作直到确认
3. 不需要确认的通知可以通过关闭按钮关闭
4. 所有通知都会显示相应的图标和颜色
5. 确认操作会发送回调到后端（如果提供了通知 ID）