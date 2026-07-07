import datetime
import os
import sqlite3

import jwt
import requests
from flask import Blueprint, request, jsonify

from app.utils.auth import token_required
from app.utils import get_db_connection

wx_blueprint = Blueprint('wx', __name__, url_prefix='/api/wx')


@wx_blueprint.route('/wxLogin', methods=['POST'])
def wx_login():
    try:
        data = request.get_json()
        code = data.get('code')

        if not code:
            return jsonify({
                'success': False,
                'message': '缺少微信登录 code'
            }), 500

        appid = os.getenv('WX_APP_ID')
        secret = os.getenv('WX_APP_SECRET')

        if not appid or not secret:
            return jsonify({
                'success': False,
                'message': '服务器未配置微信 APP ID 或 APP SECRET'
            }), 500

        # 调用微信接口
        wx_url = 'https://api.weixin.qq.com/sns/jscode2session'
        params = {
            'appid': appid,
            'secret': secret,
            'js_code': code,
            'grant_type': 'authorization_code'
        }

        wx_resp = requests.get(wx_url, params=params, timeout=10)
        wx_data = wx_resp.json()

        if 'errcode' in wx_data and wx_data['errcode'] != 0:
            # 微信返回错误（如 code 无效、频率限制等）
            err_msg = wx_data.get('errmsg', '未知错误')
            return jsonify({
                'success': False,
                'message': f'微信登录失败: {err_msg}',
                'wx_errcode': wx_data['errcode']
            }), 200

        openid = wx_data.get('openid')
        if not openid:
            return jsonify({
                'success': False,
                'message': '未能从微信获取 openid'
            }), 500

        # 查询 user_wx 表
        conn = get_db_connection()
        c = conn.cursor()

        c.execute('''
                  SELECT user_id
                  FROM user_wx
                  WHERE wx_openid = ?
                  ''', (openid,))
        result = c.fetchone()

        if not result:
            conn.close()
            return jsonify({
                'success': False,
                'message': '该微信账号未绑定系统用户，请先注册或绑定'
            }), 200

        user_id = result[0]

        # 查询 users 表获取完整用户信息
        c.execute('''
                  SELECT id, username, email, role, phone, company_id, real_name
                  FROM users
                  WHERE id = ?
                  ''', (user_id,))
        user = c.fetchone()
        conn.close()

        if not user:
            return jsonify({
                'success': False,
                'message': '关联的用户信息不存在'
            }), 200

        # 生成 JWT token（注意：这里不验证密码，因为是免密登录）
        # 生成JWT token
        exp_seconds = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', '3600'))
        token_payload = {
            'user_id': user[0],
            'username': user[1],
            'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=exp_seconds)
        }
        token = jwt.encode(token_payload, os.getenv('JWT_SECRET_KEY'), algorithm='HS256')

        return jsonify({
            'success': True,
            'message': '微信登录成功',
            'token': token,
            'user': {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'role': user[3],
                'phone': user[4],
                'company_id': user[5],
                'real_name': user[6]
            }
        })

    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'message': '请求微信服务器失败',
            'error': str(e)
        }), 502

    except sqlite3.Error as e:
        return jsonify({
            'success': False,
            'message': '数据库查询错误',
            'error': str(e)
        }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'message': '微信登录过程中发生未知错误',
            'error': str(e)
        }), 500


@wx_blueprint.route('/bind', methods=['POST'])
@token_required
def wx_bind():
    """
    微信绑定
    """
    try:
        data = request.get_json() or {}
        code = data.get('code')

        # 建议优先使用 token 注入的当前用户，避免越权绑定
        current_user_id = getattr(request, 'current_user_id', None)
        body_user_id = data.get('user_id')
        user_id = current_user_id or body_user_id

        if not user_id:
            return jsonify({
                'success': False,
                'message': '缺少用户信息，请先登录'
            }), 401

        # 若前端传了 user_id，校验和 token 一致，防止绑定到他人账号
        if current_user_id and body_user_id and int(body_user_id) != int(current_user_id):
            return jsonify({
                'success': False,
                'message': 'user_id 与当前登录用户不一致'
            }), 403

        if not code:
            return jsonify({
                'success': False,
                'message': '缺少微信 code'
            }), 400

        appid = os.getenv('WX_APP_ID')
        secret = os.getenv('WX_APP_SECRET')
        if not appid or not secret:
            return jsonify({
                'success': False,
                'message': '服务器未配置微信 APP ID 或 APP SECRET'
            }), 500

        # 1) 通过 code 换 openid
        wx_url = 'https://api.weixin.qq.com/sns/jscode2session'
        params = {
            'appid': appid,
            'secret': secret,
            'js_code': code,
            'grant_type': 'authorization_code'
        }

        wx_resp = requests.get(wx_url, params=params, timeout=10)
        wx_data = wx_resp.json()

        if 'errcode' in wx_data and wx_data['errcode'] != 0:
            return jsonify({
                'success': False,
                'message': f"微信换取 openid 失败: {wx_data.get('errmsg', '未知错误')}",
                'wx_errcode': wx_data['errcode']
            }), 200

        openid = wx_data.get('openid')
        if not openid:
            return jsonify({
                'success': False,
                'message': '未能从微信获取 openid'
            }), 500

        conn = get_db_connection()
        c = conn.cursor()

        # 2) 检查该用户是否已绑定（业务上通常一人只绑定一个微信）
        c.execute('SELECT id, wx_openid FROM user_wx WHERE user_id = ?', (user_id,))
        user_bind = c.fetchone()
        if user_bind:
            # 已经绑定同一个 openid，则视为幂等成功
            if user_bind[1] == openid:
                conn.close()
                return jsonify({
                    'success': True,
                    'message': '该账号已绑定当前微信，无需重复绑定',
                    'user_id': int(user_id),
                    'wx_openid': openid
                }), 200

            conn.close()
            return jsonify({
                'success': False,
                'message': '该用户已绑定其他微信账号，请先解绑后再绑定'
            }), 409

        # 3) 检查 openid 是否已被其他用户绑定（表里 wx_openid 是 unique）
        c.execute('SELECT user_id FROM user_wx WHERE wx_openid = ?', (openid,))
        openid_bind = c.fetchone()
        if openid_bind:
            conn.close()
            return jsonify({
                'success': False,
                'message': '该微信已绑定其他系统账号'
            }), 409

        # 4) 插入绑定关系
        c.execute('''
                  INSERT INTO user_wx (wx_openid, user_id)
                  VALUES (?, ?)
                  ''', (openid, user_id))
        conn.commit()
        bind_id = c.lastrowid
        conn.close()

        return jsonify({
            'success': True,
            'message': '微信绑定成功',
            'data': {
                'id': bind_id,
                'user_id': int(user_id),
                'wx_openid': openid
            }
        }), 200

    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'message': '请求微信服务器失败',
            'error': str(e)
        }), 502

    except sqlite3.IntegrityError as e:
        return jsonify({
            'success': False,
            'message': '绑定失败，数据约束冲突',
            'error': str(e)
        }), 409

    except sqlite3.Error as e:
        return jsonify({
            'success': False,
            'message': '数据库错误',
            'error': str(e)
        }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'message': '微信绑定过程中发生未知错误',
            'error': str(e)
        }), 500
