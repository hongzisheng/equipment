import os
from functools import wraps

import jwt
from flask import request, jsonify

from utils import get_db_connection

JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')

def token_required(f):
    """JWT认证装饰器"""
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

            # 查询用户角色
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT role FROM users WHERE id = ?', (current_user_id,))
            user_row = c.fetchone()
            conn.close()

            if not user_row:
                return jsonify({'success': False, 'message': '用户不存在'}), 401

            request.current_user_id = current_user_id
            request.current_user_role = user_row[0]  # 注入角色

        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'message': 'Token已过期'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'message': '无效Token'}), 401

        return f(*args, **kwargs)

    return decorated