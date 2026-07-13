import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from app.config import DevelopmentConfig
from app.utils.db import get_db_path, get_db_connection

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)

print("=== Current Working Directory ===")
print("os.getcwd():", os.getcwd())

print("\n=== Flask App Paths ===")
print("app.root_path:", app.root_path)
print("app.instance_path:", app.instance_path)

print("\n=== Database Path Analysis ===")
config_db_path = app.config.get("SQLITE_DB_PATH")
print("Config.SQLITE_DB_PATH:", config_db_path)
print("Is absolute:", os.path.isabs(config_db_path))

project_root = os.path.abspath(os.path.join(app.root_path, ".."))
absolute_db_path = os.path.normpath(os.path.join(project_root, config_db_path))
print("Calculated absolute path:", absolute_db_path)
print("Absolute path exists:", os.path.exists(absolute_db_path))

print("\n=== Testing get_db_path() ===")
db_path_from_utils = get_db_path()
print("get_db_path() returns:", db_path_from_utils)
print("Is absolute:", os.path.isabs(db_path_from_utils))

print("\n=== Testing get_db_connection() ===")
try:
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT 1")
        print("SUCCESS: Connected to database!")
except Exception as e:
    print(f"FAILED: {e}")

print("\n=== Testing with absolute path ===")
try:
    import sqlite3
    conn = sqlite3.connect(absolute_db_path)
    c = conn.cursor()
    c.execute("SELECT 1")
    print("SUCCESS: Connected with absolute path!")
    conn.close()
except Exception as e:
    print(f"FAILED: {e}")
