#!/usr/bin/env python3
"""
工作流系统测试脚本
"""

import asyncio
import json
import requests
import time
from typing import Dict, Any

# 配置
BASE_URL = "http://localhost:8000/api/v1"

def create_test_workflow() -> Dict[str, Any]:
    """创建测试工作流"""
    return {
        "name": "设备检测工作流",
        "description": "检测设备状态并获取设备ID的示例工作流",
        "variables": {
            "device_port": "/dev/ttyUSB0",
            "expected_voltage": 220,
            "device_id": ""
        },
        "steps": [
            {
                "id": "step_1",
                "name": "发送检测指令",
                "type": "send",
                "description": "向设备发送状态检测指令",
                "command": "AT+STATUS?",
                "delay": 1.0
            },
            {
                "id": "step_2", 
                "name": "期望OK回复",
                "type": "expect",
                "description": "期望设备返回OK状态",
                "expect_type": "string",
                "pattern": "OK",
                "timeout": 5.0
            },
            {
                "id": "step_3",
                "name": "获取设备ID",
                "type": "send",
                "description": "请求设备ID",
                "command": "AT+ID?",
                "delay": 0.5
            },
            {
                "id": "step_4",
                "name": "提取设备ID",
                "type": "assign", 
                "description": "从回复中提取设备ID",
                "variable": "device_id",
                "expression": "re.search(r'ID=(\\d+)', last_response).group(1) if re.search(r'ID=(\\d+)', last_response) else 'unknown'"
            },
            {
                "id": "step_5",
                "name": "确认设备ID",
                "type": "confirm",
                "description": "用户确认设备ID是否正确",
                "message": "检测到设备ID: ${device_id}, 是否继续？",
                "options": ["确认", "取消"],
                "timeout": 30.0
            },
            {
                "id": "step_6",
                "name": "检查确认结果",
                "type": "control",
                "description": "根据用户确认结果决定后续操作",
                "control_type": "if",
                "condition": "confirm_result == '确认'",
                "steps": [
                    {
                        "id": "step_6_1",
                        "name": "记录成功",
                        "type": "assign",
                        "variable": "test_result",
                        "expression": "'success'"
                    }
                ]
            }
        ]
    }

def test_workflow_api():
    """测试工作流API"""
    print("🧪 开始测试工作流API...")
    
    # 1. 创建工作流
    print("\n1. 创建测试工作流...")
    workflow_data = create_test_workflow()
    
    try:
        response = requests.post(f"{BASE_URL}/workflow/", json=workflow_data)
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                workflow = result["data"]
                workflow_id = workflow["id"]
                print(f"✅ 工作流创建成功: {workflow['name']} (ID: {workflow_id})")
            else:
                print(f"❌ 创建工作流失败: {result.get('msg', 'Unknown error')}")
                return None
        else:
            print(f"❌ API请求失败: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 创建工作流异常: {e}")
        return None
    
    # 2. 获取工作流列表
    print("\n2. 获取工作流列表...")
    try:
        response = requests.get(f"{BASE_URL}/workflow/")
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                workflows = result["data"]["workflows"]
                print(f"✅ 获取到 {len(workflows)} 个工作流")
            else:
                print(f"❌ 获取工作流列表失败: {result.get('msg')}")
        else:
            print(f"❌ API请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 获取工作流列表异常: {e}")
    
    # 3. 获取工作流详情
    print(f"\n3. 获取工作流详情...")
    try:
        response = requests.get(f"{BASE_URL}/workflow/{workflow_id}")
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                workflow_detail = result["data"]
                print(f"✅ 获取工作流详情成功: {workflow_detail['name']}")
                print(f"   步骤数量: {len(workflow_detail['steps'])}")
                print(f"   变量数量: {len(workflow_detail['variables'])}")
            else:
                print(f"❌ 获取工作流详情失败: {result.get('msg')}")
        else:
            print(f"❌ API请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 获取工作流详情异常: {e}")
    
    # 4. 执行工作流（模拟）
    print(f"\n4. 模拟执行工作流...")
    try:
        execute_data = {
            "variables": {
                "test_mode": True
            },
            "session_id": "test_session"
        }
        
        response = requests.post(f"{BASE_URL}/workflow/{workflow_id}/execute", json=execute_data)
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                execution_data = result["data"]
                execution_id = execution_data["execution_id"]
                print(f"✅ 工作流开始执行: {execution_id}")
                
                # 监控执行状态
                print("\n   监控执行状态...")
                for i in range(10):  # 最多监控10次
                    time.sleep(2)
                    
                    status_response = requests.get(f"{BASE_URL}/workflow/execution/{execution_id}")
                    if status_response.status_code == 200:
                        status_result = status_response.json()
                        if status_result.get("code") == 0:
                            execution = status_result["data"]
                            print(f"   状态: {execution['status']}, 当前步骤: {execution.get('current_step', 'N/A')}")
                            
                            # 如果执行完成或失败，停止监控
                            if execution['status'] in ['completed', 'failed', 'cancelled']:
                                print(f"   执行结束: {execution['status']}")
                                if execution.get('error_message'):
                                    print(f"   错误信息: {execution['error_message']}")
                                break
                        else:
                            print(f"   获取状态失败: {status_result.get('msg')}")
                            break
                    else:
                        print(f"   状态查询失败: {status_response.status_code}")
                        break
                else:
                    print("   监控超时")
                    
            else:
                print(f"❌ 执行工作流失败: {result.get('msg')}")
        else:
            print(f"❌ API请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 执行工作流异常: {e}")
    
    print(f"\n🎉 工作流API测试完成！")
    return workflow_id

def test_workflow_crud():
    """测试工作流CRUD操作"""
    print("\n🔧 开始测试工作流CRUD操作...")
    
    workflow_id = test_workflow_api()
    if not workflow_id:
        return
    
    # 5. 更新工作流
    print(f"\n5. 更新工作流...")
    try:
        update_data = {
            "description": "更新后的描述：设备检测和状态验证工作流"
        }
        
        response = requests.put(f"{BASE_URL}/workflow/{workflow_id}", json=update_data)
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                print("✅ 工作流更新成功")
            else:
                print(f"❌ 更新工作流失败: {result.get('msg')}")
        else:
            print(f"❌ API请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 更新工作流异常: {e}")
    
    # 6. 删除工作流
    print(f"\n6. 删除工作流...")
    try:
        response = requests.delete(f"{BASE_URL}/workflow/{workflow_id}")
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                print("✅ 工作流删除成功")
            else:
                print(f"❌ 删除工作流失败: {result.get('msg')}")
        else:
            print(f"❌ API请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 删除工作流异常: {e}")

def test_health_check():
    """测试健康检查"""
    print("🏥 检查服务健康状态...")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 服务运行正常: {result}")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 工作流系统测试开始...")
    print(f"📍 测试目标: {BASE_URL}")
    
    # 健康检查
    if not test_health_check():
        print("❌ 服务不可用，请检查后端服务是否启动")
        exit(1)
    
    # CRUD测试
    test_workflow_crud()
    
    print("\n🎯 所有测试完成！")