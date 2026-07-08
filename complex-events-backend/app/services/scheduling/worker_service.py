from typing import Any
from app.services.database_service.sqlite_service import get_connection


scheduler = None


class WorkerService:

    @staticmethod
    def get_all() -> list[dict[str, Any]]:
        conn = get_connection()
        c = conn.cursor()
        c.execute('''
            SELECT id, name, worker_type_id, is_certified, organization, emp_id, compose
            FROM workers
            ORDER BY id
        ''')
        rows = c.fetchall()
        conn.close()
        return [
            {
                'id': row[0],
                'name': row[1],
                'worker_type_id': row[2],
                'worker_type': row[2],
                'is_certified': row[3],
                'organization': row[4],
                'emp_id': row[5],
                'compose': row[6],
            }
            for row in rows
        ]

    @staticmethod
    def get_types() -> list[dict[str, Any]]:
        conn = get_connection()
        c = conn.cursor()
        c.execute('''
            SELECT id, name, description, requires_certification, created_at, price
            FROM worker_types
            ORDER BY id
        ''')
        rows = c.fetchall()
        conn.close()
        return [
            {
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'requires_certification': bool(row[3]),
                'created_at': row[4],
                'price': row[5],
            }
            for row in rows
        ]

    @staticmethod
    def select(worker_ids: list[int]) -> dict[str, Any]:
        conn = get_connection()
        c = conn.cursor()
        placeholders = ','.join('?' * len(worker_ids))
        c.execute(f'''
            SELECT id, name, worker_type_id, is_certified, organization, compose
            FROM workers
            WHERE id IN ({placeholders})
        ''', worker_ids)
        selected = c.fetchall()
        if len(selected) != len(worker_ids):
            conn.close()
            raise ValueError('部分工人ID不存在')
        c.execute('DELETE FROM selected_workers')
        for w in selected:
            c.execute('''
                INSERT INTO selected_workers (id, name, worker_type_id, is_certified, organization, compose)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', w)
        conn.commit()
        conn.close()
        global scheduler
        scheduler = None
        return {'selected_count': len(selected)}

    @staticmethod
    def get_selected() -> list[dict[str, Any]]:
        conn = get_connection()
        c = conn.cursor()
        c.execute('''
            SELECT sw.id, sw.name, sw.worker_type_id, sw.is_certified, sw.organization
            FROM selected_workers sw
            ORDER BY sw.worker_type_id, sw.id
        ''')
        rows = c.fetchall()
        conn.close()
        return [
            {
                'id': row[0],
                'name': row[1],
                'worker_type_id': row[2],
                'worker_type': row[2],
                'is_certified': bool(row[3]),
                'organization': row[4],
            }
            for row in rows
        ]

    @staticmethod
    def add(worker_type: str, worker_name: str, is_certified: bool,
            organization: str, compose: str, skill_level: int = 1) -> None:
        conn = get_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO workers (worker_type_id, name, is_certified, organization, compose, skill_level)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (worker_type, worker_name, is_certified, organization, compose, skill_level))
        conn.commit()
        conn.close()

    @staticmethod
    def batch_import(workers_list: list[dict[str, Any]]) -> dict[str, Any]:
        conn = get_connection()
        c = conn.cursor()
        success_count = 0
        errors = []
        for worker in workers_list:
            try:
                worker_type = worker.get('worker_type')
                worker_name = worker.get('worker_name')
                certified = worker.get('is_certified', False)
                organization = worker.get('organization', '')
                compose = worker.get('compose', '')
                skill_level = worker.get('skill_level', 1)
                if not worker_type or not worker_name:
                    errors.append(f"工人工种和工人名称不能为空: {worker}")
                    continue
                c.execute('''
                    INSERT INTO workers (worker_type_id, name, is_certified, organization, compose, skill_level)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (worker_type, worker_name, certified, organization, compose, skill_level))
                success_count += 1
            except Exception as e:
                errors.append(f"工人 {worker.get('worker_name', '未知')} 导入失败: {str(e)}")
        conn.commit()
        conn.close()
        global scheduler
        scheduler = None
        return {'success_count': success_count, 'error_count': len(errors), 'errors': errors}

    @staticmethod
    def delete(worker_id: int) -> str:
        conn = get_connection()
        c = conn.cursor()
        c.execute('SELECT name, worker_type_id FROM workers WHERE id = ?', (worker_id,))
        result = c.fetchone()
        if not result:
            conn.close()
            raise ValueError('工人不存在')
        worker_name = result[0]
        worker_type = result[1]
        c.execute('DELETE FROM workers WHERE id = ?', (worker_id,))
        conn.commit()
        conn.close()
        global scheduler
        scheduler = None
        return f'{worker_name}({worker_type})'

    @staticmethod
    def get_team() -> list[dict[str, Any]]:
        conn = get_connection()
        c = conn.cursor()
        c.execute('SELECT workerteam_type, total, assigned FROM worker_team')
        rows = c.fetchall()
        conn.close()
        return [
            {
                'type': row[0],
                'total': row[1],
                'assigned': row[2],
                'available': row[1] - row[2],
            }
            for row in rows
        ]

    @staticmethod
    def update_team(updates: dict[str, int]) -> None:
        conn = get_connection()
        c = conn.cursor()
        try:
            for t, new_assigned in updates.items():
                c.execute('SELECT total FROM worker_team WHERE workerteam_type = ?', (t,))
                row = c.fetchone()
                if not row:
                    raise ValueError(f'工种 {t} 不存在')
                if new_assigned > row[0]:
                    raise ValueError(f'{t} 的分配人数不能超过总人数 {row[0]}')
                c.execute('UPDATE worker_team SET assigned = ? WHERE workerteam_type = ?', (new_assigned, t))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
