from flask import jsonify, request
import sqlite3
from pathlib import Path

from . import worker_bp

scheduler = None


def get_db_path():
    """统一获取数据库路径"""
    current_dir = Path(__file__).parent.parent
    return current_dir / 'database' / 'db.sqlite3'


# ----------工人相关------------------
"""获取所有工人信息"""
@worker_bp.route('/workers', methods=['GET'])
def get_workers():
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()

        # 查询工人信息（增加 compose 字段）
        c.execute('''
            SELECT id, name, worker_type_id, is_certified, organization, emp_id, compose,skill_level
            FROM workers
            ORDER BY id
        ''')

        workers = []
        for row in c.fetchall():
            workers.append({
                'id': row[0],
                'name': row[1],
                'worker_type_id': row[2],
                'worker_type': row[2],          
                'is_certified': row[3],
                'organization': row[4],
                'emp_id': row[5],
                'compose': row[6],
                'skill_level': row[7]              
            })

        conn.close()

        return jsonify({
            'success': True,
            'workers': workers,
            'total_count': len(workers)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '获取工人信息失败'
        }), 500

"""获取所有工种信息"""
@worker_bp.route('/worker-types', methods=['GET'])
def get_worker_types():
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()

        c.execute('''
            SELECT id, name, description, requires_certification, created_at, price
            FROM worker_types
            ORDER BY id
        ''')

        worker_types = []
        for row in c.fetchall():
            worker_types.append({
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'requires_certification': bool(row[3]),
                'created_at': row[4],
                'price': row[5]
            })

        conn.close()

        return jsonify({
            'success': True,
            'data': worker_types
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '获取工种信息失败'
        }), 500
"""设置选中的工人"""
@worker_bp.route('/select-workers', methods=['POST'])
def select_workers():
    try:
        data = request.get_json()
        selected_worker_ids = data.get('selected_worker_ids', [])
        print(selected_worker_ids)
        if not selected_worker_ids:
            return jsonify({
                'success': False,
                'message': '请选择至少一个工人'
            }), 400

        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()

        # 1. 从 workers 表获取选中的工人信息（增加 compose）
        placeholders = ','.join('?' * len(selected_worker_ids))
        c.execute(f'''
            SELECT id, name, worker_type_id, is_certified, organization, compose
            FROM workers 
            WHERE id IN ({placeholders})
        ''', selected_worker_ids)
        selected_workers = c.fetchall()

        if len(selected_workers) != len(selected_worker_ids):
            conn.close()
            return jsonify({
                'success': False,
                'message': '部分工人ID不存在'
            }), 400

        # 2. 清空 selected_workers 表
        c.execute('DELETE FROM selected_workers')

        # 3. 将选中的工人插入 selected_workers 表（增加 compose 列）
        for worker in selected_workers:
            worker_id, name, worker_type_id, is_certified, organization, compose = worker
            c.execute('''
                INSERT INTO selected_workers (id, name, worker_type_id, is_certified, organization, compose)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (worker_id, name, worker_type_id, is_certified, organization, compose))

        conn.commit()
        conn.close()

        global scheduler
        scheduler = None   # 重置调度器以便重新加载数据

        return jsonify({
            'success': True,
            'message': f'成功选择 {len(selected_workers)} 名工人',
            'selected_count': len(selected_workers)
        })

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"select_workers 接口错误: {str(e)}")
        print(f"错误详情: {error_details}")
        return jsonify({
            'success': False,
            'error': str(e),
            'error_details': error_details,
            'message': '设置选中工人失败'
        }), 500


"""获取当前选中的工人"""
@worker_bp.route('/selected-workers', methods=['GET'])
def get_selected_workers():
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()

        # 查询选中的工人信息（增加 compose 字段）
        c.execute('''
            SELECT sw.id, sw.name, sw.worker_type_id, sw.is_certified, sw.organization
            FROM selected_workers sw
            ORDER BY sw.worker_type_id, sw.id
        ''')

        selected_workers = []
        for row in c.fetchall():
            selected_workers.append({
                'id': row[0],
                'name': row[1],
                'worker_type_id': row[2],
                'worker_type': row[2],          # 保持与现有代码一致
                'is_certified': bool(row[3]),
                'organization': row[4]             # 新增 compose 字段
            })

        conn.close()

        return jsonify({
            'success': True,
            'selected_workers': selected_workers,
            'total_count': len(selected_workers)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '获取选中工人失败'
        }), 500


"""添加工人信息到数据库"""
@worker_bp.route('/add-worker', methods=['POST'])
def add_worker():
    try:
        data = request.get_json()
        worker_type = data.get('worker_type')
        worker_name = data.get('worker_name')
        is_certified = data.get('is_certified')
        organization = data.get('organization', '')
        compose = data.get('compose', '')  
        skill_level = data.get('skill_level', 1)   

        if not worker_type or not worker_name:
            return jsonify({
                'success': False,
                'message': '工人工种和工人名称不能为空'
            }), 400

        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()

        # 插入工人到数据库（增加 compose 列）
        c.execute('''
            INSERT INTO workers (worker_type_id, name, is_certified, organization, compose, skill_level)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (worker_type, worker_name,is_certified, organization, compose, skill_level))

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': f'工人 {worker_name}({worker_type}) 添加成功'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '添加工人失败'
        }), 500


"""批量导入工人"""
@worker_bp.route('/batch-import-workers', methods=['POST'])
def batch_import_workers():
    try:
        data = request.get_json()
        workers_list = data.get('workers_list', [])

        if not workers_list:
            return jsonify({
                'success': False,
                'message': '工人列表不能为空'
            }), 400

        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()

        success_count = 0
        error_messages = []

        for worker in workers_list:
            try:
                worker_type = worker.get('worker_type')
                worker_name = worker.get('worker_name')
                certified = worker.get('is_certified', False)
                organization = worker.get('organization', '')
                compose = worker.get('compose', '')   
                skill_level = worker.get('skill_level', 1)   

                if not worker_type or not worker_name:
                    error_messages.append(f"工人工种和工人名称不能为空: {worker}")
                    continue

                # 插入工人到数据库（增加 compose 列）
                c.execute('''
                    INSERT INTO workers (worker_type_id, name, is_certified, organization, compose, skill_level)
                    VALUES (?, ?, ?, ?, ?,?)
                ''', (worker_type, worker_name, certified, organization, compose, skill_level))

                success_count += 1

            except Exception as e:
                error_messages.append(f"工人 {worker.get('worker_name', '未知')} 导入失败: {str(e)}")

        conn.commit()
        conn.close()

        global scheduler
        scheduler = None   # 重置调度器以便重新加载数据

        return jsonify({
            'success': True,
            'message': f'成功导入 {success_count} 个工人',
            'success_count': success_count,
            'error_count': len(error_messages),
            'errors': error_messages
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '批量导入工人失败'
        }), 500


"""删除工人信息"""
@worker_bp.route('/workers/<int:worker_id>', methods=['DELETE'])
def delete_worker(worker_id):
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()

        # 检查工人是否存在
        c.execute('SELECT name, worker_type_id FROM workers WHERE id = ?', (worker_id,))
        result = c.fetchone()
        if not result:
            conn.close()
            return jsonify({
                'success': False,
                'message': '工人不存在'
            }), 404

        worker_name = result[0]
        worker_type = result[1]

        # 删除工人
        c.execute('DELETE FROM workers WHERE id = ?', (worker_id,))

        conn.commit()
        conn.close()

        global scheduler
        scheduler = None   # 重置调度器以便重新加载数据

        return jsonify({
            'success': True,
            'message': f'工人 {worker_name}({worker_type}) 删除成功'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '删除工人失败'
        }), 500
# ========== 工人池管理 ==========
@worker_bp.route('/worker-team', methods=['GET'])
def get_worker_team():
    """获取工人池数据（普工、技工、高级技工的总人数和已分配人数）"""
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        
        c.execute('SELECT workerteam_type, total, assigned FROM worker_team')
        rows = c.fetchall()
        conn.close()
        
        result = []
        for row in rows:
            result.append({
                'type': row[0],
                'total': row[1],
                'assigned': row[2],
                'available': row[1] - row[2]
            })
        
        return jsonify({
            'success': True,
            'data': result
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '获取工人池数据失败'
        }), 500

@worker_bp.route('/worker-team', methods=['PUT'])
def update_worker_team():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '缺少请求体'}), 400
        
        # 支持的工种类型
        allowed_types = ['普工', '技工', '高级技工']
        updates = {}
        for t in allowed_types:
            if t in data:
                new_assigned = data[t]
                if not isinstance(new_assigned, int) or new_assigned < 0:
                    return jsonify({'success': False, 'message': f'{t} 的分配人数必须是 ≥0 的整数'}), 400
                updates[t] = new_assigned
        
        if not updates:
            return jsonify({'success': False, 'message': '没有提供任何有效工种'}), 400
        
        # 开启事务，检查总数限制
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        
        try:
            for t, new_assigned in updates.items():
                # 查询当前总数
                c.execute('SELECT total FROM worker_team WHERE workerteam_type = ?', (t,))
                row = c.fetchone()
                if not row:
                    conn.rollback()
                    return jsonify({'success': False, 'message': f'工种 {t} 不存在'}), 404
                total = row[0]
                if new_assigned > total:
                    conn.rollback()
                    return jsonify({'success': False, 'message': f'{t} 的分配人数不能超过总人数 {total}'}), 400
                # 更新
                c.execute('UPDATE worker_team SET assigned = ? WHERE workerteam_type = ?', (new_assigned, t))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': '工人池分配更新成功'
            })
        
        except Exception as e:
            conn.rollback()
            conn.close()
            raise e
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '更新工人池数据失败'
        }), 500
