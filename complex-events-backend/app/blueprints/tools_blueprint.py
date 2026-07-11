"""Maintenance tools (维修机具台账) CRUD API blueprint.

Uses the project-standard Result response format so the frontend
response interceptor (which checks ``code == 20000``) accepts every reply.
"""
from flask import Blueprint, request
import datetime
from app.models import Result
from app.utils import get_db_connection

tools_bp = Blueprint("tools", __name__)


# ---------------------------------------------------------------------------
# GET  /api/maintenance-tools  –  list all tools
# ---------------------------------------------------------------------------
@tools_bp.route("/maintenance-tools", methods=["GET"])
def get_maintenance_tools():
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute(
            """
            SELECT id, name, tool_type, capacity, daily_rental_cost,
                   is_available, requires_operator, created_at, updated_at
            FROM maintenance_tools
            ORDER BY id
            """
        )
        tools = []
        for row in c.fetchall():
            tools.append(
                {
                    "id": row[0],
                    "name": row[1],
                    "tool_type": row[2],
                    "capacity": row[3],
                    "daily_rental_cost": float(row[4]) if row[4] is not None else 0,
                    "is_available": bool(row[5]),
                    "requires_operator": bool(row[6]),
                    "created_at": row[7],
                    "updated_at": row[8],
                }
            )
        conn.close()
        return Result.success(
            data={"maintenance_tools": tools, "total_count": len(tools)},
            message="查询成功",
        )
    except Exception as e:
        return Result.fail(message=f"获取维修器具列表失败: {str(e)}")


# ---------------------------------------------------------------------------
# GET  /api/maintenance-tools/<id>  –  get one tool by id
# ---------------------------------------------------------------------------
@tools_bp.route("/maintenance-tools/<int:tool_id>", methods=["GET"])
def get_maintenance_tool(tool_id):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute(
            """
            SELECT id, name, tool_type, capacity, daily_rental_cost,
                   is_available, requires_operator, created_at, updated_at
            FROM maintenance_tools
            WHERE id = ?
            """,
            (tool_id,),
        )
        row = c.fetchone()
        conn.close()

        if not row:
            return Result.fail(message="维修器具不存在")

        tool = {
            "id": row[0],
            "name": row[1],
            "tool_type": row[2],
            "capacity": row[3],
            "daily_rental_cost": float(row[4]) if row[4] is not None else 0,
            "is_available": bool(row[5]),
            "requires_operator": bool(row[6]),
            "created_at": row[7],
            "updated_at": row[8],
        }
        return Result.success(data={"maintenance_tool": tool}, message="查询成功")
    except Exception as e:
        return Result.fail(message=f"获取维修器具信息失败: {str(e)}")


# ---------------------------------------------------------------------------
# POST  /api/maintenance-tools  –  add a single tool
# ---------------------------------------------------------------------------
@tools_bp.route("/maintenance-tools", methods=["POST"])
def add_maintenance_tool():
    try:
        data = request.get_json()
        name = data.get("name")
        tool_type = data.get("tool_type")
        capacity = data.get("capacity")
        daily_rental_cost = data.get("daily_rental_cost")
        is_available = data.get("is_available", True)
        requires_operator = data.get("requires_operator", False)

        if not all([name, tool_type, capacity is not None, daily_rental_cost is not None]):
            return Result.fail(message="器具名称、类型、容量和日租金不能为空")

        try:
            capacity = float(capacity)
            daily_rental_cost = float(daily_rental_cost)
        except (ValueError, TypeError):
            return Result.fail(message="容量和日租金必须是数字")

        now = datetime.datetime.now()
        conn = get_db_connection()
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO maintenance_tools
                (name, tool_type, capacity, daily_rental_cost,
                 is_available, requires_operator, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                tool_type,
                capacity,
                daily_rental_cost,
                bool(is_available),
                bool(requires_operator),
                now,
                now,
            ),
        )
        tool_id = c.lastrowid
        conn.commit()
        conn.close()

        return Result.success(
            data={"tool_id": tool_id}, message=f"维修器具 {name} 添加成功"
        )
    except Exception as e:
        return Result.fail(message=f"添加维修器具失败: {str(e)}")


# ---------------------------------------------------------------------------
# PUT  /api/maintenance-tools/<id>  –  update a tool
# ---------------------------------------------------------------------------
@tools_bp.route("/maintenance-tools/<int:tool_id>", methods=["PUT"])
def update_maintenance_tool(tool_id):
    try:
        data = request.get_json()

        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT name FROM maintenance_tools WHERE id = ?", (tool_id,))
        row = c.fetchone()
        if not row:
            conn.close()
            return Result.fail(message="维修器具不存在")

        allowed_fields = {
            "name": str,
            "tool_type": str,
            "capacity": float,
            "daily_rental_cost": float,
            "is_available": bool,
            "requires_operator": bool,
        }
        updates = {}
        for field, cast in allowed_fields.items():
            if field in data and data[field] is not None:
                try:
                    updates[field] = cast(data[field])
                except (ValueError, TypeError):
                    conn.close()
                    return Result.fail(message=f"{field} 格式不正确")

        if not updates:
            conn.close()
            return Result.fail(message="没有可更新的字段")

        updates["updated_at"] = datetime.datetime.now()
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [tool_id]

        c.execute(f"UPDATE maintenance_tools SET {set_clause} WHERE id = ?", values)
        conn.commit()
        conn.close()

        return Result.success(message=f"维修器具 {row[0]} 更新成功")
    except Exception as e:
        return Result.fail(message=f"更新维修器具失败: {str(e)}")


# ---------------------------------------------------------------------------
# DELETE  /api/maintenance-tools/<id>  –  delete a tool
# ---------------------------------------------------------------------------
@tools_bp.route("/maintenance-tools/<int:tool_id>", methods=["DELETE"])
def delete_maintenance_tool(tool_id):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT name FROM maintenance_tools WHERE id = ?", (tool_id,))
        row = c.fetchone()
        if not row:
            conn.close()
            return Result.fail(message="维修器具不存在")

        tool_name = row[0]
        c.execute("DELETE FROM maintenance_tools WHERE id = ?", (tool_id,))
        conn.commit()
        conn.close()

        return Result.success(message=f"维修器具 {tool_name} 删除成功")
    except Exception as e:
        return Result.fail(message=f"删除维修器具失败: {str(e)}")


# ---------------------------------------------------------------------------
# POST  /api/batch-import-maintenance-tools  –  batch import from Excel
# ---------------------------------------------------------------------------
@tools_bp.route("/batch-import-maintenance-tools", methods=["POST"])
def batch_import_maintenance_tools():
    try:
        data = request.get_json()
        tools_list = data.get("tools_list", [])

        if not tools_list:
            return Result.fail(message="维修器具列表不能为空")

        conn = get_db_connection()
        c = conn.cursor()

        success_count = 0
        error_messages = []

        for tool in tools_list:
            try:
                name = tool.get("name")
                tool_type = tool.get("tool_type")
                capacity = tool.get("capacity")
                daily_rental_cost = tool.get("daily_rental_cost")
                is_available = tool.get("is_available", True)
                requires_operator = tool.get("requires_operator", False)

                if not all([name, tool_type, capacity is not None, daily_rental_cost is not None]):
                    error_messages.append(f"维修器具 {name} 的必填字段不完整")
                    continue

                try:
                    capacity = float(capacity)
                    daily_rental_cost = float(daily_rental_cost)
                except (ValueError, TypeError):
                    error_messages.append(f"维修器具 {name} 的容量或日租金格式错误")
                    continue

                now = datetime.datetime.now()
                c.execute(
                    """
                    INSERT INTO maintenance_tools
                        (name, tool_type, capacity, daily_rental_cost,
                         is_available, requires_operator, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        name,
                        tool_type,
                        capacity,
                        daily_rental_cost,
                        bool(is_available),
                        bool(requires_operator),
                        now,
                        now,
                    ),
                )
                success_count += 1
            except Exception as e:
                error_messages.append(
                    f"维修器具 {tool.get('name', '未知')} 导入失败: {str(e)}"
                )

        conn.commit()
        conn.close()

        return Result.success(
            data={
                "success_count": success_count,
                "error_count": len(error_messages),
                "errors": error_messages,
            },
            message=f"成功导入 {success_count} 个维修器具",
        )
    except Exception as e:
        return Result.fail(message=f"批量导入维修器具失败: {str(e)}")
