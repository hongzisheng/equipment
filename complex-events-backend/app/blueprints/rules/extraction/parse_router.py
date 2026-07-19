import io
import logging
import os
import re
import time
import zipfile

from pypdf import PdfReader, PdfWriter

import requests
import requests.exceptions

from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

from .quota_extract_service import extract_and_import_from_markdown, query_quotas, clean_latex_text
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


def get_markdown_from_zip(zip_url, page_offset=0):
    """从 MinerU 返回的 zip 包中提取 markdown，并注入页码标记。

    按优先级尝试三种策略：
    1. 分页 markdown 文件（1.md, 2.md ...）
    2. 通过 content_list_v2.json 获取 block 级页码，在 full.md 中注入标记
    3. 仅使用 full.md（无页码）
    返回: (markdown_text, page_count)
    """
    zip_resp = requests.get(zip_url, timeout=120, proxies={"http": None, "https": None})
    zip_resp.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(zip_resp.content)) as archive:
        namelist = archive.namelist()

        # ---- 策略1：分页 markdown 文件 ----
        page_files = []
        for name in namelist:
            match = re.search(r'(?:^|[\\/])(\d+)\.md$', name, re.IGNORECASE)
            if match:
                page_num = int(match.group(1))
                content = archive.read(name).decode('utf-8', errors='replace')
                page_files.append((page_num, content))

        if page_files:
            page_files.sort(key=lambda x: x[0])
            parts = []
            for local_page, content in page_files:
                global_page = page_offset + local_page
                parts.append(f'<!-- PAGE:{global_page} -->\n\n{content.strip()}')
            return '\n\n'.join(parts), len(page_files)

        # ---- 策略2：通过 content_list JSON 获取页码 ----
        full_md = None
        for name in namelist:
            if name.lower().endswith('full.md'):
                full_md = archive.read(name).decode('utf-8', errors='replace')
                break

        if full_md is None:
            return None, 0

        cl_json = None
        for cl_name in ['content_list_v2.json', 'content_list.json']:
            for name in namelist:
                if name.lower().endswith(cl_name):
                    try:
                        cl_json = json.loads(archive.read(name).decode('utf-8'))
                        break
                    except Exception:
                        pass
            if cl_json is not None:
                break

        if cl_json is None:
            # 策略3：兜底 full.md
            return full_md, 0

        # 展开嵌套
        if isinstance(cl_json, dict):
            cl_json = (cl_json.get('data') or cl_json.get('pages')
                       or cl_json.get('blocks') or cl_json)
        if not isinstance(cl_json, list):
            return full_md, 0

        # ---- 从 JSON block 直接渲染 markdown ----
        def _render_spans(spans, inline=False):
            if isinstance(spans, str):
                return spans
            if isinstance(spans, dict):
                return _render_spans(spans.get('content', spans.get('text', '')), inline)
            if not isinstance(spans, list):
                return str(spans)
            result = []
            for s in spans:
                if isinstance(s, str):
                    result.append(s)
                elif isinstance(s, dict):
                    t = s.get('type', 'text')
                    c = s.get('content', '')
                    if isinstance(c, list):
                        c = _render_spans(c, inline)
                    elif not isinstance(c, str):
                        c = str(c)
                    if t in ('bold', 'strong'):
                        result.append(f'**{c}**')
                    elif t in ('italic', 'em'):
                        result.append(f'*{c}*')
                    elif t in ('inline_formula', 'inline_math'):
                        result.append(f'${c}$')
                    elif t in ('superscript', 'sup'):
                        result.append(f'^{c}')
                    elif t in ('subscript', 'sub'):
                        result.append(f'~{c}~')
                    elif t in ('strikethrough', 'del'):
                        result.append(f'~~{c}~~')
                    elif t in ('code', 'inline_code'):
                        result.append(f'`{c}`')
                    elif t == 'link':
                        url = s.get('url', '')
                        result.append(f'[{c}]({url})')
                    else:
                        result.append(c)
            return ''.join(result)

        def _render_table(table_data):
            if not isinstance(table_data, list):
                return ''
            rows_html = []
            for row in table_data:
                if not isinstance(row, list):
                    continue
                cells_html = ''.join(
                    f'<td>{_render_spans(c, inline=True) if isinstance(c, (dict, list)) else c}</td>'
                    for c in row
                )
                rows_html.append(f'<tr>{cells_html}</tr>')
            if not rows_html:
                return ''
            return f'<table>{"".join(rows_html)}</table>'

        def _render_block(block):
            if not isinstance(block, dict):
                return ''
            btype = block.get('type', '')
            content = block.get('content')
            if content is None:
                return ''

            if isinstance(content, dict):
                inner = content
                if 'title_content' in inner:
                    level = int(inner.get('level', 1))
                    prefix = '#' * min(level, 6)
                    return f'{prefix} {_render_spans(inner["title_content"])}'
                if 'paragraph_content' in inner:
                    return _render_spans(inner['paragraph_content'])
                if 'table_content' in inner:
                    return _render_table(inner['table_content'])
                if 'image_content' in inner:
                    img = inner['image_content']
                    if isinstance(img, dict):
                        path = img.get('path', img.get('src', img.get('url', '')))
                        alt = img.get('alt', '')
                        return f'![{alt}]({path})'
                    return f'![]({img})'
                if 'formula_content' in inner:
                    formula = inner['formula_content']
                    if isinstance(formula, dict):
                        latex = formula.get('latex', formula.get('content', str(formula)))
                    elif isinstance(formula, str):
                        latex = formula
                    else:
                        latex = str(formula)
                    return f'$$\n{latex}\n$$'
                if 'list_content' in inner:
                    items = inner['list_content']
                    if isinstance(items, list):
                        lines = [f'- {_render_spans(item) if not isinstance(item, str) else item}' for item in items]
                        return '\n'.join(lines)
                    return _render_spans(items)
                if 'code_content' in inner:
                    code = inner['code_content']
                    lang = inner.get('language', '')
                    text = code if isinstance(code, str) else _render_spans(code)
                    return f'```{lang}\n{text}\n```'
                if 'text' in inner:
                    return inner['text'] if isinstance(inner['text'], str) else _render_spans(inner['text'])
                for val in inner.values():
                    if isinstance(val, str) and val.strip():
                        return val
                    if isinstance(val, list):
                        rendered = _render_spans(val)
                        if rendered.strip():
                            return rendered
                return ''

            if isinstance(content, str):
                return content
            if isinstance(content, list):
                return _render_spans(content)
            return str(content)

        # 按页渲染
        page_parts = []
        for page_idx, page_items in enumerate(cl_json):
            local_page = page_idx + 1
            global_page = page_offset + local_page
            if not isinstance(page_items, list):
                continue
            blocks_md = []
            for block in page_items:
                md = _render_block(block)
                if md and md.strip():
                    blocks_md.append(md.strip())
            if blocks_md:
                page_parts.append(f'<!-- PAGE:{global_page} -->\n\n' + '\n\n'.join(blocks_md))

        if len(page_parts) >= 2:
            return '\n\n'.join(page_parts), len(page_parts)

        return full_md, 0


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


def parse_single_file(file_name, file_bytes, page_offset=0):
    """解析单个文件，返回带偏移页码的 markdown。

    page_offset: 当前文件在原始 PDF 中的起始页码偏移（如第2片 offset=200）。
    """
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
                markdown, page_count = get_markdown_from_zip(markdown_url, page_offset)
                if markdown is None:
                    raise RuntimeError('MinerU did not return full.md')
                return markdown, page_count
            if state == 'failed':
                raise RuntimeError(item.get('err_msg', 'MinerU parse failed'))
        time.sleep(POLL_INTERVAL_SECONDS)


@parse_blueprint.route('/parse', methods=['POST', 'OPTIONS'])
def parse_document():
    if request.method == 'OPTIONS':
        return '', 204

    file_id = request.form.get('file_id')
    if file_id:
        # 从文件管理读取已上传文件，优先使用预转换的 markdown
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT md_path, saved_path, original_name FROM uploaded_files WHERE id = ?', (file_id,))
        row = c.fetchone()
        conn.close()
        if not row:
            return jsonify({'ok': False, 'error': 'file not found'}), 404

        # 如果已有预转换的 markdown，直接返回
        md_path = row['md_path']
        if md_path:
            try:
                with open(md_path, 'r', encoding='utf-8') as f:
                    markdown = f.read()
                return jsonify({'ok': True, 'markdown': markdown, 'saved': os.path.basename(md_path)})
            except Exception as e:
                return jsonify({'ok': False, 'error': f'读取 markdown 失败: {str(e)}'}), 500

        # 未转换则返回提示
        return jsonify({'ok': False, 'error': '文件尚未转换为 markdown，请先在文件管理页面转换'}), 400

    # 没有 file_id 时的直接上传（兼容旧调用）
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
    total_page_count = 0
    for i, (chunk_name, chunk_bytes) in enumerate(chunks):
        try:
            page_offset = i * MAX_PDF_PAGES
            md, pc = parse_single_file(chunk_name, chunk_bytes, page_offset=page_offset)
            markdown_parts.append(md)
            total_page_count += pc
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
            attrs['计量维度'] = clean_latex_text(measurement_dimension)
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