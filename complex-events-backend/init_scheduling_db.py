"""调度模块数据库初始化脚本

创建工单和调度生成所需的所有数据库表，并从 algorithm 分支数据库复制种子数据。
运行方式: python init_scheduling_db.py
"""
import os
import sqlite3
import sys

# 数据库路径
MAIN_DB = os.path.join(os.path.dirname(__file__), "database", "db.sqlite3")
ALGO_DB = os.path.join(
    os.path.dirname(__file__), "..", "..", "equipment-algorithm", "database", "db.sqlite3"
)

# 确保使用绝对路径
MAIN_DB = os.path.abspath(MAIN_DB)
ALGO_DB = os.path.abspath(ALGO_DB)


# ==================== 建表 SQL ====================

CREATE_TABLES = [
    # 设备分类
    """CREATE TABLE IF NOT EXISTS equipment_category (
        category_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_name VARCHAR(50) NOT NULL UNIQUE,
        description TEXT
    )""",

    # 设备类型
    """CREATE TABLE IF NOT EXISTS equipment_types (
        id TEXT NOT NULL PRIMARY KEY,
        name TEXT NOT NULL,
        created_at TEXT,
        updated_at TEXT,
        category TEXT
    )""",

    # 设备实例
    """CREATE TABLE IF NOT EXISTS equipment_instances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        equipment_type_id VARCHAR(50) NOT NULL,
        name VARCHAR(200) NOT NULL UNIQUE,
        status VARCHAR(20) DEFAULT 'active',
        created_time TEXT,
        category TEXT,
        equipment_type_name TEXT,
        FOREIGN KEY (equipment_type_id) REFERENCES equipment_types(id)
    )""",

    # 选中设备
    """CREATE TABLE IF NOT EXISTS selected_equipments (
        id INTEGER PRIMARY KEY,
        name VARCHAR NOT NULL,
        equipment_type_id VARCHAR NOT NULL,
        equipment_type_name TEXT,
        category TEXT,
        created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",

    # 工种
    """CREATE TABLE IF NOT EXISTS worker_types (
        id VARCHAR(50) PRIMARY KEY,
        name VARCHAR(50) NOT NULL,
        description TEXT,
        requires_certification BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        price REAL DEFAULT 0
    )""",

    # 工人
    """CREATE TABLE IF NOT EXISTS workers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        worker_type_id TEXT NOT NULL,
        name TEXT NOT NULL,
        status TEXT DEFAULT 0,
        is_certified INTEGER DEFAULT 0,
        created_time TEXT,
        organization TEXT,
        emp_id INTEGER,
        compose TEXT,
        skill_level INTEGER DEFAULT 1,
        FOREIGN KEY (worker_type_id) REFERENCES worker_types(id)
    )""",

    # 选中工人
    """CREATE TABLE IF NOT EXISTS selected_workers (
        id INTEGER PRIMARY KEY,
        worker_type_id TEXT NOT NULL,
        name TEXT NOT NULL,
        status TEXT DEFAULT 0,
        is_certified INTEGER DEFAULT 0,
        created_time TEXT,
        organization TEXT,
        compose TEXT
    )""",

    # 工人池
    """CREATE TABLE IF NOT EXISTS worker_team (
        workerteam_type TEXT,
        total INTEGER,
        assigned INTEGER
    )""",

    # 工序模板
    """CREATE TABLE IF NOT EXISTS process_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        equipment_type_id TEXT,
        process_code TEXT,
        description TEXT,
        estimated_hours REAL,
        required_workers TEXT,
        predecessor_codes TEXT,
        parent_process_code TEXT,
        is_major_process INTEGER,
        material_requirements TEXT,
        tools_requirements TEXT,
        material_price NUMBER,
        tools_price NUMBER,
        worker_price REAL
    )""",

    # 工单
    """CREATE TABLE IF NOT EXISTS work_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_number VARCHAR(50) NOT NULL UNIQUE,
        title VARCHAR(200) NOT NULL,
        equipment_id INTEGER NOT NULL,
        equipment_name VARCHAR(100) NOT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'pending',
        created_by INTEGER,
        created_at DATETIME DEFAULT (DATETIME('now', 'localtime')),
        scheduled_start_time TEXT,
        scheduled_end_time TEXT,
        actual_start_time TEXT,
        actual_end_time TEXT,
        priority VARCHAR(10) NOT NULL DEFAULT 'medium',
        remarks TEXT,
        FOREIGN KEY (equipment_id) REFERENCES equipment_instances(id)
    )""",

    # 工单任务
    """CREATE TABLE IF NOT EXISTS work_order_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        work_order_id INTEGER NOT NULL,
        task_code VARCHAR(50),
        process_id VARCHAR(100) NOT NULL,
        process_code VARCHAR(100),
        process_name VARCHAR(200) NOT NULL,
        equipment_id INTEGER NOT NULL,
        equipment_name VARCHAR(100) NOT NULL,
        description TEXT,
        estimated_hours REAL,
        scheduled_start_time TEXT,
        scheduled_end_time TEXT,
        actual_start_time TEXT,
        actual_end_time TEXT,
        status VARCHAR(20) NOT NULL DEFAULT 'pending',
        predecessor_task_ids TEXT,
        is_milestone BOOLEAN NOT NULL DEFAULT 0,
        material_requirements TEXT,
        tools_requirements TEXT,
        workers TEXT NOT NULL DEFAULT '[]',
        approver_id INTEGER,
        approval_comments TEXT,
        approved_at DATETIME,
        created_at DATETIME DEFAULT (DATETIME('now', 'localtime')),
        updated_at DATETIME DEFAULT (DATETIME('now', 'localtime')),
        attachment_path TEXT,
        FOREIGN KEY (work_order_id) REFERENCES work_orders(id) ON DELETE CASCADE,
        FOREIGN KEY (equipment_id) REFERENCES equipment_instances(id)
    )""",

    # 调度任务
    """CREATE TABLE IF NOT EXISTS schedule_tasks (
        schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
        process_id TEXT NOT NULL,
        process_name TEXT NOT NULL,
        equipment_id INTEGER NOT NULL,
        equipment_name TEXT NOT NULL,
        equipment_type_id TEXT,
        equipment_type_name TEXT,
        equipment_category TEXT,
        start_time REAL NOT NULL,
        end_time REAL NOT NULL,
        start_time_formatted TEXT NOT NULL,
        end_time_formatted TEXT NOT NULL,
        duration_days REAL NOT NULL,
        workers TEXT,
        predecessors TEXT
    )""",

    # 任务操作日志
    """CREATE TABLE IF NOT EXISTS task_operation_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        user_id INTEGER,
        operation_type VARCHAR(50) NOT NULL,
        description TEXT,
        attachment_path VARCHAR(255),
        old_status VARCHAR(50),
        new_status VARCHAR(50),
        approval_comments TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (task_id) REFERENCES work_order_tasks(id) ON DELETE CASCADE
    )""",

    # 工单任务工人关联
    """CREATE TABLE IF NOT EXISTS work_order_task_workers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        worker_id INTEGER NOT NULL,
        worker_name VARCHAR(100) NOT NULL,
        worker_type VARCHAR(50),
        status VARCHAR(20) NOT NULL DEFAULT 'assigned',
        completion_note TEXT,
        completed_at DATETIME,
        created_at DATETIME DEFAULT (DATETIME('now', 'localtime')),
        FOREIGN KEY (task_id) REFERENCES work_order_tasks(id) ON DELETE CASCADE,
        FOREIGN KEY (worker_id) REFERENCES workers(id)
    )""",
]


# ==================== 种子数据表（从 algorithm 分支复制） ====================

SEED_TABLES = [
    "equipment_category",
    "equipment_types",
    "worker_types",
    "process_templates",
    "workers",
    "equipment_instances",
    "worker_team",
]


def create_tables(db_path):
    """创建所有表"""
    print(f"正在创建表于: {db_path}")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    for sql in CREATE_TABLES:
        c.execute(sql)
    conn.commit()
    conn.close()
    print("  表创建完成")


def copy_seed_data(main_db, algo_db):
    """从 algorithm 分支数据库复制种子数据"""
    if not os.path.exists(algo_db):
        print(f"  警告: algorithm 分支数据库不存在: {algo_db}")
        print("  跳过种子数据复制。表已创建但为空。")
        return

    print(f"正在从 algorithm 分支复制种子数据: {algo_db}")
    src_conn = sqlite3.connect(algo_db)
    src_c = src_conn.cursor()

    dst_conn = sqlite3.connect(main_db)
    dst_c = dst_conn.cursor()

    for table in SEED_TABLES:
        try:
            # 获取源表列名
            src_c.execute(f"PRAGMA table_info({table})")
            src_cols = [col[1] for col in src_c.fetchall()]

            # 获取目标表列名
            dst_c.execute(f"PRAGMA table_info({table})")
            dst_cols = [col[1] for col in dst_c.fetchall()]

            # 只复制两边都存在的列
            common_cols = [c for c in src_cols if c in dst_cols]
            if not common_cols:
                print(f"  {table}: 无匹配列，跳过")
                continue

            # 读取源表数据（只读公共列）
            col_str = ",".join(f'"{c}"' for c in common_cols)
            src_c.execute(f'SELECT {col_str} FROM {table}')
            rows = src_c.fetchall()
            if not rows:
                print(f"  {table}: 源表无数据，跳过")
                continue

            placeholders = ",".join("?" for _ in common_cols)

            # 清空目标表
            dst_c.execute(f"DELETE FROM {table}")

            # 插入数据
            inserted = 0
            for row in rows:
                try:
                    dst_c.execute(
                        f'INSERT INTO {table} ({col_str}) VALUES ({placeholders})', row
                    )
                    inserted += 1
                except Exception:
                    pass

            print(f"  {table}: 复制了 {inserted}/{len(rows)} 行")
        except Exception as e:
            print(f"  {table}: 复制失败 - {e}")

    dst_conn.commit()
    dst_conn.close()
    src_conn.close()
    print("  种子数据复制完成")


def main():
    print("=" * 60)
    print("调度模块数据库初始化")
    print("=" * 60)
    print(f"主数据库 (main): {MAIN_DB}")
    print(f"源数据库 (algorithm): {ALGO_DB}")
    print()

    # 1. 创建表
    create_tables(MAIN_DB)

    # 2. 复制种子数据
    copy_seed_data(MAIN_DB, ALGO_DB)

    # 3. 验证
    print("\n验证表结构:")
    conn = sqlite3.connect(MAIN_DB)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [t[0] for t in c.fetchall()]
    print(f"  所有表: {tables}")

    for table in SEED_TABLES + ["work_orders", "work_order_tasks", "schedule_tasks"]:
        if table in tables:
            c.execute(f"SELECT COUNT(*) FROM {table}")
            count = c.fetchone()[0]
            print(f"  {table}: {count} 行")
    conn.close()

    print("\n初始化完成！")


if __name__ == "__main__":
    main()
