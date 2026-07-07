"""工单任务状态常量与状态转换权限映射

从原 app.py 抽取，供工单相关路由复用。
"""

# 工单任务状态常量
TASK_STATUS = {
    'RELEASED': 'released',                 # 待开始
    'APPLY_START': 'apply_for_start',      # 申请开工
    'ENG_APPROVED': 'eng_approved',        # 工程师确认
    'CONSTRUCTION_CONFIRMED': 'construction_confirmed',  # 施工确认
    'TEAM_RECEIVED': 'team_received',      # 班组受理
    'CONSTRUCTION_SIGNED': 'construction_signed',        # 施工回签
    'PROCESS_CLOSED': 'process_closed',   # 工艺存储关闭
    'EQUIPMENT_CLOSED': 'equipment_closed',  # 设备部关闭
    'CANCELLED': 'cancelled',             # 取消
}

# 状态转换权限映射：当前状态 -> { 目标状态: [允许的角色列表] }
STATUS_TRANSITIONS = {
    TASK_STATUS['RELEASED']: {
        TASK_STATUS['APPLY_START']: ['worker']
    },
    TASK_STATUS['APPLY_START']: {
        TASK_STATUS['ENG_APPROVED']: ['admin']
    },
    TASK_STATUS['ENG_APPROVED']: {
        TASK_STATUS['CONSTRUCTION_CONFIRMED']: ['admin']
    },
    TASK_STATUS['CONSTRUCTION_CONFIRMED']: {
        TASK_STATUS['TEAM_RECEIVED']: ['admin']
    },
    TASK_STATUS['TEAM_RECEIVED']: {
        TASK_STATUS['CONSTRUCTION_SIGNED']: ['worker']
    },
    TASK_STATUS['CONSTRUCTION_SIGNED']: {
        TASK_STATUS['PROCESS_CLOSED']: ['admin']
    },
    TASK_STATUS['PROCESS_CLOSED']: {
        TASK_STATUS['EQUIPMENT_CLOSED']: ['admin']
    },
}
