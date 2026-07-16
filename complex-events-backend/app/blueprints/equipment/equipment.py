"""Equipment (设备台账) CRUD API blueprint.

Uses the project-standard Result response format so the frontend
response interceptor (which checks ``code == 20000``) accepts every reply.
"""
import json

from flask import Blueprint, request
import datetime
from app.models import Result
from app.utils import get_db_connection

equipment_bp = Blueprint("equipment", __name__)


# ---------------------------------------------------------------------------
# GET  /api/equipment-instances  –  list all equipment instances
# ---------------------------------------------------------------------------
@equipment_bp.route("/equipment-instances", methods=["GET"])
def get_equipment_instances():
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute(
                """
                SELECT id, name, equipment_type_id, equipment_type_name,
                       category, created_time
                FROM equipment_instances
                ORDER BY id
                """
            )
            instances = []
            for row in c.fetchall():
                instances.append(
                    {
                        "id": row[0],
                        "name": row[1],
                        "equipment_type_id": row[2],
                        "equipment_type_name": row[3] if row[3] else "",
                        "category": row[4] if row[4] else "",
                        "created_time": row[5],
                    }
                )
        return Result.success(
            data=instances,
            message="查询成功",
        )
    except Exception as e:
        return Result.fail(message=f"获取设备实例失败: {str(e)}")


# ---------------------------------------------------------------------------
# GET  /api/equipment-instances/<id>  –  get one equipment instance
# ---------------------------------------------------------------------------
@equipment_bp.route("/equipment-instances/<int:equipment_id>", methods=["GET"])
def get_equipment_instance(equipment_id):
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute(
                """
                SELECT ei.id, ei.name, ei.equipment_type_id,
                       et.name as equipment_type_name,
                       et.description, ei.created_time, ei.category
                FROM equipment_instances ei
                LEFT JOIN equipment_types et ON ei.equipment_type_id = et.id
                WHERE ei.id = ?
                """,
                (equipment_id,),
            )
            row = c.fetchone()

        if not row:
            return Result.fail(message="设备不存在")

        equipment = {
            "id": row[0],
            "name": row[1],
            "equipment_type_id": row[2],
            "equipment_type_name": row[3] if row[3] else "未知类型",
            "equipment_type_description": row[4] if row[4] else "",
            "created_time": row[5],
            "category": row[6] if row[6] else "",
        }
        return Result.success(data=equipment, message="查询成功")
    except Exception as e:
        return Result.fail(message=f"获取设备信息失败: {str(e)}")


# ---------------------------------------------------------------------------
# POST  /api/add-equipment  –  add a single equipment instance
# ---------------------------------------------------------------------------
@equipment_bp.route("/add-equipment", methods=["POST"])
def add_equipment():
    try:
        data = request.get_json()
        equipment_type_id = data.get("equipment_type_id")
        equipment_name = data.get("equipment_name")
        equipment_category = data.get("equipment_category", "")

        if not equipment_type_id or not equipment_name:
            return Result.fail(message="设备种类和设备名称不能为空")

        now = datetime.datetime.now()
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute(
                """
                INSERT INTO equipment_instances
                    (equipment_type_id, name, created_time, category)
                VALUES (?, ?, ?, ?)
                """,
                (equipment_type_id, equipment_name, now, equipment_category),
            )
            conn.commit()

        return Result.success(message=f"设备 {equipment_name} 添加成功")
    except Exception as e:
        return Result.fail(message=f"添加设备失败: {str(e)}")


# ---------------------------------------------------------------------------
# DELETE  /api/equipment-instances/<id>  –  delete an equipment instance
# ---------------------------------------------------------------------------
@equipment_bp.route("/equipment-instances/<int:equipment_id>", methods=["DELETE"])
def delete_equipment_instance(equipment_id):
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT name FROM equipment_instances WHERE id = ?", (equipment_id,)
            )
            row = c.fetchone()
            if not row:
                return Result.fail(message="设备不存在")

            equipment_name = row[0]
            c.execute("DELETE FROM equipment_instances WHERE id = ?", (equipment_id,))
            conn.commit()

        return Result.success(message=f"设备 {equipment_name} 删除成功")
    except Exception as e:
        return Result.fail(message=f"删除设备失败: {str(e)}")


# ---------------------------------------------------------------------------
# PUT  /api/equipment-instances/<id>  –  update an equipment instance
# ---------------------------------------------------------------------------
@equipment_bp.route("/equipment-instances/<int:equipment_id>", methods=["PUT"])
def update_equipment_instance(equipment_id):
    try:
        data = request.get_json()
        name = data.get("name")
        category = data.get("category")
        equipment_type_id = data.get("equipment_type_id")

        if not name:
            return Result.fail(message="设备名称不能为空")

        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT id FROM equipment_instances WHERE id = ?", (equipment_id,)
            )
            if not c.fetchone():
                return Result.fail(message="设备不存在")

            c.execute(
                """UPDATE equipment_instances
                   SET name = ?,
                       category = ?,
                       equipment_type_id = ?
                   WHERE id = ?""",
                (name, category, equipment_type_id, equipment_id),
            )
            conn.commit()

        return Result.success(message=f"设备 {name} 更新成功")
    except Exception as e:
        return Result.fail(message=f"更新设备失败: {str(e)}")


# ---------------------------------------------------------------------------
# POST  /api/batch-import-equipment  –  batch import from Excel
# ---------------------------------------------------------------------------
@equipment_bp.route("/batch-import-equipment", methods=["POST"])
def batch_import_equipment():
    try:
        data = request.get_json()
        equipment_list = data.get("equipment_list", [])

        if not equipment_list:
            return Result.fail(message="设备列表不能为空")

        with get_db_connection() as conn:
            c = conn.cursor()

            success_count = 0
            error_messages = []

            for equipment in equipment_list:
                try:
                    equipment_type_id = equipment.get("equipment_type_id")
                    equipment_name = equipment.get("equipment_name") or equipment.get("name")
                    equipment_category = equipment.get("equipment_category") or equipment.get("category", "")

                    if not equipment_type_id or not equipment_name:
                        error_messages.append(
                            f"设备类型ID和设备名称不能为空: {equipment}"
                        )
                        continue

                    now = datetime.datetime.now()
                    c.execute(
                        """
                        INSERT INTO equipment_instances
                            (equipment_type_id, name, created_time, category)
                        VALUES (?, ?, ?, ?)
                        """,
                        (equipment_type_id, equipment_name, now, equipment_category),
                    )
                    success_count += 1
                except Exception as e:
                    error_messages.append(
                        f"设备 {equipment.get('equipment_name', '未知')} 导入失败: {str(e)}"
                    )

            conn.commit()

        return Result.success(
            data={
                "success_count": success_count,
                "error_count": len(error_messages),
                "errors": error_messages,
            },
            message=f"成功导入 {success_count} 个设备实例",
        )
    except Exception as e:
        return Result.fail(message=f"批量导入设备失败: {str(e)}")


# ---------------------------------------------------------------------------
# GET  /api/work-order-tasks  –  list all work order tasks
# (used by equipment ledger's maintenance history feature)
# ---------------------------------------------------------------------------
@equipment_bp.route("/work-order-tasks", methods=["GET"])
def get_work_order_tasks():
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute(
                """
                SELECT wt.id, wt.work_order_id, wo.order_number,
                       wt.task_code, wt.process_name,
                       wt.equipment_id, wt.equipment_name,
                       wt.description, wt.estimated_hours,
                       wt.scheduled_start_time, wt.scheduled_end_time,
                       wt.status, wt.workers
                FROM work_order_tasks wt
                LEFT JOIN work_orders wo ON wt.work_order_id = wo.id
                ORDER BY wt.work_order_id, wt.id
                """
            )

            tasks = []
            for row in c.fetchall():
                workers = {}
                if row[12]:
                    try:
                        workers = json.loads(row[12])
                    except (json.JSONDecodeError, TypeError):
                        pass

                tasks.append(
                    {
                        "id": row[0],
                        "work_order_id": row[1],
                        "work_order_no": row[2] or f"WO-{row[1]}",
                        "task_code": row[3],
                        "process_name": row[4],
                        "equipment_id": row[5],
                        "equipment_name": row[6],
                        "description": row[7],
                        "estimated_hours": row[8],
                        "scheduled_start_time": row[9],
                        "scheduled_end_time": row[10],
                        "status": row[11] or "",
                        "material_requirements": {},
                        "tools_requirements": {},
                        "workers": workers,
                    }
                )

        return Result.success(data=tasks, message="查询成功")
    except Exception as e:
        return Result.fail(message=f"获取工单任务失败: {str(e)}")


# ---------------------------------------------------------------------------
# GET  /api/equipment-instances/export  –  导出设备数据（返回数据库原始列名和值）
# ---------------------------------------------------------------------------
@equipment_bp.route("/equipment-instances/export", methods=["GET"])
def export_equipment_instances():
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM equipment_instances ORDER BY id")
            columns = [desc[0] for desc in c.description]
            rows = [list(row) for row in c.fetchall()]
        return Result.success(data={"columns": columns, "rows": rows}, message="查询成功")
    except Exception as e:
        return Result.fail(message=f"导出设备数据失败: {str(e)}")