#!/usr/bin/env python3
"""
通知功能使用示例
展示如何在现有的FastAPI应用中集成和使用通知功能
"""

import asyncio
import requests
from datetime import datetime
from typing import Optional

# 导入现有的WebSocket管理器
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.api.v1.websocket import manager


class NotificationService:
    """通知服务类，封装通知发送功能"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000/api/v1"
    
    async def send_device_status_notification(self, device_name: str, status: str, temperature: float = None):
        """发送设备状态通知"""
        if status == "normal":
            level = "info"
            title = "设备状态正常"
            message = f"{device_name} 运行正常"
            if temperature:
                message += f"，当前温度：{temperature}°C"
            require_confirm = False
        elif status == "warning":
            level = "warning"
            title = "设备状态警告"
            message = f"{device_name} 检测到异常"
            if temperature:
                message += f"，温度异常：{temperature}°C"
            require_confirm = True
        elif status == "error":
            level = "error"
            title = "设备状态错误"
            message = f"{device_name} 发生错误，请立即检查"
            require_confirm = True
        else:
            level = "info"
            title = "设备状态更新"
            message = f"{device_name} 状态：{status}"
            require_confirm = False
        
        notification_id = f"device_{device_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        await manager.send_notification(
            title=title,
            message=message,
            level=level,
            require_confirm=require_confirm,
            notification_id=notification_id
        )
        
        return notification_id
    
    async def send_operation_result_notification(self, operation: str, success: bool, details: str = None):
        """发送操作结果通知"""
        if success:
            level = "success"
            title = "操作成功"
            message = f"{operation} 已成功完成"
            if details:
                message += f"：{details}"
        else:
            level = "error"
            title = "操作失败"
            message = f"{operation} 执行失败"
            if details:
                message += f"：{details}"
        
        notification_id = f"operation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        await manager.send_notification(
            title=title,
            message=message,
            level=level,
            require_confirm=True,
            notification_id=notification_id
        )
        
        return notification_id
    
    async def send_system_maintenance_notification(self, maintenance_type: str, scheduled_time: str = None):
        """发送系统维护通知"""
        title = "系统维护通知"
        if scheduled_time:
            message = f"系统将于 {scheduled_time} 进行{maintenance_type}，请提前保存工作"
        else:
            message = f"系统正在进行{maintenance_type}，请稍候"
        
        notification_id = f"maintenance_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        await manager.send_notification(
            title=title,
            message=message,
            level="warning",
            require_confirm=True,
            notification_id=notification_id
        )
        
        return notification_id
    
    def send_notification_via_api(self, title: str, message: str, level: str = "info", 
                                 require_confirm: bool = False, notification_id: str = None):
        """通过REST API发送通知（同步方法）"""
        try:
            response = requests.post(
                f"{self.base_url}/ws/send-notification",
                params={
                    "title": title,
                    "message": message,
                    "level": level,
                    "require_confirm": require_confirm,
                    "notification_id": notification_id
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "sent_to_clients": result.get("data", {}).get("sent_to_clients", 0),
                    "notification_id": notification_id
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# 使用示例
async def demo_notifications():
    """演示各种通知使用场景"""
    notification_service = NotificationService()
    
    print("=== 通知功能演示 ===\n")
    
    # 1. 设备状态通知
    print("1. 发送设备状态通知...")
    await notification_service.send_device_status_notification("温度传感器01", "normal", 25.5)
    await asyncio.sleep(2)
    
    await notification_service.send_device_status_notification("压力传感器02", "warning", 85.2)
    await asyncio.sleep(2)
    
    await notification_service.send_device_status_notification("主控制器", "error")
    await asyncio.sleep(2)
    
    # 2. 操作结果通知
    print("2. 发送操作结果通知...")
    await notification_service.send_operation_result_notification("设备校准", True, "所有参数已更新")
    await asyncio.sleep(2)
    
    await notification_service.send_operation_result_notification("数据备份", False, "存储空间不足")
    await asyncio.sleep(2)
    
    # 3. 系统维护通知
    print("3. 发送系统维护通知...")
    await notification_service.send_system_maintenance_notification("定期维护", "2024-01-15 02:00")
    await asyncio.sleep(2)
    
    print("演示完成！")


def demo_api_notifications():
    """演示通过API发送通知"""
    notification_service = NotificationService()
    
    print("=== 通过API发送通知演示 ===\n")
    
    # 通过API发送各种通知
    notifications = [
        {
            "title": "API测试通知",
            "message": "这是通过REST API发送的测试通知",
            "level": "info",
            "require_confirm": False,
            "notification_id": "api_test_001"
        },
        {
            "title": "重要提醒",
            "message": "请确认是否要执行此操作？此操作不可撤销。",
            "level": "warning",
            "require_confirm": True,
            "notification_id": "api_confirm_001"
        }
    ]
    
    for i, notification in enumerate(notifications, 1):
        print(f"{i}. 发送{notification['level']}级别通知: {notification['title']}")
        result = notification_service.send_notification_via_api(**notification)
        
        if result["success"]:
            print(f"   ✅ 成功发送到 {result['sent_to_clients']} 个客户端")
        else:
            print(f"   ❌ 发送失败: {result['error']}")
        
        if i < len(notifications):
            import time
            time.sleep(2)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="通知功能使用示例")
    parser.add_argument("--mode", choices=["websocket", "api", "both"], default="both",
                       help="选择演示模式: websocket, api, 或 both")
    
    args = parser.parse_args()
    
    print("通知功能使用示例")
    print("请确保后端服务正在运行，并且有前端客户端连接到WebSocket\n")
    
    if args.mode in ["websocket", "both"]:
        print("运行WebSocket通知演示...")
        try:
            asyncio.run(demo_notifications())
        except KeyboardInterrupt:
            print("WebSocket演示被用户中断")
        except Exception as e:
            print(f"WebSocket演示失败: {e}")
    
    if args.mode in ["api", "both"]:
        if args.mode == "both":
            print("\n" + "="*50 + "\n")
        
        print("运行API通知演示...")
        try:
            demo_api_notifications()
        except KeyboardInterrupt:
            print("API演示被用户中断")
        except Exception as e:
            print(f"API演示失败: {e}")
    
    print("\n=== 演示完成 ===")