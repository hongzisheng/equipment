<template>
  <div class="schedule-board">
    <!-- 顶部导航栏 -->
    <div class="board-header">
      <div class="header-left">
        <span class="my-schedule">我的排程</span>
        <span class="task-summary">今日任务 {{ getTodayTaskCounts().total }} 已完成 {{ getTodayTaskCounts().completed }} 进行 {{ getTodayTaskCounts().inProgress }}</span>
      </div>
      <div class="header-center">
        <span class="staff-tag">员工 | 仪表工 | 机修一班</span>
      </div>
      <div class="header-right">
        <button @click="prevWeek" class="week-nav prev">上一周</button>
        <span class="current-week">{{ currentWeekLabel }}</span>
        <button @click="nextWeek" class="week-nav next">下一周</button>
        <span class="week-number">第{{ currentWeekNumber }}周</span>
        <button @click="setViewMode('week')" :class="['view-btn', { active: viewMode === 'week' }]">周视图</button>
        <button @click="setViewMode('day')" :class="['view-btn', { active: viewMode === 'day' }]">日视图</button>
        <button @click="setViewMode('status')" :class="['view-btn', { active: viewMode === 'status' }]">状态</button>
      </div>
    </div>

    <!-- 设备/排程视图标签 -->
    <div class="view-tabs">
     
      <span @click="setScheduleView('schedule')" :class="['tab', { active: scheduleView === 'schedule' }]">排程视图</span>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>正在加载任务数据...</p>
    </div>

    <!-- 错误提示 -->
    <div v-if="error" class="error-container">
      <p class="error-message">{{ error }}</p>
      <button @click="loadWorkerTasks" class="retry-btn">重试</button>
    </div>

    <!-- 日历表格主体 -->
    <div v-if="!loading && !error" class="calendar-wrapper">
      <!-- 表头：时间 + 星期列 (显示第N天) -->
      <div class="calendar-header">
        <div class="time-col-header">时间</div>
        <div class="day-col-header" v-for="(day, idx) in weekDays" :key="idx">
          <div class="day-name">{{ day.label }}</div> <!-- 第1天, 第2天... 不显示日期数字 -->
        </div>
      </div>

      <!-- 时间行：从 08:00 到 20:00，每半小时一行 -->
      <div class="calendar-body">
        <div v-for="timeSlot in timeSlots" :key="timeSlot.time" class="time-row">
          <div class="time-label">{{ timeSlot.time }}</div>
          <div v-for="day in weekDays" :key="day.date.getTime()" class="task-cell" @click="handleCellClick(day.date, timeSlot.time)">
            <!-- 修改任务渲染逻辑，合并相同任务 -->
            <template v-for="taskGroup in getTaskGroupsForDay(day.date)" :key="taskGroup.task_id">
              <div 
                v-if="isTaskVisibleInSlot(taskGroup, timeSlot)" 
                class="task-item" 
                :style="{...getTaskStyle(taskGroup), ...getTaskPositionStyle(taskGroup, timeSlot)}"
                :class="getTaskClass(taskGroup)"
                @click.stop="selectTask(taskGroup)"
              >
                <div class="task-header">
                  <span class="task-name">{{ taskGroup.process_name }}</span>
                  <span :class="['status-tag', `tag-${taskGroup.task_status}`]">
                    {{ getStatusTagText(taskGroup.task_status) }}
                  </span>
                </div>
                <span class="task-time">{{ formatTaskTime(taskGroup) }}</span>
                <span class="task-device">{{ taskGroup.equipment_name }}</span>
              </div>
            </template>
          </div>
        </div>
      </div>
    </div>

    <!-- 任务详情弹窗 -->
    <div v-if="selectedTask" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>任务详情</h3>
          <button @click="closeModal" class="close-btn">×</button>
        </div>
        <div class="task-details">
          <div class="detail-item">
            <span class="detail-label">任务编号:</span>
            <span class="detail-value">{{ selectedTask.task_code }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">工序名称:</span>
            <span class="detail-value">{{ selectedTask.process_name }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">时间:</span>
            <span class="detail-value">{{ formatDetailDateTime(selectedTask) }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">设备:</span>
            <span class="detail-value">{{ selectedTask.equipment_name }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">工单编号:</span>
            <span class="detail-value">{{ selectedTask.order_number }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">工单标题:</span>
            <span class="detail-value">{{ selectedTask.work_order_title }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">描述:</span>
            <span class="detail-value">{{ selectedTask.description }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">预估工时:</span>
            <span class="detail-value">{{ selectedTask.estimated_hours }}小时</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">优先级:</span>
            <span class="detail-value">{{ getPriorityText(selectedTask.priority) }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">状态:</span>
            <span :class="['status-badge', `status-${selectedTask.task_status}`]">
              {{ getStatusText(selectedTask.task_status) }}
            </span>
          </div>
        </div>
        <div class="modal-actions">
          <button 
            v-if="selectedTask.task_status === 'pending'" 
            @click="updateTaskStatus('in_progress')"
            class="action-btn start-btn"
          >
            <span class="btn-icon">▶</span>
            开始任务
          </button>
          <button 
            v-if="selectedTask.task_status === 'in_progress'" 
            @click="updateTaskStatus('completed')"
            class="action-btn complete-btn"
          >
            <span class="btn-icon">✓</span>
            完成任务
          </button>
          <button @click="closeModal" class="action-btn close-action-btn">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import request from '@/utils/request'

// 视图模式
const viewMode = ref('week')
const scheduleView = ref('schedule')

// 当前日期 (用于周计算)
const currentDate = ref(new Date())
const selectedTask = ref(null)

// 加载状态和错误处理
const loading = ref(false)
const error = ref('')

// 时间槽：从08:00到20:00，每半小时
const timeSlots = computed(() => {
  const slots = []
  for (let hour = 8; hour <= 20; hour++) {
    for (let minute = 0; minute < 60; minute += 30) {
      // 确保只包含到20:00，不包含20:30
      if (hour === 20 && minute > 0) continue
      const timeStr = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`
      slots.push({
        time: timeStr,
        hour,
        minute
      })
    }
  }
  return slots
})

// 当前显示的周索引 (0表示第一周，1表示第二周)
const currentWeekIndex = ref(0)

// 当前工人ID（这里假设为固定值，实际应该从登录信息获取）
const workerId = ref(null) 

// 任务数据
const tasks = ref([])



// 修改解析调度时间字符串函数，同时记录最大天数
const parseScheduledTime = (timeString) => {
  if (!timeString) return null;
  let date = null;
  let dayIndex = null;
  const startOfWeek = getStartOfWeek(currentDate.value);
 const dayMatch = timeString.match(/第(\d+)天\s+(\d{2}):(\d{2})/);
  if (dayMatch) {
    dayIndex = parseInt(dayMatch[1]);
    const hours = parseInt(dayMatch[2]);
    const minutes = parseInt(dayMatch[3]);
    date = new Date(startOfWeek);
    date.setDate(date.getDate() + dayIndex - 1);
    date.setHours(hours, minutes, 0, 0);
  } else {
    // 匹配 "YYYY-MM-DD HH:MM:SS"
    const dateTimeMatch = timeString.match(/^(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})$/);
    if (dateTimeMatch) {
      const year = parseInt(dateTimeMatch[1]);
      const month = parseInt(dateTimeMatch[2]) - 1;
      const day = parseInt(dateTimeMatch[3]);
      const hours = parseInt(dateTimeMatch[4]);
      const minutes = parseInt(dateTimeMatch[5]);
      const seconds = parseInt(dateTimeMatch[6]);
      date = new Date(year, month, day, hours, minutes, seconds);
      
      // 计算相对于当前周的第几天
      const diffTime = date - startOfWeek;
      dayIndex = Math.floor(diffTime / (1000 * 60 * 60 * 24)) + 1;
    }
  }

  if (date && !isNaN(date.getTime())) {
    return { date, day: dayIndex };
  }
  return null;
};

// 修改周天数计算，根据最大天数动态显示
const weekDays = computed(() => {
 const days = [];
  const startOfWeek = getStartOfWeek(currentDate.value);
  const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
  for (let i = 0; i < 7; i++) {
    const date = new Date(startOfWeek);
    date.setDate(date.getDate() + i);
    const month = date.getMonth() + 1;
    const day = date.getDate();
    const weekday = weekdays[date.getDay()];
    days.push({
      date,
      label: `${month}/${day} ${weekday}` // 如 "3/17 周一"
    });
  }
  return days
})

// 修改当前周显示计算
const currentWeekLabel = computed(() => {
  if (weekDays.value.length === 0) return ''
  
  const start = weekDays.value[0].date
  const end = weekDays.value[weekDays.value.length - 1].date
  return `${start.getMonth() + 1}/${start.getDate()} - ${end.getMonth() + 1}/${end.getDate()}`
})

// 当前周数（简单计算）
const currentWeekNumber = computed(() => {
  const firstDayOfYear = new Date(currentDate.value.getFullYear(), 0, 1)
  const pastDays = (currentDate.value - firstDayOfYear) / 86400000
  return Math.ceil((pastDays + firstDayOfYear.getDay() + 1) / 7)
})
// 新增日期解析函数
const parseDateTimeString = (dateTimeStr) => {
  if (!dateTimeStr) return null
  const [datePart, timePart] = dateTimeStr.split(' ')
  if (!datePart || !timePart) return null
  const [year, month, day] = datePart.split('-').map(Number)
  const [hour, minute, second] = timePart.split(':').map(Number)
  return new Date(year, month - 1, day, hour, minute, second)
}
// 修改获取工人任务数据函数，在加载数据后更新最大天数
const loadWorkerTasks = async () => {
  try {
    loading.value = true
    error.value = ''
    
    const response = await request.get(`http://localhost:5000/api/worker-workorders/${workerId.value}`)
    
    if (response.success) {
      // 转换API数据格式为组件内部使用的格式
      tasks.value = response.data.map(task => {
        const startTimeInfo = parseScheduledTime(task.scheduled_start_time)
        const endTimeInfo = parseScheduledTime(task.scheduled_end_time)

        return {
          ...task,
          id: task.task_id,
          name: task.process_name,
          device: task.equipment_name,
          startTime: startTimeInfo ? startTimeInfo.date : null,
          endTime: endTimeInfo ? endTimeInfo.date : null,
          originalDay: startTimeInfo ? startTimeInfo.day : null, // 保存原始天数信息
          status: task.task_status,
          type: 'maintenance'
        }
        
      })
    } else {
      error.value = response.message || '获取任务数据失败'
    }
  } catch (err) {
    console.error('获取任务数据失败:', err)
    error.value = '网络请求失败，请稍后重试'
  } finally {
    loading.value = false
  }
  console.log('所有任务:', tasks.value);
}

// 解析排程时间字符串
const parseScheduleTime = (timeStr, weekDaysList) => {
  if (!timeStr) return null
  
  // 解析格式："第1天 08:00" 或 "第8天 14:30"
  const match = timeStr.match(/第(\d+)天\s+(\d{2}):(\d{2})/)
  if (match) {
    const dayIndex = parseInt(match[1]) - 1 // 第1天对应索引0
    let hours = parseInt(match[2])
    const minutes = parseInt(match[3])
    
    // 如果结束时间为8:00，则改为20:00
    if (hours === 8 && minutes === 0) {
      hours = 20
    }
    
    if (weekDaysList[dayIndex]) {
      const date = new Date(weekDaysList[dayIndex].date)
      date.setHours(hours, minutes, 0, 0)
      return date
    }
  }
  return null
}

// 修改获取指定日期的所有任务并按ID分组函数
const getTaskGroupsForDay = (date) => {
  const dayTasks = tasks.value.filter(task => {
    if (!task.startTime) return false
    return task.startTime.toDateString() === date.toDateString()
  })
  
  // 按任务ID分组，相同ID的任务合并为一组
  const groupedTasks = {}
  dayTasks.forEach(task => {
    if (!groupedTasks[task.id]) {
      groupedTasks[task.id] = { ...task, slots: [] }
    }
    // 记录该任务占据的时间槽
    const taskStart = new Date(task.startTime)
    const taskEnd = task.endTime ? new Date(task.endTime) : new Date(taskStart.getTime() + 30 * 60000) // 默认30分钟
    
    // 特殊处理：如果任务结束时间是20:00，则改为20:00
    const adjustedEndTime = taskEnd.getHours() === 20 && taskEnd.getMinutes() === 0 
      ? new Date(taskEnd.getTime() + 1000) // 微调1秒确保包含20:00槽
      : taskEnd
    
    const currentTime = new Date(taskStart)
    
    console.log(`任务 ${task.id} 开始时间:`, taskStart.toLocaleTimeString(), '结束时间:', taskEnd.toLocaleTimeString())
    
    while (currentTime < adjustedEndTime) {
      // 确保不超过20:00
      if (currentTime.getHours() > 20 || (currentTime.getHours() === 20 && currentTime.getMinutes() > 0)) {
        break
      }
      
      const timeStr = `${currentTime.getHours().toString().padStart(2, '0')}:${currentTime.getMinutes().toString().padStart(2, '0')}`
      if (!groupedTasks[task.id].slots.includes(timeStr)) {
        groupedTasks[task.id].slots.push(timeStr)
      }
      console.log(`任务 ${task.id} 包含时间槽:`, timeStr)
      currentTime.setMinutes(currentTime.getMinutes() + 30)
    }
  })
  
  // 调试输出
  Object.values(groupedTasks).forEach(group => {
    console.log(`任务组 ${group.id} 时间槽:`, group.slots)
  })
  
  return Object.values(groupedTasks)
}

// 判断任务在指定时间槽是否可见（只在第一个时间槽显示）
const isTaskVisibleInSlot = (taskGroup, timeSlot) => {
  // 确保任务组有slots数组且不为空
  if (!taskGroup.slots || taskGroup.slots.length === 0) {
    return false
  }
  
  // 检查是否匹配第一个时间槽
  return taskGroup.slots[0] === timeSlot.time
}

// 获取任务的位置样式（合并高度）
const getTaskPositionStyle = (taskGroup, timeSlot) => {
  if (!isTaskVisibleInSlot(taskGroup, timeSlot)) {
    return { display: 'none' }
  }
  
  // 计算任务跨越的时间槽数量
  const slotCount = taskGroup.slots ? taskGroup.slots.length : 1
  const height = slotCount * 44 - 2 // 44px每行高度，减去边框间距
  
  return {
    height: `${height}px`,
    position: 'absolute',
    top: '0',
    left: '4px',
    right: '4px',
    zIndex: 10
  }
}

// 选择任务（用于弹窗显示）
const selectTask = (task) => {
  selectedTask.value = { ...task }
}

// 获取指定时间槽的任务（保持原有逻辑用于其他地方）
const getTasksForTimeSlot = (date, timeSlot) => {
  const slotTime = new Date(date)
  slotTime.setHours(timeSlot.hour, timeSlot.minute, 0)
  
  return tasks.value.filter(task => {
    if (!task.startTime || !task.endTime) return false
    
    const taskStart = new Date(task.startTime)
    const taskEnd = new Date(task.endTime)
    
    // 检查是否在同一日期 (基于date的日期部分)
    const sameDay = taskStart.toDateString() === date.toDateString()
    if (!sameDay) return false
    
    // 检查时间是否在任务范围内 [start, end)
    return slotTime >= taskStart && slotTime < taskEnd
  })
}

// 获取今日任务统计
const getTodayTaskCounts = () => {
  const today = new Date()
  const todayTasks = tasks.value.filter(task => {
    if (!task.startTime) return false
    return task.startTime.toDateString() === today.toDateString()
  })
  
  return {
    total: todayTasks.length,
    completed: todayTasks.filter(t => t.status === 'completed').length,
    inProgress: todayTasks.filter(t => t.status === 'in_progress').length
  }
}

// 获取任务样式 - 修改为按设备分配颜色
const getTaskStyle = (task) => {
  // 按设备名称分配颜色，确保相同设备使用相同颜色
  const deviceColors = {
    '反应釜R-101': { bg: '#FFE4E1', border: '#FF6B6B', text: '#CC0000' },      // 浅红
    '离心泵P-101': { bg: '#E0FFFF', border: '#40E0D0', text: '#006666' },    // 青色
    '空冷器C-101': { bg: '#FFFACD', border: '#FFD700', text: '#B8860B' },      // 金色
    '压缩机K-101': { bg: '#E6E6FA', border: '#9370DB', text: '#4B0082' },      // 紫色
    '冷却塔T-101': { bg: '#F0FFF0', border: '#32CD32', text: '#006400' },      // 绿色
    '电气柜E-101': { bg: '#F5F5DC', border: '#DAA520', text: '#8B4513' },      // 黄褐色
    '备用设备': { bg: '#F0F8FF', border: '#5F9EA0', text: '#004C4C' },         // 蓝绿色
    'default': { bg: '#F8F9FA', border: '#6C757D', text: '#343A40' }           // 默认灰色
  }
  
  const colorScheme = deviceColors[task.device] || deviceColors.default
  
  return {
    backgroundColor: colorScheme.bg,
    borderLeftColor: colorScheme.border,
    color: colorScheme.text
  }
}

// 获取任务类名
const getTaskClass = (task) => {
  const duration = task.endTime && task.startTime 
    ? (task.endTime - task.startTime) / (1000 * 60 * 60) // 小时
    : 0.5 // 默认0.5小时
  return {
    'multi-hour': duration >= 2,
    [`status-${task.status}`]: true
  }
}

// 格式化任务时间 (用于任务卡片内: 10:00-12:00)
const formatTaskTime = (task) => {
  if (!task.startTime) return '时间未定'
  
  const start = task.startTime
  const end = task.endTime || new Date(start.getTime() + 30 * 60000) // 默认30分钟
  
  return `${start.getHours().toString().padStart(2, '0')}:${start.getMinutes().toString().padStart(2, '0')}-${end.getHours().toString().padStart(2, '0')}:${end.getMinutes().toString().padStart(2, '0')}`
}

// 格式化详情页日期时间: 第1天 10:00-12:00
const formatDetailDateTime = (task) => {
  // 从原始数据中获取调度时间
  if (task.scheduled_start_time && task.scheduled_end_time) {
    return `${task.scheduled_start_time}-${task.scheduled_end_time.split(' ')[1]}`
  }
  
  // 备用方案：基于解析后的时间
  if (task.startTime) {
    const taskDate = new Date(task.startTime)
    let dayIndex = -1
    for (let i = 0; i < weekDays.value.length; i++) {
      if (weekDays.value[i].date.toDateString() === taskDate.toDateString()) {
        dayIndex = i + 1
        break
      }
    }
    const dayStr = dayIndex !== -1 ? `第${dayIndex}天` : formatDate(taskDate)
    const timeStr = formatTaskTime(task)
    return `${dayStr} ${timeStr}`
  }
  
  return '时间未定'
}

// 格式化日期 (备用)
const formatDate = (date) => {
  return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')}`
}

// 获取状态文本
const getStatusText = (status) => {
  return statusTextMap[status] || status;
}

// 获取状态标签文本
const getStatusTagText = (status) => {
  return statusTextMap[status] || status;
}

// 获取优先级文本
const getPriorityText = (priority) => {
  const map = {
    'low': '低',
    'medium': '中',
    'high': '高'
  }
  return map[priority] || priority
}

// 处理单元格点击
const handleCellClick = (date, timeSlot) => {
  const slotTime = new Date(date)
  const [hour, minute] = timeSlot.split(':').map(Number)
  slotTime.setHours(hour, minute, 0)
  
  // 查找该时间槽内的任务组
  const dayTasks = getTaskGroupsForDay(date)
  const clickedTask = dayTasks.find(taskGroup => {
    if (!taskGroup.startTime || !taskGroup.endTime) return false
    const taskStart = new Date(taskGroup.startTime)
    const taskEnd = new Date(taskGroup.endTime)
    return slotTime >= taskStart && slotTime < taskEnd
  })
  
  if (clickedTask) {
    selectedTask.value = { ...clickedTask }
  }
}
//状态映射
const statusTextMap = {
  'released': '待开始',
  'apply_for_start': '申请开工',
  'eng_approved': '工程师确认',
  'construction_confirmed': '施工确认',
  'team_received': '班组受理',
  'construction_signed': '施工回签',
  'process_closed': '工艺存储关闭',
  'equipment_closed': '设备部关闭',
  'cancelled': '取消',
  // 兼容旧状态
  'pending': '待开始',
  'in_progress': '进行中',
  'completed': '已完成'
};
// 更新任务状态
const updateTaskStatus = async (newStatus) => {
  if (selectedTask.value) {
    try {
      // 这里应该调用更新任务状态的API
      // await request.put(`/api/tasks/${selectedTask.value.task_id}/status`, { status: newStatus })
      
      // 临时更新本地状态（实际应该等待API响应后再更新）
      const taskIndex = tasks.value.findIndex(t => t.task_id === selectedTask.value.task_id)
      if (taskIndex !== -1) {
        tasks.value[taskIndex].status = newStatus
        tasks.value[taskIndex].task_status = newStatus
        selectedTask.value.status = newStatus
        selectedTask.value.task_status = newStatus
      }
      
      // 显示成功提示
      console.log(`任务状态已更新为: ${getStatusText(newStatus)}`)
    } catch (err) {
      console.error('更新任务状态失败:', err)
      // 显示错误提示
    }
  }
}

// 关闭弹窗
const closeModal = () => {
  selectedTask.value = null
}

// 周导航 - 修改为在两个周之间切换
const prevWeek = () => {
  if (currentWeekIndex.value > 0) {
    // 如果当前是第二周，切换到第一周
    currentWeekIndex.value = 0
  } else {
    // 如果当前是第一周，切换到前一周的第一周
    const newDate = new Date(currentDate.value)
    newDate.setDate(newDate.getDate() - 7)
    currentDate.value = newDate
    currentWeekIndex.value = 0
  }
  // 重新加载任务数据
  loadWorkerTasks()
}

const nextWeek = () => {
  if (currentWeekIndex.value < 1) {
    // 如果当前是第一周，切换到第二周
    currentWeekIndex.value = 1
  } else {
    // 如果当前是第二周，切换到下一周的第一周
    const newDate = new Date(currentDate.value)
    newDate.setDate(newDate.getDate() + 7)
    currentDate.value = newDate
    currentWeekIndex.value = 0
  }
  // 重新加载任务数据
  loadWorkerTasks()
}

// 获取周起始 (周一为一周开始)
const getStartOfWeek = (date) => {
  const d = new Date(date)
  const day = d.getDay()
  const diff = d.getDate() - day + (day === 0 ? -6 : 1) // 周一作为第一天
  return new Date(d.setDate(diff))
}

// 设置视图模式
const setViewMode = (mode) => {
  viewMode.value = mode
}

// 设置排程视图
const setScheduleView = (view) => {
  scheduleView.value = view
}

// 组件挂载时加载数据
onMounted(() => {
  const isLoggedIn = localStorage.getItem('isLoggedIn')
  if (!isLoggedIn) {
    router.push('/login')
    return
  }
  // 获取用户信息
  const userStr = localStorage.getItem('user')
  if (userStr) {
    const user = JSON.parse(userStr)
    workerId.value = user.worker_id  // 从登录响应中保存的 user 对象
  }
  loadWorkerTasks()
})
</script>

<style scoped>
/* 全局样式 */
.schedule-board {
  font-family: 'Microsoft YaHei', 'PingFang SC', 'Helvetica Neue', Helvetica, Arial, sans-serif;
  background-color: #f2f4f8;
  min-height: 100vh;
  padding: 20px 24px;
  box-sizing: border-box;
  color: #1e293b;
  font-size: 12px;
}

/* 顶部导航栏 */
.board-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: #ffffff;
  padding: 10px 20px;
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.04);
  margin-bottom: 16px;
  border: 1px solid #e9edf2;
  font-size: 12px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.my-schedule {
  font-weight: 600;
  color: #0f1829;
  font-size: 14px;
}

.task-summary {
  color: #5a6c7e;
  background-color: #f0f3f7;
  padding: 4px 10px;
  border-radius: 30px;
  font-size: 12px;
}

.header-center .staff-tag {
  color: #2d4059;
  background-color: #f0f3f7;
  padding: 4px 12px;
  border-radius: 30px;
  font-weight: 500;
  font-size: 12px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.week-nav {
  background: none;
  border: 1px solid #d0d8e2;
  padding: 4px 12px;
  border-radius: 30px;
  color: #1e293b;
  cursor: pointer;
  font-size: 12px;
  background-color: #ffffff;
  transition: all 0.2s;
}

.week-nav:hover {
  background-color: #f0f3f7;
  border-color: #0066cc;
}

.current-week {
  font-weight: 600;
  color: #0066cc;
  background-color: #e6f0ff;
  padding: 4px 12px;
  border-radius: 30px;
  font-size: 12px;
}

.week-number {
  color: #4f6f8f;
  margin-left: 4px;
  font-size: 12px;
}

.view-btn {
  background: none;
  border: 1px solid #d0d8e2;
  padding: 4px 12px;
  border-radius: 30px;
  color: #4f6f8f;
  cursor: pointer;
  font-size: 12px;
  background-color: #ffffff;
  transition: all 0.2s;
}

.view-btn:hover {
  background-color: #f0f3f7;
}

.view-btn.active {
  background-color: #0066cc;
  color: white;
  border-color: #0066cc;
}

/* 设备/排程视图标签 */
.view-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 12px;
  padding-left: 4px;
}

.tab {
  padding: 4px 16px;
  background-color: #f0f3f7;
  border-radius: 30px;
  color: #4f6f8f;
  font-size: 12px;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.2s;
}

.tab:hover {
  background-color: #e4e9f0;
}

.tab.active {
  background-color: #ffffff;
  color: #0066cc;
  border-color: #0066cc;
  font-weight: 500;
}

/* 加载状态样式 */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background-color: #ffffff;
  border-radius: 12px;
  border: 1px solid #e4e9f0;
  margin-bottom: 16px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #0066cc;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-container p {
  color: #5a6c7e;
  font-size: 14px;
  margin: 0;
}

/* 错误提示样式 */
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background-color: #ffffff;
  border-radius: 12px;
  border: 1px solid #e4e9f0;
  margin-bottom: 16px;
}

.error-message {
  color: #dc3545;
  font-size: 14px;
  margin-bottom: 16px;
  text-align: center;
}

.retry-btn {
  background-color: #0066cc;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: background-color 0.2s;
}

.retry-btn:hover {
  background-color: #0056b3;
}

/* 日历表格包装 */
.calendar-wrapper {
  background-color: #ffffff;
  border-radius: 12px;
  border: 1px solid #e4e9f0;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0,0,0,0.02);
}

/* 日历表头 */
.calendar-header {
  display: flex;
  background-color: #f8fafd;
  border-bottom: 1px solid #dbe1e9;
  font-weight: 500;
}

.time-col-header {
  width: 120px;  /* 统一宽度 */
  padding: 12px 4px;
  text-align: center;
  color: #4f6f8f;
  border-right: 1px solid #dbe1e9;
  font-size: 12px;
  background-color: #f8fafd;
  flex-shrink: 0;
}

.day-col-header {
  flex: 1;
  min-width: 120px;  /* 统一最小宽度 */
  padding: 12px 4px;
  text-align: center;
  border-right: 1px solid #dbe1e9;
  background-color: #f8fafd;
  font-size: 12px;
}

.day-col-header:last-child {
  border-right: none;
}

.day-name {
  font-weight: 600;
  color: #1e293b;
  font-size: 13px;
}

/* 日历主体 */
.calendar-body {
  display: flex;
  flex-direction: column;
  max-height: 78vh;
  overflow-y: auto;
}

.time-row {
  display: flex;
  border-bottom: 1px solid #eef2f6;
  min-height: 44px;
}

.time-row:last-child {
  border-bottom: none;
}

.time-label {
  width: 120px;  /* 统一宽度 */
  flex-shrink: 0;
  padding: 8px 4px;
  text-align: center;
  color: #4f6f8f;
  border-right: 1px solid #dbe1e9;
  background-color: #fafcfd;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.task-cell {
  flex: 1;
  min-width: 150px;  /* 统一最小宽度 */
  padding: 0;
  border-right: 1px solid #eef2f6;
  background-color: #ffffff;
  transition: background 0.1s;
  position: relative;
  cursor: pointer;
  height: 44px;
}

.task-cell:last-child {
  border-right: none;
}

.task-cell:hover {
  background-color: #f9fcff;
}

/* 任务卡片样式 - 修改为绝对定位 */
.task-item {
  border-left: 4px solid #f3aa6d;
  border-radius: 0 6px 6px 0;
  padding: 8px 10px;
  font-size: 11px;
  line-height: 1.4;
  box-shadow: 0 2px 6px rgba(0,0,0,0.08);
  display: flex;
  flex-direction: column;
  justify-content: center;
  word-break: break-word;
  background-color: white;
  color: #2c3e50;
  /* 绝对定位相关样式在JS中动态设置 */
}

.task-item:last-child {
  margin-bottom: 0;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 4px;
  gap: 6px;
}

.task-name {
  font-weight: 600;
  color: inherit;
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 11px;
  flex: 1;
}

.status-tag {
  font-size: 9px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 10px;
  white-space: nowrap;
  flex-shrink: 0;
}

.tag-pending {
  background-color: #fff3cd;
  color: #856404;
  border: 1px solid #ffeaa7;
}

.tag-in-progress {
  background-color: #cce5ff;
  color: #004085;
  border: 1px solid #99ccff;
}

.tag-completed {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #b8e6b8;
}

.task-time {
  color: inherit;
  font-size: 10px;
  display: block;
  margin-bottom: 2px;
  opacity: 0.9;
}

.task-device {
  color: inherit;
  font-size: 10px;
  font-weight: 500;
  display: block;
  opacity: 0.8;
}

/* 状态样式 */
.status-pending {
  opacity: 0.9;
}

.status-in-progress {
  opacity: 1;
}

.status-completed {
  opacity: 0.7;
  text-decoration: line-through;
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  backdrop-filter: blur(5px);
}

.modal-content {
  background: white;
  padding: 2.5rem;
  border-radius: 15px;
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
  animation: modalSlideIn 0.3s ease-out;
}

@keyframes modalSlideIn {
  from {
    transform: translateY(-30px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.modal-header h3 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.4rem;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 2rem;
  color: #666;
  cursor: pointer;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s;
}

.close-btn:hover {
  background-color: #f5f5f5;
  color: #333;
}

.task-details {
  margin: 1.5rem 0;
}

.detail-item {
  display: flex;
  align-items: flex-start;
  margin-bottom: 1.2rem;
  padding-bottom: 1.2rem;
  border-bottom: 1px solid #f0f0f0;
}

.detail-item:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.detail-label {
  flex: 0 0 80px;
  color: #666;
  font-weight: 500;
  font-size: 0.95rem;
}

.detail-value {
  flex: 1;
  color: #2c3e50;
  font-size: 1rem;
  line-height: 1.5;
}

.status-badge {
  display: inline-block;
  padding: 0.4rem 1rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-pending {
  color: #856404;
  background-color: #fff3cd;
}

.status-in-progress {
  color: #004085;
  background-color: #cce5ff;
}

.status-completed {
  color: #155724;
  background-color: #d4edda;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid #eee;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.8rem 1.5rem;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  font-size: 0.95rem;
  font-weight: 500;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  min-width: 120px;
  justify-content: center;
}

.start-btn {
  background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
  color: white;
}

.start-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0, 123, 255, 0.3);
}

.complete-btn {
  background: linear-gradient(135deg, #28a745 0%, #1e7e34 100%);
  color: white;
}

.complete-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(40, 167, 69, 0.3);
}

.close-action-btn {
  background: #6c757d;
  color: white;
}

.close-action-btn:hover {
  background: #5a6268;
  transform: translateY(-2px);
}

/* 滚动条样式 */
.calendar-body::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.calendar-body::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.calendar-body::-webkit-scrollbar-thumb {
  background: #c1c9d2;
  border-radius: 4px;
}

.calendar-body::-webkit-scrollbar-thumb:hover {
  background: #a0aaba;
}

/* 响应式 */
@media (max-width: 1200px) {
  .board-header {
    flex-wrap: wrap;
    gap: 10px;
  }
  
  .header-right {
    flex-wrap: wrap;
  }
}

@media (max-width: 768px) {
  .schedule-board {
    padding: 10px;
  }
  
  .calendar-wrapper {
    overflow-x: auto;
  }
  
  .calendar-header,
  .time-row {
    min-width: 900px;
  }
  
  .modal-actions {
    flex-direction: column;
  }
  
  .action-btn {
    width: 100%;
  }
}
</style>