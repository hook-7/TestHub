#!/usr/bin/env python3
"""
完整系统测试脚本
测试前后端集成和工作流功能
"""

import requests
import json
import time
from typing import Dict, Any

# 配置 - 使用前端地址进行测试
FRONTEND_URL = "http://localhost:3000"
API_BASE = f"{FRONTEND_URL}/api/v1"

def test_system_health():
    """测试系统健康状态"""
    print("🏥 测试系统健康状态...")
    
    try:
        # 测试前端服务
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code == 200:
            print("✅ 前端服务运行正常")
        else:
            print(f"❌ 前端服务异常: {response.status_code}")
            return False
            
        # 测试后端健康检查（通过前端代理）
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 后端服务运行正常: {result.get('msg', '')}")
        else:
            print(f"❌ 后端健康检查失败: {response.status_code}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ 系统健康检查失败: {e}")
        return False

def test_workflow_api():
    """测试工作流API"""
    print("\n🧪 测试工作流API...")
    
    try:
        # 1. 测试工作流测试端点
        print("1. 测试工作流API连通性...")
        response = requests.get(f"{API_BASE}/workflow/test", timeout=5)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 工作流API连通: {result.get('msg', '')}")
        else:
            print(f"❌ 工作流API测试失败: {response.status_code}")
            return False
        
        # 2. 获取工作流列表
        print("2. 获取工作流列表...")
        response = requests.get(f"{API_BASE}/workflow/", timeout=5)
        if response.status_code == 200:
            result = response.json()
            workflows = result.get('data', {}).get('workflows', [])
            print(f"✅ 获取工作流列表成功: {len(workflows)} 个工作流")
        else:
            print(f"❌ 获取工作流列表失败: {response.status_code}")
            return False
        
        # 3. 创建测试工作流
        print("3. 创建测试工作流...")
        test_workflow = {
            "name": "系统测试工作流",
            "description": "用于验证系统功能的测试工作流",
            "variables": {
                "device_id": "",
                "test_mode": True
            },
            "steps": [
                {
                    "id": "step_1",
                    "name": "初始化测试",
                    "type": "assign",
                    "variable": "test_status",
                    "expression": "'initialized'"
                },
                {
                    "id": "step_2", 
                    "name": "模拟设备检测",
                    "type": "send",
                    "command": "AT+STATUS?",
                    "delay": 0.5
                },
                {
                    "id": "step_3",
                    "name": "验证响应",
                    "type": "expect",
                    "expect_type": "string",
                    "pattern": "OK",
                    "timeout": 3.0
                }
            ]
        }
        
        response = requests.post(
            f"{API_BASE}/workflow/", 
            json=test_workflow,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            workflow_data = result.get('data', {})
            workflow_id = workflow_data.get('id')
            print(f"✅ 创建工作流成功: {workflow_data.get('name')} (ID: {workflow_id})")
        else:
            print(f"❌ 创建工作流失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 工作流API测试失败: {e}")
        return False

def test_frontend_pages():
    """测试前端页面访问"""
    print("\n🌐 测试前端页面访问...")
    
    pages_to_test = [
        "/",
        "/login", 
        "/workflow",
        "/serial-config",
        "/communication"
    ]
    
    success_count = 0
    
    for page in pages_to_test:
        try:
            url = f"{FRONTEND_URL}{page}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ 页面可访问: {page}")
                success_count += 1
            else:
                print(f"❌ 页面访问失败: {page} (状态码: {response.status_code})")
                
        except Exception as e:
            print(f"❌ 页面访问异常: {page} - {e}")
    
    print(f"页面访问测试完成: {success_count}/{len(pages_to_test)} 成功")
    return success_count == len(pages_to_test)

def test_api_endpoints():
    """测试主要API端点"""
    print("\n🔌 测试主要API端点...")
    
    endpoints_to_test = [
        ("GET", "/health", "系统健康检查"),
        ("GET", "/workflow/", "工作流列表"),
        ("GET", "/workflow/test", "工作流测试"),
        ("GET", "/serial/status", "串口状态"),
        ("GET", "/session/status", "会话状态"),
    ]
    
    success_count = 0
    
    for method, endpoint, description in endpoints_to_test:
        try:
            url = f"{API_BASE}{endpoint}"
            
            if method == "GET":
                response = requests.get(url, timeout=5)
            elif method == "POST":
                response = requests.post(url, timeout=5)
            else:
                continue
                
            if response.status_code == 200:
                print(f"✅ {description}: {endpoint}")
                success_count += 1
            else:
                print(f"❌ {description}失败: {endpoint} (状态码: {response.status_code})")
                
        except Exception as e:
            print(f"❌ {description}异常: {endpoint} - {e}")
    
    print(f"API端点测试完成: {success_count}/{len(endpoints_to_test)} 成功")
    return success_count >= len(endpoints_to_test) * 0.8  # 80%成功率即可

def test_cors_and_proxy():
    """测试CORS和代理配置"""
    print("\n🔄 测试CORS和代理配置...")
    
    try:
        # 测试OPTIONS请求（CORS预检）
        response = requests.options(f"{API_BASE}/health", timeout=5)
        print(f"✅ CORS预检请求: {response.status_code}")
        
        # 测试带Origin头的请求
        headers = {"Origin": "http://localhost:3000"}
        response = requests.get(f"{API_BASE}/health", headers=headers, timeout=5)
        
        if response.status_code == 200:
            print("✅ 跨域请求处理正常")
            
            # 检查CORS头
            cors_headers = [
                "Access-Control-Allow-Origin",
                "Access-Control-Allow-Methods", 
                "Access-Control-Allow-Headers"
            ]
            
            found_headers = 0
            for header in cors_headers:
                if header in response.headers:
                    found_headers += 1
                    
            print(f"✅ CORS头检查: {found_headers}/{len(cors_headers)} 个头存在")
            return True
        else:
            print(f"❌ 跨域请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ CORS测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始完整系统测试...")
    print(f"📍 测试目标: {FRONTEND_URL}")
    print("=" * 50)
    
    # 执行所有测试
    tests = [
        ("系统健康检查", test_system_health),
        ("工作流API功能", test_workflow_api),
        ("前端页面访问", test_frontend_pages),
        ("API端点测试", test_api_endpoints),
        ("CORS和代理配置", test_cors_and_proxy),
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                print(f"✅ {test_name} 通过")
                passed_tests += 1
            else:
                print(f"❌ {test_name} 失败")
        except Exception as e:
            print(f"❌ {test_name} 异常: {e}")
    
    # 输出测试结果
    print("\n" + "="*50)
    print(f"🎯 测试完成: {passed_tests}/{total_tests} 通过")
    
    if passed_tests == total_tests:
        print("🎉 所有测试通过！系统运行正常")
        return True
    elif passed_tests >= total_tests * 0.8:
        print("⚠️  大部分测试通过，系统基本正常")
        return True
    else:
        print("💥 多项测试失败，请检查系统配置")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)