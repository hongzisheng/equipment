"""用户注册与登录认证路由

从原 app.py 抽取。密钥与过期时间统一由 app.config.Config 提供。
"""
import datetime
import sqlite3

import jwt
from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash

from app.config import Config
from app.utils import get_db_path, get_db_connection

auth_bp = Blueprint('auth', __name__, url_prefix='/api')


@auth_bp.route('/register', methods=['POST'])
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


@auth_bp.route('/login', methods=['POST'])
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
        exp_seconds = Config.JWT_ACCESS_TOKEN_EXPIRES
        token_payload = {
            'user_id': user[0],
            'username': user[1],
            'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=exp_seconds)
        }
        token = jwt.encode(token_payload, Config.JWT_SECRET_KEY, algorithm='HS256')
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
