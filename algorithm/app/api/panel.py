from flask import Blueprint, jsonify, request
import sqlite3
import datetime
from pathlib import Path
from functools import wraps
import json
from app import core
from app.utils import get_db_path
panel_bp = Blueprint('panel', __name__, url_prefix='/api')

# ----------信息面板相关------------------
def parse_time(time_str):
    # 格式示例: "第1天 08:00"
    import re
    match = re.match(r'第(\d+)天 (\d+):(\d+)', time_str)
    if match:
        day = int(match.group(1)) - 1  # 转换为0-based
        hour = int(match.group(2))
        minute = int(match.group(3))
        return day * 24 * 60 + hour * 60 + minute
    return 0


def parse_tool_requirements(req_string):
    if not req_string or req_string.strip() == '':
        return {}

    # 去除花括号
    cleaned = req_string.strip('{}')
    print(f"   去除花括号后: '{cleaned}'")
    tools_dict = {}

    # 先检测是否有分号（多个项目的情况）
    if '、' in cleaned:
        # 多个项目，按分号分割
        items = cleaned.split('、')
        for item in items:
            if not item.strip():
                continue

            # 按冒号分割每个项目
            if '：' in item:
                parts = item.split('：', 1)
            elif ':' in item:
                parts = item.split(':', 1)
            tool_name = parts[0].strip()
            quantity_part = parts[1].strip()
            # 从数量部分提取数字和单位
            quantity_str = ""
            unit_str = ""

            for char in quantity_part:
                if char.isdigit() or char == '.':
                    quantity_str += char
                else:
                    unit_str += char
            if quantity_str:
                try:
                    quantity = float(quantity_str)
                    unit = unit_str.strip() if unit_str.strip() else '台班'
                    tools_dict[tool_name] = {
                        'quantity': quantity,
                        'unit': unit
                    }
                except ValueError as e:
                    print(f"调试parse_material_requirements: 无法解析数量 '{quantity_str}': {e}")
    else:
        # 单个项目，直接解析
        # 按冒号分割
        if '：' in cleaned:
            parts = cleaned.split('：', 1)
        elif ':' in cleaned:
            parts = cleaned.split(':', 1)
        else:
            return {}

        if len(parts) != 2:
            return {}

        tool_name = parts[0].strip()
        quantity_part = parts[1].strip()

        # 从数量部分提取数字和单位
        quantity_str = ""
        unit_str = ""

        for char in quantity_part:
            if char.isdigit() or char == '.':
                quantity_str += char
            else:
                unit_str += char

        if quantity_str:
            try:
                quantity = float(quantity_str)
                unit = unit_str.strip() if unit_str.strip() else '台班'
                tools_dict[tool_name] = {
                    'quantity': quantity,
                    'unit': unit
                }
            except ValueError as e:
                print(f"调试parse_material_requirements: 无法解析数量 '{quantity_str}': {e}")
    return tools_dict


def parse_material_requirements(req_string):
    """解析材料需求字符串"""
    if not req_string or req_string.strip() == '':
        return {}
    # 去除花括号
    cleaned = req_string.strip('{}')
    # 按分号分割
    items = cleaned.split('、')
    materials_dict = {}
    for item in items:
        if not item.strip():
            continue
        # 按冒号分割材料名和数量+单位
        if '：' in item:
            name_part, quantity_part = item.split('：', 1)
            material_name = name_part.strip()
            # 从数量部分分离数值和单位
            quantity_str = ""
            unit_str = ""
            for char in quantity_part:
                if char.isdigit() or char == '.':
                    quantity_str += char
                else:
                    unit_str += char
            if quantity_str:
                try:
                    quantity = float(quantity_str)
                    unit = unit_str.strip()
                    materials_dict[material_name] = {
                        'quantity': quantity,
                        'unit': unit
                    }
                except ValueError:
                    print(f"无法解析数量: {quantity_str}")

    return materials_dict


"""获取工作人员工作状态"""


@panel_bp.route('/worker-status', methods=['POST'])
def get_worker_status():
    try:
        data = request.get_json()
        start_time_str = data.get('start_time')
        end_time_str = data.get('end_time')

        if not start_time_str or not end_time_str:
            return jsonify({
                'success': False,
                'message': '开始时间和结束时间不能为空'
            }), 400
        start_minutes = parse_time(start_time_str)
        end_minutes = parse_time(end_time_str)
        scheduler = core.get_scheduler()
        if scheduler is None:
            return jsonify({
                'success': False,
                'message': '调度器未初始化，请先执行调度'
            }), 400

        worker_status = []
        # 遍历所有工人
        for worker in scheduler.workers:
            worker_tasks = []

            # 查找工人在该时间段内的任务
            for task in scheduler.schedule_plan:
                # 检查任务是否在查询时间段内
                if (task['start_time'] <= end_minutes and
                        task['end_time'] >= start_minutes and
                        task.get('workers')):

                    # 检查该工人是否参与此任务
                    for worker_type, worker_list in task['workers'].items():
                        if worker.name in worker_list:
                            # 确定任务状态
                            if task['end_time'] <= start_minutes:
                                status = "已完成"
                            elif task['start_time'] >= end_minutes:
                                status = "未开始"
                            else:
                                status = "进行中"

                            # 获取设备信息
                            equipment = scheduler.get_equipment_by_id(task['equipment_id'])
                            equipment_name = equipment.name if equipment else task['equipment_name']
                            worker_tasks.append({
                                'task_name': task['process_name'],
                                'equipment': equipment_name,
                                'start_time': scheduler.format_time(task['start_time']),
                                'end_time': scheduler.format_time(task['end_time']),
                                'status': status
                            })
            worker_status.append({
                'worker_id': worker.id,
                'worker_name': worker.name,
                'worker_type': worker.type,
                'status': '工作中' if worker_tasks else '空闲',
                'tasks': worker_tasks
            })

        return jsonify({
            'success': True,
            'worker_status': worker_status,
            'time_period': f"{start_time_str} - {end_time_str}"
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '获取工作人员状态失败'
        }), 500


"""获取物料库存使用看板"""


@panel_bp.route('/material-inventory', methods=['POST'])
def get_material_inventory():
    """获取物料库存使用情况"""
    try:
        # 解析时间字符串为分钟数
        data = request.get_json()
        end_time_str = data.get('end_time')  # 截止时间

        if not end_time_str:
            return jsonify({
                'success': False,
                'message': '截止时间不能为空'
            }), 400
        end_minutes = parse_time(end_time_str)
        scheduler = core.get_scheduler()
        if scheduler is None:
            return jsonify({
                'success': False,
                'message': '调度器未初始化，请先执行调度'
            }), 400
        # 从数据库加载初始物料库存
        from app.models import DatabaseManager
        db_path = get_db_path()
        materials_data = DatabaseManager.load_materials_from_db(str(db_path))

        # 将材料数据转换为更方便处理的格式
        materials = {}
        material_name_to_id = {}  # 材料名称到ID的映射

        for material in materials_data:
            materials[material.id] = {
                'id': material.id,
                'name': material.name,
                'price': material.price,
                'initial_stock': material.stock_quantity,
                'current_stock': material.stock_quantity,
                'unit': material.unit
            }
            material_name_to_id[material.name] = material.id
        # 计算已完成的工序消耗的物料
        completed_tasks = []
        for task in scheduler.schedule_plan:
            if task['end_time'] <= end_minutes:
                completed_tasks.append(task)
        # 计算物料消耗
        material_consumption = {}
        for task in completed_tasks:
            # 获取工序对应的设备类型和工序代码
            process_id = task['process_id']
            if process_id.endswith('_MILESTONE'):
                parts = process_id.split('_')
                if len(parts) >= 2:
                    Equipment_id = parts[0]
                    process_code = parts[1]
                    # 获取设备信息
                    db_path = get_db_path()
                    conn = sqlite3.connect(str(db_path))
                    c = conn.cursor()
                    c.execute('''
                              SELECT pt.material_requirements
                              FROM process_templates pt
                                       INNER JOIN equipment_instances ei ON pt.equipment_type_id = ei.equipment_type_id
                              WHERE ei.id = ?
                                AND pt.process_code = ?
                              ''', (Equipment_id, process_code))

                    result = c.fetchone()
                    conn.close()
                    if result and result[0]:
                        material_req = result[0]
                        # 解析物料需求
                        material_requirements = parse_material_requirements(material_req)
                        for material_name, req_info in material_requirements.items():
                            quantity = req_info['quantity']
                            unit = req_info['unit']

                            # 找到对应的材料ID
                            material_id = material_name_to_id.get(material_name)

                            if material_id:
                                if material_id not in material_consumption:
                                    material_consumption[material_id] = 0
                                material_consumption[material_id] += quantity
                            else:
                                print(f"警告: 未找到材料 '{material_name}' 在库存中")

        # 更新当前库存
        for material_id, consumption in material_consumption.items():
            if material_id in materials:
                materials[material_id]['current_stock'] = max(
                    0, materials[material_id]['current_stock'] - consumption
                )

        # 格式化返回数据
        inventory_data = []
        for material_id, material_info in materials.items():
            consumption = material_consumption.get(material_id, 0)

            inventory_data.append({
                'material_id': material_id,
                'material_name': material_info['name'],
                'initial_stock': material_info['initial_stock'],
                'current_stock': round(material_info['current_stock'], 3),
                'unit': material_info['unit'],
                'consumption': round(consumption, 3),
                'status': '充足' if material_info['current_stock'] > 0 else '缺货'
            })

        return {
            'success': True,
            'material_inventory': inventory_data,
            'as_of_time': end_time_str,
            'total_materials': len(inventory_data),
            'materials_in_shortage': len([m for m in inventory_data if m['current_stock'] <= 0])
        }

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return {
            'success': False,
            'error': str(e),
            'error_details': error_details,
            'message': '获取物料库存失败'
        }


"""获取维修器具使用状态看板"""


@panel_bp.route('/maintenance-tool-status', methods=['POST'])
def get_maintenance_tool_status():
    try:
        data = request.get_json()
        start_time_str = data.get('start_time')
        end_time_str = data.get('end_time')

        if not start_time_str or not end_time_str:
            return jsonify({
                'success': False,
                'message': '开始时间和结束时间不能为空'
            }), 400
        start_minutes = parse_time(start_time_str)
        end_minutes = parse_time(end_time_str)

        scheduler = core.get_scheduler()
        if scheduler is None:
            return jsonify({
                'success': False,
                'message': '调度器未初始化，请先执行调度'
            }), 400

        # 从数据库加载维修器具信息
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()

        c.execute('''
                  SELECT id, name, tool_type, capacity, daily_rental_cost, is_available, requires_operator
                  FROM maintenance_tools
                  ''')

        tools = {}
        tool_name_to_id = {}
        for row in c.fetchall():
            tool_id = row[0]
            tools[tool_id] = {
                'id': tool_id,
                'name': row[1],
                'tool_type': row[2],
                'capacity': row[3],
                'daily_rental_cost': float(row[4]),
                'is_available': bool(row[5]),
                'requires_operator': bool(row[6]),
                'usage_tasks': []
            }
            tool_name_to_id[row[1]] = tool_id

        # 查找在指定时间段内使用维修器具的任务
        task_count = 0
        for task in scheduler.schedule_plan:
            task_count += 1
            # 检查任务是否在查询时间段内
            if (task['start_time'] <= end_minutes and
                    task['end_time'] >= start_minutes):

                # 获取工序模板的工具需求
                process_id = task['process_id']
                if process_id.endswith('_MILESTONE'):
                    parts = process_id.split('_')
                    if len(parts) >= 2:
                        Equipment_id = parts[0]
                        process_code = parts[1]
                        # 查询工序模板的工具需求
                        c.execute('''
                                  SELECT pt.tools_requirements
                                  FROM process_templates pt
                                           INNER JOIN equipment_instances ei ON pt.equipment_type_id = ei.equipment_type_id
                                  WHERE ei.id = ?
                                    AND pt.process_code = ?
                                  ''', (Equipment_id, process_code))

                        template = c.fetchone()
                        if template:
                            tools_req = template[0]

                            tools_requirements = parse_tool_requirements(tools_req)
                            for tool_name, req_info in tools_requirements.items():
                                tool_id = tool_name_to_id.get(tool_name)
                                if tool_id and tool_id in tools:
                                    # 确定任务状态
                                    if task['end_time'] <= start_minutes:
                                        status = "已完成"
                                    elif task['start_time'] >= end_minutes:
                                        status = "未开始"
                                    else:
                                        status = "进行中"

                                    # 获取设备信息
                                    equipment = scheduler.get_equipment_by_id(task['equipment_id'])
                                    equipment_name = equipment.name if equipment else task['equipment_name']

                                    tool_usage = {
                                        'task_name': task['process_name'],
                                        'equipment': equipment_name,
                                        'start_time': scheduler.format_time(task['start_time']),
                                        'end_time': scheduler.format_time(task['end_time']),
                                        'status': status,
                                        'required_quantity': req_info.get('quantity', 1),
                                        'unit': req_info.get('unit', '台')
                                    }

                                    tools[tool_id]['usage_tasks'].append(tool_usage)

        conn.close()

        # 格式化返回数据
        tool_status = []
        for tool_id, tool_info in tools.items():
            usage_status = "占用" if tool_info['usage_tasks'] else "空闲"
            total_rental_days = 0
            for usage in tool_info['usage_tasks']:
                # 计算每个任务的使用天数
                start_minutes_task = parse_time(usage['start_time'])
                end_minutes_task = parse_time(usage['end_time'])
                task_duration_days = max(1, (end_minutes_task - start_minutes_task) / (24 * 60))
                total_rental_days += task_duration_days

            total_rental_cost = total_rental_days * tool_info['daily_rental_cost']
            tool_status.append({
                'tool_id': tool_id,
                'tool_name': tool_info['name'],
                'tool_type': tool_info['tool_type'],
                'capacity': tool_info['capacity'],
                'daily_rental_cost': tool_info['daily_rental_cost'],
                'is_available': tool_info['is_available'],
                'requires_operator': tool_info['requires_operator'],
                'usage_status': usage_status,
                'total_rental_days': round(total_rental_days, 2),
                'total_rental_cost': round(total_rental_cost, 2),
                'usage_tasks': tool_info['usage_tasks'],
                'current_tasks_count': len(tool_info['usage_tasks'])
            })

        return {
            'success': True,
            'maintenance_tool_status': tool_status,
            'time_period': f"{start_time_str} - {end_time_str}",
            'total_tools': len(tool_status),
            'tools_in_use': len([t for t in tool_status if t['usage_status'] == '占用'])
        }

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return {
            'success': False,
            'error': str(e),
            'error_details': error_details,
            'message': '获取维修器具状态失败'
        }