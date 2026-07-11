<template>
  <div class="team-view-panel">
    <div v-if="filteredOrders.length > 0" class="team-order-list">
      <div class="team-overview-row">
        <div class="team-overview-item">
          <span class="team-overview-label">工单总数</span>
          <strong class="team-overview-value">{{ teamOverview.total }}</strong>
        </div>
        <div class="team-overview-item team-overview-progress">
          <span class="team-overview-label">总体进度</span>
          <el-progress
            :percentage="teamOverview.progressPercent"
            :stroke-width="10"
            :show-text="false"
            status="success"
          />
          <strong class="team-overview-value">{{ teamOverview.progressPercent }}%</strong>
        </div>
        <div class="team-overview-item team-overview-status">
          <span class="team-overview-label">状态分布</span>
          <div class="team-overview-status-tags">
            <el-tag
              v-for="item in teamOverview.statusCounts"
              :key="item.status"
              size="small"
              effect="light"
              class="team-overview-status-tag"
              :style="item.tagStyle"
            >
              {{ item.label }}: {{ item.count }}
            </el-tag>
          </div>
        </div>
      </div>
      <div
        v-for="(row, index) in filteredOrders"
        :key="row.work_order_id || row.order_number || index"
        class="team-order-item"
      >
        <div class="team-order-title">
          <span class="team-order-name">{{ row.process_name || '未命名工单' }}</span>
          <el-tag size="small" effect="light" class="team-order-status-tag" :style="row._progress.tagStyle">
            {{ getStatusLabel(row.status || row.work_order_status) }}
          </el-tag>
        </div>
        <div class="team-order-progress-wrap" :class="{ cancelled: row._progress.isCancelled }">
          <div
            class="team-order-progress-line"
            role="progressbar"
            :aria-valuemin="0"
            :aria-valuemax="6"
            :aria-valuenow="row._progress.completedSteps"
          >
            <span
              v-for="segment in row._progress.segments"
              :key="segment.key"
              class="progress-segment"
              :class="segment.state"
              :style="{ backgroundColor: segment.color }"
            />
          </div>
          <span class="team-order-progress-text">{{ row._progress.progressText }}</span>
        </div>
        <div class="team-order-meta">
          <div class="worker-group-list" v-if="parseWorkersByRole(row.workers).length">
            <div class="worker-group-item" v-for="group in parseWorkersByRole(row.workers)" :key="group.role">
              <span class="worker-role">{{ group.role }}</span>
              <div class="worker-chip-wrap">
                <span class="worker-chip" v-for="name in group.names" :key="`${group.role}-${name}`">{{ name }}</span>
              </div>
            </div>
          </div>
          <span v-else class="worker-empty">班组: 未分配</span>
          <span v-if="row.priority">优先级: {{ row.priority }}</span>
        </div>
      </div>
    </div>
    <el-empty v-else description="暂无班组状态数据" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import {
  buildOrderProgressModel,
  getStatusLabel,
  parseWorkersByRole,
  FLOW_PROGRESS_STEPS
} from '../utils'

const props = defineProps({
  orders: {
    type: Array,
    required: true
  },
  selectedEquipmentId: {
    type: String,
    default: ''
  },
  selectedProcessId: {
    type: String,
    default: ''
  }
})

const ordersWithProgress = computed(() => {
  return props.orders.map(row => {
    const currentStatus = row.status || row.work_order_status
    return {
      ...row,
      _progress: buildOrderProgressModel(currentStatus)
    }
  })
})

const filteredOrders = computed(() => {
  return ordersWithProgress.value.filter(row => {
    const matchEquipment = !props.selectedEquipmentId || String(row.equipment_id) === props.selectedEquipmentId
    const matchProcess = !props.selectedProcessId || String(row.process_id) === props.selectedProcessId
    return matchEquipment && matchProcess
  })
})

const teamOverview = computed(() => {
  const rows = filteredOrders.value
  const total = rows.length
  if (!total) {
    return {
      total: 0,
      progressPercent: 0,
      statusCounts: []
    }
  }

  const totalSteps = FLOW_PROGRESS_STEPS.length
  const completedStepSum = rows.reduce((sum, row) => sum + (row._progress?.completedSteps || 0), 0)
  const progressPercent = Math.round((completedStepSum / (total * totalSteps)) * 100)

  const statusMap = new Map()
  rows.forEach(row => {
    const status = typeof row.status === 'string' ? row.status : (typeof row.work_order_status === 'string' ? row.work_order_status : '')
    const previous = statusMap.get(status)
    statusMap.set(status, {
      status,
      count: previous ? previous.count + 1 : 1
    })
  })

  const getStatusStyle = (status) => {
    const styleMap = {
      released: { backgroundColor: '#f1f5f9', color: '#64748b', borderColor: '#e2e8f0' },
      apply_for_start: { backgroundColor: '#dbeafe', color: '#2563eb', borderColor: '#bfdbfe' },
      eng_approved: { backgroundColor: '#dbeafe', color: '#2563eb', borderColor: '#bfdbfe' },
      construction_confirmed: { backgroundColor: '#ecfeff', color: '#0891b2', borderColor: '#cffafe' },
      team_received: { backgroundColor: '#ecfeff', color: '#0891b2', borderColor: '#cffafe' },
      construction_signed: { backgroundColor: '#f5f3ff', color: '#7c3aed', borderColor: '#e9d5ff' },
      process_closed: { backgroundColor: '#dcfce7', color: '#16a34a', borderColor: '#bbf7d0' },
      equipment_closed: { backgroundColor: '#dcfce7', color: '#15803d', borderColor: '#bbf7d0' },
      cancelled: { backgroundColor: '#fee2e2', color: '#dc2626', borderColor: '#fecaca' }
    }
    return styleMap[status] || { backgroundColor: '#f1f5f9', color: '#64748b', borderColor: '#e2e8f0' }
  }

  const statusCounts = Array.from(statusMap.values())
    .map(item => {
      const label = getStatusLabel(item.status) || item.status || '未知'
      const style = getStatusStyle(item.status)
      return {
        ...item,
        label,
        tagStyle: {
          backgroundColor: style.backgroundColor,
          color: style.color,
          borderColor: style.borderColor
        }
      }
    })
    .sort((a, b) => b.count - a.count)

  return {
    total,
    progressPercent,
    statusCounts
  }
})
</script>

<style scoped>
.team-view-panel {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 4px 4px 0;
}

.team-order-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.team-overview-row {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid #dbeafe;
  background: linear-gradient(135deg, #f8fbff 0%, #eff6ff 100%);
  overflow-x: auto;
  white-space: nowrap;
}

.team-overview-item {
  display: inline-flex;
  align-items: center;
  flex: 0 0 auto;
  gap: 8px;
  min-width: 0;
  color: #334155;
  font-size: 12px;
}

.team-overview-label {
  color: #64748b;
}

.team-overview-value {
  color: #0f172a;
  font-size: 14px;
}

.team-overview-progress {
  flex: 0 0 230px;
  justify-content: flex-start;
}

.team-overview-progress :deep(.el-progress) {
  width: 130px;
  min-width: 130px;
}

.team-overview-status {
  flex: 1 0 auto;
  min-width: 280px;
}

.team-overview-status-tags {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.team-overview-status-tag {
  margin: 0;
}

.team-order-item {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 0;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  position: relative;
}

.team-order-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  border-radius: 12px 0 0 12px;
  background: linear-gradient(180deg, #3b82f6, #6366f1);
  transition: width 0.2s ease;
}

.team-order-item:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(59, 130, 246, 0.1);
  border-color: #93c5fd;
}

.team-order-item:hover::before {
  width: 5px;
}

.team-order-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 14px 16px 10px 20px;
}

.team-order-name {
  color: #0f172a;
  font-weight: 700;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.team-order-status-tag {
  font-weight: 600;
  border-width: 1px;
}

.team-order-progress-wrap {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 0 16px 10px 20px;
}

.team-order-progress-line {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 6px;
}

.progress-segment {
  height: 8px;
  border-radius: 999px;
  transition: all 0.2s ease;
}

.progress-segment.is-pending {
  opacity: 0.18;
}

.progress-segment.is-complete {
  opacity: 1;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.7) inset;
}

.progress-segment.is-cancelled {
  opacity: 0.95;
  background-image: repeating-linear-gradient(
    -45deg,
    rgba(255, 255, 255, 0.25),
    rgba(255, 255, 255, 0.25) 4px,
    rgba(255, 255, 255, 0) 4px,
    rgba(255, 255, 255, 0) 8px
  );
}

.team-order-progress-wrap.cancelled .team-order-progress-text {
  color: #b91c1c;
}

.team-order-progress-text {
  font-size: 12px;
  font-weight: 600;
  color: #475569;
  letter-spacing: 0.2px;
}

.team-order-meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px 16px 14px 20px;
  background: #f8fafc;
  border-top: 1px solid #f1f5f9;
  color: #475569;
  font-size: 13px;
}

.worker-group-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.worker-group-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.worker-role {
  min-width: 48px;
  color: #4338ca;
  font-weight: 600;
  line-height: 24px;
  font-size: 12px;
}

.worker-chip-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.worker-chip {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 10px;
  border-radius: 6px;
  background: #ffffff;
  border: 1px solid #c7d2fe;
  color: #4338ca;
  font-size: 12px;
  font-weight: 500;
  transition: all 0.15s ease;
}

.worker-chip:hover {
  background: #eef2ff;
  border-color: #818cf8;
}

.worker-empty {
  color: #94a3b8;
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.2s ease;
}

.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(6px);
}
</style>