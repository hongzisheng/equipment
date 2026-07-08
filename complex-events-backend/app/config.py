import os


class Config:
    """Application configuration for the retained pages."""

    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join("assets", "file"))
    SUB_GRAPH_PATH = os.environ.get("SUB_GRAPH_PATH", os.path.join("assets", "sub_graph"))
    LOG_DIR = os.environ.get("LOG_DIR", os.path.join("assets", "logs"))

    LOGIN_USERNAME = os.environ.get("LOGIN_USERNAME", "admin")
    LOGIN_PASSWORD = os.environ.get("LOGIN_PASSWORD", "admin123")
    LOGIN_DISPLAY_NAME = os.environ.get("LOGIN_DISPLAY_NAME", "管理员")

    # SQLite: local document store to replace MongoDB.
    SQLITE_DB_PATH = os.environ.get("SQLITE_DB_PATH", os.path.join("database", "db.sqlite3"))
    SQLITE_REPORTS_COLLECTION = os.environ.get("SQLITE_REPORTS_COLLECTION", "reports")
    SQLITE_EXTRACT_RESULT_COLLECTION = os.environ.get("SQLITE_EXTRACT_RESULT_COLLECTION", "extract_results")
    SQLITE_EVENT_LINK_COLLECTION = os.environ.get("SQLITE_EVENT_LINK_COLLECTION", "event_links")
    SQLITE_SUB_GRAPH_COLLECTION = os.environ.get("SQLITE_SUB_GRAPH_COLLECTION", "sub_graph")
    SQLITE_EVENT_LINK_RULES_COLLECTION = os.environ.get("SQLITE_EVENT_LINK_RULES_COLLECTION", "event_link_rules")


class DevelopmentConfig(Config):
    DEBUG = True
    PORT = 8800
