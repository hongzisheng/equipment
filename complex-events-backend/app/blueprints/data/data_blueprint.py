from flask import request

from app.models import Result
from app.services.database_service import (
    get_event_link_collection,
    get_extract_result_collection,
    get_reports_collection,
)
from app.utils import format_doc
from . import data_bp


@data_bp.route("/list", methods=["GET"])
def get_extract_result():
    collection = get_extract_result_collection()
    start_num = request.args.get("start", type=int, default=0)
    limit_num = request.args.get("limit", type=int)
    query = {"del": {"$ne": True}}

    cursor = collection.find(query).skip(start_num)
    if limit_num is not None:
        cursor = cursor.limit(limit_num)

    result_data = {
        "total": collection.count_documents(query),
        "list": [format_doc(doc) for doc in cursor],
    }
    return Result.success(message="查询成功", data=result_data)


@data_bp.route("/find", methods=["GET"])
def find_extract_result():
    find_id = request.args.get("id", type=str)
    if not find_id:
        return Result.fail(message="请传入查询 id")

    doc = get_extract_result_collection().find_one({"id": find_id})
    if not doc:
        return Result.fail(message="未找到该数据")
    return Result.success(message="查询成功", data=format_doc(doc))


@data_bp.route("/eventLink", methods=["GET"])
def get_event_link():
    find_report_id = request.args.get("report_id", type=str)
    if not find_report_id:
        return Result.fail(message="请传入报告 id")

    collection = get_event_link_collection()
    reports_collection = get_reports_collection()
    result_list = []
    for doc in collection.find({"mainEvent": find_report_id}):
        item = format_doc(doc)
        item["relevantEventDetails"] = format_doc(reports_collection.find_one({"id": item.get("relatedEvent")}))
        result_list.append(item)
    return Result.success(message="查询成功", data=result_list)


@data_bp.route("/eventLinkResult", methods=["GET"])
def get_event_link_result():
    find_report_id = request.args.get("report_id", type=str)
    if not find_report_id:
        return Result.fail(message="请传入报告 id")

    collection = get_event_link_collection()
    extract_result_collection = get_extract_result_collection()
    result_list = []
    for doc in collection.find({"mainEvent": find_report_id}):
        item = format_doc(doc)
        item["relevantEventDetails"] = format_doc(extract_result_collection.find_one({"id": item.get("relatedEvent")}))
        result_list.append(item)
    return Result.success(message="查询成功", data=result_list)


@data_bp.route("/delete", methods=["POST"])
def delete_report():
    report_id = request.args.get("id", type=str)
    result = get_extract_result_collection().update_one({"id": report_id}, {"$set": {"del": True}})
    if result.matched_count == 0:
        return Result.fail(message="未找到对应记录")
    return Result.success(message="删除成功")


@data_bp.route("/edit", methods=["POST"])
def edit_report():
    payload = request.get_json(silent=True) or {}
    edit_item = payload.get("editItem") or {}
    the_id = edit_item.get("id")
    if not the_id:
        return Result.fail(message="请传入编辑记录 id")

    update_fields = {k: v for k, v in edit_item.items() if k != "id"}
    if not update_fields:
        return Result.fail(message="没有可更新的字段")

    result = get_extract_result_collection().update_one({"id": the_id}, {"$set": update_fields})
    if result.matched_count == 0:
        return Result.fail(message="未找到对应记录")
    return Result.success(message="修改成功")


@data_bp.route("/addAction", methods=["POST"])
def add_action():
    data = request.get_json(silent=True) or {}
    report_id = data.get("report_id")
    action = data.get("actions")
    action_position = int(data.get("actionPosition", -1))

    collection = get_extract_result_collection()
    doc = collection.find_one({"id": report_id})
    if not doc:
        return Result.fail(message="未找到对应记录")

    actions = doc.get("actions", [])
    if 0 <= action_position < len(actions):
        actions.insert(action_position, action)
    else:
        actions.append(action)

    collection.update_one({"id": report_id}, {"$set": {"actions": actions}})
    return Result.success(message="添加成功")


@data_bp.route("/event_correlation_search", methods=["POST"])
def event_correlation_search():
    return Result.success(message="事件关联检索功能已精简", data=[])
