import os
import time
import uuid

from flask import Blueprint, current_app, request

from app.models import Result
from app.services.database_service import get_reports_collection
from app.utils import format_doc

file_bp = Blueprint("file", __name__)


def _public_report(doc):
    return format_doc(doc) if doc else None


@file_bp.route("", methods=["GET"])
def get_file_list():
    collection = get_reports_collection()
    page_no = request.args.get("pageNo", 1, type=int)
    page_size = request.args.get("pageSize", 10, type=int)
    query = {"deleted": {"$ne": True}}
    total_count = collection.count_documents(query)
    cursor = collection.find(query).sort("createdAt", -1).skip((page_no - 1) * page_size).limit(page_size)
    rows = [_public_report(doc) for doc in cursor]
    return Result.success(message="查询文件列表成功", data={"total": total_count, "rows": rows})


@file_bp.route("/deleteReports", methods=["DELETE"])
def delete_reports():
    report_id_list = request.get_json(silent=True) or []
    if not isinstance(report_id_list, list):
      return Result.fail(message="删除参数必须是文件 id 列表")
    collection = get_reports_collection()
    collection.update_many({"id": {"$in": report_id_list}}, {"$set": {"deleted": True}})
    return Result.success(message="删除文件成功")


@file_bp.route("/searchById", methods=["GET"])
def search_by_id():
    report_id = request.args.get("reportId")
    if not report_id:
        return Result.fail(message="请传入文件 id")
    doc = get_reports_collection().find_one({"id": report_id, "deleted": {"$ne": True}})
    if not doc:
        return Result.fail(message="文件不存在")
    return Result.success(message="查询成功", data=_public_report(doc))


@file_bp.route("/search", methods=["GET"])
def search_by_keyword():
    keyword = request.args.get("keyword", "")
    only_id = request.args.get("onlyId", "false").lower() == "true"
    if not keyword:
        return Result.fail(message="请输入关键词")

    collection = get_reports_collection()
    query = {
        "deleted": {"$ne": True},
        "$or": [
            {"title": {"$regex": keyword, "$options": "i"}},
            {"topic": {"$regex": keyword, "$options": "i"}},
            {"details": {"$regex": keyword, "$options": "i"}},
        ],
    }
    docs = list(collection.find(query).sort("createdAt", -1).limit(50))
    if only_id:
        return Result.success(message="查询成功", data=[doc.get("id") for doc in docs])
    return Result.success(message="查询成功", data=[_public_report(doc) for doc in docs])


@file_bp.route("/upload", methods=["POST", "OPTIONS"])
def upload_file():
    if request.method == "OPTIONS":
        return Result.success(message="OPTIONS 请求成功")

    file = request.files.get("file")
    if not file:
        return Result.fail(message="请选择文件")

    report_id = str(uuid.uuid4())
    original_name = file.filename or "unnamed"
    stored_name = f"{report_id}_{original_name}"
    relative_path = os.path.join(current_app.config["UPLOAD_FOLDER"], stored_name)
    os.makedirs(os.path.dirname(relative_path), exist_ok=True)
    file.save(relative_path)

    created_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    doc = {
        "id": report_id,
        "topic": "上传文件",
        "title": original_name,
        "date": created_at,
        "link_url": "",
        "details": "",
        "resources": [stored_name],
        "filePath": os.path.abspath(relative_path),
        "createdAt": created_at,
        "deleted": False,
    }
    get_reports_collection().insert_one(doc)

    return Result.success(
        message="上传成功",
        data={
            "id": report_id,
            "fileName": stored_name,
            "filePath": os.path.abspath(relative_path),
        },
    )
