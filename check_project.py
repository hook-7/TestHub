#!/usr/bin/env python3
"""
Project Status Check
检查项目完整性和功能状态
"""

import os
import sys
import asyncio
import subprocess
from pathlib import Path

def check_file_exists(file_path, description):
    """检查文件是否存在"""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} (缺失)")
        return False

def check_directory_exists(dir_path, description):
    """检查目录是否存在"""
    if os.path.isdir(dir_path):
        print(f"✅ {description}: {dir_path}")
        return True
    else:
        print(f"❌ {description}: {dir_path} (缺失)")
        return False

async def check_api_endpoint(url, description):
    """检查API端点"""
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    print(f"✅ {description}: {url}")
                    return True
                else:
                    print(f"⚠️ {description}: {url} (状态码: {response.status})")
                    return False
    except Exception as e:
        print(f"❌ {description}: {url} (错误: {e})")
        return False

def main():
    print("🔍 Industrial HMI 项目状态检查")
    print("=" * 50)
    
    # 检查项目结构
    print("\n📁 项目结构:")
    structure_ok = True
    
    # 后端文件
    backend_files = [
        ("pyproject.toml", "项目配置"),
        ("backend/app/main.py", "主应用"),
        ("backend/app/core/config.py", "配置模块"),
        ("backend/app/drivers/serial_driver.py", "串口驱动"),
        ("backend/app/drivers/rs485_protocol.py", "RS485协议"),
        ("backend/app/api/v1/endpoints/serial.py", "串口API"),
        ("backend/app/services/serial_service.py", "串口服务"),
        ("backend/start.py", "启动脚本"),
    ]
    
    for file_path, description in backend_files:
        if not check_file_exists(file_path, description):
            structure_ok = False
    
    # 前端文件
    frontend_files = [
        ("frontend/package.json", "前端配置"),
        ("frontend/vite.config.ts", "Vite配置"),
        ("frontend/src/main.ts", "前端入口"),
        ("frontend/src/App.vue", "主组件"),
        ("frontend/src/api/serial.ts", "API接口"),
        ("frontend/src/stores/connection.ts", "连接状态"),
        ("frontend/src/views/SerialConfig.vue", "串口配置页"),
        ("frontend/src/views/Communication.vue", "通信测试页"),
    ]
    
    for file_path, description in frontend_files:
        if not check_file_exists(file_path, description):
            structure_ok = False
    
    # 检查目录
    print("\n📂 目录结构:")
    dirs = [
        ("backend/app", "后端应用目录"),
        ("frontend/src", "前端源码目录"),
        ("frontend/dist", "前端构建目录"),
        ("tools", "工具目录"),
        ("scripts", "脚本目录"),
    ]
    
    for dir_path, description in dirs:
        if not check_directory_exists(dir_path, description):
            structure_ok = False
    
    # 检查依赖
    print("\n📦 依赖检查:")
    
    # 检查uv
    try:
        subprocess.run(["uv", "--version"], check=True, capture_output=True)
        print("✅ uv 包管理器已安装")
    except:
        print("❌ uv 包管理器未安装")
        structure_ok = False
    
    # 检查Python依赖
    if os.path.exists(".venv"):
        print("✅ Python虚拟环境已创建")
    else:
        print("⚠️ Python虚拟环境未创建，运行 'uv sync' 创建")
    
    # 检查前端依赖
    if os.path.exists("frontend/node_modules"):
        print("✅ 前端依赖已安装")
    else:
        print("⚠️ 前端依赖未安装，运行 'cd frontend && npm install'")
    
    # 总结
    print("\n📊 检查结果:")
    if structure_ok:
        print("✅ 项目结构完整")
        print("\n🚀 启动命令:")
        print("   开发模式: ./scripts/start-dev.sh")
        print("   生产模式: ./start.sh")
        print("   测试工具: uv run python tools/serial_test.py")
    else:
        print("❌ 项目结构不完整，请检查缺失文件")
    
    print("\n📚 更多信息请查看 USAGE.md")

if __name__ == "__main__":
    main()