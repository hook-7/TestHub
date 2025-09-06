#!/usr/bin/env python3
"""
测试API端点实现
"""
import sys
import os
sys.path.append('/workspace/backend')

from app.api.v1.endpoints.commands import get_all_commands
import asyncio

async def test_api_endpoint():
    print("Testing API endpoint directly...")
    
    try:
        result = await get_all_commands()
        print(f"API endpoint result: {result}")
        print(f"Result type: {type(result)}")
        if hasattr(result, 'data'):
            print(f"Data: {result.data}")
        if hasattr(result, 'msg'):
            print(f"Message: {result.msg}")
            
    except Exception as e:
        print(f"API endpoint test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api_endpoint())