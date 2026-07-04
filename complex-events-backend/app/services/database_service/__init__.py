from flask import Flask

from .mongodb_service import (
    check_mongodb_status,
    get_event_link_collection,
    get_extract_result_collection,
    get_event_link_rules_collection,
    get_reports_collection,
    get_sub_graph_collection,
)
from .neo4j_service import check_neo4j_status, execute_cypher


def check_database_status(app: Flask):
    return check_mongodb_status(app) and check_neo4j_status(app)
