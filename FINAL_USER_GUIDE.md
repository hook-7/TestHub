# 🎯 工作流管理系统 - 最终使用指南

## ✅ 问题解决确认

所有报告的问题已完全修复：

- ✅ **404错误**: 已添加缺失的API端点 `/workflow/executions`
- ✅ **数据访问错误**: 修复了API响应拦截器，现在可正确访问 `workflows` 和 `executions`
- ✅ **登录阻塞**: 简化了会话管理，添加了强制清理功能
- ✅ **undefined值错误**: 修复了串口配置页面的数据处理，过滤了无效数据

## 🌐 系统访问

### 主要地址
- **前端应用**: http://localhost:3000
- **工作流管理**: http://localhost:3000/workflow
- **API文档**: http://localhost:8000/api/v1/docs

### 调试工具
- **登录测试**: http://localhost:3000/login-test.html
- **API调试**: http://localhost:3000/debug.html

## 🚀 快速开始

### 1. 启动系统
```bash
# 后端 (终端1)
source $HOME/.local/bin/env
cd /workspace
uv run python backend/start.py

# 前端 (终端2) 
cd /workspace/frontend
npm run dev
```

### 2. 访问应用
1. 打开浏览器访问: **http://localhost:3000**
2. 进入登录页面，点击登录（现在不会阻塞）
3. 访问工作流管理: **http://localhost:3000/workflow**

### 3. 使用工作流功能
1. **创建工作流**: 点击"新建工作流"按钮
2. **配置步骤**: 添加send、expect、assign、confirm、control步骤
3. **执行工作流**: 在工作流列表中点击"执行"
4. **监控执行**: 查看执行进度和日志

## 🔧 故障排除

### 如果遇到登录问题
```bash
# 方法1: 运行修复脚本
source $HOME/.local/bin/env && uv run python fix_login.py

# 方法2: 访问调试页面
# http://localhost:3000/login-test.html
# 点击"强制清理所有会话"

# 方法3: 手动清理
curl -X POST http://localhost:3000/api/v1/session/force-cleanup
```

### 如果遇到API错误
```bash
# 验证所有修复
source $HOME/.local/bin/env && uv run python verify_fixes.py

# 检查服务状态
curl http://localhost:3000/api/v1/health
```

## 📋 功能特性

### ✅ 工作流定义
- 支持5种步骤类型: send, expect, assign, confirm, control
- JSON格式配置，支持变量占位符
- 可视化编辑器界面

### ✅ 变量系统
- 安全的表达式执行 (asteval)
- 支持逻辑判断: `voltage > 200 and status == "OK"`
- 支持正则提取: `re.search(r'ID=(\\d+)', reply).group(1)`
- 变量替换: `"设备${device_id}状态正常"`

### ✅ 执行引擎
- 异步工作流执行
- 实时状态监控
- 执行日志记录
- 用户确认交互

### ✅ 前端界面
- 现代化UI (Vue3 + Element Plus)
- 工作流CRUD管理
- 执行监控界面
- 实时日志展示

## 🎯 工作流示例

### 简单的设备检测工作流
```json
{
  "name": "设备检测工作流",
  "description": "检测设备状态并获取ID",
  "variables": {
    "device_id": "",
    "status": ""
  },
  "steps": [
    {
      "id": "step_1",
      "name": "发送状态查询",
      "type": "send",
      "command": "AT+STATUS?",
      "delay": 1.0
    },
    {
      "id": "step_2",
      "name": "期望OK回复",
      "type": "expect", 
      "expect_type": "string",
      "pattern": "OK",
      "timeout": 5.0
    },
    {
      "id": "step_3",
      "name": "获取设备ID",
      "type": "send",
      "command": "AT+ID?",
      "delay": 0.5
    },
    {
      "id": "step_4",
      "name": "提取设备ID",
      "type": "assign",
      "variable": "device_id",
      "expression": "re.search(r'ID=(\\d+)', last_response).group(1)"
    },
    {
      "id": "step_5",
      "name": "用户确认",
      "type": "confirm",
      "message": "检测到设备ID: ${device_id}, 是否继续？",
      "options": ["确认", "取消"],
      "timeout": 30.0
    }
  ]
}
```

## 🧪 测试验证

### 运行完整测试
```bash
# 验证所有修复
source $HOME/.local/bin/env && uv run python verify_fixes.py

# 运行完整系统测试
source $HOME/.local/bin/env && uv run python test_full_system.py
```

### 预期结果
```
🎯 验证结果: 3/3 通过
🎉 所有修复验证通过！

📱 系统现在可以正常使用:
- 主应用: http://localhost:3000
- 登录应该不会再阻塞
- 串口配置页面不会有undefined错误
- 工作流功能完全正常
```

## 📞 技术支持

### 如果仍有问题
1. **清除浏览器缓存**并刷新页面
2. **使用无痕模式**访问应用
3. **查看浏览器控制台**获取详细错误信息
4. **访问调试页面**进行诊断

### 紧急恢复
```bash
# 重启所有服务
pkill -f "python.*backend" && pkill -f "vite"
source $HOME/.local/bin/env && cd /workspace && uv run python backend/start.py &
cd /workspace/frontend && npm run dev &
```

## 🎉 总结

**工作流管理系统现在完全可用！**

- ✅ 所有核心功能正常运行
- ✅ 登录阻塞问题已解决
- ✅ API数据结构问题已修复
- ✅ 前端undefined错误已消除
- ✅ 完整的测试验证通过

**现在可以开始使用完整的工作流管理功能了！** 🚀