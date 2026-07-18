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
          <el-descriptions-item label="调度方案">
            <el-tag v-if="plan.schedule_plan_id" type="success" size="small">已生成 (ID: {{ plan.schedule_plan_id }})</el-tag>
            <el-tag v-else type="info" size="small" effect="plain">未生成</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="实际开始时间">{{ plan.actual_start_time || '--' }}</el-descriptions-item>
          <el-descriptions-item label="实际结束时间">{{ plan.actual_end_time || '--' }}</el-descriptions-item>
        </el-descriptions>

        <!-- 统计卡片 -->
        <el-row :gutter="20" class="stats-row">
          <el-col :span="12">
            <el-card class="stat-card stat-hours" shadow="never">
              <div class="stat-header">
                <el-icon><Timer /></el-icon>
                <span>人工时统计</span>
              </div>
              <div class="stat-body">
                <div class="stat-item">
                  <div class="stat-label">计划</div>
                  <div class="stat-value stat-planned">{{ plan.planned_man_hours || 0 }} h</div>
                </div>
                <div class="stat-item">
                  <div class="stat-label">实际</div>
                  <div class="stat-value stat-actual">{{ plan.actual_man_hours || 0 }} h</div>
                </div>
                <div class="stat-item">
                  <div class="stat-label">完成率</div>
                  <div class="stat-value stat-rate">{{ hoursRate }}%</div>
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card class="stat-card stat-cost" shadow="never">
              <div class="stat-header">
                <el-icon><Money /></el-icon>
                <span>成本统计</span>
              </div>
              <div class="stat-body">
                <div class="stat-item">
                  <div class="stat-label">计划</div>
                  <div class="stat-value stat-planned">¥{{ formatCost(plan.planned_cost) }}</div>
                </div>
                <div class="stat-item">
                  <div class="stat-label">实际</div>
                  <div class="stat-value stat-actual">¥{{ formatCost(plan.actual_cost) }}</div>
                </div>
                <div class="stat-item">
                  <div class="stat-label">完成率</div>
                  <div class="stat-value stat-rate">{{ costRate }}%</div>
                </div>
              </div>
            </el-card>
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
              <el-tag size="small">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="priority" label="优先级" min-width="70" align="center" />
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

    <!-- 调度方案弹窗 -->
    <el-dialog
      v-model="scheduleDialogVisible"
      title="调度方案详情"
      width="90%"
      top="5vh"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <div v-loading="scheduleLoading">
        <div v-if="scheduleData && scheduleData.schedule_tasks && scheduleData.schedule_tasks.length > 0">
          <el-descriptions :column="3" border size="small" class="schedule-info">
            <el-descriptions-item label="调度方案ID">{{ scheduleData.schedule_plan_id }}</el-descriptions-item>
            <el-descriptions-item label="计划名称">{{ scheduleData.plan_name }}</el-descriptions-item>
            <el-descriptions-item label="任务总数">{{ scheduleData.schedule_tasks.length }}</el-descriptions-item>
          </el-descriptions>

          <el-table :data="scheduleData.schedule_tasks" border stripe size="small" style="width: 100%; margin-top: 16px">
            <el-table-column prop="process_name" label="工序名称" min-width="120" />
            <el-table-column prop="equipment_name" label="设备名称" min-width="120" />
            <el-table-column prop="equipment_category" label="设备类别" min-width="90" />
            <el-table-column prop="start_time_formatted" label="开始时间" min-width="140" />
            <el-table-column prop="end_time_formatted" label="结束时间" min-width="140" />
            <el-table-column prop="duration_days" label="持续天数" width="80" align="center" />
            <el-table-column label="分配工人" min-width="200" show-overflow-tooltip>
              <template #default="{ row }">{{ formatWorkers(row.workers) }}</template>
            </el-table-column>
          </el-table>
        </div>
        <el-empty v-else description="暂无调度方案数据" />
      </div>
      <template #footer>
        <el-button @click="scheduleDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Document, View, Edit, ArrowLeft, Timer, Money } from '@element-plus/icons-vue'
import { getMaintenancePlan, getPlanSchedulePlan } from '@/api/maintenancePlan'

defineOptions({ name: 'MaintenancePlanDetail' })

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const scheduleLoading = ref(false)
const plan = ref({})
const scheduleDialogVisible = ref(false)
const scheduleData = ref(null)

const planId = computed(() => route.params.id)

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

.stats-row {
  margin-bottom: 24px;
}

.stat-card {
  border-radius: 10px;
  border: 1px solid #f0f2f5;
}

.stat-hours {
  border-left: 4px solid #3b82f6;
}

.stat-cost {
  border-left: 4px solid #10b981;
}

.stat-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 16px;
}

.stat-body {
  display: flex;
  gap: 24px;
  justify-content: space-around;
}

.stat-item {
  text-align: center;
}

.stat-label {
  font-size: 12px;
  color: #94a3b8;
  margin-bottom: 6px;
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
  font-family: 'Courier New', monospace;
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
</style>
