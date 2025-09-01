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

## 快速开始

### 后端启动

```bash
cd /workspace
source $HOME/.local/bin/env
uv sync
uv run python backend/app/main.py
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