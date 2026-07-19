"""
数据库迁移脚本：调度方案多版本管理
变更内容：
1. 新建 schedule_plans 表（调度方案注册表，每次生成调度方案都新增一条记录）
2. schedule_tasks 表增加 schedule_plan_id 字段（关联到方案注册表，实现按方案隔离）
3. maintenance_plans.schedule_plan_id 语义对齐到 schedule_plans.id（当前生效方案）

设计说明（业界标准做法）：
- 不采用"每次动态建表"，避免表数量无限增长、SQL 注入、schema 难维护等问题
- 采用"单表 + 方案标识字段"：所有调度任务统一存 schedule_tasks，通过 schedule_plan_id 区分不同方案
- schedule_plans 作为方案注册表，记录每次调度的元信息（算法、统计、关联检修计划等）
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
        # 变更 1: 新建 schedule_plans 表（调度方案注册表）
        # ============================================
        print("\n【变更 1】检查 schedule_plans 表是否已存在...")
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='schedule_plans'
        """)

        if cursor.fetchone():
            print("  schedule_plans 表已存在，跳过创建")
        else:
            print("  创建 schedule_plans 表...")
            cursor.execute("""
                CREATE TABLE schedule_plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plan_id INTEGER,
                    schedule_name VARCHAR(200) NOT NULL,
                    algorithm VARCHAR(50),
                    status VARCHAR(50) DEFAULT '生效中',
                    work_order_ids TEXT,
                    project_start_datetime TEXT,
                    statistics TEXT,
                    total_tasks INTEGER DEFAULT 0,
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (plan_id) REFERENCES maintenance_plans(id)
                )
            """)
            print("  [OK] schedule_plans 表创建成功")

        # ============================================
        # 变更 2: schedule_tasks 表增加 schedule_plan_id 字段
        # ============================================
        print("\n【变更 2】检查 schedule_tasks 表是否已有 schedule_plan_id 字段...")
        cursor.execute("PRAGMA table_info(schedule_tasks)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'schedule_plan_id' in columns:
            print("  schedule_plan_id 字段已存在，跳过添加")
        else:
            print("  添加 schedule_plan_id 字段...")
            cursor.execute("""
                ALTER TABLE schedule_tasks
                ADD COLUMN schedule_plan_id INTEGER
            """)
            print("  [OK] schedule_plan_id 字段添加成功")

        # 为 schedule_plan_id 创建索引，加速按方案查询
        print("\n【变更 3】检查 schedule_tasks.schedule_plan_id 索引...")
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND name='idx_schedule_tasks_plan_id'
        """)
        if not cursor.fetchone():
            cursor.execute("""
                CREATE INDEX idx_schedule_tasks_plan_id
                ON schedule_tasks(schedule_plan_id)
            """)
            print("  [OK] 索引 idx_schedule_tasks_plan_id 创建成功")
        else:
            print("  索引已存在，跳过")

        # 提交变更
        conn.commit()
        print("\n[OK] 数据库迁移完成！")

        # 验证结果
        print("\n" + "=" * 60)
        print("变更验证")
        print("=" * 60)

        print("\n【schedule_plans 表字段列表】")
        cursor.execute("PRAGMA table_info(schedule_plans)")
        for row in cursor.fetchall():
            print(f"  {row[1]:30s} {row[2] or ''}")

        print("\n【schedule_tasks 表字段列表】")
        cursor.execute("PRAGMA table_info(schedule_tasks)")
        for row in cursor.fetchall():
            marker = " ← 新增" if row[1] == 'schedule_plan_id' else ""
            print(f"  {row[1]:30s} {row[2] or ''}{marker}")

    except Exception as e:
        conn.rollback()
        print(f"\n[X] 迁移失败，已回滚: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
