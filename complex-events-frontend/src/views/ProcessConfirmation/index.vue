<template>
  <div class="process-confirmation-container">
    <el-card class="panel-card" shadow="hover">
      <div class="panel-header">
        <div class="panel-title">
          <el-icon class="panel-icon"><Checked /></el-icon>
          流程确认
        </div>
        <div class="header-actions">
          <el-button type="primary" size="small" @click="handleBatchConfirm" :disabled="!hasOnHoldProcesses">
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
        @confirm="handleConfirm"
        @reject="handleReject"
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
import ProcessFilter from './components/ProcessFilter.vue'
import ProcessTable from './components/ProcessTable.vue'
import ProcessDetail from './components/ProcessDetail.vue'
import { getProcessList, getEquipmentInfo, updateProcess } from '@/api/processApi'
import { parseTimeToMinutes } from './utils'

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

const hasOnHoldProcesses = computed(() => {
  return processes.value.some(p => p.status === 'on_hold')
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

function handleConfirm(process) {
  ElMessageBox.confirm(
    `确认完成「${process.process_name}」？`,
    '确认操作',
    {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'info',
      center: true,
      size: 'small'
    }
  ).then(() => {
    updateProcessStatus(process.id, 'confirmed', '')
    ElMessage.success(`"${process.process_name}" 已确认`)
  }).catch(() => {})
}

function handleReject(process) {
  const rejectAction = process.status === 'rejected' ? '再次驳回' : '驳回'

  ElMessageBox.prompt('请输入驳回原因', `${rejectAction} - ${process.process_name}`, {
    confirmButtonText: `确定${rejectAction}`,
    cancelButtonText: '取消',
    type: 'warning',
    inputPlaceholder: '请填写驳回原因（必填）',
    inputType: 'textarea',
    inputPattern: /\S+/,
    inputErrorMessage: '驳回原因不能为空'
  }).then(({ value }) => {
    updateProcessStatus(process.id, 'rejected', value)
    ElMessage.warning(`已${rejectAction} "${process.process_name}"，原因：${value}`)
  }).catch(() => {})
}

function handleDialogConfirm({ process, comment }) {
  updateProcessStatus(process.id, 'confirmed', comment)
  closeDetailDialog()
}

function handleDialogReject({ process, reason }) {
  updateProcessStatus(process.id, 'rejected', reason)
  closeDetailDialog()
}

const updateProcessStatus = async (processId, newStatus, comments = '') => {
  try {
    await updateProcess({
      id: processId,
      status: newStatus,
      approval_comments: comments
    })
    await fetchProcesses()
  } catch (error) {
    console.error('更新状态失败:', error)
  }
}

function handleBatchConfirm() {
  const onHoldNodes = processes.value.filter(p => p.status === 'on_hold')

  if (onHoldNodes.length === 0) {
    ElMessage.warning('无可确认的待审批任务')
    return
  }

  ElMessageBox.confirm(
    `确认 ${onHoldNodes.length} 个待审批任务？`,
    '批量确认',
    {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'info',
      center: true,
      size: 'small'
    }
  ).then(() => {
    onHoldNodes.forEach(node => {
      updateProcessStatus(node.id, 'confirmed', '批量确认')
    })
    ElMessage.success(`已确认 ${onHoldNodes.length} 个任务`)
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
  display: flex;
  flex-direction: column;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.04);
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