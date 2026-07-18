"""智能问答路由

基于 DashScope/OpenAI 兼容接口提供化工设备检修问答。
移植自 algorithm 分支的 chat 模块，适配 main 分支的目录结构。
"""
import json
import sqlite3

from flask import Blueprint, jsonify, request

from app.config import Config
from app.extension import get_openai_client
from app.utils import get_db_connection

chat_bp = Blueprint("chat", __name__, url_prefix="/api")


def _load_workers():
    """从调度数据库读取工人信息"""
    try:
        with get_db_connection(row_factory=sqlite3.Row) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM workers")
            rows = c.fetchall()
            return [dict(row) for row in rows] if rows else []
    except sqlite3.OperationalError:
        return []
    except Exception as e:
        print(f"读取工人信息失败: {e}")
        return []


def _load_equipment():
    """从调度数据库读取设备信息"""
    try:
        with get_db_connection(row_factory=sqlite3.Row) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM equipment")
            rows = c.fetchall()
            return [dict(row) for row in rows] if rows else []
    except sqlite3.OperationalError:
        return []
    except Exception as e:
        print(f"读取设备信息失败: {e}")
        return []


@chat_bp.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        if not data or "message" not in data:
            return jsonify({"success": False, "error": "缺少 message 参数"}), 400

        user_message = data["message"]
        include_rules = data.get("rule", 0)
        include_plan = data.get("plan", 0)
        include_selected_workers = data.get("selected_workers", 0)
        include_maintenance_tools = data.get("maintenance_tools", 0)

        system_message = """你是一个化工智能调度项目的助手。项目背景如下：
        1. 这是一个化工设备维修调度系统，所有调度时间单位均为天
        2. 系统管理各种化工设备（反应釜、离心机、干燥机等）的维修工序
        3. 涉及设备类型、工序模板、工人调度、物料管理、维修器具调配
        4. 系统支持拓扑排序、贪心算法、遗传算法等多种调度算法
        5. 调度考虑工人技能、设备可用性、工序依赖关系

        你的任务是帮助用户解决与化工设备调度、维修安排、资源配置相关的问题。
        请以专业、准确的方式回答用户的疑问。"""

        context_info = []
        if include_selected_workers == 1:
            workers = _load_workers()
            if workers:
                context_info.append("工人信息：")
                context_info.append(json.dumps(workers, ensure_ascii=False, indent=2))
        if include_maintenance_tools == 1:
            pass
        if include_rules == 1:
            pass
        if include_plan == 1:
            pass

        if context_info:
            system_message += "\n\n当前系统上下文:\n" + "\n".join(context_info)

        client = get_openai_client()
        response = client.chat.completions.create(
            model=Config.CHAT_MODEL,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
        )

        reply = response.choices[0].message.content
        return jsonify({
            "success": True,
            "reply": reply,
            "usage": {
                "total_tokens": response.usage.total_tokens,
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
            } if response.usage else None,
        })
    except RuntimeError as e:
        return jsonify({"success": False, "error": str(e), "message": "AI 服务配置错误"}), 500
    except Exception as e:
        import traceback
        print(f"Chat API Error: {e}")
        print(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "聊天功能出错",
        }), 500


@chat_bp.route("/chat/title", methods=["POST"])
def generate_title():
    """根据对话内容生成简短标题（控制成本：截断输入、低 tokens）"""
    try:
        data = request.get_json()
        if not data or "message" not in data:
            return jsonify({"success": False, "error": "缺少 message 参数"}), 400

        user_message = data["message"]
        # 截断 AI 回复，控制输入 token 成本
        ai_reply = (data.get("reply") or "")[:150]

        client = get_openai_client()
        response = client.chat.completions.create(
            model=Config.CHAT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "你是标题生成助手，根据对话内容提炼核心主题，生成简短准确的中文标题。",
                },
                {
                    "role": "user",
                    "content": (
                        f"请为以下对话生成一个中文标题。要求：不超过12字，不含标点和引号，"
                        f"排除寒暄客套，直接返回标题文字。\n\n"
                        f"用户：{user_message}\n助手：{ai_reply}"
                    ),
                },
            ],
            temperature=0.3,
            max_tokens=20,
        )

        title = response.choices[0].message.content.strip()
        # 后处理：取首行、去引号/标点、截断
        title = title.split("\n")[0].strip().strip("\"'""''「」【】。.，,！!？?：: ")
        if len(title) > 15:
            title = title[:15]
        if not title:
            return jsonify({"success": False, "error": "生成标题为空"})

        return jsonify({"success": True, "title": title})
    except RuntimeError as e:
        return jsonify({"success": False, "error": str(e)}), 500
    except Exception as e:
        print(f"Title API Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
