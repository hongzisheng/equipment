<template>
  <el-card class="worker-status-card" shadow="never">
    <template #header>
      <div class="worker-header">
        <div class="worker-header-left">
          <span>{{ showStaffView ? '工作人员状态' : '班组状态' }}</span>
          <div class="status-view-switch" role="tablist" aria-label="状态视图切换">
            <button
              type="button"
              class="switch-btn"
              :class="{ active: showStaffView }"
              @click="switchView(true)"
            >
              工作人员
            </button>
            <button
              type="button"
              class="switch-btn"
              :class="{ active: !showStaffView }"
              @click="switchView(false)"
            >
              班组
            </button>
          </div>
        </div>
        <div class="worker-filter" v-if="showStaffView">
          <el-input
            v-model="workerFilter"
            placeholder="搜索工人"
            clearable
            size="small"
            style="width: 200px; margin-right: 10px;"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-select
            v-model="statusFilter"
            placeholder="状态筛选"
            clearable
            size="small"
            style="width: 120px;"
          >
            <el-option label="全部" value="" />
            <el-option label="工作中" value="工作中" />
            <el-option label="空闲中" value="空闲中" />
            <el-option label="已完成" value="已完成" />
          </el-select>
        </div>
        <div class="worker-filter" v-else>
          <el-select
            v-model="selectedEquipmentId"
            placeholder="按设备筛选"
            clearable
            size="small"
            style="width: 170px; margin-right: 10px;"
          >
            <el-option
              v-for="option in equipmentOptions"
              :key="`eq-${option.value}`"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
          <el-select
            v-model="selectedProcessId"
            placeholder="按工序筛选"
            clearable
            size="small"
            style="width: 190px;"
          >
            <el-option
              v-for="option in processOptions"
              :key="`pr-${option.value}`"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </div>
      </div>
    </template>

    <div class="status-view-body">
      <transition name="fade-slide" mode="out-in">
        <WorkerTable
          v-if="showStaffView"
          key="staff-view"
          :workers="filteredWorkers"
          @view-calendar="handleViewCalendar"
        />
        <TeamView
          v-else
          key="team-view"
          :orders="orders"
          :selected-equipment-id="selectedEquipmentId"
          :selected-process-id="selectedProcessId"
        />
      </transition>
    </div>
  </el-card>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Search } from '@element-plus/icons-vue'
import WorkerTable from './WorkerTable.vue'
import TeamView from './TeamView.vue'

const props = defineProps({
  workers: {
    type: Array,
    required: true
  },
  orders: {
    type: Array,
    required: true
  }
})

const emit = defineEmits(['view-calendar'])

const showStaffView = ref(true)
const workerFilter = ref('')
const statusFilter = ref('')
const selectedEquipmentId = ref('')
const selectedProcessId = ref('')

const switchView = (showStaff) => {
  showStaffView.value = showStaff
}

const filteredWorkers = computed(() => {
  let workersArray = props.workers.map(worker => ({
    id: worker.id || worker.worker_id,
    name: worker.name || worker.worker_name,
    role: worker.role || worker.worker_type,
    status: worker.status,
    tasks: worker.tasks
  }))

  if (workerFilter.value) {
    workersArray = workersArray.filter(worker =>
      worker.name.includes(workerFilter.value)
    )
  }
  if (statusFilter.value) {
    workersArray = workersArray.filter(worker => worker.status === statusFilter.value)
  }
  return workersArray
})

const equipmentOptions = computed(() => {
  const map = new Map()
  props.orders.forEach(row => {
    if (row.equipment_id == null || !row.equipment_name) return
    const key = String(row.equipment_id)
    if (!map.has(key)) {
      map.set(key, { value: key, label: row.equipment_name })
    }
  })
  return Array.from(map.values())
})

const processOptions = computed(() => {
  const map = new Map()
  props.orders.forEach(row => {
    if (selectedEquipmentId.value && String(row.equipment_id) !== selectedEquipmentId.value) return
    if (row.process_id == null || !row.process_name) return
    const key = String(row.process_id)
    if (!map.has(key)) {
      map.set(key, { value: key, label: row.process_name })
    }
  })
  return Array.from(map.values())
})

const handleViewCalendar = (worker) => {
  emit('view-calendar', worker)
}
</script>

<style scoped>
.worker-status-card {
  width: 40vw;
  background: white;
  display: flex;
  flex-direction: column;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: none;
  flex: 1;
  min-width: 0;
}

.worker-status-card :deep(.el-card__header) {
  background-color: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  padding: 16px 20px;
  border-radius: 10px 10px 0 0;
}

.worker-status-card :deep(.el-card__body) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.worker-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.worker-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.worker-header-left > span {
  font-size: 18px;
  font-weight: 600;
  color: #2d3748;
}

.status-view-switch {
  display: inline-flex;
  align-items: center;
  padding: 3px;
  border-radius: 999px;
  background: #edf2f7;
  border: 1px solid #dbe3ef;
  gap: 4px;
}

.switch-btn {
  border: none;
  background: transparent;
  color: #64748b;
  border-radius: 999px;
  padding: 4px 12px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.switch-btn:hover {
  color: #334155;
  background: #e2e8f0;
}

.switch-btn.active {
  color: #2563eb;
  background: #ffffff;
  box-shadow: 0 1px 3px rgba(37, 99, 235, 0.2);
}

.status-view-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.worker-filter {
  display: flex;
  align-items: center;
}

.worker-filter .el-input {
  margin-right: 12px;
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

@media (max-width: 1400px) {
  .worker-status-card {
    width: 35vw;
  }
}

@media (max-width: 1200px) {
  .worker-status-card {
    width: 100%;
    height: 500px;
  }
}
</style>