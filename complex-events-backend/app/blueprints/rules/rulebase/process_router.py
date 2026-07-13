from flask import Blueprint, jsonify, request
import sqlite3
import datetime
from pathlib import Path
from functools import wraps
import json
process_bp = Blueprint('rules_process', __name__)
def get_db_path():
    """统一获取数据库路径"""
    base_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
    return base_dir / 'database' / 'db.sqlite3'


def parse_number(value):
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if text == '' or text == '-':
        return 0
    total = 0.0
    for part in text.split(','):
        part = part.strip()
        if part == '':
            continue
        try:
            total += float(part)
        except ValueError:
            continue
    return total
"""获取所有设备类型的工序模板"""


@process_bp.route('/all-process-templates', methods=['GET'])
def get_all_process_templates():
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        # 获取所有设备类型
        c.execute('SELECT id, name FROM equipment_types')
        equipment_types = c.fetchall()
        result = {}
        for eq_type_id, eq_type_name in equipment_types:
            # 获取每个设备类型的工序模板
            c.execute('''
                      SELECT pt.process_code,
                             pt.description,
                             pt.estimated_hours,
                             pt.required_workers,
                             pt.predecessor_codes,
                             pt.parent_process_code,
                             pt.is_major_process,
                             pt.material_requirements,
                             pt.material_price,
                             pt.tools_requirements,
                             pt.tools_price,
                             pt.id,
                             et.name as equipment_type_name
                      FROM process_templates pt
                               LEFT JOIN equipment_types et ON pt.equipment_type_id = et.id
                      WHERE pt.equipment_type_id = ?
                      ORDER BY pt.is_major_process DESC, pt.process_code
                      ''', (eq_type_id,))

            processes = []
            for row in c.fetchall():
                processes.append({
                    'process_code': row[0],
                    'description': row[1],
                    'estimated_hours': parse_number(row[2]),
                    'required_workers': json.loads(row[3]) if row[3] else {},
                    'predecessor_codes': json.loads(row[4]) if row[4] else [],
                    'parent_process_code': row[5] if row[5] else 0,
                    'is_major_process': bool(row[6]),
                    'material_requirements': row[7],
                    'material_price': parse_number(row[8]),
                    'tools_requirements': row[9],
                    'tools_price': parse_number(row[10]),
                    'id': row[11],
                    'equipment_type_name': row[12],
                })

            result[eq_type_id] = {
                'name': eq_type_name,
                'processes': processes
            }

        conn.close()

        return jsonify({
            'success': True,
            'equipment_processes': result
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '获取工序模板失败'
        }), 500


@process_bp.route('/search-processes', methods=['POST'])
def search_processes():
    try:
        data = request.get_json() or {}
        device = (data.get('device') or '').strip()
        process = (data.get('process') or '').strip()

        man_hour_min = data.get('manHourMin')
        man_hour_max = data.get('manHourMax')
        labor_cost_min = data.get('laborCostMin')
        labor_cost_max = data.get('laborCostMax')
        equipment_cost_min = data.get('equipmentCostMin')
        equipment_cost_max = data.get('equipmentCostMax')

        def to_number(value):
            if value is None or value == '':
                return None
            return float(value)

        try:
            man_hour_min = to_number(man_hour_min)
            man_hour_max = to_number(man_hour_max)
            labor_cost_min = to_number(labor_cost_min)
            labor_cost_max = to_number(labor_cost_max)
            equipment_cost_min = to_number(equipment_cost_min)
            equipment_cost_max = to_number(equipment_cost_max)
        except ValueError:
            return jsonify({
                'success': False,
                'message': '检索条件中的数值必须是数字'
            }), 400

        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        c.execute('SELECT id, name, price FROM worker_types')
        worker_price_by_id = {}
        worker_price_by_name = {}
        for row in c.fetchall():
            price = parse_number(row[2])
            if row[0] is not None:
                worker_price_by_id[str(row[0])] = price
            if row[1]:
                worker_price_by_name[str(row[1])] = price

        query = '''
            SELECT
                et.name AS equipment_name,
                pt.description AS process_name,
                pt.estimated_hours,
                pt.required_workers,
                pt.tools_price
            FROM process_templates pt
            LEFT JOIN equipment_types et ON pt.equipment_type_id = et.id
            WHERE 1 = 1
        '''
        params = []

        if device:
            query += ' AND et.name LIKE ?'
            params.append(f'%{device}%')
        if process:
            query += ' AND pt.description LIKE ?'
            params.append(f'%{process}%')

        if man_hour_min is not None:
            query += ' AND CAST(pt.estimated_hours AS REAL) >= ?'
            params.append(man_hour_min)
        if man_hour_max is not None:
            query += ' AND CAST(pt.estimated_hours AS REAL) <= ?'
            params.append(man_hour_max)

        if equipment_cost_min is not None:
            query += ' AND CAST(pt.tools_price AS REAL) >= ?'
            params.append(equipment_cost_min)
        if equipment_cost_max is not None:
            query += ' AND CAST(pt.tools_price AS REAL) <= ?'
            params.append(equipment_cost_max)

        query += ' ORDER BY et.name, pt.description'
        c.execute(query, params)

        results = []
        for row in c.fetchall():
            estimated_hours = parse_number(row['estimated_hours'])
            required_workers = json.loads(row['required_workers']) if row['required_workers'] else {}
            labor_rate = 0.0
            for worker_key, count in required_workers.items():
                price = worker_price_by_name.get(str(worker_key))
                if price is None:
                    price = worker_price_by_id.get(str(worker_key), 0)
                labor_rate += parse_number(count) * price
            labor_cost = labor_rate * estimated_hours
            equipment_cost = parse_number(row['tools_price'])

            if man_hour_min is not None and estimated_hours < man_hour_min:
                continue
            if man_hour_max is not None and estimated_hours > man_hour_max:
                continue
            if labor_cost_min is not None and labor_cost < labor_cost_min:
                continue
            if labor_cost_max is not None and labor_cost > labor_cost_max:
                continue
            if equipment_cost_min is not None and equipment_cost < equipment_cost_min:
                continue
            if equipment_cost_max is not None and equipment_cost > equipment_cost_max:
                continue

            results.append({
                'equipment': row['equipment_name'],
                'process': row['process_name'],
                'man_hours': estimated_hours,
                'labor_cost': labor_cost,
                'equipment_cost': equipment_cost
            })

        conn.close()

        return jsonify({
            'success': True,
            'data': results
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '检索失败'
        }), 500

"""获取单个设备类型的工序模板"""
@process_bp.route('/process-templates/equipment-type/<string:equipment_type_id>', methods=['GET'])
def get_process_templates_by_equipment_type(equipment_type_id):
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()

        # 1. 检查设备类型是否存在
        c.execute('SELECT id, name FROM equipment_types WHERE id = ?', (equipment_type_id,))
        eq_type = c.fetchone()
        if not eq_type:
            conn.close()
            return jsonify({
                'success': False,
                'message': f'设备类型 ID {equipment_type_id} 不存在'
            }), 404

        # 2. 查询该设备类型下的所有工序模板
        c.execute('''
            SELECT id,
                   process_code,
                   description,
                   estimated_hours,
                   required_workers,
                   predecessor_codes,
                   parent_process_code,
                   is_major_process,
                   material_requirements,
                   material_price,
                   tools_requirements,
                   tools_price,
                   worker_price
            FROM process_templates
            WHERE equipment_type_id = ?
            ORDER BY is_major_process DESC, process_code
        ''', (equipment_type_id,))

        rows = c.fetchall()
        templates = []
        for row in rows:
            templates.append({
                'id': row[0],
                'process_code': row[1],
                'description': row[2],
                'estimated_hours': parse_number(row[3]),
                'required_workers': json.loads(row[4]) if row[4] else {},
                'predecessor_codes': json.loads(row[5]) if row[5] else [],
                'parent_process_code': row[6] if row[6] else 0,
                'is_major_process': bool(row[7]),
                'material_requirements': row[8],
                'material_price': parse_number(row[9]),
                'tools_requirements': row[10],
                'tools_price': parse_number(row[11]),
                'worker_price': parse_number(row[12])
            })

        conn.close()
        return jsonify({
            'success': True,
            'equipment_type_id': equipment_type_id,
            'equipment_type_name': eq_type[1],
            'data': templates
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '获取工序模板失败'
        }), 500
"""添加工序模板"""


@process_bp.route('/process-templates', methods=['POST'])
def add_process_template():
    try:
        data = request.get_json()
        equipment_type_id = data.get('equipment_type_id')
        process_code = data.get('process_code')
        description = data.get('description', '')
        estimated_hours = data.get('estimated_hours', 0)
        required_workers = data.get('required_workers', {})
        predecessor_codes = data.get('predecessor_codes', [])
        parent_process_code = data.get('parent_process_code')
        is_major_process = data.get('is_major_process', False)
        material_requirements = data.get('material_requirements')
        material_price = data.get('material_price', 0)
        tools_requirements = data.get('tools_requirements')
        tools_price = data.get('tools_price', 0)

        # 验证必填字段
        if not all([equipment_type_id, process_code]):
            return jsonify({
                'success': False,
                'message': '设备类型ID和工序代码不能为空'
            }), 400

        # 验证数值类型
        try:
            estimated_hours = float(estimated_hours)
            material_price = float(material_price) if material_price else 0
            tools_price = float(tools_price) if tools_price else 0
        except ValueError:
            return jsonify({
                'success': False,
                'message': '预计工时、物料费用和工具费用必须是数字'
            }), 400

        # 生成模板ID
        template_id = f"{equipment_type_id}-{process_code}"

        # 连接到数据库
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()

        # 检查是否已存在相同ID的模板
        c.execute('SELECT id FROM process_templates WHERE id = ?', (template_id,))
        if c.fetchone():
            conn.close()
            return jsonify({
                'success': False,
                'message': f'工序模板 {template_id} 已存在'
            }), 400

        # 插入工序模板到数据库
        c.execute('''
                  INSERT INTO process_templates
                  (id, equipment_type_id, process_code, description, estimated_hours,
                   required_workers, predecessor_codes, parent_process_code, is_major_process,
                   material_requirements, material_price, tools_requirements, tools_price, created_time)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                  ''', (
                      template_id, equipment_type_id, process_code, description,
                      estimated_hours, json.dumps(required_workers),
                      json.dumps(predecessor_codes), parent_process_code,
                      is_major_process, material_requirements, material_price,
                      tools_requirements, tools_price, datetime.datetime.now()
                  ))

        conn.commit()
        conn.close()

        # 重置调度器以便重新加载数据
        global scheduler
        scheduler = None

        return jsonify({
            'success': True,
            'message': f'工序模板 {process_code} 添加成功',
            'template_id': template_id
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '添加工序模板失败'
        }), 500


"""更新工序模板"""


@process_bp.route('/process-templates/<string:template_id>', methods=['PUT'])
def update_process_template(template_id):
    try:
        data = request.get_json()
        description = data.get('description')
        estimated_hours = data.get('estimated_hours')
        required_workers = data.get('required_workers')
        predecessor_codes = data.get('predecessor_codes')
        parent_process_code = data.get('parent_process_code')
        is_major_process = data.get('is_major_process')
        material_requirements = data.get('material_requirements')
        material_price = data.get('material_price')
        tools_requirements = data.get('tools_requirements')
        tools_price = data.get('tools_price')

        # 连接到数据库
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()

        # 检查工序模板是否存在
        c.execute('SELECT process_code FROM process_templates WHERE id = ?', (template_id,))
        result = c.fetchone()
        if not result:
            conn.close()
            return jsonify({
                'success': False,
                'message': '工序模板不存在'
            }), 404

        process_code = result[0]

        # 构建更新语句
        update_fields = []
        update_values = []

        if description is not None:
            update_fields.append('description = ?')
            update_values.append(description)
        if estimated_hours is not None:
            try:
                estimated_hours = float(estimated_hours)
                update_fields.append('estimated_hours = ?')
                update_values.append(estimated_hours)
            except ValueError:
                conn.close()
                return jsonify({
                    'success': False,
                    'message': '预计工时必须是数字'
                }), 400
        if required_workers is not None:
            update_fields.append('required_workers = ?')
            update_values.append(json.dumps(required_workers))
        if predecessor_codes is not None:
            update_fields.append('predecessor_codes = ?')
            update_values.append(json.dumps(predecessor_codes))
        if parent_process_code is not None:
            update_fields.append('parent_process_code = ?')
            update_values.append(parent_process_code)
        if is_major_process is not None:
            update_fields.append('is_major_process = ?')
            update_values.append(bool(is_major_process))
        if material_requirements is not None:
            update_fields.append('material_requirements = ?')
            update_values.append(material_requirements)
        if material_price is not None:
            try:
                material_price = float(material_price)
                update_fields.append('material_price = ?')
                update_values.append(material_price)
            except ValueError:
                conn.close()
                return jsonify({
                    'success': False,
                    'message': '物料费用必须是数字'
                }), 400
        if tools_requirements is not None:
            update_fields.append('tools_requirements = ?')
            update_values.append(tools_requirements)
        if tools_price is not None:
            try:
                tools_price = float(tools_price)
                update_fields.append('tools_price = ?')
                update_values.append(tools_price)
            except ValueError:
                conn.close()
                return jsonify({
                    'success': False,
                    'message': '工具费用必须是数字'
                }), 400
        if not update_fields:
            conn.close()
            return jsonify({
                'success': False,
                'message': '没有提供要更新的字段'
            }), 400

        update_values.append(template_id)
        update_query = f'UPDATE process_templates SET {", ".join(update_fields)} WHERE id = ?'

        c.execute(update_query, update_values)
        conn.commit()
        conn.close()

        # 重置调度器以便重新加载数据
        global scheduler
        scheduler = None

        return jsonify({
            'success': True,
            'message': f'工序模板 {process_code} 更新成功'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '更新工序模板失败'
        }), 500


"""删除工序模板"""


@process_bp.route('/process-templates/<string:template_id>', methods=['DELETE'])
def delete_process_template(template_id):
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()

        # 检查工序模板是否存在
        c.execute('SELECT process_code FROM process_templates WHERE id = ?', (template_id,))
        result = c.fetchone()
        if not result:
            conn.close()
            return jsonify({
                'success': False,
                'message': '工序模板不存在'
            }), 404

        process_code = result[0]

        # 删除工序模板
        c.execute('DELETE FROM process_templates WHERE id = ?', (template_id,))

        conn.commit()
        conn.close()

        # 重置调度器以便重新加载数据
        global scheduler
        scheduler = None

        return jsonify({
            'success': True,
            'message': f'工序模板 {process_code} 删除成功'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '删除工序模板失败'
        }), 500


"""批量导入工序模板"""


@process_bp.route('/batch-import-process-templates', methods=['POST'])
def batch_import_process_templates():
    try:
        data = request.get_json()
        templates_list = data.get('templates_list', [])

        if not templates_list:
            return jsonify({
                'success': False,
                'message': '工序模板列表不能为空'
            }), 400

        # 连接到数据库
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()

        success_count = 0
        error_messages = []

        for template in templates_list:
            try:
                equipment_type_id = template.get('equipment_type_id')
                process_code = template.get('process_code')
                description = template.get('description', '')
                estimated_hours = template.get('estimated_hours', 0)
                required_workers = template.get('required_workers', {})
                predecessor_codes = template.get('predecessor_codes', [])
                parent_process_code = template.get('parent_process_code')
                is_major_process = template.get('is_major_process', False)
                material_requirements = template.get('material_requirements')
                material_price = template.get('material_price', 0)
                tools_requirements = template.get('tools_requirements')
                tools_price = template.get('tools_price', 0)

                # 验证必填字段
                if not all([equipment_type_id, process_code]):
                    error_messages.append(f"设备类型ID和工序代码不能为空: {template}")
                    continue

                # 验证数值类型
                try:
                    estimated_hours = float(estimated_hours)
                    material_price = float(material_price) if material_price else 0
                    tools_price = float(tools_price) if tools_price else 0
                except ValueError:
                    error_messages.append(f"预计工时必须是数字: {template}")
                    continue

                # 生成模板ID
                template_id = f"{equipment_type_id}-{process_code}"

                # 检查是否已存在相同ID的模板
                c.execute('SELECT id FROM process_templates WHERE id = ?', (template_id,))
                if c.fetchone():
                    error_messages.append(f"工序模板 {template_id} 已存在")
                    continue

                # 插入工序模板到数据库
                c.execute('''
                          INSERT INTO process_templates
                          (equipment_type_id, process_code, description, estimated_hours,
                           required_workers, predecessor_codes, parent_process_code, is_major_process,
                           material_requirements, material_price, tools_requirements, tools_price, created_time)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                          ''', (
                              equipment_type_id, process_code, description,
                              estimated_hours, json.dumps(required_workers),
                              json.dumps(predecessor_codes), parent_process_code,
                              is_major_process, material_requirements, material_price,
                              tools_requirements, tools_price, datetime.datetime.now()
                          ))

                success_count += 1

            except Exception as e:
                error_messages.append(f"工序模板 {template.get('process_code', '未知')} 导入失败: {str(e)}")

        conn.commit()
        conn.close()

        # 重置调度器以便重新加载数据
        global scheduler
        scheduler = None

        return jsonify({
            'success': True,
            'message': f'成功导入 {success_count} 个工序模板',
            'success_count': success_count,
            'error_count': len(error_messages),
            'errors': error_messages
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '批量导入工序模板失败'
        }), 