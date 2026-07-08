from flask import Blueprint

worker_bp = Blueprint("worker", __name__, url_prefix="/api")
equipment_bp = Blueprint("equipment", __name__, url_prefix="/api")    

from . import worker_blueprint
from . import equipment_blueprint