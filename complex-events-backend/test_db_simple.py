import sqlite3
import os

os.chdir(r"f:\化工\home\equipment\complex-events-backend")

print("Current directory:", os.getcwd())
print("Database path:", os.path.join("database", "db.sqlite3"))
print("Exists:", os.path.exists(os.path.join("database", "db.sqlite3")))

try:
    conn = sqlite3.connect(os.path.join("database", "db.sqlite3"))
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in c.fetchall()]
    print("Tables:", tables)
    conn.close()
    print("Connection successful!")
except Exception as e:
    print("Error:", e)
