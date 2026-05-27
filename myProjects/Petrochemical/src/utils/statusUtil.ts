const TASK_STATUS = {
  RELEASED: 'released',             // 工单发布 (初始状态)
  APPLY_START: 'apply_for_start',   // 申请开工
  ENG_APPROVED: 'eng_approved',     // 工程师确认
  CONSTRUCTION_CONFIRMED: 'construction_confirmed', // 施工确认
  TEAM_RECEIVED: 'team_received',   // 班组接收
  CONSTRUCTION_SIGNED: 'construction_signed', // 施工回签 (工人主要操作点)
  PROCESS_CLOSED: 'process_closed', // 工艺关闭
  EQUIPMENT_CLOSED: 'equipment_closed', // 设备关闭
  CANCELLED: 'cancelled'            // 取消
}
const STATUS_LABEL_MAP = {
  [TASK_STATUS.RELEASED]: '待开始',
  [TASK_STATUS.APPLY_START]: '申请开工',
  [TASK_STATUS.ENG_APPROVED]: '工程师确认',
  [TASK_STATUS.CONSTRUCTION_CONFIRMED]: '施工确认',
  [TASK_STATUS.TEAM_RECEIVED]: '班组受理',
  [TASK_STATUS.CONSTRUCTION_SIGNED]: '施工回签',
  [TASK_STATUS.PROCESS_CLOSED]: '工艺存储关闭',
  [TASK_STATUS.EQUIPMENT_CLOSED]: '设备部关闭',
  [TASK_STATUS.CANCELLED]: '取消'
}

export type StatusStyle = {
  lineBg: string
  tagBg: string
  tagText: string
  tagBorder: string
}

const DEFAULT_STATUS_STYLE: StatusStyle = {
  lineBg: '#9ca3af',
  tagBg: '#f3f4f6',
  tagText: '#4b5563',
  tagBorder: '#d1d5db'
}

const STATUS_STYLE_MAP: Record<string, StatusStyle> = {
  [TASK_STATUS.RELEASED]: {
    lineBg: '#9ca3af',
    tagBg: '#f3f4f6',
    tagText: '#4b5563',
    tagBorder: '#d1d5db'
  },
  [TASK_STATUS.APPLY_START]: {
    lineBg: '#3b82f6',
    tagBg: '#eff6ff',
    tagText: '#1d4ed8',
    tagBorder: '#bfdbfe'
  },
  [TASK_STATUS.ENG_APPROVED]: {
    lineBg: '#6366f1',
    tagBg: '#eef2ff',
    tagText: '#4338ca',
    tagBorder: '#c7d2fe'
  },
  [TASK_STATUS.CONSTRUCTION_CONFIRMED]: {
    lineBg: '#06b6d4',
    tagBg: '#ecfeff',
    tagText: '#0e7490',
    tagBorder: '#a5f3fc'
  },
  [TASK_STATUS.TEAM_RECEIVED]: {
    lineBg: '#f59e0b',
    tagBg: '#fffbeb',
    tagText: '#b45309',
    tagBorder: '#fde68a'
  },
  [TASK_STATUS.CONSTRUCTION_SIGNED]: {
    lineBg: '#8b5cf6',
    tagBg: '#f5f3ff',
    tagText: '#6d28d9',
    tagBorder: '#ddd6fe'
  },
  [TASK_STATUS.PROCESS_CLOSED]: {
    lineBg: '#10b981',
    tagBg: '#ecfdf5',
    tagText: '#047857',
    tagBorder: '#a7f3d0'
  },
  [TASK_STATUS.EQUIPMENT_CLOSED]: {
    lineBg: '#059669',
    tagBg: '#ecfdf5',
    tagText: '#065f46',
    tagBorder: '#6ee7b7'
  },
  [TASK_STATUS.CANCELLED]: {
    lineBg: '#ef4444',
    tagBg: '#fef2f2',
    tagText: '#b91c1c',
    tagBorder: '#fecaca'
  }
}
// 定义正常流程的状态顺序（不包括 CANCELLED，因为它是一个终止态，可从任意状态跳转）
export const STATUS_SEQUENCE = [
  TASK_STATUS.RELEASED,
  TASK_STATUS.APPLY_START,
  TASK_STATUS.ENG_APPROVED,
  TASK_STATUS.CONSTRUCTION_CONFIRMED,
  TASK_STATUS.TEAM_RECEIVED,
  TASK_STATUS.CONSTRUCTION_SIGNED,
  TASK_STATUS.PROCESS_CLOSED,
  TASK_STATUS.EQUIPMENT_CLOSED
];

/**
 * 获取状态标签
 * @param status
 */
export function getStatusLabel(status) {
  if(Object.keys(STATUS_LABEL_MAP).includes(status)) {
    return STATUS_LABEL_MAP[status];
  }else{
    return '未知状态';
  }

}

export function getStatusStyle(status: string): StatusStyle {
  return STATUS_STYLE_MAP[status] || DEFAULT_STATUS_STYLE
}

/**
 * 获取下一个状态（仅限正常流程）| 非标签
 * @param {string} currentStatus - 当前状态值（如 'released'）
 * @returns {string | null} 下一个状态，如果已是最后一个则返回 null
 */
export function getNextStatus(currentStatus) {
  const index = STATUS_SEQUENCE.indexOf(currentStatus);
  if (index === -1 || index === STATUS_SEQUENCE.length - 1) {
    return null; // 无效状态 或 已到最后一步
  }
  return STATUS_SEQUENCE[index + 1];
}

/**
 * 获取下一个状态的标签
 * @param currentStatus -当前状态值（如 'released'）
 */
export function getNextStatusLabel(currentStatus:string) {
  return getStatusLabel(getNextStatus(currentStatus));
}
