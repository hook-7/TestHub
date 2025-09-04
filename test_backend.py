#!/usr/bin/env python3
"""
后端服务测试脚本
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_backend_imports():
    """测试后端模块导入"""
    print("🧪 测试后端模块导入...")
    
    try:
        from app.main import app
        print("✅ 主应用导入成功")
    except Exception as e:
        print(f"❌ 主应用导入失败: {e}")
        return False
    
    try:
        from app.api.v1 import api_router
        print("✅ API路由导入成功")
    except Exception as e:
        print(f"❌ API路由导入失败: {e}")
        return False
    
    try:
        from app.api.v1.endpoints.workflow import router as workflow_router
        print("✅ 工作流路由导入成功")
    except Exception as e:
        print(f"❌ 工作流路由导入失败: {e}")
        return False
    
    return True

def test_api_routes():
    """测试API路由配置"""
    print("\n🧪 测试API路由配置...")
    
    try:
        from app.main import app
        
        # 获取路由信息
        routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                routes.append(route.path)
        
        print(f"✅ 发现 {len(routes)} 个路由")
        
        # 检查关键路由
        expected_routes = ['/api/v1/workflow/', '/api/v1/health']
        for expected in expected_routes:
            found = any(expected in route for route in routes)
            if found:
                print(f"✅ 发现路由: {expected}")
            else:
                print(f"❌ 缺少路由: {expected}")
        
        return True
        
    except Exception as e:
        print(f"❌ 路由配置测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始后端服务测试...")
    
    tests = [
        test_backend_imports,
        test_api_routes
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ 测试失败: {test.__name__}")
        except Exception as e:
            print(f"❌ 测试异常: {test.__name__}: {e}")
    
    print(f"\n🎯 测试完成: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 后端服务测试通过！")
        return True
    else:
        print("💥 后端服务测试失败，请检查代码")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)