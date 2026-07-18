// ==================== 状态常量 ====================

export const TASK_STATUS = {
  RELEASED: 'released',
  PENDING_ENGINEER: 'pending_engineer',
  PENDING_CONSTRUCTION: 'pending_construction',
  PENDING_TEAM: 'pending_team',
  PENDING_SIGN: 'pending_sign',
  SUBMITTED: 'submitted',
  PENDING_PROCESS_CLOSE: 'pending_process_close',
  PENDING_EQUIPMENT_CLOSE: 'pending_equipment_close',
  COMPLETED: 'completed',
  CANCELLED: 'cancelled',
}

// 终态集合
export const TERMINAL_STATUSES = new Set(['completed', 'cancelled'])

// 不可驳回的状态
export const NON_REJECTABLE_STATUSES = new Set(['released', 'completed', 'cancelled'])

// ==================== 状态→显示文字 ====================

export const STATUS_LABEL_MAP = {
  // 新状态
  [TASK_STATUS.RELEASED]: '待开始',
  [TASK_STATUS.PENDING_ENGINEER]: '等待工程师确认',
  [TASK_STATUS.PENDING_CONSTRUCTION]: '等待施工确认',
  [TASK_STATUS.PENDING_TEAM]: '等待班组受理',
  [TASK_STATUS.PENDING_SIGN]: '等待施工回签',
  [TASK_STATUS.SUBMITTED]: '已提交',
  [TASK_STATUS.PENDING_PROCESS_CLOSE]: '等待工艺存储关闭',
  [TASK_STATUS.PENDING_EQUIPMENT_CLOSE]: '等待设备部关闭',
  [TASK_STATUS.COMPLETED]: '已完成',
  [TASK_STATUS.CANCELLED]: '已取消',
  // 兼容旧状态值
  'pending': '待开始',
  'current': '进行中',
  'in_progress': '进行中',
  'on_hold': '待确认',
  'confirmed': '已确认',
  'rejected': '已驳回',
}

// ==================== 状态→Tag 颜色 ====================

export function getStatusTagType(status) {
  const typeMap = {
    [TASK_STATUS.RELEASED]: 'info',
    [TASK_STATUS.PENDING_ENGINEER]: '',
    [TASK_STATUS.PENDING_CONSTRUCTION]: '',
    [TASK_STATUS.PENDING_TEAM]: '',
    [TASK_STATUS.PENDING_SIGN]: 'warning',
    [TASK_STATUS.SUBMITTED]: 'success',
    [TASK_STATUS.PENDING_PROCESS_CLOSE]: '',
    [TASK_STATUS.PENDING_EQUIPMENT_CLOSE]: '',
    [TASK_STATUS.COMPLETED]: 'success',
    [TASK_STATUS.CANCELLED]: 'danger',
    // 兼容旧状态
    'completed': 'success',
    'confirmed': 'success',
    'current': 'primary',
    'in_progress': 'primary',
    'pending': 'info',
    'rejected': 'danger',
    'on_hold': 'warning',
  }
  return typeMap[status] || 'info'
}

// ==================== 状态→显示文字 辅助函数 ====================

export function getStatusText(status) {
  return STATUS_LABEL_MAP[status] || status
}

// ==================== 工具函数 ====================

export function formatTime(timeStr) {
  if (!timeStr) return '--'

  let datePart = timeStr
  let timePart = ''

  if (timeStr.includes(' ')) {
    ;[datePart, timePart] = timeStr.split(' ')
  } else if (timeStr.includes('T')) {
    ;[datePart, timePart] = timeStr.split('T')
  }

  if (timePart) {
    return `${datePart} ${timePart.substring(0, 5)}`
  }

  return datePart
}

export function formatWorkers(workers) {
  if (!workers) return '未分配'
  if (typeof workers === 'string') return workers
  if (Array.isArray(workers)) return workers.join(', ')
  if (typeof workers === 'object') {
    const workerNames = []
    Object.keys(workers).forEach(role => {
      const names = workers[role]
      if (Array.isArray(names) && names.length > 0) {
        workerNames.push(...names)
      } else if (typeof names === 'string' && names) {
        workerNames.push(names)
      }
    })
    return workerNames.length > 0 ? workerNames.join(', ') : '未分配'
  }
  return '未分配'
}

export function parseTimeToMinutes(timeStr) {
  if (!timeStr) return 0
  try {
    const dayMatch = timeStr.match(/第(\d+)天/)
    const timeMatch = timeStr.match(/(\d+):(\d+)/)

    let day = 0
    let hours = 0
    let minutes = 0

    if (dayMatch) {
      day = parseInt(dayMatch[1], 10) * 24 * 60
    }
    if (timeMatch) {
      hours = parseInt(timeMatch[1], 10)
      minutes = parseInt(timeMatch[2], 10)
    }

    return day + hours * 60 + minutes
  } catch {
    return 0
  }
}

export function getOpinionPlaceholder(status) {
  return '请填写审核意见（可选）'
}

// ==================== 行样式 ====================

export function getRowClassName(row) {
  const status = row?.status || row
  if (status === 'completed') return 'status-completed-row'
  if (status === 'cancelled') return 'status-cancelled-row'
  if (status === 'rejected') return 'status-rejected-row'
  if (status === 'pending_sign') return 'status-on-hold-row'
  if (status === 'submitted') return 'status-submitted-row'
  if (status === 'released') return 'status-pending-row'
  return ''
}

export function getCellStyle(row) {
  const status = row?.status || row
  if (status === 'completed') {
    return { backgroundColor: '#e8f5e8', borderBottom: '1px solid #c8e6c9' }
  }
  if (status === 'cancelled') {
    return { backgroundColor: '#fce4ec', borderBottom: '1px solid #f8bbd0' }
  }
  if (status === 'rejected') {
    return { backgroundColor: '#ffebee', borderBottom: '1px solid #ffcdd2' }
  }
  if (status === 'pending_sign') {
    return { backgroundColor: '#fff3e0', borderBottom: '1px solid #ffe0b2' }
  }
  if (status === 'released') {
    return { backgroundColor: '#fafafa', borderBottom: '1px solid #e0e0e0' }
  }
  return {}
}
