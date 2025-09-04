#!/usr/bin/env python3
"""
运行所有测试的主脚本
"""

import subprocess
import sys
import os

def run_test(test_file, description):
    """运行单个测试文件"""
    print(f"\n{'='*20} {description} {'='*20}")
    
    try:
        # 设置环境
        env = os.environ.copy()
        env['PYTHONPATH'] = os.path.join(os.getcwd(), 'backend')
        
        result = subprocess.run([
            'bash', '-c', 
            f'source $HOME/.local/bin/env && uv run python {test_file}'
        ], capture_output=True, text=True, env=env, timeout=60)
        
        if result.returncode == 0:
            print(f"✅ {description} 通过")
            print(result.stdout)
            return True
        else:
            print(f"❌ {description} 失败")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} 超时")
        return False
    except Exception as e:
        print(f"💥 {description} 异常: {e}")
        return False

def main():
    """主函数"""
    print("🧪 运行所有测试套件...")
    
    # 定义测试列表
    tests = [
        ("test_basic.py", "基础功能测试"),
        ("test_backend.py", "后端模块测试"),
        ("test_full_system.py", "完整系统测试"),
    ]
    
    passed = 0
    total = len(tests)
    
    # 运行所有测试
    for test_file, description in tests:
        if os.path.exists(test_file):
            if run_test(test_file, description):
                passed += 1
        else:
            print(f"⚠️  测试文件不存在: {test_file}")
    
    # 输出总结
    print("\n" + "="*60)
    print(f"🎯 测试总结: {passed}/{total} 个测试套件通过")
    
    if passed == total:
        print("🎉 所有测试套件通过！系统功能完整")
        
        # 输出系统信息
        print("\n📋 系统信息:")
        print("- 前端地址: http://localhost:3000")
        print("- 后端地址: http://localhost:8000")
        print("- API文档: http://localhost:8000/api/v1/docs")
        print("- 工作流管理: http://localhost:3000/workflow")
        
        return True
    else:
        print("💥 部分测试失败，请检查系统配置")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)