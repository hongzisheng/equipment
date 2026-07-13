"""数据库工具模块

提供统一的数据库路径获取和连接管理功能，
解决多个 blueprint 中重复定义 get_db_path 函数的问题，
同时提供安全的连接上下文管理器确保连接正确关闭。
"""
import os
import sqlite3
from contextlib import contextmanager
from typing import Generator, Any


def get_db_path() -> str:
    """获取 SQLite 数据库路径（确保返回绝对路径）"""
    from app.config import Config
    db_path = Config.SQLITE_DB_PATH
    if not os.path.isabs(db_path):
        from flask import current_app
        try:
            project_root = os.path.abspath(os.path.join(current_app.root_path, ".."))
            db_path = os.path.normpath(os.path.join(project_root, db_path))
        except RuntimeError:
            db_path = os.path.normpath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), db_path))
    return db_path


@contextmanager
def get_db_connection(row_factory: Any = None) -> Generator[sqlite3.Connection, None, None]:
    """获取数据库连接上下文管理器

    使用 with 语句管理连接，确保连接在退出时自动关闭，
    即使发生异常也能正确释放资源。

    Args:
        row_factory: 行工厂函数，如 sqlite3.Row

    Usage:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM table')
            rows = c.fetchall()
    """
    conn = None
    try:
        db_path = get_db_path()
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path, check_same_thread=False)
        if row_factory is not None:
            conn.row_factory = row_factory
        yield conn
    finally:
        if conn is not None:
            conn.close()
