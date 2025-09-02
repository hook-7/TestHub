#!/usr/bin/env python3
"""
测试会话管理功能的脚本
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any

BASE_URL = "http://192.168.100.3:3000/api/v1"

async def test_session_api():
    """测试会话管理API"""
    async with aiohttp.ClientSession() as session:
        
        print("=== 测试会话管理功能 ===\n")
        
        # 1. 获取初始会话状态
        print("1. 获取初始会话状态...")
        async with session.get(f"{BASE_URL}/session/status") as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"   状态: {data}")
            else:
                print(f"   错误: {resp.status} - {await resp.text()}")
        
        print()
        
        # 2. 创建第一个会话
        print("2. 创建第一个会话...")
        session_data = {"client_info": "Test Client 1"}
        async with session.post(f"{BASE_URL}/session/create", json=session_data) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"   成功: {data}")
                session_id_1 = data['data']['session_id']
                token_1 = data['data']['token']
            else:
                print(f"   错误: {resp.status} - {await resp.text()}")
                return
        
        print()
        
        # 3. 验证会话状态
        print("3. 验证会话状态...")
        headers = {"X-Session-Id": session_id_1}
        async with session.post(f"{BASE_URL}/session/validate", headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"   验证结果: {data}")
            else:
                print(f"   错误: {resp.status} - {await resp.text()}")
        
        print()
        
        # 4. 尝试创建第二个会话（应该失败）
        print("4. 尝试创建第二个会话（应该失败）...")
        session_data_2 = {"client_info": "Test Client 2"}
        async with session.post(f"{BASE_URL}/session/create", json=session_data_2) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"   意外成功: {data}")
            else:
                error_data = await resp.json()
                print(f"   预期失败: {resp.status} - {error_data.get('msg', 'Unknown error')}")
        
        print()
        
        # 5. 测试串口连接（需要有效会话）
        print("5. 测试串口连接（需要有效会话）...")
        serial_config = {
            "port": "/dev/ttyUSB0",  # 这个端口可能不存在，但用于测试会话验证
            "baudrate": 9600,
            "bytesize": 8,
            "parity": "N",
            "stopbits": 1,
            "timeout": 1.0
        }
        async with session.post(f"{BASE_URL}/serial/connect", 
                               json=serial_config, 
                               headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"   连接成功: {data}")
            else:
                error_data = await resp.json()
                print(f"   连接失败: {resp.status} - {error_data.get('msg', 'Unknown error')}")
        
        print()
        
        # 6. 测试无会话的串口连接（应该失败）
        print("6. 测试无会话的串口连接（应该失败）...")
        async with session.post(f"{BASE_URL}/serial/connect", json=serial_config) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"   意外成功: {data}")
            else:
                print(f"   预期失败: {resp.status} - 缺少会话ID")
        
        print()
        
        # 7. 销毁会话
        print("7. 销毁会话...")
        async with session.delete(f"{BASE_URL}/session/destroy", headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"   销毁成功: {data}")
            else:
                print(f"   错误: {resp.status} - {await resp.text()}")
        
        print()
        
        # 8. 验证会话已销毁
        print("8. 验证会话已销毁...")
        async with session.get(f"{BASE_URL}/session/status") as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"   最终状态: {data}")
            else:
                print(f"   错误: {resp.status} - {await resp.text()}")

if __name__ == "__main__":
    asyncio.run(test_session_api())