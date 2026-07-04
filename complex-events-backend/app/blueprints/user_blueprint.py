import uuid

from flask import Blueprint, current_app, request

from app.models import Result

user_bp = Blueprint("user", __name__)
_TOKENS = {}


@user_bp.route("/login", methods=["POST"])
def login():
    payload = request.get_json(silent=True) or {}
    username = payload.get("username", "")
    password = payload.get("password", "")

    if username == current_app.config["LOGIN_USERNAME"] and password == current_app.config["LOGIN_PASSWORD"]:
        token = "user:" + str(uuid.uuid4())
        _TOKENS[token] = {
            "name": current_app.config["LOGIN_DISPLAY_NAME"],
            "avatar": "",
        }
        return Result.success(message="登录成功", data={"token": token})

    return Result.fail(code=20002, message="用户名或密码不正确")


@user_bp.route("/info", methods=["GET"])
def info():
    token = request.args.get("token")
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
