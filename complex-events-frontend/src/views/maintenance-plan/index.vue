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
          <el-button size="small" @click="resetSearch">重置</el-button>
          <el-button type="primary" size="small" @click="handleSearch">查询</el-button>
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
          <el-table-column prop="plan_name" label="计划名称" min-width="150" show-overflow-tooltip />
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
          <el-table-column label="操作" min-width="200" align="center">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button size="small" type="primary" @click="goDetail(row)">查看详情</el-button>
                <el-button size="small" type="primary" :disabled="!row.schedule_plan_id" @click="goSchedule(row)">查看调度计划</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>

        <div class="bottom-bar">
          <el-button type="primary" @click="goCreate">
            <el-icon><Plus /></el-icon> + 新增检修计划
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { List, Plus } from '@element-plus/icons-vue'
import { getMaintenancePlans, deleteMaintenancePlan } from '@/api/maintenancePlan'

defineOptions({ name: 'MaintenancePlanList' })

const router = useRouter()

const loading = ref(false)
const plans = ref([])

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

const goSchedule = (row) => {
  router.push(`/maintenance-plan/detail/${row.id}`)
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
  flex-wrap: wrap;
  align-items: center;
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
</style>
