from flask import Blueprint, jsonify, request
import sqlite3
from pathlib import Path

search_archive_bp = Blueprint('search_archive', __name__)


def get_db_path():
    base_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
    return base_dir / 'database' / 'db.sqlite3'


# 1. 获取所有册名（作为"设备类型"下拉选项）
@search_archive_bp.route('/graph-archive/volumes', methods=['GET'])
def get_graph_volumes():
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        c.execute("""
            SELECT entity_id, json_extract(attributes, '$.名称') AS name
            FROM graph_nodes_archive
            WHERE entity_type = '册名'
            ORDER BY entity_id
        """)
        rows = c.fetchall()
        conn.close()
        return jsonify({
            'success': True,
            'data': [{'id': row[0], 'name': row[1]} for row in rows]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取册名失败: {str(e)}'}), 500


# 2. 按册名获取章节（作为"设备"下拉选项）
@search_archive_bp.route('/graph-archive/chapters', methods=['GET'])
def get_graph_chapters():
    try:
        volume = request.args.get('volume', '').strip()
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        if volume:
            c.execute("""
                SELECT DISTINCT t.entity_id,
                       json_extract(t.attributes, '$.名称') AS name
                FROM graph_relations_archive r
                LEFT JOIN graph_nodes_archive s ON r.source_id = s.entity_id
                LEFT JOIN graph_nodes_archive t ON r.target_id = t.entity_id
                WHERE r.source_type = '册名'
                  AND r.target_type = '章节'
                  AND r.relation_type = '包含章节'
                  AND s.entity_id = ?
                ORDER BY t.entity_id
            """, (volume,))
        else:
            c.execute("""
                SELECT DISTINCT t.entity_id,
                       json_extract(t.attributes, '$.名称') AS name
                FROM graph_relations_archive r
                LEFT JOIN graph_nodes_archive t ON r.target_id = t.entity_id
                WHERE r.source_type = '册名'
                  AND r.target_type = '章节'
                  AND r.relation_type = '包含章节'
                ORDER BY t.entity_id
            """)

        rows = c.fetchall()
        conn.close()
        return jsonify({
            'success': True,
            'data': [{'id': row['entity_id'], 'name': row['name']} for row in rows]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取章节失败: {str(e)}'}), 500


# 3. 按章节获取工序（作为"工序"下拉选项）
@search_archive_bp.route('/graph-archive/processes', methods=['GET'])
def get_graph_processes():
    try:
        chapter = request.args.get('chapter', '').strip()
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        if chapter:
            # 先按名称查章节的 entity_id
            c.execute("""
                SELECT entity_id FROM graph_nodes_archive
                WHERE entity_type = '章节'
                  AND json_extract(attributes, '$.名称') = ?
            """, (chapter,))
            row = c.fetchone()
            if not row:
                conn.close()
                return jsonify({'success': True, 'data': []})

            chapter_id = row['entity_id']
            # 查该章节下的工序（直接包含 或 通过节间接包含）
            c.execute("""
                SELECT DISTINCT p.entity_id,
                       json_extract(p.attributes, '$.名称') AS name
                FROM graph_nodes_archive p
                WHERE p.entity_type = '工序'
                  AND (
                    EXISTS (
                      SELECT 1 FROM graph_relations_archive r
                      WHERE r.source_id = ? AND r.target_id = p.entity_id
                        AND r.relation_type = '包含工序'
                    )
                    OR EXISTS (
                      SELECT 1 FROM graph_relations_archive r1
                      JOIN graph_relations_archive r2 ON r1.target_id = r2.source_id
                      WHERE r1.source_id = ? AND r1.relation_type = '包含节'
                        AND r2.target_id = p.entity_id AND r2.relation_type = '包含工序'
                    )
                  )
                ORDER BY p.entity_id
            """, (chapter_id, chapter_id))
        else:
            c.execute("""
                SELECT DISTINCT entity_id,
                       json_extract(attributes, '$.名称') AS name
                FROM graph_nodes_archive
                WHERE entity_type = '工序'
                ORDER BY entity_id
            """)

        rows = c.fetchall()
        conn.close()
        return jsonify({
            'success': True,
            'data': [{'id': row['entity_id'], 'name': row['name']} for row in rows]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取工序失败: {str(e)}'}), 500


# 4. 检索定额数据
@search_archive_bp.route('/search-graph-processes', methods=['POST'])
def search_graph_processes():
    try:
        data = request.get_json() or {}
        volume = (data.get('volume') or '').strip()
        chapter = (data.get('chapter') or '').strip()
        process_name = (data.get('process') or '').strip()

        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        sql = """
            SELECT
                json_extract(proc.attributes, '$.名称') AS process_name,
                json_extract(q.attributes, '$.计量维度') AS measure_dimension,
                json_extract(q.attributes, '$.计量值') AS measure_value,
                json_extract(q.attributes, '$.人工费(元)') AS labor_cost,
                json_extract(q.attributes, '$.材料费(元)') AS material_cost,
                json_extract(q.attributes, '$.机械费(元)') AS machine_cost,
                json_extract(labor.attributes, '$.人工明细[0].使用数量') AS total_work_days
            FROM graph_nodes_archive q
            LEFT JOIN graph_relations_archive r1
                ON r1.target_id = q.entity_id AND r1.relation_type = '包含定额'
            LEFT JOIN graph_nodes_archive proc
                ON proc.entity_id = r1.source_id AND proc.entity_type = '工序'
            LEFT JOIN graph_relations_archive r2
                ON r2.target_id = proc.entity_id AND r2.relation_type = '包含工序'
            LEFT JOIN graph_relations_archive r_sec
                ON r_sec.target_id = r2.source_id AND r_sec.relation_type = '包含节'
            LEFT JOIN graph_nodes_archive chap
                ON chap.entity_type = '章节'
                AND chap.entity_id = COALESCE(r_sec.source_id, r2.source_id)
            LEFT JOIN graph_relations_archive r3
                ON r3.target_id = chap.entity_id AND r3.relation_type = '包含章节'
            LEFT JOIN graph_nodes_archive vol
                ON vol.entity_id = r3.source_id AND vol.entity_type = '册名'
            LEFT JOIN graph_relations_archive r_labor
                ON r_labor.source_id = q.entity_id AND r_labor.relation_type = '包含人工明细'
            LEFT JOIN graph_nodes_archive labor
                ON labor.entity_id = r_labor.target_id
            WHERE q.entity_type = '定额编号'
        """
        params = []

        if volume:
            sql += " AND vol.entity_id LIKE ?"
            params.append(f'%{volume}%')
        if chapter:
            sql += " AND json_extract(chap.attributes, '$.名称') LIKE ?"
            params.append(f'%{chapter}%')
        if process_name:
            sql += " AND json_extract(proc.attributes, '$.名称') LIKE ?"
            params.append(f'%{process_name}%')

        sql += " ORDER BY proc.entity_id"

        c.execute(sql, params)
        rows = c.fetchall()
        conn.close()

        def to_num(val):
            if val is None:
                return 0
            try:
                return float(str(val).replace(',', '').strip() or 0)
            except Exception:
                return 0

        results = []
        for row in rows:
            labor = to_num(row['labor_cost'])
            material = to_num(row['material_cost'])
            machine = to_num(row['machine_cost'])
            results.append({
                'process': row['process_name'] or '未关联',
                'measure_dimension': row['measure_dimension'] or '-',
                'measure_value': row['measure_value'] or '-',
                'total_work_days': to_num(row['total_work_days']),
                'labor_cost': round(labor, 2),
                'tool_cost': round(material + machine, 2)
            })

        return jsonify({'success': True, 'data': results})
    except Exception as e:
        return jsonify({'success': False, 'message': f'检索失败: {str(e)}'}), 500