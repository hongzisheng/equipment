from flask import Flask

from .sqlite_service import (
    check_sqlite_status,
    get_event_link_collection,
    get_extract_result_collection,
    get_event_link_rules_collection,
    get_reports_collection,
    get_sub_graph_collection,
)


def check_database_status(app: Flask):
    return check_sqlite_status(app)
