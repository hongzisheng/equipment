"""员工端 API 蓝图

提供员工端（worker）所需的接口：
- GET  /api/worker-workorders/<emp_id>     获取员工被分配的工单及工序
- GET  /api/worker/<emp_id>/history        获取员工操作历史
- PUT  /api/work-order-tasks/<task_id>/update-status  更新任务状态并记录工况
"""

import os
import sqlite3
import uuid
from datetime import datetime

from flask import Blueprint, request

from app.models import Result
from app.utils.db import get_db_connection

staff_bp = Blueprint("staff", __name__)

# 状态定义（统一标准，与 process_blueprint 一致）
STATUS_SEQUENCE = [
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

# 工人可操作的状态映射：当前状态 → (下一状态, 操作描述)
WORKER_ACTION_MAP = {
    "released":     ("pending_engineer", "申请开工"),   # 待开始 → 工人申请开工 → 等待工程师确认
    "pending_sign": ("submitted",        "提交工况"),   # 等待施工回签 → 工人提交 → 已提交
}


def _get_next_status(current_status: str) -> str | None:
    """获取工人操作后的下一状态，仅支持工人可操作的状态"""
    if current_status in WORKER_ACTION_MAP:
        return WORKER_ACTION_MAP[current_status][0]
    return None


# ============================================================
# GET /api/worker-workorders/<emp_id>
# 获取员工所分配的所有工单及对应工序
# ============================================================
@staff_bp.route("/worker-workorders/<emp_id>", methods=["GET"])
def get_worker_workorders(emp_id: str):
    """获取所有工单及工序（员工端统一账号，可查看全部工单）"""
    with get_db_connection(sqlite3.Row) as conn:
        rows = conn.execute(
            """
            SELECT
                wot.id            AS task_id,
                wot.task_code,
                wot.process_id,
                wot.process_name,
                wot.equipment_id,
                wot.equipment_name,
                wot.description,
                wot.estimated_hours,
                wot.scheduled_start_time,
                wot.scheduled_end_time,
                wot.actual_start_time,
                wot.actual_end_time,
                wot.status         AS task_status,
                wot.is_milestone,
                wot.workers,
                wot.process_code,
                wo.id             AS work_order_id,
                wo.order_number,
                wo.title          AS work_order_title,
                wo.status         AS work_order_status,
                wo.priority,
                wo.created_at     AS work_order_created_at,
                MIN(wotw.worker_name) AS worker_name,
                MIN(wotw.worker_type) AS worker_type,
                MIN(wotw.status)       AS assignment_status
            FROM work_order_tasks wot
            JOIN work_orders wo ON wot.work_order_id = wo.id
            LEFT JOIN work_order_task_workers wotw ON wot.id = wotw.task_id
            GROUP BY wot.id
            ORDER BY wot.scheduled_start_time
            """
        ).fetchall()

        data = [dict(r) for r in rows]
        return Result.success(data=data)


# ============================================================
# GET /api/worker/<emp_id>/history
# 获取员工的历史操作记录
# ============================================================
@staff_bp.route("/worker/<emp_id>/history", methods=["GET"])
def get_worker_history(emp_id: str):
    """获取所有操作历史记录（员工端统一账号，可查看全部历史）"""
    with get_db_connection(sqlite3.Row) as conn:
        rows = conn.execute(
            """
            SELECT
                id,
                task_id,
                user_id,
                operation_type,
                description,
                attachment_path,
                old_status,
                new_status,
                approval_comments,
                created_at
            FROM task_operation_logs
            ORDER BY created_at DESC
            LIMIT 50
            """
        ).fetchall()

        data = [dict(r) for r in rows]
        return Result.success(data=data)


# ============================================================
# PUT /api/work-order-tasks/<int:task_id>/update-status
# 更新任务状态（员工上报工况）
# ============================================================
@staff_bp.route("/work-order-tasks/<int:task_id>/update-status", methods=["PUT"])
def update_task_status(task_id: int):
    description = (request.form.get("description") or "").strip()
    uploaded_files = request.files.getlist("photo")

    with get_db_connection(sqlite3.Row) as conn:
        row = conn.execute(
            "SELECT id, status FROM work_order_tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if row is None:
            return Result.fail(message="任务不存在")

        old_status = row["status"]

        # 仅允许工人在指定状态下操作
        if old_status not in WORKER_ACTION_MAP:
            allowed = "、".join(f"{s}({d})" for s, (_, d) in WORKER_ACTION_MAP.items())
            return Result.fail(
                message=f"当前状态「{old_status}」不允许工人操作。允许操作的状态：{allowed}"
            )

        new_status = WORKER_ACTION_MAP[old_status][0]

        # 保存上传的文件
        saved_paths = []
        for f in uploaded_files:
            if f.filename:
                upload_dir = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                    "uploads",
                    "work_reports",
                )
                os.makedirs(upload_dir, exist_ok=True)
                ext = os.path.splitext(f.filename)[1] or ".jpg"
                saved_name = f"{uuid.uuid4().hex}{ext}"
                saved_path = os.path.join(upload_dir, saved_name)
                f.save(saved_path)
                saved_paths.append(saved_path)

        attachment_path = ";".join(saved_paths) if saved_paths else None

        # 更新任务状态
        conn.execute(
            "UPDATE work_order_tasks SET status = ?, updated_at = datetime('now','localtime') WHERE id = ?",
            (new_status, task_id),
        )
        conn.commit()

        # 写入操作日志
        conn.execute(
            """
            INSERT INTO task_operation_logs
                (task_id, user_id, operation_type, description, attachment_path, old_status, new_status, created_at)
            VALUES (?, ?, 'status_update', ?, ?, ?, ?, datetime('now','localtime'))
            """,
            (task_id, None, description, attachment_path, old_status, new_status),
        )
        conn.commit()

        return Result.success(
            data={
                "task_id": task_id,
                "old_status": old_status,
                "new_status": new_status,
            },
            message="工况提交成功",
        )
