<template>
  <div class="work-report">
    <!-- 头部导航 -->
    <div class="header">
      <div class="header-left">
        <span class="title">工况反馈</span>
      </div>
      <div class="header-right">
        <span class="employee-name">hzs</span>
        <span class="role-badge">员工端</span>
      </div>
    </div>

    <!-- 主要内容区 -->
    <div class="main-content">
      <!-- 内容区 -->
      <div class="content">
        <!-- 提交说明 -->
        <div class="submission-note">
          提交现场工况（可选择上传图片附件）
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
                <span class="value">{{form.nextStatus || '-'}}</span>
              </div>
            </div>
          </div>

          <!-- 任务选择 -->
          <div class="task-select-section">
            <div class="task-select-row">
              <span class="label">工单选择</span>
              <select 
                v-model="form.selectedWorkOrderId" 
                @change="onWorkOrderChange"
                :disabled="loading"
              >
                <option value="">请选择工单</option>
                <option 
                  v-for="workOrder in workOrderOptions" 
                  :key="workOrder.work_order_id" 
                  :value="workOrder.work_order_id"
                >
                  {{ workOrder.work_order_title }} ({{ workOrder.order_number }})
                </option>
              </select>
            </div>
            
            <div class="task-select-row">
              <span class="label">工序选择</span>
              <select 
                v-model="form.selectedProcessId" 
                @change="onProcessChange"
                :disabled="!form.selectedWorkOrderId || loading"
              >
                <option value="">请选择工序</option>
                <option 
                  v-for="process in processOptions" 
                  :key="process.process_id" 
                  :value="process.process_id"
                >
                  {{ process.process_name }} ({{ process.equipment_name }}) - {{ process.task_code || '无编码' }}
                </option>
              </select>
            </div>
          </div>

          <!-- 上报表单标题 -->
          <div class="section-title">上报表单</div>

          <!-- 工况类型选择 -->
          <div class="form-group" v-if="false">
            <span class="label required">工况类型</span>
            <div class="condition-type-selector">
              <label class="type-option" :class="{ active: form.conditionType === 'in_progress' }">
                <input
                  type="radio"
                  v-model="form.conditionType"
                  value="in_progress"
                  name="conditionType"
                />
                <span class="option-content">
                  <span class="option-icon">🔄</span>
                  <span class="option-text">进行中</span>
                </span>
              </label>
              <label class="type-option" :class="{ active: form.conditionType === 'on_hold' }">
                <input
                  type="radio"
                  v-model="form.conditionType"
                  value="on_hold"
                  name="conditionType"
                />
                <span class="option-content">
                  <span class="option-icon">⏸️</span>
                  <span class="option-text">已完成</span>
                </span>
              </label>
            </div>
          </div>

          <!-- 工况描述 -->
          <div class="form-group">
            <span class="label required">工况描述</span>
            <textarea
              v-model="form.conditionDesc"
              placeholder="请描述现场工况、发现问题、临时措施等"
              rows="4"
            ></textarea>
          </div>

          <!-- 附件上传 -->
          <div class="form-group">
            <span class="label">附件上传</span>
            <div class="upload-area" @click="triggerFileInput">
              <div class="upload-content">
                <span class="upload-icon">📎</span>
                <span class="upload-text">将文件拖到此处，或点击上传</span>
                <span class="upload-hint">支持图片格式；可选择上传图片附件</span>
              </div>
              <input
                type="file"
                ref="fileInput"
                @change="handleFileUpload"
                accept=".jpg,.jpeg,.png,.gif,.bmp"
                multiple
                style="display: none;"
              />
            </div>
            <div class="file-list" v-if="uploadedFiles.length > 0">
              <div v-for="(file, index) in uploadedFiles" :key="index" class="file-item">
                <span class="file-name">📄 {{ file.name }}</span>
                <span class="file-size">{{ (file.size / 1024).toFixed(0) }}KB</span>
                <button type="button" @click="removeFile(index)" class="remove-btn">×</button>
              </div>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="form-actions">
            <button type="button" class="btn-save" @click="saveDraft">保存草稿</button>
            <button type="button" class="btn-submit" @click="submitReport" :disabled="submitting">
              {{ submitting ? '提交中...' : '提交工况' }}
            </button>
          </div>
        </div>

        <!-- 最近上报 -->
        <div class="recent-reports">
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
import { useRouter } from 'vue-router'
import request from '@/utils/request'

const router = useRouter()
const showSuccess = ref(false)
const fileInput = ref(null)
const uploadedFiles = ref([])
const workerId = ref(null) 
const submitting = ref(false) // 提交状态
const recentReports = ref([])
// 工单选项数据
const workOrderOptions = ref([])
// 工序选项数据
const processOptions = ref([])
// 加载状态
const loading = ref(false)
const loadingReports = ref(false)

// 表单数据
const form = reactive({
  selectedWorkOrderId: '', // 选中的工单ID
  selectedProcessId: '',   // 选中的工序ID
  equipment: '',
  workOrderNo: '',
  planTime: '',
  currentStatus: '',
  conditionDesc: '',
  conditionType: 'in_progress' // 工况类型，默认进行中
})

// 计算属性：显示选中的工单标题
const workOrderDisplay = computed(() => {
  const workOrder = workOrderOptions.value.find(wo => wo.work_order_id === form.selectedWorkOrderId)
  return workOrder ? workOrder.work_order_title : ''
})

// 计算属性：显示选中的工序名称
const processDisplay = computed(() => {
  const process = processOptions.value.find(p => p.process_id === form.selectedProcessId)
  return process ? process.process_name : ''
})

// 计算属性：完整的任务显示（工单标题 + 工序名称）
const taskDisplay = computed(() => {
  if (workOrderDisplay.value && processDisplay.value) {
    return `${workOrderDisplay.value} - ${processDisplay.value}`
  }
  return workOrderDisplay.value || processDisplay.value || '未选择'
})

// 最近上报 mock 数据
const fetchRecentReports = async () => {
  if (!workerId.value) {
    console.warn('workerId 为空')
    return
  }
  try {
    loadingReports.value = true
    const response = await request.get(`http://localhost:5000/api/worker/${workerId.value}/history`,{
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })
    if (response.success) {
      recentReports.value = response.data.map(item => ({
        id: item.id,
        time: item.created_at,          // 例如 "2026-03-18 10:30:00"
        type: getOperationTypeText(item.operation_type), // 转换为中文显示
        typeClass: getTypeClass(item.operation_type),
        summary: item.description || item.operation_type,
        attachments: item.attachment_path ? 1 : 0        // 简单判断
      }))
    } else {
      console.error('获取历史失败:', response.message)
    }
  } catch (error) {
    console.error('获取历史失败:', error)
  } finally {
    loadingReports.value = false
  }
}

// 操作类型转中文
const getOperationTypeText = (type) => {
  const map = {
    'status_update': '状态变更',
    'upload_photo': '上传附件',
    'approval_confirm': '审批通过',
    'approval_reject': '审批驳回',
    'approval_approved': '审批通过',
    'approval_rejected': '审批驳回'
  }
  return map[type] || type
}

// 操作类型对应样式类
const getTypeClass = (type) => {
  if (type.includes('approval')) return 'type-risk'   // 审批类用红色
  return 'type-normal'  // 其他用绿色
}

// 获取工单和工序数据
const fetchWorkOrders = async () => {
  try {
    loading.value = true
    const response = await request.get(`http://localhost:5000/api/worker-workorders/${workerId.value}`)
    
    if (response.success) {
      // 按工单ID分组并去重
      const workOrderMap = new Map()
      
      response.data.forEach(item => {
        // 创建工单对象（如果不存在）
        if (!workOrderMap.has(item.work_order_id)) {
          workOrderMap.set(item.work_order_id, {
            work_order_id: item.work_order_id,
            work_order_title: item.work_order_title,
            order_number: item.order_number,
            work_order_status: item.work_order_status,
            priority: item.priority,
            work_order_created_at: item.work_order_created_at,
            worker_name: item.worker_name,
            worker_type: item.worker_type,
            processes: []
          })
        }
        
        // 构建完整的工序对象，包含所有必要信息
        const processItem = {
          // 工序基本信息
          process_id: item.process_id,
          process_name: item.process_name,
          equipment_id: item.equipment_id,
          equipment_name: item.equipment_name,
          description: item.description,
          estimated_hours: item.estimated_hours,
          
          // 任务相关信息
          task_id: item.task_id,
          task_code: item.task_code,
          task_status: item.task_status,
          is_milestone: item.is_milestone,
          assignment_status: item.assignment_status,
          
          // 时间信息
          scheduled_start_time: item.scheduled_start_time,
          scheduled_end_time: item.scheduled_end_time,
          actual_start_time: item.actual_start_time,
          actual_end_time: item.actual_end_time,
          
          // 工单信息
          work_order_id: item.work_order_id,
          order_number: item.order_number,
          work_order_title: item.work_order_title,
          work_order_status: item.work_order_status,
          priority: item.priority,
          
          // 工人信息
          worker_name: item.worker_name,
          worker_type: item.worker_type
        }
        
        // 将工序添加到对应的工单中
        workOrderMap.get(item.work_order_id).processes.push(processItem)
      })
      
      // 转换为数组并按工单ID排序
      workOrderOptions.value = Array.from(workOrderMap.values()).sort((a, b) => 
        a.work_order_id - b.work_order_id
      )
      
      // 对每个工单下的工序按计划开始时间排序
      workOrderOptions.value.forEach(workOrder => {
        workOrder.processes.sort((a, b) => {
          // 解析时间字符串，格式为"第1天 08:00"
          const parseTime = (timeStr) => {
            if (!timeStr) return 0
            const [dayPart, timePart] = timeStr.split(' ')
            const day = parseInt(dayPart.replace('第', '').replace('天', ''))
            const [hours, minutes] = timePart.split(':').map(Number)
            return day * 24 * 60 + hours * 60 + minutes
          }
          
          return parseTime(a.scheduled_start_time) - parseTime(b.scheduled_start_time)
        })
      })
      

      // 打印第一个工序的完整信息用于调试
      if (workOrderOptions.value.length > 0 && workOrderOptions.value[0].processes.length > 0) {
        console.log('工序数据示例:', workOrderOptions.value[0].processes[0])
      }
    }
  } catch (error) {
    console.error('获取工单数据失败:', error)
    alert('获取任务数据失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  const isLoggedIn = localStorage.getItem('isLoggedIn')
  if (!isLoggedIn) {
    router.push('/login')
    return
  }
  // 获取用户信息
  const userStr = localStorage.getItem('user')
  if (userStr) {
    const user = JSON.parse(userStr)
    workerId.value = user.worker_id  // 从登录响应中保存的 user 对象
  }
  fetchWorkOrders()
  fetchRecentReports()
})

// 工单选择变化时清空工序选择并更新工序选项
const onWorkOrderChange = () => {
  // 清空工序选择
  form.selectedProcessId = ''
  form.equipment = ''
  form.workOrderNo = ''
  form.planTime = ''
  form.currentStatus = ''
  
  // 更新工序选项
  const selectedWorkOrder = workOrderOptions.value.find(wo => wo.work_order_id === form.selectedWorkOrderId)
  if (selectedWorkOrder) {
    processOptions.value = selectedWorkOrder.processes
  } else {
    processOptions.value = []
  }
}
const TASK_STATUS = {
  RELEASED: 'released',             // 工单发布 (初始状态)
  APPLY_START: 'apply_for_start',   // 申请开工
  ENG_APPROVED: 'eng_approved',     // 工程师确认
  CONSTRUCTION_CONFIRMED: 'construction_confirmed', // 施工确认
  TEAM_RECEIVED: 'team_received',   // 班组接收
  CONSTRUCTION_SIGNED: 'construction_signed', // 施工回签 (工人主要操作点)
  PROCESS_CLOSED: 'process_closed', // 工艺关闭
  EQUIPMENT_CLOSED: 'equipment_closed', // 设备关闭
  CANCELLED: 'cancelled'            // 取消
}
const STATUS_LABEL_MAP = {
  [TASK_STATUS.RELEASED]: '待开始',
  [TASK_STATUS.APPLY_START]: '申请开工',
  [TASK_STATUS.ENG_APPROVED]: '工程师确认',
  [TASK_STATUS.CONSTRUCTION_CONFIRMED]: '施工确认',
  [TASK_STATUS.TEAM_RECEIVED]: '班组受理',
  [TASK_STATUS.CONSTRUCTION_SIGNED]: '施工回签',
  [TASK_STATUS.PROCESS_CLOSED]: '工艺存储关闭',
  [TASK_STATUS.EQUIPMENT_CLOSED]: '设备部关闭',
  [TASK_STATUS.CANCELLED]: '取消'
}
// 定义正常流程的状态顺序（不包括 CANCELLED，因为它是一个终止态，可从任意状态跳转）
const STATUS_SEQUENCE = [
  TASK_STATUS.RELEASED,
  TASK_STATUS.APPLY_START,
  TASK_STATUS.ENG_APPROVED,
  TASK_STATUS.CONSTRUCTION_CONFIRMED,
  TASK_STATUS.TEAM_RECEIVED,
  TASK_STATUS.CONSTRUCTION_SIGNED,
  TASK_STATUS.PROCESS_CLOSED,
  TASK_STATUS.EQUIPMENT_CLOSED
];

/**
 * 获取下一个状态（仅限正常流程）
 * @param {string} currentStatus - 当前状态值（如 'released'）
 * @returns {string | null} 下一个状态，如果已是最后一个则返回 null
 */
function getNextStatus(currentStatus) {
  const index = STATUS_SEQUENCE.indexOf(currentStatus);
  if (index === -1 || index === STATUS_SEQUENCE.length - 1) {
    return null; // 无效状态 或 已到最后一步
  }
  return STATUS_SEQUENCE[index + 1];
}
// 工序选择变化时更新表单信息
const onProcessChange = () => {
  const selectedProcess = processOptions.value.find(p => p.process_id === form.selectedProcessId)
  if (selectedProcess) {
    // 使用工序中的完整信息更新表单
    form.equipment = selectedProcess.equipment_name || '—'
    form.workOrderNo = selectedProcess.order_number || '—'
    
    // 格式化计划时间
    if (selectedProcess.scheduled_start_time && selectedProcess.scheduled_end_time) {
      form.planTime = `${selectedProcess.scheduled_start_time} ~ ${selectedProcess.scheduled_end_time}`
    } else {
      form.planTime = '—'
    }
    form.currentStatus = STATUS_LABEL_MAP[selectedProcess.task_status] || selectedProcess.task_status || '—'
    form.nextStatus = STATUS_LABEL_MAP[getNextStatus(selectedProcess.task_status)]
  } else {
    // 清空表单信息
    form.equipment = ''
    form.workOrderNo = ''
    form.planTime = ''
    form.currentStatus = ''
  }
}

// 附件上传逻辑
const triggerFileInput = () => {
  fileInput.value.click()
}

const handleFileUpload = (event) => {
  const files = Array.from(event.target.files)
  files.forEach(file => {
    // 检查文件类型
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/bmp']
    if (!allowedTypes.includes(file.type)) {
      alert(`文件 ${file.name} 格式不支持，请上传图片文件`)
      return
    }
    
    // 检查文件大小 (10MB)
    if (file.size <= 10 * 1024 * 1024) {
      uploadedFiles.value.push(file)
    } else {
      alert(`文件 ${file.name} 超过 10MB 限制`)
    }
  })
  // 清空 input 以便重新选择相同文件
  event.target.value = ''
}

const removeFile = (index) => {
  uploadedFiles.value.splice(index, 1)
}

// 保存草稿
const saveDraft = () => {
  const draft = {
    form: { ...form },
    files: uploadedFiles.value.map(f => f.name)
  }
  localStorage.setItem('workConditionDraft', JSON.stringify(draft))
  alert('草稿已保存')
}

// 提交校验
const validateForm = () => {
  if (!form.selectedWorkOrderId) {
    alert('请选择工单')
    return false
  }
  if (!form.selectedProcessId) {
    alert('请选择工序')
    return false
  }
  if (!form.conditionType) {
    alert('请选择工况类型')
    return false
  }
  if (!form.conditionDesc || form.conditionDesc.trim() === '') {
    alert('请填写工况描述')
    return false
  }
  return true
}

// 提交工况
const submitReport = async () => {
  if (!validateForm()) return

  try {
    submitting.value = true
    
    // 准备表单数据
    const formData = new FormData()
    // 使用用户选择的工况类型
    // formData.append('status', form.conditionType)
    formData.append('description', form.conditionDesc)
    
    // 添加图片文件（如果有）
    if (uploadedFiles.value.length > 0) {
      uploadedFiles.value.forEach(file => {
        formData.append('photo', file)
      })
    }
    console.log('提交数据:', formData)
    // 获取选中的工序信息
    const selectedProcess = processOptions.value.find(p => p.process_id === form.selectedProcessId)
    
    // 调用API提交工况
    const response = await request.put(
      `http://localhost:5000/api/work-order-tasks/${selectedProcess.task_id}/update-status`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      }
    )
    
    if (response.success) {
      console.log('工况提交成功:', response)
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

// 重置表单
const resetForm = (keepTask = true) => {
  if (!keepTask) {
    form.selectedWorkOrderId = ''
    form.selectedProcessId = ''
    form.equipment = ''
    form.workOrderNo = ''
    form.planTime = ''
    form.currentStatus = ''
    form.nextStatus = ''
    processOptions.value = [] // 清空工序选项
  }
  form.conditionDesc = ''
  form.conditionType = 'in_progress' // 重置为默认值
  uploadedFiles.value = []
  if (fileInput.value) fileInput.value.value = ''
}

// 成功后继续上报
const resetAll = () => {
  showSuccess.value = false
  resetForm(false) // 不保持任务选择
  // 重新获取数据
  fetchWorkOrders()
}
</script>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.work-report {
  min-height: 100vh;
  background-color: #f5f7fa;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  color: #1e293b;
  font-size: 13px;
}

/* 头部样式 */
.header {
  background: white;
  padding: 12px 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e9ecef;
  box-shadow: 0 2px 4px rgba(0,0,0,0.02);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title {
  font-size: 16px;
  font-weight: 500;
  color: #1e293b;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.employee-name {
  font-size: 13px;
  color: #1e293b;
}

.role-badge {
  font-size: 12px;
  padding: 4px 8px;
  background: #e9ecef;
  border-radius: 4px;
  color: #4a5568;
}

/* 主要内容区 */
.main-content {
  max-width: 1300px;
  margin: 20px auto;
  padding: 0 24px;
}

/* 提交说明 */
.submission-note {
  background: #fff3e0;
  color: #e67e22;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 13px;
  margin-bottom: 16px;
}

/* 表单卡片 */
.form-card {
  background: white;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  margin-bottom: 20px;
}

/* 任务信息 */
.task-info {
  background: #f8fafc;
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 16px;
}

.info-row {
  display: flex;
  gap: 40px;
  margin-bottom: 12px;
}

.info-row:last-child {
  margin-bottom: 0;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-item .label {
  color: #64748b;
  font-size: 12px;
}

.info-item .value {
  color: #1e293b;
  font-size: 13px;
  font-weight: 500;
}

/* 任务选择区域 */
.task-select-section {
  margin-bottom: 24px;
  padding: 16px 0;
  border-bottom: 1px solid #e9ecef;
}

.task-select-row {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
}

.task-select-row:last-child {
  margin-bottom: 0;
}

.task-select-row .label {
  color: #1e293b;
  font-size: 13px;
  font-weight: 500;
  min-width: 80px;
}

.task-select-row select {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #e9ecef;
  border-radius: 4px;
  font-size: 13px;
  color: #1e293b;
  background: white;
  max-width: 400px;
}

.task-select-row select:disabled {
  background-color: #f5f5f5;
  color: #999;
  cursor: not-allowed;
}

.task-select-row select:focus {
  outline: none;
  border-color: #667eea;
}

/* 章节标题 */
.section-title {
  font-size: 15px;
  font-weight: 500;
  color: #1e293b;
  margin-bottom: 16px;
  padding-left: 8px;
  border-left: 3px solid #667eea;
}

/* 表单组 */
.form-group {
  margin-bottom: 20px;
}

.form-row {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.form-row .form-group {
  flex: 1;
  margin-bottom: 0;
}

.form-group .label {
  display: block;
  margin-bottom: 6px;
  color: #1e293b;
  font-size: 13px;
  font-weight: 500;
}

.form-group .label.required::after {
  content: '*';
  color: #e53e3e;
  margin-left: 4px;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #e9ecef;
  border-radius: 4px;
  font-size: 13px;
  color: #1e293b;
  background: white;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
}

/* 工况类型标签 */
.type-tags {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.tag {
  padding: 6px 16px;
  background: #f8fafc;
  border: 1px solid #e9ecef;
  border-radius: 20px;
  font-size: 13px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
}

.tag:hover {
  border-color: #667eea;
  color: #667eea;
}

.tag.active {
  background: #667eea;
  border-color: #667eea;
  color: white;
}

/* 工况类型选择器 */
.condition-type-selector {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.type-option {
  position: relative;
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  background: white;
}

.type-option:hover {
  border-color: #667eea;
  background: #f8fafc;
}

.type-option.active {
  border-color: #667eea;
  background: #f0f5ff;
  box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
}

.type-option input[type="radio"] {
  position: absolute;
  opacity: 0;
  cursor: pointer;
}

.option-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.option-icon {
  font-size: 16px;
}

.option-text {
  font-size: 13px;
  font-weight: 500;
  color: #1e293b;
}

.type-option.active .option-text {
  color: #667eea;
}

/* 复选框组 */
.checkbox-group {
  display: flex;
  align-items: flex-end;
}

.checkbox-group label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #1e293b;
  cursor: pointer;
  padding: 8px 0;
}

.checkbox-group input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

/* 上传区域 */
.upload-area {
  border: 1px dashed #cbd5e0;
  border-radius: 6px;
  padding: 24px;
  background: #f8fafc;
  cursor: pointer;
  transition: all 0.2s;
}

.upload-area:hover {
  border-color: #667eea;
  background: #f0f5ff;
}

.upload-content {
  text-align: center;
}

.upload-icon {
  font-size: 20px;
  color: #94a3b8;
  margin-right: 8px;
}

.upload-text {
  font-size: 13px;
  color: #1e293b;
}

.upload-hint {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: #94a3b8;
}

/* 文件列表 */
.file-list {
  margin-top: 12px;
}

.file-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: #f8fafc;
  border: 1px solid #e9ecef;
  border-radius: 4px;
  margin-bottom: 6px;
}

.file-item:last-child {
  margin-bottom: 0;
}

.file-name {
  flex: 1;
  font-size: 12px;
  color: #1e293b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-size {
  font-size: 11px;
  color: #94a3b8;
  margin: 0 12px;
}

.remove-btn {
  background: none;
  border: none;
  color: #94a3b8;
  font-size: 16px;
  cursor: pointer;
  padding: 0 4px;
}

.remove-btn:hover {
  color: #e53e3e;
}

/* 操作按钮 */
.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 24px;
}

.btn-save,
.btn-submit {
  padding: 8px 24px;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}

.btn-save {
  background: #f1f5f9;
  color: #475569;
}

.btn-save:hover {
  background: #e2e8f0;
}

.btn-submit {
  background: #667eea;
  color: white;
}

.btn-submit:hover {
  background: #5a67d8;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(102,126,234,0.2);
}

/* 最近上报 */
.recent-reports {
  background: white;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.reports-header {
  display: grid;
  grid-template-columns: 120px 1fr 60px;
  padding: 12px 0;
  border-bottom: 1px solid #e9ecef;
  color: #94a3b8;
  font-size: 12px;
}

.reports-list {
  margin-top: 8px;
}

.report-item {
  display: grid;
  grid-template-columns: 120px 1fr 60px;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f1f5f9;
}

.report-item:last-child {
  border-bottom: none;
}

.report-time {
  color: #475569;
  font-size: 12px;
}

.report-summary {
  display: flex;
  align-items: center;
  gap: 8px;
}

.report-type {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
  white-space: nowrap;
}

.type-normal {
  background: #d4edda;
  color: #155724;
}

.type-risk {
  background: #fff3cd;
  color: #856404;
}

.summary-text {
  color: #1e293b;
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.report-attachments {
  color: #667eea;
  font-size: 12px;
  text-align: right;
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  padding: 32px;
  width: 300px;
  text-align: center;
  box-shadow: 0 20px 40px rgba(0,0,0,0.2);
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    transform: translateY(-20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.modal-icon {
  width: 48px;
  height: 48px;
  background: #10b981;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  margin: 0 auto 16px;
}

.modal-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 8px;
}

.modal-text {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 20px;
}

.modal-btn {
  background: #667eea;
  color: white;
  border: none;
  padding: 8px 32px;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.modal-btn:hover {
  background: #5a67d8;
}

/* 响应式 */
@media (max-width: 768px) {
  .main-content {
    padding: 0 16px;
  }
  
  .info-row {
    flex-direction: column;
    gap: 8px;
  }
  
  .form-row {
    flex-direction: column;
    gap: 16px;
  }
  
  .task-select select {
    max-width: 100%;
  }
  
  .reports-header,
  .report-item {
    grid-template-columns: 1fr;
    gap: 8px;
  }
  
  .report-attachments {
    text-align: left;
  }
}
</style>