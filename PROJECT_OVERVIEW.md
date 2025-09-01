# Industrial HMI - 工业上位机系统

## 🎯 项目概述

这是一个基于 **FastAPI + Vue3 + Element Plus** 的工业上位机系统，主要用于与硬件设备进行RS485通信。

### 🚀 核心功能

1. **串口通信管理**
   - 自动检测可用串口设备
   - 支持手动配置串口参数
   - 实时连接状态监控

2. **RS485/Modbus RTU协议**
   - 读取保持寄存器 (功能码03)
   - 读取输入寄存器 (功能码04) 
   - 写入单个寄存器 (功能码06)
   - 写入多个寄存器 (功能码10)
   - 原始数据收发功能

3. **现代化Web界面**
   - 响应式设计
   - 实时通信日志
   - 数据格式转换 (十进制/十六进制/二进制)
   - 美观的Element Plus UI

## 🏗️ 技术架构

### 后端 (FastAPI)
```
backend/
├── app/
│   ├── main.py              # 主应用入口
│   ├── core/                # 核心模块
│   │   ├── config.py        # 配置管理
│   │   ├── logging.py       # 日志配置
│   │   └── response.py      # 统一响应格式
│   ├── drivers/             # 硬件驱动层
│   │   ├── serial_driver.py # 串口驱动
│   │   └── rs485_protocol.py# RS485协议处理
│   ├── services/            # 业务逻辑层
│   │   └── serial_service.py# 串口业务服务
│   ├── schemas/             # API数据模型
│   │   └── serial_schemas.py# 串口相关模型
│   └── api/v1/endpoints/    # API路由
│       └── serial.py        # 串口API端点
└── start.py                 # 应用启动器
```

### 前端 (Vue3 + Element Plus)
```
frontend/
├── src/
│   ├── main.ts              # 应用入口
│   ├── App.vue              # 根组件
│   ├── router/              # 路由配置
│   ├── stores/              # Pinia状态管理
│   │   ├── connection.ts    # 连接状态管理
│   │   └── communication.ts # 通信日志管理
│   ├── api/                 # API接口层
│   │   ├── index.ts         # Axios配置
│   │   └── serial.ts        # 串口API
│   ├── views/               # 页面组件
│   │   ├── SerialConfig.vue # 串口配置页
│   │   └── Communication.vue# 通信测试页
│   └── styles/              # 样式文件
└── dist/                    # 构建输出 (生产)
```

## 🔧 开发规范

### 编码风格
- **Python**: PEP8, snake_case变量, PascalCase类名
- **Vue3**: 组合式API, PascalCase组件名, TypeScript支持
- **API**: RESTful设计, 统一响应格式

### 错误码规范
- `0`: 成功
- `400`: 参数错误  
- `500`: 系统错误
- `1xxx`: 业务错误

## 🚀 快速开始

### 1. 一键启动 (推荐)
```bash
./start.sh
```

### 2. 开发模式
```bash
# 后端
source $HOME/.local/bin/env
uv sync
uv run python backend/start.py

# 前端 (新终端)
cd frontend
npm install
npm run dev
```

### 3. 生产部署
```bash
cd frontend && npm run build
cd .. && uv run python backend/start.py
```

## 🧪 测试工具

```bash
# 项目状态检查
uv run python check_project.py

# 串口功能测试
uv run python tools/serial_test.py
```

## 📱 访问地址

- **生产环境**: http://localhost:8000
- **开发前端**: http://localhost:3000  
- **API文档**: http://localhost:8000/docs
- **后端API**: http://localhost:8000/api/v1

## 📋 功能特性

### ✅ 已实现
- [x] 串口自动检测和手动配置
- [x] RS485/Modbus RTU通信协议
- [x] 寄存器读写操作
- [x] 原始数据收发
- [x] 现代化Web界面
- [x] 实时通信日志
- [x] 生产环境静态文件服务
- [x] 完整的API文档

### 🔄 可扩展功能
- [ ] 设备配置文件管理
- [ ] 通信数据持久化
- [ ] 多设备并发通信
- [ ] 数据可视化图表
- [ ] 用户权限管理
- [ ] 设备状态监控

## 🛠️ 故障排除

详见 `USAGE.md` 文件中的故障排除部分。

---

**项目状态**: ✅ 完成基础功能开发  
**下一步**: 根据实际硬件设备进行测试和调优