# 前端串口功能说明

## 概述

本项目现在支持两种串口通信模式：
1. **后端串口模式**：传统的后端处理串口通信，通过WebSocket推送数据到前端
2. **前端串口模式**：使用Web Serial API直接在浏览器中处理串口通信

## 浏览器兼容性

前端串口功能基于 Web Serial API，目前支持的浏览器：
- Chrome 89+ ✅
- Edge 89+ ✅
- Firefox ❌ (暂不支持)
- Safari ❌ (暂不支持)

## 使用方法

### 1. 切换到前端串口模式

在串口配置页面，点击"前端串口"按钮即可切换到前端串口模式。

### 2. 连接串口

在前端串口模式下：
1. 配置串口参数（波特率、数据位、校验位、停止位）
2. 点击"连接串口"按钮
3. 浏览器会弹出串口选择对话框
4. 选择要连接的串口设备
5. 串口连接成功后即可开始通信

### 3. 发送和接收数据

- **发送AT指令**：在指令输入框中输入AT指令，点击发送
- **发送原始数据**：在十六进制输入框中输入数据，点击发送
- **接收数据**：接收到的数据会自动显示在通信日志中

## 技术实现

### 前端串口服务 (`/src/services/serial.ts`)

```typescript
// 检查浏览器支持
frontendSerialAPI.isSupported()

// 连接串口
await frontendSerialAPI.connectSerial(config)

// 发送AT指令
await frontendSerialAPI.sendATCommand(command, serialId)

// 发送原始数据
await frontendSerialAPI.sendRawData(hexData, serialId)

// 设置数据回调
frontendSerialAPI.setDataCallback(serialId, callback)
```

### 状态管理

前端串口状态通过 Pinia store 管理：
- `useConnectionStore.useFrontendSerial` - 是否使用前端串口
- `useConnectionStore.frontendSerialSupported` - 浏览器是否支持Web Serial API
- `useCommunicationStore.useFrontendSerial` - 通信模式状态

## 安全注意事项

1. **HTTPS要求**：Web Serial API 只能在 HTTPS 环境下使用
2. **用户授权**：每次连接串口都需要用户手动授权
3. **权限管理**：浏览器会记住用户的串口访问权限

## 测试页面

项目提供了一个独立的测试页面来验证前端串口功能：
- 访问：`http://localhost:3000/serial-test.html`
- 功能：串口连接、数据发送接收、参数配置

## 故障排除

### 1. 浏览器不支持
**问题**：点击"前端串口"按钮没有反应
**解决**：请使用 Chrome 89+ 或 Edge 89+ 浏览器

### 2. 无法选择串口
**问题**：点击"连接串口"后没有弹出选择对话框
**解决**：
- 确保使用 HTTPS 访问
- 检查浏览器是否阻止了弹窗
- 确保有串口设备连接

### 3. 连接失败
**问题**：选择串口后连接失败
**解决**：
- 检查串口参数配置是否正确
- 确保串口设备没有被其他程序占用
- 尝试重新插拔串口设备

### 4. 数据接收异常
**问题**：发送数据后没有收到响应
**解决**：
- 检查串口连接是否正常
- 确认设备是否正常工作
- 检查波特率等参数是否匹配

## 开发说明

### 添加新的串口功能

1. 在 `SerialConnectionManager` 类中添加新方法
2. 在 `frontendSerialAPI` 中暴露接口
3. 在相应的 store 中集成功能
4. 更新 UI 组件

### 调试技巧

1. 使用浏览器开发者工具查看控制台日志
2. 检查 Web Serial API 的权限状态
3. 使用测试页面验证基本功能
4. 对比后端串口模式的行为

## 未来改进

1. 支持更多串口参数配置
2. 添加串口设备自动检测
3. 优化数据接收性能
4. 添加串口连接状态监控
5. 支持多串口并发通信

## 相关文档

- [Web Serial API 官方文档](https://developer.mozilla.org/en-US/docs/Web/API/Web_Serial_API)
- [Chrome Web Serial API 指南](https://web.dev/serial/)
- [串口通信协议参考](https://en.wikipedia.org/wiki/Serial_communication)