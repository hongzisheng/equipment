# file_router.py 顶部
import os
import uuid
import sqlite3
import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify, send_file, make_response
from werkzeug.utils import secure_filename
from app.utils import get_db_path
from ..extraction.parse_router import parse_single_file, build_pdf_chunks, MAX_PDF_PAGES

MD_FOLDER = Path(__file__).resolve().parent.parent.parent.parent.parent / 'assets' / 'mdfile'

def init_file_table():
    db_path = get_db_path()  # 复用 utils 中的数据库路径
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS uploaded_files (
            id TEXT PRIMARY KEY,
            original_name TEXT NOT NULL,
            saved_path TEXT NOT NULL,
            category TEXT NOT NULL,   -- '定额' 或 '规程'
            upload_time TEXT NOT NULL,
            md_path TEXT DEFAULT ''
        )
    ''')
    # 兼容旧表：如果 md_path 列不存在则追加
    try:
        cursor.execute('ALTER TABLE uploaded_files ADD COLUMN md_path TEXT DEFAULT \'\'')
        conn.commit()
    except sqlite3.OperationalError:
        pass  # 列已存在
    conn.commit()
    conn.close()

# 在模块加载时初始化表
init_file_table()
MD_FOLDER.mkdir(parents=True, exist_ok=True)

file_bp = Blueprint('file', __name__, url_prefix='/api')

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
QUOTA_FOLDER = PROJECT_ROOT / 'assets' / 'quotafile'
PROCEDURE_FOLDER = PROJECT_ROOT / 'assets' / 'procedurefile'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png', 'txt'}
FAULT_FOLDER = PROJECT_ROOT / 'assets' / 'faultfile'
QUOTA_FOLDER.mkdir(parents=True, exist_ok=True)
FAULT_FOLDER.mkdir(parents=True, exist_ok=True)
PROCEDURE_FOLDER.mkdir(parents=True, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 内存存储上传文件信息（生产环境可改用数据库）
@file_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有文件部分'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': '未选择文件'}), 400
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': '仅支持 PDF、Word、Excel、JPG、PNG、TXT 文件'}), 400

    # 获取分类参数（前端通过表单字段传递）
    category = request.form.get('category', '未分类')
    if category not in ['定额', '规程', '故障']:
        return jsonify({'success': False, 'message': '分类必须为 "定额"、"规程" 或 "故障"'}), 400

    # 获取原始文件名，优先使用前端传递的 original_name
    original_name = request.form.get('original_name', file.filename)
    if not original_name:
        original_name = file.filename
    
    # 保留原始文件名中的中文等 Unicode 字符，仅剔除路径分隔符等危险字符
    file_id = str(uuid.uuid4())
    raw_name = file.filename or 'file'
    safe_filename = raw_name.replace('/', '').replace('\\', '').replace('\0', '').replace('..', '')
    if not safe_filename or '.' not in safe_filename:
        ext = raw_name.rsplit('.', 1)[-1].lower() if '.' in raw_name else ''
        safe_filename = f"file.{ext}" if ext else 'file'
    saved_filename = safe_filename
    folder_map = {'定额': QUOTA_FOLDER, '规程': PROCEDURE_FOLDER, '故障': FAULT_FOLDER}
    target_folder = folder_map[category]
    filepath = target_folder / saved_filename

    # 检测重名：文件已存在时，若前端未要求覆盖则返回冲突
    overwrite = request.form.get('overwrite', 'false').lower() == 'true'
    if filepath.exists():
        if not overwrite:
            return jsonify({
                'success': False,
                'conflict': True,
                'filename': original_name,
                'message': f'文件 "{original_name}" 已存在，是否覆盖？'
            }), 409
        # 覆盖模式：删掉旧的 DB 记录
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM uploaded_files WHERE saved_path = ?', (str(filepath),))
        conn.commit()
        conn.close()

    file.save(filepath)

    # 写入数据库，保存完整的原始文件名
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO uploaded_files (id, original_name, saved_path, category, upload_time) VALUES (?, ?, ?, ?, ?)',
        (file_id, original_name, str(filepath), category, datetime.datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

    return jsonify({
        'success': True,
        'message': '上传成功',
        'file_id': file_id,
        'file_name': original_name,
        'category': category,
        'url': f"http://localhost:5000/api/pdf/{file_id}"
    })


@file_bp.route('/files/<file_id>/convert', methods=['POST', 'OPTIONS'])
def convert_file_to_md(file_id):
    """将定额文件转换为 markdown（调 MinerU）"""
    if request.method == 'OPTIONS':
        return '', 204

    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT saved_path, original_name, category, md_path FROM uploaded_files WHERE id = ?', (file_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({'success': False, 'message': '文件不存在'}), 404

    if row['category'] != '定额':
        return jsonify({'success': False, 'message': '仅支持定额文件转换'}), 400

    if row['md_path']:
        return jsonify({'success': True, 'message': '文件已转换', 'converted': True})

    file_path = row['saved_path']
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'message': '文件不存在'}), 404

    original_name = row['original_name'] or Path(file_path).name
    try:
        with open(file_path, 'rb') as f:
            file_bytes = f.read()

        # 先检查重名冲突（避免白跑 MinerU）
        base_name = Path(original_name).stem
        md_filename = f"{base_name}.md"
        md_path = MD_FOLDER / md_filename
        overwrite = request.form.get('overwrite', 'false').lower() == 'true'
        if md_path.exists() and not overwrite:
            return jsonify({
                'success': False,
                'conflict': True,
                'message': f'"{md_filename}" 已存在，是否重新转换？'
            }), 409

        # 调用 MinerU 解析（大 PDF 分块上传）
        ext = os.path.splitext(original_name)[1].lower()
        if ext == '.pdf':
            total_pages, pdf_chunks = build_pdf_chunks(file_bytes)
            if total_pages > 200:
                chunks = [(f'{base_name}_part{i:03d}.pdf', c) for i, c in enumerate(pdf_chunks, start=1)]
            else:
                chunks = [(original_name, file_bytes)]
        else:
            chunks = [(original_name, file_bytes)]

        markdown_parts = []
        for i, (chunk_name, chunk_bytes) in enumerate(chunks):
            page_offset = i * MAX_PDF_PAGES
            md, _ = parse_single_file(chunk_name, chunk_bytes, page_offset=page_offset)
            markdown_parts.append(md)
        markdown = '\n\n'.join(part.strip() for part in markdown_parts if part is not None)

        md_path.write_text(markdown, encoding='utf-8')

        # 更新数据库
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute('UPDATE uploaded_files SET md_path = ? WHERE id = ?', (str(md_path), file_id))
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': '转换完成', 'converted': True})

    except Exception as e:
        return jsonify({'success': False, 'message': f'转换失败: {str(e)}'}), 500


@file_bp.route('/pdf/<file_id>', methods=['GET'])
def get_pdf(file_id):
    """根据 file_id 返回 PDF 文件流，并强制添加 CORS 头"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT saved_path FROM uploaded_files WHERE id = ?', (file_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({'success': False, 'message': '文件不存在'}), 404

    file_path = row['saved_path']
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'message': '文件不存在'}), 404

    response = make_response(send_file(file_path, mimetype='application/pdf'))
    return response

@file_bp.route('/files/<file_id>/download', methods=['GET'])
def download_file(file_id):
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT saved_path, original_name FROM uploaded_files WHERE id = ?', (file_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({'success': False, 'message': '文件不存在'}), 404

    file_path = row['saved_path']
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'message': '文件不存在'}), 404

    return send_file(
        file_path,
        as_attachment=True,
        download_name=row['original_name']
    )

@file_bp.route('/files/<file_id>', methods=['DELETE'])
def delete_file(file_id):
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT saved_path, md_path FROM uploaded_files WHERE id = ?', (file_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return jsonify({'success': False, 'message': '文件不存在'}), 404

    saved_path = row['saved_path']
    md_path = row['md_path']
    try:
        if os.path.exists(saved_path):
            os.remove(saved_path)
        # 删除对应的 markdown 文件
        if md_path and os.path.exists(md_path):
            os.remove(md_path)
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'删除文件失败: {e}'}), 500

    cursor.execute('DELETE FROM uploaded_files WHERE id = ?', (file_id,))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': '删除成功'})


@file_bp.route('/files/<file_id>/md', methods=['DELETE'])
def delete_md(file_id):
    """只删除转换后的 md 文件，保留原始文件"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT md_path FROM uploaded_files WHERE id = ?', (file_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return jsonify({'success': False, 'message': '文件不存在'}), 404

    md_path = row['md_path']
    if not md_path:
        conn.close()
        return jsonify({'success': False, 'message': '没有已转换的 md 文件'}), 400

    try:
        if os.path.exists(md_path):
            os.remove(md_path)
        cursor.execute("UPDATE uploaded_files SET md_path='' WHERE id=?", (file_id,))
        conn.commit()
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'删除 md 文件失败: {e}'}), 500

    conn.close()
    return jsonify({'success': True, 'message': 'md 文件已删除'})


@file_bp.route('/files/scan-disk', methods=['POST'])
def scan_disk():
    """扫描磁盘上的文件，补齐数据库中缺失的记录"""
    from .sync_files_to_db import scan_and_sync
    result = scan_and_sync()
    return jsonify(result)


@file_bp.route('/files', methods=['GET'])
def list_files():
    category = request.args.get('category')  # 可选筛选
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if category:
        cursor.execute('SELECT id, original_name, saved_path, category, upload_time, md_path FROM uploaded_files WHERE category = ? ORDER BY upload_time DESC', (category,))
    else:
        cursor.execute('SELECT id, original_name, saved_path, category, upload_time, md_path FROM uploaded_files ORDER BY upload_time DESC')

    rows = cursor.fetchall()

    # 自动清理：文件已不存在的记录从数据库中删除，md 不存在的清空标记
    valid_files = []
    for row in rows:
        if row['md_path'] and not os.path.exists(row['md_path']):
            cursor.execute("UPDATE uploaded_files SET md_path='' WHERE id=?", (row['id'],))
            row = cursor.execute(
                'SELECT id, original_name, saved_path, category, upload_time, md_path FROM uploaded_files WHERE id=?',
                (row['id'],)
            ).fetchone()
        if os.path.exists(row['saved_path']):
            valid_files.append(dict(row))
        else:
            cursor.execute('DELETE FROM uploaded_files WHERE id = ?', (row['id'],))

    conn.commit()
    conn.close()

    # 返回时去掉 saved_path 避免泄露服务器路径，添加 converted 标记
    result = []
    for f in valid_files:
        item = {k: v for k, v in f.items() if k != 'saved_path'}
        item['converted'] = bool(f.get('md_path'))
        item.pop('md_path', None)  # 不暴露路径
        result.append(item)

    return jsonify({'success': True, 'data': result})


#文件类型切换服务
@file_bp.route('/files/<file_id>/category', methods=['POST'])
def update_file_category(file_id):
    data = request.get_json()
    new_category = data.get('category')

    if new_category not in ['定额', '规程', '故障']:
        return jsonify({'success': False, 'message': '分类必须为"定额"、"规程"或"故障"'}), 400

    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('SELECT saved_path, original_name, category FROM uploaded_files WHERE id = ?', (file_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({'success': False, 'message': '文件不存在'}), 404

    if row['category'] == new_category:
        conn.close()
        return jsonify({'success': False, 'message': '分类未发生变化'}), 400

    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
    folder_map = {
        '定额': PROJECT_ROOT / 'assets' / 'quotafile',
        '规程': PROJECT_ROOT / 'assets' / 'procedurefile',
        '故障': PROJECT_ROOT / 'assets' / 'faultfile',
    }
    target_folder = folder_map[new_category]
    target_folder.mkdir(parents=True, exist_ok=True)

    old_path = Path(row['saved_path'])
    new_path = target_folder / old_path.name

    if new_path.exists():
        conn.close()
        return jsonify({'success': False, 'conflict': True, 'message': f'目标目录已存在同名文件"{old_path.name}"'}), 409

    old_path.rename(new_path)

    cursor.execute('UPDATE uploaded_files SET category = ?, saved_path = ? WHERE id = ?',
                   (new_category, str(new_path), file_id))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': f'分类已更新为"{new_category}"'})