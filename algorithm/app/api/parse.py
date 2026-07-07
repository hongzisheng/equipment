import io
import os
import time
import zipfile

from pypdf import PdfReader, PdfWriter

import requests
from flask import Blueprint, jsonify, request

from app.services.quota_extract import extract_and_import_from_markdown, query_quotas
import sqlite3
import json
from app.utils import get_db_path

parse_blueprint = Blueprint('parse', __name__)

TOKEN = os.getenv('MINERU_API_TOKEN', 'eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiI5MTcwMDcyNiIsInJvbCI6IlJPTEVfUkVHSVNURVIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc3ODMxNjA2MiwiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiIiwib3BlbklkIjpudWxsLCJ1dWlkIjoiZDFiN2UyNjUtODQ3My00NzJjLTg5ZTEtMzExNzRjOGU2ODg5IiwiZW1haWwiOiIiLCJleHAiOjE3ODYwOTIwNjJ9._GWtY3lxRj4VDFm8KlZAt9M8Mi8oR_vaTx1_hDX3ygPli2Ig5OnuRj-SzQ7kulywZ2Jg9M-wTV2sshKgo5N32A')
# 标准解析 API：先申请上传链接，再上传文件，最后轮询结果。
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
	# 允许前端本地页面直接请求后端接口。
	response.headers['Access-Control-Allow-Origin'] = '*'
	response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
	response.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
	return response


def get_markdown_from_zip(zip_url):
	# 解析完成后，MinerU 会返回包含 full.md 的 zip 包。
	zip_resp = requests.get(zip_url, timeout=120)
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

	# 第一步：申请文件上传地址。
	submit_resp = requests.post(
		SUBMIT_URL,
		headers=headers,
		json={'files': [{'name': file_name}], 'model_version': MODEL_VERSION},
		timeout=120,
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

	# 第二步：把文件上传到 MinerU 提供的 OSS 地址。
	upload_resp = requests.put(file_urls[0], data=file_bytes, timeout=120)
	if upload_resp.status_code not in (200, 201):
		raise RuntimeError('upload to MinerU failed')

	# 第三步：轮询任务结果，直到完成。
	result_url = RESULT_URL.format(batch_id=batch_id)
	while True:
		result_resp = requests.get(result_url, headers={'Authorization': f'Bearer {TOKEN}', 'Accept': '*/*'}, timeout=120)
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


@parse_blueprint.route('/api/parse', methods=['POST', 'OPTIONS'])
def parse_document():
	if request.method == 'OPTIONS':
		return '', 204

	# 从表单里取上传的 PDF 文件。
	file = request.files.get('file')
	if not file:
		return jsonify({'ok': False, 'error': 'no file provided'}), 400
	if TOKEN == 'YOUR_MINERU_API_TOKEN':
		return jsonify({'ok': False, 'error': 'please set TOKEN in backend/app.py'}), 500

	filename = file.filename or 'upload.pdf'
	if not is_supported_file(filename):
		return jsonify({'ok': False, 'error': 'unsupported file type, please upload pdf, word, excel, ppt, or image files'}), 400

	# 先把文件读到内存，再传给 MinerU 返回的签名上传地址。
	file_bytes = file.read()
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
		except RuntimeError as error:
			return jsonify({'ok': False, 'error': str(error)}), 502

	merged_markdown = '\n\n'.join(part.strip() for part in markdown_parts if part is not None)

	# 只返回解析后的 Markdown 给前端，后续由前端决定是否调用入库接口
	return jsonify({'ok': True, 'markdown': merged_markdown})


@parse_blueprint.route('/api/markdown_extract', methods=['POST', 'OPTIONS'])
def markdown_extract():
	if request.method == 'OPTIONS':
		return '', 204

	data = request.get_json(silent=True) or {}
	markdown = data.get('markdown')
	if not markdown:
		return jsonify({'ok': False, 'error': 'no markdown provided'}), 400

	try:
		summary = extract_and_import_from_markdown(markdown)
		return jsonify({'ok': True, 'summary': summary})
	except Exception as e:
		return jsonify({'ok': False, 'error': str(e)}), 500


@parse_blueprint.route('/api/quotas', methods=['GET', 'OPTIONS'])
def quotas():
	if request.method == 'OPTIONS':
		return '', 204

	try:
		rows = query_quotas()
		return jsonify({'ok': True, 'data': rows, 'total': len(rows)})
	except Exception as e:
		return jsonify({'ok': False, 'error': str(e)}), 500


@parse_blueprint.route('/api/update_quota', methods=['POST', 'OPTIONS'])
def update_quota():
	if request.method == 'OPTIONS':
		return '', 204

	data = request.get_json(silent=True) or {}
	quota_id = data.get('quotaId')
	if not quota_id:
		return jsonify({'ok': False, 'error': 'quotaId required'}), 400

	# editable fields (may be None)
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
		# load existing quota node
		cursor.execute("SELECT attributes FROM graph_nodes WHERE entity_id=? AND entity_type='定额编号'", (quota_id,))
		row = cursor.fetchone()
		if not row:
			return jsonify({'ok': False, 'error': 'quota node not found'}), 404

		attrs = json.loads(row[0]) if row[0] else {}

		# apply updates to attributes
		if measurement_dimension is not None:
			attrs['计量维度'] = measurement_dimension
		if measurement_value is not None:
			attrs['计量值'] = measurement_value
		if labor_cost is not None:
			# keep same key used elsewhere
			try:
				attrs['人工费(元)'] = float(labor_cost)
			except Exception:
				attrs['人工费(元)'] = labor_cost
		if tool_cost is not None:
			attrs['机具费用(元)'] = tool_cost
		if man_hours is not None:
			# store aggregate days under a key to keep value available
			attrs['合计工日'] = man_hours

		# update main graph_nodes
		cursor.execute("UPDATE graph_nodes SET attributes=? WHERE entity_id=?", (json.dumps(attrs, ensure_ascii=False), quota_id))

		# update archive node only if it already exists (do not insert new rows)
		cursor.execute("SELECT 1 FROM graph_nodes_archive WHERE entity_id=?", (quota_id,))
		if cursor.fetchone():
			cursor.execute("UPDATE graph_nodes_archive SET attributes=? WHERE entity_id=?",
						   (json.dumps(attrs, ensure_ascii=False), quota_id))

		# handle relation update if process changed
		if new_process_id:
			cursor.execute("SELECT id, source_id FROM graph_relations WHERE target_id=? AND relation_type='包含定额' LIMIT 1", (quota_id,))
			rel = cursor.fetchone()
			if rel:
				rel_id, old_source = rel[0], rel[1]
				if old_source != new_process_id:
					cursor.execute("UPDATE graph_relations SET source_id=? WHERE id=?", (new_process_id, rel_id))
			else:
				# insert new relation if missing
				cursor.execute("INSERT INTO graph_relations (source_type, source_id, relation_type, target_type, target_id) VALUES (?, ?, ?, ?, ?)",
							   ('工序', new_process_id, '包含定额', '定额编号', quota_id))

			# update archive relation only if a matching archive row exists (do not insert)
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