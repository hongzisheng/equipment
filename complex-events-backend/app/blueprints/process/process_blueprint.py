from flask import request

from app.models import Result
from app.data.mock_data import get_mock_equipment_info, get_mock_process_list, get_mock_process_detail
from . import process_bp


@process_bp.route("/list", methods=["GET"])
def get_process_list():
    equipment_category = request.args.get("equipment_category")
    equipment_type = request.args.get("equipment_type")
    equipment_id = request.args.get("equipment_id")
    status = request.args.get("status")
    
    filters = {}
    if equipment_category:
        filters['equipment_category'] = equipment_category
    if equipment_type:
        filters['equipment_type'] = equipment_type
    if equipment_id:
        filters['equipment_id'] = equipment_id
    if status:
        filters['status'] = status
    
    result_data = get_mock_process_list(filters)
    
    return Result.success(message="查询成功", data=result_data)


@process_bp.route("/find", methods=["GET"])
def find_process():
    find_id = request.args.get("id", type=int)
    if not find_id:
        return Result.fail(message="请传入查询 id")

    process = get_mock_process_detail(find_id)
    
    if not process:
        return Result.fail(message="未找到该流程")
    
    return Result.success(message="查询成功", data=process)


@process_bp.route("/update", methods=["POST"])
def update_process():
    payload = request.get_json(silent=True) or {}
    
    process_id = payload.get("id")
    status = payload.get("status")
    approval_comments = payload.get("approval_comments")
    
    if not process_id or not status:
        return Result.fail(message="请传入流程ID和状态")

    conn = get_db_connection()
    cursor = conn.cursor()
    
    update_fields = {"status": status}
    if approval_comments:
        update_fields["approval_comments"] = approval_comments
    
    set_clause = ", ".join([f"{k} = ?" for k in update_fields.keys()])
    params = list(update_fields.values()) + [int(process_id)]
    
    cursor.execute(f"UPDATE work_order_tasks SET {set_clause} WHERE id = ?", params)
    conn.commit()
    
    if cursor.rowcount == 0:
        conn.close()
        return Result.fail(message="未找到对应记录")
    
    conn.close()
    return Result.success(message="更新成功")


@process_bp.route("/equipment/info", methods=["GET"])
def get_equipment_info():
    result = get_mock_equipment_info()
    return Result.success(message="查询成功", data=result)
