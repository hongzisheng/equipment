from pathlib import Path
import sqlite3
import os

# 模拟 worker_blueprint.py 中的 get_db_path 逻辑
worker_file = r"c:\AAAPAN\File\HDU\pgs0 in sy\Chemical industry\equipment\complex-events-backend\app\blueprints\SchedulingdataManagement\worker_blueprint.py"
current_dir = Path(worker_file).parent.parent
db_path = current_dir / 'database' / 'db.sqlite3'
print(f"Calculated DB path: {db_path}")
print(f"Exists: {db_path.exists()}")

if db_path.exists():
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in c.fetchall()]
    print(f"Tables ({len(tables)}): {tables}")
    
    # 检查关键表
    for t in ['workers', 'equipment_types', 'equipment_instances', 'work_orders', 'work_order_tasks', 'process_templates', 'schedule_tasks']:
        if t in tables:
            c.execute(f"SELECT COUNT(*) FROM {t}")
            count = c.fetchone()[0]
            print(f"  {t}: {count} rows")
    conn.close()
else:
    # 搜索所有 sqlite3 文件
    backend_dir = r"c:\AAAPAN\File\HDU\pgs0 in sy\Chemical industry\equipment\complex-events-backend"
    for root, dirs, files in os.walk(backend_dir):
        for f in files:
            if f.endswith('.sqlite3') or f.endswith('.db'):
                print(f"Found DB: {os.path.join(root, f)}")
