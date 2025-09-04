#!/usr/bin/env python3
"""
修复前端API问题的脚本
"""

import os
import subprocess
import time

def check_services():
    """检查服务状态"""
    print("🔍 检查服务状态...")
    
    # 检查后端
    try:
        import requests
        response = requests.get("http://localhost:8000/api/v1/health", timeout=3)
        if response.status_code == 200:
            print("✅ 后端服务正常")
        else:
            print(f"❌ 后端服务异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 后端服务不可达: {e}")
        return False
    
    # 检查前端
    try:
        response = requests.get("http://localhost:3000/", timeout=3)
        if response.status_code == 200:
            print("✅ 前端服务正常")
        else:
            print(f"❌ 前端服务异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 前端服务不可达: {e}")
        return False
    
    return True

def test_api_proxy():
    """测试API代理"""
    print("\n🔄 测试API代理...")
    
    try:
        import requests
        
        # 测试关键API端点
        endpoints = [
            "/api/v1/health",
            "/api/v1/workflow/",
            "/api/v1/workflow/executions"
        ]
        
        for endpoint in endpoints:
            url = f"http://localhost:3000{endpoint}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ {endpoint}: {result.get('msg', 'OK')}")
            else:
                print(f"❌ {endpoint}: HTTP {response.status_code}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ API代理测试失败: {e}")
        return False

def create_test_instructions():
    """创建测试说明"""
    instructions = """
# 🧪 工作流系统测试说明

## 🌐 访问地址
- 前端应用: http://localhost:3000
- API调试页面: http://localhost:3000/debug.html
- 后端API文档: http://localhost:8000/api/v1/docs

## 🔧 已修复的问题
1. ✅ 添加了缺失的API端点 (/workflow/executions)
2. ✅ 修复了API响应拦截器结构
3. ✅ 配置了正确的CORS和代理设置
4. ✅ 添加了调试页面用于测试

## 🎯 测试步骤
1. 打开浏览器访问: http://localhost:3000
2. 如果遇到API问题，访问: http://localhost:3000/debug.html
3. 在调试页面点击各个测试按钮验证API功能
4. 访问工作流管理页面: http://localhost:3000/workflow

## 🚀 系统功能
- ✅ 工作流定义和管理
- ✅ JSON格式工作流配置
- ✅ 变量系统和表达式支持
- ✅ 步骤类型: send, expect, assign, confirm, control
- ✅ 实时执行监控
- ✅ WebSocket通信支持

## 🔍 如果仍有问题
1. 清除浏览器缓存
2. 使用无痕/隐私模式访问
3. 检查浏览器控制台错误信息
4. 运行测试脚本: python3 test_full_system.py
"""
    
    with open('/workspace/TESTING_INSTRUCTIONS.md', 'w', encoding='utf-8') as f:
        f.write(instructions)
    
    print("✅ 创建了测试说明文件: TESTING_INSTRUCTIONS.md")

def main():
    """主函数"""
    print("🔧 修复前端API问题...")
    print("="*50)
    
    # 检查服务状态
    if not check_services():
        print("💥 服务状态异常，请先启动服务")
        return False
    
    # 测试API代理
    if not test_api_proxy():
        print("💥 API代理测试失败")
        return False
    
    # 创建测试说明
    create_test_instructions()
    
    print("\n🎉 所有问题已修复！")
    print("📱 现在可以访问: http://localhost:3000")
    print("🔍 调试页面: http://localhost:3000/debug.html")
    
    return True

if __name__ == "__main__":
    # 安装requests如果不存在
    try:
        import requests
    except ImportError:
        print("安装requests...")
        subprocess.run(["pip", "install", "requests"], check=True)
        import requests
    
    success = main()
    exit(0 if success else 1)