"""Equipment scheduling API blueprint."""
from flask import Blueprint, request
from app.models import Result
from app.utils import get_db_connection

scheduling_equipment_bp = Blueprint('scheduling_equipment', __name__)


@scheduling_equipment_bp.route('/equipment-categories', methods=['GET'])
def get_equipment_categories():
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute('SELECT category_id, category_name FROM equipment_category ORDER BY category_id')
            rows = c.fetchall()
        return Result.success(
            data=[{'id': row[0], 'name': row[1]} for row in rows],
            message="查询成功",
        )
    except Exception as e:
        return Result.fail(message=f"获取设备分类失败: {str(e)}")


@scheduling_equipment_bp.route('/equipment-types-with-category', methods=['GET'])
def get_equipment_types_with_category():
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute('SELECT id, name, category FROM equipment_types ORDER BY id')
            rows = c.fetchall()
        return Result.success(
            data=[{'id': row[0], 'name': row[1], 'category': row[2]} for row in rows],
            message="查询成功",
        )
    except Exception as e:
        return Result.fail(message=f"获取设备类型失败: {str(e)}")


@scheduling_equipment_bp.route('/equipment-types', methods=['GET'])
def get_equipment_types():
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute('SELECT id, name FROM equipment_types')
            rows = c.fetchall()
        return Result.success(
            data=[{'id': row[0], 'name': row[1]} for row in rows],
            message="查询成功",
        )
    except Exception as e:
        return Result.fail(message=f"获取设备类型失败: {str(e)}")


@scheduling_equipment_bp.route('/select-equipments', methods=['POST'])
def select_equipments():
    try:
        data = request.get_json()
        selected_equipment_ids = data.get('selected_equipment_ids', [])
        if not selected_equipment_ids:
            return Result.fail(message="请选择至少一个设备")

        with get_db_connection() as conn:
            c = conn.cursor()
            placeholders = ','.join('?' * len(selected_equipment_ids))
            c.execute(f'''
                SELECT id, name, equipment_type_id, equipment_type_name, category
                FROM equipment_instances WHERE id IN ({placeholders})
            ''', selected_equipment_ids)
            selected_equipments = c.fetchall()
            if len(selected_equipments) != len(selected_equipment_ids):
                return Result.fail(message="部分设备ID不存在")

            c.execute('DELETE FROM selected_equipments')
            for eq in selected_equipments:
                c.execute(
                    'INSERT INTO selected_equipments (id, name, equipment_type_id, equipment_type_name, category) VALUES (?, ?, ?, ?, ?)',
                    eq,
                )
        return Result.success(
            data={"selected_count": len(selected_equipments)},
            message=f"成功选择 {len(selected_equipments)} 台设备",
        )
    except Exception as e:
        return Result.fail(message=f"设置选中设备失败: {str(e)}")


@scheduling_equipment_bp.route('/selected-equipments', methods=['GET'])
def get_selected_equipments():
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute('SELECT se.id, se.name, se.equipment_type_id, se.equipment_type_name, se.category FROM selected_equipments se ORDER BY se.equipment_type_id, se.id')
            selected_equipments = []
            for row in c.fetchall():
                selected_equipments.append({
                    'id': row[0], 'name': row[1], 'equipment_type_id': row[2],
                    'equipment_type_name': row[3], 'category': row[4]
                })
        return Result.success(
            data={"selected_equipments": selected_equipments, "total_count": len(selected_equipments)},
            message="查询成功",
        )
    except Exception as e:
        return Result.fail(message=f"获取选中设备失败: {str(e)}")


@scheduling_equipment_bp.route('/equipment-instances/by-type/<string:equipment_type_id>', methods=['GET'])
def get_equipment_instances_by_type(equipment_type_id):
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute('SELECT name FROM equipment_types WHERE id = ?', (equipment_type_id,))
            type_row = c.fetchone()
            if not type_row:
                return Result.fail(message=f"设备类型 ID {equipment_type_id} 不存在")

            c.execute('''
                SELECT id, name, equipment_type_id, category, created_time
                FROM equipment_instances WHERE equipment_type_id = ? ORDER BY id
            ''', (equipment_type_id,))
            rows = c.fetchall()
            instances = []
            for row in rows:
                instances.append({
                    'id': row[0], 'name': row[1], 'equipment_type_id': row[2],
                    'category': row[3] if row[3] else '', 'created_time': row[4]
                })
        return Result.success(
            data={"equipment_instances": instances, "total_count": len(instances), "equipment_type_name": type_row[0]},
            message="查询成功",
        )
    except Exception as e:
        return Result.fail(message=f"根据设备类型查询设备实例失败: {str(e)}")
