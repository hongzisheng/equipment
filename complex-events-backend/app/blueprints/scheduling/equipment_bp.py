"""Equipment scheduling & CRUD API blueprint."""
from flask import Blueprint, request
import datetime
from app.models import Result
from app.utils import get_db_connection

equipment_bp = Blueprint('equipment', __name__)


@equipment_bp.route('/equipment-categories', methods=['GET'])
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


@equipment_bp.route('/equipment-types-with-category', methods=['GET'])
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


@equipment_bp.route('/equipment-types', methods=['GET'])
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


@equipment_bp.route('/select-equipments', methods=['POST'])
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


@equipment_bp.route('/selected-equipments', methods=['GET'])
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


@equipment_bp.route('/equipment-instances', methods=['GET'])
def get_equipment_instances():
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute('SELECT id, name, equipment_type_id, equipment_type_name, category FROM equipment_instances ORDER BY id')
            rows = c.fetchall()
            instances = []
            for row in rows:
                instances.append({
                    'id': row[0], 'name': row[1], 'equipment_type_id': row[2],
                    'equipment_type_name': row[3] if len(row) > 3 else '',
                    'category': row[4] if len(row) > 4 else ''
                })
        return Result.success(data=instances, message="查询成功")
    except Exception as e:
        return Result.fail(message=f"获取设备实例失败: {str(e)}")


@equipment_bp.route('/equipment-instances/by-type/<string:equipment_type_id>', methods=['GET'])
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


@equipment_bp.route('/add-equipment', methods=['POST'])
def add_equipment():
    try:
        data = request.get_json()
        equipment_type_id = data.get('equipment_type_id')
        equipment_name = data.get('equipment_name')
        equipment_category = data.get('equipment_category')
        if not equipment_type_id or not equipment_name:
            return Result.fail(message="设备种类和设备名称不能为空")

        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute(
                'INSERT INTO equipment_instances (equipment_type_id, name, created_time, category) VALUES (?, ?, ?, ?)',
                (equipment_type_id, equipment_name, datetime.datetime.now(), equipment_category),
            )
        return Result.success(message=f"设备 {equipment_name} 添加成功")
    except Exception as e:
        return Result.fail(message=f"添加设备失败: {str(e)}")


@equipment_bp.route('/batch-import-equipment', methods=['POST'])
def batch_import_equipment():
    try:
        data = request.get_json()
        equipment_list = data.get('equipment_list', [])
        if not equipment_list:
            return Result.fail(message="设备列表不能为空")

        success_count, error_messages = 0, []
        with get_db_connection() as conn:
            c = conn.cursor()
            for equipment in equipment_list:
                try:
                    eid = equipment.get('equipment_type_id')
                    ename = equipment.get('equipment_name')
                    ecat = equipment.get('equipment_category', '')
                    if not eid or not ename:
                        error_messages.append(f"设备类型ID和设备名称不能为空: {equipment}")
                        continue
                    c.execute(
                        'INSERT INTO equipment_instances (equipment_type_id, name, created_time, category) VALUES (?, ?, ?, ?)',
                        (eid, ename, datetime.datetime.now(), ecat),
                    )
                    success_count += 1
                except Exception as e:
                    error_messages.append(f"设备 {equipment.get('equipment_name', '未知')} 导入失败: {str(e)}")

        return Result.success(
            data={"success_count": success_count, "error_count": len(error_messages), "errors": error_messages},
            message=f"成功导入 {success_count} 个设备实例",
        )
    except Exception as e:
        return Result.fail(message=f"批量导入设备失败: {str(e)}")


@equipment_bp.route('/equipment-instances/<int:equipment_id>', methods=['DELETE'])
def delete_equipment_instance(equipment_id):
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute('SELECT name FROM equipment_instances WHERE id = ?', (equipment_id,))
            row = c.fetchone()
            if not row:
                return Result.fail(message="设备不存在")
            c.execute('DELETE FROM equipment_instances WHERE id = ?', (equipment_id,))
        return Result.success(message=f"设备 {row[0]} 删除成功")
    except Exception as e:
        return Result.fail(message=f"删除设备失败: {str(e)}")


@equipment_bp.route('/equipment-instances/<int:equipment_id>', methods=['GET'])
def get_equipment_instance(equipment_id):
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute('''
                SELECT ei.id, ei.name, ei.equipment_type_id, et.name as equipment_type_name,
                       et.description, ei.created_time, ei.category
                FROM equipment_instances ei
                LEFT JOIN equipment_types et ON ei.equipment_type_id = et.id
                WHERE ei.id = ?
            ''', (equipment_id,))
            row = c.fetchone()
            if not row:
                return Result.fail(message="设备不存在")
            equipment = {
                'id': row[0], 'name': row[1], 'equipment_type_id': row[2],
                'equipment_type_name': row[3] if row[3] else '未知类型',
                'equipment_type_description': row[4] if row[4] else '',
                'created_time': row[5], 'category': row[6] if row[6] else '',
            }
        return Result.success(data=equipment, message="查询成功")
    except Exception as e:
        return Result.fail(message=f"获取设备信息失败: {str(e)}")
