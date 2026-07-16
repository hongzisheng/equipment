import os


class Config:
    """Application configuration for the retained pages."""

    _PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join(_PROJECT_ROOT, "assets", "file"))
    SUB_GRAPH_PATH = os.environ.get("SUB_GRAPH_PATH", os.path.join(_PROJECT_ROOT, "assets", "sub_graph"))
    LOG_DIR = os.environ.get("LOG_DIR", os.path.join(_PROJECT_ROOT, "assets", "logs"))

    LOGIN_USERNAME = os.environ.get("LOGIN_USERNAME", "admin")
    LOGIN_PASSWORD = os.environ.get("LOGIN_PASSWORD", "admin123")
    LOGIN_DISPLAY_NAME = os.environ.get("LOGIN_DISPLAY_NAME", "管理员")

    # SQLite: local document store to replace MongoDB.
    SQLITE_DB_PATH = os.environ.get("SQLITE_DB_PATH", os.path.join(_PROJECT_ROOT, "database", "db.sqlite3"))
    
    # Original project database path for process confirmation and info panel
    ORIGINAL_DB_PATH = os.environ.get("ORIGINAL_DB_PATH", r"F:\化工\Project\equipment\database\db.sqlite3")
    SQLITE_REPORTS_COLLECTION = os.environ.get("SQLITE_REPORTS_COLLECTION", "reports")
    SQLITE_EXTRACT_RESULT_COLLECTION = os.environ.get("SQLITE_EXTRACT_RESULT_COLLECTION", "extract_results")
    SQLITE_EVENT_LINK_COLLECTION = os.environ.get("SQLITE_EVENT_LINK_COLLECTION", "event_links")
    SQLITE_SUB_GRAPH_COLLECTION = os.environ.get("SQLITE_SUB_GRAPH_COLLECTION", "sub_graph")
    SQLITE_EVENT_LINK_RULES_COLLECTION = os.environ.get("SQLITE_EVENT_LINK_RULES_COLLECTION", "event_link_rules")

    # ---- 智能问答 DashScope（OpenAI 兼容接口）----
    DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY")
    DASHSCOPE_API_URL = os.environ.get(
        "DASHSCOPE_API_URL",
        "https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    CHAT_MODEL = os.environ.get("CHAT_MODEL", "qwen-flash")


class DevelopmentConfig(Config):
    DEBUG = True
    PORT = 8800

if __name__ == "__main__":
    print(Config.SQLITE_DB_PATH)
