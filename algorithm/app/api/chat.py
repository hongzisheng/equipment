"""智能问答路由

从原 app.py 抽取。通过 DashScope/OpenAI 兼容接口提供化工调度问答，
可按需注入工序、调度方案、工人、维修器具上下文。
"""
import json
import sqlite3

from flask import Blueprint, jsonify, request

from app import models
from app.extensions import get_openai_client
from app.utils import get_db_path

chat_bp = Blueprint('chat', __name__, url_prefix='/api')


class AppDataManager:
    """应用数据管理器，复用 models 中的接口"""
    @staticmethod
    def get_equipment_types():
        """获取所有设备类型"""
        db_path = get_db_path()
        return models.DatabaseManager.load_equipment_types_from_db(str(db_path))

    @staticmethod
    def get_equipment_instances():
        """获取所有设备实例"""
        db_path = get_db_path()
        return models.load_equipment_instances(str(db_path))

    @staticmethod
    def get_workers():
        """获取所有工人"""
        db_path = get_db_path()
        return models.load_workers(str(db_path))

    @staticmethod
    def get_materials():
        """获取所有材料"""
        db_path = get_db_path()
        return models.load_materials(str(db_path))

    @staticmethod
    def get_maintenance_tools():
        """获取所有维修器具"""
        db_path = get_db_path()
        return models.load_maintenance_tools(str(db_path))

    @staticmethod
    def get_all_process_templates():
        """获取所有工序模板"""
        db_path = get_db_path()
        return models.DatabaseManager.load_process_templates_from_db(str(db_path))

    @staticmethod
    def get_selected_workers():
        """获取所有选择的工人"""
        db_path = get_db_path()
        return models.DatabaseManager.load_selected_workers_from_db(str(db_path))

    @staticmethod
    def get_selected_equipment_instances():
        """获取所有选择的设备实例"""
        db_path = get_db_path()
        return models.DatabaseManager.load_selected_equipment_instances_from_db(str(db_path))


@chat_bp.route('/chat', methods=['POST'])
def chat():
    try:
        # 获取前端发送的JSON数据
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({
                'success': False,
                'error': '缺少message参数'
            }), 400
        user_message = data['message']
        include_rules = data.get('rule', 0)
        include_plan = data.get('plan', 0)
        include_selected_workers = data.get('selected_workers', 0)
        include_maintenance_tools = data.get('maintenance_tools', 0)
        system_message = """你是一个化工智能调度项目的助手。项目背景如下：
        1. 这是一个化工设备维修调度系统，所有调度时间单位均为天
        2. 系统管理各种化工设备（反应釜、离心机、干燥机等）的维修工序
        3. 涉及设备类型、工序模板、工人调度、物料管理、维修器具调配
        4. 系统支持拓扑排序、贪心算法、遗传算法等多种调度算法
        5. 调度考虑工人技能、设备可用性、工序依赖关系

        你的任务是帮助用户解决与化工设备调度、维修安排、资源配置相关的问题。
        请以专业、准确的方式回答用户的疑问。"""
        # 调用DeepSeek API
        context_info = []
        if include_rules == 1:
            try:
                rules = AppDataManager.get_all_process_templates()
                if rules:
                    context_info.append("工序信息：")
                    context_info.append(json.dumps(rules, ensure_ascii=False, indent=2))
            except Exception as e:
                print(f"获取工序信息失败: {str(e)}")
        if include_plan == 1:
            try:
                db_path = get_db_path()
                conn = sqlite3.connect(str(db_path))
                c = conn.cursor()
                # 1. 获取所有调度任务
                c.execute('''
                        SELECT schedule_id,
                                process_id,
                                process_name,
                                equipment_id,
                                equipment_name,
                                start_time,
                                end_time,
                                workers,
                                predecessors
                        FROM schedule_tasks
                        ''')
                schedule_tasks = c.fetchall()
                context_info.append("调度方案：")
                context_info.append(json.dumps(schedule_tasks, ensure_ascii=False, indent=2))
            except Exception as e:
                print(f"获取调度方案失败: {str(e)}")
        if include_selected_workers == 1:
            selected_workers = AppDataManager.get_selected_workers()
            if selected_workers:
                context_info.append("工人信息：")
                context_info.append(json.dumps(selected_workers, ensure_ascii=False, indent=2))
        if include_maintenance_tools == 1:
            try:
                maintenance_tools = AppDataManager.get_maintenance_tools()
                if maintenance_tools:
                    context_info.append("维修器具：")
                    context_info.append(json.dumps(maintenance_tools, ensure_ascii=False, indent=2))
            except Exception as e:
                print(f"获取维修器具失败: {str(e)}")
        if context_info:
            system_message += "\n\n当前系统上下文:\n" + "\n".join(context_info)
        client = get_openai_client()
        response = client.chat.completions.create(
            model="qwen-flash",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
        )
        # 提取回复内容
        reply = response.choices[0].message.content
        # 返回结果给前端
        return jsonify({
            'success': True,
            'reply': reply,
            'usage': {
                'total_tokens': response.usage.total_tokens,
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens
            } if response.usage else None
        })
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Chat API Error: {str(e)}")
        print(f"Error Details: {error_details}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '聊天功能出错',
            'error_details': error_details  # 开发环境下可返回，生产环境应移除
        }), 500
