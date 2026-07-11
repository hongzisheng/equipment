<template>
  <el-table :data="workers" style="width: 100%; height: 100%;">
    <el-table-column label="工人信息" min-width="250">
      <template #default="{ row }">
        <div class="worker-basic-info clickable-card" @click="showWorkerCalendar(row)">
          <div><strong>ID:</strong> {{ row.id }}</div>
          <div><strong>姓名:</strong> {{ row.name }}</div>
          <div><strong>工种:</strong> {{ row.role }}</div>
          <div>
            <strong>状态:</strong>
            <el-tag :type="getWorkerStatusType(row.status)" size="small">
              {{ row.status }}
            </el-tag>
          </div>
          <div class="view-calendar-hint">
            <el-icon><Calendar /></el-icon>
            <span>点击查看任务日历</span>
          </div>
        </div>
      </template>
    </el-table-column>
    <el-table-column label="时间段内任务" min-width="300">
      <template #default="{ row }">
        <div v-if="row.tasks && row.tasks.length > 0">
          <el-collapse v-model="activeNames" class="custom-collapse">
            <el-collapse-item :title="'任务列表 (' + row.tasks.length + '个任务)'" :name="row.id">
              <div class="task-list-container">
                <div v-for="task in row.tasks" :key="task.task_name" class="task-item-blue">
                  <div class="task-header">
                    <div class="task-name">{{ task.task_name }}</div>
                    <el-tag :type="getTaskStatusType(task.status)" size="small" class="task-status-tag">{{ task.status }}</el-tag>
                  </div>
                  <div class="task-details">
                    <div class="task-equipment">
                      <i class="el-icon-s-tools"></i>
                      <span>设备: {{ task.equipment }}</span>
                    </div>
                    <div class="task-time">
                      <i class="el-icon-time"></i>
                      <span>第{{ extractDayFromFormattedTime(task.start_time) }}天 {{ formatTimeOnly(convertToTimestamp(extractDayFromFormattedTime(task.start_time), getTimeFromFormattedTime(task.start_time))) }} - 第{{ extractDayFromFormattedTime(task.end_time) }}天 {{ formatTimeOnly(convertToTimestamp(extractDayFromFormattedTime(task.end_time), getTimeFromFormattedTime(task.end_time))) }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </el-collapse-item>
          </el-collapse>
        </div>
        <div v-else class="no-tasks">
          无任务安排
        </div>
      </template>
    </el-table-column>
  </el-table>
</template>

<script setup>
import { ref } from 'vue'
import { Calendar } from '@element-plus/icons-vue'
import {
  getWorkerStatusType,
  getTaskStatusType,
  extractDayFromFormattedTime,
  getTimeFromFormattedTime,
  convertToTimestamp,
  formatTimeOnly
} from '../utils'

defineProps({
  workers: {
    type: Array,
    required: true
  }
})

const emit = defineEmits(['view-calendar'])

const activeNames = ref([])

const showWorkerCalendar = (worker) => {
  emit('view-calendar', worker)
}
</script>

<style scoped>
.worker-basic-info {
  padding: 12px;
  display: flex;
  flex-direction: column;
  background-color: #f1f6fa;
  border-radius: 6px;
  margin-bottom: 8px;
  transition: all 0.3s ease;
  cursor: pointer;
  position: relative;
}

.worker-basic-info.clickable-card:hover {
  background-color: #e6f3ff;
  border-color: #91d5ff;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(24, 144, 255, 0.1);
}

.worker-basic-info > div {
  margin-bottom: 5px;
}

.worker-basic-info > div:last-child {
  margin-bottom: 0;
}

.view-calendar-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #91d5ff;
  font-size: 12px;
  color: #1890ff;
}

.view-calendar-hint .el-icon {
  font-size: 14px;
}

.custom-collapse {
  border: none;
}

.custom-collapse :deep(.el-collapse-item__header) {
  background-color: #e6f7ff;
  border: 1px solid #91d5ff;
  border-radius: 6px;
  padding: 10px 15px;
  font-weight: 600;
  color: #1890ff;
  margin-bottom: 8px;
  transition: all 0.3s ease;
}

.custom-collapse :deep(.el-collapse-item__header:hover) {
  background-color: #bae7ff;
  border-color: #69c0ff;
}

.custom-collapse :deep(.el-collapse-item__wrap) {
  background-color: transparent;
  border: none;
}

.custom-collapse :deep(.el-collapse-item__content) {
  padding: 0;
}

.task-list-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 5px 0;
}

.task-item-blue {
  background: linear-gradient(135deg, #f0f8ff 0%, #e6f7ff 100%);
  border: 1px solid #bae7ff;
  border-radius: 8px;
  padding: 12px 15px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(24, 144, 255, 0.1);
}

.task-item-blue:hover {
  box-shadow: 0 4px 8px rgba(24, 144, 255, 0.15);
  transform: translateY(-2px);
  border-color: #69c0ff;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.task-name {
  font-weight: 600;
  color: #1890ff;
  font-size: 14px;
}

.task-status-tag {
  border-radius: 12px;
  font-size: 12px;
}

.task-details {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.task-equipment, .task-time {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #595959;
}

.task-equipment i, .task-time i {
  color: #1890ff;
  font-size: 13px;
}

.no-tasks {
  text-align: center;
  color: #8c8c8c;
  font-style: italic;
  padding: 15px 0;
}

:deep(.el-table) {
  background: transparent;
  border: none;
  flex: 1;
}

:deep(.el-table th) {
  background-color: #f8fafc !important;
}

:deep(.el-table tr) {
  background: transparent;
}

:deep(.el-table .el-table__row:hover) {
  background-color: #f8fafc !important;
}

:deep(.el-table .el-table__row) {
  border-bottom: 1px solid #e2e8f0 !important;
}

:deep(.el-table .el-table__row td) {
  padding: 8px 0;
  vertical-align: top;
}

:deep(.el-tag) {
  border-radius: 12px;
  padding: 0 12px;
  font-weight: 500;
}
</style>