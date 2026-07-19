import json
import os
import sqlite3
import traceback
from datetime import datetime
from functools import wraps
from pathlib import Path

import jwt
from flask import Blueprint, jsonify, request

from app.core import run_scheduling, get_scheduler
from app import core
from app.utils import get_db_path, get_db_connection



JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'success': False, 'message': 'Token缺失'}), 401
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
            current_user_id = data['user_id']

            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute('SELECT role FROM users WHERE id = ?', (current_user_id,))
                user_row = c.fetchone()

            if not user_row:
                return jsonify({'success': False, 'message': '用户不存在'}), 401

            request.current_user_id = current_user_id
            request.current_user_role = user_row[0]

        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'message': 'Token已过期'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'message': '无效Token'}), 401

        return f(*args, **kwargs)

    return decorated

schedule_bp = Blueprint('schedule', __name__, url_prefix='/api')


@schedule_bp.route('/work-orders', methods=['GET'])
def get_work_orders():
    try:
        with get_db_connection(row_factory=sqlite3.Row) as conn:
            c = conn.cursor()
            query = """
                SELECT id, order_number, title, equipment_id, equipment_name,
                       status, created_by, created_at, scheduled_start_time,
                       scheduled_end_time, priority
                FROM work_orders
                ORDER BY created_at DESC
            """
            c.execute(query)
            rows = c.fetchall()
            work_orders = []
            for row in rows:
                work_orders.append({
                    'id': row['id'],
                    'order_number': row['order_number'],
                    'title': row['title'],
                    'equipment_id': row['equipment_id'],
                    'equipment_name': row['equipment_name'],
                    'status': row['status'],
                    'created_by': row['created_by'],
                    'created_at': row['created_at'],
                    'scheduled_start_time': row['scheduled_start_time'],
                    'scheduled_end_time': row['scheduled_end_time'],
                    'priority': row['priority']
                })
            # 不需要 conn.close()
            return jsonify({'success': True, 'data': work_orders})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'message': '获取工单列表失败'}), 500

@schedule_bp.route('/selected-workers', methods=['GET'])
def get_selected_workers():
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute('''
                SELECT sw.id, sw.name, sw.worker_type_id, sw.is_certified, sw.organization
                FROM selected_workers sw
                ORDER BY sw.worker_type_id, sw.id
            ''')
            selected_workers = []
            for row in c.fetchall():
                selected_workers.append({
                    'id': row[0],
                    'name': row[1],
                    'worker_type_id': row[2],
                    'worker_type': row[2],
                    'is_certified': bool(row[3]),
                    'organization': row[4]
                })
            # 不需要 conn.close()
            return jsonify({
                'success': True,
                'selected_workers': selected_workers,
                'total_count': len(selected_workers)
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'message': '获取选中工人失败'}), 500


@schedule_bp.route('/run-scheduler', methods=['POST'])
def run_scheduler():
    try:
        data = request.get_json()
        work_order_ids = data.get('work_order_ids', [])
        algorithm_name = data.get('algorithm', 'topological')
        if not work_order_ids:
            return jsonify({'success': False, 'message': '请至少选择一个工单进行调度'}), 400

        core.reset_scheduler()
        formatted_plan, statistics, success, message = run_scheduling(work_order_ids, algorithm_name)

        if not success:
            if isinstance(message, dict) and message.get('error_type') == 'insufficient_workers':
                return jsonify({
                    'success': False,
                    'error_type': 'insufficient_workers',
                    'message': '工人资源不足，无法开始调度',
                    'error_details': message.get('details', [])
                }), 400
            else:
                return jsonify({'success': False, 'message': str(message)}), 400

        worker_pool_data = {}
        try:
            scheduler = get_scheduler()
            if scheduler:
                worker_pool_data = scheduler.get_worker_pool()
        except Exception as e:
            print(f"获取工人池失败: {e}")

        return jsonify({
            'success': True,
            'algorithm': algorithm_name,
            'schedule_plan': formatted_plan,
            'statistics': statistics,
            'worker_pool': worker_pool_data
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e), 'trace': traceback.format_exc()}), 500


@schedule_bp.route('/assign-workers-from-schedule', methods=['POST'])
@token_required
def assign_workers_from_schedule():
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute('''
                SELECT schedule_id, process_id, process_name, equipment_id,
                       equipment_name, start_time, end_time, workers, predecessors
                FROM schedule_tasks
            ''')
            schedule_tasks = c.fetchall()

            if not schedule_tasks:
                return jsonify({'success': False, 'message': 'schedule_tasks 表中无调度数据，请先运行调度算法'}), 400

            assigned_count = 0
            errors = []

            for task in schedule_tasks:
                # ... 业务逻辑代码保持不变 ...
                
                conn.commit()
                return jsonify({
                    'success': True,
                    'message': f'工人分配完成，成功处理 {assigned_count} 个任务',
                    'assigned_count': assigned_count,
                    'errors': errors[:20]
                })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e), 'message': '工人分配失败'}), 500

@schedule_bp.route('/schedule-from-plan', methods=['POST'])
def run_scheduler_from_plan():
    """基于检修计划执行调度"""
    try:
        data = request.get_json()
        plan_id = data.get('plan_id')
        algorithm_name = data.get('algorithm', 'topological')
        target = data.get('target', 'minimize_duration')

        print(f"[DEBUG] plan_id={plan_id}, type={type(plan_id)}")  # ← 添加这行

        if not plan_id:
            return jsonify({'success': False, 'message': '请提供检修计划ID'}), 400
        
        from app.core import get_scheduler, reset_scheduler
        reset_scheduler()
        scheduler = get_scheduler()
        
        result = scheduler.schedule_from_maintenance_plan(plan_id, algorithm_name)

        print(f"[DEBUG] result type={type(result)}, result={result}")  # ← 添加这行
        
        if isinstance(result, tuple) and len(result) == 4:
            formatted_plan, statistics, success, message = result

            print(f"[DEBUG] result is tuple, success={success}, message={message}")  # ← 添加这行

            if not success:
                return jsonify({'success': False, 'message': str(message)}), 400
        
        if isinstance(result, dict) and result.get('success'):
            worker_pool_data = scheduler.get_worker_pool()
            return jsonify({
                'success': True,
                'algorithm': algorithm_name,
                'schedule_plan': result.get('schedule_plan', []),
                'statistics': result.get('statistics', {}),
                'worker_pool': worker_pool_data,
                'project_start_datetime': result.get('project_start_datetime'),
                'plan_id': result.get('plan_id'),
                'schedule_plan_id': result.get('schedule_plan_id')
            })
        
        print(f"[DEBUG] Falling through to error response")  # ← 添加这行
        
        return jsonify({'success': False, 'message': '调度执行失败'}), 400
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e), 'trace': traceback.format_exc()}), 500