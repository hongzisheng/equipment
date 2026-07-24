from flask import Blueprint

workorder_mgmt_bp = Blueprint("workorder_mgmt", __name__, url_prefix="/api")

from .worker_bp import scheduling_worker_bp
from .equipment_bp import scheduling_equipment_bp
from . import workorder_blueprint
from . import maintenance_plan_blueprint
from .schedule_generate_blueprint import schedule_bp
from .simulation_blueprint import simulation_bp

