export const CANCELLED_STATUS = 'cancelled'

export const FLOW_PROGRESS_STEPS = [
  { key: 'released', statuses: ['released'], color: '#94a3b8' },
  { key: 'start', statuses: ['apply_for_start', 'eng_approved'], color: '#3b82f6' },
  { key: 'confirm', statuses: ['construction_confirmed', 'team_received'], color: '#06b6d4' },
  { key: 'signed', statuses: ['construction_signed'], color: '#8b5cf6' },
  { key: 'process', statuses: ['process_closed'], color: '#10b981' },
  { key: 'equipment', statuses: ['equipment_closed'], color: '#059669' }
]

export const normalizeOrderStatus = (status) => (typeof status === 'string' ? status : '')

export const getProgressStepIndex = (status) => {
  const normalizedStatus = normalizeOrderStatus(status)
  if (!normalizedStatus || normalizedStatus === CANCELLED_STATUS) return -1
  return FLOW_PROGRESS_STEPS.findIndex(step => step.statuses.includes(normalizedStatus))
}

export const getStatusStyle = (status) => {
  const styleMap = {
    released: { tagBg: '#f1f5f9', tagText: '#64748b', tagBorder: '#e2e8f0' },
    apply_for_start: { tagBg: '#dbeafe', tagText: '#2563eb', tagBorder: '#bfdbfe' },
    eng_approved: { tagBg: '#dbeafe', tagText: '#2563eb', tagBorder: '#bfdbfe' },
    construction_confirmed: { tagBg: '#ecfeff', tagText: '#0891b2', tagBorder: '#cffafe' },
    team_received: { tagBg: '#ecfeff', tagText: '#0891b2', tagBorder: '#cffafe' },
    construction_signed: { tagBg: '#f5f3ff', tagText: '#7c3aed', tagBorder: '#e9d5ff' },
    process_closed: { tagBg: '#dcfce7', tagText: '#16a34a', tagBorder: '#bbf7d0' },
    equipment_closed: { tagBg: '#dcfce7', tagText: '#15803d', tagBorder: '#bbf7d0' },
    cancelled: { tagBg: '#fee2e2', tagText: '#dc2626', tagBorder: '#fecaca' }
  }
  return styleMap[status] || { tagBg: '#f1f5f9', tagText: '#64748b', tagBorder: '#e2e8f0' }
}

export const getStatusLabel = (status) => {
  const labelMap = {
    released: '已发布',
    apply_for_start: '申请开工',
    eng_approved: '工程审批',
    construction_confirmed: '施工确认',
    team_received: '班组签收',
    construction_signed: '施工签字',
    process_closed: '工序关闭',
    equipment_closed: '设备关闭',
    cancelled: '已取消'
  }
  return labelMap[status] || status || '未知'
}

export const buildOrderProgressModel = (status) => {
  const normalizedStatus = normalizeOrderStatus(status)
  const isCancelled = normalizedStatus === CANCELLED_STATUS
  const stepIndex = getProgressStepIndex(normalizedStatus)
  const completedSteps = stepIndex >= 0 ? stepIndex + 1 : 0
  const statusStyle = getStatusStyle(normalizedStatus)

  const segments = FLOW_PROGRESS_STEPS.map((step, index) => {
    if (isCancelled) {
      return {
        key: `${step.key}-${index}`,
        color: '#ef4444',
        state: 'is-cancelled'
      }
    }
    return {
      key: `${step.key}-${index}`,
      color: step.color,
      state: index <= stepIndex ? 'is-complete' : 'is-pending'
    }
  })

  return {
    isCancelled,
    completedSteps,
    segments,
    progressText: isCancelled
      ? '流程已取消'
      : `进度 ${Math.max(completedSteps, 1)}/${FLOW_PROGRESS_STEPS.length}`,
    tagStyle: {
      backgroundColor: statusStyle.tagBg,
      color: statusStyle.tagText,
      borderColor: statusStyle.tagBorder
    }
  }
}

export const parseWorkersByRole = (workers) => {
  if (!workers) return []

  let workerObj = workers
  if (typeof workers === 'string') {
    try {
      workerObj = JSON.parse(workers)
    } catch (error) {
      return []
    }
  }

  if (Array.isArray(workerObj)) {
    return workerObj.length ? [{ role: '班组成员', names: workerObj }] : []
  }

  if (typeof workerObj !== 'object') return []

  return Object.entries(workerObj)
    .map(([role, names]) => ({
      role,
      names: Array.isArray(names) ? names.filter(Boolean) : []
    }))
    .filter(group => group.names.length > 0)
}

export const extractDayFromFormattedTime = (formattedTime) => {
  if (!formattedTime) return 1
  const dayMatch = formattedTime.match(/第(\d+)天/)
  return dayMatch && dayMatch[1] ? parseInt(dayMatch[1], 10) : 1
}

export const getTimeFromFormattedTime = (formattedTime) => {
  if (!formattedTime) return '08:00'
  const timeMatch = formattedTime.match(/\d{2}:\d{2}/)
  return timeMatch ? timeMatch[0] : '08:00'
}

export const convertToTimestamp = (day, time) => {
  const [hours, minutes] = time.split(':').map(Number)
  const baseDate = new Date(2023, 0, 1)
  baseDate.setDate(baseDate.getDate() + day - 1)
  baseDate.setHours(hours, minutes, 0, 0)
  return baseDate.getTime()
}

export const formatTimeOnly = (timestamp) => {
  const date = new Date(timestamp)
  return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
}

export const formatNumber = (value) => {
  if (value === undefined || value === null) return '0.000'
  return parseFloat(value).toFixed(3)
}

export const getWorkerStatusType = (status) => {
  const statusMap = {
    '工作中': 'warning',
    '空闲中': 'success',
    '已完成': 'info'
  }
  return statusMap[status] || 'info'
}

export const getTaskStatusType = (status) => {
  const statusMap = {
    '进行中': 'warning',
    '已完成': 'success',
    '未开始': 'info'
  }
  return statusMap[status] || 'info'
}

export const getPieChartColor = (material) => {
  const usageRate = material.used / material.stock
  if (usageRate > 0.9) return '#ff4d4f'
  if (usageRate > 0.5) return '#faad14'
  return '#52c41a'
}

export const getMaterialCategory = (materialName) => {
  const pipelineKeywords = ['钢材', '不锈钢管', '管道']
  const connectorKeywords = ['阀门', '法兰', '螺栓', '垫片']
  const equipmentKeywords = ['密封胶', '电缆', '仪表', '泵体']

  if (pipelineKeywords.some(keyword => materialName.includes(keyword))) {
    return 'pipeline'
  } else if (connectorKeywords.some(keyword => materialName.includes(keyword))) {
    return 'connector'
  } else if (equipmentKeywords.some(keyword => materialName.includes(keyword))) {
    return 'equipment'
  }
  return 'equipment'
}

export const getTimeSlotIndex = (time) => {
  const [hour, minute] = time.split(':').map(Number)
  return (hour - 8) * 2 + (minute >= 30 ? 1 : 0)
}

export const getDisplayEndTimeCalendar = (endTimeFormatted) => {
  const endMatch = endTimeFormatted.match(/第(\d+)天 08:00/)
  if (endMatch) {
    const day = parseInt(endMatch[1])
    if (day > 1) {
      return `第${day - 1}天 20:00`
    }
  }
  return endTimeFormatted
}

export const getCalendarTaskPositionStyle = (task) => {
  if (!task) return {}

  let startTimeFormatted = task.startTimeFormatted
  let endTimeFormatted = task.endTimeFormatted

  const endMatch = endTimeFormatted.match(/第(\d+)天 08:00/)
  if (endMatch) {
    const day = parseInt(endMatch[1])
    if (day > 1) {
      endTimeFormatted = `第${day - 1}天 20:00`
    }
  }

  const startTime = getTimeFromFormattedTime(startTimeFormatted)
  const endTime = getTimeFromFormattedTime(endTimeFormatted)

  const startIndex = getTimeSlotIndex(startTime)
  const endIndex = getTimeSlotIndex(endTime)

  const top = startIndex * 50 + 20
  const height = (endIndex - startIndex) * 50

  const equipment = task.equipment || task.device
  let backgroundColor = '#ccc'

  if (equipment) {
    const hash = Array.from(equipment).reduce((acc, char) => {
      return char.charCodeAt(0) + ((acc << 5) - acc)
    }, 0)
    const colors = ['#5470C6', '#91CC75', '#EE6666', '#73C0DE', '#3BA272', '#FC8452', '#9A60B4', '#EA7CCC']
    backgroundColor = colors[Math.abs(hash) % colors.length]
  }

  return {
    top: `${top}px`,
    height: `${height}px`,
    backgroundColor: backgroundColor,
    margin: '0',
    padding: '0'
  }
}