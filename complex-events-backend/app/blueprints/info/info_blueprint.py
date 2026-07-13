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
                    CASE WHEN w.skill_level = 1 THEN '初级' WHEN w.skill_level = 2 THEN '中级' ELSE '高级' END AS skill_level
                FROM workers w
                ORDER BY w.id
            """)
            
            rows = cursor.fetchall()
            
            worker_status_list = []
            for row in rows:
                worker_status_list.append({
                    "id": row["id"],
                    "name": row["name"],
                    "role": row["role"],
                    "status": "工作中" if row["status"] == "1" else ("空闲中" if row["status"] == "0" else row["status"]),
                    "organization": row["organization"],
                    "skill_level": row["skill_level"],
                    "tasks": []
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
            
            materials_list = []
            for row in rows:
                materials_list.append({
                    "material_name": row["material_name"],
                    "initial_stock": row["initial_stock"],
                    "current_stock": row["current_stock"],
                    "unit": row["unit"]
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
            
            tools_list = []
            for row in rows:
                tools_list.append({
                    "tool_id": row["tool_id"],
                    "tool_name": row["tool_name"],
                    "tool_type": row["tool_type"],
                    "usage_status": "空闲" if row["is_available"] else "占用",
                    "usage_tasks": []
                })
            
            return Result.success(message="查询成功", data={"maintenance_tool_status": tools_list})
    
    except Exception as e:
        return Result.fail(message=f"查询失败: {str(e)}")