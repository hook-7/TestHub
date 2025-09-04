#!/usr/bin/env python3
"""
测试前端API调用
"""

import requests
import json

def test_frontend_api():
    """测试前端API调用"""
    print("🧪 测试前端API数据结构...")
    
    base_url = "http://localhost:3000/api/v1"
    
    # 测试工作流列表
    print("\n1. 测试工作流列表API...")
    try:
        response = requests.get(f"{base_url}/workflow/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API响应成功")
            print(f"   响应结构: {list(data.keys())}")
            
            if 'data' in data and 'workflows' in data['data']:
                workflows = data['data']['workflows']
                print(f"✅ workflows字段存在: {len(workflows)} 个工作流")
            else:
                print(f"❌ workflows字段缺失")
                print(f"   实际结构: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ API请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    
    # 测试执行列表
    print("\n2. 测试执行列表API...")
    try:
        response = requests.get(f"{base_url}/workflow/executions", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API响应成功")
            print(f"   响应结构: {list(data.keys())}")
            
            if 'data' in data and 'executions' in data['data']:
                executions = data['data']['executions']
                print(f"✅ executions字段存在: {len(executions)} 个执行记录")
            else:
                print(f"❌ executions字段缺失")
                print(f"   实际结构: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ API请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

    # 测试创建工作流
    print("\n3. 测试创建工作流API...")
    try:
        test_workflow = {
            "name": "前端测试工作流",
            "description": "用于测试前端API的工作流",
            "steps": []
        }
        
        response = requests.post(
            f"{base_url}/workflow/", 
            json=test_workflow,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 创建工作流成功")
            print(f"   工作流ID: {data.get('data', {}).get('id', 'N/A')}")
            print(f"   工作流名称: {data.get('data', {}).get('name', 'N/A')}")
        else:
            print(f"❌ 创建工作流失败: {response.status_code}")
            print(f"   响应内容: {response.text}")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_frontend_api()