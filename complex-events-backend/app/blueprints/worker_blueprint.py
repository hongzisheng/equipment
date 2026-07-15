"""Worker (工人台账) CRUD API blueprint.

Uses the project-standard Result response format so the frontend
response interceptor (which checks ``code == 20000``) accepts every reply.
"""
from flask import Blueprint, request
import datetime
from app.models import Result
from app.utils import get_db_connection

worker_bp = Blueprint("worker", __name__)


# ---------------------------------------------------------------------------
# GET  /api/workers  –  list all workers
# ---------------------------------------------------------------------------
@worker_bp.route("/workers", methods=["GET"])
def get_workers():
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute(
                """
                SELECT w.id, w.name, w.worker_type_id, w.is_certified,
                       w.organization, w.emp_id, w.compose, w.created_time,
                       w.status,
                       COALESCE(wt.name, w.worker_type_id) AS worker_type_name
                FROM workers w
                LEFT JOIN worker_types wt ON w.worker_type_id = wt.id
                ORDER BY w.id
                """
            )
            workers = []
            for row in c.fetchall():
                workers.append(
                    {
                        "id": row[0],
                        "name": row[1],
                        "worker_type_id": row[2],
                        "is_certified": row[3],
                        "organization": row[4] or "",
                        "emp_id": row[5],
                        "compose": row[6] or "",
                        "created_time": row[7],
                        "status": row[8],
                        "worker_type": row[9],
                    }
                )
        return Result.success(
            data={"workers": workers, "total_count": len(workers)},
            message="查询成功",
        )
    except Exception as e:
        return Result.fail(message=f"获取工人信息失败: {str(e)}")


# ---------------------------------------------------------------------------
# POST  /api/add-worker  –  add a single worker
# ---------------------------------------------------------------------------
@worker_bp.route("/add-worker", methods=["POST"])
def add_worker():
    try:
        data = request.get_json()
        worker_type = data.get("worker_type")
        worker_name = data.get("worker_name")
        is_certified = data.get("is_certified", 0)
        organization = data.get("organization", "")
        compose = data.get("compose", "")

        if not worker_type or not worker_name:
            return Result.fail(message="工人工种和工人名称不能为空")

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute(
                """
                INSERT INTO workers
                    (worker_type_id, name, is_certified, organization, compose, created_time)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (worker_type, worker_name, int(is_certified), organization, compose, now),
            )
            conn.commit()

        return Result.success(message=f"工人 {worker_name}({worker_type}) 添加成功")
    except Exception as e:
        return Result.fail(message=f"添加工人失败: {str(e)}")


# ---------------------------------------------------------------------------
# PUT  /api/workers/<id>  –  update a worker
# ---------------------------------------------------------------------------
@worker_bp.route("/workers/<int:worker_id>", methods=["PUT"])
def update_worker(worker_id):
    try:
        data = request.get_json()

        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT name FROM workers WHERE id = ?", (worker_id,))
            row = c.fetchone()
            if not row:
                return Result.fail(message="工人不存在")

            allowed_fields = {
                "name": str,
                "worker_type": str,
                "is_certified": lambda v: 1 if v == "是" or v == 1 or v is True else 0,
                "organization": str,
                "compose": str,
            }
            updates = {}
            for field, cast in allowed_fields.items():
                if field in data and data[field] is not None:
                    try:
                        updates[field] = cast(data[field])
                    except (ValueError, TypeError):
                        return Result.fail(message=f"{field} 格式不正确")

            # Map worker_type → worker_type_id column
            if "worker_type" in updates:
                updates["worker_type_id"] = updates.pop("worker_type")

            if not updates:
                return Result.fail(message="没有可更新的字段")

            set_clause = ", ".join(f"{k} = ?" for k in updates)
            values = list(updates.values()) + [worker_id]

            c.execute(f"UPDATE workers SET {set_clause} WHERE id = ?", values)
            conn.commit()

        return Result.success(message=f"工人 {row[0]} 更新成功")
    except Exception as e:
        return Result.fail(message=f"更新工人失败: {str(e)}")


# ---------------------------------------------------------------------------
# DELETE  /api/workers/<id>  –  delete a worker
# ---------------------------------------------------------------------------
@worker_bp.route("/workers/<int:worker_id>", methods=["DELETE"])
def delete_worker(worker_id):
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT name, worker_type_id FROM workers WHERE id = ?", (worker_id,)
            )
            row = c.fetchone()
            if not row:
                return Result.fail(message="工人不存在")

            worker_name, worker_type = row[0], row[1]
            c.execute("DELETE FROM workers WHERE id = ?", (worker_id,))
            conn.commit()

        return Result.success(message=f"工人 {worker_name}({worker_type}) 删除成功")
    except Exception as e:
        return Result.fail(message=f"删除工人失败: {str(e)}")


# ---------------------------------------------------------------------------
# POST  /api/batch-import-workers  –  batch import from Excel
# ---------------------------------------------------------------------------
@worker_bp.route("/batch-import-workers", methods=["POST"])
def batch_import_workers():
    try:
        data = request.get_json()
        workers_list = data.get("workers_list", [])

        if not workers_list:
            return Result.fail(message="工人列表不能为空")

        with get_db_connection() as conn:
            c = conn.cursor()

            success_count = 0
            error_messages = []

            for worker in workers_list:
                try:
                    worker_type = worker.get("worker_type")
                    worker_name = worker.get("worker_name")
                    certified = worker.get("is_certified", False)
                    organization = worker.get("organization", "")
                    compose = worker.get("compose", "")

                    if not worker_type or not worker_name:
                        error_messages.append(
                            f"工人工种和工人名称不能为空: {worker}"
                        )
                        continue

                    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    c.execute(
                        """
                        INSERT INTO workers
                            (worker_type_id, name, is_certified, organization, compose, created_time)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            worker_type,
                            worker_name,
                            int(certified) if certified else 0,
                            organization,
                            compose,
                            now,
                        ),
                    )
                    success_count += 1
                except Exception as e:
                    error_messages.append(
                        f"工人 {worker.get('worker_name', '未知')} 导入失败: {str(e)}"
                    )

            conn.commit()

        return Result.success(
            data={
                "success_count": success_count,
                "error_count": len(error_messages),
                "errors": error_messages,
            },
            message=f"成功导入 {success_count} 个工人",
        )
    except Exception as e:
        return Result.fail(message=f"批量导入工人失败: {str(e)}")
