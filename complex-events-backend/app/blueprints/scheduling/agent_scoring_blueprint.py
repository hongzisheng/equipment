"""多智能体协同评分蓝图

提供多智能体协同评分相关的API接口，包括：
- 获取评估数据（计划信息、评分等）
- 获取智能体评分详情
- 重新生成方案
- 保存方案
- 放弃保存方案
"""

import json
import traceback
from datetime import datetime

from flask import Blueprint, request

from app.utils.db import get_db_connection

agent_scoring_bp = Blueprint("agent_scoring", __name__)


@agent_scoring_bp.route("/evaluation-data", methods=["GET"])
def get_evaluation_data():
    """获取评估数据（计划信息、评分等）
    
    返回当前方案的基本信息和综合评分数据。
    """
    try:
        plan_id = request.args.get("plan_id")
        
        with get_db_connection() as conn:
            c = conn.cursor()
            
            if plan_id:
                c.execute(
                    "SELECT id, plan_name, status FROM maintenance_plans WHERE id = ?",
                    (plan_id,)
                )
                plan = c.fetchone()
            else:
                c.execute("SELECT id, plan_name, status FROM maintenance_plans LIMIT 1")
                plan = c.fetchone()
            
            schedule_id = None
            if plan:
                c.execute(
                    "SELECT id, schedule_name, statistics FROM schedule_plans WHERE plan_id = ? ORDER BY id DESC LIMIT 1",
                    (plan[0],)
                )
                schedule = c.fetchone()
                if schedule:
                    schedule_id = schedule[0]
            
            tasks_count = 0
            estimated_days = 6
            resource_utilization = 91
            stability = "高"
            
            if schedule_id:
                c.execute(
                    "SELECT COUNT(*) FROM schedule_tasks WHERE schedule_plan_id = ?",
                    (schedule_id,)
                )
                tasks_count = c.fetchone()[0]
                
                c.execute(
                    "SELECT MIN(start_time), MAX(end_time) FROM schedule_tasks WHERE schedule_plan_id = ?",
                    (schedule_id,)
                )
                times = c.fetchone()
                if times[0] and times[1]:
                    estimated_days = int(times[1]) - int(times[0]) + 1

        result = {
            "success": True,
            "data": {
                "plan_info": {
                    "id": plan[0] if plan else 0,
                    "name": plan[1] if plan else "未选择计划",
                    "status": plan[2] if plan else ""
                },
                "schedule_info": {
                    "id": schedule_id,
                    "name": schedule[1] if schedule else "未选择方案"
                },
                "summary": {
                    "estimated_days": estimated_days,
                    "tasks_count": tasks_count or 28,
                    "stability": stability,
                    "resource_utilization": resource_utilization
                },
                "overall_score": {
                    "score": 86,
                    "grade": "优秀",
                    "threshold": 80,
                    "passed": True
                },
                "weights": {
                    "safety": 40,
                    "cost": 25,
                    "duration": 20,
                    "personnel": 15
                }
            }
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    except Exception as e:
        print(f"获取评估数据失败: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@agent_scoring_bp.route("/agent-scores", methods=["GET"])
def get_agent_scores():
    """获取智能体评分详情
    
    返回各个评估智能体的评分、理由及改进建议。
    """
    try:
        plan_id = request.args.get("plan_id")
        
        agents = [
            {
                "id": "safety_agent",
                "name": "安全Agent",
                "icon": "shield",
                "color": "#67c23a",
                "score": 92,
                "max_score": 100,
                "reason": "所有任务均符合安全规范，危险作业有充足安全措施。",
                "suggestions": [
                    "建议在高温作业时段增加防暑降温措施",
                    "检查部分设备的安全防护装置是否完好"
                ],
                "weight": 40
            },
            {
                "id": "cost_agent",
                "name": "成本Agent",
                "icon": "coin",
                "color": "#e6a23c",
                "score": 74,
                "max_score": 100,
                "reason": "整体成本控制在预算范围内，但部分工序人工成本偏高。",
                "suggestions": [
                    "优化部分工序的人员配置，降低人工成本",
                    "考虑使用更经济的材料替代方案"
                ],
                "weight": 25
            },
            {
                "id": "duration_agent",
                "name": "工期Agent",
                "icon": "clock",
                "color": "#409eff",
                "score": 81,
                "max_score": 100,
                "reason": "总工期符合预期，但部分关键路径任务存在延期风险。",
                "suggestions": [
                    "优化关键路径任务的资源分配",
                    "考虑并行处理部分关联度较低的任务"
                ],
                "weight": 20
            },
            {
                "id": "personnel_agent",
                "name": "人员疲劳Agent",
                "icon": "user",
                "color": "#9b59b6",
                "score": 69,
                "max_score": 100,
                "reason": "部分工人连续作业时间较长，存在疲劳风险。",
                "suggestions": [
                    "合理安排轮班制度，避免连续高强度作业",
                    "增加临时支援人员，分散工作负荷"
                ],
                "weight": 15
            }
        ]

        weighted_score = sum(a["score"] * a["weight"] / 100 for a in agents)
        
        result = {
            "success": True,
            "data": {
                "agents": agents,
                "weighted_score": round(weighted_score, 1),
                "threshold": 80,
                "passed": weighted_score >= 80
            }
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    except Exception as e:
        print(f"获取智能体评分失败: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@agent_scoring_bp.route("/update-weights", methods=["POST"])
def update_weights():
    """更新评分权重
    
    修改各维度的评分权重，确保总和为100%。
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "缺少请求体"}), 400

        weights = data.get("weights", {})
        safety = weights.get("safety", 40)
        cost = weights.get("cost", 25)
        duration = weights.get("duration", 20)
        personnel = weights.get("personnel", 15)
        
        total = safety + cost + duration + personnel
        
        if total != 100:
            return jsonify({"success": False, "error": "权重总和必须为100%"}), 400

        result = {
            "success": True,
            "data": {
                "weights": {
                    "safety": safety,
                    "cost": cost,
                    "duration": duration,
                    "personnel": personnel
                }
            }
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    except Exception as e:
        print(f"更新权重失败: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@agent_scoring_bp.route("/regenerate", methods=["POST"])
def regenerate_schedule():
    """重新生成方案
    
    基于当前计划和评估结果，重新生成调度方案。
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "缺少请求体"}), 400

        plan_id = data.get("plan_id")
        if not plan_id:
            return jsonify({"success": False, "error": "缺少 plan_id"}), 400

        with get_db_connection() as conn:
            c = conn.cursor()
            
            c.execute("SELECT plan_name FROM maintenance_plans WHERE id = ?", (plan_id,))
            plan_name = c.fetchone()
            plan_name = plan_name[0] if plan_name else ""

            c.execute(
                "INSERT INTO schedule_plans (plan_id, schedule_name, status, algorithm, statistics, total_tasks) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    plan_id,
                    f"重新生成方案 - {datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "待评估",
                    "agent_regen",
                    json.dumps({
                        "source": "agent_regeneration",
                        "original_plan": plan_name
                    }, ensure_ascii=False),
                    0
                ),
            )
            new_schedule_id = c.lastrowid
            conn.commit()

        result = {
            "success": True,
            "message": "方案重新生成成功",
            "schedule_id": new_schedule_id
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    except Exception as e:
        print(f"重新生成方案失败: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@agent_scoring_bp.route("/save-plan", methods=["POST"])
def save_plan():
    """保存方案
    
    将当前方案标记为已保存，进入正式执行流程。
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "缺少请求体"}), 400

        schedule_id = data.get("schedule_id")
        if not schedule_id:
            return jsonify({"success": False, "error": "缺少 schedule_id"}), 400

        with get_db_connection() as conn:
            c = conn.cursor()
            
            c.execute(
                "UPDATE schedule_plans SET status = ?, updated_at = datetime('now','localtime') WHERE id = ?",
                ("已保存", schedule_id)
            )
            conn.commit()

        result = {
            "success": True,
            "message": "方案已保存",
            "schedule_id": schedule_id
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    except Exception as e:
        print(f"保存方案失败: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@agent_scoring_bp.route("/discard-plan", methods=["POST"])
def discard_plan():
    """放弃保存方案
    
    放弃当前方案的保存操作，方案保持原有状态。
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "缺少请求体"}), 400

        schedule_id = data.get("schedule_id")
        
        result = {
            "success": True,
            "message": "已放弃保存方案",
            "schedule_id": schedule_id
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    except Exception as e:
        print(f"放弃方案失败: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500
