"""知识图谱归档关系查询路由

从原 app.py 抽取。注意：原 app.py 中的 /api/equipment-categories
与 /api/equipment-types-with-category 与 equipment 模块重复（已被
equipment 蓝图覆盖），此处不再重复定义，由 app/api/equipment.py 提供。
"""
import sqlite3
from flask import Blueprint, jsonify

from app.utils import get_db_path

graph_bp = Blueprint('graph', __name__, url_prefix='/api')


@graph_bp.route('/graph-relations-archive', methods=['GET'])
def get_graph_relations_archive():
    """获取所有图关系数据（包含实体名称）"""
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 查询关系数据并关联获取源和目标实体的名称
        cursor.execute('''
        SELECT
            r.id,
            r.source_type,
            r.source_id,
            r.relation_type,
            r.target_type,
            r.target_id,
            json_extract(s.attributes, '$.名称') AS source_name,
            json_extract(t.attributes, '$.名称') AS target_name
        FROM graph_relations_archive r
        LEFT JOIN graph_nodes_archive s ON r.source_id = s.entity_id
        LEFT JOIN graph_nodes_archive t ON r.target_id = t.entity_id
        ORDER BY r.id
        ''')

        relations = []
        for row in cursor.fetchall():
            relations.append({
                'id': row['id'],
                'source_type': row['source_type'],
                'source_id': row['source_id'],
                'relation_type': row['relation_type'],
                'target_type': row['target_type'],
                'target_id': row['target_id'],
                'source_name': row['source_name'],
                'target_name': row['target_name']
            })

        conn.close()
        return jsonify({
            'success': True,
            'data': relations
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
