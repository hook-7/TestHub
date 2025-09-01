#!/usr/bin/env python3
"""
Serial Port Test Tool
用于测试串口通信功能的独立工具
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.drivers.serial_driver import SerialDriver
from app.drivers.rs485_protocol import RS485Manager


async def main():
    print("🔧 Serial Port Test Tool")
    print("=" * 40)
    
    driver = SerialDriver()
    manager = RS485Manager(driver)
    
    # 1. 显示可用端口
    print("\n1. 可用串口:")
    ports = driver.get_available_ports()
    if not ports:
        print("   ❌ 没有找到可用串口")
        print("   💡 请检查:")
        print("      - 串口设备是否连接")
        print("      - 用户是否有串口权限 (sudo usermod -a -G dialout $USER)")
        return
    
    for i, port in enumerate(ports):
        print(f"   {i+1}. {port['device']} - {port['description']}")
    
    # 2. 自动检测
    print("\n2. 自动检测:")
    auto_port = driver.auto_detect_port()
    if auto_port:
        print(f"   ✅ 检测到: {auto_port}")
    else:
        print("   ⚠️ 未检测到USB串口设备")
    
    # 3. 提供测试选项
    print("\n3. 测试选项:")
    print("   a) 测试连接")
    print("   b) 模拟Modbus通信")
    print("   c) 原始数据测试")
    print("   q) 退出")
    
    while True:
        choice = input("\n请选择 (a/b/c/q): ").lower().strip()
        
        if choice == 'q':
            break
        elif choice == 'a':
            await test_connection(driver, ports)
        elif choice == 'b':
            await test_modbus(manager, ports)
        elif choice == 'c':
            await test_raw_data(driver, ports)
        else:
            print("无效选择，请重新输入")


async def test_connection(driver: SerialDriver, ports):
    """测试串口连接"""
    print("\n🔌 测试串口连接")
    
    if not ports:
        print("❌ 没有可用串口")
        return
    
    # 选择端口
    port_device = ports[0]['device']
    print(f"使用端口: {port_device}")
    
    try:
        # 尝试连接
        success = await driver.connect(port_device)
        if success:
            print("✅ 连接成功")
            
            # 显示连接信息
            info = driver.get_connection_info()
            print(f"配置: {info}")
            
            # 断开连接
            await driver.disconnect()
            print("🔌 已断开连接")
        else:
            print("❌ 连接失败")
    
    except Exception as e:
        print(f"❌ 连接异常: {e}")


async def test_modbus(manager: RS485Manager, ports):
    """测试Modbus通信"""
    print("\n📡 测试Modbus通信")
    
    if not ports:
        print("❌ 没有可用串口")
        return
    
    port_device = ports[0]['device']
    print(f"使用端口: {port_device}")
    
    try:
        # 连接
        success = await manager.driver.connect(port_device)
        if not success:
            print("❌ 连接失败")
            return
        
        print("✅ 连接成功，开始测试Modbus通信...")
        
        # 测试读取寄存器
        print("\n测试读取保持寄存器 (从站1, 地址0, 数量1):")
        result = await manager.read_registers(1, 0, 1)
        if result:
            print(f"✅ 读取成功: {result}")
        else:
            print("⚠️ 读取无响应 (可能设备未连接)")
        
        # 断开连接
        await manager.driver.disconnect()
        print("🔌 已断开连接")
        
    except Exception as e:
        print(f"❌ 测试异常: {e}")


async def test_raw_data(driver: SerialDriver, ports):
    """测试原始数据发送"""
    print("\n📤 测试原始数据发送")
    
    if not ports:
        print("❌ 没有可用串口")
        return
    
    port_device = ports[0]['device']
    print(f"使用端口: {port_device}")
    
    try:
        # 连接
        success = await driver.connect(port_device)
        if not success:
            print("❌ 连接失败")
            return
        
        print("✅ 连接成功")
        
        # 发送测试数据 (Modbus读取命令)
        test_data = bytes.fromhex("01 03 00 00 00 01 84 0A")
        print(f"发送数据: {test_data.hex().upper()}")
        
        response = await driver.write_read(test_data, read_timeout=2.0)
        print(f"接收数据: {response.hex().upper()}")
        
        if response:
            print("✅ 数据收发成功")
        else:
            print("⚠️ 无响应数据")
        
        # 断开连接
        await driver.disconnect()
        print("🔌 已断开连接")
        
    except Exception as e:
        print(f"❌ 测试异常: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 测试工具已退出")
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")