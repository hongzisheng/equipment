from flask import request

from app.models import Result
from app.data.mock_data import get_mock_workers, get_mock_orders, get_mock_materials, get_mock_tools
from . import info_bp


@info_bp.route("/workers", methods=["POST"])
def get_workers():
    return Result.success(message="查询成功", data=get_mock_workers())


@info_bp.route("/orders", methods=["GET"])
def get_orders():
    return Result.success(message="查询成功", data=get_mock_orders())


@info_bp.route("/materials", methods=["POST"])
def get_materials():
    return Result.success(message="查询成功", data=get_mock_materials())


@info_bp.route("/tools", methods=["POST"])
def get_tools():
    return Result.success(message="查询成功", data=get_mock_tools())
