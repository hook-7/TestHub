"""
命令行服务
处理WebSocket命令的解析和执行
"""

import asyncio
import logging
import subprocess
import sys
import platform
from datetime import datetime
from typing import Dict, List, Any, Optional
from app.schemas.websocket import CommandType, WSResponseMessage, WSMessageType

logger = logging.getLogger(__name__)


class CommandService:
    """命令行服务类"""
    
    def __init__(self):
        self.available_commands = {
            "help": self._help_command,
            "system": self._system_command,
            "device": self._device_command,
            "clear": self._clear_command,
            "ping": self._ping_command,
            "status": self._status_command,
            "version": self._version_command,
            "ls": self._ls_command,
            "pwd": self._pwd_command,
            "date": self._date_command,
        }
    
    async def execute_command(self, command: str, args: List[str] = None) -> WSResponseMessage:
        """
        执行命令
        
        Args:
            command: 命令名称
            args: 命令参数
            
        Returns:
            WSResponseMessage: 响应消息
        """
        if args is None:
            args = []
            
        try:
            logger.info(f"执行命令: {command} {' '.join(args)}")
            
            if command in self.available_commands:
                result = await self.available_commands[command](args)
                return WSResponseMessage(
                    type=WSMessageType.RESPONSE,
                    message=result,
                    timestamp=datetime.now().isoformat(),
                    success=True
                )
            else:
                # 尝试执行系统命令
                result = await self._execute_system_command(command, args)
                return WSResponseMessage(
                    type=WSMessageType.RESPONSE,
                    message=result,
                    timestamp=datetime.now().isoformat(),
                    success=True
                )
                
        except Exception as e:
            logger.error(f"命令执行失败: {command} - {str(e)}")
            return WSResponseMessage(
                type=WSMessageType.ERROR,
                message=f"命令执行失败: {str(e)}",
                timestamp=datetime.now().isoformat(),
                success=False
            )
    
    async def _help_command(self, args: List[str]) -> str:
        """帮助命令"""
        help_text = """
可用命令:
  help          - 显示帮助信息
  system        - 显示系统信息
  device        - 设备相关操作
  clear         - 清屏
  ping          - 网络连通性测试
  status        - 显示系统状态
  version       - 显示版本信息
  ls [path]     - 列出目录内容
  pwd           - 显示当前目录
  date          - 显示当前时间
  
系统命令:
  大部分Linux/Windows系统命令都可以使用
  例如: ps, top, df, free, netstat等
        """
        return help_text.strip()
    
    async def _system_command(self, args: List[str]) -> str:
        """系统信息命令"""
        info = {
            "操作系统": platform.system(),
            "系统版本": platform.release(),
            "架构": platform.machine(),
            "处理器": platform.processor(),
            "Python版本": sys.version,
            "当前时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        result = "系统信息:\n"
        for key, value in info.items():
            result += f"  {key}: {value}\n"
        
        return result.strip()
    
    async def _device_command(self, args: List[str]) -> str:
        """设备操作命令"""
        if not args:
            return "设备命令用法:\n  device list - 列出设备\n  device status - 设备状态"
        
        if args[0] == "list":
            return "设备列表:\n  - 暂无设备连接"
        elif args[0] == "status":
            return "设备状态:\n  - 系统正常运行"
        else:
            return f"未知的设备命令: {args[0]}"
    
    async def _clear_command(self, args: List[str]) -> str:
        """清屏命令"""
        return "\033[2J\033[H"  # ANSI清屏序列
    
    async def _ping_command(self, args: List[str]) -> str:
        """Ping命令"""
        target = args[0] if args else "127.0.0.1"
        try:
            if platform.system().lower() == "windows":
                cmd = ["ping", "-n", "4", target]
            else:
                cmd = ["ping", "-c", "4", target]
            
            result = await self._execute_system_command(cmd[0], cmd[1:])
            return result
        except Exception as e:
            return f"Ping失败: {str(e)}"
    
    async def _status_command(self, args: List[str]) -> str:
        """状态命令"""
        return f"系统状态: 正常\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n服务: 运行中"
    
    async def _version_command(self, args: List[str]) -> str:
        """版本命令"""
        return "Industrial HMI v1.0.0\nFastAPI + Vue3 + Element Plus"
    
    async def _ls_command(self, args: List[str]) -> str:
        """列出目录内容"""
        path = args[0] if args else "."
        try:
            if platform.system().lower() == "windows":
                result = await self._execute_system_command("dir", [path])
            else:
                result = await self._execute_system_command("ls", ["-la", path])
            return result
        except Exception as e:
            return f"无法列出目录内容: {str(e)}"
    
    async def _pwd_command(self, args: List[str]) -> str:
        """显示当前目录"""
        try:
            if platform.system().lower() == "windows":
                result = await self._execute_system_command("cd")
            else:
                result = await self._execute_system_command("pwd")
            return result
        except Exception as e:
            return f"无法获取当前目录: {str(e)}"
    
    async def _date_command(self, args: List[str]) -> str:
        """显示当前时间"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    async def _execute_system_command(self, command: str, args: List[str] = None) -> str:
        """
        执行系统命令
        
        Args:
            command: 命令名称
            args: 命令参数
            
        Returns:
            str: 命令输出
        """
        if args is None:
            args = []
        
        try:
            # 安全检查：禁止执行危险命令
            dangerous_commands = ["rm", "del", "format", "fdisk", "mkfs", "dd"]
            if command.lower() in dangerous_commands:
                return f"出于安全考虑，禁止执行命令: {command}"
            
            # 构建完整命令
            full_command = [command] + args
            
            # 执行命令
            process = await asyncio.create_subprocess_exec(
                *full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=None
            )
            
            # 等待命令完成，设置超时
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10.0)
            except asyncio.TimeoutError:
                process.kill()
                return "命令执行超时"
            
            # 处理输出
            if process.returncode == 0:
                output = stdout.decode('utf-8', errors='ignore').strip()
                return output if output else "命令执行成功，无输出"
            else:
                error = stderr.decode('utf-8', errors='ignore').strip()
                return f"命令执行失败 (退出码: {process.returncode}): {error}"
                
        except FileNotFoundError:
            return f"命令未找到: {command}"
        except Exception as e:
            return f"命令执行异常: {str(e)}"