"""工单和调度生成管理蓝图"""
from flask import Blueprint

workorder_mgmt_bp = Blueprint("workorder_mgmt", __name__, url_prefix="/api")

from . import workorder_blueprint
from . import schedule_generate_blueprint
