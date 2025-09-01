# 使用说明

## 快速启动

### 方式一：一键启动（推荐）
```bash
./start.sh
```

### 方式二：手动启动

#### 开发模式
```bash
# 启动后端
source $HOME/.local/bin/env
cd /workspace
uv sync
uv run python backend/start.py

# 启动前端（新终端）
cd frontend
npm install
npm run dev
```

#### 生产模式
```bash
# 构建前端
cd frontend
npm run build

# 启动后端（自动服务静态文件）
cd /workspace
uv run python backend/start.py
```

## 功能说明

### 1. 串口配置
- 自动检测可用串口
- 支持手动选择串口
- 配置波特率、数据位、校验位、停止位
- 实时连接状态显示

### 2. RS485通信
- 支持Modbus RTU协议
- 读取保持寄存器 (功能码03)
- 读取输入寄存器 (功能码04)
- 写入单个寄存器 (功能码06)
- 写入多个寄存器 (功能码10)
- 原始数据收发

### 3. 通信监控
- 实时通信日志
- 数据格式转换 (十进制/十六进制/二进制)
- 通信状态跟踪

## API接口

访问 http://localhost:8000/docs 查看完整API文档

### 主要端点：
- `GET /api/v1/serial/ports` - 获取可用串口
- `GET /api/v1/serial/auto-detect` - 自动检测串口
- `POST /api/v1/serial/connect` - 连接串口
- `POST /api/v1/serial/disconnect` - 断开连接
- `GET /api/v1/serial/status` - 获取连接状态
- `POST /api/v1/serial/read-registers` - 读取寄存器
- `POST /api/v1/serial/write-register` - 写入寄存器
- `POST /api/v1/serial/raw-data` - 发送原始数据

## 技术架构

### 后端 (FastAPI)
```
backend/
├── app/
│   ├── api/v1/endpoints/     # API路由
│   ├── core/                 # 核心配置
│   ├── drivers/              # 硬件驱动
│   ├── schemas/              # API模型
│   └── services/             # 业务逻辑
└── start.py                  # 启动文件
```

### 前端 (Vue3 + Element Plus)
```
frontend/
├── src/
│   ├── api/                  # API接口
│   ├── components/           # 组件
│   ├── stores/               # 状态管理
│   ├── views/                # 页面
│   └── styles/               # 样式
└── dist/                     # 构建输出
```

## 故障排除

### 1. 串口权限问题
```bash
# Linux下添加用户到dialout组
sudo usermod -a -G dialout $USER
# 重新登录生效
```

### 2. 端口被占用
```bash
# 查找占用端口的进程
lsof -i :8000
# 杀死进程
kill -9 <PID>
```

### 3. 依赖问题
```bash
# 重新安装后端依赖
uv sync --force

# 重新安装前端依赖
cd frontend && npm install --force
```