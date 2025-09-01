# Industrial HMI

工业上位机系统，支持RS485通信协议。

## 技术栈

- 后端: FastAPI + Python
- 前端: Vue3 + Element Plus + Vite
- 包管理: uv
- 通信协议: RS485 (Modbus RTU)

## 功能特性

- 串口自动检测和配置
- RS485/Modbus RTU通信
- 寄存器读写操作
- 原始数据收发
- 现代化Web界面

## 环境要求

- Python 3.8+
- uv (Python包管理器)
- Node.js 16+ (仅开发模式需要)

**安装uv:**
- Linux/macOS: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Windows: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`

## 快速开始

### 跨平台启动 (推荐)

项目提供了Python启动脚本，支持Windows和Linux：

**生产模式启动:**
```bash
python3 start.py
```

**开发模式启动:**
```bash
python3 start.py --dev
```

### 传统启动方式

**后端启动:**
```bash
uv sync
uv run python backend/start.py
```

### 前端开发

```bash
cd frontend
npm install
npm run dev
```

### 生产部署

```bash
cd frontend
npm run build
cd ..
uv run python backend/app/main.py
```

## API文档

启动后端服务后访问: http://localhost:8000/docs