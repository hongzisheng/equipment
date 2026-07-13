import sqlite3
from flask import request

from app.models import Result
from app.utils.db import get_db_connection
from . import process_bp


@process_bp.route("/list", methods=["GET"])
def get_process_list():
    equipment_category = request.args.get("equipment_category")
    equipment_type = request.args.get("equipment_type")
    equipment_id = request.args.get("equipment_id")
    status = request.args.get("status")
    
    try:
        with get_db_connection(sqlite3.Row) as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    t.id,
                    t.work_order_id,
                    t.process_id,
                    t.task_code AS process_code,
                    t.process_name,
                    t.equipment_id,
                    t.equipment_name,
                    e.equipment_type_name,
                    e.category AS equipment_category,
                    t.description,
                    t.estimated_hours,
                    t.scheduled_start_time,
                    t.scheduled_end_time,
                    t.status,
                    t.is_milestone,
                    t.approval_comments,
                    t.workers
                FROM work_order_tasks t
                LEFT JOIN equipment_instances e ON t.equipment_id = e.id
            """
            
            params = []
            conditions = []
            
            if equipment_category:
                conditions.append("e.category = ?")
                params.append(equipment_category)
            if equipment_type:
                conditions.append("e.equipment_type_name = ?")
                params.append(equipment_type)
            if equipment_id:
                conditions.append("t.equipment_id = ?")
                params.append(int(equipment_id))
            if status:
                conditions.append("t.status = ?")
                params.append(status)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY t.scheduled_start_time ASC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            result_list = []
            for row in rows:
                result_list.append({
                    "id": row["id"],
                    "work_order_id": row["work_order_id"],
                    "process_id": row["process_id"],
                    "process_code": row["process_code"],
                    "process_name": row["process_name"],
                    "equipment_id": row["equipment_id"],
                    "equipment_name": row["equipment_name"],
                    "equipment_type_name": row["equipment_type_name"],
                    "equipment_category": row["equipment_category"],
                    "description": row["description"],
                    "estimated_hours": row["estimated_hours"],
                    "scheduled_start_time": row["scheduled_start_time"],
                    "scheduled_end_time": row["scheduled_end_time"],
                    "status": row["status"],
                    "is_milestone": row["is_milestone"],
                    "approval_comments": row["approval_comments"],
                    "workers": row["workers"]
                })
            
            return Result.success(
                message="查询成功",
                data={"total": len(result_list), "list": result_list}
            )
    
    except Exception as e:
        return Result.fail(message=f"查询失败: {str(e)}")


@process_bp.route("/find", methods=["GET"])
def find_process():
    find_id = request.args.get("id", type=int)
    if not find_id:
        return Result.fail(message="请传入查询 id")

    try:
        with get_db_connection(sqlite3.Row) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    t.id,
                    t.work_order_id,
                    t.process_id,
                    t.task_code AS process_code,
                    t.process_name,
                    t.equipment_id,
                    t.equipment_name,
                    e.equipment_type_name,
                    e.category AS equipment_category,
                    t.description,
                    t.estimated_hours,
                    t.scheduled_start_time,
                    t.scheduled_end_time,
                    t.status,
                    t.is_milestone,
                    t.approval_comments,
                    t.workers,
                    t.created_at,
                    t.updated_at
                FROM work_order_tasks t
                LEFT JOIN equipment_instances e ON t.equipment_id = e.id
                WHERE t.id = ?
            """, (find_id,))
            
            row = cursor.fetchone()
            
            if not row:
                return Result.fail(message="未找到该流程")
            
            return Result.success(message="查询成功", data={
                "id": row["id"],
                "work_order_id": row["work_order_id"],
                "process_id": row["process_id"],
                "process_code": row["process_code"],
                "process_name": row["process_name"],
                "equipment_id": row["equipment_id"],
                "equipment_name": row["equipment_name"],
                "equipment_type_name": row["equipment_type_name"],
                "equipment_category": row["equipment_category"],
                "description": row["description"],
                "estimated_hours": row["estimated_hours"],
                "scheduled_start_time": row["scheduled_start_time"],
                "scheduled_end_time": row["scheduled_end_time"],
                "status": row["status"],
                "is_milestone": row["is_milestone"],
                "approval_comments": row["approval_comments"],
                "workers": row["workers"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            })
    
    except Exception as e:
        return Result.fail(message=f"查询失败: {str(e)}")


@process_bp.route("/update", methods=["POST"])
def update_process():
    payload = request.get_json(silent=True) or {}
    
    process_id = payload.get("id")
    status = payload.get("status")
    approval_comments = payload.get("approval_comments")
    
    if not process_id or not status:
        return Result.fail(message="请传入流程ID和状态")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            update_fields = {"status": status}
            if approval_comments:
                update_fields["approval_comments"] = approval_comments
            update_fields["updated_at"] = "(DATETIME('now', 'localtime'))"
            
            set_clause = ", ".join([f"{k} = {v if v.startswith('(') else '?'}" for k, v in update_fields.items()])
            params = [v for v in update_fields.values() if not v.startswith('(')] + [int(process_id)]
            
            cursor.execute(f"UPDATE work_order_tasks SET {set_clause} WHERE id = ?", params)
            conn.commit()
            
            if cursor.rowcount == 0:
                return Result.fail(message="未找到对应记录")
            
            return Result.success(message="更新成功")
    
    except Exception as e:
        return Result.fail(message=f"更新失败: {str(e)}")


@process_bp.route("/equipment/info", methods=["GET"])
def get_equipment_info():
    try:
        with get_db_connection(sqlite3.Row) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT category_name AS value, category_name AS label, COUNT(*) AS count FROM equipment_category GROUP BY category_name")
            categories = []
            for row in cursor.fetchall():
                categories.append({
                    "value": row["value"],
                    "label": row["label"],
                    "count": row["count"]
                })
            
            cursor.execute("SELECT category, name FROM equipment_types ORDER BY category")
            types_data = {}
            for row in cursor.fetchall():
                category = row["category"]
                if category not in types_data:
                    types_data[category] = []
                types_data[category].append(row["name"])
            
            cursor.execute("SELECT id, name, category, equipment_type_name FROM equipment_instances ORDER BY category, equipment_type_name")
            instances_data = {}
            for row in cursor.fetchall():
                key = f"{row['category']}|{row['equipment_type_name']}"
                if key not in instances_data:
                    instances_data[key] = []
                instances_data[key].append({
                    "id": row["id"],
                    "name": row["name"]
                })
            
            return Result.success(message="查询成功", data={
                "categories": categories,
                "types": types_data,
                "instances": instances_data
            })
    
    except Exception as e:
        return Result.fail(message=f"查询失败: {str(e)}")