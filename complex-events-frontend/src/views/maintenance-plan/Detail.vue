<template>
  <div class="detail-container" v-loading="loading">
    <el-card class="panel-card" shadow="hover">
      <div class="panel-header">
        <div class="panel-title">
          <el-icon class="panel-icon mr6"><Document /></el-icon>
          检修计划详情
        </div>
        <div class="header-actions">
          <el-button type="primary" @click="viewSchedulePlan" :disabled="!plan.schedule_plan_id">
            <el-icon><View /></el-icon> 查看调度计划
          </el-button>
          <el-button @click="goEdit">
            <el-icon><Edit /></el-icon> 编辑
          </el-button>
          <el-button type="danger" @click="handleDelete">
            <el-icon><Delete /></el-icon> 删除
          </el-button>
          <el-button @click="goBack">
            <el-icon><ArrowLeft /></el-icon> 返回
          </el-button>
        </div>
      </div>

      <div class="panel-body" v-if="plan.id">
        <!-- 基本信息 -->
        <el-descriptions title="计划基本信息" :column="3" border class="info-section">
          <el-descriptions-item label="计划名称">
            <span class="highlight-text">{{ plan.plan_name }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="检修规模">
            <el-tag :type="getScaleTagType(plan.plan_scale)" size="small">{{ plan.plan_scale || '--' }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="当前进度">
            <el-tag :type="getStatusTagType(plan.status)" size="small" effect="dark">{{ plan.status || '--' }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="发起人">{{ plan.initiator || '--' }}</el-descriptions-item>
          <el-descriptions-item label="发起时间">{{ formatDateTime(plan.initiated_at) }}</el-descriptions-item>
          <el-descriptions-item label="关联工单数">{{ plan.work_order_count || 0 }}</el-descriptions-item>
          <el-descriptions-item label="计划开始时间">{{ plan.planned_start_time || '--' }}</el-descriptions-item>
          <el-descriptions-item label="计划结束时间">{{ plan.planned_end_time || '--' }}</el-descriptions-item>
          <el-descriptions-item label="人工费用">
            <span class="highlight-text">¥{{ formatCost(totalLaborCost) }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="实际开始时间">{{ plan.actual_start_time || '--' }}</el-descriptions-item>
          <el-descriptions-item label="实际结束时间">{{ plan.actual_end_time || '--' }}</el-descriptions-item>
        </el-descriptions>

        <!-- 统计卡片 -->
        <el-row :gutter="16" class="stats-row">
          <el-col :span="12">
            <div class="stat-card stat-hours">
              <div class="stat-title-wrap">
                <el-icon class="stat-icon"><Timer /></el-icon>
                <span class="stat-title">人工时统计</span>
              </div>
              <div class="stat-data">
                <div class="stat-row">
                  <span class="stat-row-label">计划</span>
                  <span class="stat-row-value stat-planned">{{ plan.planned_man_hours || 0 }} h</span>
                </div>
                <div class="stat-row">
                  <span class="stat-row-label">实际</span>
                  <span class="stat-row-value stat-actual">{{ plan.actual_man_hours || 0 }} h</span>
                </div>
                <div class="stat-row">
                  <span class="stat-row-label">完成率</span>
                  <span class="stat-row-value stat-rate">{{ hoursRate }}%</span>
                </div>
              </div>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="stat-card stat-cost">
              <div class="stat-title-wrap">
                <el-icon class="stat-icon"><Money /></el-icon>
                <span class="stat-title">成本统计</span>
              </div>
              <div class="stat-data">
                <div class="stat-row">
                  <span class="stat-row-label">计划</span>
                  <span class="stat-row-value stat-planned">¥{{ formatCost(plan.planned_cost) }}</span>
                </div>
                <div class="stat-row">
                  <span class="stat-row-label">实际</span>
                  <span class="stat-row-value stat-actual">¥{{ formatCost(plan.actual_cost) }}</span>
                </div>
                <div class="stat-row">
                  <span class="stat-row-label">完成率</span>
                  <span class="stat-row-value stat-rate">{{ costRate }}%</span>
                </div>
              </div>
            </div>
          </el-col>
        </el-row>

        <!-- 关联工单列表 -->
        <el-divider content-position="left">关联工单列表</el-divider>

        <el-table
          :data="plan.work_orders"
          border
          stripe
          class="wo-table"
          style="width: 100%"
        >
          <el-table-column type="expand">
            <template #default="{ row }">
              <div class="task-expand">
                <div v-if="row.tasks && row.tasks.length > 0">
                  <el-table :data="row.tasks" border size="small" style="width: 100%">
                    <el-table-column prop="task_code" label="任务编码" min-width="120" />
                    <el-table-column prop="process_name" label="工序名称" min-width="120" />
                    <el-table-column prop="equipment_name" label="设备" min-width="120" />
                    <el-table-column prop="estimated_hours" label="预计工时" width="90" align="center" />
                    <el-table-column prop="status" label="状态" width="90" align="center">
                      <template #default="{ row: task }">
                        <el-tag size="small">{{ task.status }}</el-tag>
                      </template>
                    </el-table-column>
                    <el-table-column prop="scheduled_start_time" label="计划开始" min-width="120" align="center" />
                    <el-table-column prop="scheduled_end_time" label="计划结束" min-width="120" align="center" />
                    <el-table-column label="人员" min-width="160" show-overflow-tooltip>
                      <template #default="{ row: task }">{{ formatWorkers(task.workers) }}</template>
                    </el-table-column>
                  </el-table>
                </div>
                <el-empty v-else description="该工单暂无任务" :image-size="60" />
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="order_number" label="工单编号" min-width="140" />
          <el-table-column prop="title" label="工单标题" min-width="160" show-overflow-tooltip />
          <el-table-column prop="equipment_name" label="设备名称" min-width="130" show-overflow-tooltip />
          <el-table-column prop="status" label="状态" min-width="80" align="center">
            <template #default="{ row }">
              <el-tag size="small">{{ statusMap[row.status] || row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="priority" label="优先级" min-width="70" align="center">
            <template #default="{ row }">
              {{ priorityMap[row.priority] || row.priority }}
            </template>
          </el-table-column>
          <el-table-column label="人工费用" min-width="100" align="center">
            <template #default="{ row }">
              <span class="cost-value">¥{{ formatCost(row.labor_cost) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="任务进度" min-width="130" align="center">
            <template #default="{ row }">
              <el-progress
                :percentage="row.progress || 0"
                :stroke-width="14"
                :text-inside="true"
                :status="getProgressStatus(row.progress)"
              />
            </template>
          </el-table-column>
          <el-table-column label="任务统计" min-width="100" align="center">
            <template #default="{ row }">
              {{ row.task_completed || 0 }} / {{ row.task_total || 0 }}
            </template>
          </el-table-column>
        </el-table>
      </div>

      <el-empty v-else-if="!loading" description="未找到检修计划" />
    </el-card>

    <!-- 调度方案弹窗 - 卡片式甘特图布局 -->
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
                <span class="col-equipment">设备名称</span>
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
                  <span class="col-equipment" :title="task.equipment_name">{{ task.equipment_name }}</span>
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
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, View, Edit, ArrowLeft, Timer, Money, Delete } from '@element-plus/icons-vue'
import { getMaintenancePlan, getPlanSchedulePlan, deleteMaintenancePlan } from '@/api/maintenancePlan'

defineOptions({ name: 'MaintenancePlanDetail' })

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const scheduleLoading = ref(false)
const plan = ref({})
const scheduleDialogVisible = ref(false)
const scheduleData = ref(null)

const planId = computed(() => route.params.id)

const statusMap = {
  pending: '待处理',
  processing: '进行中',
  completed: '已完成',
  closed: '已关闭',
  released: '已下发',
  scheduled: '已排程',
  equipment_closed: '设备已关闭',
}

const priorityMap = {
  high: '高',
  medium: '中',
  low: '低',
}

// 人工费用合计（所有关联工单）
const totalLaborCost = computed(() => {
  if (!plan.value.work_orders) return 0
  return plan.value.work_orders.reduce((sum, wo) => sum + (wo.labor_cost || 0), 0)
})

// 完成率计算
const hoursRate = computed(() => {
  if (!plan.value.planned_man_hours) return 0
  return Math.min(100, Math.round((plan.value.actual_man_hours / plan.value.planned_man_hours) * 100))
})

const costRate = computed(() => {
  if (!plan.value.planned_cost) return 0
  return Math.min(100, Math.round((plan.value.actual_cost / plan.value.planned_cost) * 100))
})

// 加载详情
const fetchDetail = async () => {
  loading.value = true
  try {
    const res = await getMaintenancePlan(planId.value)
    plan.value = res.data || {}
  } catch (error) {
    console.error('获取计划详情失败:', error)
  } finally {
    loading.value = false
  }
}

// 查看调度方案
const viewSchedulePlan = async () => {
  scheduleDialogVisible.value = true
  scheduleLoading.value = true
  try {
    const res = await getPlanSchedulePlan(planId.value)
    scheduleData.value = res.data
  } catch (error) {
    console.error('获取调度方案失败:', error)
  } finally {
    scheduleLoading.value = false
  }
}

const goEdit = () => {
  router.push(`/maintenance-plan/edit/${planId.value}`)
}

const goBack = () => {
  router.push('/maintenance-plan/list')
}

const handleDelete = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要删除该检修计划吗？删除后关联的工单将回归工单池，可供创建新计划时选择。',
      '确认删除',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await deleteMaintenancePlan(planId.value)
    ElMessage.success('删除成功')
    router.push('/maintenance-plan/list')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 格式化
const formatDateTime = (str) => str || '--'

const formatCost = (val) => {
  if (val == null) return '0'
  return Number(val).toLocaleString('zh-CN', { maximumFractionDigits: 2 })
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

// 调度方案相关计算属性和方法
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

// 悬停提示
const taskTooltipVisible = ref(false)
const taskTooltipData = ref({})
const tooltipPosition = ref({ x: 0, y: 0 })

const showTaskTooltip = (event, task) => {
  taskTooltipData.value = task
  tooltipPosition.value = { x: event.clientX + 10, y: event.clientY + 10 }
  taskTooltipVisible.value = true
}

const hideTaskTooltip = () => {
  taskTooltipVisible.value = false
}

const getProgressStatus = (val) => {
  if (val >= 100) return 'success'
  if (val > 0) return ''
  return 'info'
}

const getScaleTagType = (scale) => {
  const map = { 日常巡检: 'info', 计划检修: '', 中型检修: 'warning', 大型检修: 'danger' }
  return map[scale] || 'info'
}

const getStatusTagType = (status) => {
  const map = {
    待开始: 'info',
    申请停车: 'warning',
    检修中: 'primary',
    验收与质量检验: 'warning',
    已完成: 'success',
  }
  return map[status] || 'info'
}

onMounted(() => {
  fetchDetail()
  const view = route.query.view
  if (view === 'schedule') {
    setTimeout(() => {
      viewSchedulePlan()
    }, 500)
  }
})
</script>

<style scoped>
.detail-container {
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
  display: flex;
  justify-content: space-between;
  align-items: center;
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

.header-actions {
  display: flex;
  gap: 10px;
}

.panel-body {
  padding: 24px;
}

.info-section {
  margin-bottom: 24px;
}

.highlight-text {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.cost-value {
  font-weight: 600;
  color: #e74c3c;
}

.stats-row {
  margin-bottom: 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 14px 18px;
  border-radius: 8px;
  background: #ffffff;
  border: 1px solid #f0f2f5;
}

.stat-hours {
  border-left: 3px solid #3b82f6;
}

.stat-cost {
  border-left: 3px solid #10b981;
}

.stat-title-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  min-width: 96px;
  padding-right: 16px;
  border-right: 1px dashed #e5e7eb;
}

.stat-icon {
  font-size: 22px;
  color: #64748b;
}

.stat-title {
  font-size: 13px;
  font-weight: 600;
  color: #475569;
}

.stat-data {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-left: 16px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-row-label {
  font-size: 12px;
  color: #94a3b8;
}

.stat-row-value {
  font-size: 15px;
  font-weight: 600;
  font-family: 'Roboto Mono', 'Consolas', monospace;
  letter-spacing: 0.3px;
}

.stat-planned {
  color: #3b82f6;
}

.stat-actual {
  color: #10b981;
}

.stat-rate {
  color: #f59e0b;
}

.wo-table {
  border-radius: 8px;
  overflow: hidden;
}

.wo-table :deep(th.el-table__cell) {
  background-color: #f8fafc !important;
  color: #475569;
  font-weight: 600;
}

.task-expand {
  padding: 16px 24px;
  background-color: #fafbfc;
}

.schedule-info {
  margin-bottom: 8px;
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

.gantt-left-header .col-equipment {
  display: none;
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

.gantt-left-body .col-equipment {
  display: none;
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
