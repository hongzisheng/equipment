import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask_cors import CORS

from app.blueprints import (
    data_bp, user_bp, process_bp, info_bp,
    worker_bp, equipment_bp, tools_bp, materials_bp,
    scheduling_worker_bp, scheduling_equipment_bp,
    rules_process_bp, parse_blueprint, tree_bp, chat_bp,
    workorder_mgmt_bp, search_archive_bp, schedule_bp, file_bp,
    procedure_bp, staff_bp
)
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
    app.register_blueprint(process_bp, url_prefix="/process")
    app.register_blueprint(info_bp, url_prefix="/info")
    app.register_blueprint(worker_bp, url_prefix="/api")
    app.register_blueprint(equipment_bp, url_prefix="/api")
    app.register_blueprint(tools_bp, url_prefix="/api")
    app.register_blueprint(materials_bp, url_prefix="/api")
    app.register_blueprint(scheduling_worker_bp, url_prefix="/api")
    app.register_blueprint(scheduling_equipment_bp, url_prefix="/api")
    app.register_blueprint(rules_process_bp, url_prefix="/api")
    app.register_blueprint(parse_blueprint, url_prefix="/api")
    app.register_blueprint(tree_bp, url_prefix="/api")
    app.register_blueprint(chat_bp)
    app.register_blueprint(workorder_mgmt_bp)
    app.register_blueprint(search_archive_bp, url_prefix="/api")
    app.register_blueprint(schedule_bp)
    app.register_blueprint(file_bp)
    app.register_blueprint(procedure_bp, url_prefix="/api")
    app.register_blueprint(staff_bp, url_prefix="/api")


def create_app(config_class="app.config.DevelopmentConfig"):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(
        app,
        resources={
            r"/*": {
                "origins": "*",
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
