# file_router.py
import os
import uuid
from flask import Blueprint, request, jsonify, send_file, make_response
from werkzeug.utils import secure_filename
from pathlib import Path

file_bp = Blueprint('file', __name__, url_prefix='/api')

BASE_DIR = Path(__file__).parent.parent
UPLOAD_FOLDER = BASE_DIR / 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 内存存储上传文件信息（生产环境可改用数据库）
uploaded_files = {}  # { file_id: {'name': original_name, 'path': Path} }

@file_bp.route('/upload', methods=['POST'])
def upload_file():
    """上传 PDF 文件，返回 file_id 和访问 URL"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有文件部分'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': '未选择文件'}), 400
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': '仅支持 PDF 文件'}), 400

    original_name = secure_filename(file.filename)
    file_id = str(uuid.uuid4())
    saved_filename = f"{file_id}_{original_name}"
    filepath = UPLOAD_FOLDER / saved_filename
    file.save(filepath)

    uploaded_files[file_id] = {
        'name': original_name,
        'path': filepath
    }

    # 返回可直接访问的 PDF URL
    full_url = f"http://localhost:5000/api/pdf/{file_id}"
    return jsonify({
        'success': True,
        'message': '上传成功',
        'file_id': file_id,
        'file_name': original_name,
        'url': full_url
    })

@file_bp.route('/pdf/<file_id>', methods=['GET'])
def get_pdf(file_id):
    """根据 file_id 返回 PDF 文件流，并强制添加 CORS 头"""
    if file_id not in uploaded_files:
        return jsonify({'success': False, 'message': '文件不存在'}), 404

    file_path = uploaded_files[file_id]['path']
    response = make_response(send_file(file_path, mimetype='application/pdf'))
    # 关键：手动设置跨域头，确保前端 PDF.js 能加载文件
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response