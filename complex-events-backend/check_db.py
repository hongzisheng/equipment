import sqlite3

conn = sqlite3.connect(r'f:\化工\home\equipment\complex-events-backend\database\db.sqlite3')
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in c.fetchall()]
print("Tables:", tables)

for table in tables:
    c.execute(f"PRAGMA table_info({table})")
    columns = [col[1] for col in c.fetchall()]
    print(f"\nTable: {table}")
    print(f"Columns: {columns}")
    
    c.execute(f"SELECT COUNT(*) FROM {table}")
    count = c.fetchone()[0]
    print(f"Row count: {count}")
    
    if count > 0:
        c.execute(f"SELECT * FROM {table} LIMIT 1")
        row = c.fetchone()
        print(f"Sample row: {row}")

conn.close()
