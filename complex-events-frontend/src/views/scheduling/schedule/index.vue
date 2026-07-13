<template>
  <div class="gantt-container">
    <!-- 调度控制面板 -->
    <div class="schedule-control-panel">
      <div class="control-row">
        <div class="control-section">
          <span class="control-label">工单选择</span>
          <el-select
            v-model="selectedWorkOrders"
            placeholder="请选择工单（可多选）"
            multiple
            clearable
            :loading="loadingWorkOrders"
            style="width: 340px;"
          >
            <el-option
              v-for="wo in workOrders"
              :key="wo.id"
              :label="`${wo.order_number} - ${wo.equipment_name}`"
              :value="wo.id"
            />
          </el-select>
        </div>

        <div class="control-section">
          <span class="control-label">算法选择</span>
          <el-select v-model="selectedAlgorithm" style="width: 160px;">
            <el-option label="拓扑排序" value="topological" />
            <el-option label="贪心算法" value="greedy" />
            <el-option label="SPT最短优先" value="spt" />
            <el-option label="遗传算法" value="genetic" />
          </el-select>
        </div>

        <div class="control-buttons">
          <el-button
            type="primary"
            :loading="loadingSchedule"
            @click="runSchedule"
          >
            生成调度
          </el-button>
          <el-button
            v-if="assignmentRows.length > 0"
            type="warning"
            :loading="generatingWorkOrders"
            @click="publishWorkOrders"
          >
            发布工单
          </el-button>
          <el-button
            v-if="assignmentRows.length > 0"
            type="default"
            @click="showDetailTable = !showDetailTable"
          >
            {{ showDetailTable ? '隐藏明细' : '显示明细' }}
          </el-button>
        </div>
      </div>

      <!-- 统计信息 -->
      <div v-if="statistics" class="stats-row">
        <el-tag type="info">总工期: {{ statistics.total_project_duration_days }} 天</el-tag>
        <el-tag type="success">工人数: {{ statistics.total_workers }}</el-tag>
        <el-tag type="warning">设备数: {{ statistics.total_equipments }}</el-tag>
        <el-tag type="primary">工序数: {{ statistics.total_processes }}</el-tag>
      </div>

      <!-- 任务分配明细表 -->
      <div v-if="showDetailTable && assignmentRows.length > 0" class="detail-table-wrapper">
        <div class="detail-filter">
          <el-input
            v-model="deviceFilter"
            placeholder="按设备名称筛选"
            clearable
            style="width: 240px;"
          />
        </div>
        <el-table
          :data="filteredAssignmentRows"
          border
          stripe
          max-height="260"
          size="small"
        >
          <el-table-column prop="task" label="工序" min-width="140" show-overflow-tooltip />
          <el-table-column prop="device" label="设备" min-width="120" show-overflow-tooltip />
          <el-table-column prop="workersText" label="工人" min-width="200" show-overflow-tooltip />
          <el-table-column prop="startTimeFormatted" label="开始" width="100" />
          <el-table-column prop="endTimeFormatted" label="结束" width="100" />
        </el-table>
      </div>
    </div>

    <div class="gantt-content">
      <!-- 左侧筛选面板 -->
      <div class="filter-panel"> 
        <h3><i class="el-icon-menu"></i> 设备分类</h3>
        <el-tree
          :data="filteredTreeData"
          node-key="id"
          :default-expanded-keys="[1]"
          @node-click="handleNodeClick"
          :props="defaultProps"
          class="custom-tree"
        >
          <template #default="{ data }">
            <div class="tree-node">
              <el-icon v-if="data.type === 'root'" class="tree-node-icon"><OfficeBuilding /></el-icon>
              <el-icon v-else-if="data.type === 'category'" class="tree-node-icon"><Box /></el-icon>
              <el-icon v-else-if="data.type === 'kind'" class="tree-node-icon"><Files /></el-icon>
              <el-icon v-else-if="data.type === 'instance'" class="tree-node-icon"><Monitor /></el-icon>
              <span>{{ data.label }}</span>
            </div>
          </template>
        </el-tree>
      </div>

      <!-- 右侧甘特图区域 -->
      <div class="chart-panel">
        <div class="chart-header">
          <div class="day-info">
            <span class="work-time">工作时间: {{ WORK_START_HOUR }}:00 - {{ WORK_END_HOUR }}:00</span>
          </div>
        </div>

        <!-- 右侧表格和甘特图 -->
        <div class="table-and-chart">
          <!-- 左侧表格 -->
          <div class="table-section" :class="{ 'expanded': !currentNode || currentNode.type !== 'instance' }">
            <div class="table-header">
              <div v-if="!currentNode || currentNode.type !== 'instance'" class="table-cell equipment-cell">
                设备名称
                <span class="sort-icon" @click="toggleEquipmentSort">
                  <el-icon v-if="sortType === 'equipment'">
                    <SortUp v-if="sortOrder === 'asc'" />
                    <SortDown v-else />
                  </el-icon>
                  <el-icon v-else-if="sortType === ''"><Sort /></el-icon>
                  <el-icon v-else><Sort /></el-icon>
                </span>
              </div>
              <div class="table-cell process-cell">工序名称</div>
              <div class="table-cell duration-cell">时长</div>
              <div class="table-cell start-time-cell">
                开始时间
                <span class="sort-icon" @click="toggleTimeSort">
                  <el-icon v-if="sortType === 'time'">
                    <SortUp v-if="sortOrder === 'asc'" />
                    <SortDown v-else />
                  </el-icon>
                  <el-icon v-else-if="sortType === ''"><Sort /></el-icon>
                  <el-icon v-else><Sort /></el-icon>
                </span>
              </div>
              <div class="table-cell end-time-cell">结束时间</div>
              <div class="table-cell workers-cell">工作人员</div>
              
              <div class="table-cell operation-cell">操作</div>
              <div class="table-cell day-cell"></div>
            </div>
            <div class="table-body" ref="tableBodyRef" @scroll="handleTableScroll">
              <!-- 按天数分组显示，跨天工序特殊处理 -->
              <template v-for="(group, groupIndex) in processedTableGroups" :key="groupIndex">
                <div class="merged-row" :style="{ height: `${group.items.length * rowHeight}px` }">
                  <!-- 左侧普通列区域 -->
                  <div class="normal-cells">
                    <div v-for="(item, itemIndex) in group.items" :key="itemIndex" 
                      class="table-row"
                      :class="[
                        { 'even-row': (groupIndex * 10 + itemIndex) % 2 === 0 },
                        { 'split-row': item.isSplit },
                        { 'split-row-first': item.isSplit && item.splitPart === 'first' },
                        { 'split-row-second': item.isSplit && item.splitPart === 'second' },
                        { 'no-bottom-border': item.isSplit && item.splitPart === 'first' },
                        { 'no-top-border': item.isSplit && item.splitPart === 'second' }
                      ]">
                      <div v-if="!currentNode || currentNode.type !== 'instance'" class="table-cell equipment-cell">{{ item.equipment_name }}</div>
                      <div class="table-cell process-cell">
                        <!-- 跨天工序只在第一行显示名称 -->
                        <span v-if="!item.isSplit || (item.isSplit && item.splitPart === 'first')">
                          {{ item.process_name }}
                          <span v-if="item.isSplit" class="split-tag">(跨天)</span>
                        </span>
                        <!-- 跨天工序的第二行留空 -->
                        <span v-else-if="item.isSplit && item.splitPart === 'second'">
                          &nbsp;
                        </span>
                      </div>
                      <div class="table-cell duration-cell">{{ item.duration_hours }}h</div>
                      <div class="table-cell start-time-cell">{{ item.actualStartTimeFormatted }}</div>
                      <div class="table-cell end-time-cell">{{ item.actualEndTimeFormatted }}</div>
                      <div class="table-cell workers-cell">{{ formatWorkers(item.workers) }}</div>
                      <div class="table-cell operation-cell">
                        <div class="operation-buttons">
                          <el-button 
                            type="primary" 
                            size="small" 
                            @click="viewDetail(item)"
                            :icon="View"
                            circle
                            title="查看详情"
                          />
                          <el-button 
                            type="warning" 
                            size="small" 
                            @click="editItem(item)"
                            :icon="Edit"
                            circle
                            title="编辑"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                  <!-- 右侧合并列（第几天） -->
                  <div class="merged-day-cell">
                    <div class="day-content">
                      <span class="day-prefix">第</span>
                      <span class="day-number">{{ group.startDay }}</span>
                      <span class="day-suffix">天</span>
                    </div>
                  </div>
                </div>
              </template>
            </div>
          </div>

          <!-- 右侧甘特图 -->
          <div class="chart-section">
            <!-- 日期刻度 -->
            <div class="time-scale-section">
              <div class="time-scale">
                <div class="time-scale">
  <div v-for="day in dayNumbers" :key="day" class="time-scale-day">
    <div class="day-label">第{{ day }}天</div>
  </div>
</div>
              </div>
            </div>

            <!-- 甘特图内容 -->
            <div 
              class="gantt-chart-section"
              ref="ganttChartContentRef"
              @scroll="syncScroll('gantt')"
              @mouseenter="disableGanttScroll"
              @mouseleave="enableGanttScroll"
            >
              <!-- Canvas 连接线容器 -->
              <canvas ref="connectionsCanvasRef" class="connections-canvas"></canvas>
              
              <div class="gantt-chart-content">
                <!-- 工序条 -->
                <div v-for="process in filteredAndGroupedProcesses" :key="process.process_id"
                    class="process-row" :class="{ 'even-row': index % 2 === 0 }">
                  <div class="process-bar-container">
                    <div class="process-bar" 
                        :style="getProcessBarStyle(process)"
                        :class="getEquipmentClass(process.equipment_name)"
                        @mouseenter="showTooltip(process, $event)"
                        @mouseleave="hideTooltip"
                        :ref="el => processBarRefs[index] = el">
                      <span class="process-bar-label">{{ process.process_name }}</span>
                    </div>
                  </div>
                </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>


    <!-- 自定义提示框 -->
    <div v-if="showTooltipContent" class="custom-tooltip" :style="tooltipStyle">
      <div class="tooltip-content">
        <div class="tooltip-item"><strong>设备:</strong> {{ currentTooltipProcess?.equipment_name }}</div>
        <div class="tooltip-item"><strong>工序:</strong> {{ currentTooltipProcess?.process_name }}</div>
        <div class="tooltip-item"><strong>计划开始:</strong> 第{{ currentTooltipProcess?.startDay }}天</div>
        <div class="tooltip-item"><strong>计划结束:</strong> 第{{ currentTooltipProcess?.endDay }}天</div>
        <div class="tooltip-item"><strong>时长:</strong> {{ currentTooltipProcess?.duration_hours }}小时</div>
        <div v-if="currentTooltipProcess?.isSplit" class="tooltip-item"><strong>说明:</strong> 跨天工序{{ currentTooltipProcess?.splitPart === 'first' ? '（当天部分）' : '（次日部分）' }}</div>
        <div class="tooltip-item"><strong>工作人员:</strong></div>
        <div v-for="(workers, role) in currentTooltipProcess?.workers || {}" :key="role" class="tooltip-worker">
          {{ role }}: {{ workers.join(', ') }}
        </div>
      </div>
    </div>

    <!-- 详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="工序详情"
      width="600px"
    >
      <div class="detail-content">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="设备名称">
            {{ currentItem?.equipment_name }}
          </el-descriptions-item>
          <el-descriptions-item label="工序名称">
            {{ currentItem?.process_name }}
          </el-descriptions-item>
          <el-descriptions-item label="计划开始时间">
            {{ currentItem?.start_time_formatted }}
          </el-descriptions-item>
          <el-descriptions-item label="计划结束时间">
            {{ currentItem?.end_time_formatted }}
          </el-descriptions-item>
          <el-descriptions-item label="实际开始时间">
            {{ currentItem?.actualStartTimeFormatted }}
          </el-descriptions-item>
          <el-descriptions-item label="实际结束时间">
            {{ currentItem?.actualEndTimeFormatted }}
          </el-descriptions-item>
          <el-descriptions-item label="时长">
            {{ currentItem?.duration_hours }} 小时
          </el-descriptions-item>
          <el-descriptions-item label="工序ID">
            {{ currentItem?.process_id }}
          </el-descriptions-item>
          <el-descriptions-item label="跨天状态" :span="2">
            <el-tag v-if="currentItem?.isSplit" type="success">
              {{ currentItem?.splitPart === 'first' ? '当天部分' : '次日部分' }}
            </el-tag>
            <el-tag v-else type="info">无</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="工作人员" :span="2">
            <div v-if="currentItem?.workers">
              <div v-for="(workers, role) in currentItem.workers" :key="role" class="worker-item">
                <strong>{{ role }}:</strong> {{ workers.join(', ') }}
              </div>
            </div>
            <span v-else>无</span>
          </el-descriptions-item>
          <el-descriptions-item label="前置工序" :span="2">
            <div v-if="currentItem?.predecessors && currentItem.predecessors.length > 0">
              <el-tag
                v-for="predecessor in currentItem.predecessors"
                :key="predecessor.process_id"
                size="small"
                style="margin-right: 5px; margin-bottom: 5px;"
              >
                {{ predecessor.process_id }}
              </el-tag>
            </div>
            <span v-else>无</span>
          </el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="detailDialogVisible = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      :title="editMode === 'create' ? '添加工序' : '编辑工序'"
      width="800px"
      @closed="resetForm"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="editFormRules"
        label-width="100px"
        label-position="right"
        status-icon
      >
        <el-form-item label="设备名称" prop="equipment_name">
          <el-input
            v-model="editForm.equipment_name"
            placeholder="请输入设备名称"
            clearable
          />
        </el-form-item>

        <el-form-item label="工序名称" prop="process_name">
          <el-input
            v-model="editForm.process_name"
            placeholder="请输入工序名称"
            clearable
          />
        </el-form-item>

        <el-form-item label="工序ID" prop="process_id">
          <el-input
            v-model="editForm.process_id"
            placeholder="请输入工序ID"
            clearable
            :disabled="editMode === 'edit'"
          />
        </el-form-item>

        <el-form-item label="开始时间" prop="start_time">
          <el-input-number
            v-model="editForm.start_time"
            :min="0"
            :step="60"
            placeholder="请输入开始时间（分钟）"
            style="width: 100%"
          />
          <div class="form-tip">当前值: {{ editForm.start_time }} 分钟 (约 {{ Math.floor(editForm.start_time / 1440) }} 天 {{ Math.floor((editForm.start_time % 1440) / 60) }} 小时 {{ editForm.start_time % 60 }} 分钟)</div>
        </el-form-item>

        <el-form-item label="时长" prop="duration_hours">
          <el-input-number
            v-model="editForm.duration_hours"
            :min="0.5"
            :step="0.5"
            :precision="1"
            placeholder="请输入时长（小时）"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="工作人员" required>
          <div class="worker-input-group">
            <div v-for="(worker, index) in editForm.workers" :key="index" class="worker-input-row">
              <el-input
                v-model="worker.role"
                placeholder="角色"
                style="width: 120px; margin-right: 10px;"
              />
              <el-input
                v-model="worker.names"
                placeholder="人员名称，用逗号分隔"
                style="flex: 1; margin-right: 10px;"
              />
              <el-button
                type="danger"
                :icon="Remove"
                circle
                @click="removeWorker(index)"
                title="删除"
              />
            </div>
            <el-button
              type="primary"
              :icon="Plus"
              @click="addWorker"
              class="add-worker-btn"
            >
              添加人员
            </el-button>
          </div>
        </el-form-item>

        <el-form-item label="前置工序">
          <div class="predecessor-input-group">
            <div v-for="(predecessor, index) in editForm.predecessors" :key="index" class="predecessor-input-row">
              <el-input
                v-model="predecessor.process_id"
                placeholder="前置工序ID"
                style="flex: 1; margin-right: 10px;"
              />
              <el-button
                type="danger"
                :icon="Remove"
                circle
                @click="removePredecessor(index)"
                title="删除"
              />
            </div>
            <el-button
              type="primary"
              :icon="Plus"
              @click="addPredecessor"
              class="add-predecessor-btn"
            >
              添加工序依赖
            </el-button>
          </div>
        </el-form-item>

        <el-form-item label="设备类别" prop="equipment_category">
          <el-select
            v-model="editForm.equipment_category"
            placeholder="请选择设备类别"
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="category in categoryOptions"
              :key="category.value"
              :label="category.label"
              :value="category.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="设备类型" prop="equipment_type_name">
          <el-input
            v-model="editForm.equipment_type_name"
            placeholder="请输入设备类型名称"
            clearable
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitEdit">
            {{ editMode === 'create' ? '创建' : '保存' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, reactive, ref, onBeforeUnmount, watch, nextTick, onMounted } from 'vue'
import {
  OfficeBuilding,
  Box,
  Files,
  Monitor,
  Sort,
  SortUp,
  SortDown,
  View,
  Edit,
  Plus,
  Remove
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

const BASE_URL = `${import.meta.env.VITE_APP_BASE_API || ''}/api`

// =================== 调度控制面板状态 ===================
const selectedWorkOrders = ref([])
const workOrders = ref([])
const loadingWorkOrders = ref(false)
const selectedAlgorithm = ref('topological')
const loadingSchedule = ref(false)
const generatingWorkOrders = ref(false)
const assignmentRows = ref([])
const statistics = ref(null)
const showDetailTable = ref(false)
const deviceFilter = ref('')

const filteredAssignmentRows = computed(() => {
  if (!deviceFilter.value) return assignmentRows.value
  return assignmentRows.value.filter(r =>
    r.device.includes(deviceFilter.value)
  )
})

async function fetchWorkOrders() {
  loadingWorkOrders.value = true
  try {
    const res = await axios.get(`${BASE_URL}/work-orders`)
    workOrders.value = res.data?.data || res.data || []
  } catch (e) {
    ElMessage.error('获取工单列表失败')
  } finally {
    loadingWorkOrders.value = false
  }
}

async function runSchedule() {
  if (!selectedWorkOrders.value.length) {
    ElMessage.warning('请先选择至少一个工单')
    return
  }
  loadingSchedule.value = true
  try {
    const res = await axios.post(`${BASE_URL}/run-scheduler`, {
      work_order_ids: selectedWorkOrders.value,
      algorithm: selectedAlgorithm.value,
    })
    const result = res.data
    if (!result.success) {
      ElMessage.error(result.message || '调度失败')
      return
    }
    const plan = result.schedule_plan || []
    localStorage.setItem('schedule_plan', JSON.stringify(plan))

    // 更新甘特图数据
    processData.value = plan
    buildTreeData()
    await nextTick()
    drawConnections()

    // 更新统计信息
    statistics.value = result.statistics || null

    // 更新任务明细
    assignmentRows.value = plan.map(t => {
      const safeWorkers = t.workers && typeof t.workers === 'object' ? t.workers : {}
      const workersText = Object.entries(safeWorkers)
        .map(([role, names]) => `${role}: ${Array.isArray(names) ? names.join('、') : '待分配'}`)
        .join('；') || '未分配'
      return {
        task: t.process_name,
        device: t.equipment_name,
        workersText,
        startTimeFormatted: t.start_time_formatted,
        endTimeFormatted: t.end_time_formatted,
      }
    })

    ElMessage.success(`调度完成，共 ${plan.length} 条工序`)
  } catch (e) {
    ElMessage.error('调度请求失败，请检查后端服务')
    console.error(e)
  } finally {
    loadingSchedule.value = false
  }
}

async function publishWorkOrders() {
  generatingWorkOrders.value = true
  try {
    const res = await axios.post(`${BASE_URL}/assign-workers-from-schedule`)
    const result = res.data
    if (result.success) {
      ElMessage.success(`发布成功，共处理 ${result.assigned_count} 个任务`)
    } else {
      ElMessage.error(result.message || '发布失败')
    }
  } catch (e) {
    ElMessage.error('发布失败，请检查后端服务')
    console.error(e)
  } finally {
    generatingWorkOrders.value = false
  }
}

// 工作时间配置
const WORK_START_HOUR = 8
const WORK_END_HOUR = 20
const WORK_HOURS_PER_DAY = WORK_END_HOUR - WORK_START_HOUR
const rowHeight = 52
const totalDays = computed(() => {
  if (!flattenedProcesses.value.length) return 1
  const maxDay = Math.max(...flattenedProcesses.value.map(p => p.endDay))
  const minDay = Math.min(...flattenedProcesses.value.map(p => p.startDay))
  return maxDay - minDay + 1
})
const dayNumbers = computed(() => {
  if (!flattenedProcesses.value.length) return [1]
  const minDay = Math.min(...flattenedProcesses.value.map(p => p.startDay))
  const maxDay = Math.max(...flattenedProcesses.value.map(p => p.endDay))
  const days = []
  for (let i = minDay; i <= maxDay; i++) {
    days.push(i)
  }
  return days
})
// 表格和甘特图的滚动容器引用
const tableBodyRef = ref(null)
const ganttChartContentRef = ref(null)
const connectionsCanvasRef = ref(null)
const processBarRefs = ref([])
const editFormRef = ref(null)

// Canvas 上下文
let canvasCtx = null

// 排序相关
const sortType = ref('equipment')
const sortOrder = ref('asc')

// 对话框相关
const detailDialogVisible = ref(false)
const editDialogVisible = ref(false)
const editMode = ref('edit') // 'edit' 或 'create'
const currentItem = ref(null)

// 编辑表单
const editForm = reactive({
  equipment_name: '',
  process_name: '',
  process_id: '',
  start_time: 0,
  duration_hours: 0,
  workers: [],
  predecessors: [],
  equipment_category: '',
  equipment_type_name: ''
})

// 编辑表单验证规则
const editFormRules = {
  equipment_name: [
    { required: true, message: '请输入设备名称', trigger: 'blur' }
  ],
  process_name: [
    { required: true, message: '请输入工序名称', trigger: 'blur' }
  ],
  process_id: [
    { required: true, message: '请输入工序ID', trigger: 'blur' }
  ],
  start_time: [
    { required: true, message: '请输入开始时间', trigger: 'blur' },
    { type: 'number', min: 0, message: '开始时间不能为负数', trigger: 'blur' }
  ],
  duration_hours: [
    { required: true, message: '请输入时长', trigger: 'blur' },
    { type: 'number', min: 0.5, message: '时长至少为0.5小时', trigger: 'blur' }
  ],
  equipment_category: [
    { required: true, message: '请选择设备类别', trigger: 'change' }
  ],
  equipment_type_name: [
    { required: true, message: '请输入设备类型名称', trigger: 'blur' }
  ]
}

// 示例数据
const processData = ref(JSON.parse(localStorage.getItem('schedule_plan') || '[]'))
console.log(processData.value)

// 树形结构数据
const treeData = ref([])

// 当前选中的节点
const currentNode = ref(null)

// 筛选相关
const filterForm = reactive({
  category: '',
  type: '',
  instance: ''
})

const categoryOptions = ref([
  { value: '静设备', label: '静设备' },
  { value: '动设备', label: '动设备' },
  { value: '电气设备', label: '电气设备' }
])

const typeOptions = ref([])

// 树形配置
const defaultProps = {
  children: 'children',
  label: 'label'
}

// 切换设备排序
const toggleEquipmentSort = () => {
  if (sortType.value === 'equipment') {
    if (sortOrder.value === 'asc') {
      sortOrder.value = 'desc'
    } else if (sortOrder.value === 'desc') {
      sortType.value = ''
      sortOrder.value = 'asc'
    }
  } else {
    sortType.value = 'equipment'
    sortOrder.value = 'asc'
  }
}

// 切换时间排序
const toggleTimeSort = () => {
  if (sortType.value === 'time') {
    if (sortOrder.value === 'asc') {
      sortOrder.value = 'desc'
    } else if (sortOrder.value === 'desc') {
      sortType.value = 'equipment'
      sortOrder.value = 'asc'
    }
  } else {
    sortType.value = 'time'
    sortOrder.value = 'asc'
  }
  
  nextTick(() => {
    drawConnections()
  })
}

// 同步滚动事件处理
const syncScroll = (source) => {
  if (source === 'table' && tableBodyRef.value && ganttChartContentRef.value) {
    ganttChartContentRef.value.scrollTop = tableBodyRef.value.scrollTop
  } else if (source === 'gantt' && tableBodyRef.value && ganttChartContentRef.value) {
    const isGanttAtBottom = ganttChartContentRef.value.scrollHeight - ganttChartContentRef.value.scrollTop <= ganttChartContentRef.value.clientHeight + 1;
    if (!isGanttAtBottom) {
      tableBodyRef.value.scrollTop = ganttChartContentRef.value.scrollTop
    }
  }
}

// 处理表格滚动事件
const handleTableScroll = (event) => {
  const element = event.target;
  if (ganttChartContentRef.value) {
    const isAtBottom = element.scrollHeight - element.scrollTop <= element.clientHeight + 1;
    if (!isAtBottom) {
      ganttChartContentRef.value.scrollTop = element.scrollTop;
    }
  }
}

// 计算工作时间段
const workHours = computed(() => {
  const hours = []
  for (let i = WORK_START_HOUR; i <= WORK_END_HOUR; i++) {
    hours.push(i)
  }
  return hours
})

// 格式化工作人员信息显示
const formatWorkers = (workers) => {
  if (!workers) return ''
  
  const workerList = []
  Object.entries(workers).forEach(([role, names]) => {
    if (Array.isArray(names) && names.length > 0) {
      workerList.push(`${role}: ${names.join(', ')}`)
    }
  })
  
  return workerList.join('; ')
}

const flattenedProcesses = computed(() => {
  const result = []
  processData.value.forEach(process => {
    // 直接使用后端返回的天数（start_time, end_time）
    const startDay = Math.floor(process.start_time) + 1
    const endDay = Math.floor(process.end_time) + 1
    
    result.push({
      ...process,
      startDay,
      endDay,
      rawStartTime: process.start_time,
      rawEndTime: process.end_time,
      actualStartTimeFormatted: `第${startDay}天`,
      actualEndTimeFormatted: `第${endDay}天`,
      predecessors: process.predecessors || []
    })
  })
  return result
})

// 过滤和分组工序
const filteredAndGroupedProcesses = computed(() => {
  let filtered = flattenedProcesses.value || []
  
  if (currentNode.value && currentNode.value.type === 'instance') {
    filtered = filtered.filter(process => process.equipment_name === currentNode.value.label)
  }

  let sorted = [...filtered]
  
  if (sortType.value === 'equipment') {
    sorted.sort((a, b) => {
      const equipmentCompare = a.equipment_name.localeCompare(b.equipment_name)
      if (equipmentCompare !== 0) {
        return sortOrder.value === 'asc' ? equipmentCompare : -equipmentCompare
      }
      const timeCompare = a.actualStartTime - b.actualStartTime
      return sortOrder.value === 'asc' ? timeCompare : -timeCompare
    })
  } else if (sortType.value === 'time') {
    sorted.sort((a, b) => {
      const timeCompare = a.actualStartTime - b.actualStartTime
      return sortOrder.value === 'asc' ? timeCompare : -timeCompare
    })
  }

  return sorted
})

// 按天数分组处理表格数据
const processedTableGroups = computed(() => {
  const sourceData = filteredAndGroupedProcesses.value
  if (!sourceData.length) return []

  if (sortType.value === 'time') {
    const dayGroups = {}
    
    sourceData.forEach(item => {
      const day = item.startDay
      if (!dayGroups[day]) {
        dayGroups[day] = []
      }
      dayGroups[day].push(item)
    })
    
    return Object.keys(dayGroups)
      .sort((a, b) => sortOrder.value === 'asc' ? parseInt(a) - parseInt(b) : parseInt(b) - parseInt(a))
      .map(day => ({
        startDay: parseInt(day),
        items: dayGroups[day]
      }))
  } else {
    const groups = []
    let currentGroup = {
      startDay: sourceData[0].startDay,
      items: [sourceData[0]]
    }

    for (let i = 1; i < sourceData.length; i++) {
      if (sourceData[i].startDay === currentGroup.startDay) {
        currentGroup.items.push(sourceData[i])
      } else {
        groups.push(currentGroup)
        currentGroup = {
          startDay: sourceData[i].startDay,
          items: [sourceData[i]]
        }
      }
    }

    groups.push(currentGroup)
    return groups
  }
})

// 获取工序条的样式
const getProcessBarStyle = (segment) => {
  const process = segment // 实际上 segment 是整个工序对象（不是时间片段）
  const startDay = process.startDay
  const endDay = process.endDay
  const totalDaysRange = dayNumbers.value.length
  const startIndex = dayNumbers.value.indexOf(startDay)
  const endIndex = dayNumbers.value.indexOf(endDay)
  const left = (startIndex / totalDaysRange) * 100
  const width = ((endIndex - startIndex + 1) / totalDaysRange) * 100
  return {
    left: `${left}%`,
    width: `${Math.max(1, width)}%`
  }
}

// 根据process_id查找工序
const findProcessById = (processId) => {
  return flattenedProcesses.value.find(process => process.process_id === processId)
}

// 绘制工序间连接线
const drawConnections = () => {
  if (sortType.value === 'time') {
    clearConnections()
    return
  }
  
  if (!currentNode.value || currentNode.value.type !== 'instance') {
    console.log('❌ 未选择具体设备，不显示连接线');
    clearConnections()
    return
  }

  const canvas = connectionsCanvasRef.value
  if (!canvas || !filteredAndGroupedProcesses.value.length) {
    console.log('❌ Canvas或工序数据不存在，不绘制连接线');
    return
  }

  if (!canvasCtx) {
    canvasCtx = canvas.getContext('2d')
  }

  clearConnections()

  const container = ganttChartContentRef.value
  const containerRect = container.getBoundingClientRect()
  const scrollLeft = container.scrollLeft
  const scrollTop = container.scrollTop
  
  canvas.width = containerRect.width
  const contentHeight = filteredAndGroupedProcesses.value.length * rowHeight
  canvas.height = Math.max(containerRect.height, contentHeight)

  canvas.style.position = 'absolute'
  canvas.style.top = '0px'
  canvas.style.left = '0px'

  const processes = filteredAndGroupedProcesses.value
  let totalConnections = 0
  let foundConnections = 0
  
  processes.forEach((process, index) => {
    if (process.predecessors && process.predecessors.length > 0) {
      totalConnections += process.predecessors.length
      
      process.predecessors.forEach((predecessor) => {
        const predecessorProcess = findProcessById(predecessor.process_id)
        
        if (predecessorProcess) {
          const predecessorIndex = processes.findIndex(p => p.process_id === predecessor.process_id)
          const currentIndex = index
          
          if (predecessorIndex !== -1 && currentIndex !== -1) {
            const predecessorBar = processBarRefs.value[predecessorIndex]
            const currentBar = processBarRefs.value[currentIndex]
            
            if (predecessorBar && currentBar) {
              foundConnections++
              
              const predecessorRect = predecessorBar.getBoundingClientRect()
              const currentRect = currentBar.getBoundingClientRect()
              
              const predecessorLeft = predecessorRect.left - containerRect.left + scrollLeft
              const predecessorTop = predecessorRect.top - containerRect.top + scrollTop
              const predecessorRight = predecessorRect.right - containerRect.left + scrollLeft
              const predecessorBottom = predecessorRect.bottom - containerRect.top + scrollTop
              
              const currentLeft = currentRect.left - containerRect.left + scrollLeft
              const currentTop = currentRect.top - containerRect.top + scrollTop
              const currentRight = currentRect.right - containerRect.left + scrollLeft
              const currentBottom = currentRect.bottom - containerRect.top + scrollTop

              const isEndAt20 = predecessorProcess.actualEndTimeFormatted && 
                                predecessorProcess.actualEndTimeFormatted.includes('20:00')

              let startX, startY;

              if (isEndAt20) {
                startX = predecessorRight - 20
                startY = predecessorBottom
              } else {
                startX = predecessorRight
                startY = predecessorTop + predecessorRect.height / 2
              }
              
              const endX = currentLeft + 20
              const endY = currentTop
              
              canvasCtx.beginPath()
              
              if (isEndAt20) {
                const verticalExtend = 5;
                const curveRadius = 3;
                
                canvasCtx.moveTo(startX, startY)
                canvasCtx.lineTo(startX, startY + verticalExtend - curveRadius)
                canvasCtx.quadraticCurveTo(startX, startY + verticalExtend, startX + curveRadius, startY + verticalExtend)
                canvasCtx.lineTo(endX - curveRadius, startY + verticalExtend)
                canvasCtx.quadraticCurveTo(endX, startY + verticalExtend, endX, startY + verticalExtend + curveRadius)
                canvasCtx.lineTo(endX, endY)
              } else {
                const extendLength = 20;
                const curveRadius = 3;
                
                canvasCtx.moveTo(startX, startY)
                canvasCtx.lineTo(startX + extendLength - curveRadius, startY)
                canvasCtx.quadraticCurveTo(startX + extendLength, startY, startX + extendLength, startY + curveRadius)
                canvasCtx.lineTo(startX + extendLength, endY - 10 - curveRadius)
                canvasCtx.quadraticCurveTo(startX + extendLength, endY - 10, startX + extendLength + curveRadius, endY - 10)
                canvasCtx.lineTo(endX - curveRadius, endY - 10)
                canvasCtx.quadraticCurveTo(endX, endY - 10, endX, endY - 10 + curveRadius)
                canvasCtx.lineTo(endX, endY)
              }
              
              canvasCtx.strokeStyle = 'black'
              canvasCtx.lineWidth = 1.2
              canvasCtx.lineCap = 'round'
              canvasCtx.stroke()
              
              drawArrowhead(endX, endY)
            }
          }
        }
      })
    }
  });
}

const drawArrowhead = (x, y) => {
  const width = 6
  
  canvasCtx.save()
  canvasCtx.translate(x, y)
  
  canvasCtx.beginPath()
  canvasCtx.moveTo(0, 0)
  canvasCtx.lineTo(-width / 2, -width)
  canvasCtx.lineTo(width / 2, -width)
  canvasCtx.closePath()
  
  canvasCtx.fillStyle = 'black'
  canvasCtx.fill()
  
  canvasCtx.restore()
}

// 清除所有连接线
const clearConnections = () => {
  if (canvasCtx && connectionsCanvasRef.value) {
    const canvas = connectionsCanvasRef.value
    canvasCtx.clearRect(0, 0, canvas.width, canvas.height)
  }
}

// 工具提示相关
const showTooltipContent = ref(false)
const currentTooltipProcess = ref(null)
const tooltipStyle = reactive({
  left: '0px',
  top: '0px'
})

const showTooltip = (process, event) => {
  currentTooltipProcess.value = process
  showTooltipContent.value = true
}

const hideTooltip = () => {
  showTooltipContent.value = false
  currentTooltipProcess.value = null
}

// 添加控制甘特图滚动的函数
const disableGanttScroll = () => {
  if (ganttChartContentRef.value) {
    ganttChartContentRef.value.style.overflow = 'hidden'
  }
}

const enableGanttScroll = () => {
  if (ganttChartContentRef.value) {
    ganttChartContentRef.value.style.overflow = 'auto'
  }
}

// 根据设备名称获取CSS类
const getEquipmentClass = (equipmentName) => {
  if (sortType.value === 'time') {
    let hash = 0;
    for (let i = 0; i < equipmentName.length; i++) {
      hash = equipmentName.charCodeAt(i) + ((hash << 5) - hash);
    }
    const hue = Math.abs(hash) % 360;
    return `equipment-color-${hue % 10}`;
  }
  return 'equipment-default';
}

// 获取筛选后的树数据
const filteredTreeData = computed(() => {
  if (!filterForm.category && !filterForm.type && !filterForm.instance) {
    return treeData.value
  }

  const filtered = JSON.parse(JSON.stringify(treeData.value))
  
  if (filtered.length > 0 && filtered[0].children) {
    if (filterForm.category) {
      const categoryNode = filtered[0].children.find(cat => cat.label === filterForm.category)
      if (categoryNode) {
        filtered[0].children = [categoryNode]
      } else {
        filtered[0].children = []
      }
    }
    
    if (filterForm.type && filtered[0].children.length > 0) {
      filtered[0].children.forEach(category => {
        if (category.children) {
          category.children = category.children.filter(kind => kind.label === filterForm.type)
        }
      })
    }
    
    if (filterForm.instance && filtered[0].children.length > 0) {
      filtered[0].children.forEach(category => {
        if (category.children) {
          category.children.forEach(kind => {
            if (kind.children) {
              kind.children = kind.children.filter(instance => 
                instance.label.toLowerCase().includes(filterForm.instance.toLowerCase())
              )
            }
          })
        }
      })
    }
  }
  
  return filtered
})

// 动态构建树形结构数据
const buildTreeData = () => {
  const uniqueCategories = [...new Set(processData.value.map(item => item.equipment_category || '未分类设备'))]
  
  const root = {
    id: 1,
    label: '设备',
    type: 'root',
    children: []
  }
  
  uniqueCategories.forEach((category, index) => {
    const categoryNode = {
      id: index + 2,
      label: category,
      type: 'category',
      children: []
    }
    
    const categoryItems = processData.value.filter(item => (item.equipment_category || '未分类设备') === category)
    const uniqueEquipmentTypes = [...new Set(categoryItems.map(item => item.equipment_type_name || '未指定类型'))]
    
    uniqueEquipmentTypes.forEach((equipmentType, typeIndex) => {
      const typeNode = {
        id: (index + 2) * 10 + typeIndex + 1,
        label: equipmentType,
        type: 'kind',
        children: []
      }
      
      const typeItems = categoryItems.filter(item => (item.equipment_type_name || '未指定类型') === equipmentType)
      const uniqueEquipmentNames = [...new Set(typeItems.map(item => item.equipment_name))]
      
      uniqueEquipmentNames.forEach((equipmentName, nameIndex) => {
        typeNode.children.push({
          id: (index + 2) * 100 + typeIndex * 10 + nameIndex + 1,
          label: equipmentName,
          type: 'instance'
        })
      })
      
      categoryNode.children.push(typeNode)
    })
    
    root.children.push(categoryNode)
  })
  
  treeData.value = [root]
}

// 操作相关方法
// 查看详情
const viewDetail = (item) => {
  currentItem.value = item
  detailDialogVisible.value = true
}

// 编辑项目
const editItem = (item) => {
  currentItem.value = item
  editMode.value = 'edit'
  
  // 转换数据格式
  editForm.equipment_name = item.equipment_name
  editForm.process_name = item.process_name
  editForm.process_id = item.process_id
  editForm.start_time = item.start_time
  editForm.duration_hours = item.duration_hours
  editForm.equipment_category = item.equipment_category || ''
  editForm.equipment_type_name = item.equipment_type_name || ''
  
  // 转换workers格式
  if (item.workers && typeof item.workers === 'object') {
    editForm.workers = Object.entries(item.workers).map(([role, names]) => ({
      role,
      names: Array.isArray(names) ? names.join(', ') : String(names)
    }))
  } else {
    editForm.workers = []
  }
  
  // 转换predecessors格式
  if (item.predecessors && Array.isArray(item.predecessors)) {
    editForm.predecessors = item.predecessors.map(predecessor => {
      if (typeof predecessor === 'object' && predecessor.process_id) {
        return { process_id: predecessor.process_id }
      } else if (typeof predecessor === 'string') {
        return { process_id: predecessor }
      }
      return { process_id: '' }
    }).filter(p => p.process_id)
  } else {
    editForm.predecessors = []
  }
  
  editDialogVisible.value = true
}

// 添加工作人员输入
const addWorker = () => {
  editForm.workers.push({
    role: '',
    names: ''
  })
}

// 移除工作人员输入
const removeWorker = (index) => {
  editForm.workers.splice(index, 1)
}

// 添加工序依赖输入
const addPredecessor = () => {
  editForm.predecessors.push({
    process_id: ''
  })
}

// 移除工序依赖输入
const removePredecessor = (index) => {
  editForm.predecessors.splice(index, 1)
}

// 提交编辑
const submitEdit = async () => {
  if (!editFormRef.value) return
  
  try {
    // 验证表单
    await editFormRef.value.validate()
    
    // 转换数据格式
    const workers = {}
    editForm.workers.forEach(worker => {
      if (worker.role && worker.names) {
        const names = worker.names.split(',').map(name => name.trim()).filter(name => name)
        if (names.length > 0) {
          workers[worker.role] = names
        }
      }
    })
    
    const predecessors = editForm.predecessors
      .filter(predecessor => predecessor.process_id)
      .map(predecessor => ({
        process_id: predecessor.process_id
      }))
    
    const newItem = {
      equipment_name: editForm.equipment_name,
      process_name: editForm.process_name,
      process_id: editForm.process_id,
      start_time: editForm.start_time,
      duration_hours: editForm.duration_hours,
      workers,
      predecessors,
      equipment_category: editForm.equipment_category,
      equipment_type_name: editForm.equipment_type_name
    }
    
    if (editMode.value === 'edit') {
      // 编辑现有项目
      const index = processData.value.findIndex(item => item.process_id === currentItem.value.process_id)
      if (index !== -1) {
        processData.value[index] = newItem
        ElMessage.success('工序更新成功')
      }
    } else {
      // 添加新项目
      const existingIndex = processData.value.findIndex(item => item.process_id === newItem.process_id)
      if (existingIndex !== -1) {
        ElMessage.warning('该工序ID已存在，将更新现有工序')
        processData.value[existingIndex] = newItem
      } else {
        processData.value.push(newItem)
        ElMessage.success('工序添加成功')
      }
    }
    
    // 保存到localStorage
    localStorage.setItem('schedule_plan', JSON.stringify(processData.value))
    
    
    // 关闭对话框
    editDialogVisible.value = false
    
    // 重新构建树形数据
    buildTreeData()
    
    // 重绘甘特图
    nextTick(() => {
      drawConnections()
    })
    
  } catch (error) {
    console.error('表单验证失败:', error)
  }
}

// 重置表单
const resetForm = () => {
  if (editFormRef.value) {
    editFormRef.value.resetFields()
  }
  editForm.workers = []
  editForm.predecessors = []
  currentItem.value = null
  editMode.value = 'edit'
}

// 添加工序
const addNewItem = () => {
  editMode.value = 'create'
  resetForm()
  editForm.start_time = 0
  editForm.duration_hours = 1
  editDialogVisible.value = true
}

// 当设备大类改变时，更新设备类型选项
watch(() => filterForm.category, (newCategory) => {
  filterForm.type = ''
  filterForm.instance = ''
  updateTypeOptions(newCategory)
})

// 当设备类型改变时，清空实例筛选
watch(() => filterForm.type, () => {
  filterForm.instance = ''
})

// 更新设备类型选项
function updateTypeOptions(category) {
  typeOptions.value = []
  if (!category) return
  
  const root = treeData.value[0]
  if (!root || !root.children) return
  
  const categoryNode = root.children.find(cat => cat.label === category)
  if (categoryNode && categoryNode.children) {
    const types = categoryNode.children.map(kind => ({
      value: kind.label,
      label: kind.label
    }))
    typeOptions.value = types
  }
}

// 处理节点点击事件
function handleNodeClick(data) {
  currentNode.value = data
  // 滚动表格到顶部
  if (tableBodyRef.value) {
    tableBodyRef.value.scrollTop = 0
  }
  // 同时滚动甘特图到顶部
  if (ganttChartContentRef.value) {
    ganttChartContentRef.value.scrollTop = 0
  }
}

// 监听数据变化
watch(processData, () => {
  nextTick(() => {
    drawConnections()
  })
}, { deep: true })

watch(filteredAndGroupedProcesses, () => {
  nextTick(() => {
    drawConnections()
  })
})

watch([sortType, sortOrder], () => {
  nextTick(() => {
    drawConnections()
  })
})

onMounted(() => {
  fetchWorkOrders()
  buildTreeData()

  window.addEventListener('resize', debouncedDrawConnections)

  nextTick(() => {
    drawConnections()
  })
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', debouncedDrawConnections)
})

// 防抖函数
function debounce(func, wait) {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

const debouncedDrawConnections = debounce(() => {
  drawConnections()
}, 100)
</script>

<style scoped>
/* ========== 调度控制面板样式 ========== */
.schedule-control-panel {
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 14px 18px;
  margin-bottom: 12px;
  box-shadow: 0 1px 6px rgba(0,0,0,0.06);
  flex-shrink: 0;
}

.control-row {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.control-section {
  display: flex;
  align-items: center;
  gap: 8px;
}

.control-label {
  font-size: 13px;
  color: #606266;
  font-weight: 500;
  white-space: nowrap;
}

.control-buttons {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.stats-row {
  display: flex;
  gap: 10px;
  margin-top: 10px;
  flex-wrap: wrap;
}

.detail-table-wrapper {
  margin-top: 10px;
}

.detail-filter {
  margin-bottom: 8px;
}

/* ========== 甘特图容器适配 ========== */
.gantt-container {
  --row-height: 52px;
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 20px;
  box-sizing: border-box;
  background-color: #f5f7fa;
}

.gantt-content {
  display: flex;
  flex: 1;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background-color: #f0f2f5;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.filter-panel {
  flex: 0 0 200px;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #e0e0e0;
  background-color: white;
  padding: 15px;
  overflow-y: auto;

}

.custom-tree {
  flex: 1;
  overflow-y: auto;
}

.tree-node {
  display: flex;
  align-items: center;
  padding: 5px 0;
}

.tree-node-icon {
  margin-right: 8px;
  font-size: 16px;
  color: #409eff;
}

.chart-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.chart-header {
  padding: 15px;
  background-color: white;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: flex-end;
}

.table-and-chart {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.table-section {
  flex: 0 0 40%;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #e0e0e0;
  background-color: white;
  min-width: 0;
  overflow-x: auto;
}

.table-section.expanded {
  flex: 0 0 40%;
}

.table-header {
  display: flex;
  height: 50px;
  background-color: #f5f7fa;
  border-bottom: 1px solid #e0e0e0;
  font-weight: bold;
  color: #303133;
  flex-shrink: 0;
  min-width: 1000px; /* 从950px增加到990px以适应列宽增加 */
  margin-left:13px;
}

.table-body {
  flex: 1;
  overflow-y: auto;
  overflow-x: auto;
  min-width: 1010px; /* 从950px增加到990px，与表头保持一致 */
  direction: rtl;
  padding-left: 5px;
}

.table-body::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.table-body::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.table-body::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.table-body::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.merged-row {
  display: flex;
  width: 100%;
  line-height: normal;
  direction: ltr;
}

.normal-cells {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.table-row {
  display: flex;
  height: var(--row-height); 
  border-bottom: 1px solid #f0f0f0;
  box-sizing: border-box;
}

.table-row:last-child {
  border-bottom: none;
}

.even-row {
  background-color: #fafafa;
}

.table-cell {
  padding: 8px 12px;
  display: flex;
  align-items: center;
  border-right: 1px solid #f0f0f0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  box-sizing: border-box;
}

.table-cell:last-child {
  border-right: none;
}

.process-cell {
  flex: 0 0 200px;
  display: flex;
  align-items: center;
  padding: 8px 12px;
}

.workers-cell {
  flex: 0 0 200px;
  display: flex;
  align-items: center;
  padding: 8px 12px;
  font-size: 12px;
}

.equipment-cell {
  flex: 0 0 120px;
  justify-content: center;
  font-weight: 500;
  color: #409eff;
  position: relative;
}

.duration-cell {
  flex: 0 0 60px;
  justify-content: center;
  font-weight: 500;
  color: #409eff;
}

.start-time-cell,
.end-time-cell {
  flex: 0 0 120px;
  font-size: 12px;
  color: #606266;
  position: relative;
}

.operation-cell {
  flex: 0 0 100px;
  justify-content: center;
  padding: 8px 4px;
}

.table-header .day-cell {
  flex: 0 0 80px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.merged-day-cell {
  flex: 0 0 80px;
  border-left: 1px solid #606266;
  border-right: 1px solid #606266;
  border-top: 1px solid #606266;
  border-bottom: 1px solid #606266;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f8f9fa;
  font-weight: bold;
  box-shadow: inset 2px 0 4px rgba(0,0,0,0.05);
  box-sizing: border-box;
}

.day-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2px;
}

.day-prefix, .day-suffix {
  writing-mode: vertical-lr;
  font-size: 12px;
}

.day-number {
  writing-mode: horizontal-tb;
  font-size: 14px;
  font-weight: bold;
  color: #303133;
}

/* 操作按钮样式 */
.operation-buttons {
  display: flex;
  gap: 4px;
  justify-content: center;
}

.operation-buttons .el-button {
  padding: 6px;
  min-width: 32px;
  height: 32px;
}

/* 跨天工序样式 */
.split-row {
  background-color: #f0f7ff !important;
  border-left: 3px solid #409eff;
}

.split-row-first {
  border-top: 1px dashed #409eff;
}

.split-row-second {
  border-bottom: 1px dashed #409eff;
}

.no-bottom-border .table-cell {
  border-bottom: none !important;
}

.no-top-border .table-cell {
  border-top: none !important;
}

.split-row .process-cell {
  background-color: #f0f7ff !important;
}

.split-tag {
  margin-left: 8px;
  padding: 2px 6px;
  background-color: #409eff;
  color: white;
  font-size: 10px;
  border-radius: 2px;
  vertical-align: middle;
}

/* 排序图标样式 */
.sort-icon {
  margin-left: 4px;
  cursor: pointer;
  color: #c0c4cc;
  transition: color 0.3s;
}

.sort-icon:hover {
  color: #409eff;
}

.sort-icon .el-icon {
  font-size: 14px;
}

/* 甘特图区域样式 */
.chart-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow-x: auto;
  overflow-y: auto;
  background-color: #f0f2f5;
}

.time-scale-section {
  flex-shrink: 0;
  height: 50px;
  border-bottom: 1px solid #e0e0e0;
  background-color: #f9f9f9;
}

.time-scale {
  display: flex;
  height: 100%;
  width: 100%;
}

.time-scale-hour {
  flex: 1;
  position: relative;
  border-right: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-width: 60px;
}

.time-scale-hour:last-child {
  border-right: none;
}

.hour-label {
  font-size: 12px;
  color: #606266;
  font-weight: 500;
  margin-bottom: 5px;
}

.hour-marker {
  width: 1px;
  height: 8px;
  background-color: #c0c4cc;
}

.gantt-chart-section {
  flex: 1;
  overflow-y: auto;
  overflow-x: auto;
  background-color: #f0f2f5;
  position: relative;
}

.gantt-chart-section::-webkit-scrollbar {
  display: none;
}

.gantt-chart-section {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.gantt-chart-content {
  height: 100%;
  width: 100%;
  position: relative;
}

/* Canvas 连接线样式 */
.connections-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  pointer-events: none;
  z-index: 5;
}

.process-row {
  height: var(--row-height); 
  border-bottom: 1px solid #e0e0e0;
  position: relative;
  background-color: #f0f2f5;
  overflow: visible;
  box-sizing: border-box;
}

.process-row:last-child {
  border-bottom: none;
}

.process-row.even-row {
  background-color: #e6e9ed;
}

.process-bar-container {
  position: absolute;
  width: 100%;
  height: calc(var(--row-height) - 16px); 
  top: 8px;
  left: 0;
  overflow: visible;
  box-sizing: border-box;
}

.process-bar {
  position: absolute;
  height: 100%;
  border-radius: 6px;
  display: flex;
  align-items: center;
  padding: 0 12px;
  box-sizing: border-box;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
  font-size: 12px;
  min-width: 60px;
  z-index: 10;
  margin-top: 0;
}

.process-bar:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.25);
  z-index: 20;
}

.process-bar-label {
  color: white;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.split-bar {
  background: linear-gradient(135deg, #52c41a 0%, #237804 100%) !important;
  border-left: 4px solid #2e7d32 !important;
}

.split-bar-first {
  border-right: 2px solid #ffffff;
}

.split-bar-second {
  border-left: 2px solid #ffffff;
}

.split-bar-tag {
  margin-left: 4px;
  font-size: 10px;
  opacity: 0.9;
}

/* 不同设备的颜色类 */
.equipment-color-0 {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
  box-shadow: 0 2px 6px rgba(255, 107, 107, 0.3);
}

.equipment-color-1 {
  background: linear-gradient(135deg, #4ecdc4 0%, #44a097 100%);
  box-shadow: 0 2px 6px rgba(78, 205, 196, 0.3);
}

.equipment-color-2 {
  background: linear-gradient(135deg, #45b7d1 0%, #3498db 100%);
  box-shadow: 0 2px 6px rgba(69, 183, 209, 0.3);
}

.equipment-color-3 {
  background: linear-gradient(135deg, #f9ca24 0%, #f6b93b 100%);
  box-shadow: 0 2px 6px rgba(249, 202, 36, 0.3);
}

.equipment-color-4 {
  background: linear-gradient(135deg, #6c5ce7 0%, #5f3dc4 100%);
  box-shadow: 0 2px 6px rgba(108, 92, 231, 0.3);
}

.equipment-color-5 {
  background: linear-gradient(135deg, #a29bfe 0%, #8c7ae6 100%);
  box-shadow: 0 2px 6px rgba(162, 155, 254, 0.3);
}

.equipment-color-6 {
  background: linear-gradient(135deg, #fd79a8 0%, #e84393 100%);
  box-shadow: 0 2px 6px rgba(253, 121, 168, 0.3);
}

.equipment-color-7 {
  background: linear-gradient(135deg, #fdcb6e 0%, #e19c24 100%);
  box-shadow: 0 2px 6px rgba(253, 203, 110, 0.3);
}

.equipment-color-8 {
  background: linear-gradient(135deg, #e17055 0%, #d63031 100%);
  box-shadow: 0 2px 6px rgba(225, 112, 85, 0.3);
}

.equipment-color-9 {
  background: linear-gradient(135deg, #00b894 0%, #008c69 100%);
  box-shadow: 0 2px 6px rgba(0, 184, 148, 0.3);
}

.equipment-default {
  background: linear-gradient(135deg, #4a9bff 0%, #2d5aa0 100%);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
}

/* 自定义提示框样式 */
.custom-tooltip {
  position: fixed;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  max-width: 300px;
  transform: translateX(-50%);
}

.tooltip-content {
  font-size: 12px;
  line-height: 1.5;
}

.tooltip-item {
  margin-bottom: 4px;
}

.tooltip-worker {
  margin-left: 8px;
  margin-bottom: 2px;
  color: #606266;
}

.work-time {
  color: #909399;
  font-size: 12px;
}

/* 对话框样式 */
.detail-content {
  padding: 10px 0;
}

.worker-item {
  margin-bottom: 4px;
  font-size: 12px;
}

/* 编辑表单样式 */
.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.worker-input-group {
  width: 100%;
}

.worker-input-row {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.add-worker-btn {
  margin-top: 8px;
}

.predecessor-input-group {
  width: 100%;
}

.predecessor-input-row {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.add-predecessor-btn {
  margin-top: 8px;
}
.time-scale-day {
  flex: 1;
  min-width: 80px;
  text-align: center;
  border-right: 1px solid #e0e0e0;
  display: flex;
  align-items: center;
  justify-content: center;
}
.time-scale-day:last-child {
  border-right: none;
}
.day-label {
  font-size: 12px;
  font-weight: bold;
  color: #303133;
}
</style>
