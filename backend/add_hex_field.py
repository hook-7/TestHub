#!/usr/bin/env python3
"""
数据库迁移脚本：为commands表添加send_as_hex字段
"""

import sqlite3
import os
from pathlib import Path

def migrate_database():
    """为commands表添加send_as_hex字段"""
    
    # 数据库文件路径
    db_path = Path(__file__).parent.parent / "data" / "commands.db"
    
    if not db_path.exists():
        print(f"数据库文件不存在: {db_path}")
        return False
    
    try:
        # 连接数据库
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(commands)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'send_as_hex' in columns:
            print("字段 send_as_hex 已存在，无需添加")
            return True
        
        # 添加新字段
        print("正在添加 send_as_hex 字段...")
        cursor.execute("ALTER TABLE commands ADD COLUMN send_as_hex BOOLEAN DEFAULT 0")
        
        # 为现有记录设置默认值（虽然DEFAULT已经处理了，但为了确保一致性）
        cursor.execute("UPDATE commands SET send_as_hex = 0 WHERE send_as_hex IS NULL")
        
        # 提交更改
        conn.commit()
        
        # 验证字段是否添加成功
        cursor.execute("PRAGMA table_info(commands)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'send_as_hex' in columns:
            print("✅ 字段 send_as_hex 添加成功！")
            
            # 显示表结构
            print("\n当前表结构:")
            cursor.execute("PRAGMA table_info(commands)")
            for column in cursor.fetchall():
                print(f"  {column[1]} ({column[2]}) - {'NOT NULL' if column[3] else 'NULL'} - Default: {column[4]}")
            
            return True
        else:
            print("❌ 字段添加失败")
            return False
            
    except Exception as e:
        print(f"❌ 数据库操作失败: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("开始数据库迁移...")
    success = migrate_database()
    if success:
        print("\n🎉 数据库迁移完成！")
    else:
        print("\n💥 数据库迁移失败！")
