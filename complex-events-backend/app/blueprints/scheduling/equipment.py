from flask import request
from app.models import Result
from app.services.scheduling.equipment_service import EquipmentService
from . import equipment_bp


@equipment_bp.route('/equipment-categories', methods=['GET'])
def get_equipment_categories():
    try:
        data = EquipmentService.get_categories()
        return Result.success(data=data)
    except Exception as e:
        return Result.fail(message=str(e))


@equipment_bp.route('/equipment-types-with-category', methods=['GET'])
def get_equipment_types_with_category():
    try:
        data = EquipmentService.get_types_with_category()
        return Result.success(data=data)
    except Exception as e:
        return Result.fail(message=str(e))


@equipment_bp.route('/equipment-types', methods=['GET'])
def get_equipment_types():
    try:
        data = EquipmentService.get_types()
        return Result.success(data=data)
    except Exception as e:
        return Result.fail(message=str(e))


@equipment_bp.route('/select-equipments', methods=['POST'])
def select_equipments():
    try:
        data = request.get_json()
        selected_ids = data.get('selected_equipment_ids', [])
        if not selected_ids:
            return Result.fail(message='请选择至少一个设备')
        result = EquipmentService.select(selected_ids)
        return Result.success(data=result)
    except ValueError as e:
        return Result.fail(message=str(e))
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"select_equipments 接口错误: {str(e)}")
        print(f"错误详情: {error_details}")
        return Result.fail(message='设置选中设备失败')


@equipment_bp.route('/selected-equipments', methods=['GET'])
def get_selected_equipments():
    try:
        selected = EquipmentService.get_selected()
        return Result.success(data={
            'selected_equipments': selected,
            'total_count': len(selected),
        })
    except Exception as e:
        return Result.fail(message='获取选中设备失败')


@equipment_bp.route('/equipment-instances', methods=['GET'])
def get_equipment_instances():
    try:
        instances = EquipmentService.get_instances()
        return Result.success(data={
            'data': instances,
            'total_count': len(instances),
        })
    except Exception as e:
        return Result.fail(message='获取设备实例失败')


@equipment_bp.route('/equipment-instances/by-type/<string:equipment_type_id>', methods=['GET'])
def get_equipment_instances_by_type(equipment_type_id):
    try:
        instances, type_name = EquipmentService.get_instances_by_type(equipment_type_id)
        return Result.success(data={
            'data': instances,
            'total_count': len(instances),
            'equipment_type_name': type_name,
        })
    except ValueError as e:
        return Result.fail(message=str(e))
    except Exception as e:
        return Result.fail(message='根据设备类型查询设备实例失败')


@equipment_bp.route('/add-equipment', methods=['POST'])
def add_equipment():
    try:
        data = request.get_json()
        equipment_type_id = data.get('equipment_type_id')
        equipment_name = data.get('equipment_name')
        equipment_category = data.get('equipment_category')
        if not equipment_type_id or not equipment_name:
            return Result.fail(message='设备种类和设备名称不能为空')
        EquipmentService.add(equipment_type_id, equipment_name, equipment_category)
        return Result.success(data={'message': f'设备 {equipment_name} 添加成功'})
    except Exception as e:
        return Result.fail(message='添加设备失败')


@equipment_bp.route('/batch-import-equipment', methods=['POST'])
def batch_import_equipment():
    try:
        data = request.get_json()
        equipment_list = data.get('equipment_list', [])
        if not equipment_list:
            return Result.fail(message='设备列表不能为空')
        result = EquipmentService.batch_import(equipment_list)
        return Result.success(data=result)
    except Exception as e:
        return Result.fail(message='批量导入设备失败')


@equipment_bp.route('/equipment-instances/<int:equipment_id>', methods=['DELETE'])
def delete_equipment_instance(equipment_id):
    try:
        name = EquipmentService.delete(equipment_id)
        return Result.success(data={'message': f'设备 {name} 删除成功'})
    except ValueError as e:
        return Result.fail(message=str(e))
    except Exception as e:
        return Result.fail(message='删除设备失败')


@equipment_bp.route('/equipment-instances/<int:equipment_id>', methods=['GET'])
def get_equipment_instance(equipment_id):
    try:
        instance = EquipmentService.get_instance(equipment_id)
        if not instance:
            return Result.fail(message='设备不存在')
        return Result.success(data={'equipment_instance': instance})
    except Exception as e:
        return Result.fail(message='获取设备信息失败')
