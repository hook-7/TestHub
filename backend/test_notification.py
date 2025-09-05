#!/usr/bin/env python3
"""
测试通知消息功能的示例脚本
展示如何从后端发送需要用户确认的通知消息
"""

import asyncio
import json
import requests
from datetime import datetime

# 后端API基础URL
BASE_URL = "http://localhost:8000/api/v1"

def test_notification_api():
    """通过REST API发送通知消息测试"""
    
    print("=== 通过REST API测试通知功能 ===")
    
    # 测试不同类型的通知
    notifications = [
        {
            "title": "系统信息",
            "message": "设备连接状态正常，当前温度：25°C",
            "level": "info",
            "require_confirm": False,
            "notification_id": "info_001"
        },
        {
            "title": "设备警告", 
            "message": "检测到温度异常（35°C），请检查散热系统是否正常工作",
            "level": "warning",
            "require_confirm": True,
            "notification_id": "warning_001"
        },
        {
            "title": "系统错误",
            "message": "设备通信失败，请检查连接线路并重新连接设备",
            "level": "error",
            "require_confirm": True,
            "notification_id": "error_001"
        },
        {
            "title": "操作成功",
            "message": "设备校准完成，所有参数已更新至最新配置",
            "level": "success", 
            "require_confirm": True,
            "notification_id": "success_001"
        }
    ]
    
    for i, notification in enumerate(notifications):
        try:
            print(f"\n{i+1}. 发送{notification['level']}通知: {notification['title']}")
            
            # 发送POST请求
            response = requests.post(
                f"{BASE_URL}/ws/send-notification",
                params=notification
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ 发送成功: {result.get('msg', '')}")
                print(f"   发送到 {result.get('data', {}).get('sent_to_clients', 0)} 个客户端")
            else:
                print(f"   ❌ 发送失败: {response.status_code} - {response.text}")
                
            # 间隔2秒
            if i < len(notifications) - 1:
                print("   等待2秒...")
                import time
                time.sleep(2)
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ 连接失败: 无法连接到后端服务 {BASE_URL}")
            break
        except Exception as e:
            print(f"   ❌ 发送失败: {e}")


async def test_websocket_direct():
    """直接通过WebSocket发送通知消息测试"""
    
    print("\n=== 直接通过WebSocket测试通知功能 ===")
    
    # WebSocket连接地址
    uri = "ws://localhost:8000/api/v1/ws/terminal/test_client"
    
    try:
        import websockets
        
        async with websockets.connect(uri) as websocket:
            print("已连接到WebSocket服务器")
            
            # 直接发送通知消息（模拟后端发送）
            notifications = [
                {
                    "type": "notification",
                    "title": "WebSocket直连测试",
                    "message": "这是通过WebSocket直接发送的通知消息",
                    "level": "info",
                    "requireConfirm": False,
                    "timestamp": datetime.now().isoformat(),
                    "id": "ws_direct_001"
                },
                {
                    "type": "notification", 
                    "title": "需要确认的通知",
                    "message": "这条消息需要用户确认才能关闭",
                    "level": "warning",
                    "requireConfirm": True,
                    "timestamp": datetime.now().isoformat(),
                    "id": "ws_direct_002"
                }
            ]
            
            for notification in notifications:
                await websocket.send(json.dumps(notification))
                print(f"发送通知: {notification['title']}")
                await asyncio.sleep(2)
            
            # 监听确认消息
            print("\n等待用户确认消息...")
            try:
                while True:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    message = json.loads(response)
                    
                    if message.get("type") == "command" and message.get("command") == "NOTIFICATION_CONFIRM":
                        confirm_data = json.loads(message.get("args", ["{}"])[0])
                        print(f"收到用户确认: 通知ID {confirm_data.get('notification_id')}")
                    else:
                        print(f"收到其他消息: {message.get('type', 'unknown')}")
                        
            except asyncio.TimeoutError:
                print("等待确认超时")
                
    except ImportError:
        print("需要安装 websockets 库: pip install websockets")
    except ConnectionRefusedError:
        print("无法连接到WebSocket服务器，请确保后端服务正在运行")
    except Exception as e:
        print(f"WebSocket测试失败: {e}")


def check_websocket_status():
    """检查WebSocket连接状态"""
    try:
        response = requests.get(f"{BASE_URL}/ws/status")
        if response.status_code == 200:
            result = response.json()
            data = result.get('data', {})
            print(f"WebSocket状态: {data.get('active_connections', 0)} 个活跃连接")
            print(f"连接的客户端: {data.get('connected_clients', [])}")
            return data.get('active_connections', 0) > 0
        else:
            print(f"获取WebSocket状态失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"检查WebSocket状态失败: {e}")
        return False


if __name__ == "__main__":
    print("=== 通知消息功能测试 ===")
    print("此脚本将测试通知消息功能")
    print("请确保:")
    print("1. 后端服务正在运行 (http://localhost:8000)")
    print("2. 前端应用已打开并连接到WebSocket")
    print("3. 前端页面在Communication页面")
    print()
    
    # 检查WebSocket状态
    print("1. 检查WebSocket连接状态...")
    has_connections = check_websocket_status()
    
    if not has_connections:
        print("⚠️  没有活跃的WebSocket连接，通知可能无法送达")
        print("   请确保前端已连接到WebSocket")
    
    print("\n2. 通过REST API发送通知...")
    test_notification_api()
    
    print("\n3. 直接通过WebSocket发送通知...")
    try:
        asyncio.run(test_websocket_direct())
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    
    print("\n=== 测试完成 ===")