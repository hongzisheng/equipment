"""工单与工单任务路由

从 algorithm 分支移植，适配 main 分支。
包含工单列表、任务 CRUD、手动创建工单等接口。
"""
import datetime
import json
import os
import sqlite3
import traceback
import uuid

from flask import jsonify, request, send_from_directory, current_app

from . import workorder_mgmt_bp
from app.models import Result
from app.utils import get_db_connection


# ----------工单相关------------------
@workorder_mgmt_bp.route("/work-orders", methods=["GET"])
def get_work_orders():
    """获取所有工单列表"""
    try:
        with get_db_connection(row_factory=sqlite3.Row) as conn:
            c = conn.cursor()
            c.execute(
                """
                SELECT id, order_number, title, equipment_id, equipment_name,
                       status, created_by, created_at, scheduled_start_time,
                       scheduled_end_time, priority
                FROM work_orders
                ORDER BY created_at DESC
                """
            )
            rows = c.fetchall()
            work_orders = []
            for row in rows:
                work_orders.append(
                    {
                        "id": row["id"],
                        "order_number": row["order_number"],
                        "title": row["title"],
                        "equipment_id": row["equipment_id"],
                        "equipment_name": row["equipment_name"],
                        "status": row["status"],
                        "created_by": row["created_by"],
                        "created_at": row["created_at"],
                        "scheduled_start_time": row["scheduled_start_time"],
                        "scheduled_end_time": row["scheduled_end_time"],
                        "priority": row["priority"],
                    }
                )
            return jsonify({"success": True, "data": work_orders})
    except Exception as e:
        return jsonify(
            {"success": False, "error": str(e), "message": "获取工单列表失败"}
        ), 500


@workorder_mgmt_bp.route("/work-order-tasks", methods=["GET"])
def get_work_order_tasks():
    """获取所有工单任务列表"""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute(
                """
                SELECT id, work_order_id, task_code, process_id, process_name,
                       equipment_id, equipment_name, description, estimated_hours,
                       scheduled_start_time, scheduled_end_time, actual_start_time,
                       actual_end_time, status, predecessor_task_ids, is_milestone,
                       material_requirements, tools_requirements,
                       workers, approver_id, approval_comments, approved_at,
                       created_at, updated_at, attachment_path
                FROM work_order_tasks
                ORDER BY created_at DESC
                """
            )
            rows = c.fetchall()
            tasks = []
            column_names = [desc[0] for desc in c.description]
            for row in rows:
                task = dict(zip(column_names, row))
                for json_field in ["predecessor_task_ids", "workers",
                                   "material_requirements", "tools_requirements"]:
                    if task.get(json_field):
                        try:
                            task[json_field] = json.loads(task[json_field])
                        except (json.JSONDecodeError, TypeError):
                            pass
                    else:
                        task[json_field] = {} if json_field in ("material_requirements", "tools_requirements") else []
                task["is_milestone"] = bool(task["is_milestone"])
                tasks.append(task)
            return Result.success(data=tasks, message="查询成功")
    except Exception as e:
        return Result.fail(message=f"获取工单任务列表失败: {str(e)}")


@workorder_mgmt_bp.route("/manual-create-work-order", methods=["POST"])
def manual_create_work_order():
    """手动创建工单：选择设备实例和多个工序模板，校验前置依赖"""
    try:
        data = request.get_json()
        equipment_id = data.get("equipment_id")
        process_template_ids = data.get("process_template_ids")
        if (
            not equipment_id
            or not process_template_ids
            or not isinstance(process_template_ids, list)
            or len(process_template_ids) == 0
        ):
            return jsonify(
                {"success": False, "message": "设备ID和工序模板ID列表不能为空"}
            ), 400

        with get_db_connection() as conn:
            c = conn.cursor()

            # 1. 获取设备信息
            c.execute(
                "SELECT id, name, equipment_type_id FROM equipment_instances WHERE id = ?",
                (equipment_id,),
            )
            eq = c.fetchone()
            if not eq:
                return jsonify({"success": False, "message": "设备不存在"}), 404

            # 2. 获取所有工序模板信息
            placeholders = ",".join("?" for _ in process_template_ids)
            c.execute(
                f"""
                SELECT id, process_code, description, estimated_hours, required_workers,
                       predecessor_codes
                FROM process_templates WHERE id IN ({placeholders})
            """,
                process_template_ids,
            )
            templates = c.fetchall()
            if len(templates) != len(process_template_ids):
                found_ids = {t[0] for t in templates}
                missing = set(process_template_ids) - found_ids
                return jsonify({"success": False, "message": f"工序模板不存在: {missing}"}), 400

            # 3. 构建工序信息映射
            process_map = {}
            for tmpl in templates:
                tmpl_id = tmpl[0]
                process_code = tmpl[1]
                description = tmpl[2]
                estimated_hours = tmpl[3]
                required_workers = json.loads(tmpl[4]) if tmpl[4] else {}
                predecessor_codes = json.loads(tmpl[5]) if tmpl[5] else []
                process_map[tmpl_id] = {
                    "id": tmpl_id,
                    "code": process_code,
                    "description": description,
                    "estimated_hours": estimated_hours,
                    "required_workers": required_workers,
                    "predecessor_codes": predecessor_codes,
                }

            # 4. 校验前置依赖
            code_to_id = {proc["code"]: proc["id"] for proc in process_map.values()}
            selected_codes = set(code_to_id.keys())
            missing_predecessors = []
            for proc_id, proc in process_map.items():
                for pred_code in proc["predecessor_codes"]:
                    if pred_code not in selected_codes:
                        missing_predecessors.append(
                            {"process": proc["code"], "missing_predecessor": pred_code}
                        )
            if missing_predecessors:
                return jsonify(
                    {
                        "success": False,
                        "message": "工序前置依赖不满足",
                        "details": missing_predecessors,
                    }
                ), 400

            # 5. 生成工单编号
            current_date = datetime.datetime.now().strftime("%Y%m%d")
            c.execute(
                "SELECT COUNT(*) FROM work_orders WHERE order_number LIKE ?",
                (f"WO-{current_date}-%",),
            )
            order_count = c.fetchone()[0]
            order_number = f"WO-{current_date}-{str(order_count + 1).zfill(4)}"

            # 6. 插入工单
            c.execute(
                """
                INSERT INTO work_orders
                (order_number, title, equipment_id, equipment_name, status, created_by, created_at,
                 scheduled_start_time, scheduled_end_time, priority)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    order_number,
                    f"{eq[1]} - 多工序工单",
                    equipment_id,
                    eq[1],
                    "pending",
                    1,  # 默认创建者ID
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    None,
                    None,
                    "medium",
                ),
            )
            work_order_id = c.lastrowid

            # 7. 为每个工序创建任务
            task_ids = []
            task_map = {}  # process_code -> task_id
            for proc_id, proc in process_map.items():
                task_code = f"TSK-{work_order_id}-{proc['code']}"
                is_milestone = 1 if proc["code"].startswith("M") else 0
                c.execute(
                    """
                    INSERT INTO work_order_tasks
                    (work_order_id, task_code, process_id, process_code, process_name, equipment_id, equipment_name,
                     estimated_hours, scheduled_start_time, scheduled_end_time,
                     status, created_at, is_milestone)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        work_order_id,
                        task_code,
                        str(proc["id"]),
                        proc["code"],
                        proc["description"],
                        equipment_id,
                        eq[1],
                        proc["estimated_hours"],
                        None,
                        None,
                        "released",
                        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        is_milestone,
                    ),
                )
                task_id = c.lastrowid
                task_ids.append(task_id)
                task_map[proc["code"]] = task_id

            # 8. 设置前置任务ID
            for proc_id, proc in process_map.items():
                pred_codes = proc.get("predecessor_codes", [])
                if pred_codes:
                    pred_task_ids = [task_map[code] for code in pred_codes if code in task_map]
                    pred_task_ids_json = json.dumps(pred_task_ids)
                else:
                    pred_task_ids_json = json.dumps([])
                c.execute(
                    """
                    UPDATE work_order_tasks
                    SET predecessor_task_ids = ?
                    WHERE work_order_id = ? AND process_code = ?
                """,
                    (pred_task_ids_json, work_order_id, proc["code"]),
                )

            conn.commit()
            return jsonify(
                {
                    "success": True,
                    "message": f"工单及{len(task_ids)}个任务创建成功",
                    "work_order_id": work_order_id,
                    "order_number": order_number,
                    "task_ids": task_ids,
                }
            )
    except Exception as e:
        traceback.print_exc()
        return jsonify(
            {"success": False, "error": str(e), "message": "创建工单失败"}
        ), 500


@workorder_mgmt_bp.route("/work-orders/<int:work_order_id>", methods=["DELETE"])
def delete_work_order(work_order_id):
    """删除工单"""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT order_number FROM work_orders WHERE id = ?", (work_order_id,))
            result = c.fetchone()
            if not result:
                return jsonify({"success": False, "message": "工单不存在"}), 404
            c.execute("DELETE FROM work_order_tasks WHERE work_order_id = ?", (work_order_id,))
            c.execute("DELETE FROM work_orders WHERE id = ?", (work_order_id,))
            conn.commit()
            return jsonify({"success": True, "message": f"工单 {result[0]} 删除成功"})
    except Exception as e:
        return jsonify(
            {"success": False, "error": str(e), "message": "删除工单失败"}
        ), 500


@workorder_mgmt_bp.route("/process-templates", methods=["GET"])
def get_process_templates():
    """获取所有工序模板"""
    try:
        with get_db_connection(row_factory=sqlite3.Row) as conn:
            c = conn.cursor()
            equipment_type_id = request.args.get("equipment_type_id")
            if equipment_type_id:
                c.execute(
                    """
                    SELECT id, equipment_type_id, process_code, description, estimated_hours,
                           required_workers, predecessor_codes, parent_process_code,
                           is_major_process, material_requirements, tools_requirements,
                           material_price, tools_price, worker_price
                    FROM process_templates
                    WHERE equipment_type_id = ?
                    ORDER BY process_code
                """,
                    (equipment_type_id,),
                )
            else:
                c.execute(
                    """
                    SELECT id, equipment_type_id, process_code, description, estimated_hours,
                           required_workers, predecessor_codes, parent_process_code,
                           is_major_process, material_requirements, tools_requirements,
                           material_price, tools_price, worker_price
                    FROM process_templates
                    ORDER BY equipment_type_id, process_code
                """
                )
            rows = c.fetchall()
            templates = []
            for row in rows:
                tmpl = dict(row)
                for json_field in ["required_workers", "predecessor_codes"]:
                    if tmpl.get(json_field):
                        try:
                            tmpl[json_field] = json.loads(tmpl[json_field])
                        except (json.JSONDecodeError, TypeError):
                            pass
                    else:
                        tmpl[json_field] = [] if json_field == "predecessor_codes" else {}
                tmpl["is_major_process"] = bool(tmpl["is_major_process"])
                templates.append(tmpl)
            return jsonify({"success": True, "data": templates})
    except Exception as e:
        return jsonify(
            {"success": False, "error": str(e), "message": "获取工序模板失败"}
        ), 500


@workorder_mgmt_bp.route("/process-templates/equipment-type/<equipment_type_id>", methods=["GET"])
def get_process_templates_by_equipment_type(equipment_type_id):
    """根据设备类型ID获取工序模板"""
    try:
        with get_db_connection(row_factory=sqlite3.Row) as conn:
            c = conn.cursor()
            c.execute(
                """
                SELECT id, equipment_type_id, process_code, description, estimated_hours,
                       required_workers, predecessor_codes, parent_process_code,
                       is_major_process, material_requirements, tools_requirements,
                       material_price, tools_price, worker_price
                FROM process_templates
                WHERE equipment_type_id = ?
                ORDER BY process_code
            """,
                (equipment_type_id,),
            )
            rows = c.fetchall()
            templates = []
            for row in rows:
                tmpl = dict(row)
                for json_field in ["required_workers", "predecessor_codes"]:
                    if tmpl.get(json_field):
                        try:
                            tmpl[json_field] = json.loads(tmpl[json_field])
                        except (json.JSONDecodeError, TypeError):
                            pass
                    else:
                        tmpl[json_field] = [] if json_field == "predecessor_codes" else {}
                tmpl["is_major_process"] = bool(tmpl["is_major_process"])
                templates.append(tmpl)
            return jsonify({"success": True, "data": templates})
    except Exception as e:
        return jsonify(
            {"success": False, "error": str(e), "message": "获取工序模板失败"}
        ), 500


@workorder_mgmt_bp.route("/assign-workers-from-schedule", methods=["POST"])
def assign_workers_from_schedule():
    """将调度结果中的工人分配写入 work_order_tasks"""
    conn = None
    try:
        with get_db_connection(row_factory=sqlite3.Row) as conn:
            c = conn.cursor()
            c.execute(
                """
                SELECT schedule_id, process_id, equipment_id, workers
                FROM schedule_tasks
                """
            )
            schedule_tasks = c.fetchall()
            if not schedule_tasks:
                return jsonify(
                    {"success": False, "message": "schedule_tasks 表中无调度数据，请先运行调度算法"}
                ), 400

            assigned_count = 0
            errors = []

            for st in schedule_tasks:
                schedule_id = st["schedule_id"]
                process_id_raw = st["process_id"]  # 格式: "{equipment_id}_{process_code}"
                equipment_id = st["equipment_id"]
                workers_raw = st["workers"]

                workers_dict = {}
                if workers_raw:
                    try:
                        workers_dict = json.loads(workers_raw)
                        if not isinstance(workers_dict, dict):
                            workers_dict = {}
                    except (json.JSONDecodeError, TypeError):
                        workers_dict = {}

                if not workers_dict:
                    errors.append(f"调度任务 {schedule_id} 没有有效的工人分配信息")
                    continue

                # 从 process_id_raw 中提取工序代码（第一个下划线后面的部分）
                if "_" in process_id_raw:
                    process_code = process_id_raw.split("_", 1)[1]
                else:
                    process_code = process_id_raw

                c.execute(
                    """
                    SELECT id FROM work_order_tasks
                    WHERE equipment_id = ? AND process_id = ?
                    AND status NOT IN ('equipment_closed', 'cancelled')
                    """,
                    (equipment_id, process_code),
                )
                task_row = c.fetchone()
                if not task_row:
                    errors.append(
                        f"未找到匹配任务: equipment_id={equipment_id}, process_id={process_code}"
                    )
                    continue

                task_id = task_row["id"]
                workers_json = json.dumps(workers_dict, ensure_ascii=False)
                c.execute(
                    "UPDATE work_order_tasks SET workers = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (workers_json, task_id),
                )
                assigned_count += 1

            conn.commit()
            return jsonify(
                {
                    "success": True,
                    "message": f"工人分配完成，成功处理 {assigned_count} 个任务",
                    "assigned_count": assigned_count,
                    "errors": errors[:20],
                }
            )
    except Exception as e:
        traceback.print_exc()
        return jsonify(
            {"success": False, "error": str(e), "message": "工人分配失败"}
        ), 500


# 状态机定义（统一标准，与 process_blueprint 一致）
_STATE_ORDER = [
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

_STATUS_TRANSITIONS = {
    "released":                 {"pending_engineer": ["worker"]},
    "pending_engineer":         {"pending_construction": ["admin"]},
    "pending_construction":     {"pending_team": ["admin"]},
    "pending_team":             {"pending_sign": ["admin"]},
    "pending_sign":             {"submitted": ["worker"]},
    "submitted":                {"pending_process_close": ["admin"]},
    "pending_process_close":    {"pending_equipment_close": ["admin"]},
    "pending_equipment_close":  {"completed": ["admin"]},
}

# 驳回映射（与 process_blueprint 一致）
_REJECT_TARGET = {
    "pending_engineer":         "released",
    "pending_construction":     "pending_engineer",
    "pending_team":             "pending_construction",
    "pending_sign":             "pending_team",
    "submitted":                "pending_team",          # 已提交驳回 → 等待班组受理
    "pending_process_close":    "pending_sign",
    "pending_equipment_close":  "pending_process_close",
}


@workorder_mgmt_bp.route("/work-order-tasks/<int:task_id>/update-status", methods=["PUT", "POST"])
def update_work_order_task_status(task_id):
    """推进或驳回工单任务状态（简化版，不校验用户角色）"""
    try:
        data = request.get_json(silent=True) or {}
        action = data.get("action", "confirm")  # confirm | reject
        approval_comments = data.get("approval_comments", "")

        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT status FROM work_order_tasks WHERE id = ?", (task_id,))
            row = c.fetchone()
            if not row:
                return jsonify({"success": False, "message": "工单任务不存在"}), 404

            current_status = row[0]
            if current_status in ("completed", "cancelled"):
                return jsonify({"success": False, "message": "任务已关闭，不可修改"}), 400

            if action == "confirm":
                transitions = _STATUS_TRANSITIONS.get(current_status, {})
                next_statuses = list(transitions.keys())
                if not next_statuses:
                    return jsonify(
                        {"success": False, "message": f"当前状态 {current_status} 无下一步"}
                    ), 400
                target_status = next_statuses[0]
            else:  # reject / 驳回
                target_status = _REJECT_TARGET.get(current_status)
                if target_status is None:
                    return jsonify(
                        {"success": False, "message": f"当前状态「{current_status}」不可驳回"}
                    ), 400

            update_fields = ["status = ?", "updated_at = CURRENT_TIMESTAMP"]
            update_values = [target_status]

            if approval_comments:
                update_fields.append("approval_comments = ?")
                update_values.append(approval_comments)
                update_fields.append("approved_at = CURRENT_TIMESTAMP")

            update_values.append(task_id)
            c.execute(
                f"UPDATE work_order_tasks SET {', '.join(update_fields)} WHERE id = ?",
                update_values,
            )
            conn.commit()

            # 写入操作日志
            operation_type = "approval_confirm" if action == "confirm" else "approval_reject"
            c.execute(
                """INSERT INTO task_operation_logs
                   (task_id, operation_type, old_status, new_status, approval_comments)
                   VALUES (?, ?, ?, ?, ?)""",
                (task_id, operation_type, current_status, target_status, approval_comments),
            )
            conn.commit()
            return jsonify(
                {
                    "success": True,
                    "message": "工单任务状态更新成功",
                    "task_id": task_id,
                    "new_status": target_status,
                }
            )
    except Exception as e:
        traceback.print_exc()
        return jsonify(
            {"success": False, "error": str(e), "message": "更新工单任务状态失败"}
        ), 500


@workorder_mgmt_bp.route("/work-order-tasks/<int:task_id>/approve", methods=["PUT"])
def approve_work_order_task(task_id):
    """批量审批通过工单任务（将状态推进到下一步）"""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT status FROM work_order_tasks WHERE id = ?", (task_id,))
            row = c.fetchone()
            if not row:
                return jsonify({"success": False, "message": "工单任务不存在"}), 404

            current_status = row[0]
            if current_status in ("equipment_closed", "cancelled"):
                return jsonify({"success": False, "message": "任务已关闭，不可审批"}), 400

            transitions = _STATUS_TRANSITIONS.get(current_status, {})
            next_statuses = list(transitions.keys())
            if not next_statuses:
                return jsonify(
                    {"success": False, "message": f"当前状态 {current_status} 无下一步"}
                ), 400
            target_status = next_statuses[0]

            c.execute(
                """
                UPDATE work_order_tasks
                SET status = ?, approved_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (target_status, task_id),
            )
            conn.commit()
            return jsonify(
                {
                    "success": True,
                    "message": f"审批完成，新状态: {target_status}",
                    "task_id": task_id,
                    "new_status": target_status,
                }
            )
    except Exception as e:
        traceback.print_exc()
        return jsonify(
            {"success": False, "error": str(e), "message": "审批失败"}
        ), 500


@workorder_mgmt_bp.route("/schedule-tasks", methods=["GET"])
def get_schedule_tasks():
    """获取调度任务列表"""
    try:
        with get_db_connection(row_factory=sqlite3.Row) as conn:
            c = conn.cursor()
            c.execute(
                """
                SELECT schedule_id, process_id, process_name, equipment_id, equipment_name,
                       equipment_type_id, equipment_type_name, equipment_category,
                       start_time, end_time, start_time_formatted, end_time_formatted,
                       duration_days, workers, predecessors
                FROM schedule_tasks
                ORDER BY equipment_id, start_time
            """
            )
            rows = c.fetchall()
            tasks = []
            for row in rows:
                task = dict(row)
                for json_field in ["workers", "predecessors"]:
                    if task.get(json_field):
                        try:
                            task[json_field] = json.loads(task[json_field])
                        except (json.JSONDecodeError, TypeError):
                            pass
                    else:
                        task[json_field] = {} if json_field == "workers" else []
                tasks.append(task)
            return jsonify({"success": True, "data": tasks})
    except Exception as e:
        return jsonify(
            {"success": False, "error": str(e), "message": "获取调度任务失败"}
        ), 500


# ──────────────────────────────────────────────
#  操作日志查询
# ──────────────────────────────────────────────

@workorder_mgmt_bp.route("/work-order-tasks/<int:task_id>/logs", methods=["GET"])
def get_task_operation_logs(task_id):
    """获取指定工单任务的操作日志"""
    try:
        with get_db_connection(row_factory=sqlite3.Row) as conn:
            c = conn.cursor()
            c.execute(
                """
                SELECT id, task_id, user_id, operation_type,
                       description, attachment_path,
                       old_status, new_status, approval_comments, created_at
                FROM task_operation_logs
                WHERE task_id = ?
                ORDER BY created_at DESC
                """,
                (task_id,),
            )
            rows = c.fetchall()
            data = [dict(r) for r in rows]
            return jsonify({"success": True, "data": data})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "message": f"查询操作日志失败: {str(e)}"}), 500


# ──────────────────────────────────────────────
#  图片上传 & 静态文件服务
# ──────────────────────────────────────────────

@workorder_mgmt_bp.route("/work-order-tasks/<int:task_id>/upload-image", methods=["POST"])
def upload_task_image(task_id):
    """为工单任务上传图片附件"""
    uploaded_file = request.files.get("image")
    if not uploaded_file or not uploaded_file.filename:
        return jsonify({"success": False, "message": "未选择文件"}), 400

    # 仅允许图片格式
    allowed_exts = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
    ext = os.path.splitext(uploaded_file.filename)[1].lower()
    if ext not in allowed_exts:
        return jsonify({"success": False, "message": f"不支持的图片格式: {ext}"}), 400

    # 保存到 process_images 目录
    upload_dir = os.path.join(current_app.root_path, "..", "assets", "process_images")
    os.makedirs(upload_dir, exist_ok=True)
    saved_name = f"{uuid.uuid4().hex}{ext}"
    saved_path = os.path.join(upload_dir, saved_name)
    uploaded_file.save(saved_path)

    # 相对于 /api 前缀的访问路径
    relative_path = f"/api/uploads/process_images/{saved_name}"

    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute(
                "UPDATE work_order_tasks SET attachment_path = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (relative_path, task_id),
            )
            conn.commit()
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "message": f"更新数据库失败: {str(e)}"}), 500

    return jsonify({
        "success": True,
        "message": "图片上传成功",
        "data": {"attachment_path": relative_path},
    })


@workorder_mgmt_bp.route("/uploads/process_images/<path:filename>", methods=["GET"])
def serve_process_image(filename):
    """提供 process_images 下的静态图片"""
    upload_dir = os.path.join(current_app.root_path, "..", "assets", "process_images")
    return send_from_directory(upload_dir, filename)
