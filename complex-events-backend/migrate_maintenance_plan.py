"""
数据库迁移脚本：检修计划模块
变更内容：
1. work_orders 表增加 plan_id 字段
2. 新建 maintenance_plans 表
"""
import sqlite3
import os
import shutil
from datetime import datetime


def backup_database(db_path):
    """备份数据库"""
    backup_path = db_path + f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    shutil.copy2(db_path, backup_path)
    print(f"数据库已备份到: {backup_path}")
    return backup_path


def migrate():
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'db.sqlite3')

    if not os.path.exists(db_path):
        print(f"错误：数据库文件不存在: {db_path}")
        return

    print(f"数据库路径: {db_path}")

    # 备份数据库
    backup_database(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # ============================================
        # 变更 1: work_orders 表增加 plan_id 字段
        # ============================================
        print("\n【变更 1】检查 work_orders 表是否已有 plan_id 字段...")
        cursor.execute("PRAGMA table_info(work_orders)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'plan_id' in columns:
            print("  plan_id 字段已存在，跳过添加")
        else:
            print("  添加 plan_id 字段...")
            cursor.execute("""
                ALTER TABLE work_orders
                ADD COLUMN plan_id INTEGER
            """)
            print("  ✅ plan_id 字段添加成功")

        # ============================================
        # 变更 2: 新建 maintenance_plans 表
        # ============================================
        print("\n【变更 2】检查 maintenance_plans 表是否已存在...")
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='maintenance_plans'
        """)

        if cursor.fetchone():
            print("  maintenance_plans 表已存在，跳过创建")
        else:
            print("  创建 maintenance_plans 表...")
            cursor.execute("""
                CREATE TABLE maintenance_plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plan_name VARCHAR(200) NOT NULL,
                    plan_scale VARCHAR(50),
                    status VARCHAR(50) DEFAULT '待开始',
                    initiator VARCHAR(100),
                    initiated_at DATETIME,
                    planned_start_time TEXT,
                    planned_end_time TEXT,
                    actual_start_time TEXT,
                    actual_end_time TEXT,
                    planned_man_hours REAL DEFAULT 0,
                    actual_man_hours REAL DEFAULT 0,
                    planned_cost REAL DEFAULT 0,
                    actual_cost REAL DEFAULT 0,
                    schedule_plan_id VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("  ✅ maintenance_plans 表创建成功")

        # 提交变更
        conn.commit()
        print("\n✅ 数据库迁移完成！")

        # 验证结果
        print("\n" + "=" * 60)
        print("变更验证")
        print("=" * 60)

        print("\n【work_orders 表字段列表】")
        cursor.execute("PRAGMA table_info(work_orders)")
        for row in cursor.fetchall():
            field_type = row[2] if row[2] else ''
            not_null = " NOT NULL" if row[3] else ''
            default = f" DEFAULT {row[4]}" if row[4] else ''
            print(f"  {row[1]:25s} {field_type}{not_null}{default}")

        print("\n【maintenance_plans 表字段列表】")
        cursor.execute("PRAGMA table_info(maintenance_plans)")
        for row in cursor.fetchall():
            field_type = row[2] if row[2] else ''
            not_null = " NOT NULL" if row[3] else ''
            default = f" DEFAULT {row[4]}" if row[4] else ''
            print(f"  {row[1]:25s} {field_type}{not_null}{default}")

        print("\n【数据库表列表】")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        for table in tables:
            marker = " ← 新增" if table == 'maintenance_plans' else ""
            print(f"  {table}{marker}")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ 迁移失败，已回滚: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
