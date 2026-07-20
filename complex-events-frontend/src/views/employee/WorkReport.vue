<template>
  <div class="work-report">
    <!-- 头部导航 -->
    <div class="header">
      <div class="header-left">
        <span class="title">工况反馈</span>
      </div>
      <div class="header-right">
        <span class="employee-name">{{ userStore.name }}</span>
        <span class="role-badge">员工端</span>
      </div>
    </div>

    <!-- 主要内容区 -->
    <div class="main-content">
      <div class="content">
        <!-- 提交说明（仅可操作时显示） -->
        <div v-if="canOperate" class="submission-note">
          {{ submissionHint }}
        </div>

        <!-- 表单卡片 -->
        <div class="form-card">
          <!-- 任务信息 -->
          <div class="task-info">
            <div class="info-row">
              <div class="info-item">
                <span class="label">任务</span>
                <span class="value">{{ taskDisplay || '未选择' }}</span>
              </div>
              <div class="info-item">
                <span class="label">设备</span>
                <span class="value">{{ form.equipment || '—' }}</span>
              </div>
              <div class="info-item">
                <span class="label">工单号</span>
                <span class="value">{{ form.workOrderNo || '—' }}</span>
              </div>
            </div>
            <div class="info-row">
              <div class="info-item">
                <span class="label">计划时间</span>
                <span class="value">{{ form.planTime || '—' }}</span>
              </div>
              <div class="info-item">
                <span class="label">当前状态</span>
                <span class="value">{{ form.currentStatus || '—' }}</span>
              </div>
              <div class="info-item">
                <span class="label">下一个状态</span>
                <span class="value">{{ form.nextStatus || '-' }}</span>
              </div>
            </div>
          </div>

          <!-- 任务选择 -->
          <div class="task-select-section">
            <div class="task-select-row">
              <span class="label">工单选择</span>
              <select v-model="form.selectedWorkOrderId" @change="onWorkOrderChange" :disabled="loading">
                <option value="">请选择工单</option>
                <option v-for="wo in workOrderOptions" :key="wo.work_order_id" :value="wo.work_order_id">
                  {{ wo.work_order_title }} ({{ wo.order_number }})
                </option>
              </select>
            </div>

            <div class="task-select-row">
              <span class="label">工序选择</span>
              <select v-model="form.selectedProcessId" @change="onProcessChange" :disabled="!form.selectedWorkOrderId || loading">
                <option value="">请选择工序</option>
                <option v-for="proc in processOptions" :key="proc.process_id" :value="proc.process_id">
                  {{ proc.process_name }} ({{ proc.equipment_name }}) - {{ proc.task_code || '无编码' }}
                </option>
              </select>
            </div>
          </div>

          <!-- 不可操作提示 -->
          <div v-if="form.selectedProcessId && !canOperate" class="non-operable-hint">
            当前工序状态为「{{ form.currentStatus }}」，{{ hintReason }}
          </div>

          <!-- 上报表单（仅可操作时显示） -->
          <template v-if="canOperate">
            <div class="section-title">上报表单</div>

            <div class="form-group">
              <span class="label required">工况描述</span>
              <textarea v-model="form.conditionDesc" placeholder="请描述现场工况、发现问题、临时措施等" rows="4"></textarea>
            </div>

            <div class="form-group">
              <span class="label">附件上传</span>
              <div class="upload-area" @click="triggerFileInput">
                <div class="upload-content">
                  <span class="upload-icon">📎</span>
                  <span class="upload-text">将文件拖到此处，或点击上传</span>
                  <span class="upload-hint">支持图片格式；可选择上传图片附件</span>
                </div>
                <input type="file" ref="fileInput" @change="handleFileUpload" accept=".jpg,.jpeg,.png,.gif,.bmp" multiple style="display: none;" />
              </div>
              <div class="file-list" v-if="uploadedFiles.length > 0">
                <div v-for="(file, index) in uploadedFiles" :key="index" class="file-item">
                  <span class="file-name">📄 {{ file.name }}</span>
                  <span class="file-size">{{ (file.size / 1024).toFixed(0) }}KB</span>
                  <button type="button" @click="removeFile(index)" class="remove-btn">×</button>
                </div>
              </div>
            </div>

            <div class="form-actions">
              <button type="button" class="btn-save" @click="saveDraft">保存草稿</button>
              <button type="button" class="btn-submit" @click="submitReport" :disabled="submitting">
                {{ submitting ? '提交中...' : workerActionLabel }}
              </button>
            </div>
          </template>
        </div>

        <!-- 操作日志 -->
        <div class="recent-reports">
          <div class="section-title">{{ isProcessSelected ? '工序操作日志' : '最近操作' }}</div>

          <!-- 日志列表（和管理员端格式一致） -->
          <div
            v-if="operationLogs.length > 0"
            class="log-list"
            ref="logListRef"
            @scroll="handleLogScroll"
          >
            <div v-for="log in operationLogs" :key="log.id" class="log-item">
              <div class="log-header">
                <span v-if="log.user_id" class="log-operator">{{ log.user_id }}</span>
                <span :class="['log-type-tag', getLogTypeClass(log.operation_type)]">
                  {{ getOperationTypeLabel(log.operation_type) }}
                </span>
                <span class="log-status-flow">
                  <span class="log-status">{{ getStatusShortLabel(log.old_status) }}</span>
                  <span class="log-arrow">→</span>
                  <span class="log-status">{{ getStatusShortLabel(log.new_status) }}</span>
                </span>
                <span class="log-time">{{ log.created_at }}</span>
              </div>
              <div v-if="!isProcessSelected && (log.equipment_name || log.process_name)" class="log-task-info">
                {{ log.equipment_name }}{{ log.equipment_name && log.process_name ? ' · ' : '' }}{{ log.process_name }}
              </div>
              <div v-if="log.approval_comments" class="log-comment">{{ log.approval_comments }}</div>
              <div v-if="log.description" class="log-comment">{{ log.description }}</div>
            </div>

            <!-- 加载更多（仅未选工序时显示） -->
            <div v-if="!isProcessSelected && logsLoadingMore" class="log-loading-more">加载中...</div>
            <div v-else-if="!isProcessSelected && !logsHasMore && operationLogs.length > 0" class="log-no-more">— 没有更多了 —</div>
          </div>

          <!-- 空状态 -->
          <div v-else class="log-empty">暂无操作记录</div>
        </div>

        <!-- 提交成功弹窗 -->
        <div v-if="showSuccess" class="modal-overlay">
          <div class="modal-content">
            <div class="modal-icon">✓</div>
            <div class="modal-title">上报成功</div>
            <div class="modal-text">您的工况报告已成功提交</div>
            <button class="modal-btn" @click="resetAll">继续上报</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useUserStore } from '@/stores/user.js'
import request from '@/utils/request'

const userStore = useUserStore()
const showSuccess = ref(false)
const fileInput = ref(null)
const uploadedFiles = ref([])
const submitting = ref(false)
const workOrderOptions = ref([])
const processOptions = ref([])
const loading = ref(false)

// 操作日志（替代原来的 recentReports）
const operationLogs = ref([])
const logListRef = ref(null)
const logsOffset = ref(0)
const logsHasMore = ref(true)
const logsLoadingMore = ref(false)
const logsTotal = ref(0)
const LOGS_PAGE_SIZE = 10

const isProcessSelected = computed(() => !!form.selectedProcessId)

const form = reactive({
  selectedWorkOrderId: '',
  selectedProcessId: '',
  equipment: '',
  workOrderNo: '',
  planTime: '',
  currentStatus: '',
  nextStatus: '',
  conditionDesc: '',
  conditionType: 'in_progress'
})

// 状态常量（统一标准，与管理员端一致）
const TASK_STATUS = {
  RELEASED: 'released',
  PENDING_ENGINEER: 'pending_engineer',
  PENDING_CONSTRUCTION: 'pending_construction',
  PENDING_TEAM: 'pending_team',
  PENDING_SIGN: 'pending_sign',
  SUBMITTED: 'submitted',
  PENDING_PROCESS_CLOSE: 'pending_process_close',
  PENDING_EQUIPMENT_CLOSE: 'pending_equipment_close',
  COMPLETED: 'completed',
  CANCELLED: 'cancelled',
}

const STATUS_LABEL_MAP = {
  [TASK_STATUS.RELEASED]: '待开始',
  [TASK_STATUS.PENDING_ENGINEER]: '等待工程师确认',
  [TASK_STATUS.PENDING_CONSTRUCTION]: '等待施工确认',
  [TASK_STATUS.PENDING_TEAM]: '等待班组受理',
  [TASK_STATUS.PENDING_SIGN]: '等待施工回签',
  [TASK_STATUS.SUBMITTED]: '已提交',
  [TASK_STATUS.PENDING_PROCESS_CLOSE]: '等待工艺存储关闭',
  [TASK_STATUS.PENDING_EQUIPMENT_CLOSE]: '等待设备部关闭',
  [TASK_STATUS.COMPLETED]: '已完成',
  [TASK_STATUS.CANCELLED]: '已取消',
}

const STATUS_SEQUENCE = [
  TASK_STATUS.RELEASED,
  TASK_STATUS.PENDING_ENGINEER,
  TASK_STATUS.PENDING_CONSTRUCTION,
  TASK_STATUS.PENDING_TEAM,
  TASK_STATUS.PENDING_SIGN,
  TASK_STATUS.SUBMITTED,
  TASK_STATUS.PENDING_PROCESS_CLOSE,
  TASK_STATUS.PENDING_EQUIPMENT_CLOSE,
  TASK_STATUS.COMPLETED,
]

function getNextStatus(currentStatus) {
  const index = STATUS_SEQUENCE.indexOf(currentStatus)
  if (index === -1) return null
  if (index + 1 < STATUS_SEQUENCE.length) {
    return STATUS_SEQUENCE[index + 1]
  }
  return null
}

const workOrderDisplay = computed(() => {
  const wo = workOrderOptions.value.find(w => w.work_order_id === form.selectedWorkOrderId)
  return wo ? wo.work_order_title : ''
})

const processDisplay = computed(() => {
  const p = processOptions.value.find(p => p.process_id === form.selectedProcessId)
  return p ? p.process_name : ''
})

const taskDisplay = computed(() => {
  if (workOrderDisplay.value && processDisplay.value) {
    return `${workOrderDisplay.value} - ${processDisplay.value}`
  }
  return workOrderDisplay.value || processDisplay.value || '未选择'
})

// 当前选中工序的原始状态值
const selectedTaskStatus = computed(() => {
  const proc = processOptions.value.find(p => p.process_id === form.selectedProcessId)
  return proc ? proc.task_status : null
})

// 是否允许工人操作（仅在 released 或 pending_sign 时）
const canOperate = computed(() => {
  return selectedTaskStatus.value === 'released'
      || selectedTaskStatus.value === 'pending_sign'
})

// 按钮文字
const workerActionLabel = computed(() => {
  if (selectedTaskStatus.value === 'released') return '申请开工'
  if (selectedTaskStatus.value === 'pending_sign') return '提交工况'
  return '提交工况'
})

// 提交说明提示文字
const submissionHint = computed(() => {
  if (selectedTaskStatus.value === 'released')
    return '确认现场条件无误后，点击「申请开工」向管理员提交开工申请'
  if (selectedTaskStatus.value === 'pending_sign')
    return '提交现场工况照片及描述（可选择上传图片附件）'
  return ''
})

// 不可操作时的原因提示
const hintReason = computed(() => {
  if (!selectedTaskStatus.value) return ''
  if (selectedTaskStatus.value === 'submitted')
    return '工况已提交，等待管理员审批'
  return '需等待管理员确认后方可操作'
})

// 操作类型映射（和管理员端一致）
const OPERATION_TYPE_MAP = {
  'confirm': '确认通过',
  'reject': '驳回',
  'cancel': '取消',
  'approval_confirm': '确认通过',
  'approval_reject': '驳回',
  'approval_approved': '审批通过',
  'approval_rejected': '审批驳回',
  'status_update': '状态变更',
  'upload_photo': '上传图片',
}

const STATUS_SHORT_MAP = {
  'released': '待开始',
  'pending_engineer': '待工程师确认',
  'pending_construction': '待施工确认',
  'pending_team': '待班组受理',
  'pending_sign': '待施工回签',
  'submitted': '已提交',
  'pending_process_close': '待工艺关闭',
  'pending_equipment_close': '待设备部关闭',
  'completed': '已完成',
  'cancelled': '已取消',
  'apply_for_start': '申请开工',
  'eng_approved': '工程师确认',
  'construction_confirmed': '施工确认',
  'team_received': '班组受理',
  'construction_signed': '施工回签',
  'process_closed': '工艺关闭',
  'equipment_closed': '设备部关闭',
  'in_progress': '进行中',
  'pending': '待开始',
  'rejected': '已驳回',
}

function getOperationTypeLabel(type) {
  return OPERATION_TYPE_MAP[type] || type
}

function getLogTypeClass(type) {
  if (!type) return 'tag-default'
  if (type.includes('confirm') || type.includes('approved')) return 'tag-confirm'
  if (type.includes('reject') || type.includes('rejected')) return 'tag-reject'
  if (type.includes('cancel')) return 'tag-cancel'
  if (type.includes('upload')) return 'tag-upload'
  if (type.includes('status')) return 'tag-status'
  return 'tag-default'
}

function getStatusShortLabel(status) {
  return STATUS_SHORT_MAP[status] || status || '--'
}

// 获取选中工序的操作日志（和管理员端同一个 API）
async function fetchProcessLogs() {
  const proc = processOptions.value.find(p => p.process_id === form.selectedProcessId)
  if (!proc?.task_id) {
    operationLogs.value = []
    return
  }
  try {
    const res = await request.get(`/api/work-order-tasks/${proc.task_id}/logs`)
    operationLogs.value = res.success ? (res.data || []) : []
  } catch (e) {
    operationLogs.value = []
  }
}

// 获取最近操作记录（分页，懒加载）
async function fetchRecentOperations(reset = false) {
  if (reset) {
    logsOffset.value = 0
    logsHasMore.value = true
    operationLogs.value = []
  }
  if (!logsHasMore.value) return

  logsLoadingMore.value = true
  try {
    const res = await request.get('/api/worker/recent-operations', {
      params: { limit: LOGS_PAGE_SIZE, offset: logsOffset.value }
    })
    if (res.success) {
      const { items, total } = res.data
      if (reset) {
        operationLogs.value = items
      } else {
        operationLogs.value.push(...items)
      }
      logsTotal.value = total
      logsOffset.value += items.length
      logsHasMore.value = logsOffset.value < total
    }
  } catch (e) {
    console.error('获取操作记录失败:', e)
  } finally {
    logsLoadingMore.value = false
  }
}

// 滚动懒加载
function handleLogScroll() {
  if (isProcessSelected.value) return  // 工序日志不需要懒加载
  const el = logListRef.value
  if (!el || logsLoadingMore.value || !logsHasMore.value) return
  if (el.scrollTop + el.clientHeight >= el.scrollHeight - 40) {
    loadMoreLogs()
  }
}

function loadMoreLogs() {
  fetchRecentOperations(false)
}

// 获取工单和工序数据
const fetchWorkOrders = async () => {
  try {
    loading.value = true
    const workerId = userStore.emp_id
    if (!workerId) {
      console.warn('员工ID为空')
      return
    }

    const response = await request.get(`/api/worker-workorders/${workerId}`)

    if (response.success) {
      const workOrderMap = new Map()

      response.data.forEach(item => {
        if (!workOrderMap.has(item.work_order_id)) {
          workOrderMap.set(item.work_order_id, {
            work_order_id: item.work_order_id,
            work_order_title: item.work_order_title,
            order_number: item.order_number,
            work_order_status: item.work_order_status,
            priority: item.priority,
            work_order_created_at: item.work_order_created_at,
            processes: []
          })
        }
        workOrderMap.get(item.work_order_id).processes.push({
          process_id: item.process_id,
          process_name: item.process_name,
          equipment_id: item.equipment_id,
          equipment_name: item.equipment_name,
          description: item.description,
          estimated_hours: item.estimated_hours,
          task_id: item.task_id,
          task_code: item.task_code,
          task_status: item.task_status,
          is_milestone: item.is_milestone,
          assignment_status: item.assignment_status,
          scheduled_start_time: item.scheduled_start_time,
          scheduled_end_time: item.scheduled_end_time,
          actual_start_time: item.actual_start_time,
          actual_end_time: item.actual_end_time,
          work_order_id: item.work_order_id,
          order_number: item.order_number,
          work_order_title: item.work_order_title,
          priority: item.priority,
          worker_name: item.worker_name,
          worker_type: item.worker_type
        })
      })

      workOrderOptions.value = Array.from(workOrderMap.values()).sort((a, b) => a.work_order_id - b.work_order_id)
    }
  } catch (error) {
    console.error('获取工单数据失败:', error)
    alert('获取任务数据失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchWorkOrders()
  fetchRecentOperations(true)
})

const onWorkOrderChange = () => {
  form.selectedProcessId = ''
  form.equipment = ''
  form.workOrderNo = ''
  form.planTime = ''
  form.currentStatus = ''
  form.nextStatus = ''

  const selectedWO = workOrderOptions.value.find(wo => wo.work_order_id === form.selectedWorkOrderId)
  if (selectedWO) {
    processOptions.value = selectedWO.processes
  } else {
    processOptions.value = []
  }
}

const onProcessChange = () => {
  const selectedProc = processOptions.value.find(p => p.process_id === form.selectedProcessId)
  if (selectedProc) {
    form.equipment = selectedProc.equipment_name || '—'
    form.workOrderNo = selectedProc.order_number || '—'
    if (selectedProc.scheduled_start_time && selectedProc.scheduled_end_time) {
      form.planTime = `${selectedProc.scheduled_start_time} ~ ${selectedProc.scheduled_end_time}`
    } else {
      form.planTime = '—'
    }
    form.currentStatus = STATUS_LABEL_MAP[selectedProc.task_status] || selectedProc.task_status || '—'
    form.nextStatus = STATUS_LABEL_MAP[getNextStatus(selectedProc.task_status)] || '-'
    // 选中工序 → 加载该工序的操作日志
    fetchProcessLogs()
  } else {
    form.equipment = ''
    form.workOrderNo = ''
    form.planTime = ''
    form.currentStatus = ''
    form.nextStatus = ''
    // 取消选中 → 切回最近操作
    fetchRecentOperations(true)
  }
}

// 附件上传
const triggerFileInput = () => { fileInput.value && fileInput.value.click() }

const handleFileUpload = (event) => {
  const files = Array.from(event.target.files)
  files.forEach(file => {
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/bmp']
    if (!allowedTypes.includes(file.type)) {
      alert(`文件 ${file.name} 格式不支持，请上传图片文件`)
      return
    }
    if (file.size <= 10 * 1024 * 1024) {
      uploadedFiles.value.push(file)
    } else {
      alert(`文件 ${file.name} 超过 10MB 限制`)
    }
  })
  event.target.value = ''
}

const removeFile = (index) => { uploadedFiles.value.splice(index, 1) }

// 保存草稿
const saveDraft = () => {
  const draft = { form: { ...form }, files: uploadedFiles.value.map(f => f.name) }
  localStorage.setItem('workConditionDraft', JSON.stringify(draft))
  alert('草稿已保存')
}

// 提交校验
const validateForm = () => {
  if (!form.selectedWorkOrderId) { alert('请选择工单'); return false }
  if (!form.selectedProcessId) { alert('请选择工序'); return false }
  if (!form.conditionDesc || form.conditionDesc.trim() === '') { alert('请填写工况描述'); return false }
  return true
}

// 提交工况
const submitReport = async () => {
  if (!validateForm()) return

  try {
    submitting.value = true

    const formData = new FormData()
    formData.append('description', form.conditionDesc)

    if (uploadedFiles.value.length > 0) {
      uploadedFiles.value.forEach(file => {
        formData.append('photo', file)
      })
    }

    const selectedProc = processOptions.value.find(p => p.process_id === form.selectedProcessId)

    const response = await request.put(
      `/api/work-order-tasks/${selectedProc.task_id}/update-status`,
      formData
    )

    if (response.success) {
      showSuccess.value = true
    } else {
      alert(`提交失败: ${response.message || '未知错误'}`)
    }
  } catch (error) {
    console.error('提交工况失败:', error)
    alert('提交失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}

const resetForm = (keepTask = true) => {
  if (!keepTask) {
    form.selectedWorkOrderId = ''
    form.selectedProcessId = ''
    form.equipment = ''
    form.workOrderNo = ''
    form.planTime = ''
    form.currentStatus = ''
    form.nextStatus = ''
    processOptions.value = []
    operationLogs.value = []
  }
  form.conditionDesc = ''
  form.conditionType = 'in_progress'
  uploadedFiles.value = []
  if (fileInput.value) fileInput.value.value = ''
}

const resetAll = () => {
  showSuccess.value = false
  resetForm(false)
  fetchWorkOrders()
  fetchRecentOperations(true)
}
</script>

<style scoped>
* { margin: 0; padding: 0; box-sizing: border-box; }

.work-report {
  min-height: calc(100vh - 64px - 48px);
  background-color: #f5f7fa;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  color: #1e293b;
  font-size: 13px;
}

.header {
  background: white;
  padding: 12px 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e9ecef;
  box-shadow: 0 2px 4px rgba(0,0,0,0.02);
  border-radius: 8px;
  margin-bottom: 16px;
}

.header-left { display: flex; align-items: center; gap: 12px; }
.title { font-size: 16px; font-weight: 500; color: #1e293b; }
.header-right { display: flex; align-items: center; gap: 12px; }
.employee-name { font-size: 13px; color: #1e293b; }
.role-badge { font-size: 12px; padding: 4px 8px; background: #e9ecef; border-radius: 4px; color: #4a5568; }

.main-content { max-width: 1300px; margin: 0 auto; padding: 0 4px; }

.submission-note {
  background: #fff3e0; color: #e67e22; padding: 8px 16px;
  border-radius: 6px; font-size: 13px; margin-bottom: 16px;
}

.non-operable-hint {
  background: #f0f7ff;
  border: 1px solid #b8d4f0;
  border-radius: 6px;
  padding: 14px 18px;
  color: #3a6d99;
  font-size: 13px;
  text-align: center;
  margin-top: 12px;
}

.form-card {
  background: white; border-radius: 8px; padding: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-bottom: 20px;
}

.task-info { background: #f8fafc; border-radius: 6px; padding: 16px; margin-bottom: 16px; }
.info-row { display: flex; gap: 40px; margin-bottom: 12px; }
.info-row:last-child { margin-bottom: 0; }
.info-item { display: flex; align-items: center; gap: 8px; }
.info-item .label { color: #64748b; font-size: 12px; }
.info-item .value { color: #1e293b; font-size: 13px; font-weight: 500; }

.task-select-section { margin-bottom: 24px; padding: 16px 0; border-bottom: 1px solid #e9ecef; }
.task-select-row { display: flex; align-items: center; gap: 16px; margin-bottom: 12px; }
.task-select-row:last-child { margin-bottom: 0; }
.task-select-row .label { color: #1e293b; font-size: 13px; font-weight: 500; min-width: 80px; }
.task-select-row select {
  flex: 1; padding: 8px 12px; border: 1px solid #e9ecef; border-radius: 4px;
  font-size: 13px; color: #1e293b; background: white; max-width: 400px;
}
.task-select-row select:disabled { background-color: #f5f5f5; color: #999; cursor: not-allowed; }
.task-select-row select:focus { outline: none; border-color: #667eea; }

.section-title {
  font-size: 15px; font-weight: 500; color: #1e293b; margin-bottom: 16px;
  padding-left: 8px; border-left: 3px solid #667eea;
}

.form-group { margin-bottom: 20px; }
.form-group .label { display: block; margin-bottom: 6px; color: #1e293b; font-size: 13px; font-weight: 500; }
.form-group .label.required::after { content: '*'; color: #e53e3e; margin-left: 4px; }
.form-group textarea {
  width: 100%; padding: 8px 12px; border: 1px solid #e9ecef; border-radius: 4px;
  font-size: 13px; color: #1e293b; background: white; resize: vertical;
}
.form-group textarea:focus { outline: none; border-color: #667eea; box-shadow: 0 0 0 3px rgba(102,126,234,0.1); }

.upload-area {
  border: 1px dashed #cbd5e0; border-radius: 6px; padding: 24px;
  background: #f8fafc; cursor: pointer; transition: all 0.2s;
}
.upload-area:hover { border-color: #667eea; background: #f0f5ff; }
.upload-content { text-align: center; }
.upload-icon { font-size: 20px; color: #94a3b8; margin-right: 8px; }
.upload-text { font-size: 13px; color: #1e293b; }
.upload-hint { display: block; margin-top: 4px; font-size: 12px; color: #94a3b8; }

.file-list { margin-top: 12px; }
.file-item {
  display: flex; align-items: center; padding: 8px 12px; background: #f8fafc;
  border: 1px solid #e9ecef; border-radius: 4px; margin-bottom: 6px;
}
.file-item:last-child { margin-bottom: 0; }
.file-name { flex: 1; font-size: 12px; color: #1e293b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.file-size { font-size: 11px; color: #94a3b8; margin: 0 12px; }
.remove-btn { background: none; border: none; color: #94a3b8; font-size: 16px; cursor: pointer; padding: 0 4px; }
.remove-btn:hover { color: #e53e3e; }

.form-actions { display: flex; gap: 12px; justify-content: flex-end; margin-top: 24px; }
.btn-save, .btn-submit {
  padding: 8px 24px; border-radius: 4px; font-size: 13px; font-weight: 500;
  cursor: pointer; border: none; transition: all 0.2s;
}
.btn-save { background: #f1f5f9; color: #475569; }
.btn-save:hover { background: #e2e8f0; }
.btn-submit { background: #667eea; color: white; }
.btn-submit:hover { background: #5a67d8; transform: translateY(-1px); box-shadow: 0 4px 8px rgba(102,126,234,0.2); }
.btn-submit:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }

.recent-reports { background: white; border-radius: 8px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }

/* 操作日志（和管理员端一致） */
.log-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 360px;
  overflow-y: auto;
}

.log-item {
  background: #f8fbfd;
  border: 1px solid #e4edf2;
  border-radius: 6px;
  padding: 10px 14px;
}

.log-header {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.log-operator {
  font-size: 12px;
  font-weight: 600;
  color: #1e3747;
  white-space: nowrap;
}

.log-type-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
}

.tag-confirm { background: #d4edda; color: #155724; }
.tag-reject  { background: #fff3cd; color: #856404; }
.tag-cancel  { background: #e2e3e5; color: #383d41; }
.tag-upload  { background: #e6e6fa; color: #4b0082; }
.tag-status  { background: #cce5ff; color: #004085; }
.tag-default { background: #f0f3f7; color: #5a6c7e; }

.log-status-flow {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #4f6f8f;
}

.log-status {
  background: #eef2f6;
  padding: 1px 8px;
  border-radius: 4px;
  color: #1e3747;
  font-weight: 500;
}

.log-arrow {
  color: #99aab9;
  font-weight: 600;
}

.log-time {
  margin-left: auto;
  font-size: 11px;
  color: #99aab9;
}

.log-task-info {
  margin-top: 6px;
  font-size: 11px;
  color: #6b859c;
  padding-left: 2px;
}

.log-comment {
  margin-top: 8px;
  padding: 8px 12px;
  background: #ffffff;
  border-radius: 4px;
  border-left: 3px solid #409eff;
  font-size: 12px;
  color: #4a5e71;
  line-height: 1.5;
}

.log-loading-more {
  text-align: center;
  padding: 12px;
  color: #409eff;
  font-size: 12px;
}

.log-no-more {
  text-align: center;
  padding: 12px;
  color: #99aab9;
  font-size: 12px;
}

.log-empty {
  text-align: center;
  color: #99aab9;
  padding: 24px;
  background: #f8fbfd;
  border-radius: 6px;
  border: 1px dashed #d9e2e9;
  font-size: 13px;
}

.modal-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000;
}
.modal-content {
  background: white; border-radius: 8px; padding: 32px; width: 300px;
  text-align: center; box-shadow: 0 20px 40px rgba(0,0,0,0.2); animation: slideIn 0.3s ease;
}
@keyframes slideIn { from { transform: translateY(-20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
.modal-icon {
  width: 48px; height: 48px; background: #10b981; color: white; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; font-size: 24px; margin: 0 auto 16px;
}
.modal-title { font-size: 16px; font-weight: 600; color: #1e293b; margin-bottom: 8px; }
.modal-text { font-size: 13px; color: #64748b; margin-bottom: 20px; }
.modal-btn {
  background: #667eea; color: white; border: none; padding: 8px 32px;
  border-radius: 4px; font-size: 13px; font-weight: 500; cursor: pointer; transition: all 0.2s;
}
.modal-btn:hover { background: #5a67d8; }

@media (max-width: 768px) {
  .main-content { padding: 0 8px; }
  .info-row { flex-direction: column; gap: 8px; }
  .reports-header, .report-item { grid-template-columns: 1fr; gap: 8px; }
  .report-attachments { text-align: left; }
}
</style>
