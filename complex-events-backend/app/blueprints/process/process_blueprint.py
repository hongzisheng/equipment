import sqlite3
from flask import request

from app.models import Result
from app.utils.db import get_db_connection
from . import process_bp


# ==================== 状态流转定义 ====================

# 状态流转顺序（确认前进的方向）
STATUS_FLOW_ORDER = [
    "released",                 # 0: 待开始
    "pending_engineer",         # 1: 等待工程师确认
    "pending_construction",     # 2: 等待施工确认
    "pending_team",             # 3: 等待班组受理
    "pending_sign",             # 4: 等待施工回签
    "submitted",                # 5: 已提交（工人提交后）
    "pending_process_close",    # 6: 等待工艺存储关闭
    "pending_equipment_close",  # 7: 等待设备部关闭
    "completed",                # 8: 已完成
]

# 终态（不可再操作）
TERMINAL_STATUSES = {"completed", "cancelled"}

# 驳回目标映射（驳回并非简单回退一位，部分状态有特定驳回目标）
REJECT_TARGET = {
    "released": "released",                          # 待开始驳回仍停留
    "pending_engineer": "released",                  # → 待开始
    "pending_construction": "pending_engineer",      # → 等待工程师确认
    "pending_team": "pending_construction",          # → 等待施工确认
    "pending_sign": "pending_team",                  # → 等待班组受理
    "submitted": "pending_sign",                     # → 等待施工回签
    "pending_process_close": "pending_sign",         # → 等待施工回签（跳过已提交）
    "pending_equipment_close": "pending_process_close",  # → 等待工艺存储关闭
}


def get_next_status(current: str) -> str:
    """获取确认后的下一状态"""
    if current in TERMINAL_STATUSES:
        return current
    try:
        idx = STATUS_FLOW_ORDER.index(current)
        if idx < len(STATUS_FLOW_ORDER) - 1:
            return STATUS_FLOW_ORDER[idx + 1]
    except ValueError:
        pass
    return current


def get_prev_status(current: str) -> str:
    """获取驳回目标状态（根据 REJECT_TARGET 映射表）"""
    if current in TERMINAL_STATUSES:
        return current
    return REJECT_TARGET.get(current, current)


def log_operation(conn, task_id, operation_type, old_status, new_status, comments=""):
    """写入操作日志"""
    conn.execute(
        """INSERT INTO task_operation_logs
           (task_id, operation_type, old_status, new_status, approval_comments)
           VALUES (?, ?, ?, ?, ?)""",
        (task_id, operation_type, old_status, new_status, comments),
    )


# ==================== API 端点 ====================


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
    """确认/驳回操作：确认→下一状态，驳回→上一状态"""
    payload = request.get_json(silent=True) or {}

    process_id = payload.get("id")
    action = payload.get("action")  # "confirm" 或 "reject"
    approval_comments = payload.get("approval_comments", "")

    if not process_id or not action:
        return Result.fail(message="请传入流程ID和操作类型(action)")

    if action not in ("confirm", "reject"):
        return Result.fail(message="action 必须是 confirm 或 reject")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 查询当前状态
            cursor.execute(
                "SELECT status FROM work_order_tasks WHERE id = ?",
                (int(process_id),),
            )
            row = cursor.fetchone()
            if not row:
                return Result.fail(message="未找到对应记录")

            old_status = row[0]

            # 终态不可操作
            if old_status in TERMINAL_STATUSES:
                return Result.fail(message=f"当前状态「{old_status}」为终态，不可操作")

            # 计算新状态
            if action == "confirm":
                new_status = get_next_status(old_status)
                operation_type = "confirm"
            else:
                new_status = get_prev_status(old_status)
                operation_type = "reject"

            # 更新状态
            cursor.execute(
                """UPDATE work_order_tasks
                   SET status = ?, approval_comments = ?,
                       updated_at = DATETIME('now', 'localtime')
                   WHERE id = ?""",
                (new_status, approval_comments, int(process_id)),
            )

            # 写入操作日志
            log_operation(conn, int(process_id), operation_type,
                         old_status, new_status, approval_comments)

            conn.commit()

            return Result.success(
                message=f"操作成功: {old_status} → {new_status}",
                data={"old_status": old_status, "new_status": new_status},
            )

    except Exception as e:
        return Result.fail(message=f"更新失败: {str(e)}")


@process_bp.route("/cancel", methods=["POST"])
def cancel_process():
    """管理员取消：任意状态 → cancelled"""
    payload = request.get_json(silent=True) or {}

    process_id = payload.get("id")
    approval_comments = payload.get("approval_comments", "管理员取消")

    if not process_id:
        return Result.fail(message="请传入流程ID")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT status FROM work_order_tasks WHERE id = ?",
                (int(process_id),),
            )
            row = cursor.fetchone()
            if not row:
                return Result.fail(message="未找到对应记录")

            old_status = row[0]

            if old_status in TERMINAL_STATUSES:
                return Result.fail(message=f"当前状态「{old_status}」为终态，不可取消")

            new_status = "cancelled"

            cursor.execute(
                """UPDATE work_order_tasks
                   SET status = ?, approval_comments = ?,
                       updated_at = DATETIME('now', 'localtime')
                   WHERE id = ?""",
                (new_status, approval_comments, int(process_id)),
            )

            log_operation(conn, int(process_id), "cancel",
                         old_status, new_status, approval_comments)

            conn.commit()

            return Result.success(
                message=f"已取消: {old_status} → {new_status}",
                data={"old_status": old_status, "new_status": new_status},
            )

    except Exception as e:
        return Result.fail(message=f"取消失败: {str(e)}")


@process_bp.route("/equipment/info", methods=["GET"])
def get_equipment_info():
    try:
        with get_db_connection(sqlite3.Row) as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT category_name AS value, category_name AS label, "
                "COUNT(*) AS count FROM equipment_category GROUP BY category_name"
            )
            categories = []
            for row in cursor.fetchall():
                categories.append({
                    "value": row["value"],
                    "label": row["label"],
                    "count": row["count"]
                })

            cursor.execute(
                "SELECT category, name FROM equipment_types ORDER BY category"
            )
            types_data = {}
            for row in cursor.fetchall():
                category = row["category"]
                if category not in types_data:
                    types_data[category] = []
                types_data[category].append(row["name"])

            cursor.execute(
                "SELECT id, name, category, equipment_type_name "
                "FROM equipment_instances ORDER BY category, equipment_type_name"
            )
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
