import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask_cors import CORS

from app.blueprints import data_bp, user_bp
from app.extension import init_extensions
from app.services.database_service import check_database_status


def make_dirs(app: Flask):
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["SUB_GRAPH_PATH"], exist_ok=True)
    os.makedirs(app.config["LOG_DIR"], exist_ok=True)


def configure_logging(app: Flask):
    file_handler = RotatingFileHandler(
        os.path.join(app.config.get("LOG_DIR", "logs"), "app.log"),
        maxBytes=1024 * 1024 * 10,
        backupCount=10,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info("Application startup")


def register_blueprints(app: Flask):
    app.register_blueprint(user_bp, url_prefix="/user")
    app.register_blueprint(data_bp, url_prefix="/data")


def create_app(config_class="app.config.DevelopmentConfig"):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(
        app,
        resources={
            r"/*": {
                "origins": ["http://localhost:8888", "http://localhost:5000"],
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "X-Token"],
                "supports_credentials": True,
            }
        },
    )

    init_extensions(app)
    make_dirs(app)
    configure_logging(app)

    if not check_database_status(app):
        raise RuntimeError("数据库连接失败，请检查 SQLite 配置。")

    register_blueprints(app)
    return app
