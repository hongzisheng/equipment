<template>
  <div class="info-panel-container">
    <el-card class="panel-card" shadow="hover">
      <div class="panel-header">
        <div class="panel-title">
          <img src="/src/assets/iconfont/任务管理.png" alt="信息面板" class="panel-icon mr6" />
          信息面板
        </div>
      </div>
      <div class="panel-body">
        <!-- 时间段选择 -->
        <div class="time-period-selector">
          <el-form :inline="true" :model="searchForm" class="time-period-form">
            <el-form-item label="从第">
              <el-input-number v-model="searchForm.startDay" :min="1" :max="projectTotalDays" size="small" />
            </el-form-item>
            <el-form-item label="天的">
              <el-time-select
                v-model="searchForm.startTime"
                :picker-options="timeOptions"
                placeholder="选择时间"
                size="small"
              />
            </el-form-item>
            <el-form-item label="到第">
              <el-input-number v-model="searchForm.endDay" :min="1" :max="projectTotalDays" size="small" />
            </el-form-item>
            <el-form-item label="天的">
              <el-time-select
                v-model="searchForm.endTime"
                :picker-options="timeOptions"
                placeholder="选择时间"
                size="small"
              />
            </el-form-item>
          </el-form>
        </div>

        <!-- 主内容区：左侧工作人员状态（拉满高度） + 右侧物料看板 + 下方维修器具（在工作人员左侧） -->
        <div class="main-layout">
          <!-- 左侧：工作人员状态/班组状态（高度拉满） -->
          <el-card class="worker-status-card" shadow="never">
            <template #header>
              <div class="worker-header">
                <div class="worker-header-left">
                  <span>{{ staffStatusViewVisible ? '工作人员状态' : '班组状态' }}</span>
                  <div class="status-view-switch" role="tablist" aria-label="状态视图切换">
                    <button
                      type="button"
                      class="switch-btn"
                      :class="{ active: staffStatusViewVisible }"
                      @click="switchStaffView(true)"
                    >
                      工作人员
                    </button>
                    <button
                      type="button"
                      class="switch-btn"
                      :class="{ active: !staffStatusViewVisible }"
                      @click="switchStaffView(false)"
                    >
                      班组
                    </button>
                  </div>
                </div>
                <div class="worker-filter" v-if="staffStatusViewVisible">
                  <el-input
                    v-model="workerFilter"
                    placeholder="搜索工人"
                    clearable
                    size="small"
                    style="width: 200px; margin-right: 10px;"
                  >
                    <template #prefix>
                      <el-icon><Search /></el-icon>
                    </template>
                  </el-input>
                  <el-select
                    v-model="statusFilter"
                    placeholder="状态筛选"
                    clearable
                    size="small"
                    style="width: 120px;"
                  >
                    <el-option label="全部" value="" />
                    <el-option label="工作中" value="工作中" />
                    <el-option label="空闲中" value="空闲" />
                    <el-option label="已完成" value="已完成" />
                  </el-select>
                </div>
                <div class="worker-filter" v-else>
                  <el-select
                    v-model="selectedTeamEquipmentId"
                    placeholder="按设备筛选"
                    clearable
                    size="small"
                    style="width: 170px; margin-right: 10px;"
                  >
                    <el-option
                      v-for="option in teamEquipmentOptions"
                      :key="`eq-${option.value}`"
                      :label="option.label"
                      :value="option.value"
                    />
                  </el-select>
                  <el-select
                    v-model="selectedTeamProcessId"
                    placeholder="按工序筛选"
                    clearable
                    size="small"
                    style="width: 190px;"
                  >
                    <el-option
                      v-for="option in teamProcessOptions"
                      :key="`pr-${option.value}`"
                      :label="option.label"
                      :value="option.value"
                    />
                  </el-select>
                </div>
              </div>
            </template>

            <div class="status-view-body">
              <transition name="fade-slide" mode="out-in">
                <el-table
                  v-if="staffStatusViewVisible"
                  key="staff-view"
                  :data="filteredWorkersInPeriod"
                  style="width: 100%; height: 100%;"
                >
                  <el-table-column label="工人信息" min-width="250">
                    <template #default="{ row }">
                      <!-- 可点击的工人信息卡片 -->
                      <div class="worker-basic-info clickable-card" @click="showWorkerCalendar(row)">
                        <div><strong>ID:</strong> {{ row.id }}</div>
                        <div><strong>姓名:</strong> {{ row.name }}</div>
                        <div><strong>工种:</strong> {{ row.role }}</div>
                        <div>
                          <strong>状态:</strong>
                          <el-tag :type="getWorkerStatusType(row.status)" size="small">
                            {{ getWorkerStatusText(row.status) }}
                          </el-tag>
                        </div>
                        <div class="view-calendar-hint">
                          <el-icon><Calendar /></el-icon>
                          <span>点击查看任务日历</span>
                        </div>
                      </div>
                    </template>
                  </el-table-column>
                  <el-table-column label="时间段内任务" min-width="300">
                    <template #default="{ row }">
                      <div v-if="row.tasks && row.tasks.length > 0">
                        <el-collapse v-model="activeNames" class="custom-collapse">
                          <el-collapse-item :title="'任务列表 (' + row.tasks.length + '个任务)'" :name="row.id">
                            <div class="task-list-container">
                              <div v-for="task in row.tasks" :key="task.task_name" class="task-item-blue">
                                <div class="task-header">
                                  <div class="task-name">{{ task.task_name }}</div>
                                  <el-tag :type="getTaskStatusType(task.status)" size="small" class="task-status-tag">{{ task.status }}</el-tag>
                                </div>
                                <div class="task-details">
                                  <div class="task-equipment">
                                    <i class="el-icon-s-tools"></i>
                                    <span>设备: {{ task.equipment }}</span>
                                  </div>
                                  <div class="task-time">
                                    <i class="el-icon-time"></i>
                                    <span>第{{ extractDayFromFormattedTime(task.start_time) }}天 {{ formatTimeOnly(convertToTimestamp(extractDayFromFormattedTime(task.start_time), getTimeFromFormattedTime(task.start_time))) }} - 第{{ extractDayFromFormattedTime(task.end_time) }}天 {{ formatTimeOnly(convertToTimestamp(extractDayFromFormattedTime(task.end_time), getTimeFromFormattedTime(task.end_time))) }}</span>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </el-collapse-item>
                        </el-collapse>
                      </div>
                      <div v-else class="no-tasks">
                        无任务安排
                      </div>
                    </template>
                  </el-table-column>
                </el-table>

                <div v-else key="team-view" class="team-view-panel">
                  <div v-if="filteredWorkerOrdersWithProgress.length > 0" class="team-order-list">
                    <div class="team-overview-row">
                      <div class="team-overview-item">
                        <span class="team-overview-label">工单总数</span>
                        <strong class="team-overview-value">{{ teamOverview.total }}</strong>
                      </div>
                      <div class="team-overview-item team-overview-progress">
                        <span class="team-overview-label">总体进度</span>
                        <el-progress
                          :percentage="teamOverview.progressPercent"
                          :stroke-width="10"
                          :show-text="false"
                          status="success"
                        />
                        <strong class="team-overview-value">{{ teamOverview.progressPercent }}%</strong>
                      </div>
                      <div class="team-overview-item team-overview-status">
                        <span class="team-overview-label">状态分布</span>
                        <div class="team-overview-status-tags">
                          <el-tag
                            v-for="item in teamOverview.statusCounts"
                            :key="item.status"
                            size="small"
                            effect="light"
                            class="team-overview-status-tag"
                            :style="item.tagStyle"
                          >
                            {{ item.label }}: {{ item.count }}
                          </el-tag>
                        </div>
                      </div>
                    </div>
                    <div
                      v-for="(row, index) in filteredWorkerOrdersWithProgress"
                      :key="row.work_order_id || row.order_number || index"
                      class="team-order-item"
                    >
                      <div class="team-order-title">
                        <span class="team-order-name">{{ row.process_name || '未命名工单' }}</span>
                        <el-tag size="small" effect="light" class="team-order-status-tag" :style="row._progress.tagStyle">
                          {{ getStatusLabel(row.status || row.work_order_status) }}
                        </el-tag>
                      </div>
                      <div class="team-order-progress-wrap" :class="{ cancelled: row._progress.isCancelled }">
                        <div
                          class="team-order-progress-line"
                          role="progressbar"
                          :aria-valuemin="0"
                          :aria-valuemax="FLOW_PROGRESS_STEPS.length"
                          :aria-valuenow="row._progress.completedSteps"
                        >
                          <span
                            v-for="segment in row._progress.segments"
                            :key="segment.key"
                            class="progress-segment"
                            :class="segment.state"
                            :style="{ backgroundColor: segment.color }"
                          />
                        </div>
                        <span class="team-order-progress-text">{{ row._progress.progressText }}</span>
                      </div>
                      <div class="team-order-meta">
                        <div class="worker-group-list" v-if="parseWorkersByRole(row.workers).length">
                          <div class="worker-group-item" v-for="group in parseWorkersByRole(row.workers)" :key="group.role">
                            <span class="worker-role">{{ group.role }}</span>
                            <div class="worker-chip-wrap">
                              <span class="worker-chip" v-for="name in group.names" :key="`${group.role}-${name}`">{{ name }}</span>
                            </div>
                          </div>
                        </div>
                        <span v-else class="worker-empty">班组: 未分配</span>
                        <span v-if="row.priority">优先级: {{ row.priority }}</span>
                      </div>
                    </div>
                  </div>
                  <el-empty v-else description="暂无班组状态数据" />
                </div>
              </transition>
            </div>
          </el-card>

          <!-- 右侧：物料看板 + 维修器具看板（在工作人员左侧，物料下方） -->
          <div class="right-content">
            <!-- 物料看板（饼图形式） -->
            <el-card class="material-board-card" shadow="never">
              <template #header>
                <div class="material-header">
                  <span>物料库存使用看板</span>
                  <div class="material-header-right">
                    <el-select
                      v-model="searchForm.selectedTask"
                      placeholder="全部任务"
                      clearable
                      size="small"
                      style="width: 140px; margin-right: 10px;"
                    >
                      <el-option label="全部任务" value="" />
                      <el-option label="空冷器1检修" value="空冷器1检修" />
                      <el-option label="轴流式通风机1检修" value="轴流式通风机1检修" />
                      <el-option label="离心泵1检修" value="离心泵1检修" />
                    </el-select>
                    <el-tag
                      :type="currentTaskStockStatus === 'warning' ? 'danger' : 'success'"
                      size="small"
                    >
                      {{ currentTaskStockStatus === 'warning' ? '库存预警' : '库存正常' }}
                    </el-tag>
                  </div>
                </div>
              </template>

              <div class="material-content">
                <div class="chart-group-wrapper">
                  <div class="chart-group">
                    <div class="chart-item" style="width: 100%;">
                      <div class="chart-container">
                        <div v-for="(material, index) in allMaterials" :key="index" class="single-chart">
                          <div class="material-label">{{ material.name }}</div>
                          <div class="chart-wrapper">
                            <el-progress
                              type="circle"
                              :percentage="Math.round((material.used / material.stock) * 100)"
                              :color="getPieChartColor(material)"
                              :width="80"
                              :stroke-width="8"
                            >
                              <template #default="{ percentage }">
                                <span class="percentage-text">{{ percentage }}%</span>
                              </template>
                            </el-progress>
                          </div>
                          <div class="stock-info">
                            <span>库存: {{ material.stock }}{{ material.unit || '' }}</span>
                            <span>已用: {{ formatNumber(material.used) }}{{ material.unit || '' }}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </el-card>

            <!-- 维修器具看板（在工作人员左侧，物料看板下方） -->
            <el-card class="repair-tools-card" shadow="never">
              <template #header>
                <div class="tools-header">
                  <span>维修器具使用状态看板</span>
                  <el-select
                    v-model="toolsFilter"
                    placeholder="按类型筛选"
                    clearable
                    size="small"
                    style="width: 140px;"
                  >
                    <el-option label="全部类型" value="" />
                    <el-option label="起重设备" value="起重设备" />
                    <el-option label="运输设备" value="运输设备" />
                    <el-option label="焊接设备" value="焊接设备" />
                    <el-option label="通风设备" value="通风设备" />
                    <el-option label="加热设备" value="加热设备" />
                  </el-select>
                </div>
              </template>

              <div class="tools-content-wrapper">
                <div class="tools-content">
                  <el-table :data="filteredToolsInPeriod" style="width: 100%">
                    <el-table-column prop="name" label="器具名称" width="200" />
                    <el-table-column prop="type" label="器具类型" width="150" />
                    <el-table-column label="使用状态" width="150">
                      <template #default="{ row }">
                        <el-tag :type="row.isAvailable ? 'success' : 'danger'" size="small">
                          {{ row.isAvailable ? '可用' : '占用' }}
                        </el-tag>
                      </template>
                    </el-table-column>
                    <el-table-column prop="usedBy" label="使用任务" min-width="200">
                      <template #default="{ row }">
                        {{ row.isAvailable ? '无' : row.usedBy }}
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
              </div>
            </el-card>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 工人任务日历弹窗 -->
    <el-dialog
      v-model="calendarDialogVisible"
      :title="`${selectedWorker.name} 的任务课表`"
      width="90%"
      height="80%"
      :fullscreen="false"
    >
      <div class="schedule-table-container">
        <!-- 添加分页控件 -->
        <div class="pagination-controls" style="margin-bottom: 16px; display: flex; justify-content: center; align-items: center;">
          <el-button @click="prevWeekCalendar" :disabled="currentWeekCalendar <= 1">上一周</el-button>
          <span style="margin: 0 16px;">第 {{ currentWeekCalendar }} 周 / 共 {{ totalWeeksCalendar }} 周</span>
          <el-button @click="nextWeekCalendar" :disabled="currentWeekCalendar >= totalWeeksCalendar">下一周</el-button>
          <div style="margin-left: 20px;">
            <el-select
              v-model="selectedCalendarEquipment"
              placeholder="选择设备"
              clearable
              style="width: 200px; margin-right: 10px;"
              @change="currentWeekCalendar = 1"
            >
              <el-option
                v-for="option in calendarEquipmentOptions"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
            <el-button
              v-for="week in totalWeeksCalendar"
              :key="week"
              @click="goToWeekCalendar(week)"
              :type="week === currentWeekCalendar ? 'primary' : 'default'"
              style="margin: 0 4px;"
              size="small"
            >
              第{{ week }}周
            </el-button>
          </div>
        </div>

        <div class="schedule-table-wrapper">
          <!-- 表头：天数 -->
          <div class="time-column-header">时间</div>
          <div
            v-for="day in 7"
            :key="day"
            class="day-column-header"
          >
            第{{ day }}天
          </div>

          <!-- 左侧时间列 -->
          <div class="time-column">
            <div
              v-for="(time, index) in timeSlotsCalendar"
              :key="index"
              class="time-slot"
            >
              {{ time }}
            </div>
          </div>

          <!-- 每天的任务内容 -->
          <div
            v-for="day in 7"
            :key="day"
            class="day-column"
          >
            <!-- 时间槽背景 -->
            <div
              v-for="(time, index) in timeSlotsCalendar"
              :key="index"
              class="time-slot-bg"
            ></div>

            <!-- 任务项 -->
            <div
              v-for="task in weeklyCalendarData[day]"
              :key="task.processId"
              class="task-item"
              :style="getCalendarTaskPositionStyle(task)"
              :title="`${task.task} (${task.startTimeFormatted} - ${getDisplayEndTimeCalendar(task.endTimeFormatted)})`"
            >
              <div class="task-content">
                <div class="task-name">{{ task.task }}</div>
                <div class="task-device">{{ task.equipment || task.device }}</div>
                <div class="task-time">{{ task.startTimeFormatted.split(' ')[1] }}-{{ getDisplayEndTimeCalendar(task.endTimeFormatted).split(' ')[1] }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="calendarDialogVisible = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted, onUnmounted, watch } from 'vue'
import { Search, Calendar, Refresh, Setting } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { getStatusLabel, getStatusStyle } from '@/utils/statusUtil.ts'
// 搜索条件（整合时间段+任务选择）
const searchForm = reactive({
  startDay: 1,
  startTime: '08:00',
  endDay: 1,
  endTime: '20:00',
  selectedTask: '' // 选中的任务，空为全部
})
const activeNames = ref([])
const scheduleData = ref([])
const scheduleDataLoaded = ref(false)
const projectTotalDays = ref(6) // 默认项目总天数

// 日历弹窗相关
const calendarDialogVisible = ref(false)
const selectedWorker = ref({})
const calendarLoading = ref(false)
const currentDay = ref(1) // 当前天数，可以根据需要调整

// 预设颜色列表（用于分配不同设备的颜色）
const colorPalette = [
  '#67c23a', // 绿色
  '#409eff', // 蓝色
  '#e6a23c', // 橙色
  '#f56c6c', // 红色
  '#9b8bba', // 紫色
  '#5daf34', // 深绿
  '#337ecc', // 深蓝
  '#b88230', // 深橙
  '#c45656', // 深红
  '#7a6ba0', // 深紫
  '#8dd3c7', // 青绿
  '#ffffb3', // 浅黄
  '#bebada', // 淡紫
  '#fb8072', // 粉红
  '#80b1d3', // 浅蓝
  '#fdb462', // 浅橙
  '#b3de69', // 黄绿
  '#fccde5', // 淡粉
  '#d9d9d9', // 灰色
  '#bc80bd', // 紫红
]

// 时间选择器选项（仅8:00-20:00，30分钟间隔）
const timeOptions = {
  start: '08:00',
  step: '00:30',
  end: '20:00'
}
const staffStatusViewVisible = ref(true);

const switchStaffView = (showStaffView) => {
  staffStatusViewVisible.value = showStaffView
}

const parseWorkersByRole = (workers) => {
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

// 工人筛选条件
const workerFilter = ref('')
const statusFilter = ref('')
const selectedTeamEquipmentId = ref('')
const selectedTeamProcessId = ref('')
// 维修器具筛选条件
const toolsFilter = ref('')

// 时间槽定义（8:00-20:00，每30分钟一格，排除20:30）
const timeSlots = computed(() => {
  const slots = []
  for (let hour = 8; hour <= 20; hour++) {
    for (let minute of [0, 30]) {
      // 跳过20:30，因为结束时间是20:00
      if (hour === 20 && minute === 30) continue;

      const timeValue = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`
      let label = ''
      if (minute === 0) {
        label = `${hour}:00`
      } else {
        label = `${hour}:${minute}`
      }
      slots.push({ value: timeValue, label })
    }
  }
  return slots
})

// 工人基础数据
const workerBaseData = [
  { name: '张三', role: '钳工' },
  { name: '李四', role: '焊工' },
  { name: '王五', role: '起重工' },
  { name: '赵六', role: '电工' },
  { name: '钱七', role: '管工' },
  { name: '孙八', role: '仪表工' },
  { name: '周九', role: '车工' },
  { name: '吴十', role: '铣工' },
  { name: '郑一', role: '钻工' },
  { name: '王二', role: '刨工' }
]

// 任务列表（只包括指定的三个任务）
const taskList = [
  '空冷器1检修',
  '轴流式通风机1检修',
  '离心泵1检修'
]

// 存储维修器具数据
const repairToolsData = ref([]) // 用于存储从后端获取的维修器具状态数据
const materialInventoryData = ref([]) // 用于存储从后端获取的物料库存数据

// 工人状态数据
const workerStatusData = ref([])
const workerOrdersData = ref([])

const CANCELLED_STATUS = 'cancelled'

// 视觉进度条拆为 6 段；每段可覆盖 1~2 个业务状态。
const FLOW_PROGRESS_STEPS = [
  { key: 'released', statuses: ['released'], color: '#94a3b8' },
  { key: 'start', statuses: ['apply_for_start', 'eng_approved'], color: '#3b82f6' },
  { key: 'confirm', statuses: ['construction_confirmed', 'team_received'], color: '#06b6d4' },
  { key: 'signed', statuses: ['construction_signed'], color: '#8b5cf6' },
  { key: 'process', statuses: ['process_closed'], color: '#10b981' },
  { key: 'equipment', statuses: ['equipment_closed'], color: '#059669' }
]

const normalizeOrderStatus = (status) => (typeof status === 'string' ? status : '')

const getProgressStepIndex = (status) => {
  const normalizedStatus = normalizeOrderStatus(status)
  if (!normalizedStatus || normalizedStatus === CANCELLED_STATUS) return -1
  return FLOW_PROGRESS_STEPS.findIndex(step => step.statuses.includes(normalizedStatus))
}

const buildOrderProgressModel = (status) => {
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

const workerOrdersWithProgress = computed(() => {
  return workerOrdersData.value.map(row => {
    const currentStatus = row.status || row.work_order_status
    return {
      ...row,
      _progress: buildOrderProgressModel(currentStatus)
    }
  })
})

const teamEquipmentOptions = computed(() => {
  const map = new Map()
  workerOrdersData.value.forEach(row => {
    if (row.equipment_id == null || !row.equipment_name) return
    const key = String(row.equipment_id)
    if (!map.has(key)) {
      map.set(key, { value: key, label: row.equipment_name })
    }
  })
  return Array.from(map.values())
})

const teamProcessOptions = computed(() => {
  const map = new Map()
  workerOrdersData.value.forEach(row => {
    if (selectedTeamEquipmentId.value && String(row.equipment_id) !== selectedTeamEquipmentId.value) return
    if (row.process_id == null || !row.process_name) return
    const key = String(row.process_id)
    if (!map.has(key)) {
      map.set(key, { value: key, label: row.process_name })
    }
  })
  return Array.from(map.values())
})

const filteredWorkerOrdersWithProgress = computed(() => {
  return workerOrdersWithProgress.value.filter(row => {
    const matchEquipment = !selectedTeamEquipmentId.value || String(row.equipment_id) === selectedTeamEquipmentId.value
    const matchProcess = !selectedTeamProcessId.value || String(row.process_id) === selectedTeamProcessId.value
    return matchEquipment && matchProcess
  })
})

const teamOverview = computed(() => {
  const rows = filteredWorkerOrdersWithProgress.value
  const total = rows.length
  if (!total) {
    return {
      total: 0,
      progressPercent: 0,
      statusCounts: []
    }
  }

  const totalSteps = FLOW_PROGRESS_STEPS.length
  const completedStepSum = rows.reduce((sum, row) => sum + (row._progress?.completedSteps || 0), 0)
  const progressPercent = Math.round((completedStepSum / (total * totalSteps)) * 100)

  const statusMap = new Map()
  rows.forEach(row => {
    const status = normalizeOrderStatus(row.status || row.work_order_status)
    const previous = statusMap.get(status)
    statusMap.set(status, {
      status,
      count: previous ? previous.count + 1 : 1
    })
  })

  const statusCounts = Array.from(statusMap.values())
    .map(item => {
      const label = getStatusLabel(item.status) || item.status || '未知'
      const style = getStatusStyle(item.status)
      return {
        ...item,
        label,
        tagStyle: {
          backgroundColor: style.tagBg,
          color: style.tagText,
          borderColor: style.tagBorder
        }
      }
    })
    .sort((a, b) => b.count - a.count)

  return {
    total,
    progressPercent,
    statusCounts
  }
})

// 计算设备列表（从工人的任务中提取）
const equipmentList = computed(() => {
  if (!selectedWorker.value.tasks || selectedWorker.value.tasks.length === 0) {
    return []
  }

  const equipmentSet = new Set()
  selectedWorker.value.tasks.forEach(task => {
    if (task.equipment) {
      equipmentSet.add(task.equipment)
    }
  })

  return Array.from(equipmentSet)
})

// 设备到颜色的映射（动态生成）
const equipmentColorMap = computed(() => {
  const map = {}
  equipmentList.value.forEach((equipment, index) => {
    // 循环使用颜色列表
    const colorIndex = index % colorPalette.length
    map[equipment] = colorPalette[colorIndex]
  })
  return map
})

// 页面加载时自动获取调度计划数据并启动定时更新
onMounted(() => {
  // 设置默认时间周期
  setDefaultTimePeriod()

  refreshData()
})

// 监听时间选择变化，重新获取数据
watch([() => searchForm.startDay, () => searchForm.startTime, () => searchForm.endDay, () => searchForm.endTime], () => {
  refreshData()
})

// 页面卸载时清除定时器
onUnmounted(() => {
  // 定时器相关代码已删除
})

// 刷新数据
const refreshData = () => {
  // 获取工人状态数据
  fetchWorkerStatus()

  // 获取物料库存数据
  fetchMaterialInventory()

  // 获取维修器具状态数据
  fetchMaintenanceToolStatus()
  // 获取工单信息（为了班组）
  fetchOrders()
}

// 获取工人状态数据
const fetchWorkerStatus = async () => {
  try {
    const response = await request({
      url: 'http://localhost:5000/api/worker-status',
      method: 'post',
      data: {
        start_time: `第${searchForm.startDay}天 ${searchForm.startTime}`,
        end_time: `第${searchForm.endDay}天 ${searchForm.endTime}`
      }
    })
    if (response.success) {
      workerStatusData.value = response.worker_status
    }
  } catch (error) {
    console.error('获取工人状态失败:', error)
  }
}

// 获取物料库存数据
const fetchMaterialInventory = async () => {
  try {
    const response = await request({
      url: 'http://localhost:5000/api/material-inventory',
      method: 'post',
      data: {
        end_time: `第${searchForm.endDay}天 ${searchForm.endTime}`
      }
    })
    if (response.success) {
      materialInventoryData.value = response.material_inventory
    }
  } catch (error) {
    console.error('获取物料库存数据失败:', error)
  }
}

// 获取维修器具使用状态数据
const fetchMaintenanceToolStatus = async () => {
  try {
    const response = await request({
      url: 'http://localhost:5000/api/maintenance-tool-status',
      method: 'post',
      data: {
        start_time: `第${searchForm.startDay}天 ${searchForm.startTime}`,
        end_time: `第${searchForm.endDay}天 ${searchForm.endTime}`
      }
    })
    if (response.success) {
      repairToolsData.value = response.maintenance_tool_status
    }
  } catch (error) {
    console.error('获取维修器具状态失败:', error)
  }
}

// 获取工单信息
const fetchOrders = async () => {
  try {
    const response = await request({
      url: 'http://localhost:5000/api/work-order-tasks',
      method: 'get',
    })
    if (response.success) {
      // 这里可以处理工单数据，例如存储到某个ref中
      workerOrdersData.value = response.data
    }
  } catch (error) {
    console.error('获取工单信息失败:', error)
  }
}

// 显示工人任务日历
const showWorkerCalendar = (worker) => {
  selectedWorker.value = { ...worker }
  calendarDialogVisible.value = true
}

// 刷新日历数据
const refreshWorkerCalendar = async () => {
  if (!selectedWorker.value.id) return

  calendarLoading.value = true
  try {
    // 模拟延迟
    await new Promise(resolve => setTimeout(resolve, 500))
  } catch (error) {
    console.error('获取日历数据失败:', error)
  } finally {
    calendarLoading.value = false
  }
}

// 获取指定时间点的任务
const getTaskAtTime = (day, time) => {
  if (!selectedWorker.value.tasks) return null

  const targetTimestamp = convertToTimestamp(day, time)

  return selectedWorker.value.tasks.find(task => {
    const taskStart = convertToTimestamp(
      extractDayFromFormattedTime(task.start_time),
      getTimeFromFormattedTime(task.start_time)
    )
    const taskEnd = convertToTimestamp(
      extractDayFromFormattedTime(task.end_time),
      getTimeFromFormattedTime(task.end_time)
    )

    return targetTimestamp >= taskStart && targetTimestamp <= taskEnd
  })
}

// 获取时间段样式类
const getTimeSlotClass = (day, time) => {
  const task = getTaskAtTime(day, time)
  if (task) {
    return 'has-task'
  }
  return 'no-task'
}

// 根据设备获取颜色
const getEquipmentColor = (equipment, opacity = 1) => {
  if (!equipment || !equipmentColorMap.value[equipment]) {
    // 如果没有设备或设备不在映射表中，返回默认颜色
    return `rgba(144, 147, 153, ${opacity})` // 灰色
  }

  const hexColor = equipmentColorMap.value[equipment]
  if (opacity === 1) return hexColor

  // 将hex颜色转换为rgba
  const r = parseInt(hexColor.slice(1, 3), 16)
  const g = parseInt(hexColor.slice(3, 5), 16)
  const b = parseInt(hexColor.slice(5, 7), 16)
  return `rgba(${r}, ${g}, ${b}, ${opacity})`
}

// 获取任务块样式
const getTaskBlockStyle = (task) => {
  if (!task) return {}

  const backgroundColor = getEquipmentColor(task.equipment, 0.8)
  const borderColor = getEquipmentColor(task.equipment)

  return {
    backgroundColor,
    borderColor,
    borderWidth: '2px',
    borderStyle: 'solid'
  }
}

// 获取任务提示信息
const getTaskTooltip = (task) => {
  if (!task) return ''

  return `${task.task_name}\n设备: ${task.equipment}\n状态: ${task.status}\n时间: 第${extractDayFromFormattedTime(task.start_time)}天 ${getTimeFromFormattedTime(task.start_time)} - 第${extractDayFromFormattedTime(task.end_time)}天 ${getTimeFromFormattedTime(task.end_time)}`
}

// 获取设备任务数量
const getEquipmentTaskCount = (equipment) => {
  if (!selectedWorker.value.tasks) return 0

  return selectedWorker.value.tasks.filter(task => task.equipment === equipment).length
}

// 提取天数
const extractDayFromFormattedTime = (formattedTime) => {
  if (!formattedTime) return 1
  const dayMatch = formattedTime.match(/第(\d+)天/)
  return dayMatch && dayMatch[1] ? parseInt(dayMatch[1], 10) : 1
}

// 从格式化的时间字符串中提取时间(HH:mm)
const getTimeFromFormattedTime = (formattedTime) => {
  if (!formattedTime) return '08:00'
  const timeMatch = formattedTime.match(/\d{2}:\d{2}/)
  return timeMatch ? timeMatch[0] : '08:00'
}

// 计算项目总天数
const calculateProjectTotalDays = () => {
  // 使用固定值10天
  projectTotalDays.value = 10
  searchForm.endDay = projectTotalDays.value
}

// 添加当前周数状态 - 用于日历视图
const currentWeekCalendar = ref(1)

// 添加设备筛选状态 - 用于日历视图
const selectedCalendarEquipment = ref('')

// 时间槽计算，只显示当前周的时间 - 用于日历视图
const timeSlotsCalendar = computed(() => {
  const slots = []
  for (let hour = 8; hour <= 19; hour++) {
    slots.push(`${hour.toString().padStart(2, '0')}:00`)
    slots.push(`${hour.toString().padStart(2, '0')}:30`)
  }
  // 添加最后一小时的结束时间20:00
  slots.push(`20:00`)
  return slots
})

// 计算日历数据，只返回当前周的数据
const weeklyCalendarData = computed(() => {
  if (!selectedWorker.value.tasks) return {}

  // 按天数分组任务，并只返回当前周的数据
  const tasksByDay = {}
  const startDay = (currentWeekCalendar.value - 1) * 7 + 1
  const endDay = currentWeekCalendar.value * 7

  selectedWorker.value.tasks.forEach(task => {
    // 添加设备筛选逻辑
    if (selectedCalendarEquipment.value && task.equipment !== selectedCalendarEquipment.value) {
      return // 如果选择了特定设备且当前任务不是该设备，则跳过
    }

    const dayMatch = task.start_time.match(/第(\d+)天/)
    if (dayMatch) {
      const day = parseInt(dayMatch[1])
      // 只处理当前周的天数
      if (day >= startDay && day <= endDay) {
        const weekDay = day - startDay + 1
        if (!tasksByDay[weekDay]) {
          tasksByDay[weekDay] = []
        }
        // 更新任务中的天数信息以适应当前周显示
        const updatedTask = {
          task: task.task_name,
          equipment: task.equipment,
          startTimeFormatted: task.start_time,
          endTimeFormatted: task.end_time,
          processId: task.task_id
        }
        tasksByDay[weekDay].push(updatedTask)
      }
    }
  })

  return tasksByDay
})

// 计算日历总周数
const totalWeeksCalendar = computed(() => {
  if (!selectedWorker.value.tasks) return 1

  const days = selectedWorker.value.tasks.map(task => {
    const dayMatch = task.start_time.match(/第(\d+)天/)
    return dayMatch ? parseInt(dayMatch[1]) : 1
  })
  const maxDay = days.length > 0 ? Math.max(...days) : 0
  return Math.ceil(maxDay / 7) || 1
})

// 获取日历设备选项
const calendarEquipmentOptions = computed(() => {
  if (!selectedWorker.value.tasks) return []

  // 提取唯一的设备名称
  const equipmentSet = new Set()
  selectedWorker.value.tasks.forEach(task => {
    if (task.equipment) {
      equipmentSet.add(task.equipment)
    }
  })

  // 转换为选项数组
  return Array.from(equipmentSet).map(equipment => ({
    label: equipment,
    value: equipment
  }))
})

// 上一周 - 日历视图
function prevWeekCalendar() {
  if (currentWeekCalendar.value > 1) {
    currentWeekCalendar.value--
  }
}

// 下一周 - 日历视图
function nextWeekCalendar() {
  if (currentWeekCalendar.value < totalWeeksCalendar.value) {
    currentWeekCalendar.value++
  }
}

// 跳转到指定周 - 日历视图
function goToWeekCalendar(week) {
  if (week >= 1 && week <= totalWeeksCalendar.value) {
    currentWeekCalendar.value = week
  }
}

// 获取显示用的结束时间 - 日历视图
function getDisplayEndTimeCalendar(endTimeFormatted) {
  // 检查结束时间是否为8:00
  const endMatch = endTimeFormatted.match(/第(\d+)天 08:00/)
  if (endMatch) {
    const day = parseInt(endMatch[1])
    if (day > 1) {
      // 将第n天8:00改为第(n-1)天20:00
      return `第${day - 1}天 20:00`
    }
  }
  return endTimeFormatted
}

// 根据任务时间计算时间槽索引
function getTimeSlotIndex(time) {
  const [hour, minute] = time.split(':').map(Number)
  // 8:00对应索引0，每30分钟加1
  return (hour - 8) * 2 + (minute >= 30 ? 1 : 0)
}

// 获取任务的样式 - 日历视图（修复高度对齐问题）
function getCalendarTaskPositionStyle(task) {
  if (!task) return {}

  let startTimeFormatted = task.startTimeFormatted
  let endTimeFormatted = task.endTimeFormatted

  // 处理特殊情况：如果结束时间是第n天的8:00，应该显示为第(n-1)天的20:00
  const endMatch = endTimeFormatted.match(/第(\d+)天 08:00/)
  if (endMatch) {
    const day = parseInt(endMatch[1])
    if (day > 1) {
      endTimeFormatted = `第${day - 1}天 20:00`
    }
  }

  const startTime = getTimeFromFormattedTime(startTimeFormatted)
  const endTime = getTimeFromFormattedTime(endTimeFormatted)

  // 计算时间槽索引
  const startIndex = getTimeSlotIndex(startTime)
  const endIndex = getTimeSlotIndex(endTime)

  // 计算位置和高度 - 使用50px作为每个时间槽的高度
  const top = startIndex * 50+20
  const height = (endIndex - startIndex) * 50

  // 使用预定义颜色，基于设备名生成
  const equipment = task.equipment || task.device
  let backgroundColor = '#ccc' // 默认颜色

  if (equipment) {
    // 基于设备名生成哈希值，然后映射到颜色数组
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

// 设置默认时间段
const setDefaultTimePeriod = () => {
  searchForm.startDay = 1
  searchForm.startTime = '08:00'
  searchForm.endDay = projectTotalDays.value
  searchForm.endTime = '20:00'
}

// 时间戳转换
const convertToTimestamp = (day, time) => {
  const [hours, minutes] = time.split(':').map(Number)
  const baseDate = new Date(2023, 0, 1)
  baseDate.setDate(baseDate.getDate() + day - 1)
  baseDate.setHours(hours, minutes, 0, 0)
  return baseDate.getTime()
}

// 时间格式化
const formatTimeOnly = (timestamp) => {
  const date = new Date(timestamp)
  return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
}

// 筛选工人列表
const filteredWorkersInPeriod = computed(() => {
  // 使用从API获取的工人状态数据
  let workersArray = workerStatusData.value.map(worker => ({
    id: worker.worker_id,
    name: worker.worker_name,
    role: worker.worker_type,
    status: worker.status,
    tasks: worker.tasks
  }))

  // 应用筛选条件
  if (workerFilter.value) {
    workersArray = workersArray.filter(worker =>
      worker.name.includes(workerFilter.value)
    )
  }
  if (statusFilter.value) {
    workersArray = workersArray.filter(worker => worker.status === statusFilter.value)
  }
  return workersArray
})

// 工人状态类型
const getWorkerStatusType = (status) => {
  const statusMap = {
    '工作中': 'warning',
    '空闲中': 'success',
    '已完成': 'info'
  }
  return statusMap[status] || 'info'
}

// 工人状态文本
const getWorkerStatusText = (status) => {
  return status
}

// 任务状态类型
const getTaskStatusType = (status) => {
  const statusMap = {
    '进行中': 'warning',
    '已完成': 'success',
    '未开始': 'info'
  }
  return statusMap[status] || 'info'
}

// 判断当前时段
const getCurrentPeriod = computed(() => {
  const startHour = parseInt(searchForm.startTime.split(':')[0])
  if (startHour < 11) return 'period1'
  if (startHour < 14) return 'period2'
  if (startHour < 17) return 'period3'
  return 'period4'
})

// 判断当前项目阶段
const getCurrentProjectStage = computed(() => {
  const midDay = Math.floor((searchForm.startDay + searchForm.endDay) / 2)
  if (midDay <= 3) return 'early'
  if (midDay <= 6) return 'middle'
  return 'late'
})

// 获取当前时段物料库存数据（直接使用接口返回的数据）
const currentPeriodMaterialStock = computed(() => {
  return formattedMaterialInventory.value
})

// 获取饼图颜色
const getPieChartColor = (material) => {
  const usageRate = material.used / material.stock
  if (usageRate > 0.9) return '#ff4d4f'     // 红色 - 使用率超过90%
  if (usageRate > 0.5) return '#faad14'     // 黄色 - 使用率超过50%但不超过90%
  return '#52c41a'                          // 绿色 - 使用率不超过50%
}

// 格式化数字，保留三位小数
const formatNumber = (value) => {
  if (value === undefined || value === null) return '0.000'
  return parseFloat(value).toFixed(3)
}

// 当前任务库存整体状态
const currentTaskStockStatus = computed(() => {
  const stockData = currentPeriodMaterialStock.value
  for (const typeKey in stockData) {
    for (const material of stockData[typeKey]) {
      if (material.used / material.stock >= 0.8) {
        return 'warning'
      }
    }
  }
  return 'normal'
})

// 获取所有物料数据，不区分分类
const allMaterials = computed(() => {
  const materials = []
  const stockData = currentPeriodMaterialStock.value

  // 如果没有数据，返回空数组
  if (Object.keys(stockData).length === 0) {
    return []
  }

  // 遍历所有分类中的物料
  for (const typeKey in stockData) {
    materials.push(...stockData[typeKey])
  }

  return materials
})

// 将后端获取的物料数据转换为前端需要的格式
const formattedMaterialInventory = computed(() => {
  if (!materialInventoryData.value || materialInventoryData.value.length === 0) {
    return {}
  }

  // 按物料类别分组
  const groupedMaterials = {
    pipeline: [],     // 管道类
    connector: [],    // 连接件类
    equipment: []     // 设备配件类
  }

  // 根据物料名称判断类别
  const getMaterialCategory = (materialName) => {
    // 管道类物料关键词
    const pipelineKeywords = ['钢材', '不锈钢管', '管道']
    // 连接件类物料关键词
    const connectorKeywords = ['阀门', '法兰', '螺栓', '垫片']
    // 设备配件类物料关键词
    const equipmentKeywords = ['密封胶', '电缆', '仪表', '泵体']

    if (pipelineKeywords.some(keyword => materialName.includes(keyword))) {
      return 'pipeline'
    } else if (connectorKeywords.some(keyword => materialName.includes(keyword))) {
      return 'connector'
    } else if (equipmentKeywords.some(keyword => materialName.includes(keyword))) {
      return 'equipment'
    }
    // 默认归类为设备配件类
    return 'equipment'
  }

  // 处理物料数据
  materialInventoryData.value.forEach(material => {
    const category = getMaterialCategory(material.material_name)
    groupedMaterials[category].push({
      name: material.material_name,
      stock: material.initial_stock,
      used: material.initial_stock - material.current_stock,
      unit: material.unit
    })
  })

  return groupedMaterials
})

// 筛选当前时段的维修器具数据
const filteredToolsInPeriod = computed(() => {
  // 使用从API获取的维修器具状态数据
  let toolsArray = repairToolsData.value

  // 按类型筛选
  if (toolsFilter.value) {
    toolsArray = toolsArray.filter(tool => tool.tool_type === toolsFilter.value)
  }

  // 转换数据格式以适配表格
  return toolsArray.map(tool => ({
    id: tool.tool_id,
    name: tool.tool_name,
    type: tool.tool_type,
    isAvailable: tool.usage_status === '空闲',
    usedBy: tool.usage_tasks && tool.usage_tasks.length > 0
      ? tool.usage_tasks.map(task => task.task_name).join(', ')
      : '无'
  }))
})
</script>

<style scoped>
/* 移除 lang="scss" 尝试修复可能的解析错误 */
@import '@/scss/InfoPanel.scss';
</style>
