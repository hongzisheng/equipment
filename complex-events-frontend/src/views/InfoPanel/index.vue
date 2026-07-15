<template>
  <div class="info-panel-container">
    <el-card class="panel-card" shadow="hover">
      <div class="panel-header">
        <div class="panel-title">
          <el-icon class="panel-icon"><DataBoard /></el-icon>
          信息面板
        </div>
      </div>
      <div class="panel-body">
        <TimePeriodSelector
          v-model="searchForm"
          :project-total-days="projectTotalDays"
          @time-change="handleTimeChange"
        />

        <div class="main-layout">
          <WorkerStatusPanel
            :workers="workers"
            :orders="orders"
            @view-calendar="showWorkerCalendar"
          />

          <div class="right-content">
            <MaterialBoard :materials="materials" />
            <RepairToolsBoard :tools="tools" />
          </div>
        </div>
      </div>
    </el-card>

    <WorkerCalendar
      :visible="calendarVisible"
      :worker="selectedWorker"
      @close="closeCalendar"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, nextTick } from 'vue'
import { DataBoard } from '@element-plus/icons-vue'
import TimePeriodSelector from './components/TimePeriodSelector.vue'
import WorkerStatusPanel from './components/WorkerStatusPanel.vue'
import MaterialBoard from './components/MaterialBoard.vue'
import RepairToolsBoard from './components/RepairToolsBoard.vue'
import WorkerCalendar from './components/WorkerCalendar.vue'
import { getWorkerStatus, getOrders, getMaterialInventory, getMaintenanceTools } from '@/api/infoApi'

const projectTotalDays = ref(10)

const searchForm = reactive({
  startDay: 1,
  startTime: '08:00',
  endDay: projectTotalDays.value,
  endTime: '20:00',
  selectedTask: ''
})

const workers = ref([])
const orders = ref([])
const materials = ref([])
const tools = ref([])
const loading = ref(false)

const calendarVisible = ref(false)
const selectedWorker = ref({})

const refreshData = async () => {
  loading.value = true

  try {
    const workersResponse = await getWorkerStatus({
      start_time: `第${searchForm.startDay}天 ${searchForm.startTime}`,
      end_time: `第${searchForm.endDay}天 ${searchForm.endTime}`
    })
    workers.value = workersResponse.data.worker_status
  } catch (error) {
    console.error('获取工作人员状态失败:', error)
  }

  try {
    const ordersResponse = await getOrders()
    orders.value = ordersResponse.data.data
  } catch (error) {
    console.error('获取工单失败:', error)
  }

  try {
    const materialsResponse = await getMaterialInventory({
      end_time: `第${searchForm.endDay}天 ${searchForm.endTime}`
    })
    materials.value = materialsResponse.data.material_inventory
  } catch (error) {
    console.error('获取物料库存失败:', error)
  }

  try {
    const toolsResponse = await getMaintenanceTools({
      start_time: `第${searchForm.startDay}天 ${searchForm.startTime}`,
      end_time: `第${searchForm.endDay}天 ${searchForm.endTime}`
    })
    tools.value = toolsResponse.data.maintenance_tool_status
  } catch (error) {
    console.error('获取维修器具失败:', error)
  }

  loading.value = false
}

const handleTimeChange = (timeRange) => {
  refreshData()
}

const showWorkerCalendar = (worker) => {
  console.log('showWorkerCalendar called:', worker.name)
  console.log('worker object:', JSON.stringify(worker))
  selectedWorker.value = { ...worker }
  console.log('selectedWorker after set:', JSON.stringify(selectedWorker.value))
  calendarVisible.value = true
  console.log('calendarVisible set to:', calendarVisible.value)
}

const closeCalendar = () => {
  calendarVisible.value = false
  selectedWorker.value = {}
}

const testDialog = () => {
  calendarVisible.value = true
  selectedWorker.value = { name: '测试工人', tasks: [] }
  console.log('Test dialog triggered')
}

watch(
  [() => searchForm.startDay, () => searchForm.startTime, () => searchForm.endDay, () => searchForm.endTime],
  () => {
    refreshData()
  }
)

onMounted(() => {
  refreshData()
})
</script>

<style scoped>
.info-panel-container {
  padding: 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4edf5 100%);
  min-height: 100vh;
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
}

.panel-card {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-radius: 12px;
  border: none;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.panel-title {
  font-size: 22px;
  font-weight: 600;
  display: flex;
  align-items: center;
  color: #2c3e50;
}

.panel-icon {
  width: 28px;
  height: 28px;
  margin-right: 10px;
}

.mr6 {
  margin-right: 6px;
}

.main-layout {
  display: flex;
  gap: 24px;
  height: calc(100vh - 240px);
  min-height: 0;
}

.right-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 24px;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
}

@media (max-height: 900px) {
  .main-layout {
    height: calc(100vh - 220px);
  }
}

@media (max-width: 1200px) {
  .main-layout {
    flex-direction: column;
    height: auto;
  }
  .right-content {
    margin-top: 20px;
  }
}
</style>