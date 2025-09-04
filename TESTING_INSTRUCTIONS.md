
# 🧪 工作流系统测试说明

## 🌐 访问地址
- 前端应用: http://localhost:3000
- API调试页面: http://localhost:3000/debug.html
- 后端API文档: http://localhost:8000/api/v1/docs

## 🔧 已修复的问题
1. ✅ 添加了缺失的API端点 (/workflow/executions)
2. ✅ 修复了API响应拦截器结构
3. ✅ 配置了正确的CORS和代理设置
4. ✅ 添加了调试页面用于测试

## 🎯 测试步骤
1. 打开浏览器访问: http://localhost:3000
2. 如果遇到API问题，访问: http://localhost:3000/debug.html
3. 在调试页面点击各个测试按钮验证API功能
4. 访问工作流管理页面: http://localhost:3000/workflow

## 🚀 系统功能
- ✅ 工作流定义和管理
- ✅ JSON格式工作流配置
- ✅ 变量系统和表达式支持
- ✅ 步骤类型: send, expect, assign, confirm, control
- ✅ 实时执行监控
- ✅ WebSocket通信支持

## 🔍 如果仍有问题
1. 清除浏览器缓存
2. 使用无痕/隐私模式访问
3. 检查浏览器控制台错误信息
4. 运行测试脚本: python3 test_full_system.py
