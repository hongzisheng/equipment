from flask import Blueprint, jsonify, request, current_app
import sqlite3
import datetime
equipment_bp = Blueprint('equipment', __name__)

def get_db_path():
    return current_app.config['DATABASE_URI']

"""获取设备分类"""
@equipment_bp.route('/equipment-categories', methods=['GET'])
def get_equipment_categories():
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        c.execute('SELECT category_id, category_name FROM equipment_category ORDER BY category_id')
        rows = c.fetchall()
        conn.close()
        return jsonify({
            'success': True,
            'data': [{'id': row[0], 'name': row[1]} for row in rows]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

"""获取设备类型（含分类字段）"""
@equipment_bp.route('/equipment-types-with-category', methods=['GET'])
def get_equipment_types_with_category():
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        c.execute('SELECT id, name, category FROM equipment_types ORDER BY id')
        rows = c.fetchall()
        conn.close()
        return jsonify({
            'success': True,
            'data': [{'id': row[0], 'name': row[1], 'category': row[2]} for row in rows]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

#----------设备相关------------------
"""获取所有设备类型"""
@equipment_bp.route('/equipment-types', methods=['GET'])
def get_equipment_types():
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        c.execute('SELECT id, name FROM equipment_types')
        rows = c.fetchall()
        conn.close()
        return jsonify({
            'success': True,
            'data': [{'id': row[0], 'name': row[1]} for row in rows]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@equipment_bp.route('/select-equipments', methods=['POST'])
def select_equipments():
    try:
        data = request.get_json()
        selected_equipment_ids = data.get('selected_equipment_ids', [])
        if not selected_equipment_ids:
            return jsonify({
                'success': False,
                'message': '请选择至少一个设备'
            }), 400
        
        # 连接到数据库
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        
        # 1. 从 equipment_instances 表获取选中的设备信息
        placeholders = ','.join('?' * len(selected_equipment_ids))
        c.execute(f'''
            SELECT id, name, equipment_type_id, equipment_type_name, category
            FROM equipment_instances 
            WHERE id IN ({placeholders})
        ''', selected_equipment_ids)
        
        selected_equipments = c.fetchall()
        if len(selected_equipments) != len(selected_equipment_ids):
            conn.close()
            return jsonify({
                'success': False,
                'message': '部分设备ID不存在'
            }), 400
        
        # 2. 清空 selected_equipments 表
        c.execute('DELETE FROM selected_equipments')
        
        # 3. 将选中的设备插入 selected_equipments 表
        for equipment in selected_equipments:
            equipment_id, name, equipment_type_id, equipment_type_name, category = equipment
            c.execute('''
                INSERT INTO selected_equipments (id, name, equipment_type_id, equipment_type_name, category)
                VALUES (?, ?, ?, ?, ?)
            ''', (equipment_id, name, equipment_type_id, equipment_type_name, category))
        
        conn.commit()
        conn.close()
        
        # 重置调度器以便重新加载数据
        global scheduler
        scheduler = None
        
        return jsonify({
            'success': True,
            'message': f'成功选择 {len(selected_equipments)} 台设备',
            'selected_count': len(selected_equipments)
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"select_equipments 接口错误: {str(e)}")
        print(f"错误详情: {error_details}")
        return jsonify({
            'success': False,
            'error': str(e),
            'error_details': error_details,
            'message': '设置选中设备失败'
        }), 500

"""获取当前选中的设备"""
@equipment_bp.route('/selected-equipments', methods=['GET'])
def get_selected_equipments():
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        
        # 查询选中的设备信息
        c.execute('''
            SELECT se.id, se.name, se.equipment_type_id, se.equipment_type_name, se.category
            FROM selected_equipments se
            ORDER BY se.equipment_type_id, se.id
        ''')
        
        selected_equipments = []
        for row in c.fetchall():
            selected_equipments.append({
                'id': row[0],
                'name': row[1],
                'equipment_type_id': row[2],
                'equipment_type_name': row[3],
                'category': row[4]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'selected_equipments': selected_equipments,
            'total_count': len(selected_equipments)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '获取选中设备失败'
        }), 500
"""获取所有设备实例"""
@equipment_bp.route('/equipment-instances', methods=['GET'])
def get_equipment_instances():
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        c.execute('SELECT id, name, equipment_type_id, equipment_type_name, category FROM equipment_instances ORDER BY id')
        rows = c.fetchall()
        conn.close()

        equipment_instances = []
        for row in rows:
            equipment_instances.append({
                'id': row[0],
                'name': row[1],
                'equipment_type_id': row[2],
                'equipment_type_name': row[3] if len(row) > 3 else '',
                'category': row[4] if len(row) > 4 else ''
            })
        
        return jsonify({
            'success': True,
            'data': equipment_instances,
            'total_count': len(equipment_instances)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '获取设备实例失败'
        }), 500
"""根据设备类型ID查询该类型下的所有设备实例"""
@equipment_bp.route('/equipment-instances/by-type/<string:equipment_type_id>', methods=['GET'])
def get_equipment_instances_by_type(equipment_type_id):
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        
        # 检查设备类型是否存在
        c.execute('SELECT name FROM equipment_types WHERE id = ?', (equipment_type_id,))
        type_row = c.fetchone()
        if not type_row:
            conn.close()
            return jsonify({
                'success': False,
                'message': f'设备类型 ID {equipment_type_id} 不存在'
            }), 404
        
        # 查询该类型下的所有设备实例
        c.execute('''
            SELECT id, name, equipment_type_id, category, created_time
            FROM equipment_instances
            WHERE equipment_type_id = ?
            ORDER BY id
        ''', (equipment_type_id,))
        
        rows = c.fetchall()
        conn.close()
        
        equipment_instances = []
        for row in rows:
            equipment_instances.append({
                'id': row[0],
                'name': row[1],
                'equipment_type_id': row[2],
                'category': row[3] if row[3] else '',
                'created_time': row[4]
            })
        
        return jsonify({
            'success': True,
            'data': equipment_instances,
            'total_count': len(equipment_instances),
            'equipment_type_name': type_row[0]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '根据设备类型查询设备实例失败'
        }), 500
"""添加设备实例"""
@equipment_bp.route('/add-equipment', methods=['POST'])
def add_equipment():
    try:
        data = request.get_json()
        equipment_type_id = data.get('equipment_type_id')
        equipment_name = data.get('equipment_name')
        equipment_category=data.get('equipment_category')
        if not equipment_type_id or not equipment_name:
            return jsonify({
                'success': False,
                'message': '设备种类和设备名称不能为空'
            }), 400
        
        # 连接到数据库
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()

        # 插入设备实例到数据库
        c.execute('''
            INSERT INTO equipment_instances (equipment_type_id, name, created_time,category)
            VALUES (?, ?, ?,?)
        ''', (equipment_type_id, equipment_name, datetime.datetime.now(),equipment_category))
        
        conn.commit()
        conn.close()
        
        # 重置调度器以便重新加载数据
        global scheduler
        scheduler = None
        
        return jsonify({
            'success': True,
            'message': f'设备 {equipment_name} 添加成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '添加设备失败'
        }), 500

"""批量导入设备实例"""
@equipment_bp.route('/batch-import-equipment', methods=['POST'])
def batch_import_equipment():
    try:
        data = request.get_json()
        equipment_list = data.get('equipment_list', [])
        
        if not equipment_list:
            return jsonify({
                'success': False,
                'message': '设备列表不能为空'
            }), 400
        
        # 连接到数据库
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        
        success_count = 0
        error_messages = []
        
        for equipment in equipment_list:
            try:
                equipment_type_id = equipment.get('equipment_type_id')
                equipment_name = equipment.get('equipment_name')
                equipment_category = equipment.get('equipment_category', '')
                
                if not equipment_type_id or not equipment_name:
                    error_messages.append(f"设备类型ID和设备名称不能为空: {equipment}")
                    continue
                
                # 插入设备实例到数据库
                c.execute('''
                    INSERT INTO equipment_instances (equipment_type_id, name, created_time, category)
                    VALUES (?, ?, ?, ?)
                ''', (equipment_type_id, equipment_name, datetime.datetime.now(), equipment_category))
                
                success_count += 1
                
            except Exception as e:
                error_messages.append(f"设备 {equipment.get('equipment_name', '未知')} 导入失败: {str(e)}")
        
        conn.commit()
        conn.close()
        
        # 重置调度器以便重新加载数据
        global scheduler
        scheduler = None
        
        return jsonify({
            'success': True,
            'message': f'成功导入 {success_count} 个设备实例',
            'success_count': success_count,
            'error_count': len(error_messages),
            'errors': error_messages
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '批量导入设备失败'
        }), 500 

"""删除设备实例"""
@equipment_bp.route('/equipment-instances/<int:equipment_id>', methods=['DELETE'])
def delete_equipment_instance(equipment_id):
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        
        # 检查设备是否存在
        c.execute('SELECT name FROM equipment_instances WHERE id = ?', (equipment_id,))
        result = c.fetchone()
        if not result:
            conn.close()
            return jsonify({
                'success': False,
                'message': '设备不存在'
            }), 404
        
        equipment_name = result[0]
        
        # 删除设备实例
        c.execute('DELETE FROM equipment_instances WHERE id = ?', (equipment_id,))
        
        conn.commit()
        conn.close()
        
        # 重置调度器以便重新加载数据
        global scheduler
        scheduler = None
        
        return jsonify({
            'success': True,
            'message': f'设备 {equipment_name} 删除成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '删除设备失败'
        }), 500

"""根据ID查询单个设备实例"""
@equipment_bp.route('/equipment-instances/<int:equipment_id>', methods=['GET'])
def get_equipment_instance(equipment_id):
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        
        # 关联查询设备实例和设备类型信息
        c.execute('''
            SELECT ei.id, ei.name, ei.equipment_type_id,et.name as equipment_type_name, 
                   et.description, ei.created_time,ei.category
            FROM equipment_instances ei
            LEFT JOIN equipment_types et ON ei.equipment_type_id = et.id
            WHERE ei.id = ?
        ''', (equipment_id,))
        
        row = c.fetchone()
        if not row:
            conn.close()
            return jsonify({
                'success': False,
                'message': '设备不存在'
            }), 404
        
        equipment_instance = {
            'id': row[0],
            'name': row[1],
            'equipment_type_id': row[2],
            'equipment_type_name': row[3] if row[3] else '未知类型',
            'equipment_type_description': row[4] if row[4] else '',
            'created_time': row[5],
            'ei.category':row[6]
        }
        
        conn.close()
        
        return jsonify({
            'success': True,
            'equipment_instance': equipment_instance
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '获取设备信息失败'
        }), 500
