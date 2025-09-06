#!/usr/bin/env python3
"""
测试数据库连接和数据查询
"""
import sys
import os
sys.path.append('/workspace/backend')

from app.core.database import engine, Command
from sqlmodel import Session, select

def test_database():
    print("Testing database connection...")
    
    try:
        with Session(engine) as session:
            # 查询所有指令
            commands = session.exec(select(Command)).all()
            print(f"Found {len(commands)} commands in database:")
            
            for cmd in commands:
                print(f"  ID: {cmd.id}")
                print(f"  Name: {cmd.name}")
                print(f"  Command: {cmd.command}")
                print(f"  Description: {cmd.description}")
                print(f"  Expected Response: {cmd.expected_response}")
                print(f"  Send as Hex: {cmd.send_as_hex}")
                print(f"  Show Notification: {cmd.show_notification}")
                print(f"  Target Serial ID: {cmd.target_serial_id}")
                print(f"  Created At: {cmd.created_at}")
                print("-" * 50)
                
    except Exception as e:
        print(f"Database test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_database()