from flask import request
from app.models import Result
from app.services.scheduling.worker_service import WorkerService
from . import worker_bp


@worker_bp.route('/workers', methods=['GET'])
def get_workers():
    try:
        workers = WorkerService.get_all()
        return Result.success(data={
            'workers': workers,
            'total_count': len(workers),
        })
    except Exception as e:
        print("!!! 获取工人接口报错了 !!!:", str(e))
        return Result.fail(message='获取工人信息失败')


@worker_bp.route('/worker-types', methods=['GET'])
def get_worker_types():
    try:
        data = WorkerService.get_types()
        return Result.success(data=data)
    except Exception as e:
        return Result.fail(message='获取工种信息失败')


@worker_bp.route('/select-workers', methods=['POST'])
def select_workers():
    try:
        data = request.get_json()
        selected_worker_ids = data.get('selected_worker_ids', [])
        print(selected_worker_ids)
        if not selected_worker_ids:
            return Result.fail(message='请选择至少一个工人')
        result = WorkerService.select(selected_worker_ids)
        return Result.success(data=result)
    except ValueError as e:
        return Result.fail(message=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Result.fail(message='设置选中工人失败')


@worker_bp.route('/selected-workers', methods=['GET'])
def get_selected_workers():
    try:
        selected = WorkerService.get_selected()
        return Result.success(data={
            'selected_workers': selected,
            'total_count': len(selected),
        })
    except Exception as e:
        return Result.fail(message='获取选中工人失败')


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
            return Result.fail(message='工人工种和工人名称不能为空')

        WorkerService.add(worker_type, worker_name, is_certified, organization, compose, skill_level)
        return Result.success(data={'message': f'工人 {worker_name}({worker_type}) 添加成功'})
    except Exception as e:
        return Result.fail(message='添加工人失败')


@worker_bp.route('/batch-import-workers', methods=['POST'])
def batch_import_workers():
    try:
        data = request.get_json()
        workers_list = data.get('workers_list', [])
        if not workers_list:
            return Result.fail(message='工人列表不能为空')
        result = WorkerService.batch_import(workers_list)
        return Result.success(data=result)
    except Exception as e:
        return Result.fail(message='批量导入工人失败')


@worker_bp.route('/workers/<int:worker_id>', methods=['DELETE'])
def delete_worker(worker_id):
    try:
        name = WorkerService.delete(worker_id)
        return Result.success(data={'message': f'工人 {name} 删除成功'})
    except ValueError as e:
        return Result.fail(message=str(e))
    except Exception as e:
        return Result.fail(message='删除工人失败')


@worker_bp.route('/worker-team', methods=['GET'])
def get_worker_team():
    try:
        data = WorkerService.get_team()
        return Result.success(data=data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Result.fail(message='获取工人池数据失败')


@worker_bp.route('/worker-team', methods=['PUT'])
def update_worker_team():
    try:
        data = request.get_json()
        if not data:
            return Result.fail(message='缺少请求体')

        allowed_types = ['普工', '技工', '高级技工']
        updates = {}
        for t in allowed_types:
            if t in data:
                new_assigned = data[t]
                if not isinstance(new_assigned, int) or new_assigned < 0:
                    return Result.fail(message=f'{t} 的分配人数必须是 ≥0 的整数')
                updates[t] = new_assigned

        if not updates:
            return Result.fail(message='没有提供任何有效工种')

        WorkerService.update_team(updates)
        return Result.success(data={'message': '工人池分配更新成功'})
    except ValueError as e:
        return Result.fail(message=str(e))
    except Exception as e:
        return Result.fail(message='更新工人池数据失败')
