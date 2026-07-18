"""用户认证蓝图

提供登录、获取用户信息、注销功能。
认证方式：查询数据库 users 表，使用 bcrypt 验证密码。
Token 使用 UUID 存储于内存字典（服务重启后需重新登录）。
"""

import sqlite3
import uuid

from flask import Blueprint, request

from app.models import Result
from app.utils.db import get_db_connection
from app.utils.password_utils import check_password

user_bp = Blueprint("user", __name__)

# 内存 Token 存储（key: token 值, value: 用户信息）
_TOKENS: dict[str, dict] = {}


@user_bp.route("/login", methods=["POST"])
def login():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""

    if not username or not password:
        return Result.fail(code=20002, message="用户名或密码不能为空")

    # 查询数据库 users 表
    with get_db_connection(sqlite3.Row) as conn:
        row = conn.execute(
            "SELECT id, username, password, real_name, role FROM users WHERE username = ?",
            (username,),
        ).fetchone()

    if row is None:
        return Result.fail(code=20002, message="用户名或密码不正确")

    # 校验密码（使用 bcrypt）
    if not check_password(password, row["password"]):
        return Result.fail(code=20002, message="用户名或密码不正确")

    # 生成 token 并存入内存
    token = "user:" + str(uuid.uuid4())
    _TOKENS[token] = {
        "user_id": row["id"],
        "name": row["real_name"] or row["username"],
        "username": row["username"],
        "role": row["role"],
        "avatar": "",
    }

    return Result.success(message="登录成功", data={"token": token})


@user_bp.route("/info", methods=["GET"])
def info():
    # 优先从请求头 X-Token 获取，兼容 query 参数
    token = request.headers.get("X-Token") or request.args.get("token")
    user_data = _TOKENS.get(token)
    if not user_data:
        return Result.fail(code=20002, message="登录信息无效，请重新登录")
    return Result.success(message="获取用户信息成功", data=user_data)


@user_bp.route("/logout", methods=["POST"])
def logout():
    token = request.headers.get("X-Token") or request.args.get("token")
    if token:
        _TOKENS.pop(token, None)
    return Result.success(message="注销成功")
