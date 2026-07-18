<template>
  <div class="create-plan-container">
    <el-card class="panel-card" shadow="hover">
      <div class="panel-header">
        <div class="panel-title">
          <el-icon class="panel-icon mr6"><EditPen /></el-icon>
          {{ isEdit ? '编辑检修计划' : '新建检修计划' }}
        </div>
        <el-button @click="goBack">
          <el-icon><ArrowLeft /></el-icon> 返回
        </el-button>
      </div>

      <div class="panel-body" v-loading="loading">
        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-width="130px"
          class="plan-form"
        >
          <!-- 基本信息 -->
          <el-divider content-position="left">基本信息</el-divider>

          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item label="计划名称" prop="plan_name">
                <el-input v-model="form.plan_name" placeholder="如：7.14A单元检修" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="检修规模" prop="plan_scale">
                <el-select v-model="form.plan_scale" placeholder="请选择检修规模" style="width: 100%">
                  <el-option label="日常巡检" value="日常巡检" />
                  <el-option label="计划检修" value="计划检修" />
                  <el-option label="中型检修" value="中型检修" />
                  <el-option label="大型检修" value="大型检修" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item label="计划状态" prop="status">
                <el-select v-model="form.status" placeholder="请选择状态" style="width: 100%">
                  <el-option label="待开始" value="待开始" />
                  <el-option label="申请停车" value="申请停车" />
                  <el-option label="检修中" value="检修中" />
                  <el-option label="验收与质量检验" value="验收与质量检验" />
                  <el-option label="已完成" value="已完成" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="发起人" prop="initiator">
                <el-input v-model="form.initiator" placeholder="请输入发起人姓名" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item label="发起时间" prop="initiated_at">
            <el-date-picker
              v-model="form.initiated_at"
              type="datetime"
              placeholder="选择发起时间"
              format="YYYY-MM-DD HH:mm:ss"
              value-format="YYYY-MM-DD HH:mm:ss"
              style="width: 300px"
            />
          </el-form-item>

          <!-- 时间与工时 -->
          <el-divider content-position="left">时间与工时</el-divider>

          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item label="计划开始时间">
                <el-input
                  :value="autoPlannedStartTime"
                  readonly
                  placeholder="选择工单后自动计算"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="计划结束时间">
                <el-input
                  :value="autoPlannedEndTime"
                  readonly
                  placeholder="选择工单后自动计算"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item label="实际开始时间">
                <el-date-picker
                  v-model="form.actual_start_time"
                  type="datetime"
                  placeholder="选择实际开始时间（可选）"
                  format="YYYY-MM-DD HH:mm:ss"
                  value-format="YYYY-MM-DD HH:mm:ss"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="实际结束时间">
                <el-date-picker
                  v-model="form.actual_end_time"
                  type="datetime"
                  placeholder="选择实际结束时间（可选）"
                  format="YYYY-MM-DD HH:mm:ss"
                  value-format="YYYY-MM-DD HH:mm:ss"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item label="计划人工时(h)">
                <el-input
                  :value="totalPlannedManHours"
                  readonly
                  placeholder="自动计算"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="实际人工时(h)">
                <el-input-number
                  v-model="form.actual_man_hours"
                  :min="0"
                  :step="0.5"
                  :precision="1"
                  placeholder="实际人工时"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item label="计划成本(元)">
                <el-input-number
                  v-model="form.planned_cost"
                  :min="0"
                  :step="100"
                  :precision="2"
                  placeholder="计划成本"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="实际成本(元)">
                <el-input-number
                  v-model="form.actual_cost"
                  :min="0"
                  :step="100"
                  :precision="2"
                  placeholder="实际成本"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
          </el-row>

          <!-- 关联工单选择 -->
          <el-divider content-position="left">关联工单</el-divider>

          <div class="work-order-section">
            <div class="wo-toolbar">
              <el-input
                v-model="woSearchKeyword"
                placeholder="搜索工单编号/标题/设备"
                clearable
                size="small"
                class="wo-search"
                :prefix-icon="Search"
              />
              <el-button type="primary" size="small" @click="fetchUnplannedWorkOrders" :loading="woLoading">
                <el-icon><Refresh /></el-icon> 刷新未计划工单
              </el-button>
            </div>

            <el-table
              ref="woTableRef"
              :data="filteredUnplannedOrders"
              v-loading="woLoading"
              border
              stripe
              max-height="360"
              @selection-change="handleSelectionChange"
              :row-key="(row) => row.id"
            >
              <el-table-column type="selection" width="50" reserve-selection />
              <el-table-column prop="order_number" label="工单编号" min-width="140">
                <template #default="{ row }">
                  <el-tag v-if="row.is_associated" type="success" size="small" effect="light" class="mr8">已关联</el-tag>
                  {{ row.order_number }}
                </template>
              </el-table-column>
              <el-table-column prop="title" label="工单标题" min-width="160" show-overflow-tooltip />
              <el-table-column prop="equipment_name" label="设备名称" min-width="130" show-overflow-tooltip />
              <el-table-column prop="status" label="状态" min-width="80" align="center">
                <template #default="{ row }">
                  <el-tag size="small">{{ row.status }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="priority" label="优先级" min-width="80" align="center" />
              <el-table-column prop="created_at" label="创建时间" min-width="140" align="center" />
            </el-table>

            <div class="selected-info" v-if="selectedWorkOrders.length > 0">
              <el-tag type="success" size="large">
                已选 {{ selectedWorkOrders.length }} 个工单
              </el-tag>
            </div>
          </div>

          <!-- 提交 -->
          <el-form-item class="form-footer">
            <el-button @click="goBack">取消</el-button>
            <el-button type="primary" @click="handleSubmit" :loading="submitting">
              {{ isEdit ? '保存修改' : '创建计划' }}
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { EditPen, ArrowLeft, Search, Refresh } from '@element-plus/icons-vue'
import {
  createMaintenancePlan,
  updateMaintenancePlan,
  getMaintenancePlan,
  getUnplannedWorkOrders,
} from '@/api/maintenancePlan'

defineOptions({ name: 'MaintenancePlanCreateOrEdit' })

const router = useRouter()
const route = useRoute()

const isEdit = computed(() => !!route.params.id)
const planId = computed(() => route.params.id)

const loading = ref(false)
const submitting = ref(false)
const woLoading = ref(false)
const formRef = ref()
const woTableRef = ref()

const form = reactive({
  plan_name: '',
  plan_scale: '',
  status: '待开始',
  initiator: '',
  initiated_at: '',
  planned_start_time: '',
  planned_end_time: '',
  actual_start_time: '',
  actual_end_time: '',
  planned_man_hours: 0,
  actual_man_hours: 0,
  planned_cost: 0,
  actual_cost: 0,
})

const rules = {
  plan_name: [{ required: true, message: '请输入计划名称', trigger: 'blur' }],
  plan_scale: [{ required: true, message: '请选择检修规模', trigger: 'change' }],
  status: [{ required: true, message: '请选择计划状态', trigger: 'change' }],
}

// 未计划工单
const unplannedOrders = ref([])
const woSearchKeyword = ref('')
const selectedWorkOrders = ref([])

const filteredUnplannedOrders = computed(() => {
  if (!woSearchKeyword.value) return unplannedOrders.value
  const kw = woSearchKeyword.value.toLowerCase()
  return unplannedOrders.value.filter((wo) => {
    return (
      (wo.order_number && wo.order_number.toLowerCase().includes(kw)) ||
      (wo.title && wo.title.toLowerCase().includes(kw)) ||
      (wo.equipment_name && wo.equipment_name.toLowerCase().includes(kw))
    )
  })
})

const totalPlannedManHours = computed(() => {
  return selectedWorkOrders.value.reduce((sum, wo) => {
    return sum + (wo.estimated_hours || 0)
  }, 0).toFixed(1)
})

const autoPlannedStartTime = computed(() => {
  if (selectedWorkOrders.value.length === 0) return ''
  const times = selectedWorkOrders.value
    .map((wo) => wo.scheduled_start_time)
    .filter(Boolean)
  if (times.length === 0) return '选中工单均未设置时间'
  return [...times].sort()[0]
})

const autoPlannedEndTime = computed(() => {
  if (selectedWorkOrders.value.length === 0) return ''
  const times = selectedWorkOrders.value
    .map((wo) => wo.scheduled_end_time)
    .filter(Boolean)
  if (times.length === 0) return '选中工单均未设置时间'
  return [...times].sort().pop()
})

// 获取未计划工单（编辑模式下传入 plan_id 获取已关联+未计划工单）
const fetchUnplannedWorkOrders = async () => {
  woLoading.value = true
  try {
    const params = isEdit.value ? { plan_id: planId.value } : {}
    const res = await getUnplannedWorkOrders(params)
    unplannedOrders.value = res.data || []
    if (isEdit.value && woTableRef.value) {
      await nextTick()
      unplannedOrders.value.forEach((wo) => {
        if (wo.is_associated) {
          woTableRef.value.toggleRowSelection(wo, true)
        }
      })
    }
  } catch (error) {
    console.error('获取未计划工单失败:', error)
  } finally {
    woLoading.value = false
  }
}

// 选择变化
const handleSelectionChange = (selection) => {
  selectedWorkOrders.value = selection
}

// 加载计划详情（编辑模式）
const loadPlanDetail = async () => {
  if (!isEdit.value) return
  loading.value = true
  try {
    const res = await getMaintenancePlan(planId.value)
    const data = res.data
    Object.keys(form).forEach((key) => {
      if (data[key] !== undefined && data[key] !== null) {
        form[key] = data[key]
      }
    })
  } catch (error) {
    console.error('获取计划详情失败:', error)
    ElMessage.error('获取计划详情失败')
  } finally {
    loading.value = false
  }
}

// 提交
const handleSubmit = async () => {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  submitting.value = true
  try {
    const workOrderIds = selectedWorkOrders.value.map((wo) => wo.id)
    const payload = { ...form }
    if (isEdit.value) {
      payload.work_order_ids = workOrderIds
      await updateMaintenancePlan(planId.value, payload)
      ElMessage.success('修改成功')
    } else {
      payload.work_order_ids = workOrderIds
      await createMaintenancePlan(payload)
      ElMessage.success('创建成功')
    }
    router.push('/maintenance-plan/list')
  } catch (error) {
    console.error('提交失败:', error)
  } finally {
    submitting.value = false
  }
}

const goBack = () => {
  router.push('/maintenance-plan/list')
}

onMounted(async () => {
  await fetchUnplannedWorkOrders()
  if (isEdit.value) {
    await loadPlanDetail()
  }
})
</script>

<style scoped>
.create-plan-container {
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

.panel-body {
  padding: 24px;
}

.plan-form {
  max-width: 1000px;
}

.work-order-section {
  margin-bottom: 24px;
}

.wo-toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  align-items: center;
}

.wo-search {
  width: 280px;
}

.selected-info {
  margin-top: 12px;
  display: flex;
  gap: 8px;
  align-items: center;
}

.form-footer {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #f0f2f5;
}

.form-footer :deep(.el-form-item__content) {
  justify-content: flex-end;
}

.mr8 {
  margin-right: 8px;
}
</style>
