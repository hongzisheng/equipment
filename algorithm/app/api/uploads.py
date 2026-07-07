"""上传文件静态服务路由

提供工单照片等上传文件的访问入口（/uploads/<filename>）。
"""
from flask import Blueprint, send_from_directory

from app.config import Config

uploads_bp = Blueprint('uploads', __name__)


@uploads_bp.route('/uploads/<path:filename>')
def uploaded_file(filename):
    # 安全地构建上传文件夹的绝对路径
    return send_from_directory(str(Config.UPLOAD_DIR), filename)
