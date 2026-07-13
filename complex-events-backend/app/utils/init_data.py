import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app import create_app
from app.services.database_service import get_collection, _ensure_current_app


mock_processes = [
    {
        "id": 1,
        "equipment_id": "R-101",
        "equipment_name": "R-101 反应釜",
        "equipment_category": "生产设备",
        "equipment_type_name": "反应釜",
        "process_name": "设备停机",
        "status": "completed",
        "workers": {"操作工": ["张三"], "技术员": ["李四"]},
        "estimated_hours": 4,
        "scheduled_start_time": "2026-07-01 08:00",
        "scheduled_end_time": "2026-07-01 12:00",
        "description": "按照操作规程进行设备停机操作，关闭进料阀、出料阀，切断电源",
        "is_milestone": True,
        "material_requirements": {},
        "tools_requirements": {"扳手": {"quantity": 2, "unit": "把"}, "螺丝刀": {"quantity": 1, "unit": "把"}},
        "approval_comments": "已完成设备停机，确认设备状态正常"
    },
    {
        "id": 2,
        "equipment_id": "R-101",
        "equipment_name": "R-101 反应釜",
        "equipment_category": "生产设备",
        "equipment_type_name": "反应釜",
        "process_name": "安全隔离",
        "status": "completed",
        "workers": {"操作工": ["张三"], "安全员": ["王五"]},
        "estimated_hours": 6,
        "scheduled_start_time": "2026-07-01 12:00",
        "scheduled_end_time": "2026-07-01 18:00",
        "description": "执行LOTO隔离程序，挂设安全警示牌，确保设备与系统完全隔离",
        "is_milestone": True,
        "material_requirements": {},
        "tools_requirements": {"隔离锁": {"quantity": 5, "unit": "把"}},
        "approval_comments": "隔离完成，安全措施到位"
    },
    {
        "id": 3,
        "equipment_id": "R-101",
        "equipment_name": "R-101 反应釜",
        "equipment_category": "生产设备",
        "equipment_type_name": "反应釜",
        "process_name": "物料清理",
        "status": "current",
        "workers": {"操作工": ["张三"], "技术员": ["李四"]},
        "estimated_hours": 8,
        "scheduled_start_time": "2026-07-02 08:00",
        "scheduled_end_time": "2026-07-02 16:00",
        "description": "清空反应釜内残留物料，进行氮气置换，检测氧气含量",
        "is_milestone": False,
        "material_requirements": {"氮气": {"quantity": 50, "unit": "m³"}},
        "tools_requirements": {"检测仪": {"quantity": 2, "unit": "台"}},
        "approval_comments": ""
    },
    {
        "id": 4,
        "equipment_id": "R-101",
        "equipment_name": "R-101 反应釜",
        "equipment_category": "生产设备",
        "equipment_type_name": "反应釜",
        "process_name": "设备解体",
        "status": "on_hold",
        "workers": {"维修工": ["赵六"], "技术员": ["李四"]},
        "estimated_hours": 12,
        "scheduled_start_time": "2026-07-03 08:00",
        "scheduled_end_time": "2026-07-03 20:00",
        "description": "拆除设备外部管道、仪表，打开人孔，准备内部检修",
        "is_milestone": True,
        "material_requirements": {},
        "tools_requirements": {"起重设备": {"quantity": 1, "unit": "台"}, "扳手": {"quantity": 10, "unit": "把"}},
        "approval_comments": ""
    },
    {
        "id": 5,
        "equipment_id": "R-101",
        "equipment_name": "R-101 反应釜",
        "equipment_category": "生产设备",
        "equipment_type_name": "反应釜",
        "process_name": "内部检查",
        "status": "pending",
        "workers": {"维修工": ["赵六"], "质检员": ["孙七"]},
        "estimated_hours": 6,
        "scheduled_start_time": "2026-07-04 08:00",
        "scheduled_end_time": "2026-07-04 14:00",
        "description": "对反应釜内壁、搅拌器、密封件进行全面检查，记录缺陷",
        "is_milestone": False,
        "material_requirements": {},
        "tools_requirements": {"内窥镜": {"quantity": 1, "unit": "台"}, "手电筒": {"quantity": 2, "unit": "个"}},
        "approval_comments": ""
    },
    {
        "id": 6,
        "equipment_id": "R-102",
        "equipment_name": "R-102 反应釜",
        "equipment_category": "生产设备",
        "equipment_type_name": "反应釜",
        "process_name": "设备停机",
        "status": "completed",
        "workers": {"操作工": ["周八"], "技术员": ["吴九"]},
        "estimated_hours": 4,
        "scheduled_start_time": "2026-07-01 08:00",
        "scheduled_end_time": "2026-07-01 12:00",
        "description": "按照操作规程进行设备停机操作",
        "is_milestone": True,
        "material_requirements": {},
        "tools_requirements": {},
        "approval_comments": "停机完成"
    },
    {
        "id": 7,
        "equipment_id": "R-102",
        "equipment_name": "R-102 反应釜",
        "equipment_category": "生产设备",
        "equipment_type_name": "反应釜",
        "process_name": "安全隔离",
        "status": "rejected",
        "workers": {"操作工": ["周八"], "安全员": ["郑十"]},
        "estimated_hours": 6,
        "scheduled_start_time": "2026-07-01 12:00",
        "scheduled_end_time": "2026-07-01 18:00",
        "description": "执行LOTO隔离程序",
        "is_milestone": True,
        "material_requirements": {},
        "tools_requirements": {},
        "approval_comments": "隔离不彻底，需重新执行隔离程序"
    },
    {
        "id": 8,
        "equipment_id": "T-201",
        "equipment_name": "T-201 蒸馏塔",
        "equipment_category": "生产设备",
        "equipment_type_name": "蒸馏塔",
        "process_name": "设备停机",
        "status": "completed",
        "workers": {"操作工": ["钱十一"]},
        "estimated_hours": 8,
        "scheduled_start_time": "2026-07-01 06:00",
        "scheduled_end_time": "2026-07-01 14:00",
        "description": "蒸馏塔逐步降温降压，停止进料",
        "is_milestone": True,
        "material_requirements": {},
        "tools_requirements": {},
        "approval_comments": "停机完成"
    },
    {
        "id": 9,
        "equipment_id": "T-201",
        "equipment_name": "T-201 蒸馏塔",
        "equipment_category": "生产设备",
        "equipment_type_name": "蒸馏塔",
        "process_name": "塔板清洗",
        "status": "on_hold",
        "workers": {"维修工": ["王十二"], "技术员": ["陈十三"]},
        "estimated_hours": 24,
        "scheduled_start_time": "2026-07-02 08:00",
        "scheduled_end_time": "2026-07-03 08:00",
        "description": "对蒸馏塔各层塔板进行清洗，清除结垢和残留物",
        "is_milestone": True,
        "material_requirements": {"清洗剂": {"quantity": 100, "unit": "kg"}},
        "tools_requirements": {"清洗设备": {"quantity": 1, "unit": "套"}},
        "approval_comments": ""
    },
    {
        "id": 10,
        "equipment_id": "T-201",
        "equipment_name": "T-201 蒸馏塔",
        "equipment_category": "生产设备",
        "equipment_type_name": "蒸馏塔",
        "process_name": "填料更换",
        "status": "pending",
        "workers": {"维修工": ["王十二"], "技术员": ["陈十三"]},
        "estimated_hours": 16,
        "scheduled_start_time": "2026-07-03 08:00",
        "scheduled_end_time": "2026-07-04 00:00",
        "description": "更换蒸馏塔内的填料，确保分离效率",
        "is_milestone": True,
        "material_requirements": {"填料": {"quantity": 5, "unit": "m³"}},
        "tools_requirements": {},
        "approval_comments": ""
    },
    {
        "id": 11,
        "equipment_id": "V-301",
        "equipment_name": "V-301 储罐",
        "equipment_category": "生产设备",
        "equipment_type_name": "储罐",
        "process_name": "物料转移",
        "status": "completed",
        "workers": {"操作工": ["刘十四"]},
        "estimated_hours": 12,
        "scheduled_start_time": "2026-07-01 08:00",
        "scheduled_end_time": "2026-07-01 20:00",
        "description": "将储罐内物料转移至备用储罐",
        "is_milestone": True,
        "material_requirements": {},
        "tools_requirements": {},
        "approval_comments": "物料转移完成"
    },
    {
        "id": 12,
        "equipment_id": "V-301",
        "equipment_name": "V-301 储罐",
        "equipment_category": "生产设备",
        "equipment_type_name": "储罐",
        "process_name": "罐体清洗",
        "status": "in_progress",
        "workers": {"操作工": ["刘十四"], "维修工": ["赵十五"]},
        "estimated_hours": 16,
        "scheduled_start_time": "2026-07-02 08:00",
        "scheduled_end_time": "2026-07-03 00:00",
        "description": "对储罐内部进行彻底清洗",
        "is_milestone": False,
        "material_requirements": {"清洗液": {"quantity": 200, "unit": "kg"}},
        "tools_requirements": {},
        "approval_comments": ""
    },
    {
        "id": 13,
        "equipment_id": "P-401",
        "equipment_name": "P-401 输送泵",
        "equipment_category": "辅助设备",
        "equipment_type_name": "泵",
        "process_name": "泵体拆卸",
        "status": "completed",
        "workers": {"维修工": ["孙十六"]},
        "estimated_hours": 4,
        "scheduled_start_time": "2026-07-01 08:00",
        "scheduled_end_time": "2026-07-01 12:00",
        "description": "拆卸泵体，检查叶轮磨损情况",
        "is_milestone": False,
        "material_requirements": {},
        "tools_requirements": {"扳手": {"quantity": 5, "unit": "把"}},
        "approval_comments": "拆卸完成"
    },
    {
        "id": 14,
        "equipment_id": "P-401",
        "equipment_name": "P-401 输送泵",
        "equipment_category": "辅助设备",
        "equipment_type_name": "泵",
        "process_name": "叶轮更换",
        "status": "on_hold",
        "workers": {"维修工": ["孙十六"], "技术员": ["周十七"]},
        "estimated_hours": 8,
        "scheduled_start_time": "2026-07-01 12:00",
        "scheduled_end_time": "2026-07-01 20:00",
        "description": "更换磨损的叶轮，调整间隙",
        "is_milestone": True,
        "material_requirements": {"叶轮": {"quantity": 1, "unit": "个"}},
        "tools_requirements": {},
        "approval_comments": ""
    },
    {
        "id": 15,
        "equipment_id": "P-402",
        "equipment_name": "P-402 输送泵",
        "equipment_category": "辅助设备",
        "equipment_type_name": "泵",
        "process_name": "轴承检查",
        "status": "pending",
        "workers": {"维修工": ["孙十六"]},
        "estimated_hours": 4,
        "scheduled_start_time": "2026-07-02 08:00",
        "scheduled_end_time": "2026-07-02 12:00",
        "description": "检查轴承磨损情况，必要时更换",
        "is_milestone": False,
        "material_requirements": {},
        "tools_requirements": {},
        "approval_comments": ""
    },
    {
        "id": 16,
        "equipment_id": "C-501",
        "equipment_name": "C-501 压缩机",
        "equipment_category": "辅助设备",
        "equipment_type_name": "压缩机",
        "process_name": "设备停机",
        "status": "completed",
        "workers": {"操作工": ["吴十八"]},
        "estimated_hours": 6,
        "scheduled_start_time": "2026-07-01 06:00",
        "scheduled_end_time": "2026-07-01 12:00",
        "description": "按照停机程序逐步停机",
        "is_milestone": True,
        "material_requirements": {},
        "tools_requirements": {},
        "approval_comments": "停机完成"
    },
    {
        "id": 17,
        "equipment_id": "C-501",
        "equipment_name": "C-501 压缩机",
        "equipment_category": "辅助设备",
        "equipment_type_name": "压缩机",
        "process_name": "气缸检查",
        "status": "on_hold",
        "workers": {"维修工": ["郑十九"], "技术员": ["黄二十"]},
        "estimated_hours": 12,
        "scheduled_start_time": "2026-07-02 08:00",
        "scheduled_end_time": "2026-07-02 20:00",
        "description": "检查气缸磨损、活塞环状态",
        "is_milestone": True,
        "material_requirements": {},
        "tools_requirements": {"塞尺": {"quantity": 1, "unit": "套"}, "千分尺": {"quantity": 1, "unit": "个"}},
        "approval_comments": ""
    },
    {
        "id": 18,
        "equipment_id": "R-101",
        "equipment_name": "R-101 反应釜",
        "equipment_category": "生产设备",
        "equipment_type_name": "反应釜",
        "process_name": "密封件更换",
        "status": "pending",
        "workers": {"维修工": ["赵六"], "技术员": ["李四"]},
        "estimated_hours": 8,
        "scheduled_start_time": "2026-07-04 14:00",
        "scheduled_end_time": "2026-07-04 22:00",
        "description": "更换反应釜密封件，确保密封性能",
        "is_milestone": True,
        "material_requirements": {"密封件": {"quantity": 2, "unit": "套"}},
        "tools_requirements": {},
        "approval_comments": ""
    },
    {
        "id": 19,
        "equipment_id": "R-101",
        "equipment_name": "R-101 反应釜",
        "equipment_category": "生产设备",
        "equipment_type_name": "反应釜",
        "process_name": "设备组装",
        "status": "pending",
        "workers": {"维修工": ["赵六"], "技术员": ["李四"]},
        "estimated_hours": 12,
        "scheduled_start_time": "2026-07-05 08:00",
        "scheduled_end_time": "2026-07-05 20:00",
        "description": "重新组装设备，连接管道和仪表",
        "is_milestone": True,
        "material_requirements": {},
        "tools_requirements": {},
        "approval_comments": ""
    },
    {
        "id": 20,
        "equipment_id": "R-101",
        "equipment_name": "R-101 反应釜",
        "equipment_category": "生产设备",
        "equipment_type_name": "反应釜",
        "process_name": "试运验收",
        "status": "pending",
        "workers": {"操作工": ["张三"], "技术员": ["李四"], "质检员": ["孙七"]},
        "estimated_hours": 8,
        "scheduled_start_time": "2026-07-06 08:00",
        "scheduled_end_time": "2026-07-06 16:00",
        "description": "进行设备试运，检查各项指标，签署验收报告",
        "is_milestone": True,
        "material_requirements": {},
        "tools_requirements": {},
        "approval_comments": ""
    }
]


mock_workers = [
    {
        "worker_id": "W001",
        "name": "张三",
        "department": "生产部",
        "role": "操作工",
        "status": "working",
        "current_task": "设备停机",
        "equipment_id": "R-101",
        "next_task": "安全隔离",
        "available_time": "12:00",
        "schedule": [
            {"day": 1, "time": "08:00-12:00", "task": "设备停机", "equipment": "R-101"},
            {"day": 1, "time": "12:00-18:00", "task": "安全隔离", "equipment": "R-101"},
            {"day": 2, "time": "08:00-16:00", "task": "物料清理", "equipment": "R-101"}
        ],
        "skills": ["设备操作", "安全隔离"],
        "total_hours_worked": 48,
        "efficiency": 0.92
    },
    {
        "worker_id": "W002",
        "name": "李四",
        "department": "技术部",
        "role": "技术员",
        "status": "working",
        "current_task": "设备停机",
        "equipment_id": "R-101",
        "next_task": "设备解体",
        "available_time": "12:00",
        "schedule": [
            {"day": 1, "time": "08:00-12:00", "task": "设备停机", "equipment": "R-101"},
            {"day": 3, "time": "08:00-20:00", "task": "设备解体", "equipment": "R-101"}
        ],
        "skills": ["设备检修", "故障诊断"],
        "total_hours_worked": 36,
        "efficiency": 0.88
    },
    {
        "worker_id": "W003",
        "name": "王五",
        "department": "安全部",
        "role": "安全员",
        "status": "idle",
        "current_task": "",
        "equipment_id": "",
        "next_task": "安全隔离",
        "available_time": "立即",
        "schedule": [
            {"day": 1, "time": "12:00-18:00", "task": "安全隔离", "equipment": "R-101"}
        ],
        "skills": ["安全检查", "风险评估"],
        "total_hours_worked": 12,
        "efficiency": 0.95
    },
    {
        "worker_id": "W004",
        "name": "赵六",
        "department": "维修部",
        "role": "维修工",
        "status": "working",
        "current_task": "设备解体",
        "equipment_id": "R-101",
        "next_task": "内部检查",
        "available_time": "20:00",
        "schedule": [
            {"day": 3, "time": "08:00-20:00", "task": "设备解体", "equipment": "R-101"},
            {"day": 4, "time": "08:00-14:00", "task": "内部检查", "equipment": "R-101"}
        ],
        "skills": ["设备维修", "机械装配"],
        "total_hours_worked": 40,
        "efficiency": 0.90
    },
    {
        "worker_id": "W005",
        "name": "孙七",
        "department": "质检部",
        "role": "质检员",
        "status": "idle",
        "current_task": "",
        "equipment_id": "",
        "next_task": "内部检查",
        "available_time": "立即",
        "schedule": [
            {"day": 4, "time": "08:00-14:00", "task": "内部检查", "equipment": "R-101"}
        ],
        "skills": ["质量检验", "无损检测"],
        "total_hours_worked": 8,
        "efficiency": 0.98
    },
    {
        "worker_id": "W006",
        "name": "周八",
        "department": "生产部",
        "role": "操作工",
        "status": "working",
        "current_task": "安全隔离",
        "equipment_id": "R-102",
        "next_task": "",
        "available_time": "18:00",
        "schedule": [
            {"day": 1, "time": "08:00-12:00", "task": "设备停机", "equipment": "R-102"},
            {"day": 1, "time": "12:00-18:00", "task": "安全隔离", "equipment": "R-102"}
        ],
        "skills": ["设备操作"],
        "total_hours_worked": 24,
        "efficiency": 0.85
    }
]


mock_orders = [
    {
        "work_order_id": "WO20260701001",
        "title": "R-101反应釜年度检修",
        "priority": "high",
        "status": "in_progress",
        "equipment_id": "R-101",
        "equipment_name": "R-101 反应釜",
        "created_time": "2026-06-25 09:00",
        "start_time": "2026-07-01 08:00",
        "end_time": "2026-07-06 16:00",
        "assignee": "张三",
        "progress": 35,
        "tasks": [
            {"name": "设备停机", "status": "completed"},
            {"name": "安全隔离", "status": "completed"},
            {"name": "物料清理", "status": "in_progress"},
            {"name": "设备解体", "status": "pending"},
            {"name": "内部检查", "status": "pending"}
        ],
        "materials": {"氮气": 50, "密封件": 2},
        "tools": {"扳手": 10, "起重设备": 1}
    },
    {
        "work_order_id": "WO20260701002",
        "title": "T-201蒸馏塔塔板清洗",
        "priority": "medium",
        "status": "in_progress",
        "equipment_id": "T-201",
        "equipment_name": "T-201 蒸馏塔",
        "created_time": "2026-06-28 14:00",
        "start_time": "2026-07-01 06:00",
        "end_time": "2026-07-04 00:00",
        "assignee": "王十二",
        "progress": 40,
        "tasks": [
            {"name": "设备停机", "status": "completed"},
            {"name": "塔板清洗", "status": "pending"},
            {"name": "填料更换", "status": "pending"}
        ],
        "materials": {"清洗剂": 100, "填料": 5},
        "tools": {"清洗设备": 1}
    },
    {
        "work_order_id": "WO20260701003",
        "title": "P-401输送泵叶轮更换",
        "priority": "high",
        "status": "pending",
        "equipment_id": "P-401",
        "equipment_name": "P-401 输送泵",
        "created_time": "2026-07-01 10:00",
        "start_time": "2026-07-01 12:00",
        "end_time": "2026-07-01 20:00",
        "assignee": "孙十六",
        "progress": 0,
        "tasks": [
            {"name": "泵体拆卸", "status": "completed"},
            {"name": "叶轮更换", "status": "pending"}
        ],
        "materials": {"叶轮": 1},
        "tools": {"扳手": 5}
    },
    {
        "work_order_id": "WO20260702001",
        "title": "V-301储罐清洗",
        "priority": "medium",
        "status": "in_progress",
        "equipment_id": "V-301",
        "equipment_name": "V-301 储罐",
        "created_time": "2026-06-30 11:00",
        "start_time": "2026-07-01 08:00",
        "end_time": "2026-07-03 00:00",
        "assignee": "刘十四",
        "progress": 50,
        "tasks": [
            {"name": "物料转移", "status": "completed"},
            {"name": "罐体清洗", "status": "in_progress"}
        ],
        "materials": {"清洗液": 200},
        "tools": {}
    },
    {
        "work_order_id": "WO20260702002",
        "title": "C-501压缩机气缸检查",
        "priority": "high",
        "status": "pending",
        "equipment_id": "C-501",
        "equipment_name": "C-501 压缩机",
        "created_time": "2026-07-01 08:00",
        "start_time": "2026-07-02 08:00",
        "end_time": "2026-07-02 20:00",
        "assignee": "郑十九",
        "progress": 0,
        "tasks": [
            {"name": "设备停机", "status": "completed"},
            {"name": "气缸检查", "status": "pending"}
        ],
        "materials": {},
        "tools": {"塞尺": 1, "千分尺": 1}
    }
]


mock_materials = [
    {
        "material_id": "M001",
        "material_name": "氮气",
        "unit": "m³",
        "total_stock": 500,
        "used_stock": 50,
        "available_stock": 450,
        "location": "B区仓库",
        "supplier": "气体公司",
        "last_update": "2026-07-01 08:00",
        "safety_stock": 100,
        "critical_level": 50,
        "status": "normal"
    },
    {
        "material_id": "M002",
        "material_name": "清洗剂",
        "unit": "kg",
        "total_stock": 500,
        "used_stock": 100,
        "available_stock": 400,
        "location": "A区仓库",
        "supplier": "化工原料公司",
        "last_update": "2026-07-01 10:00",
        "safety_stock": 200,
        "critical_level": 100,
        "status": "normal"
    },
    {
        "material_id": "M003",
        "material_name": "密封件",
        "unit": "套",
        "total_stock": 20,
        "used_stock": 0,
        "available_stock": 20,
        "location": "备件库",
        "supplier": "设备厂家",
        "last_update": "2026-06-20 14:00",
        "safety_stock": 10,
        "critical_level": 5,
        "status": "normal"
    },
    {
        "material_id": "M004",
        "material_name": "叶轮",
        "unit": "个",
        "total_stock": 5,
        "used_stock": 0,
        "available_stock": 5,
        "location": "备件库",
        "supplier": "泵厂",
        "last_update": "2026-06-15 09:00",
        "safety_stock": 3,
        "critical_level": 1,
        "status": "normal"
    },
    {
        "material_id": "M005",
        "material_name": "填料",
        "unit": "m³",
        "total_stock": 20,
        "used_stock": 0,
        "available_stock": 20,
        "location": "A区仓库",
        "supplier": "填料厂家",
        "last_update": "2026-06-25 11:00",
        "safety_stock": 10,
        "critical_level": 5,
        "status": "normal"
    },
    {
        "material_id": "M006",
        "material_name": "清洗液",
        "unit": "kg",
        "total_stock": 300,
        "used_stock": 200,
        "available_stock": 100,
        "location": "B区仓库",
        "supplier": "化工原料公司",
        "last_update": "2026-07-02 08:00",
        "safety_stock": 150,
        "critical_level": 50,
        "status": "warning"
    }
]


mock_tools = [
    {
        "tool_id": "T001",
        "tool_name": "扳手",
        "type": "手动工具",
        "quantity": 20,
        "available": 8,
        "in_use": 12,
        "status": "normal",
        "location": "工具间A",
        "last_maintenance": "2026-06-01",
        "next_maintenance": "2026-09-01",
        "assigned_workers": ["张三", "赵六", "孙十六"],
        "calibration_status": "valid"
    },
    {
        "tool_id": "T002",
        "tool_name": "检测仪",
        "type": "检测设备",
        "quantity": 5,
        "available": 3,
        "in_use": 2,
        "status": "normal",
        "location": "检测室",
        "last_maintenance": "2026-06-15",
        "next_maintenance": "2026-07-15",
        "assigned_workers": ["李四"],
        "calibration_status": "valid"
    },
    {
        "tool_id": "T003",
        "tool_name": "起重设备",
        "type": "重型设备",
        "quantity": 2,
        "available": 1,
        "in_use": 1,
        "status": "normal",
        "location": "吊装区",
        "last_maintenance": "2026-05-01",
        "next_maintenance": "2026-08-01",
        "assigned_workers": ["赵六"],
        "calibration_status": "valid"
    },
    {
        "tool_id": "T004",
        "tool_name": "内窥镜",
        "type": "检测设备",
        "quantity": 2,
        "available": 2,
        "in_use": 0,
        "status": "normal",
        "location": "检测室",
        "last_maintenance": "2026-06-20",
        "next_maintenance": "2026-07-20",
        "assigned_workers": [],
        "calibration_status": "valid"
    },
    {
        "tool_id": "T005",
        "tool_name": "清洗设备",
        "type": "专用设备",
        "quantity": 1,
        "available": 0,
        "in_use": 1,
        "status": "busy",
        "location": "清洗车间",
        "last_maintenance": "2026-06-10",
        "next_maintenance": "2026-07-10",
        "assigned_workers": ["王十二"],
        "calibration_status": "valid"
    },
    {
        "tool_id": "T006",
        "tool_name": "塞尺",
        "type": "测量工具",
        "quantity": 3,
        "available": 2,
        "in_use": 1,
        "status": "normal",
        "location": "工具间B",
        "last_maintenance": "2026-06-01",
        "next_maintenance": "2026-09-01",
        "assigned_workers": ["郑十九"],
        "calibration_status": "valid"
    }
]


def init_process_data():
    app = create_app()
    _ensure_current_app(app)
    
    collection = get_collection("processes")
    
    for process in mock_processes:
        existing = collection.find_one({"id": process["id"]})
        if not existing:
            collection.insert_one(process)
            print(f"插入流程: {process['process_name']}")
    
    print(f"流程数据初始化完成，共 {len(mock_processes)} 条")


def init_info_panel_data():
    app = create_app()
    _ensure_current_app(app)
    
    workers_collection = get_collection("workers")
    orders_collection = get_collection("orders")
    materials_collection = get_collection("materials")
    tools_collection = get_collection("tools")
    
    for worker in mock_workers:
        existing = workers_collection.find_one({"worker_id": worker["worker_id"]})
        if not existing:
            workers_collection.insert_one(worker)
    print(f"工人数据初始化完成，共 {len(mock_workers)} 条")
    
    for order in mock_orders:
        existing = orders_collection.find_one({"work_order_id": order["work_order_id"]})
        if not existing:
            orders_collection.insert_one(order)
    print(f"工单数据初始化完成，共 {len(mock_orders)} 条")
    
    for material in mock_materials:
        existing = materials_collection.find_one({"material_name": material["material_name"]})
        if not existing:
            materials_collection.insert_one(material)
    print(f"物料数据初始化完成，共 {len(mock_materials)} 条")
    
    for tool in mock_tools:
        existing = tools_collection.find_one({"tool_id": tool["tool_id"]})
        if not existing:
            tools_collection.insert_one(tool)
    print(f"工具数据初始化完成，共 {len(mock_tools)} 条")


if __name__ == "__main__":
    print("开始初始化数据库数据...")
    init_process_data()
    init_info_panel_data()
    print("数据初始化完成！")