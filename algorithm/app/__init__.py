"""应用工厂

采用 Flask 应用工厂模式（Application Factory Pattern）：
- create_app() 负责创建并配置 Flask 实例
- 注册所有蓝图（Blueprint）
- 统一开启 CORS
"""
from flask import Flask
from flask_cors import CORS

from app.config import Config


def create_app(config_class=Config):
    """创建并配置 Flask 应用实例"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 允许跨域请求
    CORS(app)

    # 兼容旧版 Python：datetime.UTC
    import datetime
    if not hasattr(datetime, 'UTC'):
        datetime.UTC = datetime.timezone.utc

    # 注册所有蓝图
    from app.api import register_blueprints
    register_blueprints(app)

    return app
