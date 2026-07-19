from .data import data_bp
from .user_blueprint import user_bp
from .process import process_bp
from .info import info_bp
from .worker.worker_blueprint import worker_bp
from .equipment.equipment import equipment_bp
from .tools.tools_blueprint import tools_bp
from .materials.materials_blueprint import materials_bp

from .scheduling import worker_bp as scheduling_worker_bp, equipment_bp as scheduling_equipment_bp
from .scheduling import scheduling_worker_bp, scheduling_equipment_bp, workorder_mgmt_bp
from .scheduling import schedule_bp
# maintenance_plan_blueprint 的路由已注册在 workorder_mgmt_bp 上，
# 通过 scheduling/__init__.py 的 `from . import maintenance_plan_blueprint` 自动加载
from .rules.rulebase.process_router import process_bp as rules_process_bp
from .rules.extraction.parse_router import parse_blueprint
from .rules.tree.tree_router import tree_bp
from .chat.chat_blueprint import chat_bp

from .rules.search.search_router import search_archive_bp
from .rules.file.file_router import file_bp
from .rules.extraction.procedure_router import procedure_bp
from .staff import staff_bp
