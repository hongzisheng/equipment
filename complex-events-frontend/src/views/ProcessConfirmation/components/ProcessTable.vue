<template>
  <div class="table-container" ref="containerRef">
    <el-table
      :data="processes"
      border
      size="small"
      style="width: 100%"
      :height="tableHeight"
      @row-click="handleRowClick($event, row)"
      :row-class-name="getRowClassName"
      :cell-style="getCellStyle"
      highlight-current-row
    >
      <el-table-column prop="id" label="序号" width="55" fixed="left" align="center" sortable />

      <el-table-column prop="equipment_name" label="设备名称" min-width="120" show-overflow-tooltip fixed="left">
        <template #default="{ row }">
          <div class="equipment-info">
            <el-icon><Monitor /></el-icon>
            <span>{{ row.equipment_name || '--' }}</span>
          </div>
        </template>
      </el-table-column>

      <el-table-column prop="equipment_category" label="设备种类" min-width="100" show-overflow-tooltip align="center" />

      <el-table-column prop="equipment_type_name" label="设备类型" min-width="100" show-overflow-tooltip align="center" />

      <el-table-column prop="process_name" label="工序名称" min-width="120" show-overflow-tooltip>
        <template #default="{ row }">
          <div class="process-name">
            <span>{{ row.process_name }}</span>
            <el-tag v-if="row.is_milestone" size="small" type="warning" class="milestone-tag">里程碑</el-tag>
          </div>
        </template>
      </el-table-column>

      <el-table-column prop="status" label="状态" width="90" align="center">
        <template #default="{ row }">
          <ProcessStatusTag :status="row.status" class="status-tag" />
        </template>
      </el-table-column>

      <el-table-column prop="workers" label="责任人" min-width="120" show-overflow-tooltip>
        <template #default="{ row }">
          {{ formatWorkers(row.workers) }}
        </template>
      </el-table-column>

      <el-table-column prop="estimated_hours" label="预计时长" width="80" align="center">
        <template #default="{ row }">
          {{ row.estimated_hours || '--' }}天
        </template>
      </el-table-column>

      <el-table-column prop="scheduled_start_time" label="开始时间" min-width="140" align="center">
        <template #default="{ row }">
          {{ formatTime(row.scheduled_start_time) }}
        </template>
      </el-table-column>

      <el-table-column prop="scheduled_end_time" label="结束时间" min-width="140" align="center">
        <template #default="{ row }">
          {{ formatTime(row.scheduled_end_time) }}
        </template>
      </el-table-column>

      <el-table-column label="操作" width="160" fixed="right" align="center">
        <template #default="{ row }">
          <div class="action-buttons">
            <el-button
              type="primary"
              size="small"
              plain
              @click.stop="$emit('view-detail', row)"
            >
              <el-icon><View /></el-icon> 详情
            </el-button>
            <el-button
              v-if="row.status !== 'completed' && row.status !== 'cancelled'"
              type="warning"
              size="small"
              plain
              @click.stop="$emit('cancel', row)"
            >
              <el-icon><CircleClose /></el-icon> 取消
            </el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { Monitor, View, CircleClose } from '@element-plus/icons-vue'
import ProcessStatusTag from './ProcessStatusTag.vue'
import { formatTime, formatWorkers, getRowClassName, getCellStyle } from '../utils'

defineProps({
  processes: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['view-detail', 'cancel'])

function handleRowClick(event, row) {
  emit('view-detail', row)
}

// 动态计算表格高度，参照工人台账的固定高度模式
const containerRef = ref(null)
const tableHeight = ref(670) // 默认值，与工人台账一致

let resizeObserver = null

onMounted(() => {
  if (!containerRef.value) return
  resizeObserver = new ResizeObserver((entries) => {
    for (const entry of entries) {
      const { height } = entry.contentRect
      if (height > 0) {
        tableHeight.value = height
      }
    }
  })
  resizeObserver.observe(containerRef.value)
})

onBeforeUnmount(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
})
</script>

<style scoped>
.table-container {
  flex: 1;
  min-height: 0;
  padding: 0 20px 16px;
  overflow: hidden;
}

/* 参照工人台账表格样式：圆角 + 边框 */
.table-container :deep(.el-table) {
  border-radius: 8px;
  border: 1px solid #f0f2f5;
  overflow: hidden;
}

/* 隐藏 el-table 内部顶部的伪元素分隔线 */
.table-container :deep(.el-table__inner-wrapper::before) {
  display: none;
}

:deep(.el-table .status-current-row),
:deep(.el-table .status-in-progress-row) {
  --el-table-tr-bg-color: #e3f2fd;
}

:deep(.el-table .status-rejected-row) {
  --el-table-tr-bg-color: #ffebee;
}

:deep(.el-table .status-completed-row) {
  --el-table-tr-bg-color: #e8f5e8;
}

:deep(.el-table .status-on-hold-row) {
  --el-table-tr-bg-color: #fff3e0;
}

:deep(.el-table .status-submitted-row) {
  --el-table-tr-bg-color: #e8f5e9;
}

:deep(.el-table .status-cancelled-row) {
  --el-table-tr-bg-color: #fce4ec;
}

:deep(.el-table .status-pending-row) {
  --el-table-tr-bg-color: #fafafa;
}

:deep(.el-table .el-table__row:hover) {
  --el-table-tr-bg-color: var(--el-table-row-hover-bg-color) !important;
}

:deep(.el-table .status-current-row:hover),
:deep(.el-table .status-in-progress-row:hover) {
  --el-table-tr-bg-color: #bbdefb !important;
}

:deep(.el-table .status-rejected-row:hover) {
  --el-table-tr-bg-color: #ffcdd2 !important;
}

:deep(.el-table .status-completed-row:hover) {
  --el-table-tr-bg-color: #c8e6c9 !important;
}

:deep(.el-table .status-on-hold-row:hover) {
  --el-table-tr-bg-color: #ffe0b2 !important;
}

:deep(.el-table .status-submitted-row:hover) {
  --el-table-tr-bg-color: #c8e6c9 !important;
}

:deep(.el-table .status-pending-row:hover) {
  --el-table-tr-bg-color: #eeeeee !important;
}

:deep(.el-table .status-cancelled-row:hover) {
  --el-table-tr-bg-color: #f8bbd0 !important;
}

.equipment-info {
  display: flex;
  align-items: center;
  gap: 6px;
}

.equipment-info .el-icon {
  color: #1f6e9c;
  font-size: 14px;
}

.process-name {
  display: flex;
  align-items: center;
  gap: 6px;
}

.milestone-tag {
  font-size: 10px;
  padding: 0 4px;
  height: 18px;
  line-height: 18px;
}

.status-tag {
  width: 60px;
  text-align: center;
}

.action-buttons {
  display: flex;
  gap: 4px;
  justify-content: center;
}

.action-buttons .el-button {
  padding: 4px 6px;
  font-size: 11px;
}

.action-buttons .el-button .el-icon {
  font-size: 12px;
  margin-right: 2px;
}
</style>