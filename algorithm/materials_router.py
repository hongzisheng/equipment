from flask import Blueprint, jsonify, request
import sqlite3
import datetime
from pathlib import Path
materials_bp = Blueprint('materials', __name__, url_prefix='/api')
def get_db_path():
    """统一获取数据库路径"""
    current_dir = Path(__file__).parent.parent
    return current_dir / 'database' / 'db.sqlite3'
#----------材料相关------------------
"""获取所有材料"""
@materials_bp.route('/materials', methods=['GET'])
def get_materials():
    
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        c.execute('''
            SELECT id, name, price, stock_quantity, unit, created_at, updated_at
            FROM materials
            ORDER BY created_at DESC
        ''')
        
        materials = []
        for row in c.fetchall():
            materials.append({
                'id': row[0],
                'name': row[1],
                'price': float(row[2]) if row[2]!='-' else 0,
                'stock_quantity': float(row[3]) if row[3]!='-' else 0,
                'unit': row[4],
                'created_at': row[5],
                'updated_at': row[6]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'materials': materials,
            'total_count': len(materials)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '获取材料列表失败'
        }), 500

"""添加新材料"""
@materials_bp.route('/materials', methods=['POST'])
def add_material():
    try:
        data = request.get_json()
        name = data.get('name')
        price = data.get('price')
        stock_quantity = data.get('stock_quantity')
        unit = data.get('unit')
        
        # 验证必填字段
        if not all([name, price is not None, stock_quantity is not None, unit]):
            return jsonify({
                'success': False,
                'message': '材料名称、单价、库存数量和计量单位不能为空'
            }), 400
        
        # 验证数值类型
        try:
            price = float(price)
            stock_quantity = float(stock_quantity)
        except ValueError:
            return jsonify({
                'success': False,
                'message': '单价和库存数量必须是数字'
            }), 400
        
        # 连接到数据库
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        
        # 插入新材料
        c.execute('''
            INSERT INTO materials (name, price, stock_quantity, unit, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, price, stock_quantity, unit, datetime.datetime.now(), datetime.datetime.now()))
        
        material_id = c.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'材料 {name} 添加成功',
            'material_id': material_id
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '添加材料失败'
        }), 500

"""批量导入材料"""
@materials_bp.route('/batch-import-materials', methods=['POST'])
def batch_import_materials():
    try:
        data = request.get_json()
        materials_list = data.get('materials_list', [])
        
        if not materials_list:
            return jsonify({
                'success': False,
                'message': '材料列表不能为空'
            }), 400
        
        # 连接到数据库
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        
        success_count = 0
        error_messages = []
        
        for material in materials_list:
            try:
                name = material.get('name')
                price = material.get('price')
                stock_quantity = material.get('stock_quantity')
                unit = material.get('unit')
                
                # 验证必填字段
                if not all([name, price is not None, stock_quantity is not None, unit]):
                    error_messages.append(f"材料 {name} 的必填字段不完整")
                    continue
                
                # 验证数值类型
                try:
                    price = float(price)
                    stock_quantity = float(stock_quantity)
                except ValueError:
                    error_messages.append(f"材料 {name} 的单价或库存数量格式错误")
                    continue
                
                # 插入材料到数据库
                c.execute('''
                    INSERT INTO materials (name, price, stock_quantity, unit, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (name, price, stock_quantity, unit, datetime.datetime.now(), datetime.datetime.now()))
                
                success_count += 1
                
            except Exception as e:
                error_messages.append(f"材料 {material.get('name', '未知')} 导入失败: {str(e)}")
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'成功导入 {success_count} 个材料',
            'success_count': success_count,
            'error_count': len(error_messages),
            'errors': error_messages
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '批量导入材料失败'
        }), 500

"""删除材料"""
@materials_bp.route('/materials/<int:material_id>', methods=['DELETE'])
def delete_material(material_id):
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        
        # 检查材料是否存在
        c.execute('SELECT name FROM materials WHERE id = ?', (material_id,))
        result = c.fetchone()
        if not result:
            conn.close()
            return jsonify({
                'success': False,
                'message': '材料不存在'
            }), 404
        
        material_name = result[0]
        
        # 删除材料
        c.execute('DELETE FROM materials WHERE id = ?', (material_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'材料 {material_name} 删除成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '删除材料失败'
        }), 500