from flask import request

from app.build_neo4j import insert_graph_data_to_neo4j
from app.models import Result
from . import graph_bp


@graph_bp.route("/build", methods=["POST"])
def build_graph_database():
    try:
        ids = (request.get_json(silent=True) or {}).get("ids")
        if not ids:
            return Result.fail(message="请传入报告 id")
        insert_graph_data_to_neo4j(ids)
        return Result.success(message="图谱已成功构建到 Neo4j")
    except Exception as e:
        return Result.fail(code=500, message=f"构建失败: {str(e)}")


@graph_bp.route("/rebuild", methods=["GET"])
def rebuild_neo4j_database():
    try:
        insert_graph_data_to_neo4j()
        return Result.success(message="重建成功")
    except Exception as e:
        return Result.fail(code=500, message=f"重建失败: {str(e)}")
