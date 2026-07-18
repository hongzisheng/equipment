"""数据库迁移脚本：将旧状态值迁移为新状态值

运行方式: python migrate_process_status.py
"""
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "database", "db.sqlite3")
DB_PATH = os.path.abspath(DB_PATH)

STATUS_MIGRATION_MAP = {
    "pending": "released",
    "on_hold": "pending_sign",
    "in_progress": "pending_engineer",
    "current": "pending_engineer",
    "confirmed": "completed",
    "rejected": "released",  # 已驳回的回退到待开始，需重新确认
}


def migrate():
    if not os.path.exists(DB_PATH):
        print(f"数据库不存在: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 查看当前状态分布
    print("当前状态分布:")
    cursor.execute(
        "SELECT status, COUNT(*) FROM work_order_tasks GROUP BY status"
    )
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} 条")

    # 执行迁移
    print("\n开始迁移...")
    for old_status, new_status in STATUS_MIGRATION_MAP.items():
        cursor.execute(
            "UPDATE work_order_tasks SET status = ? WHERE status = ?",
            (new_status, old_status),
        )
        count = cursor.rowcount
        if count > 0:
            print(f"  {old_status} → {new_status}: {count} 条")

    conn.commit()

    # 验证迁移后状态分布
    print("\n迁移后状态分布:")
    cursor.execute(
        "SELECT status, COUNT(*) FROM work_order_tasks GROUP BY status"
    )
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} 条")

    conn.close()
    print("\n迁移完成!")


if __name__ == "__main__":
    migrate()
