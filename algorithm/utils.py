import sqlite3
from pathlib import Path


def get_db_path():
    """统一获取数据库路径"""
    current_dir = Path(__file__).parent
    return current_dir.parent / 'database' / 'db.sqlite3'


def get_db_connection():
    """
    获取数据库连接对象
    :return:
    """
    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path))
    return conn
