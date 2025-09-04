#!/usr/bin/env python3
"""
自动化模块快速启动脚本
解决依赖问题，快速测试功能
"""
import subprocess
import sys
import os
from pathlib import Path


def install_dependencies():
    """安装必要依赖"""
    print("📦 安装必要依赖...")
    
    # 创建虚拟环境
    venv_path = Path(".venv")
    if not venv_path.exists():
        print("🔧 创建虚拟环境...")
        subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True)
    
    # 激活虚拟环境并安装依赖
    if os.name == 'nt':  # Windows
        pip_path = ".venv/Scripts/pip"
        python_path = ".venv/Scripts/python"
    else:  # Linux/Mac
        pip_path = ".venv/bin/pip"
        python_path = ".venv/bin/python"
    
    print("📥 安装Python包...")
    packages = [
        "fastapi>=0.104.1",
        "uvicorn[standard]>=0.24.0", 
        "pydantic>=2.5.0",
        "pydantic-settings>=2.0.0"
    ]
    
    for package in packages:
        print(f"   安装 {package}...")
        subprocess.run([pip_path, "install", package], check=True)
    
    return python_path


def start_backend(python_path):
    """启动后端服务"""
    print("🚀 启动后端服务...")
    
    # 设置环境变量
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path("backend").absolute())
    
    # 启动uvicorn
    cmd = [
        python_path, "-m", "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ]
    
    print(f"执行命令: {' '.join(cmd)}")
    print("🌐 服务将在 http://localhost:8000 启动")
    print("📖 API文档: http://localhost:8000/api/v1/docs")
    print("🤖 自动化API: http://localhost:8000/api/v1/automation/templates")
    
    # 切换到backend目录
    os.chdir("backend")
    subprocess.run(cmd, env=env)


def main():
    """主函数"""
    print("🤖 自动化命令模块快速启动")
    print("=" * 50)
    
    try:
        # 检查当前目录
        if not Path("backend").exists():
            print("❌ 未找到backend目录，请在项目根目录运行此脚本")
            return
        
        # 安装依赖
        python_path = install_dependencies()
        
        # 启动服务
        start_backend(python_path)
        
    except KeyboardInterrupt:
        print("\n⚠️  服务已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()