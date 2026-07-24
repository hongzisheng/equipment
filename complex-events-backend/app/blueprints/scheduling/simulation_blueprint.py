"""模拟沙盘验证路由

提供基于自然语言和甘特图拖拽的调度方案虚拟推演功能。
包括：
1. 获取当前调度方案甘特图数据
2. 自然语言指令解析为结构化修改计划
3. 虚拟推演（基于修改计划模拟调度变化）
4. 大模型影响分析（工期、资源、安全风险）
"""
import json
import sqlite3
import traceback

from flask import Blueprint, jsonify, request

from app.extension import get_openai_client
from app.config import Config
from app.utils import get_db_connection

simulation_bp = Blueprint("simulation", __name__, url_prefix="/api/simulation")


# ===================== 数据读取 =====================

def _load_schedule_tasks(schedule_plan_id=None):
    """从数据库读取调度任务列表"""
    try:
        with get_db_connection(row_factory=sqlite3.Row) as conn:
            c = conn.cursor()
            if schedule_plan_id:
                c.execute(
                    "SELECT * FROM schedule_tasks WHERE schedule_plan_id = ? ORDER BY start_time",
                    (schedule_plan_id,),
                )
            else:
                c.execute(
                    "SELECT * FROM schedule_tasks ORDER BY schedule_plan_id DESC, start_time"
                )
            rows = c.fetchall()
            return [dict(row) for row in rows] if rows else []
    except sqlite3.OperationalError:
        return []
    except Exception as e:
        print(f"读取调度任务失败: {e}")
        return []


def _load_schedule_plan_info(schedule_plan_id):
    """读取调度方案信息"""
    try:
        with get_db_connection(row_factory=sqlite3.Row) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM schedule_plans WHERE id = ?", (schedule_plan_id,))
            row = c.fetchone()
            return dict(row) if row else None
    except Exception:
        return None


def _load_workers():
    """读取工人信息"""
    try:
        with get_db_connection(row_factory=sqlite3.Row) as conn:
            c = conn.cursor()
            c.execute("SELECT id, name, worker_type_id, status FROM workers")
            return [dict(row) for row in c.fetchall()]
    except Exception:
        return []


def _load_equipment():
    """读取设备信息"""
    try:
        with get_db_connection(row_factory=sqlite3.Row) as conn:
            c = conn.cursor()
            c.execute("SELECT id, name, status FROM equipment_instances")
            return [dict(row) for row in c.fetchall()]
    except Exception:
        return []


def _load_maintenance_plans():
    """读取检修计划列表（用于下拉选择）"""
    try:
        with get_db_connection(row_factory=sqlite3.Row) as conn:
            c = conn.cursor()
            c.execute(
                "SELECT id, plan_name, status FROM maintenance_plans ORDER BY id DESC"
            )
            return [dict(row) for row in c.fetchall()]
    except Exception:
        return []


def _load_schedule_plans_by_maintenance(plan_id):
    """根据检修计划ID读取关联的调度方案列表"""
    try:
        with get_db_connection(row_factory=sqlite3.Row) as conn:
            c = conn.cursor()
            c.execute(
                "SELECT id, schedule_name, algorithm, status, created_at "
                "FROM schedule_plans WHERE plan_id = ? ORDER BY id DESC",
                (plan_id,),
            )
            return [dict(row) for row in c.fetchall()]
    except Exception:
        return []


# ===================== API 路由 =====================

@simulation_bp.route("/init-data", methods=["GET"])
def get_init_data():
    """初始化数据：检修计划列表"""
    try:
        plans = _load_maintenance_plans()
        return jsonify({"success": True, "plans": plans})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@simulation_bp.route("/schedule-plans/<int:plan_id>", methods=["GET"])
def get_schedule_plans(plan_id):
    """获取某检修计划下的调度方案列表"""
    try:
        plans = _load_schedule_plans_by_maintenance(plan_id)
        return jsonify({"success": True, "data": plans})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@simulation_bp.route("/gantt-data", methods=["GET"])
def get_gantt_data():
    """获取甘特图数据（当前调度方案的任务列表）"""
    try:
        schedule_plan_id = request.args.get("schedule_plan_id", type=int)
        if not schedule_plan_id:
            return jsonify({"success": False, "error": "缺少 schedule_plan_id 参数"}), 400

        tasks = _load_schedule_tasks(schedule_plan_id)
        plan_info = _load_schedule_plan_info(schedule_plan_id)

        # 转换为前端甘特图所需格式
        gantt_tasks = []
        for t in tasks:
            gantt_tasks.append({
                "schedule_id": t.get("schedule_id"),
                "process_id": t.get("process_id"),
                "process_name": t.get("process_name"),
                "equipment_id": t.get("equipment_id"),
                "equipment_name": t.get("equipment_name"),
                "equipment_type_name": t.get("equipment_type_name"),
                "start_time": t.get("start_time"),
                "end_time": t.get("end_time"),
                "start_time_formatted": t.get("start_time_formatted"),
                "end_time_formatted": t.get("end_time_formatted"),
                "duration_days": t.get("duration_days"),
                "workers": t.get("workers"),
                "predecessors": t.get("predecessors"),
                "worker_price": t.get("worker_price"),
            })

        return jsonify({
            "success": True,
            "tasks": gantt_tasks,
            "plan_info": plan_info,
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@simulation_bp.route("/parse-command", methods=["POST"])
def parse_command():
    """自然语言指令解析：将用户的自然语言修改意图转为结构化修改计划"""
    try:
        data = request.get_json()
        if not data or "command" not in data:
            return jsonify({"success": False, "error": "缺少 command 参数"}), 400

        command = data["command"]
        current_tasks = data.get("current_tasks", [])

        client = get_openai_client()
        system_prompt = """你是一个化工设备检修调度系统的自然语言解析助手。
用户会用自然语言描述对调度方案的修改意图，你需要将其解析为结构化的JSON修改计划。

修改计划的JSON格式如下：
{
  "modifications": [
    {
      "type": "reschedule",       // 修改类型: reschedule(调整时间), reassign(更换工人), add_task(新增任务), remove_task(删除任务), change_order(调整顺序)
      "target_process": "工序名称", // 目标工序名称
      "target_process_id": "工序ID", // 目标工序ID（如有）
      "params": {
        "new_start_time": 5,       // 新开始时间（天，相对项目起点）
        "new_end_time": 8,         // 新结束时间（天）
        "new_workers": {"钳工": "张三"}, // 更换后的工人
        "reason": "用户指定的原因"
      }
    }
  ],
  "summary": "修改计划的简要描述"
}

注意：
1. 时间单位为天，相对于项目起始日
2. 只返回JSON，不要有任何其他文字
3. 如果无法理解用户意图，返回 {"modifications": [], "summary": "无法解析用户指令"}"""

        user_content = f"用户指令：{command}\n\n当前调度任务列表（摘要）：\n"
        for t in current_tasks[:20]:
            user_content += f"- 工序: {t.get('process_name', '未知')}, ID: {t.get('process_id', '')}, 开始: 第{t.get('start_time', 0)}天, 结束: 第{t.get('end_time', 0)}天, 工人: {t.get('workers', '无')}\n"

        response = client.chat.completions.create(
            model=Config.CHAT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.1,
        )

        raw = response.choices[0].message.content.strip()
        # 尝试提取JSON
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return jsonify({
                "success": False,
                "error": "大模型返回格式异常，无法解析为JSON",
                "raw_response": raw,
            }), 500

        return jsonify({"success": True, "modification_plan": parsed})

    except RuntimeError as e:
        return jsonify({"success": False, "error": str(e), "message": "AI服务配置错误"}), 500
    except Exception as e:
        print(f"解析指令失败: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@simulation_bp.route("/run-simulation", methods=["POST"])
def run_simulation():
    """虚拟推演：基于修改计划模拟调度方案变化

    接收修改计划 + 当前任务列表，在内存中模拟应用修改后的新调度方案，
    返回修改前后的对比数据。
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "缺少请求体"}), 400

        original_tasks = data.get("original_tasks", [])
        modifications = data.get("modifications", [])
        # manual_edits: 用户在甘特图上直接拖拽产生的修改（与自然语言修改合并）
        manual_edits = data.get("manual_edits", [])

        # 合并所有修改
        all_mods = list(modifications) + list(manual_edits)

        # 深拷贝原始任务
        import copy
        simulated_tasks = copy.deepcopy(original_tasks)

        # 应用每条修改
        applied_mods = []
        for mod in all_mods:
            mod_type = mod.get("type")
            target = mod.get("target_process_id") or mod.get("target_process")
            params = mod.get("params", {})

            matched = False
            for task in simulated_tasks:
                task_id = str(task.get("process_id", ""))
                task_name = task.get("process_name", "")
                if target and (target == task_id or target == task_name):
                    matched = True
                    if mod_type == "reschedule":
                        if "new_start_time" in params:
                            task["start_time"] = params["new_start_time"]
                        if "new_end_time" in params:
                            task["end_time"] = params["new_end_time"]
                        # 重算工期
                        try:
                            task["duration_days"] = float(task["end_time"]) - float(task["start_time"])
                        except (TypeError, ValueError):
                            pass
                    elif mod_type == "reassign":
                        if "new_workers" in params:
                            task["workers"] = json.dumps(params["new_workers"], ensure_ascii=False)
                    elif mod_type == "change_order":
                        if "new_start_time" in params:
                            old_start = task.get("start_time", 0)
                            delta = params["new_start_time"] - old_start
                            task["start_time"] = params["new_start_time"]
                            task["end_time"] = task.get("end_time", 0) + delta

                    applied_mods.append({
                        "process": task.get("process_name"),
                        "type": mod_type,
                        "details": params,
                    })
                    break

            if not matched and mod_type == "add_task":
                new_task = {
                    "process_id": params.get("process_id", f"new_{len(simulated_tasks)}"),
                    "process_name": params.get("process_name", "新增工序"),
                    "equipment_name": params.get("equipment_name", ""),
                    "start_time": params.get("new_start_time", 0),
                    "end_time": params.get("new_end_time", 0),
                    "duration_days": params.get("new_end_time", 0) - params.get("new_start_time", 0),
                    "workers": json.dumps(params.get("new_workers", {}), ensure_ascii=False),
                    "predecessors": "",
                }
                simulated_tasks.append(new_task)
                applied_mods.append({
                    "process": new_task["process_name"],
                    "type": "add_task",
                    "details": params,
                })

        # 排序
        simulated_tasks.sort(key=lambda x: float(x.get("start_time", 0) or 0))

        # 计算统计指标
        def _calc_stats(tasks):
            if not tasks:
                return {"total_tasks": 0, "total_duration": 0, "start": 0, "end": 0}
            starts = [float(t.get("start_time", 0) or 0) for t in tasks]
            ends = [float(t.get("end_time", 0) or 0) for t in tasks]
            return {
                "total_tasks": len(tasks),
                "total_duration": max(ends) - min(starts) if starts else 0,
                "start": min(starts) if starts else 0,
                "end": max(ends) if ends else 0,
            }

        original_stats = _calc_stats(original_tasks)
        simulated_stats = _calc_stats(simulated_tasks)

        # 计算差异
        diff = {
            "duration_change": simulated_stats["total_duration"] - original_stats["total_duration"],
            "task_count_change": simulated_stats["total_tasks"] - original_stats["total_tasks"],
            "end_time_change": simulated_stats["end"] - original_stats["end"],
        }

        return jsonify({
            "success": True,
            "original_tasks": original_tasks,
            "simulated_tasks": simulated_tasks,
            "applied_modifications": applied_mods,
            "original_stats": original_stats,
            "simulated_stats": simulated_stats,
            "diff": diff,
        })
    except Exception as e:
        print(f"虚拟推演失败: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@simulation_bp.route("/analyze-impact", methods=["POST"])
def analyze_impact():
    """大模型影响分析：基于推演结果，分析工期、资源、安全风险等影响"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "缺少请求体"}), 400

        original_tasks = data.get("original_tasks", [])
        simulated_tasks = data.get("simulated_tasks", [])
        applied_mods = data.get("applied_modifications", [])
        original_stats = data.get("original_stats", {})
        simulated_stats = data.get("simulated_stats", {})
        user_command = data.get("user_command", "")

        client = get_openai_client()

        system_prompt = """你是一个化工设备检修调度方案的影响分析专家。
基于虚拟推演前后的调度方案对比，你需要从以下维度进行影响分析：

1. **工期影响**：总工期变化、关键路径是否改变、工序衔接是否受影响
2. **资源影响**：工人分配是否合理、是否有资源冲突、设备利用率变化
3. **安全风险**：工序顺序变更是否带来安全隐患、是否有高危作业重叠
4. **成本影响**：工期变化导致的成本变化、资源重新分配的成本
5. **建议**：是否推荐采用此修改方案，如有问题给出改进建议

请以结构化JSON格式返回分析结果：
{
  "duration_impact": {"level": "低/中/高", "description": "..."},
  "resource_impact": {"level": "低/中/高", "description": "..."},
  "safety_risk": {"level": "低/中/高", "description": "..."},
  "cost_impact": {"level": "低/中/高", "description": "..."},
  "recommendation": "推荐/不推荐/需修改",
  "suggestions": ["建议1", "建议2"]
}

只返回JSON，不要有其他文字。"""

        # 构建用户消息
        user_content = f"用户修改意图：{user_command}\n\n"
        user_content += f"应用的修改：{json.dumps(applied_mods, ensure_ascii=False, indent=2)}\n\n"
        user_content += f"原始统计：{json.dumps(original_stats, ensure_ascii=False)}\n"
        user_content += f"推演后统计：{json.dumps(simulated_stats, ensure_ascii=False)}\n\n"

        user_content += "原始调度方案（摘要）：\n"
        for t in original_tasks[:15]:
            user_content += f"- {t.get('process_name', '?')}: 第{t.get('start_time', 0)}天-第{t.get('end_time', 0)}天, 工人: {t.get('workers', '无')}\n"

        user_content += "\n推演后调度方案（摘要）：\n"
        for t in simulated_tasks[:15]:
            user_content += f"- {t.get('process_name', '?')}: 第{t.get('start_time', 0)}天-第{t.get('end_time', 0)}天, 工人: {t.get('workers', '无')}\n"

        response = client.chat.completions.create(
            model=Config.CHAT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
        )

        raw = response.choices[0].message.content.strip()
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()

        try:
            analysis = json.loads(raw)
        except json.JSONDecodeError:
            analysis = {
                "duration_impact": {"level": "未知", "description": raw},
                "resource_impact": {"level": "未知", "description": ""},
                "safety_risk": {"level": "未知", "description": ""},
                "cost_impact": {"level": "未知", "description": ""},
                "recommendation": "需人工复核",
                "suggestions": ["大模型返回格式异常，请人工复核分析结果"],
            }

        return jsonify({"success": True, "analysis": analysis})

    except RuntimeError as e:
        return jsonify({"success": False, "error": str(e), "message": "AI服务配置错误"}), 500
    except Exception as e:
        print(f"影响分析失败: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@simulation_bp.route("/generate-report", methods=["POST"])
def generate_report():
    """生成完整报告：基于推演结果和影响分析，生成结构化报告"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "缺少请求体"}), 400

        original_stats = data.get("original_stats", {})
        simulated_stats = data.get("simulated_stats", {})
        analysis = data.get("analysis", {})
        applied_mods = data.get("applied_modifications", [])
        plan_info = data.get("plan_info", {})
        user_command = data.get("user_command", "")

        report = {
            "report_title": f"模拟沙盘验证报告 - {plan_info.get('schedule_name', '未命名方案')}",
            "report_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "plan_info": plan_info,
            "user_command": user_command,
            "executive_summary": {
                "original_duration": original_stats.get("total_duration", 0),
                "simulated_duration": simulated_stats.get("total_duration", 0),
                "duration_change": simulated_stats.get("total_duration", 0) - original_stats.get("total_duration", 0),
                "recommendation": analysis.get("recommendation", "需人工复核"),
            },
            "original_stats": original_stats,
            "simulated_stats": simulated_stats,
            "applied_modifications": applied_mods,
            "impact_analysis": analysis,
            "detailed_items": [
                {
                    "category": "工期影响",
                    "level": analysis.get("duration_impact", {}).get("level", "未知"),
                    "description": analysis.get("duration_impact", {}).get("description", ""),
                },
                {
                    "category": "资源影响",
                    "level": analysis.get("resource_impact", {}).get("level", "未知"),
                    "description": analysis.get("resource_impact", {}).get("description", ""),
                },
                {
                    "category": "安全风险",
                    "level": analysis.get("safety_risk", {}).get("level", "未知"),
                    "description": analysis.get("safety_risk", {}).get("description", ""),
                },
                {
                    "category": "成本影响",
                    "level": analysis.get("cost_impact", {}).get("level", "未知"),
                    "description": analysis.get("cost_impact", {}).get("description", ""),
                },
            ],
            "suggestions": analysis.get("suggestions", []),
        }

        return jsonify({"success": True, "report": report})
    except Exception as e:
        print(f"生成报告失败: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@simulation_bp.route("/execute-plan", methods=["POST"])
def execute_plan():
    """落地执行：将模拟方案正式应用到生产环境

    创建新的调度方案记录，更新相关状态。
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "缺少请求体"}), 400

        plan_id = data.get("plan_id")
        schedule_name = data.get("schedule_name")
        simulated_tasks = data.get("simulated_tasks", [])
        analysis = data.get("analysis", {})

        if not plan_id:
            return jsonify({"success": False, "error": "缺少 plan_id"}), 400

        with get_db_connection() as conn:
            c = conn.cursor()

            c.execute(
                "INSERT INTO schedule_plans (plan_id, schedule_name, status, algorithm, statistics, total_tasks) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    plan_id,
                    schedule_name or f"模拟推演方案 - {datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "生效中",
                    "simulation",
                    json.dumps({
                        "source": "simulation",
                        "analysis": analysis,
                    }, ensure_ascii=False),
                    len(simulated_tasks),
                ),
            )
            new_schedule_id = c.lastrowid

            for task in simulated_tasks:
                c.execute(
                    "INSERT INTO schedule_tasks (schedule_plan_id, process_id, process_name, "
                    "equipment_id, equipment_name, equipment_type_name, start_time, end_time, "
                    "duration_days, workers, predecessors, worker_price) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        new_schedule_id,
                        task.get("process_id", ""),
                        task.get("process_name", ""),
                        task.get("equipment_id", 0),
                        task.get("equipment_name", ""),
                        task.get("equipment_type_name", ""),
                        task.get("start_time", 0),
                        task.get("end_time", 0),
                        task.get("duration_days", 0),
                        task.get("workers", "{}"),
                        task.get("predecessors", "[]"),
                        task.get("worker_price", ""),
                    ),
                )

            conn.commit()

        return jsonify({
            "success": True,
            "message": "方案已成功落地执行",
            "schedule_id": new_schedule_id,
        })
    except Exception as e:
        print(f"落地执行失败: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500
