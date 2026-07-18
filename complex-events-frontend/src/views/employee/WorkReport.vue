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

        <!-- 最近上报 -->
        <div class="recent-reports" v-if="recentReports.length > 0">
          <div class="section-title">最近上报</div>
          <div class="reports-header">
            <span>时间</span>
            <span>摘要</span>
            <span>附件</span>
          </div>
          <div class="reports-list">
            <div v-for="report in recentReports" :key="report.id" class="report-item">
              <span class="report-time">{{ report.time }}</span>
              <div class="report-summary">
                <span :class="['report-type', report.typeClass]">{{ report.type }}</span>
                <span class="summary-text">{{ report.summary }}</span>
              </div>
              <span class="report-attachments">{{ report.attachments }}个</span>
            </div>
          </div>
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
const recentReports = ref([])
const workOrderOptions = ref([])
const processOptions = ref([])
const loading = ref(false)

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

// 获取操作类型文本
const getOperationTypeText = (type) => {
  const map = {
    'status_update': '状态变更',
    'upload_photo': '上传附件',
    'approval_confirm': '审批通过',
    'approval_reject': '审批驳回'
  }
  return map[type] || type
}

const getTypeClass = (type) => {
  if (type && type.includes('approval')) return 'type-risk'
  return 'type-normal'
}

// 获取历史记录
const fetchRecentReports = async () => {
  try {
    const workerId = userStore.emp_id
    if (!workerId) return

    const response = await request.get(`/api/worker/${workerId}/history`)

    if (response.success) {
      recentReports.value = response.data.map(item => ({
        id: item.id,
        time: item.created_at,
        type: getOperationTypeText(item.operation_type),
        typeClass: getTypeClass(item.operation_type),
        summary: item.description || item.operation_type,
        attachments: item.attachment_path ? 1 : 0
      }))
    }
  } catch (error) {
    console.error('获取历史失败:', error)
  }
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
  fetchRecentReports()
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
  } else {
    form.equipment = ''
    form.workOrderNo = ''
    form.planTime = ''
    form.currentStatus = ''
    form.nextStatus = ''
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
.reports-header { display: grid; grid-template-columns: 120px 1fr 60px; padding: 12px 0; border-bottom: 1px solid #e9ecef; color: #94a3b8; font-size: 12px; }
.reports-list { margin-top: 8px; }
.report-item { display: grid; grid-template-columns: 120px 1fr 60px; align-items: center; padding: 12px 0; border-bottom: 1px solid #f1f5f9; }
.report-item:last-child { border-bottom: none; }
.report-time { color: #475569; font-size: 12px; }
.report-summary { display: flex; align-items: center; gap: 8px; }
.report-type { padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 500; white-space: nowrap; }
.type-normal { background: #d4edda; color: #155724; }
.type-risk { background: #fff3cd; color: #856404; }
.summary-text { color: #1e293b; font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.report-attachments { color: #667eea; font-size: 12px; text-align: right; }

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
