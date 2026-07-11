"""Materials (辅助物料台账) CRUD API blueprint.

Uses the project-standard Result response format so the frontend
response interceptor (which checks ``code == 20000``) accepts every reply.
"""
from flask import Blueprint, request
import datetime
from app.models import Result
from app.utils import get_db_connection

materials_bp = Blueprint("materials", __name__)


# ---------------------------------------------------------------------------
# GET  /api/materials  –  list all materials
# ---------------------------------------------------------------------------
@materials_bp.route("/materials", methods=["GET"])
def get_materials():
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute(
            """
            SELECT id, name, price, stock_quantity, unit, created_at, updated_at
            FROM materials
            ORDER BY created_at DESC
            """
        )
        materials = []
        for row in c.fetchall():
            materials.append(
                {
                    "id": row[0],
                    "name": row[1],
                    "price": float(row[2]) if row[2] != "-" else 0,
                    "stock_quantity": float(row[3]) if row[3] != "-" else 0,
                    "unit": row[4],
                    "created_at": row[5],
                    "updated_at": row[6],
                }
            )
        conn.close()
        return Result.success(
            data={"materials": materials, "total_count": len(materials)},
            message="查询成功",
        )
    except Exception as e:
        return Result.fail(message=f"获取材料列表失败: {str(e)}")


# ---------------------------------------------------------------------------
# POST  /api/materials  –  add a single material
# ---------------------------------------------------------------------------
@materials_bp.route("/materials", methods=["POST"])
def add_material():
    try:
        data = request.get_json()
        name = data.get("name")
        price = data.get("price")
        stock_quantity = data.get("stock_quantity")
        unit = data.get("unit")

        if not all([name, price is not None, stock_quantity is not None, unit]):
            return Result.fail(message="材料名称、单价、库存数量和计量单位不能为空")

        try:
            price = float(price)
            stock_quantity = float(stock_quantity)
        except (ValueError, TypeError):
            return Result.fail(message="单价和库存数量必须是数字")

        conn = get_db_connection()
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO materials (name, price, stock_quantity, unit, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                price,
                stock_quantity,
                unit,
                datetime.datetime.now(),
                datetime.datetime.now(),
            ),
        )
        material_id = c.lastrowid
        conn.commit()
        conn.close()

        return Result.success(
            data={"material_id": material_id},
            message=f"材料 {name} 添加成功",
        )
    except Exception as e:
        return Result.fail(message=f"添加材料失败: {str(e)}")


# ---------------------------------------------------------------------------
# POST  /api/batch-import-materials  –  batch import from Excel
# ---------------------------------------------------------------------------
@materials_bp.route("/batch-import-materials", methods=["POST"])
def batch_import_materials():
    try:
        data = request.get_json()
        materials_list = data.get("materials_list", [])

        if not materials_list:
            return Result.fail(message="材料列表不能为空")

        conn = get_db_connection()
        c = conn.cursor()

        success_count = 0
        error_messages = []

        for material in materials_list:
            try:
                name = material.get("name")
                price = material.get("price")
                stock_quantity = material.get("stock_quantity")
                unit = material.get("unit")

                if not all(
                    [name, price is not None, stock_quantity is not None, unit]
                ):
                    error_messages.append(f"材料 {name} 的必填字段不完整")
                    continue

                try:
                    price = float(price)
                    stock_quantity = float(stock_quantity)
                except (ValueError, TypeError):
                    error_messages.append(f"材料 {name} 的单价或库存数量格式错误")
                    continue

                c.execute(
                    """
                    INSERT INTO materials (name, price, stock_quantity, unit, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        name,
                        price,
                        stock_quantity,
                        unit,
                        datetime.datetime.now(),
                        datetime.datetime.now(),
                    ),
                )
                success_count += 1
            except Exception as e:
                error_messages.append(
                    f"材料 {material.get('name', '未知')} 导入失败: {str(e)}"
                )

        conn.commit()
        conn.close()

        return Result.success(
            data={
                "success_count": success_count,
                "error_count": len(error_messages),
                "errors": error_messages,
            },
            message=f"成功导入 {success_count} 个材料",
        )
    except Exception as e:
        return Result.fail(message=f"批量导入材料失败: {str(e)}")


# ---------------------------------------------------------------------------
# DELETE  /api/materials/<id>  –  delete a material
# ---------------------------------------------------------------------------
@materials_bp.route("/materials/<int:material_id>", methods=["DELETE"])
def delete_material(material_id):
    try:
        conn = get_db_connection()
        c = conn.cursor()

        c.execute("SELECT name FROM materials WHERE id = ?", (material_id,))
        row = c.fetchone()
        if not row:
            conn.close()
            return Result.fail(message="材料不存在")

        material_name = row[0]
        c.execute("DELETE FROM materials WHERE id = ?", (material_id,))
        conn.commit()
        conn.close()

        return Result.success(message=f"材料 {material_name} 删除成功")
    except Exception as e:
        return Result.fail(message=f"删除材料失败: {str(e)}")


# ---------------------------------------------------------------------------
# PUT  /api/materials/<id>  –  update a material
# ---------------------------------------------------------------------------
@materials_bp.route("/materials/<int:material_id>", methods=["PUT"])
def update_material(material_id):
    try:
        data = request.get_json()

        conn = get_db_connection()
        c = conn.cursor()

        c.execute("SELECT id FROM materials WHERE id = ?", (material_id,))
        if not c.fetchone():
            conn.close()
            return Result.fail(message="材料不存在")

        # Build dynamic UPDATE based on provided fields
        allowed_fields = ["name", "price", "stock_quantity", "unit"]
        updates = {}
        for field in allowed_fields:
            if field in data and data[field] is not None:
                val = data[field]
                if field in ("price", "stock_quantity"):
                    try:
                        val = float(val)
                    except (ValueError, TypeError):
                        conn.close()
                        return Result.fail(message=f"{field} 必须是数字")
                updates[field] = val

        if not updates:
            conn.close()
            return Result.fail(message="没有可更新的字段")

        updates["updated_at"] = datetime.datetime.now()

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [material_id]

        c.execute(
            f"UPDATE materials SET {set_clause} WHERE id = ?", values
        )
        conn.commit()
        conn.close()

        return Result.success(message="材料更新成功")
    except Exception as e:
        return Result.fail(message=f"更新材料失败: {str(e)}")
