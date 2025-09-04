#!/usr/bin/env python3
"""
测试所有API端点
"""

import requests
import json

def test_api_endpoint(method, url, description, data=None):
    """测试单个API端点"""
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        else:
            return False, f"不支持的HTTP方法: {method}"
        
        if response.status_code == 200:
            try:
                result = response.json()
                return True, f"✅ {description}: {result.get('msg', 'OK')}"
            except:
                return True, f"✅ {description}: HTTP 200"
        else:
            return False, f"❌ {description}: HTTP {response.status_code}"
            
    except Exception as e:
        return False, f"❌ {description}: {str(e)}"

def main():
    print("🧪 测试所有API端点...")
    print("="*60)
    
    # 测试两个地址
    base_urls = [
        "http://localhost:8000/api/v1",
        "http://localhost:3000/api/v1"
    ]
    
    # 测试的端点
    endpoints = [
        ("GET", "/health", "健康检查"),
        ("GET", "/workflow/", "工作流列表"),
        ("GET", "/workflow/test", "工作流测试"),
        ("GET", "/workflow/executions", "执行列表"),
        ("GET", "/workflow/execution/test_123", "执行详情"),
        ("POST", "/workflow/", "创建工作流", {"name": "测试工作流", "steps": []}),
    ]
    
    for base_url in base_urls:
        print(f"\n📍 测试地址: {base_url}")
        print("-" * 40)
        
        success_count = 0
        total_count = len(endpoints)
        
        for method, endpoint, description, *data in endpoints:
            url = base_url + endpoint
            test_data = data[0] if data else None
            
            success, message = test_api_endpoint(method, url, description, test_data)
            print(message)
            
            if success:
                success_count += 1
        
        print(f"\n📊 结果: {success_count}/{total_count} 成功")
        print(f"成功率: {success_count/total_count*100:.1f}%")

if __name__ == "__main__":
    main()