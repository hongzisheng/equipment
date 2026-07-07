"""API 蓝图注册中心

所有路由蓝图在此集中注册到 Flask 应用实例。
每个模块对应一个业务领域，遵循 MVC 的 Controller 层职责：
仅处理 HTTP 请求/响应，业务逻辑下沉到 services / core。
"""
from flask import Flask


def register_blueprints(app: Flask):
    """注册全部蓝图"""
    # ---- 由原 app.py 拆分出的系统级路由 ----
    from app.api.auth import auth_bp
    from app.api.chat import chat_bp
    from app.api.workorder import workorder_bp
    from app.api.scheduler import scheduler_bp
    from app.api.graph import graph_bp
    from app.api.uploads import uploads_bp

    # ---- 领域资源路由（原各 *_router.py）----
    from app.api.equipment import equipment_bp
    from app.api.worker import worker_bp
    from app.api.maintenance import maintenance_bp
    from app.api.materials import materials_bp
    from app.api.process import process_bp
    from app.api.panel import panel_bp
    from app.api.parse import parse_blueprint
    from app.api.file import file_bp
    from app.api.wx import wx_blueprint

    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(workorder_bp)
    app.register_blueprint(scheduler_bp)
    app.register_blueprint(graph_bp)
    app.register_blueprint(uploads_bp)

    app.register_blueprint(equipment_bp)
    app.register_blueprint(worker_bp)
    app.register_blueprint(maintenance_bp)
    app.register_blueprint(materials_bp)
    app.register_blueprint(process_bp)
    app.register_blueprint(panel_bp)
    app.register_blueprint(parse_blueprint)
    app.register_blueprint(file_bp)
    app.register_blueprint(wx_blueprint)
