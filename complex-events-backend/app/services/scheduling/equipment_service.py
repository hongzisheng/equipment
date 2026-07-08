from datetime import datetime
from typing import Any
from app.services.database_service.sqlite_service import get_connection


scheduler = None


class EquipmentService:

    @staticmethod
    def get_categories() -> list[dict[str, Any]]:
        conn = get_connection()
        c = conn.cursor()
        c.execute('SELECT category_id, category_name FROM equipment_category ORDER BY category_id')
        rows = c.fetchall()
        conn.close()
        return [{'id': row[0], 'name': row[1]} for row in rows]

    @staticmethod
    def get_types_with_category() -> list[dict[str, Any]]:
        conn = get_connection()
        c = conn.cursor()
        c.execute('SELECT id, name, category FROM equipment_types ORDER BY id')
        rows = c.fetchall()
        conn.close()
        return [{'id': row[0], 'name': row[1], 'category': row[2]} for row in rows]

    @staticmethod
    def get_types() -> list[dict[str, Any]]:
        conn = get_connection()
        c = conn.cursor()
        c.execute('SELECT id, name FROM equipment_types')
        rows = c.fetchall()
        conn.close()
        return [{'id': row[0], 'name': row[1]} for row in rows]

    @staticmethod
    def select(equipment_ids: list[int]) -> dict[str, Any]:
        conn = get_connection()
        c = conn.cursor()
        placeholders = ','.join('?' * len(equipment_ids))
        c.execute(f'''
            SELECT id, name, equipment_type_id, equipment_type_name, category
            FROM equipment_instances
            WHERE id IN ({placeholders})
        ''', equipment_ids)
        selected = c.fetchall()
        if len(selected) != len(equipment_ids):
            conn.close()
            raise ValueError('部分设备ID不存在')
        c.execute('DELETE FROM selected_equipments')
        for eq in selected:
            c.execute('''
                INSERT INTO selected_equipments (id, name, equipment_type_id, equipment_type_name, category)
                VALUES (?, ?, ?, ?, ?)
            ''', eq)
        conn.commit()
        conn.close()
        global scheduler
        scheduler = None
        return {'selected_count': len(selected)}

    @staticmethod
    def get_selected() -> list[dict[str, Any]]:
        conn = get_connection()
        c = conn.cursor()
        c.execute('''
            SELECT se.id, se.name, se.equipment_type_id, se.equipment_type_name, se.category
            FROM selected_equipments se
            ORDER BY se.equipment_type_id, se.id
        ''')
        rows = c.fetchall()
        conn.close()
        return [
            {
                'id': row[0],
                'name': row[1],
                'equipment_type_id': row[2],
                'equipment_type_name': row[3],
                'category': row[4],
            }
            for row in rows
        ]

    @staticmethod
    def get_instances() -> list[dict[str, Any]]:
        conn = get_connection()
        c = conn.cursor()
        c.execute('''
            SELECT id, name, equipment_type_id, equipment_type_name, category
            FROM equipment_instances
            ORDER BY id
        ''')
        rows = c.fetchall()
        conn.close()
        return [
            {
                'id': row[0],
                'name': row[1],
                'equipment_type_id': row[2],
                'equipment_type_name': row[3],
                'category': row[4],
            }
            for row in rows
        ]

    @staticmethod
    def get_instances_by_type(equipment_type_id: str) -> tuple[list[dict[str, Any]], str]:
        conn = get_connection()
        c = conn.cursor()
        c.execute('SELECT name FROM equipment_types WHERE id = ?', (equipment_type_id,))
        type_row = c.fetchone()
        if not type_row:
            conn.close()
            raise ValueError(f'设备类型 ID {equipment_type_id} 不存在')
        c.execute('''
            SELECT id, name, equipment_type_id, category, created_time
            FROM equipment_instances
            WHERE equipment_type_id = ?
            ORDER BY id
        ''', (equipment_type_id,))
        rows = c.fetchall()
        conn.close()
        instances = [
            {
                'id': row[0],
                'name': row[1],
                'equipment_type_id': row[2],
                'category': row[3] if row[3] else '',
                'created_time': row[4],
            }
            for row in rows
        ]
        return instances, type_row[0]

    @staticmethod
    def add(equipment_type_id: str, equipment_name: str, equipment_category: str = '') -> None:
        conn = get_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO equipment_instances (equipment_type_id, name, created_time, category)
            VALUES (?, ?, ?, ?)
        ''', (equipment_type_id, equipment_name, datetime.now(), equipment_category))
        conn.commit()
        conn.close()
        global scheduler
        scheduler = None

    @staticmethod
    def batch_import(equipment_list: list[dict[str, Any]]) -> dict[str, Any]:
        conn = get_connection()
        c = conn.cursor()
        success_count = 0
        errors = []
        for eq in equipment_list:
            try:
                equipment_type_id = eq.get('equipment_type_id')
                equipment_name = eq.get('equipment_name')
                equipment_category = eq.get('equipment_category', '')
                if not equipment_type_id or not equipment_name:
                    errors.append(f"设备类型ID和设备名称不能为空: {eq}")
                    continue
                c.execute('''
                    INSERT INTO equipment_instances (equipment_type_id, name, created_time, category)
                    VALUES (?, ?, ?, ?)
                ''', (equipment_type_id, equipment_name, datetime.now(), equipment_category))
                success_count += 1
            except Exception as e:
                errors.append(f"设备 {eq.get('equipment_name', '未知')} 导入失败: {str(e)}")
        conn.commit()
        conn.close()
        global scheduler
        scheduler = None
        return {'success_count': success_count, 'error_count': len(errors), 'errors': errors}

    @staticmethod
    def delete(equipment_id: int) -> str:
        conn = get_connection()
        c = conn.cursor()
        c.execute('SELECT name FROM equipment_instances WHERE id = ?', (equipment_id,))
        result = c.fetchone()
        if not result:
            conn.close()
            raise ValueError('设备不存在')
        equipment_name = result[0]
        c.execute('DELETE FROM equipment_instances WHERE id = ?', (equipment_id,))
        conn.commit()
        conn.close()
        global scheduler
        scheduler = None
        return equipment_name

    @staticmethod
    def get_instance(equipment_id: int) -> dict[str, Any] | None:
        conn = get_connection()
        c = conn.cursor()
        c.execute('''
            SELECT ei.id, ei.name, ei.equipment_type_id, et.name as equipment_type_name,
                   et.description, ei.created_time, ei.category
            FROM equipment_instances ei
            LEFT JOIN equipment_types et ON ei.equipment_type_id = et.id
            WHERE ei.id = ?
        ''', (equipment_id,))
        row = c.fetchone()
        conn.close()
        if not row:
            return None
        return {
            'id': row[0],
            'name': row[1],
            'equipment_type_id': row[2],
            'equipment_type_name': row[3] if row[3] else '未知类型',
            'equipment_type_description': row[4] if row[4] else '',
            'created_time': row[5],
            'category': row[6],
        }
