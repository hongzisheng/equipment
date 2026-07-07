from flask import Blueprint, jsonify, request
import sqlite3
import datetime
from pathlib import Path
from functools import wraps
from app.utils import get_db_path
maintenance_bp = Blueprint('maintenance', __name__, url_prefix='/api')


"""获取所有维修器具"""
@maintenance_bp.route('/maintenance-tools', methods=['GET'])
def get_maintenance_tools():
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        
        c.execute('''
            SELECT id, name, tool_type, capacity, daily_rental_cost, is_available, requires_operator
            FROM maintenance_tools
            ORDER BY id
        ''')
        
        tools = []
        for row in c.fetchall():
            tools.append({
                'id': row[0],
                'name': row[1],
                'tool_type': row[2],
                'capacity': row[3],
                'daily_rental_cost': float(row[4]),
                'is_available': bool(row[5]),
                'requires_operator': bool(row[6])
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'maintenance_tools': tools,
            'total_count': len(tools)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '获取维修器具列表失败'
        }), 500

"""添加维修器具"""
@maintenance_bp.route('/maintenance-tools', methods=['POST'])
def add_maintenance_tool():
    try:
        data = request.get_json()
        name = data.get('name')
        tool_type = data.get('tool_type')
        capacity = data.get('capacity')
        daily_rental_cost = data.get('daily_rental_cost')
        is_available = data.get('is_available', True)
        requires_operator = data.get('requires_operator', False)
        
        # 验证必填字段
        if not all([name, tool_type, capacity is not None, daily_rental_cost is not None]):
            return jsonify({
                'success': False,
                'message': '器具名称、类型、容量和日租金不能为空'
            }), 400
        
        # 验证数值类型
        try:
            capacity = float(capacity)
            daily_rental_cost = float(daily_rental_cost)
        except ValueError:
            return jsonify({
                'success': False,
                'message': '容量和日租金必须是数字'
            }), 400
        
        # 连接到数据库
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        
        # 插入维修器具
        c.execute('''
            INSERT INTO maintenance_tools (name, tool_type, capacity, daily_rental_cost, is_available, requires_operator)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, tool_type, capacity, daily_rental_cost, is_available, requires_operator))
        
        tool_id = c.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'维修器具 {name} 添加成功',
            'tool_id': tool_id
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '添加维修器具失败'
        }), 500

"""更新维修器具"""
@maintenance_bp.route('/maintenance-tools/<int:tool_id>', methods=['PUT'])
def update_maintenance_tool(tool_id):
    try:
        data = request.get_json()
        name = data.get('name')
        tool_type = data.get('tool_type')
        capacity = data.get('capacity')
        daily_rental_cost = data.get('daily_rental_cost')
        is_available = data.get('is_available')
        requires_operator = data.get('requires_operator')
        
        # 连接到数据库
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        
        # 检查维修器具是否存在
        c.execute('SELECT name FROM maintenance_tools WHERE id = ?', (tool_id,))
        result = c.fetchone()
        if not result:
            conn.close()
            return jsonify({
                'success': False,
                'message': '维修器具不存在'
            }), 404
        
        # 构建更新语句
        update_fields = []
        update_values = []
        
        if name is not None:
            update_fields.append('name = ?')
            update_values.append(name)
        if tool_type is not None:
            update_fields.append('tool_type = ?')
            update_values.append(tool_type)
        if capacity is not None:
            update_fields.append('capacity = ?')
            update_values.append(float(capacity))
        if daily_rental_cost is not None:
            update_fields.append('daily_rental_cost = ?')
            update_values.append(float(daily_rental_cost))
        if is_available is not None:
            update_fields.append('is_available = ?')
            update_values.append(bool(is_available))
        if requires_operator is not None:
            update_fields.append('requires_operator = ?')
            update_values.append(bool(requires_operator))
        
        if not update_fields:
            conn.close()
            return jsonify({
                'success': False,
                'message': '没有提供要更新的字段'
            }), 400
        
        update_values.append(tool_id)
        update_query = f'UPDATE maintenance_tools SET {", ".join(update_fields)} WHERE id = ?'
        
        c.execute(update_query, update_values)
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'维修器具 {result[0]} 更新成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '更新维修器具失败'
        }), 500

"""删除维修器具"""
@maintenance_bp.route('/maintenance-tools/<int:tool_id>', methods=['DELETE'])
def delete_maintenance_tool(tool_id):
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        
        # 检查维修器具是否存在
        c.execute('SELECT name FROM maintenance_tools WHERE id = ?', (tool_id,))
        result = c.fetchone()
        if not result:
            conn.close()
            return jsonify({
                'success': False,
                'message': '维修器具不存在'
            }), 404
        
        tool_name = result[0]
        
        # 删除维修器具
        c.execute('DELETE FROM maintenance_tools WHERE id = ?', (tool_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'维修器具 {tool_name} 删除成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '删除维修器具失败'
        }), 500

"""根据ID查询单个维修器具"""
@maintenance_bp.route('/maintenance-tools/<int:tool_id>', methods=['GET'])
def get_maintenance_tool(tool_id):
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        
        c.execute('''
            SELECT id, name, tool_type, capacity, daily_rental_cost, is_available, requires_operator
            FROM maintenance_tools
            WHERE id = ?
        ''', (tool_id,))
        
        row = c.fetchone()
        if not row:
            conn.close()
            return jsonify({
                'success': False,
                'message': '维修器具不存在'
            }), 404
        
        tool = {
            'id': row[0],
            'name': row[1],
            'tool_type': row[2],
            'capacity': row[3],
            'daily_rental_cost': float(row[4]),
            'is_available': bool(row[5]),
            'requires_operator': bool(row[6])
        }
        
        conn.close()
        
        return jsonify({
            'success': True,
            'maintenance_tool': tool
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '获取维修器具信息失败'
        }), 500

"""批量导入维修器具"""
@maintenance_bp.route('/batch-import-maintenance-tools', methods=['POST'])
def batch_import_maintenance_tools():
    try:
        data = request.get_json()
        tools_list = data.get('tools_list', [])
        
        if not tools_list:
            return jsonify({
                'success': False,
                'message': '维修器具列表不能为空'
            }), 400
        
        # 连接到数据库
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        
        success_count = 0
        error_messages = []
        
        for tool in tools_list:
            try:
                name = tool.get('name')
                tool_type = tool.get('tool_type')
                capacity = tool.get('capacity')
                daily_rental_cost = tool.get('daily_rental_cost')
                is_available = tool.get('is_available', True)
                requires_operator = tool.get('requires_operator', False)
                
                # 验证必填字段
                if not all([name, tool_type, capacity is not None, daily_rental_cost is not None]):
                    error_messages.append(f"维修器具 {name} 的必填字段不完整")
                    continue
                
                # 验证数值类型
                try:
                    capacity = float(capacity)
                    daily_rental_cost = float(daily_rental_cost)
                except ValueError:
                    error_messages.append(f"维修器具 {name} 的容量或日租金格式错误")
                    continue
                
                # 插入维修器具到数据库
                c.execute('''
                    INSERT INTO maintenance_tools (name, tool_type, capacity, daily_rental_cost, is_available, requires_operator)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (name, tool_type, capacity, daily_rental_cost, is_available, requires_operator))
                
                success_count += 1
                
            except Exception as e:
                error_messages.append(f"维修器具 {tool.get('name', '未知')} 导入失败: {str(e)}")
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'成功导入 {success_count} 个维修器具',
            'success_count': success_count,
            'error_count': len(error_messages),
            'errors': error_messages
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '批量导入维修器具失败'
        }), 500