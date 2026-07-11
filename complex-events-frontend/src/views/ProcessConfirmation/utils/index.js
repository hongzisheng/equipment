export const TASK_STATUS = {
  RELEASED: 'released',
  APPLY_START: 'apply_for_start',
  ENG_APPROVED: 'eng_approved',
  CONSTRUCTION_CONFIRMED: 'construction_confirmed',
  TEAM_RECEIVED: 'team_received',
  CONSTRUCTION_SIGNED: 'construction_signed',
  PROCESS_CLOSED: 'process_closed',
  EQUIPMENT_CLOSED: 'equipment_closed',
  CANCELLED: 'cancelled'
}

export const STATUS_LABEL_MAP = {
  'pending': '待处理',
  'current': '进行中',
  'in_progress': '进行中',
  'on_hold': '待确认',
  'confirmed': '已确认',
  [TASK_STATUS.RELEASED]: '待开始',
  [TASK_STATUS.APPLY_START]: '申请开工',
  [TASK_STATUS.ENG_APPROVED]: '工程师确认',
  [TASK_STATUS.CONSTRUCTION_CONFIRMED]: '施工确认',
  [TASK_STATUS.TEAM_RECEIVED]: '班组受理',
  [TASK_STATUS.CONSTRUCTION_SIGNED]: '施工回签',
  [TASK_STATUS.PROCESS_CLOSED]: '工艺存储关闭',
  [TASK_STATUS.EQUIPMENT_CLOSED]: '设备部关闭',
  [TASK_STATUS.CANCELLED]: '取消',
  'completed': '已完成',
  'rejected': '已驳回'
}

export function getStatusTagType(status) {
  const typeMap = {
    'completed': 'success',
    'confirmed': 'success',
    'current': 'primary',
    'in_progress': 'primary',
    'pending': 'info',
    'rejected': 'danger',
    'on_hold': 'warning'
  }
  return typeMap[status] || 'info'
}

export function getStatusText(status) {
  return STATUS_LABEL_MAP[status] || status
}

export function formatTime(timeStr) {
  if (!timeStr) return '--'
  
  let datePart = timeStr
  let timePart = ''
  
  if (timeStr.includes(' ')) {
    [datePart, timePart] = timeStr.split(' ')
  } else if (timeStr.includes('T')) {
    [datePart, timePart] = timeStr.split('T')
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
  if (status === 'rejected') {
    return '请填写重新确认意见（可选）'
  }
  return '请填写你的审核意见（可选）'
}

export function getRowClassName(status) {
  if (status === 'completed') return 'status-completed-row'
  if (status === 'confirmed') return 'status-completed-row'
  if (status === 'rejected') return 'status-rejected-row'
  if (status === 'current') return 'status-current-row'
  if (status === 'on_hold') return 'status-on-hold-row'
  if (status === 'in_progress') return 'status-in-progress-row'
  if (status === 'pending') return 'status-pending-row'
  return ''
}

export function getCellStyle(status) {
  if (status === 'current' || status === 'in_progress') {
    return {
      backgroundColor: '#e3f2fd',
      borderBottom: '1px solid #bbdefb'
    }
  }
  if (status === 'rejected') {
    return {
      backgroundColor: '#ffebee',
      borderBottom: '1px solid #ffcdd2'
    }
  }
  if (status === 'completed' || status === 'confirmed') {
    return {
      backgroundColor: '#e8f5e8',
      borderBottom: '1px solid #c8e6c9'
    }
  }
  if (status === 'on_hold') {
    return {
      backgroundColor: '#fff3e0',
      borderBottom: '1px solid #ffe0b2'
    }
  }
  if (status === 'pending') {
    return {
      backgroundColor: '#fafafa',
      borderBottom: '1px solid #e0e0e0'
    }
  }
  return {}
}