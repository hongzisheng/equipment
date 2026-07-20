<template>
  <div class="maintenance-plan-container">
    <el-card class="panel-card" shadow="hover">
      <div class="panel-header">
        <div class="panel-title">
          <el-icon class="panel-icon"><List /></el-icon>
          检修计划管理
        </div>
      </div>

      <div class="panel-body">
        <div class="filter-toolbar">
          <el-input
            v-model="filters.plan_name"
            placeholder="请输入计划名称"
            clearable
            size="small"
            class="search-input"
            @keyup.enter="handleSearch"
            @clear="handleSearch"
          />
          <el-select
            v-model="filters.plan_scale"
            placeholder="计划规模"
            clearable
            size="small"
            class="filter-select"
            @change="handleSearch"
          >
            <el-option label="全部" value="" />
            <el-option label="日常巡检" value="日常巡检" />
            <el-option label="计划检修" value="计划检修" />
            <el-option label="中型检修" value="中型检修" />
            <el-option label="大型检修" value="大型检修" />
          </el-select>
          <el-select
            v-model="filters.status"
            placeholder="当前进度"
            clearable
            size="small"
            class="filter-select"
            @change="handleSearch"
          >
            <el-option label="全部" value="" />
            <el-option label="待开始" value="待开始" />
            <el-option label="申请停车" value="申请停车" />
            <el-option label="检修中" value="检修中" />
            <el-option label="验收与质量检验" value="验收与质量检验" />
            <el-option label="已完成" value="已完成" />
          </el-select>
          <div class="date-range-group">
            <span class="date-label">计划开始时间</span>
            <el-date-picker
              v-model="filters.start_date_from"
              type="date"
              placeholder="开始日期"
              size="small"
              value-format="YYYY-MM-DD"
              class="date-picker"
              @change="handleSearch"
            />
            <span class="date-sep">至</span>
            <el-date-picker
              v-model="filters.start_date_to"
              type="date"
              placeholder="结束日期"
              size="small"
              value-format="YYYY-MM-DD"
              class="date-picker"
              @change="handleSearch"
            />
          </div>
          <div class="date-range-group">
            <span class="date-label">计划结束时间</span>
            <el-date-picker
              v-model="filters.end_date_from"
              type="date"
              placeholder="开始日期"
              size="small"
              value-format="YYYY-MM-DD"
              class="date-picker"
              @change="handleSearch"
            />
            <span class="date-sep">至</span>
            <el-date-picker
              v-model="filters.end_date_to"
              type="date"
              placeholder="结束日期"
              size="small"
              value-format="YYYY-MM-DD"
              class="date-picker"
              @change="handleSearch"
            />
          </div>
          <div class="filter-actions">
            <el-button size="small" @click="resetSearch">重置</el-button>
            <el-button type="primary" size="small" @click="handleSearch">查询</el-button>
          </div>
        </div>

        <el-table
          :data="plans"
          v-loading="loading"
          border
          stripe
          class="plan-table"
          style="width: 100%"
        >
          <el-table-column type="index" label="序号" width="55" align="center" />
          <el-table-column prop="plan_name" label="计划名称" min-width="150" align="center" show-overflow-tooltip />
          <el-table-column prop="plan_scale" label="规模" min-width="90" align="center" />
          <el-table-column prop="status" label="当前进度" min-width="120" align="center">
            <template #default="{ row }">
              <el-tag :type="getStatusTagType(row.status)" size="small" effect="light">
                {{ row.status || '--' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="planned_start_time" label="计划开始时间" min-width="120" align="center">
            <template #default="{ row }">{{ formatDate(row.planned_start_time) }}</template>
          </el-table-column>
          <el-table-column prop="planned_end_time" label="计划结束时间" min-width="120" align="center">
            <template #default="{ row }">{{ formatDate(row.planned_end_time) }}</template>
          </el-table-column>
          <el-table-column label="人工时（小时）" min-width="180" align="center">
            <template #default="{ row }">
              <div class="stats-row">
                <div class="stat-item">
                  <div class="stat-value">{{ row.planned_man_hours || 0 }}</div>
                  <div class="stat-label">计划</div>
                </div>
                <div class="stat-item">
                  <div class="stat-value">{{ row.actual_man_hours || 0 }}</div>
                  <div class="stat-label">实际</div>
                </div>
                <div class="stat-item">
                  <div class="stat-value rate">{{ getRate(row.actual_man_hours, row.planned_man_hours) }}</div>
                  <div class="stat-label">完成率</div>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="其他成本（元）" min-width="180" align="center">
            <template #default="{ row }">
              <div class="stats-row">
                <div class="stat-item">
                  <div class="stat-value">{{ formatCost(row.planned_cost) }}</div>
                  <div class="stat-label">计划</div>
                </div>
                <div class="stat-item">
                  <div class="stat-value">{{ formatCost(row.actual_cost) }}</div>
                  <div class="stat-label">实际</div>
                </div>
                <div class="stat-item">
                  <div class="stat-value rate">{{ getRate(row.actual_cost, row.planned_cost) }}</div>
                  <div class="stat-label">完成率</div>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="操作" min-width="220" align="center">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button size="small" type="primary" @click="goDetail(row)">查看详情</el-button>
                <el-button
                  v-if="row.schedule_plan_id"
                  size="small"
                  type="primary"
                  @click="goSchedule(row)"
                >查看调度计划</el-button>
                <el-button
                  v-else
                  size="small"
                  type="success"
                  @click="handleGenerateSchedule(row)"
                >生成调度方案</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>

        <div class="bottom-bar">
          <el-button type="primary" @click="goCreate">
            <el-icon><Plus /></el-icon> 新增检修计划
          </el-button>
          <div class="pagination-wrapper">
            <span class="total-text">共 {{ pagination.total }} 条</span>
            <el-pagination
              v-model:current-page="pagination.page"
              v-model:page-size="pagination.page_size"
              :page-sizes="[10, 20, 50]"
              :total="pagination.total"
              layout="sizes, prev, pager, next, jumper"
              background
              @size-change="fetchPlans"
              @current-change="fetchPlans"
            />
          </div>
        </div>
      </div>
    </el-card>

    <!-- 调度方案详情弹窗 - 直接在列表页展示 -->
    <el-dialog
      v-model="scheduleDialogVisible"
      title="调度方案详情"
      width="95%"
      top="3vh"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <div v-loading="scheduleLoading">
        <div v-if="scheduleData && scheduleData.schedule_tasks && scheduleData.schedule_tasks.length > 0">
          <!-- 方案基本信息 -->
          <div class="schedule-header">
            <div class="schedule-info-item">
              <span class="label">方案名称</span>
              <span class="value">{{ scheduleData.schedule_name }}</span>
            </div>
            <div class="schedule-info-item">
              <span class="label">算法</span>
              <span class="value">{{ scheduleData.algorithm || '--' }}</span>
            </div>
            <div class="schedule-info-item">
              <span class="label">创建时间</span>
              <span class="value">{{ scheduleData.created_at || '--' }}</span>
            </div>
            <div class="schedule-info-item">
              <span class="label">项目开始日期</span>
              <span class="value">{{ scheduleData.project_start_date || '--' }}</span>
            </div>
            <div class="schedule-info-item">
              <span class="label">总工期</span>
              <span class="value highlight">{{ scheduleData.total_days || 0 }} 天</span>
            </div>
            <div class="schedule-info-item">
              <span class="label">任务总数</span>
              <span class="value">{{ scheduleData.schedule_tasks.length }} 项</span>
            </div>
          </div>

          <!-- 甘特图区域 -->
          <div class="gantt-container">
            <!-- 左侧工序列表 -->
            <div class="gantt-left-panel">
              <div class="gantt-left-header">
                <span class="col-id">#</span>
                <span class="col-process">工序名称</span>
                <span class="col-duration">时长</span>
              </div>
              <div class="gantt-left-body">
                <div
                  v-for="(task, index) in sortedScheduleTasks"
                  :key="task.schedule_id"
                  class="gantt-row"
                >
                  <span class="col-id">{{ index + 1 }}</span>
                  <span class="col-process" :title="task.process_name">{{ task.process_name }}</span>
                  <span class="col-duration">{{ task.duration_days }}d</span>
                </div>
              </div>
            </div>

            <!-- 右侧时间轴 -->
            <div class="gantt-right-panel">
              <!-- 时间轴头部 -->
              <div class="gantt-header">
                <div
                  v-for="day in totalDaysArray"
                  :key="day"
                  class="gantt-header-cell"
                >
                  第{{ day }}天
                </div>
              </div>
              <!-- 时间轴主体 -->
              <div class="gantt-body">
                <div
                  v-for="task in sortedScheduleTasks"
                  :key="task.schedule_id"
                  class="gantt-row"
                >
                  <div class="gantt-row-content">
                    <div
                      class="gantt-bar"
                      :style="getBarStyle(task)"
                      @mouseenter="showTaskTooltip($event, task)"
                      @mouseleave="hideTaskTooltip"
                    >
                      <span class="bar-label">{{ task.process_name }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 任务详情列表 -->
          <div class="schedule-tasks-detail">
            <h4>任务详情</h4>
            <el-table :data="sortedScheduleTasks" border stripe size="small" style="width: 100%">
              <el-table-column prop="process_name" label="工序名称" min-width="140" />
              <el-table-column prop="equipment_name" label="设备名称" min-width="120" />
              <el-table-column prop="start_time_formatted" label="开始时间" min-width="140" />
              <el-table-column prop="end_time_formatted" label="结束时间" min-width="140" />
              <el-table-column prop="duration_days" label="持续天数" width="80" align="center" />
              <el-table-column label="分配工人" min-width="200" show-overflow-tooltip>
                <template #default="{ row }">{{ formatWorkers(row.workers) }}</template>
              </el-table-column>
            </el-table>
          </div>
        </div>
        <el-empty v-else description="暂无调度方案数据" />
      </div>
      <template #footer>
        <el-button @click="scheduleDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 任务悬停提示 -->
    <div
      v-if="taskTooltipVisible"
      class="task-tooltip"
      :style="{ left: tooltipPosition.x + 'px', top: tooltipPosition.y + 'px' }"
    >
      <div class="tooltip-title">{{ taskTooltipData.process_name }}</div>
      <div class="tooltip-row">
        <span class="tooltip-label">设备：</span>
        <span>{{ taskTooltipData.equipment_name }}</span>
      </div>
      <div class="tooltip-row">
        <span class="tooltip-label">开始：</span>
        <span>{{ taskTooltipData.start_time_formatted }}</span>
      </div>
      <div class="tooltip-row">
        <span class="tooltip-label">结束：</span>
        <span>{{ taskTooltipData.end_time_formatted }}</span>
      </div>
      <div class="tooltip-row">
        <span class="tooltip-label">工人：</span>
        <span>{{ formatWorkers(taskTooltipData.workers) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { List, Plus } from '@element-plus/icons-vue'
import { getMaintenancePlans, deleteMaintenancePlan, getPlanSchedulePlan } from '@/api/maintenancePlan'

defineOptions({ name: 'MaintenancePlanList' })

const router = useRouter()

const loading = ref(false)
const plans = ref([])
const scheduleDialogVisible = ref(false)
const scheduleLoading = ref(false)
const scheduleData = ref(null)
const taskTooltipVisible = ref(false)
const taskTooltipData = ref({})
const tooltipPosition = ref({ x: 0, y: 0 })

const filters = reactive({
  plan_name: '',
  plan_scale: '',
  status: '',
  start_date_from: '',
  start_date_to: '',
  end_date_from: '',
  end_date_to: '',
})

const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0,
})

const fetchPlans = async () => {
  loading.value = true
  try {
    const res = await getMaintenancePlans({
      page: pagination.page,
      page_size: pagination.page_size,
      plan_name: filters.plan_name,
      plan_scale: filters.plan_scale,
      status: filters.status,
    })
    plans.value = res.data || []
    pagination.total = res.total || 0
  } catch (error) {
    console.error('获取检修计划列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchPlans()
}

const resetSearch = () => {
  filters.plan_name = ''
  filters.plan_scale = ''
  filters.status = ''
  filters.start_date_from = ''
  filters.start_date_to = ''
  filters.end_date_from = ''
  filters.end_date_to = ''
  pagination.page = 1
  fetchPlans()
}

const goCreate = () => {
  router.push('/maintenance-plan/create')
}

const goDetail = (row) => {
  router.push(`/maintenance-plan/detail/${row.id}`)
}

const goSchedule = async (row) => {
  scheduleDialogVisible.value = true
  scheduleLoading.value = true
  try {
    const res = await getPlanSchedulePlan(row.id)
    scheduleData.value = res.data
  } catch (error) {
    console.error('获取调度方案失败:', error)
  } finally {
    scheduleLoading.value = false
  }
}

const sortedScheduleTasks = computed(() => {
  if (!scheduleData.value?.schedule_tasks) return []
  return [...scheduleData.value.schedule_tasks].sort((a, b) => {
    if (a.start_time !== b.start_time) return a.start_time - b.start_time
    return a.equipment_name.localeCompare(b.equipment_name)
  })
})

const totalDaysArray = computed(() => {
  const total = scheduleData.value?.total_days || 0
  return Array.from({ length: total }, (_, i) => i + 1)
})

const getBarStyle = (task) => {
  const totalDays = scheduleData.value?.total_days || 1
  const leftPercent = (task.start_time / totalDays) * 100
  const widthPercent = (task.duration_days / totalDays) * 100
  return {
    left: `${leftPercent}%`,
    width: `${widthPercent}%`,
  }
}

const showTaskTooltip = (event, task) => {
  taskTooltipData.value = task
  tooltipPosition.value = { x: event.clientX + 10, y: event.clientY + 10 }
  taskTooltipVisible.value = true
}

const hideTaskTooltip = () => {
  taskTooltipVisible.value = false
}

const formatWorkers = (workers) => {
  if (!workers) return '--'
  const parts = []
  if (typeof workers === 'object' && !Array.isArray(workers)) {
    for (const [role, names] of Object.entries(workers)) {
      if (Array.isArray(names) && names.length) {
        parts.push(`${role}: ${names.join(', ')}`)
      }
    }
  }
  return parts.join('；') || '--'
}

const handleGenerateSchedule = (row) => {
  ElMessage.info(`计划「${row.plan_name}」的调度方案生成功能待调度模块完成后开放`)
}

const formatDate = (str) => {
  if (!str) return '--'
  return str.substring(0, 10)
}

const formatCost = (val) => {
  if (val == null) return '0'
  return Number(val).toLocaleString('zh-CN', { maximumFractionDigits: 0 })
}

const getRate = (actual, planned) => {
  if (!planned || !actual) return '0%'
  return Math.min(100, Math.round((actual / planned) * 100)) + '%'
}

const getStatusTagType = (status) => {
  const map = {
    待开始: 'info',
    申请停车: 'warning',
    检修中: 'primary',
    验收与质量检验: 'danger',
    已完成: 'success',
  }
  return map[status] || 'info'
}

onMounted(() => {
  fetchPlans()
})
</script>

<style scoped>
.maintenance-plan-container {
  padding: 24px;
  min-height: 100%;
  box-sizing: border-box;
}

.panel-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 4px 24px 0 rgba(0, 0, 0, 0.04);
  background: #ffffff;
  overflow: hidden;
}

.panel-header {
  padding: 20px 24px;
  background-color: #ffffff;
  border-bottom: 1px solid #f0f2f5;
}

.panel-title {
  font-size: 18px;
  font-weight: 600;
  display: flex;
  align-items: center;
  color: #1a1a1a;
}

.panel-icon {
  width: 24px;
  height: 24px;
  margin-right: 12px;
}

.panel-body {
  padding: 24px;
}

.filter-toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: nowrap;
  align-items: center;
  overflow-x: auto;
}

.search-input {
  width: 180px;
}

.filter-select {
  width: 130px;
}

.date-range-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.date-label {
  font-size: 13px;
  color: #606266;
  white-space: nowrap;
}

.date-picker {
  width: 120px;
}

.date-sep {
  color: #909399;
  font-size: 12px;
}

.filter-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
  margin-left: auto;
}

.plan-table {
  border-radius: 8px;
  overflow: hidden;
}

.plan-table :deep(th.el-table__cell) {
  background-color: #f8fafc !important;
  color: #475569;
  font-weight: 600;
}

.stats-row {
  display: flex;
  justify-content: space-around;
  gap: 8px;
}

.stat-item {
  text-align: center;
  flex: 1;
}

.stat-value {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.stat-value.rate {
  color: #f59e0b;
}

.stat-label {
  font-size: 11px;
  color: #909399;
  margin-top: 2px;
}

.action-buttons {
  display: flex;
  gap: 8px;
  justify-content: center;
}

.bottom-bar {
  margin-top: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}

.total-text {
  font-size: 13px;
  color: #606266;
}

/* 调度方案弹窗样式 */
.schedule-header {
  display: flex;
  flex-wrap: wrap;
  gap: 16px 24px;
  padding: 16px 20px;
  background-color: #f8fafc;
  border-radius: 8px;
  margin-bottom: 16px;
}

.schedule-info-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.schedule-info-item .label {
  font-size: 13px;
  color: #64748b;
}

.schedule-info-item .value {
  font-size: 13px;
  font-weight: 500;
  color: #1e293b;
}

.schedule-info-item .value.highlight {
  font-size: 16px;
  font-weight: 700;
  color: #3b82f6;
}

/* 甘特图容器 */
.gantt-container {
  display: flex;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 16px;
}

/* 左侧面板 */
.gantt-left-panel {
  width: 280px;
  flex-shrink: 0;
  border-right: 1px solid #e2e8f0;
  background-color: #ffffff;
}

.gantt-left-header {
  display: flex;
  padding: 12px 8px;
  background-color: #f1f5f9;
  border-bottom: 1px solid #e2e8f0;
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
}

.gantt-left-header .col-id {
  width: 36px;
  text-align: center;
}

.gantt-left-header .col-process {
  flex: 1;
  padding-left: 8px;
}

.gantt-left-header .col-duration {
  width: 40px;
  text-align: center;
}

.gantt-left-body {
  max-height: 360px;
  overflow-y: auto;
}

.gantt-left-body .gantt-row {
  display: flex;
  padding: 10px 8px;
  border-bottom: 1px solid #f1f5f9;
  font-size: 12px;
  align-items: center;
}

.gantt-left-body .gantt-row:hover {
  background-color: #f8fafc;
}

.gantt-left-body .col-id {
  width: 36px;
  text-align: center;
  color: #94a3b8;
}

.gantt-left-body .col-process {
  flex: 1;
  padding-left: 8px;
  color: #1e293b;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.gantt-left-body .col-duration {
  width: 40px;
  text-align: center;
  color: #64748b;
  font-weight: 500;
}

/* 右侧时间轴面板 */
.gantt-right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.gantt-header {
  display: flex;
  padding: 12px 0;
  background-color: #f1f5f9;
  border-bottom: 1px solid #e2e8f0;
  overflow-x: auto;
}

.gantt-header-cell {
  flex: 1;
  min-width: 60px;
  text-align: center;
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  white-space: nowrap;
}

.gantt-body {
  flex: 1;
  max-height: 360px;
  overflow-y: auto;
  overflow-x: auto;
}

.gantt-body .gantt-row {
  display: flex;
  min-height: 42px;
  border-bottom: 1px solid #f1f5f9;
}

.gantt-row-content {
  flex: 1;
  position: relative;
  min-width: 0;
  padding: 6px 0;
}

.gantt-bar {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  border-radius: 4px;
  padding: 4px 8px;
  cursor: pointer;
  transition: opacity 0.2s;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}

.gantt-bar:hover {
  opacity: 0.9;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

.bar-label {
  font-size: 11px;
  color: #ffffff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 120px;
}

/* 任务详情列表 */
.schedule-tasks-detail {
  margin-top: 16px;
}

.schedule-tasks-detail h4 {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 12px;
}

/* 任务悬停提示 */
.task-tooltip {
  position: fixed;
  z-index: 9999;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 12px 16px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  min-width: 240px;
  pointer-events: none;
}

.tooltip-title {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid #f1f5f9;
}

.tooltip-row {
  display: flex;
  gap: 8px;
  font-size: 13px;
  line-height: 1.8;
  color: #475569;
}

.tooltip-label {
  font-weight: 500;
  color: #64748b;
  white-space: nowrap;
}
</style>
