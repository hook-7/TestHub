#!/usr/bin/env python3
"""
Database Migration Script
用于管理数据库模式变更的简单迁移脚本
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import create_db_and_tables, engine
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def backup_database():
    """备份数据库文件"""
    db_file = settings.DATABASE_FILE
    if db_file.exists():
        backup_file = db_file.with_suffix(f'.backup_{int(datetime.now().timestamp())}')
        try:
            import shutil
            shutil.copy2(db_file, backup_file)
            logger.info(f"Database backed up to: {backup_file}")
            return backup_file
        except Exception as e:
            logger.error(f"Failed to backup database: {e}")
            return None
    return None


def migrate_database():
    """执行数据库迁移"""
    try:
        logger.info("Starting database migration...")

        # 备份现有数据库
        backup_file = backup_database()

        # 创建/更新表结构
        create_db_and_tables()

        logger.info("Database migration completed successfully!")

        if backup_file:
            logger.info(f"Original database backed up as: {backup_file}")

    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        if backup_file:
            logger.info(f"You can restore from backup: {backup_file}")
        sys.exit(1)


def reset_database():
    """重置数据库（删除所有数据并重新创建表）"""
    try:
        logger.warning("Resetting database - all data will be lost!")

        # 删除数据库文件
        db_file = settings.DATABASE_FILE
        if db_file.exists():
            db_file.unlink()
            logger.info(f"Deleted database file: {db_file}")

        # 重新创建表
        create_db_and_tables()
        logger.info("Database reset completed successfully!")

    except Exception as e:
        logger.error(f"Database reset failed: {e}")
        sys.exit(1)


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("Usage: python migrate_db.py <command>")
        print("Commands:")
        print("  migrate  - Migrate database to latest schema")
        print("  reset    - Reset database (WARNING: deletes all data)")
        print("  backup   - Create database backup")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "migrate":
        migrate_database()
    elif command == "reset":
        confirm = input("This will delete all data. Are you sure? (yes/no): ")
        if confirm.lower() == "yes":
            reset_database()
        else:
            logger.info("Operation cancelled")
    elif command == "backup":
        backup_file = backup_database()
        if backup_file:
            logger.info(f"Backup created: {backup_file}")
    else:
        logger.error(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
