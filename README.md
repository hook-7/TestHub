# Industrial HMI - AT指令交互系统

工业上位机系统，专注于AT指令通信交互。

## 技术栈

- 后端: FastAPI + Python
- 前端: Vue3 + Element Plus + Vite
- 数据库: PostgreSQL
- 包管理: uv
- 通信协议: AT指令 (串口通信)

## 功能特性

- 串口自动检测和配置
- AT指令发送和响应（前端完全控制格式）
- 常用AT指令快捷按钮
- AT指令历史记录
- 批量AT指令发送
- 终止符控制（\r\n, \r, \n 或无终止符）
- 原始十六进制数据收发
- 通信日志记录和导出
- 现代化Web界面


## 环境要求

- Python 3.9+
- PostgreSQL 12+
- uv (Python包管理器)
- Node.js 16+ (仅开发模式需要)

**安装uv:**
- Linux/macOS: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Windows: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`

**安装PostgreSQL:**
- Ubuntu/Debian: `sudo apt-get install postgresql postgresql-contrib`
- CentOS/RHEL: `sudo yum install postgresql-server postgresql-contrib`
- Windows: 下载并安装 [PostgreSQL官方安装包](https://www.postgresql.org/download/windows/)
- macOS: `brew install postgresql`

## 快速开始

### 1. 数据库配置

首先需要创建PostgreSQL数据库：

```sql
-- 连接到PostgreSQL
psql -U postgres

-- 创建数据库
CREATE DATABASE testhub;

-- 创建用户（可选，也可以使用默认的postgres用户）
CREATE USER testhub_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE testhub TO testhub_user;
```

### 2. 环境配置

创建 `.env` 文件并配置数据库连接：

```bash
# 数据库配置
HMI_DB_HOST=localhost
HMI_DB_PORT=5432
HMI_DB_NAME=testhub
HMI_DB_USER=postgres
HMI_DB_PASSWORD=postgres
HMI_DB_ECHO=false

# 其他配置...
```

### 3. 跨平台启动 (推荐)

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

## 使用说明

1. **串口配置**: 首先在串口配置页面选择串口并设置通信参数

2. **AT指令交互**: 进入通信页面，可以：
   - **手动输入AT指令**: 在输入框中输入指令，支持回车快速发送
   - **终止符控制**: 选择合适的终止符（\r\n, \r, \n）或无终止符
   - **快捷按钮**: 使用预置的常用AT指令快捷按钮
   - **历史记录**: 查看和重用之前发送的指令
   - **批量发送**: 一次性发送多个AT指令，可设置发送间隔
   - **原始数据**: 发送十六进制原始数据
   - **日志管理**: 查看通信日志并导出为CSV文件

3. **前端完全控制**: 
   - 后端只做数据透传，不修改AT指令格式
   - 前端控制指令格式化、终止符添加等所有细节
   - 支持任意自定义AT指令格式

## 接口地址

- 前端界面: http://localhost:8000 (生产模式) 或 http://localhost:3000 (开发模式)
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

## 项目结构

```
├── backend/                # 后端代码
│   ├── app/
│   │   ├── api/           # API路由
│   │   ├── core/          # 核心配置
│   │   ├── drivers/       # 串口驱动
│   │   ├── schemas/       # 数据模型
│   │   └── services/      # 业务逻辑
│   └── start.py           # 后端启动脚本
├── frontend/              # 前端代码
│   ├── src/
│   │   ├── api/          # API接口
│   │   ├── stores/       # 状态管理
│   │   ├── views/        # 页面组件
│   │   └── router/       # 路由配置
│   └── package.json
└── start.py              # 项目启动脚本
```