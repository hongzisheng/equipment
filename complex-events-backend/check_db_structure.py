import sqlite3

conn = sqlite3.connect('database/db.sqlite3')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cursor.fetchall()]
print("Tables:", tables)

print("\n=== Table Structures ===")
for table in tables:
    print(f"\n--- {table} ---")
    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]} ({col[2]}){' [PK]' if col[5] == 1 else ''}")
    
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"  Rows: {count}")
    
    if count > 0:
        cursor.execute(f"SELECT * FROM {table} LIMIT 2")
        sample = cursor.fetchall()
        print(f"  Sample data:")
        for row in sample:
            print(f"    {row}")

conn.close()