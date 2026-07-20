<template>
  <div class="process-confirmation-container">
    <el-card class="panel-card" shadow="hover">
      <div class="panel-header">
        <div class="panel-title">
          <el-icon class="panel-icon"><Checked /></el-icon>
          流程确认
        </div>
        <div class="header-actions">
          <el-button type="primary" size="small" @click="handleBatchConfirm" :disabled="!hasPendingProcesses">
            <el-icon><Checked /></el-icon> 批量确认
          </el-button>
        </div>
      </div>

      <ProcessFilter
        :processes="processes"
        :equipment-info="equipmentInfo"
        @filter-change="handleFilterChange"
      />

      <ProcessTable
        :processes="filteredProcesses"
        @view-detail="openProcessDetail"
        @cancel="handleCancel"
      />

      <ProcessDetail
        :visible="detailDialogVisible"
        :process="currentProcess"
        :all-processes="processes"
        @close="closeDetailDialog"
        @confirm="handleDialogConfirm"
        @reject="handleDialogReject"
        @view-node="viewProcessNode"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Checked } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import ProcessFilter from './components/ProcessFilter.vue'
import ProcessTable from './components/ProcessTable.vue'
import ProcessDetail from './components/ProcessDetail.vue'
import { getProcessList, getEquipmentInfo, updateProcess, cancelProcess } from '@/api/processApi'
import { parseTimeToMinutes, TASK_STATUS } from './utils'

const userStore = useUserStore()

const processes = ref([])
const equipmentInfo = ref({ categories: [], types: {}, instances: {} })
const loading = ref(false)

const detailDialogVisible = ref(false)
const currentProcess = ref(null)

const filters = ref({
  category: '',
  type: '',
  instance: '',
  status: ''
})

const fetchProcesses = async (params = {}) => {
  loading.value = true
  try {
    const response = await getProcessList(params)
    processes.value = response.data.list
  } catch (error) {
    console.error('获取流程列表失败:', error)
  } finally {
    loading.value = false
  }
}

const fetchEquipmentInfo = async () => {
  try {
    const response = await getEquipmentInfo()
    equipmentInfo.value = response.data
  } catch (error) {
    console.error('获取设备信息失败:', error)
  }
}

// 后台管理员不可操作的状态：终态 + 待开始（工人操作）+ 等待施工回签（工人操作）
const ADMIN_NON_OPERABLE = new Set([
  TASK_STATUS.COMPLETED,
  TASK_STATUS.CANCELLED,
  TASK_STATUS.RELEASED,
  TASK_STATUS.PENDING_SIGN,
])

const hasPendingProcesses = computed(() => {
  return processes.value.some(p => !ADMIN_NON_OPERABLE.has(p.status))
})

const filteredProcesses = computed(() => {
  let result = [...processes.value]

  if (filters.value.instance) {
    result = result.filter(p => p.equipment_id === filters.value.instance)
  } else if (filters.value.type) {
    result = result.filter(p => p.equipment_type_name === filters.value.type)
  } else if (filters.value.category) {
    result = result.filter(p => p.equipment_category === filters.value.category)
  }

  if (filters.value.status) {
    result = result.filter(p => p.status === filters.value.status)
  }

  result.sort((a, b) => {
    const aTime = parseTimeToMinutes(a.scheduled_start_time)
    const bTime = parseTimeToMinutes(b.scheduled_end_time)
    return aTime - bTime
  })

  return result
})

function handleFilterChange(newFilters) {
  filters.value = newFilters
}

function openProcessDetail(process) {
  currentProcess.value = process
  detailDialogVisible.value = true
}

function closeDetailDialog() {
  detailDialogVisible.value = false
  currentProcess.value = null
}

function viewProcessNode(node) {
  currentProcess.value = node
}

function handleCancel(process) {
  ElMessageBox.confirm(
    `确定取消「${process.process_name}」？取消后不可恢复。`,
    '取消操作',
    {
      confirmButtonText: '确定取消',
      cancelButtonText: '返回',
      type: 'warning',
      center: true,
      size: 'small'
    }
  ).then(() => {
    cancelProcessStatus(process.id)
  }).catch(() => {})
}

function handleDialogConfirm({ process, comment }) {
  confirmProcessStatus(process.id, 'confirm', comment)
  closeDetailDialog()
}

function handleDialogReject({ process, reason }) {
  confirmProcessStatus(process.id, 'reject', reason)
  closeDetailDialog()
}

const confirmProcessStatus = async (processId, action, comments = '') => {
  try {
    await updateProcess({
      id: processId,
      action: action,
      approval_comments: comments,
      operator_name: userStore.name
    })
    await fetchProcesses()
    ElMessage.success(action === 'confirm' ? '已确认，进入下一状态' : '已驳回，退回上一状态')
  } catch (error) {
    console.error('更新状态失败:', error)
  }
}

const cancelProcessStatus = async (processId) => {
  try {
    await cancelProcess({
      id: processId,
      approval_comments: '管理员取消',
      operator_name: userStore.name
    })
    await fetchProcesses()
    ElMessage.warning('流程已取消')
  } catch (error) {
    console.error('取消失败:', error)
  }
}

function handleBatchConfirm() {
  const pendingNodes = processes.value.filter(
    p => !ADMIN_NON_OPERABLE.has(p.status)
  )

  if (pendingNodes.length === 0) {
    ElMessage.warning('无可确认的待审批任务')
    return
  }

  ElMessageBox.confirm(
    `确认 ${pendingNodes.length} 个待审批任务？将全部推进到下一状态。`,
    '批量确认',
    {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'info',
      center: true,
      size: 'small'
    }
  ).then(() => {
    pendingNodes.forEach(node => {
      confirmProcessStatus(node.id, 'confirm', '批量确认')
    })
    ElMessage.success(`已确认 ${pendingNodes.length} 个任务`)
  }).catch(() => {})
}

onMounted(() => {
  fetchProcesses()
  fetchEquipmentInfo()
})
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
  min-height: 0;
  display: flex;
  flex-direction: column;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.04);
}

/* el-card 将 slot 内容包在 el-card__body 中，必须让它参与 flex 布局 */
.panel-card :deep(.el-card__body) {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  overflow: hidden;
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
  color: #0b2c44;
  display: flex;
  align-items: center;
}

.panel-icon {
  margin-right: 8px;
  font-size: 20px;
  color: #1f6e9c;
}

.header-actions {
  display: flex;
  gap: 8px;
}
</style>