"""调度生成路由

从 algorithm 分支移植，调用 core 调度引擎完成排程。
"""
import traceback

from flask import jsonify, request

from . import workorder_mgmt_bp
from app import core


@workorder_mgmt_bp.route("/run-scheduler", methods=["POST"])
def run_scheduler():
    """运行调度算法"""
    try:
        data = request.get_json()
        work_order_ids = data.get("work_order_ids", [])
        algorithm_name = data.get("algorithm", "topological")

        if not work_order_ids:
            return jsonify(
                {"success": False, "message": "请至少选择一个工单进行调度"}
            ), 400

        # 重置调度器以重新加载数据
        core.reset_scheduler()

        formatted_plan, statistics, success, message = core.run_scheduling(
            work_order_ids, algorithm_name
        )

        if not success:
            if isinstance(message, dict) and message.get("error_type") == "insufficient_workers":
                return jsonify(
                    {
                        "success": False,
                        "error_type": "insufficient_workers",
                        "message": "工人资源不足，无法开始调度",
                        "error_details": message.get("details", []),
                    }
                ), 400
            else:
                return jsonify({"success": False, "message": str(message)}), 400

        # 获取工人池信息
        worker_pool_data = {}
        try:
            sched = core.get_scheduler()
            if sched:
                worker_pool_data = sched.get_worker_pool()
        except Exception as e:
            print(f"获取工人池失败: {e}")

        return jsonify(
            {
                "success": True,
                "algorithm": algorithm_name,
                "schedule_plan": formatted_plan,
                "statistics": statistics,
                "worker_pool": worker_pool_data,
            }
        )
    except Exception as e:
        traceback.print_exc()
        return jsonify(
            {"success": False, "error": str(e), "trace": traceback.format_exc()}
        ), 500
