# file_router.py
import os
from flask import Blueprint, request, jsonify, send_file, make_response
from werkzeug.utils import secure_filename
from pathlib import Path

file_bp = Blueprint('file', __name__, url_prefix='/api')

BASE_DIR = Path(__file__).parent.parent
UPLOAD_FOLDER = BASE_DIR / 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

# ===================== 核心修改：使用固定文件名和文件ID =====================
# 固定保存的文件名（每次上传都会覆盖这个文件）
FIXED_FILENAME = "latest_quota.pdf"
# 固定的文件ID（接口返回的URL永远不变）
FIXED_FILE_ID = "latest"
# 固定的文件保存路径
FIXED_FILEPATH = UPLOAD_FOLDER / FIXED_FILENAME

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 现在只需要存储最新的一个文件信息
uploaded_files = {}

@file_bp.route('/upload', methods=['POST'])
def upload_file():
    """上传 PDF 文件，自动覆盖上次上传的文件"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有文件部分'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': '未选择文件'}), 400
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': '仅支持 PDF 文件'}), 400

    original_name = secure_filename(file.filename)

    # ===================== 核心修改：直接覆盖固定文件 =====================
    # 先删除旧文件（可选，file.save会自动覆盖，但删除更彻底）
    if FIXED_FILEPATH.exists():
        try:
            os.remove(FIXED_FILEPATH)
        except Exception:
            pass  # 如果删除失败也没关系，save会直接覆盖
    
    # 直接保存到固定路径，自动覆盖旧文件
    file.save(FIXED_FILEPATH)

    # 更新内存中的文件信息（只保留最新的一个）
    uploaded_files.clear()
    uploaded_files[FIXED_FILE_ID] = {
        'name': original_name,
        'path': FIXED_FILEPATH
    }

    # 返回固定的访问URL
    full_url = f"http://localhost:5000/api/pdf/{FIXED_FILE_ID}"
    return jsonify({
        'success': True,
        'message': '上传成功（已覆盖上次文件）',
        'file_id': FIXED_FILE_ID,
        'file_name': original_name,
        'url': full_url
    })

@file_bp.route('/pdf/<file_id>', methods=['GET'])
def get_pdf(file_id):
    """根据 file_id 返回 PDF 文件流"""
    # 只允许访问固定的latest文件ID
    if file_id != FIXED_FILE_ID or FIXED_FILE_ID not in uploaded_files:
        return jsonify({'success': False, 'message': '文件不存在或已被覆盖'}), 404

    file_path = uploaded_files[FIXED_FILE_ID]['path']
    response = make_response(send_file(file_path, mimetype='application/pdf'))
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response