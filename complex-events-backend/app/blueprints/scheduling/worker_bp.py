"""Worker scheduling & CRUD API blueprint."""
from flask import Blueprint, request
import datetime
from app.models import Result
from app.utils import get_db_connection

worker_bp = Blueprint('scheduling_worker', __name__)


@worker_bp.route('/workers', methods=['GET'])
def get_workers():
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute('''
                SELECT w.id, w.name, w.worker_type_id, w.is_certified,
                       w.organization, w.emp_id, w.compose, w.status,
                       COALESCE(wt.name, w.worker_type_id) AS worker_type_name
                FROM workers w
                LEFT JOIN worker_types wt ON w.worker_type_id = wt.id
                ORDER BY w.id
            ''')
            workers = []
            for row in c.fetchall():
                workers.append({
                    'id': row[0], 'name': row[1], 'worker_type_id': row[2],
                    'worker_type': row[8], 'is_certified': row[3],
                    'organization': row[4], 'emp_id': row[5],
                    'compose': row[6], 'status': row[7]
                })
        return Result.success(
            data={"workers": workers, "total_count": len(workers)},
            message="查询成功",
        )
    except Exception as e:
        return Result.fail(message=f"获取工人信息失败: {str(e)}")


@worker_bp.route('/worker-types', methods=['GET'])
def get_worker_types():
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute('SELECT id, name, description, requires_certification, created_at FROM worker_types ORDER BY id')
            worker_types = []
            for row in c.fetchall():
                worker_types.append({
                    'id': row[0], 'name': row[1], 'description': row[2],
                    'requires_certification': bool(row[3]), 'created_at': row[4]
                })
        return Result.success(data=worker_types, message="查询成功")
    except Exception as e:
        return Result.fail(message=f"获取工种信息失败: {str(e)}")


@worker_bp.route('/select-workers', methods=['POST'])
def select_workers():
    try:
        data = request.get_json()
        selected_worker_ids = data.get('selected_worker_ids', [])
        if not selected_worker_ids:
            return Result.fail(message="请选择至少一个工人")

        with get_db_connection() as conn:
            c = conn.cursor()
            placeholders = ','.join('?' * len(selected_worker_ids))
            c.execute(f'''
                SELECT id, name, worker_type_id, is_certified, organization
                FROM workers WHERE id IN ({placeholders})
            ''', selected_worker_ids)
            selected_workers = c.fetchall()
            if len(selected_workers) != len(selected_worker_ids):
                return Result.fail(message="部分工人ID不存在")

            c.execute('DELETE FROM selected_workers')
            for worker in selected_workers:
                c.execute(
                    'INSERT INTO selected_workers (id, name, worker_type_id, is_certified, organization) VALUES (?, ?, ?, ?, ?)',
                    worker,
                )
        return Result.success(message=f"成功选择 {len(selected_workers)} 名工人",
                             data={"selected_count": len(selected_workers)})
    except Exception as e:
        return Result.fail(message=f"设置选中工人失败: {str(e)}")


@worker_bp.route('/selected-workers', methods=['GET'])
def get_selected_workers():
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute('SELECT sw.id, sw.name, sw.worker_type_id, sw.is_certified, sw.organization FROM selected_workers sw ORDER BY sw.worker_type_id, sw.id')
            selected_workers = []
            for row in c.fetchall():
                selected_workers.append({
                    'id': row[0], 'name': row[1], 'worker_type_id': row[2],
                    'worker_type': row[2], 'is_certified': bool(row[3]), 'organization': row[4]
                })
        return Result.success(
            data={"selected_workers": selected_workers, "total_count": len(selected_workers)},
            message="查询成功",
        )
    except Exception as e:
        return Result.fail(message=f"获取选中工人失败: {str(e)}")


@worker_bp.route('/add-worker', methods=['POST'])
def add_worker():
    try:
        data = request.get_json()
        worker_type = data.get('worker_type')
        worker_name = data.get('worker_name')
        is_certified = data.get('is_certified')
        organization = data.get('organization', '')
        compose = data.get('compose', '')

        if not worker_type or not worker_name:
            return Result.fail(message="工人工种和工人名称不能为空")

        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute(
                'INSERT INTO workers (worker_type_id, name, is_certified, organization, compose) VALUES (?, ?, ?, ?, ?)',
                (worker_type, worker_name, is_certified, organization, compose),
            )
        return Result.success(message=f"工人 {worker_name}({worker_type}) 添加成功")
    except Exception as e:
        return Result.fail(message=f"添加工人失败: {str(e)}")


@worker_bp.route('/batch-import-workers', methods=['POST'])
def batch_import_workers():
    try:
        data = request.get_json()
        workers_list = data.get('workers_list', [])
        if not workers_list:
            return Result.fail(message="工人列表不能为空")

        success_count, error_messages = 0, []
        with get_db_connection() as conn:
            c = conn.cursor()
            for worker in workers_list:
                try:
                    worker_type = worker.get('worker_type')
                    worker_name = worker.get('worker_name')
                    certified = worker.get('is_certified', False)
                    organization = worker.get('organization', '')
                    compose = worker.get('compose', '')
                    if not worker_type or not worker_name:
                        error_messages.append(f"工人工种和工人名称不能为空: {worker}")
                        continue
                    c.execute(
                        'INSERT INTO workers (worker_type_id, name, is_certified, organization, compose) VALUES (?, ?, ?, ?, ?)',
                        (worker_type, worker_name, certified, organization, compose),
                    )
                    success_count += 1
                except Exception as e:
                    error_messages.append(f"工人 {worker.get('worker_name', '未知')} 导入失败: {str(e)}")

        return Result.success(
            data={"success_count": success_count, "error_count": len(error_messages), "errors": error_messages},
            message=f"成功导入 {success_count} 个工人",
        )
    except Exception as e:
        return Result.fail(message=f"批量导入工人失败: {str(e)}")


@worker_bp.route('/workers/<int:worker_id>', methods=['DELETE'])
def delete_worker(worker_id):
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute('SELECT name, worker_type_id FROM workers WHERE id = ?', (worker_id,))
            row = c.fetchone()
            if not row:
                return Result.fail(message="工人不存在")
            c.execute('DELETE FROM workers WHERE id = ?', (worker_id,))
        return Result.success(message=f"工人 {row[0]}({row[1]}) 删除成功")
    except Exception as e:
        return Result.fail(message=f"删除工人失败: {str(e)}")


@worker_bp.route('/worker-team', methods=['GET'])
def get_worker_team():
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute('SELECT workerteam_type, total, assigned FROM worker_team')
            rows = c.fetchall()
            result = []
            for row in rows:
                result.append({'type': row[0], 'total': row[1], 'assigned': row[2], 'available': row[1] - row[2]})
        return Result.success(data=result, message="查询成功")
    except Exception as e:
        return Result.fail(message=f"获取工人池数据失败: {str(e)}")


@worker_bp.route('/worker-team', methods=['PUT'])
def update_worker_team():
    try:
        data = request.get_json()
        if not data:
            return Result.fail(message="缺少请求体")

        allowed_types = ['普工', '技工', '高级技工']
        updates = {}
        for t in allowed_types:
            if t in data:
                new_assigned = data[t]
                if not isinstance(new_assigned, int) or new_assigned < 0:
                    return Result.fail(message=f'{t} 的分配人数必须是 ≥0 的整数')
                updates[t] = new_assigned
        if not updates:
            return Result.fail(message="没有提供任何有效工种")

        with get_db_connection() as conn:
            c = conn.cursor()
            for t, new_assigned in updates.items():
                c.execute('SELECT total FROM worker_team WHERE workerteam_type = ?', (t,))
                row = c.fetchone()
                if not row:
                    return Result.fail(message=f'工种 {t} 不存在')
                if new_assigned > row[0]:
                    return Result.fail(message=f'{t} 的分配人数不能超过总人数 {row[0]}')
                c.execute('UPDATE worker_team SET assigned = ? WHERE workerteam_type = ?', (new_assigned, t))
        return Result.success(message="工人池分配更新成功")
    except Exception as e:
        return Result.fail(message=f"更新工人池数据失败: {str(e)}")
