import datetime
import json
import os
import sqlite3
import traceback
from json import JSONDecodeError
from pathlib import Path
import jwt
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask import send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import core
import models
from jwt_decorated import token_required
from utils import get_db_path, get_db_connection
load_dotenv()
from openai import OpenAI
from wx_router import wx_blueprint
from equipment_router import equipment_bp
from worker_router import worker_bp
from maintenance_router import maintenance_bp
from materials_router import materials_bp
from process_router import process_bp
from panel_router import panel_bp
from parse_router import parse_blueprint
from file_router import file_bp     
app = Flask(__name__)
CORS(app)  # 允许跨域请求
app.register_blueprint(equipment_bp)
app.register_blueprint(worker_bp)
app.register_blueprint(maintenance_bp)
app.register_blueprint(materials_bp)
app.register_blueprint(wx_blueprint)
app.register_blueprint(process_bp)
app.register_blueprint(panel_bp)
app.register_blueprint(parse_blueprint)
app.register_blueprint(file_bp)
# ----------系统相关------------------
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')  # 生产环境请使用强密钥
# ----------智能问答------------------
client = OpenAI(
    api_key=os.environ.get('DASHSCOPE_API_KEY'),
    base_url=os.environ.get('DASHSCOPE_API_URL'),)
# ----------工单任务状态常量------------------#
TASK_STATUS = {
    'RELEASED': 'released',  # 待开始
    'APPLY_START': 'apply_for_start',  # 申请开工
    'ENG_APPROVED': 'eng_approved',  # 工程师确认
    'CONSTRUCTION_CONFIRMED': 'construction_confirmed',  # 施工确认
    'TEAM_RECEIVED': 'team_received',  # 班组受理
    'CONSTRUCTION_SIGNED': 'construction_signed',  # 施工回签
    'PROCESS_CLOSED': 'process_closed',  # 工艺存储关闭
    'EQUIPMENT_CLOSED': 'equipment_closed',  # 设备部关闭
    'CANCELLED': 'cancelled'  # 取消
}
# 状态转换权限映
# 格式: 当前状态 -> { 目标状态: [允许的角色列表] }
STATUS_TRANSITIONS = {
    TASK_STATUS['RELEASED']: {
        TASK_STATUS['APPLY_START']: ['worker']  # 工人可提交开工申请
    },
    TASK_STATUS['APPLY_START']: {
        TASK_STATUS['ENG_APPROVED']: ['admin']  # 工艺/储运工程师确认
    },
    TASK_STATUS['ENG_APPROVED']: {
        TASK_STATUS['CONSTRUCTION_CONFIRMED']: ['admin']  # 施工负责人确认
    },
    TASK_STATUS['CONSTRUCTION_CONFIRMED']: {
        TASK_STATUS['TEAM_RECEIVED']: ['admin']  # 班组长接收
    },
    TASK_STATUS['TEAM_RECEIVED']: {
        TASK_STATUS['CONSTRUCTION_SIGNED']: ['worker']  # 工人施工回签
    },
    TASK_STATUS['CONSTRUCTION_SIGNED']: {
        TASK_STATUS['PROCESS_CLOSED']: ['admin']  # 工艺工程师关闭
    },
    TASK_STATUS['PROCESS_CLOSED']: {
        TASK_STATUS['EQUIPMENT_CLOSED']: ['admin']  # 设备部关闭
    }
}

# ===================== 新增：知识树相关API =====================
@app.route('/api/graph-relations-archive', methods=['GET'])
def get_graph_relations_archive():
    """获取所有图关系数据（包含实体名称）"""
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 查询关系数据并关联获取源和目标实体的名称
        cursor.execute('''
        SELECT 
            r.id,
            r.source_type,
            r.source_id,
            r.relation_type,
            r.target_type,
            r.target_id,
            json_extract(s.attributes, '$.名称') AS source_name,
            json_extract(t.attributes, '$.名称') AS target_name
        FROM graph_relations_archive r
        LEFT JOIN graph_nodes_archive s ON r.source_id = s.entity_id
        LEFT JOIN graph_nodes_archive t ON r.target_id = t.entity_id
        ORDER BY r.id
        ''')
        
        relations = []
        for row in cursor.fetchall():
            relations.append({
                'id': row['id'],
                'source_type': row['source_type'],
                'source_id': row['source_id'],
                'relation_type': row['relation_type'],
                'target_type': row['target_type'],
                'target_id': row['target_id'],
                'source_name': row['source_name'],
                'target_name': row['target_name']
            })
        
        conn.close()
        return jsonify({
            'success': True,
            'data': relations
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/equipment-categories', methods=['GET'])
def get_equipment_categories():
    """获取设备分类列表"""
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, name FROM equipment_category ORDER BY id')
        categories = []
        for row in cursor.fetchall():
            categories.append({
                'id': str(row['id']),
                'name': row['name']
            })
        
        conn.close()
        return jsonify({
            'success': True,
            'data': categories
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/equipment-types-with-category', methods=['GET'])
def get_equipment_types_with_category():
    """获取带分类的设备类型列表"""
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT et.id, et.name, ec.name as category
        FROM equipment_types et
        LEFT JOIN equipment_category ec ON et.category_id = ec.id
        ORDER BY ec.id, et.id
        ''')
        
        types = []
        for row in cursor.fetchall():
            types.append({
                'id': str(row['id']),
                'name': row['name'],
                'category': row['category'] or '未分类'
            })
        
        conn.close()
        return jsonify({
            'success': True,
            'data': types
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
# ===================== 知识树API结束 =====================

@app.route('/api/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        role = data.get('role')
        phone = data.get('phone')
        company_id = data.get('company_id')
        real_name = data.get('real_name')
        if not all([username, password, email, phone, real_name]):
            return jsonify({
                'success': False,
                'message': '用户名、密码、手机号和邮箱不能为空'
            }), 400
        # 连接到数据库
        conn = get_db_connection()
        c = conn.cursor()
        # 检查用户是否已存在
        c.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
        if c.fetchone():
            conn.close()
            return jsonify({
                'success': False,
                'message': '用户名或邮箱已存在'
            }), 400
        # 创建用户
        password_hash = generate_password_hash(password)
        c.execute('''
                  INSERT INTO users (username, password, email, created_time, role, phone, company_id, real_name)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                  ''', (username, password_hash, email, datetime.datetime.now(), role, phone, company_id, real_name))
        user_id = c.lastrowid
        conn.commit()
        conn.close()
        return jsonify({
            'success': True,
            'message': '注册成功',
            'user_id': user_id
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '注册失败'
        }), 500
@app.route('/api/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        if not username or not password:
            return jsonify({
                'success': False,
                'message': '用户名和密码不能为空'
            }), 400
        # 连接到数据库
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        # 查询用户
        c.execute('''
                  SELECT id,
                         username,
                         password,
                         email,
                         role,
                         phone,
                         company_id,
                         real_name,
                         emp_id
                  FROM users
                  WHERE username = ?
                     OR email = ?
                  ''', (username, username))
        user = c.fetchone()
        if not user or not check_password_hash(user[2], password):
            return jsonify({
                'success': False,
                'message': '用户名或密码错误'
            }), 401
        # 生成JWT token
        exp_seconds = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', '3600'))
        token_payload = {
            'user_id': user[0],
            'username': user[1],
            'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=exp_seconds)
        }
        token = jwt.encode(token_payload, os.getenv('JWT_SECRET_KEY'), algorithm='HS256')
        user_info = {
            'id': user[0],
            'username': user[1],
            'email': user[3],
            'role': user[4],
            'phone': user[5],
            'company_id': user[6],
            'real_name': user[7],
            'emp_id': user[8]  # 添加 emp_id
        }
        # 如果用户角色是工人，从 workers 表查询 worker_id
        worker_id = None
        if user[4] == 'worker':
            # 假设 workers 表有 emp_id 字段，且与 users.emp_id 对应
            c.execute('SELECT id FROM workers WHERE emp_id = ?', (user[8],))
            row = c.fetchone()
            if row:
                worker_id = row[0]
            else:
                # 可选：如果 workers 表没有对应记录，记录日志
                print(f"警告：用户 {username} (emp_id={user[8]}) 在 workers 表中无对应记录")
        user_info['worker_id'] = worker_id
        conn.close()
        return jsonify({
            'success': True,
            'message': '登录成功',
            'token': token,
            'user': user_info
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '登录失败'
        }), 500
@app.route('/api/chat', methods=['POST'])
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
class AppDataManager:
    """应用数据管理器，复用models.py中的接口"""
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
        current_dir = Path(__file__).parent
        db_path = current_dir.parent / 'database' / 'db.sqlite3'
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
# 全局调度器实例
# ----------调度相关------------------
scheduler = None
"""执行调度算法"""
@app.route('/api/run-scheduler', methods=['POST'])
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
            # 获取全局调度器实例（由 core.run_scheduling 内部创建并存储）
            global scheduler
            scheduler = core.get_scheduler()  # 假设 core 提供了此方法
            if scheduler:
                worker_pool_data = scheduler.get_worker_pool()
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
# 在 chat 函数内部：
scheduler = core.get_scheduler()
if scheduler:
    plan = scheduler.schedule_plan  # 或重新调度
# ----------工单相关------------------
"""添加工单"""
def generate_work_orders_from_selected():
    conn = None
    global scheduler
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        # 從selected_equipments表獲取選中的設備信息
        c.execute('''
                  SELECT se.id, ei.name, ei.equipment_type_id, et.name as equipment_type_name
                  FROM selected_equipments se
                           INNER JOIN equipment_instances ei ON se.id = ei.id
                           INNER JOIN equipment_types et ON ei.equipment_type_id = et.id
                  ''')
        selected_equipments = c.fetchall()
        if not selected_equipments:
            return {
                'success': False,
                'message': 'selected_equipments表中没有选中的设备',
                'generated_orders': [],
                'failed_orders': []
            }
        generated_orders = []
        failed_orders = []
        for equipment in selected_equipments:
            try:
                equipment_id = equipment[0]
                equipment_name = equipment[1]
                from datetime import datetime
                current_date = datetime.now().strftime('%Y%m%d')
                c.execute('''
                          SELECT COUNT(*)
                          FROM work_orders
                          WHERE order_number LIKE ?
                          ''', (f'WO-{current_date}-%',))
                order_count = c.fetchone()[0]
                order_number = f'WO-{current_date}-{str(order_count + 1).zfill(4)}'
                title = f'{equipment_name}維修'
                # 從調度計劃中查詢該設備的計劃開始和結束時間
                c.execute('''
                          SELECT MIN(start_time), MAX(end_time)
                          FROM schedule_tasks
                          WHERE equipment_id = ?
                          ''', (equipment_id,))
                schedule_result = c.fetchone()
                if schedule_result[0] is not None:
                    scheduled_start_abs = scheduler.get_absolute_time(schedule_result[0])
                    scheduled_end_abs = scheduler.get_absolute_time(schedule_result[1])
                else:
                    scheduled_start_abs = scheduled_end_abs = None
                # 插入到work_orders表
                c.execute('''
                          INSERT INTO work_orders
                          (order_number, title, equipment_id, equipment_name,
                           status, created_by, created_at, scheduled_start_time,
                           scheduled_end_time, priority)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                          ''', (
                              order_number,
                              title,
                              equipment_id,
                              equipment_name,
                              'pending',  # 默認狀態
                              'admin',  # 默認創建者
                              datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                              scheduled_start_abs,
                              scheduled_end_abs,
                              'medium'
                          ))
                work_order_id = c.lastrowid
                # 為這個工單生成相關的工序任務
                generated_orders.append({
                    'work_order_id': work_order_id,
                    'order_number': order_number,
                    'equipment_id': equipment_id,
                    'equipment_name': equipment_name,
                    'scheduled_start_time': scheduled_start_abs,
                    'scheduled_end_time': scheduled_end_abs
                })
            except Exception as e:
                failed_orders.append({
                    'equipment_id': equipment[0] if equipment else '未知',
                    'equipment_name': equipment[1] if equipment else '未知',
                    'error': str(e)
                })
                continue
        if generated_orders:
            conn.commit()
            return {
                'success': True,
                'message': f'成功生成 {len(generated_orders)} 个工单',
                'generated_orders': generated_orders,
                'failed_orders': failed_orders,
                'total_generated': len(generated_orders),
                'total_failed': len(failed_orders)
            }
        else:
            return {
                'success': False,
                'message': '没有成功生成任何工单',
                'generated_orders': [],
                'failed_orders': failed_orders,
                'total_failed': len(failed_orders)
            }
    except Exception as e:
        # 全局异常捕获，返回字典而不是响应对象
        return {
            'success': False,
            'message': '工单生成过程中发生严重错误',
            'error': str(e),
            'generated_orders': [],
            'failed_orders': []
        }
    finally:
        if conn:
            conn.close()
"""获取所有工单列表"""
@app.route('/api/work-orders', methods=['GET'])
def get_work_orders():
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row  # 使返回结果可用列名访问
        c = conn.cursor()
        # 查询所有工单，按创建时间倒序排列
        query = """
                SELECT id,
                       order_number,
                       title,
                       equipment_id,
                       equipment_name,
                       status,
                       created_by,
                       created_at,
                       scheduled_start_time,
                       scheduled_end_time,
                       priority
                FROM work_orders
                ORDER BY created_at DESC \
                """
        c.execute(query)
        rows = c.fetchall()
        # 转换为字典列表
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
        conn.close()
        return jsonify({
            'success': True,
            'data': work_orders
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '获取工单列表失败'
        }), 500
"""获取所有工单任务列表"""
@app.route('/api/work-order-tasks', methods=['GET'])
def get_work_order_tasks():
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        # 查询所有工单任务，按创建时间倒序排列
        query = """
                SELECT id,
                       work_order_id,
                       task_code,
                       process_id,
                       process_name,
                       equipment_id,
                       equipment_name,
                       description,
                       estimated_hours,
                       scheduled_start_time,
                       scheduled_end_time,
                       actual_start_time,
                       actual_end_time,
                       status,
                       predecessor_task_ids,
                       is_milestone,
                       workers,
                       approver_id,
                       approval_comments,
                       approved_at,
                       created_at,
                       updated_at,
                       attachment_path
                FROM work_order_tasks
                ORDER BY created_at DESC \
                """
        c.execute(query)
        rows = c.fetchall()
        # 转换为字典列表，并解析JSON字段
        tasks = []
        for row in rows:
            task = dict(row)  # sqlite3.Row 转 dict
            # 解析 JSON 字段
            for json_field in ['predecessor_task_ids', 'workers']:
                if task.get(json_field):
                    try:
                        task[json_field] = json.loads(task[json_field])
                    except (json.JSONDecodeError, TypeError):
                        # 如果解析失败，保留原字符串（但通常不应发生）
                        pass
                else:
                    # 空字符串或 NULL 返回空列表/字典
                    if json_field in ['predecessor_task_ids', 'workers']:
                        task[json_field] = []
                    else:
                        task[json_field] = None
            # 布尔字段 is_milestone 在 SQLite 中存为 0/1，转换为 bool
            task['is_milestone'] = bool(task['is_milestone'])
            tasks.append(task)
        conn.close()
        return jsonify({
            'success': True,
            'data': tasks
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '获取工单任务列表失败'
        }), 500
"""手动创建工单：选择设备实例和多个工序模板，校验前置依赖"""
@app.route('/api/manual-create-work-order', methods=['POST'])
@token_required
def manual_create_work_order():
    try:
        data = request.get_json()
        equipment_id = data.get('equipment_id')
        process_template_ids = data.get('process_template_ids')
        if not equipment_id or not process_template_ids or not isinstance(process_template_ids, list) or len(
                process_template_ids) == 0:
            return jsonify({'success': False, 'message': '设备ID和工序模板ID列表不能为空'}), 400
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        # 1. 获取设备信息
        c.execute('SELECT id, name, equipment_type_id FROM equipment_instances WHERE id = ?', (equipment_id,))
        eq = c.fetchone()
        if not eq:
            conn.close()
            return jsonify({'success': False, 'message': '设备不存在'}), 404
        equipment_type_id = eq[2]
        # 2. 获取所有工序模板信息（包括前置工序）
        placeholders = ','.join('?' for _ in process_template_ids)
        c.execute(f'''
            SELECT id, process_code, description, estimated_hours, required_workers,
                   worker_price, material_requirements, tools_requirements, predecessor_codes
            FROM process_templates WHERE id IN ({placeholders})
        ''', process_template_ids)
        templates = c.fetchall()
        if len(templates) != len(process_template_ids):
            found_ids = {t[0] for t in templates}
            missing = set(process_template_ids) - found_ids
            conn.close()
            return jsonify({'success': False, 'message': f'工序模板不存在: {missing}'}), 400
        # 3. 构建工序信息映射
        process_map = {}
        for tmpl in templates:
            tmpl_id = tmpl[0]
            process_code = tmpl[1]
            description = tmpl[2]
            estimated_hours = tmpl[3]
            required_workers = json.loads(tmpl[4]) if tmpl[4] else {}
            worker_price = tmpl[5]
            material_req = tmpl[6]
            tools_req = tmpl[7]
            predecessor_codes = json.loads(tmpl[8]) if tmpl[8] else []
            process_map[tmpl_id] = {
                'id': tmpl_id,
                'code': process_code,
                'description': description,
                'estimated_hours': estimated_hours,
                'required_workers': required_workers,
                'worker_price': worker_price,
                'material_req': material_req,
                'tools_req': tools_req,
                'predecessor_codes': predecessor_codes
            }
        # 4. 校验前置依赖
        code_to_id = {proc['code']: proc['id'] for proc in process_map.values()}
        selected_codes = set(code_to_id.keys())
        missing_predecessors = []
        for proc_id, proc in process_map.items():
            for pred_code in proc['predecessor_codes']:
                if pred_code not in selected_codes:
                    missing_predecessors.append({
                        'process': proc['code'],
                        'missing_predecessor': pred_code
                    })
        if missing_predecessors:
            conn.close()
            return jsonify({
                'success': False,
                'message': '工序前置依赖不满足',
                'details': missing_predecessors
            }), 400
        # 5. 生成工单编号
        current_date = datetime.datetime.now().strftime('%Y%m%d')
        c.execute("SELECT COUNT(*) FROM work_orders WHERE order_number LIKE ?", (f'WO-{current_date}-%',))
        order_count = c.fetchone()[0]
        order_number = f'WO-{current_date}-{str(order_count + 1).zfill(4)}'
        # 6. 插入工单（计划时间置空）
        c.execute('''
                  INSERT INTO work_orders
                  (order_number, title, equipment_id, equipment_name, status, created_by, created_at,
                   scheduled_start_time, scheduled_end_time, priority)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                  ''', (
                      order_number,
                      f'{eq[1]} - 多工序工单',
                      equipment_id,
                      eq[1],
                      'pending',
                      request.current_user_id,
                      datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                      None,  # 计划开始时间置空
                      None,  # 计划结束时间置空
                      'medium'
                  ))
        work_order_id = c.lastrowid
        # 7. 为每个工序创建任务
        task_ids = []
        task_map = {}  # process_code -> task_id
        for proc_id, proc in process_map.items():
            task_code = f'TSK-{work_order_id}-{proc["code"]}'
            is_milestone = 1 if proc['code'].startswith('M') else 0
            c.execute('''
                      INSERT INTO work_order_tasks
                      (work_order_id, task_code, process_id, process_code, process_name, equipment_id, equipment_name,
                       estimated_hours, scheduled_start_time, scheduled_end_time,
                       status, created_at, is_milestone)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                      ''', (
                          work_order_id,
                          task_code,
                          proc['id'],
                          proc['code'],
                          proc['description'],
                          equipment_id,
                          eq[1],
                          proc['estimated_hours'],
                          None,  # 计划开始时间置空
                          None,  # 计划结束时间置空
                          'released',
                          datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                          is_milestone
                      ))
            task_id = c.lastrowid
            task_ids.append(task_id)
            task_map[proc['code']] = task_id
        for proc_id, proc in process_map.items():
            pred_codes = proc.get('predecessor_codes', [])
            if pred_codes:
                pred_task_ids = [task_map[code] for code in pred_codes if code in task_map]
                pred_task_ids_json = json.dumps(pred_task_ids)
            else:
                pred_task_ids_json = json.dumps([])  # 显式设为空数组
            c.execute('''
                      UPDATE work_order_tasks
                      SET predecessor_task_ids = ?
                      WHERE work_order_id = ?
                        AND process_id = ?
                      ''', (pred_task_ids_json, work_order_id, proc['code']))
        conn.commit()
        conn.close()
        return jsonify({
            'success': True,
            'message': f'工单及{len(task_ids)}个任务创建成功',
            'work_order_id': work_order_id,
            'order_number': order_number,
            'task_ids': task_ids
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e), 'message': '创建工单失败'}), 500
"""工人与工单关联"""
@app.route('/api/assign-workers-from-schedule', methods=['POST'])
@token_required
def assign_workers_from_schedule():
    conn = None
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
        if not schedule_tasks:
            return jsonify({'success': False, 'message': 'schedule_tasks 表中无调度数据，请先运行调度算法'}), 400
        assigned_count = 0
        errors = []
        # 2. 遍历调度任务，匹配 work_order_tasks
        for st in schedule_tasks:
            schedule_id = st[0]
            process_id_raw = st[1]  # 例如 "1_CLEAN"
            equipment_id = st[3]
            workers_raw = st[7]  # JSON 字符串，格式如 {"1": ["张三"], "2": ["李四"]}
            workers_dict = {}
            print(workers_raw)
            if workers_raw is None:
                workers_dict = {}
            elif isinstance(workers_raw, dict):
                workers_dict = workers_raw
            elif isinstance(workers_raw, str):
                try:
                    workers_dict = json.loads(workers_raw)
                    if not isinstance(workers_dict, dict):
                        workers_dict = {}
                except json.JSONDecodeError:
                    workers_dict = {}
            else:
                # 其他类型，记录错误
                errors.append(f"调度任务 {schedule_id} 的 workers 字段类型异常: {type(workers_raw)}")
                continue
            if not workers_dict:
                errors.append(f"调度任务 {schedule_id} 没有有效的工人分配信息")
                continue
            # 从 process_id_raw 中提取工序代码（下划线后面的部分）
            if '_' in process_id_raw:
                process_id = process_id_raw.split('_', 1)[1]
            else:
                process_id = process_id_raw  # 如果没有下划线，则整个作为代码
            c.execute('''
                      SELECT id, status
                      FROM work_order_tasks
                      WHERE equipment_id = ?
                        AND process_id = ?
                        AND status NOT IN ('equipment_closed', 'cancelled')
                      ''', (equipment_id, process_id))
            task_row = c.fetchone()
            if not task_row:
                errors.append(f"未找到匹配的任务: equipment_id={equipment_id}, process_id={process_id}")
                continue
            task_id = task_row[0]
            task_status = task_row[1]
            if task_status in ['equipment_closed', 'cancelled']:
                errors.append(f"任务 {task_id} 已关闭或取消，跳过分配")
                continue
            # 4. 分配工人到 work_order_tasks
            c.execute('DELETE FROM work_order_task_workers WHERE task_id = ?', (task_id,))
            inserted = 0
            for worker_type, worker_names in workers_dict.items():
                # worker_names 可以是列表或字符串
                if isinstance(worker_names, str):
                    worker_names = [worker_names]
                for worker_name in worker_names:
                    # 根据姓名和工种查询工人 ID
                    c.execute('SELECT id FROM workers WHERE name = ? AND worker_type_id = ?',
                              (worker_name, worker_type))
                    worker_row = c.fetchone()
                    if worker_row:
                        worker_id = worker_row[0]
                        c.execute('''
                                  INSERT INTO work_order_task_workers (task_id, worker_id, worker_name, worker_type, status)
                                  VALUES (?, ?, ?, ?, 'assigned')
                                  ''', (task_id, worker_id, worker_name, worker_type))
                        inserted += 1
                    else:
                        errors.append(f"未找到工人: {worker_name}（工种 {worker_type}）")
            if inserted > 0:
                assigned_count += 1
        conn.commit()
        return jsonify({
            'success': True,
            'message': f'工人分配完成，成功处理 {assigned_count} 个任务',
            'assigned_count': assigned_count,
            'errors': errors[:20]  # 限制返回的错误数量
        })
    except Exception as e:
        if conn:
            conn.rollback()
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e), 'message': '工人分配失败'}), 500
    finally:
        if conn:
            conn.close()
"""获取工人工单信息"""
@app.route('/api/worker-workorders/<int:worker_id>', methods=['GET'])
def get_worker_workorders(worker_id):
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        # 查询该工人参与的所有任务，并关联工单信息
        query = """
                SELECT t.id          as task_id,
                       t.task_code,
                       t.process_id,
                       t.process_name,
                       t.equipment_id,
                       t.equipment_name,
                       t.description,
                       t.estimated_hours,
                       t.scheduled_start_time,
                       t.scheduled_end_time,
                       t.actual_start_time,
                       t.actual_end_time,
                       t.status      as task_status,
                       t.is_milestone,
                       wo.id         as work_order_id,
                       wo.order_number,
                       wo.title      as work_order_title,
                       wo.status     as work_order_status,
                       wo.priority,
                       wo.created_at as work_order_created_at,
                       wt.worker_name,
                       wt.worker_type,
                       wt.status     as assignment_status
                FROM work_order_task_workers wt
                         JOIN work_order_tasks t ON wt.task_id = t.id
                         LEFT JOIN work_orders wo ON t.work_order_id = wo.id
                WHERE wt.worker_id = ?
                ORDER BY t.scheduled_start_time DESC \
                """
        c.execute(query, (worker_id,))
        rows = c.fetchall()
        tasks = []
        for row in rows:
            task = dict(row)
            # 转换 JSON 字段
            for json_field in ['predecessor_task_ids', 'workers']:
                if task.get(json_field):
                    try:
                        task[json_field] = json.loads(task[json_field])
                    except:
                        pass
            # 布尔字段转换
            task['is_milestone'] = bool(task['is_milestone'])
            tasks.append(task)
        conn.close()
        return jsonify({
            'success': True,
            'worker_id': worker_id,
            'data': tasks
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '获取工人工单失败'
        }), 500
"""更新工单任务状态并上传附件（工人）"""
@app.route('/api/work-order-tasks/<int:task_id>/update-status', methods=['PUT', 'POST'])
@token_required  # 需要登录，但所有认证用户（工人）都可访问
def update_work_order_task_status(task_id):
    state_order = [
        TASK_STATUS['RELEASED'],
        TASK_STATUS['APPLY_START'],
        TASK_STATUS['ENG_APPROVED'],
        TASK_STATUS['CONSTRUCTION_CONFIRMED'],
        TASK_STATUS['TEAM_RECEIVED'],
        TASK_STATUS['CONSTRUCTION_SIGNED'],
        TASK_STATUS['PROCESS_CLOSED'],
        TASK_STATUS['EQUIPMENT_CLOSED'],
        TASK_STATUS['CANCELLED']
    ]
    try:
        # 1. 获取当前用户（工人）信息
        current_user_id = request.current_user_id
        current_user_role = request.current_user_role
        if request.files:
            # 文件上传场景：从 form 中获取字段
            new_status = request.form.get('status')
            description = request.form.get('description', '')
            action = request.form.get('action')  # 管理员专用：confirm / reject
            approval_comments = request.form.get('approval_comments', '')
        else:
            # JSON 场景
            data = request.get_json(silent=True) or {}
            new_status = data.get('status')
            description = data.get('description', '')
            action = data.get('action')
            approval_comments = data.get('approval_comments', '')
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        c.execute('SELECT status, attachment_path FROM work_order_tasks WHERE id = ?', (task_id,))
        old_status, old_attach = c.fetchone()
        # 2. 检查任务是否存在
        c.execute('SELECT id, status FROM work_order_tasks WHERE id = ?', (task_id,))
        task = c.fetchone()
        if not task:
            conn.close()
            return jsonify({
                'success': False,
                'message': '指定的工单任务不存在'
            }), 404
        current_status = task[1]
        # 终态不可再变更
        if current_status in [TASK_STATUS['EQUIPMENT_CLOSED'], TASK_STATUS['CANCELLED']]:
            conn.close()
            return jsonify({'success': False, 'message': '任务已关闭，不可修改'}), 400
        # 3. 获取并验证请求数据
        # 支持表单数据（用于文件上传）和JSON数据
        target_status = None
        if current_user_role == 'worker':
            # 自动计算工人下一步
            transitions = STATUS_TRANSITIONS.get(current_status, {})
            worker_next = [st for st, roles in transitions.items() if 'worker' in roles]
            if len(worker_next) == 0:
                conn.close()
                return jsonify({'success': False, 'message': '当前状态下工人无法执行下一步'}), 400
            elif len(worker_next) > 1:
                conn.close()
                return jsonify({'success': False, 'message': '存在多个可能的下一步，请明确指定'}), 400
            target_status = worker_next[0]
        elif current_user_role == 'admin':
            # ----- 管理员操作：必须提供 action -----
            if not action or action not in ['confirm', 'reject']:
                conn.close()
                return jsonify(
                    {'success': False, 'message': '管理员必须提供 action 参数，且值为 confirm 或 reject'}), 400
            if action == 'confirm':
                # 自动计算管理员下一步
                transitions = STATUS_TRANSITIONS.get(current_status, {})
                admin_next = [st for st, roles in transitions.items() if 'admin' in roles]
                if len(admin_next) == 0:
                    conn.close()
                    return jsonify({'success': False, 'message': '当前状态下管理员无法确认下一步'}), 400
                elif len(admin_next) > 1:
                    conn.close()
                    return jsonify({'success': False, 'message': '存在多个可能的下一步，请明确指定'}), 400
                target_status = admin_next[0]
            else:
                try:
                    current_idx = state_order.index(current_status)
                except ValueError:
                    conn.close()
                    return jsonify({'success': False, 'message': f'未知的当前状态：{current_status}'}), 400
                if current_idx == 0:
                    conn.close()
                    return jsonify({'success': False, 'message': '已是第一个状态，无法驳回'}), 400
                target_status = state_order[current_idx - 1]
        else:
            conn.close()
            return jsonify({'success': False, 'message': f'未知角色：{current_user_role}'}), 403
        # 5. 处理文件上传（照片附件）
        attachment_path = None
        if 'photo' in request.files:
            photo_file = request.files['photo']
            if photo_file and photo_file.filename:
                # 简单的文件类型检查（可根据需要扩展）
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
                if '.' in photo_file.filename and photo_file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                    # 生成安全的文件名并保存
                    from werkzeug.utils import secure_filename
                    filename = secure_filename(photo_file.filename)
                    # 创建按任务ID组织的目录
                    upload_dir = Path(__file__).parent / 'uploads' / 'work_order_photos' / str(task_id)
                    upload_dir.mkdir(parents=True, exist_ok=True)
                    # 生成唯一文件名，避免覆盖
                    unique_filename = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                    file_path = upload_dir / unique_filename
                    photo_file.save(str(file_path))
                    # 存储相对路径，便于前端访问或后续提供下载服务
                    attachment_path = f"/uploads/work_order_photos/{task_id}/{unique_filename}"
                else:
                    conn.close()
                    return jsonify({
                        'success': False,
                        'message': '不支持的文件格式，仅允许图片文件 (png, jpg, jpeg, gif, bmp)'
                    }), 400
        # 6. 更新数据库记录
        update_fields = []
        update_values = []
        update_fields.append('status = ?')
        update_values.append(target_status)
        if description:
            # 可以更新description，或在历史记录中记录。这里选择更新description字段。
            # 更完善的方案是添加一个状态变更历史表。
            update_fields.append('description = ?')
            update_values.append(description)
        if attachment_path:
            update_fields.append('attachment_path = ?')
            update_values.append(attachment_path)
        # 记录实际开始/结束时间（根据业务逻辑调整）
        if target_status == TASK_STATUS['APPLY_START']:  # 工人申请开工 -> 记录实际开始时间
            c.execute('SELECT actual_start_time FROM work_order_tasks WHERE id = ?', (task_id,))
            if c.fetchone()[0] is None:
                update_fields.append('actual_start_time = ?')
                update_values.append(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        elif target_status == TASK_STATUS['EQUIPMENT_CLOSED']:  # 最终关闭 -> 记录实际结束时间
            update_fields.append('actual_end_time = ?')
            update_values.append(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        # 审批信息（仅管理员驳回时记录）
        if current_user_role == 'admin' and action == 'reject':
            update_fields.append('approver_id = ?')
            update_values.append(current_user_id)
            update_fields.append('approval_comments = ?')
            update_values.append(approval_comments)
            update_fields.append('approved_at = CURRENT_TIMESTAMP')
        # 更新时间戳
        update_fields.append('updated_at = CURRENT_TIMESTAMP')
        # 执行更新
        update_values.append(task_id)
        update_query = f'UPDATE work_order_tasks SET {", ".join(update_fields)} WHERE id = ?'
        c.execute(update_query, update_values)
        log_data = {
            'task_id': task_id,
            'user_id': current_user_id,
            'operation_type': 'status_update',
            'description': description or '',
            'attachment_path': attachment_path,
            'old_status': old_status,
            'new_status': target_status,
            'approval_comments': None
        }
        # 如果是驳回操作，设置 operation_type 为 approval_reject
        if action == 'reject':
            log_data['operation_type'] = 'approval_reject'
            log_data['approval_comments'] = approval_comments
        elif action == 'confirm':
            log_data['operation_type'] = 'approval_confirm'
        elif attachment_path:
            # 如果有附件上传，可细化操作类型
            log_data['operation_type'] = 'upload_photo'
        c.execute('''
                  INSERT INTO task_operation_logs
                  (task_id, user_id, operation_type, description, attachment_path, old_status, new_status,
                   approval_comments, created_at)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                  ''', (
                      log_data['task_id'], log_data['user_id'], log_data['operation_type'],
                      log_data['description'], log_data['attachment_path'],
                      log_data['old_status'], log_data['new_status'], log_data['approval_comments']
                  ))
        conn.commit()
        conn.close()
        # 8. 返回成功
        response_data = {
            'success': True,
            'message': '工单任务状态更新成功',
            'task_id': task_id,
            'new_status': target_status
        }
        if attachment_path:
            response_data['attachment_path'] = attachment_path
        return jsonify(response_data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e), 'message': '更新工单任务状态失败'}), 500
@app.route('/api/worker/<int:worker_id>/history', methods=['GET'])
@token_required
def get_worker_history(worker_id):
    """获取指定工人的所有操作历史（按时间倒序）"""
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        query = '''
                SELECT l.id,
                       l.task_id,
                       t.process_name as task_name,
                       l.operation_type,
                       l.description,
                       l.attachment_path,
                       l.old_status,
                       l.new_status,
                       l.approval_comments,
                       l.created_at,
                       u.real_name    as operator_name
                FROM task_operation_logs l
                         JOIN work_order_tasks t ON l.task_id = t.id
                         JOIN work_order_task_workers w ON t.id = w.task_id
                         LEFT JOIN users u ON l.user_id = u.id
                WHERE w.worker_id = ?
                ORDER BY l.created_at DESC \
                '''
        c.execute(query, (worker_id,))
        rows = c.fetchall()
        history = [dict(row) for row in rows]
        conn.close()
        return jsonify({'success': True, 'data': history})
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '获取工人历史失败'
        }), 500
# ----------工单任务审批（管理层）------------------
"""审批工单任务（管理层）"""
@app.route('/api/work-order-tasks/<int:task_id>/approve', methods=['PUT'])
@token_required  # 需要登录
def approve_work_order_task(task_id):
    try:
        # 获取当前用户（审批人）信息
        current_user_id = request.current_user_id
        # 检查当前用户角色是否为“管理员”或“经理”等管理层角色
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        c.execute('SELECT role FROM users WHERE id = ?', (current_user_id,))
        user_role = c.fetchone()
        if user_role and user_role[0] not in ['admin', 'manager']:
            return jsonify({'success': False, 'message': '权限不足，仅管理层可审批'}), 403
        # 获取请求数据（审批意见和结果）
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求体不能为空'
            }), 400
        approval_result = data.get('approval_result')  # 例如: 'approved', 'rejected'
        approval_comments = data.get('approval_comments', '')
        if not approval_result or approval_result not in ['approved', 'rejected']:
            return jsonify({
                'success': False,
                'message': '审批结果（approval_result）为必填项，且必须为 "approved" 或 "rejected"'
            }), 400
        # 检查任务是否存在并获取当前状态
        c.execute('SELECT id, status FROM work_order_tasks WHERE id = ?', (task_id,))
        task = c.fetchone()
        if not task:
            conn.close()
            return jsonify({
                'success': False,
                'message': '指定的工单任务不存在'
            }), 404
        current_status = task[1]
        if current_status != 'completed':
            return jsonify({'success': False, 'message': '只有已完成的任务可提交审批'}), 400
        # 更新数据库记录
        new_status = 'approved' if approval_result == 'approved' else 'rejected'
        c.execute('''
                  UPDATE work_order_tasks
                  SET status            = ?,
                      approver_id       = ?,
                      approval_comments = ?,
                      approved_at       = CURRENT_TIMESTAMP,
                      updated_at        = CURRENT_TIMESTAMP
                  WHERE id = ?
                  ''', (new_status, current_user_id, approval_comments, task_id))
        conn.commit()
        conn.close()
        return jsonify({
            'success': True,
            'message': f'工单任务审批完成，结果：{new_status}',
            'task_id': task_id,
            'approval_result': approval_result,
            'approver_id': current_user_id,
            'approval_comments': approval_comments
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '工单任务审批失败'
        }), 500
# ----------获取工单任务附件（管理层/工人查看）------------------
"""获取工单任务的附件信息（例如照片路径）"""
@app.route('/api/work-order-tasks/<int:task_id>/attachments', methods=['GET'])
@token_required
def get_task_attachments(task_id):
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        c.execute('SELECT attachment_path FROM work_order_tasks WHERE id = ?', (task_id,))
        result = c.fetchone()
        conn.close()
        if not result:
            return jsonify({'success': False, 'message': '工单任务不存在'}), 404
        attachment_path = result[0]
        # 这里返回附件路径。前端可以根据此路径向另一个专门的文件服务端点请求文件，或者直接使用静态文件服务。
        # 例如，如果配置了Flask的静态文件服务，路径可能是 `/static/uploads/work_order_photos/...`
        # 以下返回假设您的Flapp配置了静态文件夹服务于 `uploads` 目录。
        attachment_url = f"/static{attachment_path}" if attachment_path else None
        return jsonify({
            'success': True,
            'task_id': task_id,
            'attachment_path': attachment_path,
            'attachment_url': attachment_url  # 提供给前端的可访问URL
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '获取附件信息失败'
        }), 500
@app.route('/api/work-order-tasks/<int:task_id>/suggestions', methods=['GET'])
@token_required
def get_task_suggestions(task_id):
    """
    获取这个task的建议
    :param task_id:
    :return:
    """
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        c.execute('SELECT worker_type FROM work_order_task_workers WHERE task_id = ?', (task_id,))
        result = c.fetchone()
        if not result:
            return jsonify({'success': False, 'message': '工单任务不存在'}), 404
        worker_type = result[0]
        c.execute('SELECT process_name FROM work_order_tasks WHERE id = ?', (task_id,))
        result = c.fetchone()
        if not result:
            return jsonify({'success': False, 'message': '工单任务不存在'}), 404
        process_name = result[0]
        conn.close()
        # 组装提示词
        prompt = """
        你是化工设备维修专家。请仅输出 JSON 对象，不要输出任何解释文字。
        要求：
        1) 顶层只有两个字段："materials"、"guide"
        2) 两个字段值都必须是字符串（markdown 文本）
        3) JSON 必须合法：键和字符串都用双引号
        4) 如果内容里需要反斜杠，必须写成 \\\\
        
        示例：
        {
          "materials": "- 材料A\\n- 材料B",
          "guide": "1. 步骤一\\n2. 步骤二\\n\\n\\n**注意事项**：..."
        }
        
        """
        response = client.chat.completions.create(
            model="qwen-flash",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"工人身份: {worker_type}, 任务内容: {process_name}"}
            ],
            stream=False,
            extra_body={"enable_search": True},
            response_format={
                'type': 'json_object'
            }
        )
        raw = response.choices[0].message.content.strip()
        # 兼容模型偶尔包一层 markdown 代码块
        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.lower().startswith("json"):
                raw = raw[4:].strip()
        try:
            output = json.loads(raw)
        except JSONDecodeError as e:
            return jsonify({
                "success": False,
                "message": "模型返回的 JSON 非法",
                "error": str(e),
                "raw": raw
            }), 500
        return jsonify({
            'success': True,
            'task_id': task_id,
            'output': output
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '获取失败'
        }), 500
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    # 安全地构建上传文件夹的绝对路径
    upload_folder = Path(__file__).parent / 'uploads'
    return send_from_directory(str(upload_folder), filename)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)