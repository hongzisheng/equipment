import flask
from flask import current_app

from app.blueprints.associate import associate_bp
from app.blueprints.associate.event_link_filter import generate_link_cypher
from app.models import Result
from app.services import execute_cypher
from app.services.database_service import get_event_link_collection


def get_all_real_links():
    return get_event_link_collection().find(
        {
            "relation.prior": {"$exists": True, "$ne": "null"},
            "relation.after": {"$exists": True, "$ne": "null"},
            "relation.type": {"$ne": "没有关系"},
        }
    )


@associate_bp.route("/linkInGraph", methods=["GET"])
def link_in_graph():
    try:
        for link_doc in get_all_real_links():
            relation = link_doc.get("relation", {})
            link_cypher = generate_link_cypher(
                relation.get("prior"),
                relation.get("after"),
                relation.get("type"),
            )
            execute_cypher(flask.current_app, link_cypher)
        return Result.success(message="关系已全部建立")
    except Exception as e:
        current_app.logger.error(e)
        return Result.fail(message=str(e))
