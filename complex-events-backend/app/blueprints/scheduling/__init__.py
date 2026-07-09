from flask import Blueprint

worker_bp = Blueprint("worker", __name__)
equipment_bp = Blueprint("equipment", __name__)

from . import worker_bp
from . import equipment_bp
