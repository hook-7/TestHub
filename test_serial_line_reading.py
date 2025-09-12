#!/usr/bin/env python3
"""
测试串口行读取机制
验证新的基于行的串口读取是否正常工作
"""

import asyncio
import logging
import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.drivers.serial_driver import SerialDriver

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_line_reading():
    """测试基于行的串口读取"""
    driver = SerialDriver()
    
    # 设置数据回调函数
    received_lines = []
    
    async def data_callback(serial_id: int, data: bytes):
        """数据回调函数"""
        line = data.decode('utf-8', errors='ignore').strip()
        received_lines.append((serial_id, line))
        logger.info(f"Received line from serial {serial_id}: {repr(line)}")
    
    driver.set_data_callback(data_callback)
    
    try:
        # 获取可用端口
        ports = driver.get_available_ports()
        if not ports:
            logger.warning("No serial ports available for testing")
            return
        
        logger.info(f"Available ports: {[p['device'] for p in ports]}")
        
        # 尝试连接第一个可用端口
        test_port = ports[0]['device']
        logger.info(f"Testing with port: {test_port}")
        
        # 连接串口
        serial_id = await driver.connect(test_port, baudrate=115200)
        logger.info(f"Connected to serial port with ID: {serial_id}")
        
        # 等待一段时间让实时读取工作
        logger.info("Waiting for real-time data...")
        await asyncio.sleep(5)
        
        # 测试手动读取
        logger.info("Testing manual read...")
        try:
            manual_data = await driver.read_until(serial_id, b'\r\n', timeout=2.0)
            logger.info(f"Manual read result: {repr(manual_data)}")
        except Exception as e:
            logger.error(f"Manual read failed: {e}")
        
        # 测试发送AT命令
        logger.info("Testing AT command...")
        try:
            at_response = await driver.write_read_until(serial_id, b'AT\r\n', b'\r\n', timeout=2.0)
            logger.info(f"AT command response: {repr(at_response)}")
        except Exception as e:
            logger.error(f"AT command failed: {e}")
        
        # 显示接收到的所有行
        logger.info(f"Total lines received: {len(received_lines)}")
        for i, (sid, line) in enumerate(received_lines):
            logger.info(f"Line {i+1} (serial {sid}): {repr(line)}")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
    finally:
        # 断开连接
        try:
            await driver.disconnect()
            logger.info("Disconnected from serial port")
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")

if __name__ == "__main__":
    asyncio.run(test_line_reading())
