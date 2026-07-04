from flask import Blueprint

associate_bp = Blueprint('associate', __name__)

from . import rules, event_link_filter, link_in_graph
