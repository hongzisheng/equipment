import os


class Config:
    """Application configuration for the retained pages."""

    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join("assets", "file"))
    SUB_GRAPH_PATH = os.environ.get("SUB_GRAPH_PATH", os.path.join("assets", "sub_graph"))
    LOG_DIR = os.environ.get("LOG_DIR", os.path.join("assets", "logs"))

    LOGIN_USERNAME = os.environ.get("LOGIN_USERNAME", "admin")
    LOGIN_PASSWORD = os.environ.get("LOGIN_PASSWORD", "admin123")
    LOGIN_DISPLAY_NAME = os.environ.get("LOGIN_DISPLAY_NAME", "管理员")

    # MongoDB: stores uploaded file metadata, event lists, and event association data.
    MONGODB_HOST = os.environ.get("MONGODB_HOST", "localhost")
    MONGODB_PORT = int(os.environ.get("MONGODB_PORT", 27017))
    MONGODB_USER = os.environ.get("MONGODB_USER", "")
    MONGODB_PASSWORD = os.environ.get("MONGODB_PASSWORD", "")
    MONGODB_DATABASE = os.environ.get("MONGODB_DATABASE", "MongoDB-数据库名")
    MONGODB_REPORTS_COLLECTION = os.environ.get("MONGODB_REPORTS_COLLECTION", "MongoDB-上传文件元数据集合名")
    MONGODB_EXTRACT_RESULT_COLLECTION = os.environ.get("MONGODB_EXTRACT_RESULT_COLLECTION", "MongoDB-事件列表集合名")
    MONGODB_EVENT_LINK_COLLECTION = os.environ.get("MONGODB_EVENT_LINK_COLLECTION", "MongoDB-事件关联集合名")
    MONGODB_SUB_GRAPH_COLLECTION = os.environ.get("MONGODB_SUB_GRAPH_COLLECTION", "MongoDB-子图集合名")
    MONGODB_EVENT_LINK_RULES_COLLECTION = os.environ.get("MONGODB_EVENT_LINK_RULES_COLLECTION", "MongoDB-事件关联规则集合名")

    # Neo4j: stores graph nodes and relationships for graph-based event association visualization.
    NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.environ.get("NEO4J_USER", "Neo4j-用户名")
    NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "Neo4j-密码")


class DevelopmentConfig(Config):
    DEBUG = True
    PORT = 8800


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    DEBUG = True


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
