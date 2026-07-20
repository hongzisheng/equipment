<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="$emit('close')"
    :title="`流程详情 - ${process?.process_name || ''}`"
    width="600px"
    destroy-on-close
    class="process-detail-dialog"
  >
    <div v-if="process" class="process-detail">
      <div class="detail-section">
        <h4>设备信息</h4>
        <div class="info-grid">
          <div class="info-item">
            <span class="label">设备名称：</span>
            <span class="value">{{ process.equipment_name }}</span>
          </div>
          <div class="info-item">
            <span class="label">设备种类：</span>
            <span class="value">{{ process.equipment_category }}</span>
          </div>
          <div class="info-item">
            <span class="label">设备类型：</span>
            <span class="value">{{ process.equipment_type_name }}</span>
          </div>
        </div>
      </div>

      <div class="detail-section">
        <h4>工序信息</h4>
        <div class="info-grid">
          <div class="info-item">
            <span class="label">工序名称：</span>
            <span class="value">{{ process.process_name }}</span>
          </div>
          <div class="info-item">
            <span class="label">工序状态：</span>
            <ProcessStatusTag :status="process.status" />
          </div>
          <div class="info-item">
            <span class="label">责任人：</span>
            <span class="value">{{ formatWorkers(process.workers) }}</span>
          </div>
          <div class="info-item">
            <span class="label">预计时长：</span>
            <span class="value">{{ process.estimated_hours || '--' }}h</span>
          </div>
          <div class="info-item">
            <span class="label">开始时间：</span>
            <span class="value">{{ formatTime(process.scheduled_start_time) }}</span>
          </div>
          <div class="info-item">
            <span class="label">结束时间：</span>
            <span class="value">{{ formatTime(process.scheduled_end_time) }}</span>
          </div>
        </div>
      </div>

      <div v-if="process.description" class="detail-section">
        <h4>工序描述</h4>
        <div class="description">{{ process.description }}</div>
      </div>

      <div class="detail-section">
        <h4>现场图片</h4>
        <!-- 加载中 -->
        <div v-if="imagesLoading" class="images-loading">
          <el-icon class="is-loading"><Loading /></el-icon>
          加载中...
        </div>
        <!-- 图片画廊 -->
        <div v-else-if="workerImages.length > 0" class="images-gallery">
          <div v-for="(img, idx) in workerImages" :key="idx" class="image-card">
            <el-image
              :src="img.url"
              fit="cover"
              :preview-src-list="previewSrcList"
              :initial-index="idx"
              class="gallery-image"
            />
            <div class="image-info">
              <span class="image-time">{{ img.created_at }}</span>
              <span v-if="img.description" class="image-desc">{{ img.description }}</span>
            </div>
          </div>
        </div>
        <!-- 空状态 -->
        <div v-else class="images-empty">暂无工人上传图片</div>
      </div>

      <!-- 操作日志 -->
      <div class="detail-section">
        <h4>操作日志</h4>
        <div v-if="logsLoading" class="log-loading">加载中...</div>
        <div v-else-if="operationLogs.length === 0" class="log-empty">暂无操作记录</div>
        <div v-else class="log-list">
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
            <div v-if="log.approval_comments" class="log-comment">{{ log.approval_comments }}</div>
            <div v-if="log.description" class="log-comment">{{ log.description }}</div>
          </div>
        </div>
      </div>

      <div v-if="process.material_requirements && Object.keys(process.material_requirements).length > 0" class="detail-section">
        <h4>物料需求</h4>
        <div class="info-grid">
          <div v-for="(value, key) in process.material_requirements" :key="key" class="info-item">
            <span class="label">{{ key }}：</span>
            <span class="value">{{ value.quantity }} {{ value.unit }}</span>
          </div>
        </div>
      </div>

      <div v-if="process.tools_requirements && Object.keys(process.tools_requirements).length > 0" class="detail-section">
        <h4>工具需求</h4>
        <div class="info-grid">
          <div v-for="(value, key) in process.tools_requirements" :key="key" class="info-item">
            <span class="label">{{ key }}：</span>
            <span class="value">{{ value.quantity }} {{ value.unit }}</span>
          </div>
        </div>
      </div>

      <div v-if="process.status === 'rejected' && process.approval_comments" class="detail-section reject">
        <h4>驳回原因</h4>
        <div class="reject-reason">{{ process.approval_comments }}</div>
      </div>

      <div v-if="process.status === 'completed' && process.approval_comments" class="detail-section">
        <h4>完成意见</h4>
        <div class="comment">{{ process.approval_comments }}</div>
      </div>

      <div class="detail-section">
        <h4>工序流程</h4>
        <ProcessTimeline
          :processes="allProcesses"
          :equipment-id="process.equipment_id"
          :current-process-id="process.id"
          @view-node="$emit('view-node', $event)"
        />
      </div>

      <div v-if="canConfirm || canReject" class="detail-section opinion">
        <h4>审核意见</h4>
        <el-input
          v-model="opinionText"
          type="textarea"
          :rows="3"
          :placeholder="getOpinionPlaceholder(process.status)"
          maxlength="200"
          show-word-limit
        />
      </div>
    </div>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="$emit('close')" size="small">关闭</el-button>
        <el-button
          v-if="canReject"
          type="danger"
          size="small"
          :loading="rejectLoading"
          @click="handleReject"
        >
          <el-icon><Close /></el-icon> 驳回
        </el-button>
        <el-button
          v-if="canConfirm"
          type="primary"
          size="small"
          :loading="confirmLoading"
          @click="handleConfirm"
        >
          <el-icon><Checked /></el-icon> 确认
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Checked, Close, Loading } from '@element-plus/icons-vue'
import ProcessStatusTag from './ProcessStatusTag.vue'
import ProcessTimeline from './ProcessTimeline.vue'
import { formatTime, formatWorkers, getOpinionPlaceholder, TERMINAL_STATUSES, NON_REJECTABLE_STATUSES, TASK_STATUS } from '../utils'
import request from '@/utils/request'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  process: {
    type: Object,
    default: null
  },
  allProcesses: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['close', 'confirm', 'reject', 'view-node'])

const opinionText = ref('')
const confirmLoading = ref(false)
const rejectLoading = ref(false)

// 操作日志
const operationLogs = ref([])
const logsLoading = ref(false)

// 工人上传图片
const workerImages = ref([])
const imagesLoading = ref(false)
const previewSrcList = computed(() => workerImages.value.map(img => img.url))

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

async function fetchOperationLogs() {
  if (!props.process?.id) return
  logsLoading.value = true
  try {
    const res = await request.get(`/api/work-order-tasks/${props.process.id}/logs`)
    operationLogs.value = res.success ? res.data : []
  } catch (e) {
    operationLogs.value = []
  } finally {
    logsLoading.value = false
  }
}

async function fetchWorkerImages() {
  if (!props.process?.id) return
  imagesLoading.value = true
  try {
    const res = await request.get(`/api/work-order-tasks/${props.process.id}/worker-images`)
    workerImages.value = res.success ? res.data : []
  } catch (e) {
    workerImages.value = []
  } finally {
    imagesLoading.value = false
  }
}

// 弹窗打开时自动加载日志和工人图片
watch(() => props.visible, (visible) => {
  if (visible && props.process?.id) {
    fetchOperationLogs()
    fetchWorkerImages()
  }
})

// 管理员不可操作的状态：终态 + 待开始（工人动作） + 等待施工回签（工人动作）
const ADMIN_NON_OPERABLE = new Set([
  ...TERMINAL_STATUSES,
  TASK_STATUS.RELEASED,
  TASK_STATUS.PENDING_SIGN,
])

// 确认：非管理员不可操作状态即可确认
const canConfirm = computed(() => {
  if (!props.process) return false
  return !ADMIN_NON_OPERABLE.has(props.process.status)
})

// 驳回：非终态且非待开始且非等待施工回签即可驳回
const canReject = computed(() => {
  if (!props.process) return false
  return !NON_REJECTABLE_STATUSES.has(props.process.status)
    && props.process.status !== TASK_STATUS.PENDING_SIGN
})

function handleConfirm() {
  if (!props.process) return

  ElMessageBox.confirm(
    `确认后将进入下一状态。确认完成「${props.process.process_name}」？`,
    `确认 - ${props.process.process_name}`,
    {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'info',
      center: true,
      size: 'small'
    }
  ).then(() => {
    confirmLoading.value = true
    setTimeout(() => {
      ElMessage.success(`"${props.process.process_name}" 已确认`)
      emit('confirm', { process: props.process, comment: opinionText.value })
      confirmLoading.value = false
      opinionText.value = ''
    }, 500)
  }).catch(() => {
    confirmLoading.value = false
  })
}

function handleReject() {
  if (!props.process) return

  ElMessageBox.prompt('请输入驳回原因', `驳回 - ${props.process.process_name}`, {
    confirmButtonText: '确定驳回',
    cancelButtonText: '取消',
    type: 'warning',
    inputPlaceholder: '请填写驳回原因（必填）',
    inputType: 'textarea',
    inputPattern: /\S+/,
    inputErrorMessage: '驳回原因不能为空'
  }).then(({ value }) => {
    rejectLoading.value = true
    setTimeout(() => {
      ElMessage.warning(`已驳回 "${props.process.process_name}"，原因：${value}`)
      emit('reject', { process: props.process, reason: value })
      rejectLoading.value = false
      opinionText.value = ''
    }, 500)
  }).catch(() => {
    rejectLoading.value = false
  })
}

</script>

<style scoped>
.process-detail-dialog :deep(.el-dialog__body) {
  padding: 20px;
  max-height: 60vh;
  overflow-y: auto;
}

.process-detail {
  font-size: 13px;
}

.detail-section {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px dashed #e4edf2;
}

.detail-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.detail-section h4 {
  margin: 0 0 12px;
  font-size: 14px;
  font-weight: 600;
  color: #1f4e6a;
  display: flex;
  align-items: center;
}

.detail-section h4::before {
  content: '';
  display: inline-block;
  width: 3px;
  height: 14px;
  background: #409eff;
  margin-right: 8px;
  border-radius: 2px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.info-item {
  display: flex;
  align-items: baseline;
}

.info-item .label {
  color: #6b859c;
  font-size: 12px;
  width: 70px;
  flex-shrink: 0;
}

.info-item .value {
  color: #1e3747;
  font-weight: 500;
  font-size: 13px;
}

.description,
.comment,
.reject-reason {
  background: #f8fbfd;
  padding: 12px;
  border-radius: 6px;
  line-height: 1.6;
  color: #2c4a63;
  font-size: 13px;
}

.reject h4::before {
  background: #f56c6c;
}

.reject-reason {
  background: #fff5f5;
  color: #c96b6b;
  border-left: 3px solid #f56c6c;
}

/* 工人上传图片画廊 */
.images-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  background: #f8fbfd;
  border-radius: 6px;
  border: 1px dashed #d9e2e9;
  color: #409eff;
  font-size: 13px;
}

.images-gallery {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.image-card {
  border: 1px solid #e4edf2;
  border-radius: 8px;
  overflow: hidden;
  background: #fff;
  transition: box-shadow 0.2s;
}

.image-card:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.gallery-image {
  width: 100%;
  height: 140px;
  object-fit: cover;
  cursor: pointer;
}

.image-info {
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.image-time {
  font-size: 11px;
  color: #99aab9;
}

.image-desc {
  font-size: 12px;
  color: #4a5e71;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.images-empty {
  text-align: center;
  padding: 24px;
  background: #f8fbfd;
  border-radius: 6px;
  border: 1px dashed #d9e2e9;
  color: #99aab9;
  font-size: 13px;
}

/* 操作日志 */
.log-loading {
  text-align: center;
  color: #99aab9;
  padding: 16px;
  font-size: 13px;
}

.log-empty {
  text-align: center;
  color: #99aab9;
  padding: 16px;
  background: #f8fbfd;
  border-radius: 6px;
  border: 1px dashed #d9e2e9;
  font-size: 13px;
}

.log-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
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

.no-image {
  background: #f8fbfd;
  padding: 20px;
  text-align: center;
  color: #99aab9;
  border-radius: 6px;
  border: 1px dashed #d9e2e9;
}

.opinion {
  margin-top: 16px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>