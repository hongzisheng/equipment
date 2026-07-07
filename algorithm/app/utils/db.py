"""数据库路径与连接工具

统一所有模块对 SQLite 数据库的访问入口。
数据库路径由 app.config.Config 集中管理。
"""
import sqlite3

from app.config import Config


def get_db_path():
    """统一获取数据库路径"""
    return Config.DB_PATH


def get_db_connection():
    """获取数据库连接对象"""
    conn = sqlite3.connect(str(Config.DB_PATH))
    return conn
