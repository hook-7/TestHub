#!/usr/bin/env python3
"""
测试工作流模板API
"""

import requests
import json

def test_api():
    base_url = "http://localhost:8000"
    
    print("🧪 测试工作流模板API")
    
    # 测试健康检查
    try:
        response = requests.get(f"{base_url}/api/v1/health")
        print(f"✅ 健康检查: {response.status_code}")
        if response.status_code == 200:
            print(f"   响应: {response.json()}")
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return
    
    # 测试工作流模板统计
    try:
        response = requests.get(f"{base_url}/api/v1/workflow-templates/stats")
        print(f"✅ 工作流模板统计: {response.status_code}")
        if response.status_code == 200:
            print(f"   响应: {response.json()}")
        else:
            print(f"   错误: {response.text}")
    except Exception as e:
        print(f"❌ 工作流模板统计失败: {e}")
    
    # 测试工作流模板列表
    try:
        response = requests.get(f"{base_url}/api/v1/workflow-templates/templates")
        print(f"✅ 工作流模板列表: {response.status_code}")
        if response.status_code == 200:
            print(f"   响应: {response.json()}")
        else:
            print(f"   错误: {response.text}")
    except Exception as e:
        print(f"❌ 工作流模板列表失败: {e}")
    
    # 测试命令列表
    try:
        response = requests.get(f"{base_url}/api/v1/commands/")
        print(f"✅ 命令列表: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   找到 {len(data.get('data', {}).get('commands', []))} 个命令")
        else:
            print(f"   错误: {response.text}")
    except Exception as e:
        print(f"❌ 命令列表失败: {e}")

if __name__ == "__main__":
    test_api()