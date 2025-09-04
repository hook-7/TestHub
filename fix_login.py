#!/usr/bin/env python3
"""
一键修复登录问题脚本
"""

import requests
import time

def fix_login_issues():
    """修复登录问题"""
    print("🔧 正在修复登录问题...")
    
    base_url = "http://localhost:3000/api/v1"
    
    try:
        # 1. 检查系统状态
        print("1. 检查系统状态...")
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 系统运行正常")
        else:
            print("❌ 系统异常，请检查服务是否启动")
            return False
        
        # 2. 强制清理所有会话
        print("2. 强制清理所有会话...")
        response = requests.post(f"{base_url}/session/force-cleanup", json={}, timeout=5)
        if response.status_code == 200:
            result = response.json()
            cleaned_count = result.get('data', {}).get('cleaned_count', 0)
            print(f"✅ 清理了 {cleaned_count} 个会话")
        else:
            print("❌ 会话清理失败")
            return False
        
        # 3. 测试创建新会话
        print("3. 测试创建新会话...")
        test_session_data = {
            "client_info": "Fix Login Test Client"
        }
        
        response = requests.post(f"{base_url}/session/create", json=test_session_data, timeout=5)
        if response.status_code == 200:
            result = response.json()
            session_id = result.get('data', {}).get('session_id')
            print(f"✅ 测试会话创建成功: {session_id}")
            
            # 4. 验证会话
            print("4. 验证测试会话...")
            validate_data = {"session_id": session_id}
            response = requests.post(f"{base_url}/session/validate", json=validate_data, timeout=5)
            if response.status_code == 200:
                print("✅ 会话验证成功")
            else:
                print("❌ 会话验证失败")
                return False
                
        else:
            print("❌ 测试会话创建失败")
            return False
        
        print("\n🎉 登录问题修复完成！")
        print("📱 现在可以正常登录: http://localhost:3000")
        return True
        
    except Exception as e:
        print(f"❌ 修复过程中出现错误: {e}")
        return False

def show_usage_instructions():
    """显示使用说明"""
    print("\n" + "="*50)
    print("🎯 登录问题解决方案")
    print("="*50)
    print()
    print("🌐 访问地址:")
    print("- 主应用: http://localhost:3000")
    print("- 登录测试: http://localhost:3000/login-test.html")
    print("- API调试: http://localhost:3000/debug.html")
    print()
    print("🔧 如果仍然无法登录:")
    print("1. 访问登录测试页面进行诊断")
    print("2. 点击'强制清理所有会话'按钮")
    print("3. 清除浏览器缓存并刷新")
    print("4. 重新尝试登录")
    print()
    print("🆘 紧急恢复:")
    print("重启后端服务: pkill -f python && uv run python backend/start.py")

if __name__ == "__main__":
    print("🚀 开始修复登录问题...")
    
    if fix_login_issues():
        show_usage_instructions()
    else:
        print("💥 修复失败，请检查服务状态")
        print("🔍 建议访问: http://localhost:3000/login-test.html 进行诊断")