from flask import Blueprint

scheduling_bp = Blueprint("scheduling", __name__, url_prefix="/api")

from . import worker_blueprint
from . import equipment_blueprint