MOCK_EQUIPMENT_CATEGORIES = [
    {"value": "动设备", "label": "动设备", "count": 5},
    {"value": "静设备", "label": "静设备", "count": 4},
    {"value": "电气设备", "label": "电气设备", "count": 3},
    {"value": "管道设备", "label": "管道设备", "count": 2},
]

MOCK_EQUIPMENT_TYPES = {
    "动设备": ["离心泵", "压缩机", "风机", "齿轮泵", "真空泵"],
    "静设备": ["储罐", "换热器", "反应器", "塔器"],
    "电气设备": ["变压器", "配电柜", "电动机"],
    "管道设备": ["阀门", "管道"]
}

MOCK_EQUIPMENT_INSTANCES = {
    "动设备|离心泵": [
        {"id": 1, "name": "P01 离心泵"},
        {"id": 2, "name": "P02 离心泵"},
    ],
    "动设备|压缩机": [
        {"id": 3, "name": "C01 压缩机"},
    ],
    "动设备|风机": [
        {"id": 4, "name": "F01 风机"},
    ],
    "动设备|齿轮泵": [
        {"id": 5, "name": "G01 齿轮泵"},
    ],
    "静设备|储罐": [
        {"id": 6, "name": "TK01 储罐"},
        {"id": 7, "name": "TK02 储罐"},
    ],
    "静设备|换热器": [
        {"id": 8, "name": "E01 换热器"},
    ],
    "静设备|反应器": [
        {"id": 9, "name": "R01 反应器"},
    ],
    "电气设备|变压器": [
        {"id": 10, "name": "T01 变压器"},
    ],
    "电气设备|配电柜": [
        {"id": 11, "name": "PC01 配电柜"},
        {"id": 12, "name": "PC02 配电柜"},
    ],
    "管道设备|阀门": [
        {"id": 13, "name": "V01 阀门"},
        {"id": 14, "name": "V02 阀门"},
    ],
}

MOCK_PROCESSES = [
    {"id": 1, "equipment_id": 1, "equipment_name": "P01 离心泵", "equipment_category": "动设备", "equipment_type_name": "离心泵", "process_name": "离心泵检修", "status": "on_hold", "estimated_hours": 8, "scheduled_start_time": "2026-03-12 08:00:00", "scheduled_end_time": "2026-03-12 16:00:00", "description": "定期检修离心泵，检查轴承和密封", "is_milestone": True},
    {"id": 2, "equipment_id": 2, "equipment_name": "P02 离心泵", "equipment_category": "动设备", "equipment_type_name": "离心泵", "process_name": "离心泵保养", "status": "pending", "estimated_hours": 4, "scheduled_start_time": "2026-03-13 08:00:00", "scheduled_end_time": "2026-03-13 12:00:00", "description": "日常保养，更换润滑油", "is_milestone": False},
    {"id": 3, "equipment_id": 3, "equipment_name": "C01 压缩机", "equipment_category": "动设备", "equipment_type_name": "压缩机", "process_name": "压缩机大修", "status": "completed", "estimated_hours": 24, "scheduled_start_time": "2026-03-10 08:00:00", "scheduled_end_time": "2026-03-11 08:00:00", "description": "全面大修，更换转子和轴承", "is_milestone": True},
    {"id": 4, "equipment_id": 6, "equipment_name": "TK01 储罐", "equipment_category": "静设备", "equipment_type_name": "储罐", "process_name": "储罐清洗", "status": "on_hold", "estimated_hours": 12, "scheduled_start_time": "2026-03-14 08:00:00", "scheduled_end_time": "2026-03-14 20:00:00", "description": "内部清洗和防腐处理", "is_milestone": False},
    {"id": 5, "equipment_id": 8, "equipment_name": "E01 换热器", "equipment_category": "静设备", "equipment_type_name": "换热器", "process_name": "换热器检修", "status": "pending", "estimated_hours": 6, "scheduled_start_time": "2026-03-15 08:00:00", "scheduled_end_time": "2026-03-15 14:00:00", "description": "检查换热管，清理污垢", "is_milestone": False},
    {"id": 6, "equipment_id": 9, "equipment_name": "R01 反应器", "equipment_category": "静设备", "equipment_type_name": "反应器", "process_name": "反应器维护", "status": "in_progress", "estimated_hours": 16, "scheduled_start_time": "2026-03-11 08:00:00", "scheduled_end_time": "2026-03-12 00:00:00", "description": "催化剂更换和设备检查", "is_milestone": True},
    {"id": 7, "equipment_id": 10, "equipment_name": "T01 变压器", "equipment_category": "电气设备", "equipment_type_name": "变压器", "process_name": "变压器检测", "status": "on_hold", "estimated_hours": 4, "scheduled_start_time": "2026-03-16 08:00:00", "scheduled_end_time": "2026-03-16 12:00:00", "description": "绝缘测试和油质分析", "is_milestone": False},
    {"id": 8, "equipment_id": 11, "equipment_name": "PC01 配电柜", "equipment_category": "电气设备", "equipment_type_name": "配电柜", "process_name": "配电柜检修", "status": "rejected", "estimated_hours": 2, "scheduled_start_time": "2026-03-17 08:00:00", "scheduled_end_time": "2026-03-17 10:00:00", "description": "检查接线和保护装置", "is_milestone": False, "approval_comments": "需要补充材料"},
    {"id": 9, "equipment_id": 13, "equipment_name": "V01 阀门", "equipment_category": "管道设备", "equipment_type_name": "阀门", "process_name": "阀门更换", "status": "pending", "estimated_hours": 3, "scheduled_start_time": "2026-03-18 08:00:00", "scheduled_end_time": "2026-03-18 11:00:00", "description": "更换损坏的阀门", "is_milestone": False},
    {"id": 10, "equipment_id": 4, "equipment_name": "F01 风机", "equipment_category": "动设备", "equipment_type_name": "风机", "process_name": "风机平衡", "status": "in_progress", "estimated_hours": 6, "scheduled_start_time": "2026-03-12 08:00:00", "scheduled_end_time": "2026-03-12 14:00:00", "description": "动平衡测试和校正", "is_milestone": False},
    {"id": 11, "equipment_id": 5, "equipment_name": "G01 齿轮泵", "equipment_category": "动设备", "equipment_type_name": "齿轮泵", "process_name": "齿轮泵维修", "status": "on_hold", "estimated_hours": 5, "scheduled_start_time": "2026-03-19 08:00:00", "scheduled_end_time": "2026-03-19 13:00:00", "description": "修复齿轮磨损问题", "is_milestone": False},
    {"id": 12, "equipment_id": 7, "equipment_name": "TK02 储罐", "equipment_category": "静设备", "equipment_type_name": "储罐", "process_name": "储罐检测", "status": "completed", "estimated_hours": 8, "scheduled_start_time": "2026-03-08 08:00:00", "scheduled_end_time": "2026-03-08 16:00:00", "description": "壁厚检测和安全评估", "is_milestone": False},
]

MOCK_WORKERS = [
    {"id": 1, "name": "张三", "role": "高级工程师", "status": "工作中", "organization": "维修部", "skill_level": "高级", "tasks": [{"task_id": 1, "task_name": "离心泵检修", "equipment": "P01 离心泵", "start_time": "第1天 08:00", "end_time": "第1天 16:00", "status": "进行中"}, {"task_id": 6, "task_name": "反应器维护", "equipment": "R01 反应器", "start_time": "第1天 08:00", "end_time": "第2天 00:00", "status": "进行中"}]},
    {"id": 2, "name": "李四", "role": "技术员", "status": "工作中", "organization": "维修部", "skill_level": "中级", "tasks": [{"task_id": 2, "task_name": "离心泵保养", "equipment": "P02 离心泵", "start_time": "第2天 08:00", "end_time": "第2天 12:00", "status": "进行中"}]},
    {"id": 3, "name": "王五", "role": "初级工程师", "status": "空闲中", "organization": "电气部", "skill_level": "初级", "tasks": []},
    {"id": 4, "name": "赵六", "role": "高级工程师", "status": "工作中", "organization": "工艺部", "skill_level": "高级", "tasks": [{"task_id": 4, "task_name": "储罐清洗", "equipment": "TK01 储罐", "start_time": "第3天 08:00", "end_time": "第3天 20:00", "status": "进行中"}]},
    {"id": 5, "name": "孙七", "role": "技术员", "status": "空闲中", "organization": "管道部", "skill_level": "中级", "tasks": []},
    {"id": 6, "name": "周八", "role": "设备管理员", "status": "工作中", "organization": "设备部", "skill_level": "中级", "tasks": [{"task_id": 7, "task_name": "变压器检测", "equipment": "T01 变压器", "start_time": "第5天 08:00", "end_time": "第5天 12:00", "status": "进行中"}]},
]

MOCK_ORDERS = [
    {"work_order_id": "WO001", "order_number": "WO-2024-001", "process_name": "离心泵检修", "status": "on_hold", "work_order_status": "on_hold", "equipment_id": "E001", "equipment_name": "P01 离心泵", "priority": "高"},
    {"work_order_id": "WO002", "order_number": "WO-2024-002", "process_name": "压缩机大修", "status": "completed", "work_order_status": "completed", "equipment_id": "E003", "equipment_name": "C01 压缩机", "priority": "高"},
    {"work_order_id": "WO003", "order_number": "WO-2024-003", "process_name": "储罐清洗", "status": "on_hold", "work_order_status": "on_hold", "equipment_id": "E006", "equipment_name": "TK01 储罐", "priority": "中"},
    {"work_order_id": "WO004", "order_number": "WO-2024-004", "process_name": "变压器检测", "status": "pending", "work_order_status": "pending", "equipment_id": "E010", "equipment_name": "T01 变压器", "priority": "低"},
]

MOCK_MATERIALS = [
    {"material_name": "润滑油", "initial_stock": 100.0, "current_stock": 70.0, "unit": "升"},
    {"material_name": "密封件", "initial_stock": 50.0, "current_stock": 35.0, "unit": "个"},
    {"material_name": "轴承", "initial_stock": 30.0, "current_stock": 20.0, "unit": "套"},
    {"material_name": "垫片", "initial_stock": 200.0, "current_stock": 150.0, "unit": "片"},
    {"material_name": "螺栓", "initial_stock": 500.0, "current_stock": 400.0, "unit": "个"},
]

MOCK_TOOLS = [
    {"tool_id": "TL001", "tool_name": "扳手组", "tool_type": "手动工具", "usage_status": "占用", "usage_tasks": [{"task_name": "离心泵检修"}]},
    {"tool_id": "TL002", "tool_name": "万用表", "tool_type": "测量工具", "usage_status": "空闲", "usage_tasks": []},
    {"tool_id": "TL003", "tool_name": "起重机", "tool_type": "起重设备", "usage_status": "占用", "usage_tasks": [{"task_name": "压缩机大修"}]},
    {"tool_id": "TL004", "tool_name": "液压扳手", "tool_type": "动力工具", "usage_status": "空闲", "usage_tasks": []},
    {"tool_id": "TL005", "tool_name": "探伤仪", "tool_type": "检测设备", "usage_status": "空闲", "usage_tasks": []},
]

def get_mock_equipment_info():
    return {
        "categories": MOCK_EQUIPMENT_CATEGORIES,
        "types": MOCK_EQUIPMENT_TYPES,
        "instances": MOCK_EQUIPMENT_INSTANCES
    }

def get_mock_process_list(filters=None):
    processes = MOCK_PROCESSES
    if filters:
        if filters.get('equipment_category'):
            processes = [p for p in processes if p['equipment_category'] == filters['equipment_category']]
        if filters.get('equipment_type'):
            processes = [p for p in processes if p['equipment_type_name'] == filters['equipment_type']]
        if filters.get('equipment_id'):
            processes = [p for p in processes if p['equipment_id'] == int(filters['equipment_id'])]
        if filters.get('status'):
            processes = [p for p in processes if p['status'] == filters['status']]
    return {"total": len(processes), "list": processes}

def get_mock_process_detail(process_id):
    for p in MOCK_PROCESSES:
        if p['id'] == process_id:
            return p
    return None

def get_mock_workers():
    return {"success": True, "worker_status": MOCK_WORKERS}

def get_mock_orders():
    return {"success": True, "data": MOCK_ORDERS}

def get_mock_materials():
    return {"success": True, "material_inventory": MOCK_MATERIALS}

def get_mock_tools():
    return {"success": True, "maintenance_tool_status": MOCK_TOOLS}
