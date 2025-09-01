#!/usr/bin/env python3
"""
Industrial HMI Startup Script
工业上位机系统启动脚本

支持 Windows 和 Linux 跨平台运行
"""

import os
import sys
import subprocess
import platform
import time
import signal
import shutil
from pathlib import Path
from typing import Optional, List


class CrossPlatformRunner:
    """跨平台运行器"""
    
    def __init__(self):
        self.system = platform.system()
        self.is_windows = self.system == "Windows"
        self.project_root = Path(__file__).parent.absolute()
        self.backend_process: Optional[subprocess.Popen] = None
        self.frontend_process: Optional[subprocess.Popen] = None
        
    def print_header(self):
        """打印启动头信息"""
        print("🏭 Industrial HMI - 工业上位机系统")
        print("==================================")
        print(f"Platform: {self.system}")
        print(f"Project Root: {self.project_root}")
        print("")
        
    def check_command(self, command: str) -> bool:
        """检查命令是否存在"""
        return shutil.which(command) is not None
        
    def check_dependencies(self):
        """检查必要的依赖"""
        print("🔍 Checking dependencies...")
        
        # 检查 uv
        if not self.check_command("uv"):
            print("❌ uv not found. Please install uv:")
            print("   Linux/macOS: curl -LsSf https://astral.sh/uv/install.sh | sh")
            print("   Windows: powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\"")
            sys.exit(1)
        print("✅ uv found")
        
        # 检查 node (仅开发模式需要)
        if hasattr(self, '_dev_mode') and self._dev_mode:
            if not self.check_command("npm"):
                print("❌ npm not found. Please install Node.js")
                print("   https://nodejs.org/")
                sys.exit(1)
            print("✅ npm found")
            
    def setup_backend(self):
        """设置后端环境"""
        print("📦 Installing backend dependencies...")
        os.chdir(self.project_root)
        
        try:
            subprocess.run(["uv", "sync"], check=True)
            print("✅ Backend dependencies installed")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install backend dependencies: {e}")
            sys.exit(1)
            
    def setup_frontend(self):
        """设置前端环境"""
        frontend_dir = self.project_root / "frontend"
        dist_dir = frontend_dir / "dist"
        node_modules = frontend_dir / "node_modules"
        
        # 如果已经构建过，跳过
        if dist_dir.exists():
            print("✅ Frontend already built")
            return
            
        print("🎨 Building frontend...")
        os.chdir(frontend_dir)
        
        # 安装依赖
        if not node_modules.exists():
            print("📦 Installing frontend dependencies...")
            try:
                subprocess.run(["npm", "install"], check=True)
                print("✅ Frontend dependencies installed")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install frontend dependencies: {e}")
                sys.exit(1)
        
        # 构建前端
        try:
            subprocess.run(["npm", "run", "build"], check=True)
            print("✅ Frontend built successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to build frontend: {e}")
            sys.exit(1)
            
        os.chdir(self.project_root)
        
    def start_production(self):
        """启动生产模式"""
        print("")
        print("🚀 Starting Industrial HMI in production mode...")
        print("Backend: http://localhost:8000")
        print("API Docs: http://localhost:8000/docs") 
        print("Frontend: http://localhost:8000")
        print("")
        print("Press Ctrl+C to stop...")
        
        # 启动后端
        try:
            os.chdir(self.project_root)
            if self.is_windows:
                self.backend_process = subprocess.Popen([
                    "uv", "run", "python", "backend/start.py"
                ])
            else:
                self.backend_process = subprocess.Popen([
                    "uv", "run", "python", "backend/start.py"
                ])
                
            # 等待进程结束
            self.backend_process.wait()
            
        except KeyboardInterrupt:
            print("\n🛑 Stopping services...")
            self.cleanup()
        except Exception as e:
            print(f"❌ Error starting application: {e}")
            self.cleanup()
            sys.exit(1)
            
    def start_development(self):
        """启动开发模式"""
        self._dev_mode = True  # 标记为开发模式
        print("")
        print("🚀 Starting Industrial HMI in development mode...")
        
        # 启动后端
        print("📡 Starting FastAPI backend...")
        os.chdir(self.project_root)
        
        try:
            if self.is_windows:
                self.backend_process = subprocess.Popen([
                    "uv", "run", "python", "backend/start.py"
                ], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            else:
                self.backend_process = subprocess.Popen([
                    "uv", "run", "python", "backend/start.py"
                ])
        except Exception as e:
            print(f"❌ Failed to start backend: {e}")
            sys.exit(1)
            
        # 等待后端启动
        time.sleep(3)
        
        # 启动前端
        print("🎨 Starting Vue3 frontend...")
        frontend_dir = self.project_root / "frontend"
        os.chdir(frontend_dir)
        
        # 检查依赖
        if not (frontend_dir / "node_modules").exists():
            print("📦 Installing frontend dependencies...")
            try:
                subprocess.run(["npm", "install"], check=True)
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install frontend dependencies: {e}")
                self.cleanup()
                sys.exit(1)
        
        try:
            if self.is_windows:
                self.frontend_process = subprocess.Popen([
                    "npm", "run", "dev"
                ], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            else:
                self.frontend_process = subprocess.Popen([
                    "npm", "run", "dev"
                ])
        except Exception as e:
            print(f"❌ Failed to start frontend: {e}")
            self.cleanup()
            sys.exit(1)
            
        print("✅ Services started!")
        print("Backend: http://localhost:8000")
        print("Frontend: http://localhost:3000") 
        print("API Docs: http://localhost:8000/docs")
        print("")
        print("Press Ctrl+C to stop all services...")
        
        # 等待进程
        try:
            while True:
                time.sleep(1)
                # 检查进程是否还在运行
                if self.backend_process.poll() is not None:
                    print("❌ Backend process stopped")
                    break
                if self.frontend_process.poll() is not None:
                    print("❌ Frontend process stopped")
                    break
        except KeyboardInterrupt:
            print("\n🛑 Stopping services...")
            self.cleanup()
            
    def cleanup(self):
        """清理进程"""
        if self.backend_process:
            try:
                if self.is_windows:
                    self.backend_process.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    self.backend_process.terminate()
                self.backend_process.wait(timeout=5)
            except (subprocess.TimeoutExpired, ProcessLookupError):
                if self.backend_process.poll() is None:
                    self.backend_process.kill()
                    
        if self.frontend_process:
            try:
                if self.is_windows:
                    self.frontend_process.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    self.frontend_process.terminate()
                self.frontend_process.wait(timeout=5)
            except (subprocess.TimeoutExpired, ProcessLookupError):
                if self.frontend_process.poll() is None:
                    self.frontend_process.kill()


def main():
    """主函数"""
    runner = CrossPlatformRunner()
    
    # 解析命令行参数
    dev_mode = "--dev" in sys.argv or "-d" in sys.argv
    help_mode = "--help" in sys.argv or "-h" in sys.argv
    
    if help_mode:
        print("Industrial HMI Startup Script")
        print("Usage:")
        print("  python start.py        # 生产模式")
        print("  python start.py --dev  # 开发模式")
        print("  python start.py -d     # 开发模式")
        print("  python start.py --help # 显示帮助")
        return
        
    runner.print_header()
    
    # 检查依赖
    if dev_mode:
        runner._dev_mode = True
    runner.check_dependencies()
    
    # 设置后端
    runner.setup_backend()
    
    if dev_mode:
        # 开发模式
        runner.start_development()
    else:
        # 生产模式
        runner.setup_frontend()
        runner.start_production()


if __name__ == "__main__":
    main()
