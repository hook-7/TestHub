#!/usr/bin/env python3
"""
基础功能测试脚本
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_imports():
    """测试模块导入"""
    print("🧪 测试模块导入...")
    
    try:
        from app.schemas.workflow_schemas import WorkflowDefinition, WorkflowStep
        print("✅ 工作流模式导入成功")
    except Exception as e:
        print(f"❌ 工作流模式导入失败: {e}")
        return False
    
    try:
        from app.services.workflow_service import WorkflowService, VariableContext
        print("✅ 工作流服务导入成功")
    except Exception as e:
        print(f"❌ 工作流服务导入失败: {e}")
        return False
    
    try:
        from app.core.exceptions import WorkflowError, ValidationError
        print("✅ 异常类导入成功")
    except Exception as e:
        print(f"❌ 异常类导入失败: {e}")
        return False
    
    return True

def test_variable_context():
    """测试变量上下文"""
    print("\n🧪 测试变量上下文...")
    
    try:
        from app.services.workflow_service import VariableContext
        
        # 创建上下文
        context = VariableContext({"test_var": "hello", "number": 42})
        
        # 测试变量设置和获取
        context.set_variable("new_var", "world")
        assert context.get_variable("test_var") == "hello"
        assert context.get_variable("new_var") == "world"
        print("✅ 变量设置和获取成功")
        
        # 测试表达式求值
        result = context.evaluate_expression("test_var + ' ' + new_var")
        assert result == "hello world"
        print("✅ 字符串表达式求值成功")
        
        result = context.evaluate_expression("number * 2")
        assert result == 84
        print("✅ 数值表达式求值成功")
        
        # 测试逻辑表达式
        result = context.evaluate_expression("number > 40 and test_var == 'hello'")
        assert result == True
        print("✅ 逻辑表达式求值成功")
        
        # 测试正则表达式
        context.set_variable("reply", "OK ID=12345 STATUS=READY")
        result = context.evaluate_expression("re.search(r'ID=(\\d+)', reply).group(1)")
        assert result == "12345"
        print("✅ 正则表达式提取成功")
        
        # 测试变量替换
        template = "Device ${test_var} has ID ${device_id}"
        context.set_variable("device_id", "67890")
        result = context.substitute_variables(template)
        expected = "Device hello has ID 67890"
        assert result == expected
        print("✅ 变量替换成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 变量上下文测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_workflow_parsing():
    """测试工作流解析"""
    print("\n🧪 测试工作流解析...")
    
    try:
        from app.services.workflow_service import WorkflowService
        from app.services.serial_service import SerialService
        
        # 创建模拟的串口服务
        class MockSerialService:
            async def send_command(self, session_id, command):
                class MockResponse:
                    data = f"Mock response for: {command}"
                return MockResponse()
        
        # 创建工作流服务
        mock_serial = MockSerialService()
        workflow_service = WorkflowService(mock_serial)
        
        # 测试工作流数据
        workflow_data = {
            "name": "测试工作流",
            "description": "用于测试的简单工作流",
            "variables": {"device_id": "", "status": ""},
            "steps": [
                {
                    "id": "step_1",
                    "name": "发送状态查询",
                    "type": "send",
                    "command": "AT+STATUS?",
                    "delay": 1.0
                },
                {
                    "id": "step_2",
                    "name": "期望OK回复",
                    "type": "expect",
                    "expect_type": "string",
                    "pattern": "OK",
                    "timeout": 5.0
                },
                {
                    "id": "step_3",
                    "name": "提取设备ID",
                    "type": "assign",
                    "variable": "device_id",
                    "expression": "'test_device_123'"
                }
            ]
        }
        
        # 创建工作流
        workflow = workflow_service.create_workflow(workflow_data)
        assert workflow.name == "测试工作流"
        assert len(workflow.steps) == 3
        print("✅ 工作流创建成功")
        
        # 测试步骤解析
        assert workflow.steps[0].type == "send"
        assert workflow.steps[1].type == "expect"
        assert workflow.steps[2].type == "assign"
        print("✅ 工作流步骤解析成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 工作流解析测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 开始基础功能测试...")
    
    tests = [
        test_imports,
        test_variable_context,
        test_workflow_parsing
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
        print("🎉 所有基础功能测试通过！")
        return True
    else:
        print("💥 部分测试失败，请检查代码")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)