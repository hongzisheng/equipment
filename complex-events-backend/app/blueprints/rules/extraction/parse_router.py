import io
import logging
import os
import time
import zipfile

from pypdf import PdfReader, PdfWriter

import requests
import requests.exceptions

from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

from .quota_extract_service import extract_and_import_from_markdown, query_quotas
import sqlite3
import json
from pathlib import Path


def get_db_path():
    """获取数据库路径"""
    base_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
    return base_dir / 'database' / 'db.sqlite3'

parse_blueprint = Blueprint('parse', __name__)

TOKEN = os.getenv('MINERU_API_TOKEN', 'eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiIzMDUwMDczNSIsInJvbCI6IlJPTEVfUkVHSVNURVIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc3OTU0NjgxMSwiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiMTUyNzkwNjk2NzkiLCJvcGVuSWQiOm51bGwsInV1aWQiOiIyNmRiOGIyMy01MWFkLTQ4OWItOTcyNi05YTkyZTBiZjgzYjMiLCJlbWFpbCI6IiIsImV4cCI6MTc4NzMyMjgxMX0.bRraQfCUKj2dhlQuUi1NGNIpqAiZ-J71zGg-yVmuFXWcd8Yl_EGN2BmYG_BxNXdb-l2_CMQDcFOXGCe1Pm5rFw')
SUBMIT_URL = 'https://mineru.net/api/v4/file-urls/batch'
RESULT_URL = 'https://mineru.net/api/v4/extract-results/batch/{batch_id}'
MODEL_VERSION = 'vlm'
MAX_PDF_PAGES = 200
POLL_TIMEOUT_SECONDS = 300
POLL_INTERVAL_SECONDS = 3
SUPPORTED_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx',
    '.png', '.jpg', '.jpeg', '.jp2', '.webp', '.gif', '.bmp',
}


def get_file_extension(filename):
    return os.path.splitext(filename or '')[1].lower()


def is_supported_file(filename):
    return get_file_extension(filename) in SUPPORTED_EXTENSIONS


@parse_blueprint.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
    return response


def get_markdown_from_zip(zip_url):
    zip_resp = requests.get(zip_url, timeout=120, proxies={"http": None, "https": None})
    zip_resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(zip_resp.content)) as archive:
        for name in archive.namelist():
            if name.lower().endswith('full.md'):
                return archive.read(name).decode('utf-8', errors='replace')
    return None


def build_pdf_chunks(file_bytes, max_pages=MAX_PDF_PAGES):
    reader = PdfReader(io.BytesIO(file_bytes))
    total_pages = len(reader.pages)
    chunks = []
    for start_page in range(0, total_pages, max_pages):
        writer = PdfWriter()
        for page_index in range(start_page, min(start_page + max_pages, total_pages)):
            writer.add_page(reader.pages[page_index])
        buffer = io.BytesIO()
        writer.write(buffer)
        chunks.append(buffer.getvalue())
    return total_pages, chunks


def parse_single_file(file_name, file_bytes):
    headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}

    submit_resp = requests.post(
        SUBMIT_URL,
        headers=headers,
        json={'files': [{'name': file_name}], 'model_version': MODEL_VERSION},
        timeout=120,
        proxies={"http": None, "https": None}
    )
    submit_resp.raise_for_status()
    submit_json = submit_resp.json()
    if submit_json.get('code') != 0:
        raise RuntimeError(submit_json.get('msg', 'submit task failed'))

    data = submit_json.get('data') or {}
    batch_id = data.get('batch_id')
    file_urls = data.get('file_urls') or []
    if not batch_id or not file_urls:
        raise RuntimeError('MinerU did not return upload url')

    upload_resp = requests.put(file_urls[0], data=file_bytes, timeout=300, proxies={"http": None, "https": None})
    if upload_resp.status_code not in (200, 201):
        raise RuntimeError('upload to MinerU failed')

    result_url = RESULT_URL.format(batch_id=batch_id)
    while True:
        result_resp = requests.get(result_url, headers={'Authorization': f'Bearer {TOKEN}', 'Accept': '*/*'}, timeout=120, proxies={"http": None, "https": None})
        result_resp.raise_for_status()
        result_json = result_resp.json()
        if result_json.get('code') != 0:
            raise RuntimeError(result_json.get('msg', 'query task failed'))

        items = (result_json.get('data') or {}).get('extract_result') or []
        if items:
            item = items[0]
            state = item.get('state')
            if state == 'done':
                markdown_url = item.get('full_zip_url')
                if not markdown_url:
                    raise RuntimeError('MinerU did not return full_zip_url')
                markdown = get_markdown_from_zip(markdown_url)
                if markdown is None:
                    raise RuntimeError('MinerU did not return full.md')
                return markdown
            if state == 'failed':
                raise RuntimeError(item.get('err_msg', 'MinerU parse failed'))
        time.sleep(POLL_INTERVAL_SECONDS)


@parse_blueprint.route('/parse', methods=['POST', 'OPTIONS'])
def parse_document():
    if request.method == 'OPTIONS':
        return '', 204

    file_id = request.form.get('file_id')
    if file_id:
        # 从文件管理读取已上传文件
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT saved_path, original_name FROM uploaded_files WHERE id = ?', (file_id,))
        row = c.fetchone()
        conn.close()
        if not row:
            return jsonify({'ok': False, 'error': 'file not found'}), 404
        file_path = row['saved_path']
        filename = row['original_name'] or Path(file_path).name
        with open(file_path, 'rb') as f:
            file_bytes = f.read()
    else:
        file = request.files.get('file')
        if not file:
            return jsonify({'ok': False, 'error': 'no file provided'}), 400
        filename = file.filename or 'upload.pdf'
        file_bytes = file.read()

    if TOKEN == 'YOUR_MINERU_API_TOKEN':
        return jsonify({'ok': False, 'error': 'please set TOKEN in backend/app.py'}), 500
    if not is_supported_file(filename):
        return jsonify({'ok': False, 'error': 'unsupported file type, please upload pdf, word, excel, ppt, or image files'}), 400

    chunks = [(filename, file_bytes)]
    if get_file_extension(filename) == '.pdf':
        try:
            total_pages, pdf_chunks = build_pdf_chunks(file_bytes)
            if total_pages > MAX_PDF_PAGES:
                base_name, _ = os.path.splitext(filename)
                chunks = [
                    (f'{base_name}_part{index:03d}.pdf', chunk_bytes)
                    for index, chunk_bytes in enumerate(pdf_chunks, start=1)
                ]
        except Exception as error:
            return jsonify({'ok': False, 'error': f'failed to split pdf: {error}'}), 400

    markdown_parts = []
    for chunk_name, chunk_bytes in chunks:
        try:
            markdown_parts.append(parse_single_file(chunk_name, chunk_bytes))
        except Exception as error:
            logger.error(f'MinerU parse failed for {chunk_name}: {error}', exc_info=True)
            return jsonify({'ok': False, 'error': str(error)}), 502

    merged_markdown = '\n\n'.join(part.strip() for part in markdown_parts if part is not None)

    base_name, _ = os.path.splitext(filename)
    md_filename = f"{base_name}.md"
    md_save_dir = Path(__file__).resolve().parent.parent.parent.parent.parent / 'assets' / 'mdfile'
    md_save_path = md_save_dir / md_filename
    try:
        md_save_dir.mkdir(parents=True, exist_ok=True)
        md_save_path.write_text(merged_markdown, encoding='utf-8')
        logger.info(f'Markdown saved to {md_save_path}')
    except Exception as error:
        logger.error(f'Failed to save markdown file: {error}', exc_info=True)

    return jsonify({'ok': True, 'markdown': merged_markdown, 'saved': md_filename})


@parse_blueprint.route('/markdown_extract', methods=['POST', 'OPTIONS'])
def markdown_extract():
    if request.method == 'OPTIONS':
        return '', 204

    data = request.get_json(silent=True) or {}
    markdown = data.get('markdown')
    if not markdown:
        logger.warning('markdown_extract: no markdown provided')
        return jsonify({'ok': False, 'error': 'no markdown provided'}), 400

    logger.info(f'markdown_extract: received {len(markdown)} chars of markdown')
    try:
        summary = extract_and_import_from_markdown(markdown)
        logger.info(f'markdown_extract success: {summary}')
        return jsonify({'ok': True, 'summary': summary})
    except Exception as e:
        logger.error(f'markdown_extract failed: {e}', exc_info=True)
        return jsonify({'ok': False, 'error': str(e)}), 500


@parse_blueprint.route('/quotas', methods=['GET', 'OPTIONS'])
def quotas():
    if request.method == 'OPTIONS':
        return '', 204

    try:
        rows = query_quotas()
        return jsonify({'ok': True, 'data': rows, 'total': len(rows)})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@parse_blueprint.route('/update_quota', methods=['POST', 'OPTIONS'])
def update_quota():
    if request.method == 'OPTIONS':
        return '', 204

    data = request.get_json(silent=True) or {}
    quota_id = data.get('quotaId')
    if not quota_id:
        return jsonify({'ok': False, 'error': 'quotaId required'}), 400

    measurement_dimension = data.get('measurementDimension')
    measurement_value = data.get('measurementValue')
    man_hours = data.get('manHours')
    labor_cost = data.get('laborCost')
    tool_cost = data.get('toolCost')
    new_process_id = data.get('processId')

    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT attributes FROM graph_nodes WHERE entity_id=? AND entity_type='定额编号'", (quota_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({'ok': False, 'error': 'quota node not found'}), 404

        attrs = json.loads(row[0]) if row[0] else {}

        if measurement_dimension is not None:
            attrs['计量维度'] = measurement_dimension
        if measurement_value is not None:
            attrs['计量值'] = measurement_value
        if labor_cost is not None:
            try:
                attrs['人工费(元)'] = float(labor_cost)
            except Exception:
                attrs['人工费(元)'] = labor_cost
        if tool_cost is not None:
            attrs['机具费用(元)'] = tool_cost
        if man_hours is not None:
            attrs['合计工日'] = man_hours

        cursor.execute("UPDATE graph_nodes SET attributes=? WHERE entity_id=?", (json.dumps(attrs, ensure_ascii=False), quota_id))

        cursor.execute("SELECT 1 FROM graph_nodes_archive WHERE entity_id=?", (quota_id,))
        if cursor.fetchone():
            cursor.execute("UPDATE graph_nodes_archive SET attributes=? WHERE entity_id=?",
                           (json.dumps(attrs, ensure_ascii=False), quota_id))

        if new_process_id:
            cursor.execute("SELECT id, source_id FROM graph_relations WHERE target_id=? AND relation_type='包含定额' LIMIT 1", (quota_id,))
            rel = cursor.fetchone()
            if rel:
                rel_id, old_source = rel[0], rel[1]
                if old_source != new_process_id:
                    cursor.execute("UPDATE graph_relations SET source_id=? WHERE id=?", (new_process_id, rel_id))
            else:
                cursor.execute("INSERT INTO graph_relations (source_type, source_id, relation_type, target_type, target_id) VALUES (?, ?, ?, ?, ?)",
                               ('工序', new_process_id, '包含定额', '定额编号', quota_id))

            cursor.execute("SELECT id, source_id FROM graph_relations_archive WHERE target_id=? AND relation_type='包含定额' LIMIT 1", (quota_id,))
            ar = cursor.fetchone()
            if ar:
                aid, a_source = ar[0], ar[1]
                if a_source != new_process_id:
                    cursor.execute("UPDATE graph_relations_archive SET source_id=? WHERE id=?", (new_process_id, aid))

        conn.commit()
        return jsonify({'ok': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 500
    finally:
        conn.close()


# 文件上传统一由文件管理模块处理（file_router.py）
# 知识提取不再单独提供上传和文件服务