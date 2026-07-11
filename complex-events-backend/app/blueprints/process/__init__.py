from flask import Blueprint

process_bp = Blueprint("process", __name__)

from . import process_blueprint