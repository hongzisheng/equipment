"""调度算法执行路由

从原 app.py 抽取。调用 app.core 调度引擎完成排程。
"""
import traceback
from flask import Blueprint, jsonify, request

from app import core

scheduler_bp = Blueprint('scheduler', __name__, url_prefix='/api')


@scheduler_bp.route('/run-scheduler', methods=['POST'])
def run_scheduler():
    try:
        data = request.get_json()
        work_order_ids = data.get('work_order_ids', [])
        algorithm_name = data.get('algorithm', 'topological')
        if not work_order_ids:
            return jsonify({'success': False, 'message': '请至少选择一个工单进行调度'}), 400
        formatted_plan, statistics, success, message = core.run_scheduling(work_order_ids, algorithm_name)
        if not success:
            # 处理错误信息（可能是字符串或字典）
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
            sched = core.get_scheduler()
            if sched:
                worker_pool_data = sched.get_worker_pool()
        except Exception as e:
            # 工人池获取失败不应影响调度结果的返回，可记录日志
            print(f"获取工人池失败: {e}")
        return jsonify({
            'success': True,
            'algorithm': algorithm_name,
            'schedule_plan': formatted_plan,
            'statistics': statistics,
            'worker_pool': worker_pool_data
        })
    except Exception as e:
        traceback.print_exc()  # 打印到控制台
        return jsonify({'success': False, 'error': str(e), 'trace': traceback.format_exc()}), 500
