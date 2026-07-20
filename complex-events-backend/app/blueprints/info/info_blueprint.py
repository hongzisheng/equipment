import sqlite3
from flask import request

from app.models import Result
from app.utils.db import get_db_connection
from . import info_bp


@info_bp.route("/workers", methods=["POST"])
def get_workers():
    try:
        with get_db_connection(sqlite3.Row) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    w.id,
                    w.name,
                    w.worker_type_id AS role,
                    w.status,
                    w.organization,
                    COALESCE(wt.name, w.worker_type_id) AS role_name
                FROM workers w
                LEFT JOIN worker_types wt ON w.worker_type_id = wt.id
                ORDER BY w.id
            """)
            
            rows = cursor.fetchall()
            
            cursor.execute("""
                SELECT 
                    wtw.worker_id,
                    wtw.task_id,
                    wtw.status AS assignment_status,
                    wtw.worker_name,
                    wtw.worker_type,
                    wot.id AS work_order_task_id,
                    wot.process_name AS task_name,
                    wot.status AS task_status,
                    wot.task_code,
                    wot.scheduled_start_time AS start_time,
                    wot.scheduled_end_time AS end_time,
                    wo.equipment_name,
                    wo.equipment_id
                FROM work_order_task_workers wtw
                LEFT JOIN work_order_tasks wot ON wtw.task_id = wot.id
                LEFT JOIN work_orders wo ON wot.work_order_id = wo.id
                ORDER BY wtw.worker_id, wtw.task_id
            """)
            
            task_rows = cursor.fetchall()
            
            worker_tasks_map = {}
            for task_row in task_rows:
                worker_id = task_row["worker_id"]
                if worker_id not in worker_tasks_map:
                    worker_tasks_map[worker_id] = []
                worker_tasks_map[worker_id].append({
                    "task_id": task_row["task_id"],
                    "task_name": task_row["task_name"] or task_row["task_code"] or "未知任务",
                    "status": task_row["task_status"] or task_row["assignment_status"],
                    "equipment": task_row["equipment_name"] or "未知设备",
                    "start_time": task_row["start_time"] or "",
                    "end_time": task_row["end_time"] or "",
                    "work_order_code": task_row["task_code"] or ""
                })
            
            worker_status_list = []
            for row in rows:
                worker_id = row["id"]
                tasks = worker_tasks_map.get(worker_id, [])
                has_active_tasks = any(t["status"] not in ("completed", "confirmed", "cancelled") for t in tasks)
                status_text = "工作中" if has_active_tasks else ("空闲中" if len(tasks) == 0 else "已完成")
                
                worker_status_list.append({
                    "id": worker_id,
                    "name": row["name"],
                    "role": row["role_name"] or row["role"],
                    "status": status_text,
                    "organization": row["organization"],
                    "skill_level": "高级",
                    "tasks": tasks
                })
            
            return Result.success(message="查询成功", data={"worker_status": worker_status_list})
    
    except Exception as e:
        return Result.fail(message=f"查询失败: {str(e)}")


@info_bp.route("/orders", methods=["GET"])
def get_orders():
    try:
        with get_db_connection(sqlite3.Row) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    wo.id AS work_order_id,
                    wo.order_number,
                    wo.title AS process_name,
                    wo.status,
                    wo.equipment_id,
                    wo.equipment_name,
                    wo.priority
                FROM work_orders wo
                ORDER BY wo.created_at DESC
            """)
            
            rows = cursor.fetchall()
            
            orders_list = []
            for row in rows:
                orders_list.append({
                    "work_order_id": row["work_order_id"],
                    "order_number": row["order_number"],
                    "process_name": row["process_name"],
                    "status": row["status"],
                    "work_order_status": row["status"],
                    "equipment_id": row["equipment_id"],
                    "equipment_name": row["equipment_name"],
                    "priority": row["priority"]
                })
            
            return Result.success(message="查询成功", data={"data": orders_list})
    
    except Exception as e:
        return Result.fail(message=f"查询失败: {str(e)}")


def parse_material_requirements(req_str):
    result = {}
    if not req_str or not isinstance(req_str, str):
        return result
    if not (req_str.startswith('{') and req_str.endswith('}')):
        return result
    content = req_str[1:-1]
    items = content.split('、')
    for item in items:
        parts = item.split('：')
        if len(parts) >= 2:
            name = parts[0].strip()
            value = parts[1].strip()
            num_str = ''
            unit_str = ''
            for c in value:
                if c.isdigit() or c == '.':
                    num_str += c
                else:
                    unit_str += c
            try:
                qty = float(num_str) if num_str else 0
                result[name] = {
                    'quantity': qty,
                    'unit': unit_str.strip()
                }
            except ValueError:
                pass
    return result


@info_bp.route("/materials", methods=["POST"])
def get_materials():
    try:
        with get_db_connection(sqlite3.Row) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    id,
                    name AS material_name,
                    stock_quantity AS initial_stock,
                    stock_quantity AS current_stock,
                    unit
                FROM materials
                ORDER BY id
            """)
            
            rows = cursor.fetchall()
            
            cursor.execute("""
                SELECT t.status, p.material_requirements
                FROM work_order_tasks t
                LEFT JOIN process_templates p ON t.process_code = p.process_code
            """)
            task_rows = cursor.fetchall()
            
            plan_usage = {}
            actual_usage = {}
            
            for task_row in task_rows:
                status = task_row["status"]
                req_str = task_row["material_requirements"]
                requirements = parse_material_requirements(req_str)
                for mat_name, mat_info in requirements.items():
                    qty = mat_info.get("quantity", 0)
                    if mat_name not in plan_usage:
                        plan_usage[mat_name] = 0
                        actual_usage[mat_name] = 0
                    plan_usage[mat_name] += qty
                    if status == "completed" or status == "confirmed":
                        actual_usage[mat_name] += qty
            
            materials_list = []
            for row in rows:
                mat_name = row["material_name"]
                materials_list.append({
                    "material_name": mat_name,
                    "initial_stock": round(row["initial_stock"], 2),
                    "current_stock": round(row["current_stock"], 2),
                    "unit": row["unit"],
                    "plan_usage": round(plan_usage.get(mat_name, 0), 2),
                    "actual_usage": round(actual_usage.get(mat_name, 0), 2)
                })
            
            return Result.success(message="查询成功", data={"material_inventory": materials_list})
    
    except Exception as e:
        return Result.fail(message=f"查询失败: {str(e)}")


@info_bp.route("/tools", methods=["POST"])
def get_tools():
    try:
        with get_db_connection(sqlite3.Row) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    id AS tool_id,
                    name AS tool_name,
                    tool_type,
                    is_available
                FROM maintenance_tools
                ORDER BY id
            """)
            
            rows = cursor.fetchall()
            
            cursor.execute("""
                SELECT id, description, tools_requirements 
                FROM process_templates 
                WHERE tools_requirements IS NOT NULL AND tools_requirements != ''
            """)
            template_rows = cursor.fetchall()
            
            template_map = {}
            for row in template_rows:
                template_map[row["id"]] = row
                template_map[str(row["id"])] = row
            
            cursor.execute("""
                SELECT id AS task_id, process_name, status, task_code, process_id
                FROM work_order_tasks
                WHERE status NOT IN ('completed', 'confirmed', 'cancelled')
            """)
            task_rows = cursor.fetchall()
            
            tool_tasks = {}
            
            for task_row in task_rows:
                task_id = task_row["task_id"]
                process_name = task_row["process_name"]
                task_code = task_row["task_code"]
                status = task_row["status"]
                process_id = task_row["process_id"]
                
                matched_template = template_map.get(process_id)
                
                if matched_template:
                    template_description = matched_template["description"]
                    if template_description and template_description not in process_name:
                        matched_template = None
                
                if not matched_template:
                    for template in template_rows:
                        template_description = template["description"]
                        if template_description and template_description in process_name:
                            matched_template = template
                            break
                
                if matched_template:
                    req_str = matched_template["tools_requirements"]
                    requirements = parse_material_requirements(req_str)
                    for tool_name, tool_info in requirements.items():
                        if tool_name not in tool_tasks:
                            tool_tasks[tool_name] = []
                        
                        exists = False
                        for existing_task in tool_tasks[tool_name]:
                            if existing_task["task_id"] == task_id:
                                existing_task["quantity"] += round(tool_info.get("quantity", 0), 2)
                                exists = True
                                break
                        
                        if not exists:
                            tool_tasks[tool_name].append({
                                "task_id": task_id,
                                "task_name": process_name or task_code,
                                "work_order_code": task_code,
                                "status": status,
                                "quantity": round(tool_info.get("quantity", 0), 2),
                                "unit": tool_info.get("unit", "")
                            })
            
            tools_list = []
            for row in rows:
                tool_name = row["tool_name"]
                tasks = []
                for req_name, req_tasks in tool_tasks.items():
                    if tool_name in req_name or req_name in tool_name:
                        tasks.extend(req_tasks)
                in_use_tasks = [t for t in tasks if t["status"] not in ("completed", "confirmed", "cancelled")]
                
                tools_list.append({
                    "tool_id": row["tool_id"],
                    "tool_name": tool_name,
                    "tool_type": row["tool_type"],
                    "usage_status": "占用" if len(in_use_tasks) > 0 else "空闲",
                    "usage_tasks": in_use_tasks
                })
            
            return Result.success(message="查询成功", data={"maintenance_tool_status": tools_list})
    
    except Exception as e:
        return Result.fail(message=f"查询失败: {str(e)}")