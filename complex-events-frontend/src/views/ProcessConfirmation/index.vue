<template>
  <div class="process-confirmation-container">
    <el-card class="panel-card" shadow="hover">
      <div class="panel-header">
        <div class="panel-title">
          <el-icon class="panel-icon"><Checked /></el-icon>
          流程确认
        </div>
        <div class="header-actions">
          <el-button type="primary" size="small" @click="loadSchedulePlan" :loading="loading">
            <el-icon><Refresh /></el-icon> 刷新
          </el-button>
          <el-button type="success" size="small" @click="handleBatchConfirm" :disabled="!hasPendingProcesses">
            <el-icon><Checked /></el-icon> 批量确认
          </el-button>
        </div>
      </div>

      <!-- 设备筛选 - 三级联动 -->
      <div class="filter-section">
        <el-row :gutter="16" class="filter-row">
          <el-col :xs="24" :sm="6">
            <div class="filter-item">
              <div class="filter-label"><el-icon><Folder /></el-icon><span>设备种类</span></div>
              <el-select v-model="selectedCategory" placeholder="全部种类" clearable @change="handleCategoryChange" class="filter-select">
                <el-option v-for="item in categoryOptions" :key="item.value" :label="`${item.label} (${item.count})`" :value="item.value" />
              </el-select>
            </div>
          </el-col>
          <el-col :xs="24" :sm="6">
            <div class="filter-item">
              <div class="filter-label"><el-icon><Files /></el-icon><span>设备类型</span></div>
              <el-select v-model="selectedType" placeholder="全部类型" :disabled="!selectedCategory" clearable @change="handleTypeChange" class="filter-select">
                <el-option v-for="item in typeOptions" :key="item.value" :label="`${item.label} (${item.count})`" :value="item.value" />
              </el-select>
            </div>
          </el-col>
          <el-col :xs="24" :sm="6">
            <div class="filter-item">
              <div class="filter-label"><el-icon><Monitor /></el-icon><span>设备实例</span></div>
              <el-select v-model="selectedInstance" placeholder="全部实例" :disabled="!selectedType" clearable filterable class="filter-select">
                <el-option v-for="item in instanceOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </div>
          </el-col>
          <el-col :xs="24" :sm="6">
            <div class="filter-item">
              <div class="filter-label"><el-icon><DataLine /></el-icon><span>工单状态</span></div>
              <el-select v-model="selectedStatus" placeholder="全部状态" clearable class="filter-select">
                <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </div>
          </el-col>
        </el-row>
        <div class="filter-stats-bar">
          <el-tag type="info" effect="plain">共 {{ filteredProcesses.length }} 条工序</el-tag>
          <el-button v-if="selectedCategory || selectedType || selectedInstance || selectedStatus" type="primary" link size="small" @click="clearFilters">清除筛选</el-button>
        </div>
      </div>

      <!-- 主表格 -->
      <div class="table-container">
        <el-table
          :data="filteredProcesses"
          border
          size="small"
          height="60vh"
          v-loading="loading"
          :row-class-name="getRowClassName"
          highlight-current-row
        >
          <el-table-column prop="id" label="#" width="55" fixed="left" align="center" />
          <el-table-column prop="equipment_name" label="设备名称" min-width="120" show-overflow-tooltip fixed="left">
            <template #default="{ row }">
              <div class="equipment-info">
                <el-icon><Monitor /></el-icon>
                <span>{{ row.equipment_name || '--' }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="process_name" label="工序名称" min-width="130" show-overflow-tooltip>
            <template #default="{ row }">
              <span>{{ row.process_name }}</span>
              <el-tag v-if="row.is_milestone" size="small" type="warning" style="margin-left:4px;">里程碑</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="110" align="center">
            <template #default="{ row }">
              <el-tag :type="getStatusTagType(row.status)" size="small">{{ getStatusText(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="workers" label="责任人" min-width="120" show-overflow-tooltip>
            <template #default="{ row }">{{ formatWorkers(row.workers) }}</template>
          </el-table-column>
          <el-table-column prop="estimated_hours" label="预计时长" width="80" align="center">
            <template #default="{ row }">{{ row.estimated_hours || '--' }}天</template>
          </el-table-column>
          <el-table-column prop="scheduled_start_time" label="开始时间" min-width="130" align="center">
            <template #default="{ row }">{{ row.scheduled_start_time || '--' }}</template>
          </el-table-column>
          <el-table-column prop="scheduled_end_time" label="结束时间" min-width="130" align="center">
            <template #default="{ row }">{{ row.scheduled_end_time || '--' }}</template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right" align="center">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button type="primary" size="small" plain @click="openProcessDetail(row)">
                  <el-icon><View /></el-icon> 详情
                </el-button>
                <el-button type="success" size="small" plain @click="handleConfirm(row)">
                  <el-icon><Checked /></el-icon> 确认
                </el-button>
                <el-button type="danger" size="small" plain @click="handleReject(row)">
                  <el-icon><Close /></el-icon> 驳回
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 详情弹窗 -->
      <el-dialog v-model="detailDialogVisible" :title="`工序详情 - ${currentProcess?.process_name || ''}`" width="600px" destroy-on-close>
        <div v-if="currentProcess" class="process-detail">
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="设备名称">{{ currentProcess.equipment_name }}</el-descriptions-item>
            <el-descriptions-item label="工序名称">{{ currentProcess.process_name }}</el-descriptions-item>
            <el-descriptions-item label="当前状态">
              <el-tag :type="getStatusTagType(currentProcess.status)" size="small">{{ getStatusText(currentProcess.status) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="责任人">{{ formatWorkers(currentProcess.workers) }}</el-descriptions-item>
            <el-descriptions-item label="预计时长">{{ currentProcess.estimated_hours || '--' }}天</el-descriptions-item>
            <el-descriptions-item label="任务编码">{{ currentProcess.task_code || '--' }}</el-descriptions-item>
            <el-descriptions-item label="开始时间" :span="2">{{ currentProcess.scheduled_start_time || '--' }}</el-descriptions-item>
            <el-descriptions-item label="结束时间" :span="2">{{ currentProcess.scheduled_end_time || '--' }}</el-descriptions-item>
            <el-descriptions-item v-if="currentProcess.description" label="描述" :span="2">{{ currentProcess.description }}</el-descriptions-item>
            <el-descriptions-item v-if="currentProcess.approval_comments" label="审批意见" :span="2">{{ currentProcess.approval_comments }}</el-descriptions-item>
          </el-descriptions>

          <!-- 同设备工序流程 -->
          <div class="process-flow-section">
            <div class="section-title">工序流程（该设备）</div>
            <div class="process-timeline">
              <div
                v-for="(node, idx) in sortedProcessesByEquipment(currentProcess.equipment_id)"
                :key="node.id"
                class="timeline-item"
                :class="{ 'current-item': node.id === currentProcess.id }"
                @click="currentProcess = node"
              >
                <div class="timeline-dot" :class="`dot-${node.status}`">{{ idx + 1 }}</div>
                <div class="timeline-content">
                  <div class="timeline-name">{{ node.process_name }}</div>
                  <el-tag :type="getStatusTagType(node.status)" size="small" effect="plain">{{ getStatusText(node.status) }}</el-tag>
                </div>
              </div>
            </div>
          </div>
        </div>
        <template #footer>
          <el-button @click="detailDialogVisible = false">关闭</el-button>
          <el-button type="success" :loading="confirmLoading" @click="handleDialogConfirm">
            <el-icon><Checked /></el-icon> 确认
          </el-button>
          <el-button type="danger" :loading="rejectLoading" @click="handleDialogReject">
            <el-icon><Close /></el-icon> 驳回
          </el-button>
        </template>
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Checked, Monitor, Close, View, Folder, Files, DataLine, Refresh } from '@element-plus/icons-vue'
import axios from 'axios'

const BASE_URL = `${import.meta.env.VITE_APP_BASE_API || 'http://localhost:8800'}/api`

const schedulePlan = ref([])
const loading = ref(false)
const detailDialogVisible = ref(false)
const currentProcess = ref(null)
const confirmLoading = ref(false)
const rejectLoading = ref(false)

// 筛选
const selectedCategory = ref('')
const selectedType = ref('')
const selectedInstance = ref('')
const selectedStatus = ref('')
const categoryOptions = ref([])
const typeOptions = ref([])
const instanceOptions = ref([])

const STATUS_LABEL_MAP = {
  released: '待开始',
  apply_for_start: '申请开工',
  eng_approved: '工程师确认',
  construction_confirmed: '施工确认',
  team_received: '班组受理',
  construction_signed: '施工回签',
  process_closed: '工艺存储关闭',
  equipment_closed: '设备部关闭',
  cancelled: '取消',
  pending: '待处理',
  in_progress: '进行中',
  completed: '已完成',
  rejected: '已驳回',
}

const hasPendingProcesses = computed(() =>
  schedulePlan.value.some(p => !['equipment_closed', 'cancelled'].includes(p.status))
)

const statusOptions = computed(() => {
  const set = new Set(schedulePlan.value.map(p => p.status))
  return Array.from(set).map(s => ({ value: s, label: getStatusText(s) }))
})

const filteredProcesses = computed(() => {
  let list = [...schedulePlan.value]
  if (selectedInstance.value) list = list.filter(p => p.equipment_id === selectedInstance.value)
  else if (selectedType.value) list = list.filter(p => p.equipment_type_name === selectedType.value)
  else if (selectedCategory.value) list = list.filter(p => p.equipment_category === selectedCategory.value)
  if (selectedStatus.value) list = list.filter(p => p.status === selectedStatus.value)
  return list.sort((a, b) => parseTime(a.scheduled_start_time) - parseTime(b.scheduled_start_time))
})

function parseTime(str) {
  if (!str) return 0
  const dayM = str.match(/第(\d+)天/)
  const timeM = str.match(/(\d+):(\d+)/)
  return (dayM ? parseInt(dayM[1]) * 1440 : 0) + (timeM ? parseInt(timeM[1]) * 60 + parseInt(timeM[2]) : 0)
}

function extractEquipmentInfo() {
  const cats = new Map()
  schedulePlan.value.forEach(p => {
    const cat = p.equipment_category || '未分类'
    const type = p.equipment_type_name || '未知类型'
    const catEntry = cats.get(cat) || { count: 0, types: new Map() }
    catEntry.count++
    const typeEntry = catEntry.types.get(type) || { count: 0, instances: new Map() }
    typeEntry.count++
    typeEntry.instances.set(p.equipment_id, p.equipment_name)
    catEntry.types.set(type, typeEntry)
    cats.set(cat, catEntry)
  })
  categoryOptions.value = Array.from(cats.entries()).map(([v, d]) => ({ value: v, label: v, count: d.count }))
}

function handleCategoryChange() {
  selectedType.value = ''
  selectedInstance.value = ''
  if (!selectedCategory.value) { typeOptions.value = []; return }
  const types = new Map()
  schedulePlan.value.filter(p => (p.equipment_category || '未分类') === selectedCategory.value)
    .forEach(p => {
      const t = p.equipment_type_name || '未知类型'
      types.set(t, (types.get(t) || 0) + 1)
    })
  typeOptions.value = Array.from(types.entries()).map(([v, c]) => ({ value: v, label: v, count: c }))
}

function handleTypeChange() {
  selectedInstance.value = ''
  if (!selectedType.value) { instanceOptions.value = []; return }
  const insts = new Map()
  schedulePlan.value.filter(p =>
    (p.equipment_category || '未分类') === selectedCategory.value &&
    (p.equipment_type_name || '未知类型') === selectedType.value
  ).forEach(p => insts.set(p.equipment_id, p.equipment_name))
  instanceOptions.value = Array.from(insts.entries()).map(([v, l]) => ({ value: v, label: l }))
}

function clearFilters() {
  selectedCategory.value = ''
  selectedType.value = ''
  selectedInstance.value = ''
  selectedStatus.value = ''
  typeOptions.value = []
  instanceOptions.value = []
}

function getStatusTagType(status) {
  const map = { completed: 'success', equipment_closed: 'success', released: 'info', cancelled: 'danger', rejected: 'danger', apply_for_start: 'primary', eng_approved: 'primary', construction_confirmed: 'primary', team_received: 'warning', construction_signed: 'warning', process_closed: 'warning' }
  return map[status] || 'info'
}

function getStatusText(status) {
  return STATUS_LABEL_MAP[status] || status
}

function formatWorkers(workers) {
  if (!workers) return '未分配'
  if (typeof workers === 'string') {
    try { workers = JSON.parse(workers) } catch { return workers }
  }
  if (typeof workers === 'object' && !Array.isArray(workers)) {
    return Object.entries(workers).map(([r, ns]) => `${r}: ${Array.isArray(ns) ? ns.join('、') : ns}`).join('；') || '未分配'
  }
  return String(workers)
}

function getRowClassName({ row }) {
  if (['equipment_closed', 'completed'].includes(row.status)) return 'row-completed'
  if (['cancelled', 'rejected'].includes(row.status)) return 'row-rejected'
  if (['apply_for_start', 'eng_approved', 'construction_confirmed', 'team_received', 'construction_signed', 'process_closed'].includes(row.status)) return 'row-active'
  return ''
}

function sortedProcessesByEquipment(equipmentId) {
  return schedulePlan.value.filter(p => p.equipment_id === equipmentId)
    .sort((a, b) => parseTime(a.scheduled_start_time) - parseTime(b.scheduled_start_time))
}

function openProcessDetail(row) {
  currentProcess.value = row
  detailDialogVisible.value = true
}

async function callUpdateStatus(taskId, action, comments = '') {
  const res = await axios.put(`${BASE_URL}/work-order-tasks/${taskId}/update-status`, {
    action,
    approval_comments: comments,
  })
  return res.data
}

function updateLocalStatus(taskId, newStatus, comments) {
  const idx = schedulePlan.value.findIndex(p => p.id === taskId)
  if (idx !== -1) {
    schedulePlan.value[idx] = { ...schedulePlan.value[idx], status: newStatus, approval_comments: comments }
  }
}

async function handleConfirm(row) {
  try {
    const { value: comment } = await ElMessageBox.prompt('确认意见（可选）', `确认 - ${row.process_name}`, {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      inputPlaceholder: '请输入确认意见',
      inputType: 'textarea',
    })
    confirmLoading.value = true
    const result = await callUpdateStatus(row.id, 'confirm', comment || '')
    if (result.success) {
      ElMessage.success(`"${row.process_name}" 已确认，新状态: ${getStatusText(result.new_status)}`)
      updateLocalStatus(row.id, result.new_status, comment || '')
      detailDialogVisible.value = false
    } else {
      ElMessage.error(result.message || '确认失败')
    }
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('确认失败：' + (e?.response?.data?.message || e?.message || ''))
  } finally {
    confirmLoading.value = false
  }
}

async function handleReject(row) {
  try {
    const { value: reason } = await ElMessageBox.prompt('请输入驳回原因（必填）', `驳回 - ${row.process_name}`, {
      confirmButtonText: '确定驳回',
      cancelButtonText: '取消',
      type: 'warning',
      inputPlaceholder: '驳回原因',
      inputType: 'textarea',
      inputPattern: /\S+/,
      inputErrorMessage: '驳回原因不能为空',
    })
    rejectLoading.value = true
    const result = await callUpdateStatus(row.id, 'reject', reason)
    if (result.success) {
      ElMessage.warning(`已驳回 "${row.process_name}"，状态回退`)
      updateLocalStatus(row.id, result.new_status, reason)
      detailDialogVisible.value = false
    } else {
      ElMessage.error(result.message || '驳回失败')
    }
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('驳回失败：' + (e?.response?.data?.message || e?.message || ''))
  } finally {
    rejectLoading.value = false
  }
}

function handleDialogConfirm() { if (currentProcess.value) handleConfirm(currentProcess.value) }
function handleDialogReject() { if (currentProcess.value) handleReject(currentProcess.value) }

async function handleBatchConfirm() {
  const targets = filteredProcesses.value.filter(p => !['equipment_closed', 'cancelled'].includes(p.status))
  if (!targets.length) { ElMessage.warning('无可确认的工序'); return }
  try {
    await ElMessageBox.confirm(`确认 ${targets.length} 条工序？`, '批量确认', { type: 'info' })
    let ok = 0
    for (const row of targets) {
      try {
        const res = await axios.put(`${BASE_URL}/work-order-tasks/${row.id}/approve`)
        if (res.data.success) { updateLocalStatus(row.id, res.data.new_status, '批量确认'); ok++ }
      } catch {}
    }
    ElMessage.success(`批量确认完成，成功 ${ok} / ${targets.length}`)
  } catch {}
}

async function loadSchedulePlan() {
  loading.value = true
  try {
    const res = await axios.get(`${BASE_URL}/work-order-tasks`)
    const data = res.data?.data || res.data || []
    schedulePlan.value = data.map(p => ({
      ...p,
      equipment_category: p.equipment_category || '未分类',
      equipment_type_name: p.equipment_type_name || '未知类型',
    }))
    extractEquipmentInfo()
  } catch (e) {
    ElMessage.error('加载工单任务失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadSchedulePlan)
</script>

<style scoped>
.process-confirmation-container {
  padding: 16px;
  height: 100%;
  box-sizing: border-box;
  background-color: #f5f8fa;
}

.panel-card {
  height: 100%;
  border-radius: 12px;
}

.panel-header {
  padding: 12px 20px;
  border-bottom: 1px solid #eef2f6;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-title {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
  display: flex;
  align-items: center;
  gap: 8px;
}

.panel-icon { font-size: 20px; color: #409eff; }

.header-actions { display: flex; gap: 8px; }

.filter-section {
  padding: 12px 20px;
  border-bottom: 1px solid #eef2f6;
  background: #fafcfd;
}

.filter-row { margin-bottom: 8px; }

.filter-item {
  background: white;
  border-radius: 8px;
  padding: 8px 12px;
  border: 1px solid #e4edf2;
}

.filter-label {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 6px;
  font-size: 12px;
  color: #606266;
}

.filter-select { width: 100%; }

.filter-stats-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 8px;
}

.table-container { padding: 0 20px 16px; }

.equipment-info { display: flex; align-items: center; gap: 6px; }

.action-buttons { display: flex; gap: 4px; justify-content: center; }

/* 行颜色 */
:deep(.el-table .row-completed) { --el-table-tr-bg-color: #f0faf0; }
:deep(.el-table .row-rejected) { --el-table-tr-bg-color: #fff5f5; }
:deep(.el-table .row-active) { --el-table-tr-bg-color: #f0f7ff; }

/* 详情弹窗 */
.process-detail { font-size: 13px; }

.process-flow-section { margin-top: 16px; }

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f4e6a;
  margin-bottom: 10px;
  padding-left: 8px;
  border-left: 3px solid #409eff;
}

.process-timeline {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 240px;
  overflow-y: auto;
  padding: 8px;
  background: #f8fbfd;
  border-radius: 6px;
}

.timeline-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.timeline-item:hover { background: #eef2f6; }
.timeline-item.current-item { background: #e3f0fa; border: 1px solid #409eff; }

.timeline-dot {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 600;
  color: white;
  flex-shrink: 0;
}

.dot-released, .dot-pending { background: #99aab9; }
.dot-apply_for_start, .dot-eng_approved, .dot-construction_confirmed, .dot-in_progress { background: #409eff; }
.dot-team_received, .dot-construction_signed, .dot-process_closed { background: #e6a23c; }
.dot-equipment_closed, .dot-completed { background: #67c23a; }
.dot-cancelled, .dot-rejected { background: #f56c6c; }

.timeline-content { flex: 1; }

.timeline-name {
  font-size: 13px;
  font-weight: 500;
  color: #1c3343;
  margin-bottom: 3px;
}
</style>
