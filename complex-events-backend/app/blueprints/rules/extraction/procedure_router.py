"""
规程文件知识提取路由（待实现）

提供规程文件的知识提取 API 端点
TODO: 后续实现具体接口逻辑
"""

import logging

from flask import Blueprint, jsonify, request

from .procedure_extract_service import extract_procedure_from_markdown

logger = logging.getLogger(__name__)

procedure_bp = Blueprint('procedure', __name__)


@procedure_bp.route('/procedure_extract', methods=['POST', 'OPTIONS'])
def procedure_extract():
    """
    规程文件知识提取

    接收规程文件的 markdown 内容，提取结构化知识数据。
    当前返回 501 状态码，表示功能暂未实现。

    Request body:
        {
            "markdown": "规程文件的 markdown 内容"
        }

    Returns:
        501: {"ok": false, "error": "规程文件提取功能暂未实现"}
    """
    if request.method == 'OPTIONS':
        return '', 204

    logger.warning('规程文件提取功能被调用，但暂未实现')
    return jsonify({'ok': False, 'error': '规程文件提取功能暂未实现'}), 501


@procedure_bp.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
    return response
