"""
扫描 assets/ 目录下的文件，补齐数据库 uploaded_files 表中缺失的记录。

可作为独立脚本运行：
    python -m app.blueprints.rules.file.sync_files_to_db

也可作为模块被 API 调用：
    from .sync_files_to_db import scan_and_sync
    result = scan_and_sync()
"""

import os
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

# ---- 路径配置 ----
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
DB_PATH = BASE_DIR / 'database' / 'db.sqlite3'
ASSETS_DIR = BASE_DIR / 'assets'
QUOTA_DIR = ASSETS_DIR / 'quotafile'
PROCEDURE_DIR = ASSETS_DIR / 'procedurefile'
MD_DIR = ASSETS_DIR / 'mdfile'


def _get_conn():
    return sqlite3.connect(str(DB_PATH))


def _existing_index(conn):
    """返回 {saved_path: row} 和 {stem_lower: row} 两个索引"""
    conn.row_factory = sqlite3.Row
    rows = conn.execute('SELECT * FROM uploaded_files').fetchall()
    by_path = {}
    by_stem = {}
    for r in rows:
        if r['saved_path']:
            by_path[r['saved_path']] = r
            stem = Path(r['saved_path']).stem.lower()
            if stem not in by_stem:
                by_stem[stem] = r
        name_stem = Path(r['original_name']).stem.lower()
        if name_stem not in by_stem:
            by_stem[name_stem] = r
    return by_path, by_stem


def _scan_folder(folder, category, conn, existing_by_path):
    """扫描文件夹，返回新增记录列表"""
    if not folder.exists():
        return []

    new_records = []
    for fpath in sorted(folder.iterdir()):
        if not fpath.is_file():
            continue
        abs_path = str(fpath.resolve())
        if abs_path in existing_by_path:
            continue

        file_id = str(uuid.uuid4())
        original_name = fpath.name
        upload_time = datetime.fromtimestamp(fpath.stat().st_mtime).isoformat()
        conn.execute(
            'INSERT INTO uploaded_files (id, original_name, saved_path, category, upload_time, md_path) '
            'VALUES (?, ?, ?, ?, ?, ?)',
            (file_id, original_name, abs_path, category, upload_time, '')
        )
        new_records.append(file_id)
    return new_records


def _match_md_files(conn):
    """扫描 mdfile/，匹配原始文件记录并补 md_path"""
    if not MD_DIR.exists():
        return []

    matched = []
    for fpath in sorted(MD_DIR.iterdir()):
        if not fpath.is_file() or fpath.suffix.lower() != '.md':
            continue

        abs_path = str(fpath.resolve())
        stem = fpath.stem.lower()

        # 跳过已匹配的
        existing = conn.execute(
            "SELECT id FROM uploaded_files WHERE md_path=?", (abs_path,)
        ).fetchone()
        if existing:
            continue

        # 按 stem 模糊匹配 original_name
        clean_stem = stem
        for suffix in ['_part001', '_part01', '_part1', '_part_001']:
            if clean_stem.endswith(suffix):
                clean_stem = clean_stem[:-len(suffix)]
                break

        rows = conn.execute(
            "SELECT id, original_name, md_path FROM uploaded_files "
            "WHERE LOWER(original_name) LIKE ? AND (md_path IS NULL OR md_path = '')",
            (f'%{clean_stem}%',)
        ).fetchall()
        if rows:
            conn.execute('UPDATE uploaded_files SET md_path=? WHERE id=?', (abs_path, rows[0]['id']))
            matched.append(fpath.name)
    return matched


def scan_and_sync():
    """
    执行磁盘扫描与数据库同步。
    返回: dict { new_records: int, matched_md: int, detail: str }
    """
    if not DB_PATH.exists():
        return {'success': False, 'message': f'数据库不存在: {DB_PATH}'}

    conn = sqlite3.connect(str(DB_PATH))
    existing_by_path, existing_by_stem = _existing_index(conn)

    new_quota = _scan_folder(QUOTA_DIR, '定额', conn, existing_by_path)
    new_proc = _scan_folder(PROCEDURE_DIR, '规程', conn, existing_by_path)
    conn.commit()

    matched_md = _match_md_files(conn)
    conn.commit()
    conn.close()

    total_new = len(new_quota) + len(new_proc)
    parts = []
    if new_quota:
        parts.append(f'定额 {len(new_quota)} 个')
    if new_proc:
        parts.append(f'规程 {len(new_proc)} 个')
    detail_parts = []
    if parts:
        detail_parts.append(f'新增 {", ".join(parts)}')
    if matched_md:
        detail_parts.append(f'匹配 md {len(matched_md)} 个')
    detail = '；'.join(detail_parts) if detail_parts else '无新增'

    return {
        'success': True,
        'new_records': total_new,
        'matched_md': len(matched_md),
        'message': detail,
    }


# ---- 独立运行入口 ----
if __name__ == '__main__':
    print('=' * 60)
    print('文件磁盘同步工具')
    print('=' * 60)
    result = scan_and_sync()
    print(f'结果: {result["message"]}')
    print('完成！')
