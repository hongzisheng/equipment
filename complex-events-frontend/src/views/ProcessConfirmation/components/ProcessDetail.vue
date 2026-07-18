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

      <div v-if="process.attachment_path" class="detail-section">
        <h4>上传图片</h4>
        <div class="image-preview">
          <el-image
            :src="'http://localhost:5000' + process.attachment_path"
            fit="contain"
            :preview-src-list="['http://localhost:5000' + process.attachment_path]"
            class="preview-image"
          />
        </div>
      </div>
      <div v-else class="detail-section">
        <h4>上传图片</h4>
        <div class="no-image">暂无图片</div>
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
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Checked, Close } from '@element-plus/icons-vue'
import ProcessStatusTag from './ProcessStatusTag.vue'
import ProcessTimeline from './ProcessTimeline.vue'
import { formatTime, formatWorkers, getOpinionPlaceholder, TERMINAL_STATUSES, NON_REJECTABLE_STATUSES, TASK_STATUS } from '../utils'

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

.image-preview {
  display: flex;
  justify-content: center;
  background: #fafafa;
  border-radius: 6px;
  padding: 12px;
  border: 1px solid #e4edf2;
}

.preview-image {
  max-width: 100%;
  max-height: 300px;
  object-fit: contain;
  border-radius: 4px;
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