#!/usr/bin/env python3
"""
测试通知消息功能的示例脚本
展示如何从后端发送需要用户确认的通知消息
"""

import asyncio
import json
import websockets
from datetime import datetime

# 模拟发送通知消息的示例
async def send_notification_example():
    """发送各种类型的通知消息示例"""
    
    # WebSocket连接地址（需要根据实际情况调整）
    uri = "ws://localhost:8000/api/v1/ws/terminal/test_client"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("已连接到WebSocket服务器")
            
            # 示例1: 信息通知（不需要确认）
            info_notification = {
                "type": "notification",
                "title": "系统信息",
                "message": "设备连接状态正常，当前温度：25°C",
                "level": "info",
                "requireConfirm": False,
                "timestamp": datetime.now().isoformat(),
                "id": "info_001"
            }
            
            await websocket.send(json.dumps(info_notification))
            print(f"发送信息通知: {info_notification['message']}")
            
            # 等待2秒
            await asyncio.sleep(2)
            
            # 示例2: 警告通知（需要确认）
            warning_notification = {
                "type": "notification",
                "title": "设备警告",
                "message": "检测到温度异常（35°C），请检查散热系统是否正常工作",
                "level": "warning",
                "requireConfirm": True,
                "timestamp": datetime.now().isoformat(),
                "id": "warning_001"
            }
            
            await websocket.send(json.dumps(warning_notification))
            print(f"发送警告通知: {warning_notification['message']}")
            
            # 等待2秒
            await asyncio.sleep(2)
            
            # 示例3: 错误通知（需要确认）
            error_notification = {
                "type": "notification",
                "title": "系统错误",
                "message": "设备通信失败，请检查连接线路并重新连接设备",
                "level": "error",
                "requireConfirm": True,
                "timestamp": datetime.now().isoformat(),
                "id": "error_001"
            }
            
            await websocket.send(json.dumps(error_notification))
            print(f"发送错误通知: {error_notification['message']}")
            
            # 等待2秒
            await asyncio.sleep(2)
            
            # 示例4: 成功通知（需要确认）
            success_notification = {
                "type": "notification",
                "title": "操作成功",
                "message": "设备校准完成，所有参数已更新至最新配置",
                "level": "success",
                "requireConfirm": True,
                "timestamp": datetime.now().isoformat(),
                "id": "success_001"
            }
            
            await websocket.send(json.dumps(success_notification))
            print(f"发送成功通知: {success_notification['message']}")
            
            # 监听确认消息
            print("\n等待用户确认消息...")
            try:
                while True:
                    response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    message = json.loads(response)
                    
                    if message.get("type") == "command" and message.get("command") == "NOTIFICATION_CONFIRM":
                        confirm_data = json.loads(message.get("args", ["{}"])[0])
                        print(f"收到用户确认: 通知ID {confirm_data.get('notification_id')}")
                    else:
                        print(f"收到其他消息: {message}")
                        
            except asyncio.TimeoutError:
                print("等待确认超时")
                
    except ConnectionRefusedError:
        print("无法连接到WebSocket服务器，请确保后端服务正在运行")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    print("=== 通知消息测试示例 ===")
    print("此脚本将发送不同类型的通知消息到前端")
    print("请确保:")
    print("1. 后端WebSocket服务正在运行")
    print("2. 前端应用已打开并连接到WebSocket")
    print("3. 前端页面在Communication页面")
    print()
    
    asyncio.run(send_notification_example())