import sqlite3
import os

db_path = r'f:\化工\home\equipment\complex-events-backend\database\db.sqlite3'

print(f"数据库路径: {db_path}")
print(f"文件存在: {os.path.exists(db_path)}")
print(f"文件大小: {os.path.getsize(db_path)} bytes")
print(f"文件可读: {os.access(db_path, os.R_OK)}")
print(f"文件可写: {os.access(db_path, os.W_OK)}")
print(f"目录可写: {os.access(os.path.dirname(db_path), os.W_OK)}")

try:
    print("\n尝试直接连接数据库...")
    conn = sqlite3.connect(db_path)
    print("连接成功!")
    
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"表数量: {len(tables)}")
    print(f"表名: {tables[:10]}")
    
    cursor.execute("SELECT COUNT(*) FROM workers")
    count = cursor.fetchone()[0]
    print(f"workers表记录数: {count}")
    
    conn.close()
    print("连接已关闭")
    
except Exception as e:
    print(f"连接失败: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n尝试使用Config获取路径...")
try:
    from app.config import Config
    config_path = Config.SQLITE_DB_PATH
    print(f"Config.SQLITE_DB_PATH: {config_path}")
    print(f"绝对路径: {os.path.abspath(config_path)}")
    print(f"路径存在: {os.path.exists(config_path)}")
    
    conn = sqlite3.connect(config_path)
    print("使用Config路径连接成功!")
    conn.close()
except Exception as e:
    print(f"使用Config路径连接失败: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
