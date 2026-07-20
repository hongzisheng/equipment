"""检修计划路由

提供检修计划的 CRUD、关联工单管理、调度方案查询等接口。
所有路由挂载在 workorder_mgmt_bp（url_prefix="/api"）下，
因此装饰器中不重复写 /api 前缀。
"""
import json
import sqlite3
import traceback
from datetime import datetime

from flask import jsonify, request

from . import workorder_mgmt_bp
from app.models import Result
from app.utils import get_db_connection
from app.core import run_scheduling, get_scheduler
from app import core


# ======================== 列表查询 ========================

@workorder_mgmt_bp.route("/maintenance-plans", methods=["GET"])
def get_maintenance_plans():
    """检修计划列表（支持分页、按名称/规模/状态筛选）"""
    try:
        page = request.args.get("page", 1, type=int)
        page_size = request.args.get("page_size", 10, type=int)
        plan_name = request.args.get("plan_name", "").strip()
        plan_scale = request.args.get("plan_scale", "").strip()
        status = request.args.get("status", "").strip()

        conditions = []
        params = []

        if plan_name:
            conditions.append("plan_name LIKE ?")
            params.append(f"%{plan_name}%")
        if plan_scale:
            conditions.append("plan_scale = ?")
            params.append(plan_scale)
        if status:
            conditions.append("status = ?")
            params.append(status)

        where_clause = (" WHERE " + " AND ".join(conditions)) if conditions else ""

        with get_db_connection(row_factory=sqlite3.Row) as conn:
            c = conn.cursor()

            # 总数
            c.execute(f"SELECT COUNT(*) FROM maintenance_plans{where_clause}", params)
            total = c.fetchone()[0]

            # 分页数据
            offset = (page - 1) * page_size
            c.execute(
                f"""
                SELECT id, plan_name, plan_scale, status, initiator, initiated_at,
                       planned_start_time, planned_end_time, actual_start_time, actual_end_time,
                       planned_man_hours, actual_man_hours, planned_cost, actual_cost,
                       schedule_plan_id, created_at, updated_at
                FROM maintenance_plans{where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                params + [page_size, offset],
            )
            rows = c.fetchall()
            plans = [dict(row) for row in rows]

            # 为每个计划附加关联工单数量
            for plan in plans:
                c.execute(
                    "SELECT COUNT(*) FROM work_orders WHERE plan_id = ?",
                    (plan["id"],),
                )
                plan["work_order_count"] = c.fetchone()[0]

        return jsonify({
            "success": True,
            "data": plans,
            "total": total,
            "page": page,
            "page_size": page_size,
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e), "message": "获取检修计划列表失败"}), 500


# ======================== 详情查询 ========================

@workorder_mgmt_bp.route("/maintenance-plans/<int:plan_id>", methods=["GET"])
def get_maintenance_plan(plan_id):
    """计划详情（含发起人、时间、成本、进度、关联工单列表）"""
    try:
        with get_db_connection(row_factory=sqlite3.Row) as conn:
            c = conn.cursor()
            c.execute(
                """
                SELECT id, plan_name, plan_scale, status, initiator, initiated_at,
                       planned_start_time, planned_end_time, actual_start_time, actual_end_time,
                       planned_man_hours, actual_man_hours, planned_cost, actual_cost,
                       schedule_plan_id, created_at, updated_at
                FROM maintenance_plans
                WHERE id = ?
                """,
                (plan_id,),
            )
            plan = c.fetchone()
            if not plan:
                return jsonify({"success": False, "message": "检修计划不存在"}), 404

            plan_dict = dict(plan)

            # 关联工单列表
            c.execute(
                """
                SELECT id, order_number, title, equipment_id, equipment_name,
                       status, priority, created_at
                FROM work_orders
                WHERE plan_id = ?
                ORDER BY created_at DESC
                """,
                (plan_id,),
            )
            work_orders = [dict(row) for row in c.fetchall()]

            # 每个工单的任务统计 + 人工费用
            for wo in work_orders:
                c.execute(
                    """
                    SELECT COUNT(*) AS total,
                           SUM(CASE WHEN status IN ('equipment_closed') THEN 1 ELSE 0 END) AS completed
                    FROM work_order_tasks
                    WHERE work_order_id = ?
                    """,
                    (wo["id"],),
                )
                stat = c.fetchone()
                wo["task_total"] = stat["total"]
                wo["task_completed"] = stat["completed"] or 0

                # 计算该工单的人工费用
                # worker_price 格式："普工天数,技工天数,高级技工天数"
                # 人工费用 = 普工天数 × 126 + 技工天数 × 173 + 高级技工天数 × 236
                c.execute(
                    """
                    SELECT pt.worker_price
                    FROM work_order_tasks t
                    LEFT JOIN process_templates pt ON CAST(pt.id AS TEXT) = t.process_id
                    WHERE t.work_order_id = ?
                    """,
                    (wo["id"],),
                )
                labor_cost = 0.0
                for (wp,) in c.fetchall():
                    if not wp:
                        continue
                    parts = str(wp).split(",")
                    common = float(parts[0]) if len(parts) >= 1 and parts[0].strip() else 0.0
                    skilled = float(parts[1]) if len(parts) >= 2 and parts[1].strip() else 0.0
                    senior = float(parts[2]) if len(parts) >= 3 and parts[2].strip() else 0.0
                    labor_cost += common * 126 + skilled * 173 + senior * 236
                wo["labor_cost"] = round(labor_cost, 2)

            plan_dict["work_orders"] = work_orders
            plan_dict["work_order_count"] = len(work_orders)

        return jsonify({"success": True, "data": plan_dict})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e), "message": "获取检修计划详情失败"}), 500


# ======================== 新建计划 ========================

@workorder_mgmt_bp.route("/maintenance-plans", methods=["POST"])
def create_maintenance_plan():
    """新建计划（传入计划信息 + 选择的工单ID数组）"""
    try:
        data = request.get_json()
        plan_name = data.get("plan_name", "").strip()
        plan_scale = data.get("plan_scale", "").strip()
        status = data.get("status", "待开始").strip()
        initiator = data.get("initiator", "").strip()
        initiated_at = data.get("initiated_at")
        planned_start_time = data.get("planned_start_time")
        planned_end_time = data.get("planned_end_time")
        actual_start_time = data.get("actual_start_time")
        actual_end_time = data.get("actual_end_time")
        actual_cost = data.get("actual_cost", 0)
        work_order_ids = data.get("work_order_ids", [])

        if not plan_name:
            return jsonify({"success": False, "message": "计划名称不能为空"}), 400

        with get_db_connection() as conn:
            c = conn.cursor()

            # 计算关联工单的总人工时、计划时间范围、计划成本
            planned_man_hours = 0
            actual_man_hours = 0
            auto_planned_start_time = None
            auto_planned_end_time = None
            planned_cost = 0
            if work_order_ids:
                placeholders = ",".join("?" for _ in work_order_ids)
                c.execute(
                    f"""
                    SELECT SUM(t.estimated_hours)
                    FROM work_order_tasks t
                    WHERE t.work_order_id IN ({placeholders})
                    """,
                    work_order_ids,
                )
                total = c.fetchone()[0]
                if total:
                    planned_man_hours = round(total, 1)

                c.execute(
                    f"""
                    SELECT MIN(scheduled_start_time), MAX(scheduled_end_time)
                    FROM work_orders
                    WHERE id IN ({placeholders})
                    """,
                    work_order_ids,
                )
                time_range = c.fetchone()
                auto_planned_start_time = time_range[0]
                auto_planned_end_time = time_range[1]

                # 方案A：按工单汇总，每个工单取其工序组对应的 M01 主工序价格
                # （通过 equipment_type_id 关联父工序，避免子工序重复计算）
                c.execute(
                    f"""
                    SELECT COALESCE(SUM(
                        COALESCE((
                            SELECT SUM(COALESCE(mpt.material_price, 0) + COALESCE(mpt.tools_price, 0))
                            FROM process_templates mpt
                            WHERE mpt.is_major_process = 1
                              AND mpt.equipment_type_id IN (
                                  SELECT DISTINCT pt2.equipment_type_id
                                  FROM work_order_tasks t2
                                  LEFT JOIN process_templates pt2 ON CAST(pt2.id AS TEXT) = t2.process_id
                                  WHERE t2.work_order_id = wo.id
                                    AND pt2.equipment_type_id IS NOT NULL
                              )
                        ), 0)
                    ), 0)
                    FROM work_orders wo
                    WHERE wo.id IN ({placeholders})
                    """,
                    work_order_ids,
                )
                planned_cost = round(c.fetchone()[0], 2)

            planned_start_time = auto_planned_start_time or planned_start_time
            planned_end_time = auto_planned_end_time or planned_end_time

            # 插入检修计划
            c.execute(
                """
                INSERT INTO maintenance_plans
                    (plan_name, plan_scale, status, initiator, initiated_at,
                     planned_start_time, planned_end_time, actual_start_time, actual_end_time,
                     planned_man_hours, actual_man_hours, planned_cost, actual_cost)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    plan_name, plan_scale, status, initiator, initiated_at,
                    planned_start_time, planned_end_time, actual_start_time, actual_end_time,
                    planned_man_hours, actual_man_hours, planned_cost, actual_cost,
                ),
            )
            new_plan_id = c.lastrowid

            # 将选中的工单关联到该计划
            if work_order_ids:
                placeholders = ",".join("?" for _ in work_order_ids)
                c.execute(
                    f"""
                    UPDATE work_orders SET plan_id = ?
                    WHERE id IN ({placeholders}) AND plan_id IS NULL
                    """,
                    [new_plan_id] + work_order_ids,
                )

            conn.commit()

        return jsonify({
            "success": True,
            "message": "检修计划创建成功",
            "data": {"id": new_plan_id, "plan_name": plan_name},
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e), "message": "创建检修计划失败"}), 500


# ======================== 更新计划 ========================

# 允许更新的字段白名单
_UPDATABLE_FIELDS = {
    "plan_name", "plan_scale", "status", "initiator", "initiated_at",
    "planned_start_time", "planned_end_time", "actual_start_time", "actual_end_time",
    "planned_man_hours", "actual_man_hours", "planned_cost", "actual_cost",
    "schedule_plan_id",
}


@workorder_mgmt_bp.route("/maintenance-plans/<int:plan_id>", methods=["PUT"])
def update_maintenance_plan(plan_id):
    """更新计划信息"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "请求体不能为空"}), 400

        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT id FROM maintenance_plans WHERE id = ?", (plan_id,))
            if not c.fetchone():
                return jsonify({"success": False, "message": "检修计划不存在"}), 404

            # 从白名单构建 SET 子句
            set_parts = []
            values = []
            for field in _UPDATABLE_FIELDS:
                if field in data:
                    set_parts.append(f"{field} = ?")
                    values.append(data[field])

            if not set_parts:
                return jsonify({"success": False, "message": "没有需要更新的字段"}), 400

            set_parts.append("updated_at = CURRENT_TIMESTAMP")
            values.append(plan_id)

            c.execute(
                f"UPDATE maintenance_plans SET {', '.join(set_parts)} WHERE id = ?",
                values,
            )

            # 如果请求中包含 work_order_ids，更新关联工单
            if "work_order_ids" in data:
                work_order_ids = data["work_order_ids"]
                # 先清空旧的关联
                c.execute(
                    "UPDATE work_orders SET plan_id = NULL WHERE plan_id = ?",
                    (plan_id,),
                )
                # 再设置新的关联
                if work_order_ids:
                    placeholders = ",".join("?" for _ in work_order_ids)
                    c.execute(
                        f"""
                        UPDATE work_orders SET plan_id = ?
                        WHERE id IN ({placeholders})
                        """,
                        [plan_id] + work_order_ids,
                    )
                # 重新计算人工时、计划时间范围和计划成本
                c.execute(
                    f"""
                    SELECT SUM(t.estimated_hours)
                    FROM work_order_tasks t
                    WHERE t.work_order_id IN ({placeholders})
                    """,
                    work_order_ids if work_order_ids else [0],
                )
                total = c.fetchone()[0]

                c.execute(
                    f"""
                    SELECT MIN(scheduled_start_time), MAX(scheduled_end_time)
                    FROM work_orders
                    WHERE id IN ({placeholders})
                    """,
                    work_order_ids if work_order_ids else [0],
                )
                time_range = c.fetchone()
                auto_planned_start_time = time_range[0]
                auto_planned_end_time = time_range[1]

                # 方案A：按工单汇总，每个工单取其工序组对应的 M01 主工序价格
                # （通过 equipment_type_id 关联父工序，避免子工序重复计算）
                c.execute(
                    f"""
                    SELECT COALESCE(SUM(
                        COALESCE((
                            SELECT SUM(COALESCE(mpt.material_price, 0) + COALESCE(mpt.tools_price, 0))
                            FROM process_templates mpt
                            WHERE mpt.is_major_process = 1
                              AND mpt.equipment_type_id IN (
                                  SELECT DISTINCT pt2.equipment_type_id
                                  FROM work_order_tasks t2
                                  LEFT JOIN process_templates pt2 ON CAST(pt2.id AS TEXT) = t2.process_id
                                  WHERE t2.work_order_id = wo.id
                                    AND pt2.equipment_type_id IS NOT NULL
                              )
                        ), 0)
                    ), 0)
                    FROM work_orders wo
                    WHERE wo.id IN ({placeholders})
                    """,
                    work_order_ids if work_order_ids else [0],
                )
                planned_cost_total = round(c.fetchone()[0], 2)

                c.execute(
                    """
                    UPDATE maintenance_plans
                    SET planned_man_hours = ?, planned_start_time = ?, planned_end_time = ?,
                        planned_cost = ?
                    WHERE id = ?
                    """,
                    (
                        round(total, 1) if total else 0,
                        auto_planned_start_time,
                        auto_planned_end_time,
                        planned_cost_total,
                        plan_id,
                    ),
                )

            conn.commit()

        return jsonify({"success": True, "message": "检修计划更新成功"})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e), "message": "更新检修计划失败"}), 500


# ======================== 删除计划 ========================

@workorder_mgmt_bp.route("/maintenance-plans/<int:plan_id>", methods=["DELETE"])
def delete_maintenance_plan(plan_id):
    """删除计划（同步清空关联工单的 plan_id）"""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT id FROM maintenance_plans WHERE id = ?", (plan_id,))
            if not c.fetchone():
                return jsonify({"success": False, "message": "检修计划不存在"}), 404

            # 清空关联工单的 plan_id
            c.execute(
                "UPDATE work_orders SET plan_id = NULL WHERE plan_id = ?",
                (plan_id,),
            )
            # 删除计划
            c.execute(
                "DELETE FROM maintenance_plans WHERE id = ?",
                (plan_id,),
            )
            conn.commit()

        return jsonify({"success": True, "message": "检修计划删除成功"})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e), "message": "删除检修计划失败"}), 500


# ======================== 未计划工单 ========================

@workorder_mgmt_bp.route("/work-orders/unplanned", methods=["GET"])
def get_unplanned_work_orders():
    """获取尚未被纳入任何计划的工单列表（供新建/编辑计划时选择）

    支持传入 plan_id 参数：
    - 不传 plan_id：只返回 plan_id IS NULL 的工单
    - 传入 plan_id：返回 plan_id IS NULL 或 plan_id = 指定ID 的工单（用于编辑模式）
    """
    try:
        plan_id = request.args.get("plan_id", type=int)

        with get_db_connection(row_factory=sqlite3.Row) as conn:
            c = conn.cursor()

            if plan_id:
                c.execute(
                    """
                    SELECT wo.id, wo.order_number, wo.title, wo.equipment_id, wo.equipment_name,
                           wo.status, wo.priority, wo.created_at, wo.plan_id,
                           wo.scheduled_start_time, wo.scheduled_end_time,
                           COALESCE((
                               SELECT SUM(t.estimated_hours)
                               FROM work_order_tasks t
                               WHERE t.work_order_id = wo.id
                           ), 0) as estimated_hours,
                           COALESCE((
                               SELECT SUM(COALESCE(mpt.material_price, 0) + COALESCE(mpt.tools_price, 0))
                               FROM process_templates mpt
                               WHERE mpt.is_major_process = 1
                                 AND mpt.equipment_type_id IN (
                                     SELECT DISTINCT pt2.equipment_type_id
                                     FROM work_order_tasks t2
                                     LEFT JOIN process_templates pt2 ON CAST(pt2.id AS TEXT) = t2.process_id
                                     WHERE t2.work_order_id = wo.id
                                       AND pt2.equipment_type_id IS NOT NULL
                                 )
                           ), 0) as estimated_cost
                    FROM work_orders wo
                    WHERE wo.plan_id IS NULL OR wo.plan_id = ?
                    ORDER BY wo.plan_id DESC, wo.created_at DESC
                    """,
                    (plan_id,),
                )
            else:
                c.execute(
                    """
                    SELECT wo.id, wo.order_number, wo.title, wo.equipment_id, wo.equipment_name,
                           wo.status, wo.priority, wo.created_at, NULL as plan_id,
                           wo.scheduled_start_time, wo.scheduled_end_time,
                           COALESCE((
                               SELECT SUM(t.estimated_hours)
                               FROM work_order_tasks t
                               WHERE t.work_order_id = wo.id
                           ), 0) as estimated_hours,
                           COALESCE((
                               SELECT SUM(COALESCE(mpt.material_price, 0) + COALESCE(mpt.tools_price, 0))
                               FROM process_templates mpt
                               WHERE mpt.is_major_process = 1
                                 AND mpt.equipment_type_id IN (
                                     SELECT DISTINCT pt2.equipment_type_id
                                     FROM work_order_tasks t2
                                     LEFT JOIN process_templates pt2 ON CAST(pt2.id AS TEXT) = t2.process_id
                                     WHERE t2.work_order_id = wo.id
                                       AND pt2.equipment_type_id IS NOT NULL
                                 )
                           ), 0) as estimated_cost
                    FROM work_orders wo
                    WHERE wo.plan_id IS NULL
                    ORDER BY wo.created_at DESC
                    """
                )

            rows = c.fetchall()
            work_orders = [dict(row) for row in rows]
            for wo in work_orders:
                wo["is_associated"] = wo["plan_id"] is not None

        return jsonify({"success": True, "data": work_orders})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e), "message": "获取未计划工单失败"}), 500


# ======================== 计划下工单详情 ========================

@workorder_mgmt_bp.route("/maintenance-plans/<int:plan_id>/work-orders", methods=["GET"])
def get_plan_work_orders(plan_id):
    """获取该计划下的所有工单详情（含任务、设备信息）"""
    try:
        with get_db_connection(row_factory=sqlite3.Row) as conn:
            c = conn.cursor()

            # 确认计划存在
            c.execute("SELECT id, plan_name FROM maintenance_plans WHERE id = ?", (plan_id,))
            plan = c.fetchone()
            if not plan:
                return jsonify({"success": False, "message": "检修计划不存在"}), 404

            # 工单列表
            c.execute(
                """
                SELECT wo.id, wo.order_number, wo.title, wo.equipment_id, wo.equipment_name,
                       wo.status, wo.priority, wo.created_at,
                       wo.scheduled_start_time, wo.scheduled_end_time
                FROM work_orders wo
                WHERE wo.plan_id = ?
                ORDER BY wo.created_at DESC
                """,
                (plan_id,),
            )
            work_orders = []
            for wo_row in c.fetchall():
                wo = dict(wo_row)

                # 设备信息
                c.execute(
                    """
                    SELECT name, equipment_type_name, category
                    FROM equipment_instances
                    WHERE id = ?
                    """,
                    (wo["equipment_id"],),
                )
                eq = c.fetchone()
                wo["equipment_type_name"] = eq["equipment_type_name"] if eq else ""
                wo["equipment_category"] = eq["category"] if eq else ""

                # 工单任务
                c.execute(
                    """
                    SELECT id, task_code, process_id, process_name, process_code,
                           equipment_id, equipment_name, description, estimated_hours,
                           scheduled_start_time, scheduled_end_time, actual_start_time, actual_end_time,
                           status, is_milestone, workers, predecessor_task_ids
                    FROM work_order_tasks
                    WHERE work_order_id = ?
                    ORDER BY id
                    """,
                    (wo["id"],),
                )
                tasks = []
                for t_row in c.fetchall():
                    task = dict(t_row)
                    # 解析 JSON 字段
                    for json_field in ["workers", "predecessor_task_ids"]:
                        if task.get(json_field):
                            try:
                                task[json_field] = json.loads(task[json_field])
                            except (json.JSONDecodeError, TypeError):
                                pass
                        else:
                            task[json_field] = {} if json_field == "workers" else []
                    task["is_milestone"] = bool(task["is_milestone"])
                    tasks.append(task)

                wo["tasks"] = tasks

                # 任务统计
                total_tasks = len(tasks)
                completed_tasks = sum(
                    1 for t in tasks if t["status"] in ("equipment_closed",)
                )
                wo["task_total"] = total_tasks
                wo["task_completed"] = completed_tasks
                wo["progress"] = round(completed_tasks / total_tasks * 100, 1) if total_tasks else 0

                work_orders.append(wo)

        return jsonify({
            "success": True,
            "data": {
                "plan_id": plan["id"],
                "plan_name": plan["plan_name"],
                "work_orders": work_orders,
            },
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e), "message": "获取计划工单详情失败"}), 500


# ======================== 查看调度方案 ========================

@workorder_mgmt_bp.route("/maintenance-plans/<int:plan_id>/schedule-plan", methods=["GET"])
def get_plan_schedule_plan(plan_id):
    """查看该检修计划关联的调度方案

    读取 maintenance_plans.schedule_plan_id，
    若存在则查询 schedule_tasks 返回调度方案详情。
    """
    try:
        with get_db_connection(row_factory=sqlite3.Row) as conn:
            c = conn.cursor()

            # 确认计划存在并获取 schedule_plan_id
            c.execute(
                "SELECT id, plan_name, schedule_plan_id FROM maintenance_plans WHERE id = ?",
                (plan_id,),
            )
            plan = c.fetchone()
            if not plan:
                return jsonify({"success": False, "message": "检修计划不存在"}), 404

            if not plan["schedule_plan_id"]:
                return jsonify({
                    "success": True,
                    "data": None,
                    "message": "该计划暂无关联的调度方案",
                })

            schedule_plan_id = int(plan["schedule_plan_id"])

            # 按 schedule_plan_id 查询该方案的调度任务（方案隔离，不再用 equipment_id 跨方案匹配）
            c.execute(
                """
                SELECT schedule_id, process_id, process_name, equipment_id, equipment_name,
                       equipment_type_id, equipment_type_name, equipment_category,
                       start_time, end_time, start_time_formatted, end_time_formatted,
                       duration_days, workers, predecessors
                FROM schedule_tasks
                WHERE schedule_plan_id = ?
                ORDER BY equipment_id, start_time
                """,
                (schedule_plan_id,),
            )
            rows = c.fetchall()
            schedule_tasks = []
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
                schedule_tasks.append(task)

        return jsonify({
            "success": True,
            "data": {
                "schedule_plan_id": schedule_plan_id,
                "plan_id": plan_id,
                "plan_name": plan["plan_name"],
                "schedule_tasks": schedule_tasks,
            },
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e), "message": "获取调度方案失败"}), 500


# ======================== 调度方案生成与历史 ========================

@workorder_mgmt_bp.route("/maintenance-plans/<int:plan_id>/run-scheduler", methods=["POST"])
def run_scheduler_by_plan(plan_id):
    """按检修计划生成调度方案

    自动查询该计划下所有工单执行调度，并将结果作为新方案保存到
    schedule_plans + schedule_tasks（每次生成新方案，不覆盖已有方案）。
    """
    try:
        data = request.get_json() or {}
        algorithm_name = data.get("algorithm", "topological")
        target = data.get("target", "minimize_duration")
        print(f"[DEBUG] 生成调度: plan_id={plan_id}, algorithm={algorithm_name}, target={target}")

        # 1. 确认检修计划存在并查询关联工单
        with get_db_connection(row_factory=sqlite3.Row) as conn:
            c = conn.cursor()
            c.execute(
                "SELECT id, plan_name FROM maintenance_plans WHERE id = ?",
                (plan_id,),
            )
            plan = c.fetchone()
            if not plan:
                return jsonify({"success": False, "message": "检修计划不存在"}), 404

            c.execute(
                "SELECT id FROM work_orders WHERE plan_id = ? ORDER BY id",
                (plan_id,),
            )
            work_order_ids = [row["id"] for row in c.fetchall()]

        if not work_order_ids:
            return jsonify({"success": False, "message": "该检修计划下没有关联工单，无法调度"}), 400

        # 2. 在 schedule_plans 注册一条新方案（占位），获取 schedule_plan_id
        schedule_name = f"{plan['plan_name']}-方案-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute(
                """INSERT INTO schedule_plans
                   (plan_id, schedule_name, algorithm, status, work_order_ids, created_at)
                   VALUES (?, ?, ?, '生成中', ?, ?)""",
                (
                    plan_id,
                    schedule_name,
                    algorithm_name,
                    json.dumps(work_order_ids),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
            schedule_plan_id = c.lastrowid
            conn.commit()

        # 3. 执行调度（带 schedule_plan_id，结果按方案隔离写入 schedule_tasks）
        core.reset_scheduler()
        formatted_plan, statistics, success, message = run_scheduling(
            work_order_ids, algorithm_name, schedule_plan_id=schedule_plan_id
        )

        if not success:
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute(
                    "UPDATE schedule_plans SET status = '失败' WHERE id = ?",
                    (schedule_plan_id,),
                )
                conn.commit()
            if isinstance(message, dict) and message.get("error_type") == "insufficient_workers":
                return jsonify({
                    "success": False,
                    "error_type": "insufficient_workers",
                    "message": "工人资源不足，无法开始调度",
                    "error_details": message.get("details", []),
                }), 400
            return jsonify({"success": False, "message": str(message)}), 400

        # 4. 调度成功，回填方案记录（统计、任务数、状态）
        total_tasks = len(formatted_plan) if formatted_plan else 0
        project_start = None
        try:
            scheduler = get_scheduler()
            if scheduler and scheduler.project_start_datetime:
                project_start = scheduler.project_start_datetime.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass

        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute(
                """UPDATE schedule_plans
                   SET status = '生效中', statistics = ?, total_tasks = ?, project_start_datetime = ?
                   WHERE id = ?""",
                (
                    json.dumps(statistics, ensure_ascii=False),
                    total_tasks,
                    project_start,
                    schedule_plan_id,
                ),
            )
            # 5. 更新 maintenance_plans.schedule_plan_id 指向当前生效方案
            c.execute(
                "UPDATE maintenance_plans SET schedule_plan_id = ?, updated_at = ? WHERE id = ?",
                (
                    str(schedule_plan_id),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    plan_id,
                ),
            )
            # 6. 将该检修计划下其他方案标记为"已归档"，只保留当前方案为"生效中"
            c.execute(
                "UPDATE schedule_plans SET status = '已归档' WHERE plan_id = ? AND id != ? AND status = '生效中'",
                (plan_id, schedule_plan_id),
            )
            conn.commit()

        # 获取工人池（前端展示用）
        worker_pool_data = {}
        try:
            scheduler = get_scheduler()
            if scheduler:
                worker_pool_data = scheduler.get_worker_pool()
        except Exception as e:
            print(f"获取工人池失败: {e}")

        return jsonify({
            "success": True,
            "schedule_plan_id": schedule_plan_id,
            "schedule_name": schedule_name,
            "plan_id": plan_id,
            "plan_name": plan["plan_name"],
            "algorithm": algorithm_name,
            "schedule_plan": formatted_plan,
            "statistics": statistics,
            "worker_pool": worker_pool_data,
            "total_tasks": total_tasks,
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e), "message": "按检修计划调度失败"}), 500


@workorder_mgmt_bp.route("/maintenance-plans/<int:plan_id>/schedule-plans", methods=["GET"])
def get_plan_schedule_plans(plan_id):
    """获取检修计划的调度方案历史列表

    返回该计划下所有生成的调度方案（按创建时间倒序）。
    """
    try:
        with get_db_connection(row_factory=sqlite3.Row) as conn:
            c = conn.cursor()
            # 确认计划存在并获取当前生效方案
            c.execute(
                "SELECT id, plan_name, schedule_plan_id FROM maintenance_plans WHERE id = ?",
                (plan_id,),
            )
            plan = c.fetchone()
            if not plan:
                return jsonify({"success": False, "message": "检修计划不存在"}), 404

            c.execute(
                """SELECT id, schedule_name, algorithm, status, work_order_ids,
                          project_start_datetime, statistics, total_tasks, created_at
                   FROM schedule_plans
                   WHERE plan_id = ?
                   ORDER BY created_at DESC""",
                (plan_id,),
            )
            rows = c.fetchall()
            plans = []
            for row in rows:
                item = dict(row)
                if item.get("work_order_ids"):
                    try:
                        item["work_order_ids"] = json.loads(item["work_order_ids"])
                    except (json.JSONDecodeError, TypeError):
                        pass
                if item.get("statistics"):
                    try:
                        item["statistics"] = json.loads(item["statistics"])
                    except (json.JSONDecodeError, TypeError):
                        pass
                plans.append(item)

        return jsonify({
            "success": True,
            "data": plans,
            "total": len(plans),
            "current_schedule_plan_id": plan["schedule_plan_id"],
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e), "message": "获取方案历史失败"}), 500


@workorder_mgmt_bp.route("/schedule-plans/<int:schedule_plan_id>", methods=["GET"])
def get_schedule_plan_detail(schedule_plan_id):
    """按调度方案ID查询方案详情（支持查看历史方案的任务列表）

    与 /maintenance-plans/<plan_id>/schedule-plan 不同：
    - 后者只返回检修计划当前生效方案
    - 本接口按任意 schedule_plan_id 查询，可查看历史方案
    """
    try:
        with get_db_connection(row_factory=sqlite3.Row) as conn:
            c = conn.cursor()

            # 方案元信息
            c.execute(
                """SELECT id, plan_id, schedule_name, algorithm, status, work_order_ids,
                          project_start_datetime, statistics, total_tasks, created_at
                   FROM schedule_plans WHERE id = ?""",
                (schedule_plan_id,),
            )
            plan = c.fetchone()
            if not plan:
                return jsonify({"success": False, "message": "调度方案不存在"}), 404

            # 该方案的任务（按 schedule_plan_id 隔离查询）
            c.execute(
                """SELECT schedule_id, process_id, process_name, equipment_id, equipment_name,
                          equipment_type_id, equipment_type_name, equipment_category,
                          start_time, end_time, start_time_formatted, end_time_formatted,
                          duration_days, workers, predecessors
                   FROM schedule_tasks
                   WHERE schedule_plan_id = ?
                   ORDER BY equipment_id, start_time""",
                (schedule_plan_id,),
            )
            rows = c.fetchall()
            schedule_tasks = []
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
                schedule_tasks.append(task)

            result = dict(plan)
            if result.get("work_order_ids"):
                try:
                    result["work_order_ids"] = json.loads(result["work_order_ids"])
                except (json.JSONDecodeError, TypeError):
                    pass
            if result.get("statistics"):
                try:
                    result["statistics"] = json.loads(result["statistics"])
                except (json.JSONDecodeError, TypeError):
                    pass
            result["schedule_tasks"] = schedule_tasks

        return jsonify({"success": True, "data": result})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e), "message": "获取方案详情失败"}), 500


# ======================== 方案对比 ========================

@workorder_mgmt_bp.route("/schedule-plans/compare", methods=["GET"])
def compare_schedule_plans():
    """对比两个调度方案

    查询参数：id1, id2（两个方案的 schedule_plan_id）
    返回：两个方案的元信息、任务列表、概览统计、任务级差异
    """
    try:
        id1 = request.args.get("id1", type=int)
        id2 = request.args.get("id2", type=int)
        if not id1 or not id2:
            return jsonify({"success": False, "message": "请提供 id1 和 id2 两个参数"}), 400
        if id1 == id2:
            return jsonify({"success": False, "message": "不能对比同一个方案"}), 400

        with get_db_connection(row_factory=sqlite3.Row) as conn:
            c = conn.cursor()
            plans_data = {}
            for plan_id in (id1, id2):
                c.execute(
                    """SELECT id, plan_id, schedule_name, algorithm, status, work_order_ids,
                              project_start_datetime, statistics, total_tasks, created_at
                       FROM schedule_plans WHERE id = ?""",
                    (plan_id,),
                )
                plan = c.fetchone()
                if not plan:
                    return jsonify({"success": False, "message": f"方案 {plan_id} 不存在"}), 404

                plan_dict = dict(plan)
                if plan_dict.get("work_order_ids"):
                    try:
                        plan_dict["work_order_ids"] = json.loads(plan_dict["work_order_ids"])
                    except (json.JSONDecodeError, TypeError):
                        pass
                if plan_dict.get("statistics"):
                    try:
                        plan_dict["statistics"] = json.loads(plan_dict["statistics"])
                    except (json.JSONDecodeError, TypeError):
                        pass

                c.execute(
                    """SELECT schedule_id, process_id, process_name, equipment_id, equipment_name,
                              equipment_type_id, equipment_type_name, equipment_category,
                              start_time, end_time, start_time_formatted, end_time_formatted,
                              duration_days, workers, predecessors, worker_price
                       FROM schedule_tasks
                       WHERE schedule_plan_id = ?
                       ORDER BY equipment_id, start_time""",
                    (plan_id,),
                )
                tasks = []
                for row in c.fetchall():
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
                plan_dict["schedule_tasks"] = tasks
                plans_data[plan_id] = plan_dict

            plan1 = plans_data[id1]
            plan2 = plans_data[id2]

            overview1 = _compute_plan_overview(plan1)
            overview2 = _compute_plan_overview(plan2)
            task_diff = _compute_task_diff(plan1["schedule_tasks"], plan2["schedule_tasks"])

        return jsonify({
            "success": True,
            "data": {
                "plan1": plan1,
                "plan2": plan2,
                "overview1": overview1,
                "overview2": overview2,
                "task_diff": task_diff,
            },
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e), "message": "方案对比失败"}), 500


def _compute_plan_overview(plan):
    """计算方案概览统计：总任务数、总工期、起止时间、工人数量、按设备分组、预估成本"""
    tasks = plan.get("schedule_tasks") or []
    if not tasks:
        return {
            "total_tasks": 0,
            "total_duration_days": 0,
            "start_time": None,
            "end_time": None,
            "start_time_formatted": None,
            "end_time_formatted": None,
            "worker_count": 0,
            "workers": [],
            "by_equipment": {},
            "estimated_cost": 0,
            "common_hours": 0,
            "skilled_hours": 0,
            "senior_hours": 0,
        }

    indexed_starts = [(i, t["start_time"]) for i, t in enumerate(tasks) if t.get("start_time") is not None]
    indexed_ends = [(i, t["end_time"]) for i, t in enumerate(tasks) if t.get("end_time") is not None]

    start_time = min(s for _, s in indexed_starts) if indexed_starts else None
    end_time = max(e for _, e in indexed_ends) if indexed_ends else None

    start_idx = min(indexed_starts, key=lambda x: x[1])[0] if indexed_starts else None
    end_idx = max(indexed_ends, key=lambda x: x[1])[0] if indexed_ends else None

    total_duration = sum(t.get("duration_days", 0) or 0 for t in tasks)

    worker_set = set()
    for t in tasks:
        workers = t.get("workers") or {}
        for _, names in workers.items():
            if isinstance(names, list):
                for name in names:
                    worker_set.add(name)

    by_equipment = {}
    for t in tasks:
        eq_name = t.get("equipment_name") or t.get("equipment_id") or "未知"
        by_equipment[eq_name] = by_equipment.get(eq_name, 0) + 1

    # 计算工时和成本
    common_hours = 0
    skilled_hours = 0
    senior_hours = 0
    PRICE_COMMON = 126
    PRICE_SKILLED = 173
    PRICE_SENIOR = 236

    for task in tasks:
        wp = task.get("worker_price")
        if wp:
            try:
                parts = str(wp).split(",")
                if len(parts) >= 3:
                    common_hours += float(parts[0] or 0)
                    skilled_hours += float(parts[1] or 0)
                    senior_hours += float(parts[2] or 0)
            except (ValueError, TypeError):
                pass

    estimated_cost = common_hours * PRICE_COMMON + skilled_hours * PRICE_SKILLED + senior_hours * PRICE_SENIOR

    return {
        "total_tasks": len(tasks),
        "total_duration_days": round(total_duration, 2),
        "start_time": start_time,
        "end_time": end_time,
        "start_time_formatted": tasks[start_idx]["start_time_formatted"] if start_idx is not None else None,
        "end_time_formatted": tasks[end_idx]["end_time_formatted"] if end_idx is not None else None,
        "worker_count": len(worker_set),
        "workers": sorted(worker_set),
        "by_equipment": by_equipment,
        "estimated_cost": round(estimated_cost, 2),
        "common_hours": round(common_hours, 3),
        "skilled_hours": round(skilled_hours, 3),
        "senior_hours": round(senior_hours, 3),
    }


def _compute_task_diff(tasks1, tasks2):
    """计算任务级差异

    按 (equipment_id, process_id) 对齐两个方案的任务，标记差异类型：
    - added: 方案2有但方案1没有
    - removed: 方案1有但方案2没有
    - changed: 两方案都有但有字段差异（时间/工人/工期）
    - unchanged: 完全相同
    """
    map1 = {(t.get("equipment_id"), t.get("process_id")): t for t in tasks1}
    map2 = {(t.get("equipment_id"), t.get("process_id")): t for t in tasks2}

    all_keys = set(map1.keys()) | set(map2.keys())

    diff_list = []
    for key in sorted(all_keys, key=lambda k: (str(k[0]), str(k[1]))):
        t1 = map1.get(key)
        t2 = map2.get(key)

        if t1 and not t2:
            diff_list.append({
                "key": list(key),
                "status": "removed",
                "task1": t1,
                "task2": None,
                "changes": ["方案1独有"],
            })
        elif t2 and not t1:
            diff_list.append({
                "key": list(key),
                "status": "added",
                "task1": None,
                "task2": t2,
                "changes": ["方案2独有"],
            })
        else:
            changes = []
            if t1.get("start_time") != t2.get("start_time") or t1.get("end_time") != t2.get("end_time"):
                changes.append("时间变化")
            w1 = t1.get("workers") or {}
            w2 = t2.get("workers") or {}
            if w1 != w2:
                changes.append("工人变化")
            if t1.get("duration_days") != t2.get("duration_days"):
                changes.append("工期变化")

            diff_list.append({
                "key": list(key),
                "status": "changed" if changes else "unchanged",
                "task1": t1,
                "task2": t2,
                "changes": changes,
            })

    summary = {
        "total": len(diff_list),
        "added": sum(1 for d in diff_list if d["status"] == "added"),
        "removed": sum(1 for d in diff_list if d["status"] == "removed"),
        "changed": sum(1 for d in diff_list if d["status"] == "changed"),
        "unchanged": sum(1 for d in diff_list if d["status"] == "unchanged"),
    }

    return {
        "summary": summary,
        "items": diff_list,
    }


# ======================== 切换生效方案 ========================

@workorder_mgmt_bp.route("/schedule-plans/<int:schedule_plan_id>/activate", methods=["PUT"])
def activate_schedule_plan(schedule_plan_id):
    """将指定调度方案设为生效

    - 将该方案 status 改为 '生效中'
    - 同 plan_id 下其他方案改为 '已归档'
    - 更新 maintenance_plans.schedule_plan_id 指向该方案
    """
    try:
        with get_db_connection(row_factory=sqlite3.Row) as conn:
            c = conn.cursor()

            c.execute(
                "SELECT id, plan_id, schedule_name FROM schedule_plans WHERE id = ?",
                (schedule_plan_id,),
            )
            plan = c.fetchone()
            if not plan:
                return jsonify({"success": False, "message": "调度方案不存在"}), 404

            plan_id = plan["plan_id"]
            schedule_name = plan["schedule_name"]

            if not plan_id:
                return jsonify({"success": False, "message": "该方案未关联检修计划，无法切换生效"}), 400

            # 同计划下其他生效方案改为已归档
            c.execute(
                "UPDATE schedule_plans SET status = '已归档' WHERE plan_id = ? AND id != ? AND status = '生效中'",
                (plan_id, schedule_plan_id),
            )
            # 目标方案设为生效中
            c.execute(
                "UPDATE schedule_plans SET status = '生效中' WHERE id = ?",
                (schedule_plan_id,),
            )
            # 更新 maintenance_plans.schedule_plan_id 指向
            c.execute(
                "UPDATE maintenance_plans SET schedule_plan_id = ?, updated_at = ? WHERE id = ?",
                (
                    str(schedule_plan_id),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    plan_id,
                ),
            )

            conn.commit()

        return jsonify({
            "success": True,
            "message": f"方案「{schedule_name}」已设为生效",
            "data": {
                "schedule_plan_id": schedule_plan_id,
                "plan_id": plan_id,
                "schedule_name": schedule_name,
            },
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e), "message": "切换生效方案失败"}), 500
