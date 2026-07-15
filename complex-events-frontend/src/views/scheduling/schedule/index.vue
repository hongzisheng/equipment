<template>
<<<<<<< HEAD
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
=======
  <div class="home-container">
    <!-- 主体三栏布局 -->
    <div class="layout">
      <!-- 右侧：算法与明细 -->
      <div class="right">
        <el-card class="panel-card" shadow="hover">
          <div style="display: flex;">
            <div class="section-title">
    <img src="/src/assets/iconfont/算法选择.png" alt="工单选择" class="panel-icon mr6" /> 
    工单选择
  </div>
          <div class="section-title"><img src="/src/assets/iconfont/算法选择.png" alt="算法选择" class="panel-icon mr6" />目标选择 </div>
          <div class="section-title" ><img src="/src/assets/iconfont/算法选择.png" alt="算法选择" class="panel-icon mr6" />模型选择 </div>
          </div>
         
          <div class="algorithm-target-selection">
            <el-select
    v-model="selectedWorkOrders"
    placeholder="请选择工单"
    class="selection-item"
    :loading="loadingWorkOrders"
    multiple
    clearable
    @change="onWorkOrderChange"
    style="width: 100%;"
  >
    <el-option
      v-for="workOrder in workOrders"
      :key="workOrder.id"
      :label="`${workOrder.order_number} - ${workOrder.title} (${workOrder.equipment_name})`"
      :value="workOrder.id"
    />
  </el-select>
            <el-select v-model="selectedTarget" placeholder="请选择目标" class="selection-item">
              <el-option label="最小化工期" value="minimize_duration" />
              <el-option label="最小化成本" value="minimize_cost" />
              <el-option label="最大化资源利用率" value="maximize_resource_utilization" />
            </el-select>
            <el-select v-model="selectedAlgorithm" placeholder="请选择算法" class="selection-item">
              <el-option v-for="opt in algorithmOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
            </el-select>
          </div>
          <div class="button-group mt8">
            <el-button type="primary" class="schedule-btn" :loading="loadingSchedule"
              @click="runSchedule">生成调度</el-button>
          
            <el-button type="success" @click="savePlan" :loading="saving" class="save-btn">保存方案</el-button>
           <el-button
    v-if="showGanttView"
    type="warning"
    @click="generateWorkOrders"
    :loading="generatingWorkOrders"
    class="generate-workorder-btn"
  >
    发布工单
  </el-button>
          </div>
        </el-card>

        <el-card class="panel-card mt12" shadow="hover">
          <div class="section-title">任务分配明细</div>


          <div class="filter-worker">
            <el-input 
              v-model="workerNameFilter" 
              placeholder="输入工人姓名查看" 
              style="width: 200px; margin-right: 10px;"
              clearable
              @keyup.enter="showWorkerSchedule"
            />
            <el-button type="primary" @click="showWorkerSchedule">查看任务表</el-button>
            
          </div>
          <div class="filter-bar" style="margin-bottom: 16px; display: flex; align-items: center; gap: 12px;">
  <span style="color: #606266; font-weight: 500;">筛选设备：</span>
  <el-select 
    v-model="selectedDeviceFilter" 
    placeholder="请选择设备" 
    clearable 
    style="width: 300px;" 
    @change="handleDeviceFilterChange"
  >
    <!-- 这里的选项是从当前任务数据中提取的 -->
    <el-option 
    v-for="device in [...new Set(assignmentRows?.map(row => row.device) || [])].sort()" 
      :key="device" 
      :label="device" 
      :value="device" 
    />
  </el-select>
  <!-- 提示当前筛选状态 -->
  <span v-if="selectedDeviceFilter" style="color: #409EFF; font-size: 14px;">
    正在查看 "{{ selectedDeviceFilter }}" 的任务
  </span>
</div>
          <el-table 
  :data="paginatedAssignmentRows" 
  style="width: 100%; margin-top: 16px" 
  border 
  stripe
  :row-style="getRowStyle"
>
            <el-table-column prop="task" label="工序" min-width="150"></el-table-column>
            <el-table-column prop="device" label="设备" min-width="120"></el-table-column>
            <el-table-column prop="workersText" label="工人" min-width="200"></el-table-column>
            <el-table-column prop="startTimeFormatted" label="开始时间" min-width="140"></el-table-column>
            <el-table-column prop="endTimeFormatted" label="结束时间" min-width="140"></el-table-column>
            <el-table-column label="操作" min-width="100" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" link @click="openEditWorkers(row)">更换工人</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="pagination-container" style="margin-top: 20px; display: flex; justify-content: flex-end;">
  <el-pagination
    @current-change="handleCurrentChange"
    :current-page="currentPage"
    :page-size="pageSize"
    :total="filteredAssignmentData.length"
    layout="total, prev, pager, next, jumper"
    background
  />
</div>
          <div class="gantt-container">
            <GanttView v-if="showGanttView" class="gantt-view" />
          </div>
        </el-card>
      </div>
    </div>

    <!-- 工人课表弹窗 -->
    <el-dialog
      v-model="showScheduleTable"
      :title="`${workerNameFilter} 的任务课表`"
      width="90%"
      height="80%"
      :fullscreen="false"
    >
      <div class="schedule-table-container">
        <!-- 添加分页控件 -->
        <div class="pagination-controls" style="margin-bottom: 16px; display: flex; justify-content: center; align-items: center;">
          <el-button @click="prevWeek" :disabled="currentWeek <= 1">上一周</el-button>
          <span style="margin: 0 16px;">第 {{ currentWeek }} 周 / 共 {{ totalWeeks }} 周</span>
          <el-button @click="nextWeek" :disabled="currentWeek >= totalWeeks">下一周</el-button>
          <div style="margin-left: 20px;">
            <el-select 
              v-model="selectedScheduleEquipment" 
              placeholder="选择设备" 
              clearable 
              style="width: 200px; margin-right: 10px;"
              @change="currentWeek = 1"
            >
              <el-option
                v-for="option in scheduleEquipmentOptions"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
            <el-button 
              v-for="week in totalWeeks" 
              :key="week"
              @click="goToWeek(week)"
              :type="week === currentWeek ? 'primary' : 'default'"
              style="margin: 0 4px;"
              size="small"
            >
              第{{ week }}周
            </el-button>
          </div>
        </div>
        
        <div class="schedule-table-wrapper">
          <!-- 表头：天数 -->
          <div class="time-column-header">时间</div>
          <div 
            v-for="day in 7" 
            :key="day" 
            class="day-column-header"
          >
            第{{ day }}天
          </div>
          
          <!-- 左侧时间列 -->
          <div class="time-column">
            <div 
              v-for="(time, index) in timeSlots" 
              :key="index" 
              class="time-slot"
            >
              {{ time }}
            </div>
          </div>
          
          <!-- 每天的任务内容 -->
          <div 
            v-for="day in 7" 
            :key="day" 
            class="day-column"
          >
            <!-- 时间槽背景 -->
            <div 
              v-for="(time, index) in timeSlots" 
              :key="index" 
              class="time-slot-bg"
            ></div>
            
            <!-- 任务项 -->
            <div 
              v-for="task in weeklyScheduleTableData[day]" 
              :key="task.processId"
              class="task-item"
              :style="[getTaskPositionStyle(task), { margin: 0, padding: 0 }]"
              :title="`${task.task} (${task.startTimeFormatted} - ${getDisplayEndTime(task.endTimeFormatted)})`"
            >
              <div class="task-content">
                <div class="task-name">{{ task.task }}</div>
                <div class="task-device">{{ task.device }}</div>
                <div class="task-time">{{ task.startTimeFormatted.split(' ')[1] }}-{{ getDisplayEndTime(task.endTimeFormatted).split(' ')[1] }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="closeScheduleTable">关闭</el-button>
        </span>
      </template>
    </el-dialog>
    <el-dialog
      v-model="editWorkerDialogVisible"
      title="更换工人"
      width="700px"
      :close-on-click-modal="false"
    >
      <div v-if="currentEditingTask">
        <el-form label-width="100px">
          <el-form-item
            v-for="(workerList, trade) in editingWorkers"
            :key="trade"
            :label="trade"
          >
            <el-select
              v-model="editingWorkers[trade]"
              filterable
              placeholder="请选择工人"
              style="width: 100%"
            >
              <el-option
                v-for="worker in getAvailableWorkersByTrade(trade)"
                :key="worker.id"
                :label="`${worker.name} (技能等级: ${worker.skill_level})`"
                :value="worker.id"
                :class="{ 'conflict-option': isWorkerConflicted(worker.id) }"
                :title="isWorkerConflicted(worker.id) ? '该工人存在时间冲突' : ''"
              />
            </el-select>
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="editWorkerDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveWorkersEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>

</template>

<script setup>
import { computed, reactive, ref, onBeforeUnmount, watch, nextTick,onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'
import * as XLSX from 'xlsx'
import axios from 'axios'
import request from '@/utils/request'
import GanttView from './GanttView.vue'
const selectedDeviceFilter = ref('')
const currentPage = ref(1)          // 当前页码
const pageSize = ref(10) 
const projectStartDatetime = ref(null)
const selectedWorkOrders = ref([]) // 选中的工单ID列表
const workOrders = ref([]) // 工单列表
const loadingWorkOrders = ref(false) // 工单加载状态
const workerBusyMap = ref(new Map())
const workerPool = ref([]) // 工人池数据
const editWorkerDialogVisible = ref(false)
const currentEditingTask = ref(null)        // 当前正在编辑的任务行
const editingWorkers = ref({})


const saving = ref(false)

async function savePlan() {
  saving.value = true
  try {
    await new Promise((r) => setTimeout(r, 600))
    ElMessage.success('方案已保存')
    
    // 保存完成后自动导出Excel文件
    exportAssignmentToExcel()
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}
async function fetchWorkOrders() {
  loadingWorkOrders.value = true
  try {
    const result = await request({
      url: 'http://localhost:5000/api/work-orders',
      method: 'get',
      headers: {
        Authorization: `Bearer ${localStorage.getItem('token')}`
      }
    })
    
    if (result.success && Array.isArray(result.data)) {
      workOrders.value = result.data
    } else {
      workOrders.value = []
      ElMessage.warning(result.message || '获取工单列表失败')
    }
  } catch (error) {
    console.error('获取工单列表失败:', error)
    ElMessage.error('获取工单列表失败，请检查网络连接')
    workOrders.value = []
>>>>>>> c589649ceb11edd98eb5b9fff54865511d861051
  } finally {
    loadingWorkOrders.value = false
  }
}
<<<<<<< HEAD

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
=======
const filteredAssignmentData = computed(() => {
  let data = assignmentRows.value || []

  // 第一步：根据工人姓名过滤（原有的逻辑）
  if (workerNameFilter.value) {
    const workerName = workerNameFilter.value.trim()
    data = data.filter(row => {
      const workerGroups = row.workersText?.split('；') || []
      return workerGroups.some(group => {
        const parts = group.split(': ')
        if (parts.length > 1) {
          const workersStr = parts[1]
          return workersStr.includes(workerName)
        }
        return false
      })
    })
  }
  if (selectedDeviceFilter.value) {
    data = data.filter(row => row.device === selectedDeviceFilter.value)
  }

  // 排序逻辑保持不变
  return data.sort((a, b) => {
    const dayA = parseInt(a.startTimeFormatted.match(/第(\d+)天/)?.[1] || 0)
    const dayB = parseInt(b.startTimeFormatted.match(/第(\d+)天/)?.[1] || 0)
    if (dayA !== dayB) return dayA - dayB
    return a.startTimeFormatted.localeCompare(b.startTimeFormatted)
  })
})

// 2. 计算当前页显示的数据 (用于表格绑定)
const paginatedAssignmentRows = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredAssignmentData.value.slice(start, end)
})

// 3. 计算总页数
const totalPageCount = computed(() => {
  return Math.ceil(filteredAssignmentData.value.length / pageSize.value) || 1
})
function handleCurrentChange(page) {
  currentPage.value = page
}

// 设备筛选改变时，重置为第一页
function handleDeviceFilterChange() {
  currentPage.value = 1 // 筛选后回到第一页
}
function getAvailableWorkersByTrade(trade) {
  if (!workerPool.value) return [];
  return workerPool.value
    .filter(w => w.type === trade)
    .sort((a, b) => {
      // 将 skill_level 转为数字进行比较，数字越大等级越高，降序排列
      const levelA = Number(a.skill_level) || 0;
      const levelB = Number(b.skill_level) || 0;
      return levelB - levelA;
    });
}
function getRowStyle({ row }) {
  // 兼容多种可能的"待分配"文本格式
  const workersText = row.workersText || '';
  if (workersText.includes('待分配') || workersText.includes('未分配')) {
    return {
      backgroundColor: '#fef0f0',
      color: '#f56c6c'
    };
  }
  return {};
}
function openEditWorkers(row) {
  currentEditingTask.value = row;
  
  const workersObj = row.workers || {};
  const initialEdit = {};
  
  for (const [trade, names] of Object.entries(workersObj)) {
    const ids = [];
    // 防御性处理：确保 names 是数组
    const nameArray = Array.isArray(names) ? names : [names];
    
    for (const name of nameArray) {
      const worker = workerPool.value.find(w => w.type === trade && w.name === name);
      if (worker) {
        ids.push(worker.id);
      } else {
        console.warn(`工人 ${name} (${trade}) 不在工人池中`);
      }
    }
    // 关键：始终将工种对应的值设置为数组
    initialEdit[trade] = ids;
  }
  editingWorkers.value = initialEdit;
  editWorkerDialogVisible.value = true;
}
async function saveWorkersEdit() {
  if (!currentEditingTask.value) return;
  const task = currentEditingTask.value;
  const taskStart = task.startDay;
  const taskEnd = task.endDay;
  const processId = task.processId;

  // 收集新分配的工人信息
  const newWorkerIds = [];
  const newWorkersObj = {};
  const newWorkersTextParts = [];

  for (const [trade, ids] of Object.entries(editingWorkers.value)) {
    const idArray = Array.isArray(ids) ? ids : (ids != null ? [ids] : []);
    const names = [];
    for (const id of idArray) {
      const worker = workerPool.value.find(w => w.id === id);
      if (worker) {
        names.push(worker.name);
        newWorkerIds.push(id);
      }
    }
    if (names.length > 0) {
      newWorkersObj[trade] = names;
      newWorkersTextParts.push(`${trade}: ${names.join('、')}`);
    }
  }
  const allConflicts = []; // 结构: [{ worker, conflicts }]
  for (const workerId of newWorkerIds) {
    const conflicts = findConflictingTasks(workerId, taskStart, taskEnd, processId);
    if (conflicts.length) {
      const worker = workerPool.value.find(w => w.id === workerId);
      allConflicts.push({ worker, conflicts });
    }
  }
  // 如果有冲突，弹出确认框
  if (allConflicts.length > 0) {
    const conflictMessages = allConflicts.map(item => {
      const workerName = item.worker.name;
      const taskNames = item.conflicts.map(c => `「${c.task}」(${c.device})`).join('、');
      return `• ${workerName} 与 ${taskNames} 时间冲突`;
    }).join('\n');

    try {
      await ElMessageBox.confirm(
        `检测到以下时间冲突：\n${conflictMessages}\n\n是否强制分配？确认后将自动从冲突任务中移除该工人，后续请为冲突任务重新分配人员。`,
        '强制分配确认',
        {
          type: 'warning',
          confirmButtonText: '强制分配',
          cancelButtonText: '取消',
          dangerouslyUseHTMLString: false,
        }
      );
    } catch {
      return; // 用户取消，终止操作
    }
  }

  // ========== 执行强制分配 ==========
  // 1. 从冲突任务中移除相关工人
  const affectedTaskNames = new Set(); // 记录受影响的冲突任务名称，用于提示

  for (const item of allConflicts) {
    const workerId = item.worker.id;
    const workerName = item.worker.name;

    for (const conflictTask of item.conflicts) {
      const conflictRow = assignmentRows.value.find(r => r.processId === conflictTask.processId);
      if (!conflictRow) continue;

      // 从 workers 对象中移除该工人
      const newWorkers = { ...conflictRow.workers };
      for (const [trade, names] of Object.entries(newWorkers)) {
        if (Array.isArray(names)) {
          const filtered = names.filter(name => name !== workerName);     
          newWorkers[trade] = filtered;
        }
      }
      conflictRow.workers = newWorkers;

      // 更新 workersText
      const textParts = [];
      for (const [trade, names] of Object.entries(newWorkers)) {
      const nameStr = Array.isArray(names) && names.length > 0 
        ? names.join('、') 
        : '待分配'; // ✅ 无工人时显示“待分配”
      textParts.push(`${trade}: ${nameStr}`);
    }
    conflictRow.workersText = textParts.join('；');

      // 记录受影响的冲突任务名称
      affectedTaskNames.add(`${conflictTask.task} (${conflictTask.device})`);
    }
  }

  // 2. 更新当前编辑任务
  const rowIndex = assignmentRows.value.findIndex(r => r.processId === processId);
  if (rowIndex !== -1) {
    assignmentRows.value[rowIndex].workers = newWorkersObj;
    assignmentRows.value[rowIndex].workersText = newWorkersTextParts.join('；');
  }

  // 3. 同步到 localStorage
  syncSchedulePlanToStorage();

  // 4. 刷新甘特图
  showGanttView.value = false;
  await nextTick();
  showGanttView.value = true;

  // 5. 关闭弹窗并给出最终提示
  editWorkerDialogVisible.value = false;

  if (allConflicts.length > 0) {
    const taskListStr = Array.from(affectedTaskNames).join('、');
    ElMessage.success(`已强制分配。请记得为以下冲突任务重新分配人员：${taskListStr}`);
  } else {
    ElMessage.success('工人更换成功');
  }
}
// 新增方法：工单选择变化处理
function onWorkOrderChange(workOrderId) {
  console.log('选中的工单ID:', workOrderId)
  if (workOrderId) {
    const selectedOrder = workOrders.value.find(order => order.id === workOrderId)
    if (selectedOrder) {
      ElMessage.info(`已选择工单: ${selectedOrder.order_number} - ${selectedOrder.title}`)
      // 这里可以添加选中工单后的其他逻辑，比如根据工单信息预填充某些数据
    }
  }
}
// 在现有响应式变量定义区域添加
const generatingWorkOrders = ref(false)
// 新增方法
async function generateWorkOrders() {
  generatingWorkOrders.value = true
  try {
    const result = await request({
      url: 'http://localhost:5000/api/assign-workers-from-schedule',
      method: 'post',
      headers: {
        Authorization: `Bearer ${localStorage.getItem('token')}`
      }
      // 不需要传递 body，后端自动处理
    })
    if (result.success) {
      ElMessage.success(`工人分配成功！共处理 ${result.assigned_count} 个任务`)
    } else {
      ElMessage.error(result.message || '工人分配失败')
    }
  } catch (error) {
    console.error('工人分配失败:', error)
    ElMessage.error('工人分配失败，请检查后端服务')
>>>>>>> c589649ceb11edd98eb5b9fff54865511d861051
  } finally {
    generatingWorkOrders.value = false
  }
}

<<<<<<< HEAD
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
=======

const devices = ref()
devices.value = JSON.parse(localStorage.getItem('devices'))

const deviceForm = reactive({
  id: 0,
  name: '',
  code: '',
  category: '',
  type: '',

  size: '',
  location: '',
  description: '',
  applications: '',
  status: '正常'
})

const workers = ref()
workers.value = JSON.parse(localStorage.getItem('workers'))
console.log('workers:', workers.value)



const algorithmOptions = [
  { label: 'deepseek', value: 'topological' },
  { label: 'chatGPT—4.5', value: 'greedy' },
  { label: 'Claude', value: 'genetic' },
  { label: 'CodeX', value: 'spt' },
  { label:'通义千问', value:'lowest_cost'}
]
const selectedAlgorithm = ref('topological')
const selectedTarget = ref('minimize_duration') // 添加默认目标选择
const loadingSchedule = ref(false)
const assignmentRows = ref([])
const workerNameFilter = ref('')
const showGanttView = ref(false) // 新增状态控制GanttView显示
const showScheduleTable = ref(false) // 控制课表弹窗显示
const selectedScheduleEquipment = ref('') // 添加设备筛选状态

// 添加计算属性，用于筛选按工人姓名的任务
// 修改filteredAssignmentRows计算属性中的排序逻辑
const filteredAssignmentRows = computed(() => {
  if (!workerNameFilter.value) {
    return assignmentRows.value
  }
  
  const workerName = workerNameFilter.value.trim();
  if (!workerName) {
    return assignmentRows.value
  }
  
  // 筛选逻辑保持不变
  const filtered = assignmentRows.value.filter(row => {
    const workerGroups = row.workersText.split('；');
    for (const group of workerGroups) {
      const parts = group.split(': ');
      if (parts.length > 1) {
        const workersPart = parts[1];
        const workers = workersPart.split('、');
        if (workers.some(worker => worker.includes(workerName))) {
          return true;
        }
      }
    }
    return false;
  })
  
  // 按开始时间中的天数升序排列（提取"第X天"中的数字进行比较）
  return filtered.sort((a, b) => {
    // 从开始时间字符串中提取天数（假设格式如"第1天 08:00"）
    const dayA = parseInt(a.startTimeFormatted.match(/第(\d+)天/)[1], 10);
    const dayB = parseInt(b.startTimeFormatted.match(/第(\d+)天/)[1], 10);
    
    // 先按天数排序
    if (dayA !== dayB) {
      return dayA - dayB;
    }
    
    // 天数相同则按时间排序
    const timeA = a.startTimeFormatted.split(' ')[1];
    const timeB = b.startTimeFormatted.split(' ')[1];
    return timeA.localeCompare(timeB);
  })
})

// 添加课表数据计算属性
const scheduleTableData = computed(() => {
  if (!workerNameFilter.value) return {}
  
  const workerName = workerNameFilter.value.trim()
  if (!workerName) return {}
  
  // 筛选包含该工人的任务
  const workerTasks = assignmentRows.value.filter(row => {
    const workersArray = row.workersText.split('；')
    return workersArray.some(workerGroup => {
      const [type, workersStr] = workerGroup.split(': ')
      if (!workersStr) return false
      return workersStr.includes(workerName)
    })
  })
  
  // 按天数分组任务
  const tasksByDay = {}
  workerTasks.forEach(task => {
    const dayMatch = task.startTimeFormatted.match(/第(\d+)天/)
    if (dayMatch) {
      const day = parseInt(dayMatch[1])
      if (!tasksByDay[day]) {
        tasksByDay[day] = []
      }
      tasksByDay[day].push(task)
    }
  })
  
  return tasksByDay
})

// 获取最大天数


// 获取设备列表用于筛选
const scheduleEquipmentOptions = computed(() => {
  if (!workerNameFilter.value) return []
  
  const workerName = workerNameFilter.value.trim()
  if (!workerName) return []
  
  // 获取该工人的所有任务涉及的设备
  const workerTasks = assignmentRows.value.filter(row => {
    const workersArray = row.workersText.split('；')
    return workersArray.some(workerGroup => {
      const [type, workersStr] = workerGroup.split(': ')
      if (!workersStr) return false
      return workersStr.includes(workerName)
    })
  })
  
  // 提取唯一的设备名称
  const equipmentSet = new Set()
  workerTasks.forEach(task => {
    if (task.device) {
      equipmentSet.add(task.device)
    }
  })
  
  // 转换为选项数组
  return Array.from(equipmentSet).map(equipment => ({
    label: equipment,
    value: equipment
  }))
})

// 添加当前周数状态
const currentWeek = ref(1)

// 修改时间槽计算，只显示当前周的时间
const timeSlots = computed(() => {
  const slots = []
  for (let hour = 8; hour <= 19; hour++) {
    slots.push(`${hour.toString().padStart(2, '0')}:00`)
    slots.push(`${hour.toString().padStart(2, '0')}:30`)
  }
  // 添加最后一小时的结束时间20:00
  slots.push(`20:00`)
  return slots
})

// 修改课表数据计算属性，只返回当前周的数据
const weeklyScheduleTableData = computed(() => {
  if (!workerNameFilter.value) return {}
  
  const workerName = workerNameFilter.value.trim()
  if (!workerName) return {}
  
  // 筛选包含该工人的任务
  let workerTasks = assignmentRows.value.filter(row => {
    const workersArray = row.workersText.split('；')
    return workersArray.some(workerGroup => {
      const [type, workersStr] = workerGroup.split(': ')
      if (!workersStr) return false
      return workersStr.includes(workerName)
    })
  })
  
  // 如果选择了特定设备，则进一步筛选
  if (selectedScheduleEquipment.value) {
    workerTasks = workerTasks.filter(task => task.device === selectedScheduleEquipment.value)
  }
  
  // 按天数分组任务，并只返回当前周的数据
  const tasksByDay = {}
  const startDay = (currentWeek.value - 1) * 7 + 1
  const endDay = currentWeek.value * 7
  
  workerTasks.forEach(task => {
    const dayMatch = task.startTimeFormatted.match(/第(\d+)天/)
    if (dayMatch) {
      const day = parseInt(dayMatch[1])
      // 只处理当前周的天数
      if (day >= startDay && day <= endDay) {
        const weekDay = day - startDay + 1
        if (!tasksByDay[weekDay]) {
          tasksByDay[weekDay] = []
        }
        // 更新任务中的天数信息以适应当前周显示
        const updatedTask = {...task}
        tasksByDay[weekDay].push(updatedTask)
      }
    }
  })
  
  return tasksByDay
})

// 计算总周数
const totalWeeks = computed(() => {
  const days = Object.keys(scheduleTableData.value).map(day => parseInt(day))
  const maxDay = days.length > 0 ? Math.max(...days) : 0
  return Math.ceil(maxDay / 7) || 1
})

// 上一周
function prevWeek() {
  if (currentWeek.value > 1) {
    currentWeek.value--
  }
}

// 下一周
function nextWeek() {
  if (currentWeek.value < totalWeeks.value) {
    currentWeek.value++
  }
}

// 跳转到指定周
function goToWeek(week) {
  if (week >= 1 && week <= totalWeeks.value) {
    currentWeek.value = week
  }
}

// 获取显示用的结束时间
function getDisplayEndTime(endTimeFormatted) {
  // 检查结束时间是否为8:00
  const endMatch = endTimeFormatted.match(/第(\d+)天 08:00/)
  if (endMatch) {
    const day = parseInt(endMatch[1])
    if (day > 1) {
      // 将第n天8:00改为第(n-1)天20:00
      return `第${day - 1}天 20:00`
    }
  }
  return endTimeFormatted
}

// 根据任务时间获取在课表中的位置
function getTaskPosition(task) {
  // 处理特殊情况：如果结束时间是第n天的8:00，应该显示为第(n-1)天的20:00
  let startTimeFormatted = task.startTimeFormatted
  let endTimeFormatted = task.endTimeFormatted
  
  // 检查结束时间是否为8:00
  const endMatch = endTimeFormatted.match(/第(\d+)天 08:00/)
  if (endMatch) {
    const day = parseInt(endMatch[1])
    if (day > 1) {
      // 将第n天8:00改为第(n-1)天20:00
      endTimeFormatted = `第${day - 1}天 20:00`
    }
  }
  
  const startTimeMatch = startTimeFormatted.match(/(\d+):(\d+)$/)
  const endTimeMatch = endTimeFormatted.match(/(\d+):(\d+)$/)
  
  if (!startTimeMatch || !endTimeMatch) return null
  
  const startHour = parseInt(startTimeMatch[1])
  const startMinute = parseInt(startTimeMatch[2])
  const endHour = parseInt(endTimeMatch[1])
  const endMinute = parseInt(endTimeMatch[2])
  
  // 计算开始和结束的时间槽索引（从8:00开始，每半小时一个槽）
  const startIndex = (startHour - 8) * 2 + (startMinute >= 30 ? 1 : 0)
  const endIndex = (endHour - 8) * 2 + (endMinute >= 30 ? 1 : 0)
  
  return {
    startIndex,
    endIndex,
    span: endIndex - startIndex
  }
}

// 获取任务的样式
function getTaskPositionStyle(task) {
  const position = getTaskPosition(task)
  if (!position) return {}
  
  // 每个时间槽高度为40px，与CSS中的.grid-template-rows保持一致
  // 为了精确对齐，top应该等于startIndex * 40px
  const top = position.startIndex * 40
  // 高度应该等于span * 40px，减去2px以留出适当的间隔
  const height = position.span * 40 - 1
  
  // 根据设备ID获取颜色，确保每个设备实例有不同的颜色
  const taskWithEquipmentId = assignmentRows.value.find(row => row.processId === task.processId)
  let backgroundColor = '#ccc' // 默认颜色
  
  if (taskWithEquipmentId && taskWithEquipmentId.equipmentId) {
    // 使用已有的设备颜色映射或创建新的颜色
    if (!equipmentColors.has(taskWithEquipmentId.equipmentId)) {
      equipmentColors.set(taskWithEquipmentId.equipmentId, colorPalette[equipmentColors.size % colorPalette.length])
    }
    backgroundColor = equipmentColors.get(taskWithEquipmentId.equipmentId)
  }
  
  return {
    top: `${top}px`,
    height: `${height}px`,
    backgroundColor: backgroundColor
  }
}

// 显示工人课表
function showWorkerSchedule() {
  if (!workerNameFilter.value.trim()) {
    ElMessage.warning('请输入工人姓名')
    return
  }
  currentWeek.value = 1 // 重置到第一周
  selectedScheduleEquipment.value = '' // 重置设备筛选
  showScheduleTable.value = true
}

// 关闭课表弹窗
function closeScheduleTable() {
  showScheduleTable.value = false
  selectedScheduleEquipment.value = '' // 清除设备筛选
}

function buildWorkerBusyMap(schedulePlan) {
  const map = new Map();
  schedulePlan.forEach(task => {
    const startDay = task.start_time;
    const endDay = task.end_time;
    if (task.workers) {
      for (const [trade, names] of Object.entries(task.workers)) {
        names.forEach(name => {
          const worker = workerPool.value.find(w => w.type === trade && w.name === name);
          if (worker) {
            const slots = map.get(worker.id) || [];
            slots.push({ start: startDay, end: endDay });
            map.set(worker.id, slots);
          }
        });
      }
    }
  });
  workerBusyMap.value = map;
}
// 统计信息相关数据
const equipmentUtilizationData = ref([]) // 设备利用率数据
const workerTypeUtilizationData = ref([]) // 工种利用率数据
const statisticsData = ref({
  total_project_duration_days: 0,
  total_project_duration_hours: 0,
  total_workers: 0,
  total_equipments: 0,
  total_processes: 0
})
function isWorkerConflicted(workerId) {
  if (!currentEditingTask.value) return false;
  const task = currentEditingTask.value;
  const conflicts = findConflictingTasks(
    workerId,
    task.startDay,
    task.endDay,
    task.processId
  );
  return conflicts.length > 0;
}
// 返回冲突任务列表（每个冲突任务包含完整行数据）
function findConflictingTasks(workerId, taskStart, taskEnd, excludeProcessId = null) {
  const conflicts = [];
  for (const row of assignmentRows.value) {
    if (excludeProcessId && row.processId === excludeProcessId) continue;

    // 提取当前任务中所有工人的 ID
    const workerIdsInTask = [];
    if (row.workers) {
      for (const [trade, names] of Object.entries(row.workers)) {
        const nameArray = Array.isArray(names) ? names : [names];
        for (const name of nameArray) {
          const worker = workerPool.value.find(w => w.type === trade && w.name === name);
          if (worker) workerIdsInTask.push(worker.id);
        }
      }
    }

    if (!workerIdsInTask.includes(workerId)) continue;

    // 时间段重叠判断
    if (taskStart < row.endDay && taskEnd > row.startDay) {
      conflicts.push({ ...row }); // 返回副本避免意外修改
    }
  }
  return conflicts;
}
function syncSchedulePlanToStorage() {
  const schedulePlan = JSON.parse(localStorage.getItem('schedule_plan') || '[]');
  assignmentRows.value.forEach(row => {
    const planIndex = schedulePlan.findIndex(p => p.process_id === row.processId);
    if (planIndex !== -1) {
      schedulePlan[planIndex].workers = row.workers;
    }
  });
  localStorage.setItem('schedule_plan', JSON.stringify(schedulePlan));
}
async function runSchedule() {
  loadingSchedule.value = true
  try {
    if (selectedWorkOrders.value.length === 0) {
      ElMessage.warning('请先选择至少一个工单')
      return
    }
    // 调用后端算法API
    const data = await request({
      url: 'http://localhost:5000/api/selected-workers',
      method: 'get'
    })
    const selected_worker = data.selected_workers
    console.log(selected_worker)
    const result = await request({
      url: 'http://localhost:5000/api/run-scheduler',
      method: 'post',
      data: {
        algorithm: selectedAlgorithm.value,
        target: selectedTarget.value,
        selected_worker_ids: selected_worker.map(worker => worker.id),
        work_order_ids: selectedWorkOrders.value
      }
    })
    console.log('调度结果:', result)
    if (result.success) {
      projectStartDatetime.value = result.project_start_datetime
      localStorage.setItem('schedule_plan' , JSON.stringify(result.schedule_plan || []))
      // 处理调度结果
      const workerPoolData = result.worker_pool || {}
      // 将 workerPoolData（按工种分组的格式）转换为前端需要的扁平数组
      const flatWorkers = []
      for (const [trade, workers] of Object.entries(workerPoolData)) {
        workers.forEach(worker => {
          flatWorkers.push({
            ...worker,
            type: trade
          })
        })
      }
      workerPool.value = flatWorkers
      assignmentRows.value = result.schedule_plan?.map(task => {
        const safeWorkers = task.workers && typeof task.workers === 'object' ? task.workers : {};
        const workersArray = Object.entries(safeWorkers).map(([type, workers]) => {
          const workersList = Array.isArray(workers) ? workers : [];
          const names = workersList.length > 0 ? workersList.join('、') : '待分配';
          return `${type}: ${names}`
        })
        return {
          task: task.process_name,
          device: `${task.equipment_name}`,
          processId: task.process_id,
          equipmentId: task.equipment_id,
          workers: safeWorkers,
          workersText: Array.isArray(workersArray) && workersArray.length > 0 ? workersArray.join('；') : '未分配',
          startTimeFormatted: task.start_time_formatted,
          endTimeFormatted: task.end_time_formatted,
          durationHours: task.duration_hours,
          startDay: task.start_time,
          endDay: task.end_time
        }
      }) || []

      // 构建甘特图数据（使用后端真实调度结果）
      buildScheduleRows(result.schedule_plan || [], projectStartDatetime.value)
      useRealSchedule.value = true
      // 设置显示甘特图
      showGanttView.value = false          // 先销毁组件
      await nextTick()                     // 等待 DOM 更新
      showGanttView.value = true 
      buildWorkerBusyMap(result.schedule_plan || []);
      // 处理统计信息
      if (result.statistics) {
        statisticsData.value = result.statistics
      }

      // 处理设备利用率数据
      if (result.equipment_utilization) {
        equipmentUtilizationData.value = result.equipment_utilization
      }

      // 处理工种利用率数据
      if (result.worker_utilization && result.worker_utilization.type_utilization) {
        workerTypeUtilizationData.value = result.worker_utilization.type_utilization
      }
    } else {
      ElMessage.error(result.message || '调度执行失败')
    }
  } catch (error) {
    console.error('调度执行失败:', error)
    ElMessage.error('调度执行失败，请检查后端服务是否启动')
  } finally {
    loadingSchedule.value = false
  }
}

// 导出任务分配明细为Excel文件
function exportAssignmentToExcel() {
  if (!assignmentRows.value || assignmentRows.value.length === 0) {
    ElMessage.warning('没有数据可以导出')
    return
  }

  // 创建工作簿
  const wb = XLSX.utils.book_new()
  
  // 准备第一个工作表的数据 - 按开始时间排序
  const sortedByStartTime = [...assignmentRows.value].sort((a, b) => {
    // 从开始时间字符串中提取天数和时间进行排序
    const dayA = parseInt(a.startTimeFormatted.match(/第(\d+)天/)[1], 10);
    const dayB = parseInt(b.startTimeFormatted.match(/第(\d+)天/)[1], 10);
    
    if (dayA !== dayB) {
      return dayA - dayB;
    }
    
    const timeA = a.startTimeFormatted.split(' ')[1];
    const timeB = b.startTimeFormatted.split(' ')[1];
    return timeA.localeCompare(timeB);
  });
  
  const data1 = sortedByStartTime.map(row => ({
    '任务': row.task,
    '设备': row.device,
    '工序ID': row.processId,
    '设备ID': row.equipmentId,
    '工人': row.workersText,
    '开始时间': row.startTimeFormatted,
    '结束时间': row.endTimeFormatted,
    '工时(h)': row.durationHours
  }));

  // 创建第一个工作表（按开始时间排序）
  const ws1 = XLSX.utils.json_to_sheet(data1)
  ws1['!cols'] = [
    { wch: 20 }, // 任务
    { wch: 20 }, // 设备
    { wch: 15 }, // 工序ID
    { wch: 15 }, // 设备ID
    { wch: 30 }, // 工人
    { wch: 20 }, // 开始时间
    { wch: 20 }, // 结束时间
    { wch: 10 }  // 工时(h)
  ]
  XLSX.utils.book_append_sheet(wb, ws1, '按开始时间排序')

  // 准备第二个工作表的数据 - 按设备分类排序
  const groupedByDevice = {};
  assignmentRows.value.forEach(row => {
    if (!groupedByDevice[row.device]) {
      groupedByDevice[row.device] = [];
    }
    groupedByDevice[row.device].push(row);
  });

  // 对每个设备内的工序按开始时间排序
  Object.keys(groupedByDevice).forEach(device => {
    groupedByDevice[device].sort((a, b) => {
      const dayA = parseInt(a.startTimeFormatted.match(/第(\d+)天/)[1], 10);
      const dayB = parseInt(b.startTimeFormatted.match(/第(\d+)天/)[1], 10);
      
      if (dayA !== dayB) {
        return dayA - dayB;
      }
      
      const timeA = a.startTimeFormatted.split(' ')[1];
      const timeB = b.startTimeFormatted.split(' ')[1];
      return timeA.localeCompare(timeB);
    });
  });

  // 按设备名称排序
  const sortedDevices = Object.keys(groupedByDevice).sort();

  // 创建按设备分类的数据数组，设备之间插入空行
  const data2 = [];
  sortedDevices.forEach((device, index) => {
    // 添加设备内排序好的工序
    groupedByDevice[device].forEach(row => {
      data2.push({
        '任务': row.task,
        '设备': row.device,
        '工序ID': row.processId,
        '设备ID': row.equipmentId,
        '工人': row.workersText,
        '开始时间': row.startTimeFormatted,
        '结束时间': row.endTimeFormatted,
        '工时(h)': row.durationHours
      });
    });
    
    // 如果不是最后一个设备，添加一个空行
    if (index < sortedDevices.length - 1) {
      data2.push({
        '任务': '',
        '设备': '',
        '工序ID': '',
        '设备ID': '',
        '工人': '',
        '开始时间': '',
        '结束时间': '',
        '工时(h)': ''
      });
    }
  });

  // 创建第二个工作表（按设备分类排序）
  const ws2 = XLSX.utils.json_to_sheet(data2)
  ws2['!cols'] = [
    { wch: 20 }, // 任务
    { wch: 20 }, // 设备
    { wch: 15 }, // 工序ID
    { wch: 15 }, // 设备ID
    { wch: 30 }, // 工人
    { wch: 20 }, // 开始时间
    { wch: 20 }, // 结束时间
    { wch: 10 }  // 工时(h)
  ]
  XLSX.utils.book_append_sheet(wb, ws2, '按设备排序')

  // 导出文件
  const filename = '任务分配明细.xlsx'
  XLSX.writeFile(wb, filename)
  
  ElMessage.success('导出成功')
}


const ganttVisible = ref(false)




// 任务数据
const tasks = ref()
tasks.value = JSON.parse(localStorage.getItem('tasks'))
console.log('任务数据:', tasks.value)




// =================== 甘特图 三层交互逻辑（ECharts） ===================
// 层级：overview -> device -> worker
const currentLevel = ref('overview')
const currentDeviceId = ref(null)
const currentDeviceName = ref('')
const currentWorkerInfo = ref(null)
const currentProcessInfo = ref(null)
const currentCategory = ref('')

// 甘特图数据：总览层（设备分类的检修任务段）
// 时间单位以时间戳毫秒为准


// 是否使用真实调度结果驱动甘特图
const useRealSchedule = ref(false)
// 由后端调度结果转换得到的甘特图行
const scheduleGanttRows = ref([])
const equipmentColors = reactive(new Map())
const colorPalette = ['#5470C6', '#91CC75', '#EE6666', '#73C0DE', '#3BA272', '#FC8452', '#9A60B4', '#EA7CCC']



// 根据设备名称推断设备类型
function inferDeviceType(equipmentName) {
  if (!equipmentName) return '未分类'

  const name = equipmentName.toLowerCase()

  // 静设备关键词
  if (name.includes('塔') || name.includes('罐') || name.includes('炉') ||
    name.includes('换热器') || name.includes('容器') || name.includes('反应器')) {
    return '静设备'
  }

  // 动设备关键词
  if (name.includes('泵') || name.includes('压缩机') || name.includes('风机') ||
    name.includes('电机') || name.includes('汽轮机')) {
    return '动设备'
  }

  // 特种设备关键词
  if (name.includes('变压器') || name.includes('开关') || name.includes('仪表') ||
    name.includes('阀门') || name.includes('管道')) {
    return '特种设备'
  }

  return '未分类'
}



function buildScheduleRows(plan, startDateTimeStr) {
  if (!plan || plan.length === 0) return
  equipmentColors.clear()
  const rows = []
  plan.forEach(t => {
    const startDay = t.start_time        // 相对天数（如 0.0, 0.33）
    const endDay = t.end_time
    const color = equipmentColors.get(t.equipment_id) || colorPalette[equipmentColors.size % colorPalette.length]
    if (!equipmentColors.has(t.equipment_id)) {
      equipmentColors.set(t.equipment_id, color)
    }
    rows.push({
      y: t.equipment_name,
      start: startDay,
      end: endDay,
      name: t.process_name,
      color,
      deviceName: t.equipment_name,
      processName: t.process_name,
      workers: t.workers,
      startFormatted: t.start_time_formatted,
      endFormatted: t.end_time_formatted,
      meta: {
        level: 'overview',
        deviceType: inferDeviceType(t.equipment_name),
        deviceName: t.equipment_name,
        processId: t.process_id,
        workers: t.workers,
        startFormatted: t.start_time_formatted,
        endFormatted: t.end_time_formatted
      }
    })
  })
  scheduleGanttRows.value = rows
  saveScheduleGanttRowsToLocalStorage()
}

// 保存scheduleGanttRows到localStorage
function saveScheduleGanttRowsToLocalStorage() {
  try {
    // 创建数据副本并转换Date对象为时间戳
    const rowsToSave = scheduleGanttRows.value.map(row => {
      return {
        ...row,
        start: row.start instanceof Date ? row.start.getTime() : row.start,
        end: row.end instanceof Date ? row.end.getTime() : row.end,
        // meta对象保持不变
        meta: row.meta
      }
    })
    
    localStorage.setItem('scheduleGanttRows', JSON.stringify(rowsToSave))
    console.log('甘特图数据已保存')
  } catch (e) {
    console.error('保存甘特图数据到localStorage失败:', e)
  }
}

function getOverviewOption() {
  if (!useRealSchedule.value || !scheduleGanttRows.value.length) {
    return {
      title: { text: '暂无调度数据，请先执行调度', left: 'center', top: 'center' },
      xAxis: { type: 'value' },
      yAxis: { type: 'category', data: [] },
      series: []
    }
  }

  // 按设备类型分组（同原逻辑）
  const typeMap = new Map()
  scheduleGanttRows.value.forEach(row => {
    const type = row.meta.deviceType || '未分类'
    if (!typeMap.has(type)) {
      typeMap.set(type, { start: row.start, end: row.end, tasks: [] })
    }
    const group = typeMap.get(type)
    group.start = Math.min(group.start, row.start)
    group.end = Math.max(group.end, row.end)
    group.tasks.push(row)
  })

  const dataRows = []
  const yCategories = []
  for (const [type, group] of typeMap.entries()) {
    yCategories.push(type)
    const color = group.tasks[0]?.color || '#409EFF'
    dataRows.push({
      y: type,
      start: group.start,
      end: group.end,
      name: `${type}检修`,
      color: color,
      meta: { level: 'overview', category: type, deviceType: type }
    })
  }

  const legendData = yCategories.map(name => ({
    name: name,
    itemStyle: { color: dataRows.find(r => r.y === name)?.color || '#ccc' }
  }))

  return {
    title: { text: '三层交互式检修进度甘特图（按设备类型）', left: 10, top: 10, textStyle: { fontSize: 16, fontWeight: 'bold' } },
    backgroundColor: '#fafafa',
    legend: { type: 'plain', orient: 'vertical', right: 20, top: 60, data: legendData, textStyle: { fontSize: 12 } },
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        const v = params.value
        if (!v) return ''
        const startDay = Math.floor(v[1]) + 1;   // 开始天数
    const endDay = Math.floor(v[2]) + 1;     // 结束天数
    return `工序: ${v[3]}<br/>开始: 第${startDay}天<br/>结束: 第${endDay}天`;
      },
      backgroundColor: 'rgba(0,0,0,0.8)'
    },
    grid: { left: 100, right: 160, top: 100, bottom: 60, containLabel: true },
    xAxis: {
      type: 'value',
      name: '调度天数',
      axisLabel: {
        formatter: (value) => {
          const day = Math.floor(value) + 1
          return `第${day}天`
        }
      },
      splitLine: { show: true, lineStyle: { color: '#e5e5e5', type: 'dashed' } }
    },
    yAxis: { type: 'category', data: yCategories, axisLabel: { fontSize: 13 } },
    series: buildCustomSeries(dataRows, yCategories)
  }
}

const ganttEl = ref(null)
let chart = null
let ro = null // ResizeObserver

function buildCustomSeries(dataRows, yCategories) {
  const seriesData = dataRows.map((r, index) => {
    const yIndex = yCategories.indexOf(r.y)
    if (yIndex < 0) return null
    return [yIndex, r.start, r.end, r.name, r.meta, r.color]
  }).filter(item => item !== null)

  return [{
    type: 'custom',
    name: '设备进度',
    silent: false,
    triggerEvent: true,
    renderItem(params, api) {
      const yIndex = api.value(0)
      const startDay = api.value(1)
      const endDay = api.value(2)
      const color = api.value(5)

      const startCoord = api.coord([startDay, yIndex])
      const endCoord = api.coord([endDay, yIndex])
      const height = api.size([0, 1])[1] * 0.4
      const y = startCoord[1] - height / 2
      const x = startCoord[0]
      const width = Math.max(3, endCoord[0] - startCoord[0])

      return {
        type: 'rect',
        shape: { x, y, width, height },
        style: { fill: color },
        emphasis: { style: { fill: color, opacity: 0.8 } }
      }
    },
    encode: { x: [1, 2], y: 0 },
    data: seriesData
  }]
}

function renderChart() {
  console.log('开始渲染甘特图，ganttEl.value:', ganttEl.value)
  if (!ganttEl.value) {
    console.error('甘特图容器元素不存在')
    return
  }
  if (!chart) {
    chart = echarts.init(ganttEl.value)
    console.log('ECharts 实例已初始化，准备注册点击事件。') // 调试信息
  }

  // 确保事件绑定在每次渲染时都重新绑定
  if (chart) {
    // 先移除旧的事件监听器
    chart.off('click')

    // 甘特图点击事件处理
    chart.on('click', (params) => {
      console.log('=== 甘特图点击事件触发 ===')
      console.log('点击事件参数:', params)

      // 简单的点击测试
      ElMessage.success('甘特图被点击了！')

      // 检查数据结构
      if (params.value && params.value.length >= 5) {
        const meta = params.value[4]
        console.log('点击元数据:', meta)

        if (meta && meta.level === 'overview') {
          // 真实数据：点击类别 -> 第二层
          if (useRealSchedule.value) {
            currentLevel.value = 'device'
            currentCategory.value = meta.category || meta.deviceName || ''
            updateChart()
            return
          }
          console.log('点击总览层，设备ID:', meta.deviceId)
          if (meta.deviceId === 1) { // 静设备
            currentLevel.value = 'device'
            currentDeviceId.value = meta.deviceId
            currentDeviceName.value = meta.deviceName
            console.log('切换到设备层')
            updateChart()
          } else if (meta.deviceId === 2) { // 动设备
            currentLevel.value = 'device'
            currentDeviceId.value = meta.deviceId
            currentDeviceName.value = meta.deviceName
            console.log('切换到设备层')
            updateChart()
          } else if (meta.deviceId === 3) { // 特种设备
            currentLevel.value = 'device'
            currentDeviceId.value = meta.deviceId
            currentDeviceName.value = meta.deviceName
            console.log('切换到设备层')
            updateChart()
          } else {
            // 其他设备类型暂时显示总览
            ElMessage.info('该设备类型暂未开放详细视图')
          }
        } else if (meta && meta.level === 'device') {
          // 真实数据：点击某台设备 -> 第三层（展示工序详情）
          if (useRealSchedule.value) {
            currentLevel.value = 'worker'
            currentDeviceName.value = meta.deviceName
            currentWorkerInfo.value = { requiredTrade: '工序详情', processName: meta.deviceName }
            updateChart()
            ElMessage.info(`查看设备: ${meta.deviceName} 的工序详情`)
            return
          }
          console.log('点击设备层工序')
          // 设置当前工序信息
          currentProcessInfo.value = {
            deviceName: meta.deviceName,
            processName: params.value[3],
            requiredTrade: meta.requiredTrade
          }
          // 切换到第三层工人详情
          currentLevel.value = 'worker'
          currentWorkerInfo.value = {
            requiredTrade: meta.requiredTrade,
            processName: params.value[3]
          }
          console.log('切换到工人层:', currentWorkerInfo.value)
          updateChart()
        } else if (meta && meta.level === 'worker') {
          console.log('点击工人层')
          // 显示工人详情
          ElMessage.info(`工人详情: ${meta.worker.name} - ${meta.worker.level}`)
        } else {
          console.log('未识别的点击类型或缺少元数据')
        }
      } else {
        console.log('点击数据格式不正确:', params.value)
      }
    })
  }

  updateChart()
}


function updateChart() {
  console.log('更新甘特图，当前层级:', currentLevel.value)
  if (!chart) {
    console.error('图表实例不存在')
    return
  }

  let option = null
  if (currentLevel.value === 'overview') {
    option = getOverviewOption()
    console.log('使用总览层配置:', option)
  } else if (currentLevel.value === 'device') {
    option = getStaticDeviceOption()
    console.log('使用设备层配置:', option)
  } else if (currentLevel.value === 'worker') {
    option = getWorkerOption(currentWorkerInfo.value?.requiredTrade || '工序详情')
    console.log('使用工人层配置:', option)
  }

  if (option) {
    chart.setOption(option, true)
    console.log('甘特图配置已应用')
  }

  nextTick(() => {
    if (chart) {
      chart.resize()
      console.log('甘特图已调整大小')
    }
  })
}



function setupResize() {
  if (!ganttEl.value) return
  ro = new ResizeObserver(() => {
    chart && chart.resize()
  })
  ro.observe(ganttEl.value)
  window.addEventListener('resize', onWindowResize)
}
function teardownResize() {
  window.removeEventListener('resize', onWindowResize)
  if (ro) { ro.disconnect(); ro = null }
}
function onWindowResize() { chart && chart.resize() }

watch(ganttVisible, async (val) => {
  if (val) {
    await nextTick()
    currentLevel.value = 'overview'
    renderChart()
    setupResize()
  } else {
    teardownResize()
    if (chart) { chart.dispose(); chart = null }
  }
})

onBeforeUnmount(() => {
  teardownResize()
  if (chart) { chart.dispose(); chart = null }
})

function getStaticDeviceOption() {
  if (!useRealSchedule.value || !scheduleGanttRows.value.length) {
    return {
      title: { text: '暂无设备数据', left: 'center', top: 'center' },
      xAxis: { type: 'value' },
      yAxis: { type: 'category', data: [] },
      series: []
    }
  }

  // 筛选当前类别的任务
  const categoryRows = scheduleGanttRows.value.filter(
    row => row.meta.deviceType === currentCategory.value
  )
  if (categoryRows.length === 0) {
    return {
      title: { text: `${currentCategory.value} 类别下无设备数据`, left: 'center', top: 'center' },
      xAxis: { type: 'value' },
      yAxis: { type: 'category', data: [] },
      series: []
    }
  }

  // 按设备名称分组
  const deviceMap = new Map()
  categoryRows.forEach(row => {
    const deviceName = row.deviceName
    if (!deviceMap.has(deviceName)) {
      deviceMap.set(deviceName, { start: row.start, end: row.end, tasks: [] })
    }
    const group = deviceMap.get(deviceName)
    group.start = Math.min(group.start, row.start)
    group.end = Math.max(group.end, row.end)
    group.tasks.push(row)
  })

  const dataRows = []
  const yCategories = []
  for (const [deviceName, group] of deviceMap.entries()) {
    yCategories.push(deviceName)
    const color = group.tasks[0]?.color || '#1890ff'
    dataRows.push({
      y: deviceName,
      start: group.start,
      end: group.end,
      name: deviceName,
      color: color,
      meta: { level: 'device', deviceName: deviceName, category: currentCategory.value }
    })
  }

  const legendData = yCategories.map(name => ({
    name: name,
    itemStyle: { color: dataRows.find(r => r.y === name)?.color || '#ccc' }
  }))

  return {
    title: {
      text: `${currentCategory.value} - 设备列表`,
      left: 10,
      top: 10,
      textStyle: { fontSize: 16, fontWeight: 'bold', color: '#000' }
    },
    backgroundColor: '#fafafa',
    legend: {
      type: 'plain',
      orient: 'vertical',
      right: 20,
      top: 60,
      selectedMode: false,
      data: legendData,
      textStyle: { fontSize: 12, color: '#333' },
      itemWidth: 20,
      itemHeight: 14,
      itemGap: 10
    },
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        const v = params.value
        if (!v) return ''
        const startDay = Math.floor(v[1]) + 1;
    const endDay = Math.floor(v[2]) + 1;
    return `工序: ${v[3]}<br/>开始: 第${startDay}天<br/>结束: 第${endDay}天`;
      },
      backgroundColor: 'rgba(0,0,0,0.8)',
      borderColor: '#333',
      textStyle: { color: '#fff' }
    },
    grid: {
      left: 100,
      right: 160,
      top: 100,
      bottom: 60,
      containLabel: true
    },
    xAxis: {
      type: 'value',
      axisLabel: {
        formatter: (value) => {
          const day = Math.floor(value) + 1; // 将相对天数转为“第X天”，假设项目从第1天开始
    return `第${day}天`;
        },
        fontSize: 11,
        color: '#666'
      },
      splitLine: { show: true, lineStyle: { color: '#e5e5e5', type: 'dashed' } },
      axisLine: { lineStyle: { color: '#d0d0d0' } },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'category',
      data: yCategories,
      axisLabel: { fontSize: 13, fontWeight: '500', color: '#333' },
      axisLine: { lineStyle: { color: '#d0d0d0' } },
      axisTick: { show: false }
    },
    series: buildCustomSeries(dataRows, yCategories)
  }
}

function getWorkerOption(requiredTrade) {
  // 注意：requiredTrade 参数在真实调度中可能不再使用，这里改为显示当前选中设备的工序
  if (!useRealSchedule.value || !scheduleGanttRows.value.length) {
    return {
      title: { text: '暂无工序数据', left: 'center', top: 'center' },
      xAxis: { type: 'value' },
      yAxis: { type: 'category', data: [] },
      series: []
    }
  }

  // 获取当前选中设备的所有工序
  const deviceRows = scheduleGanttRows.value.filter(
    row => row.deviceName === currentDeviceName.value
  )
  if (deviceRows.length === 0) {
    return {
      title: { text: `${currentDeviceName.value} 无工序数据`, left: 'center', top: 'center' },
      xAxis: { type: 'value' },
      yAxis: { type: 'category', data: [] },
      series: []
    }
  }

  // 按工序名称分组（通常每个工序独立显示）
  const dataRows = deviceRows.map(row => ({
    y: row.processName,
    start: row.start,
    end: row.end,
    name: row.processName,
    color: row.color,
    meta: {
      level: 'worker',
      deviceName: row.deviceName,
      processName: row.processName,
      workers: row.workers
    }
  }))

  const yCategories = dataRows.map(r => r.y)
  const legendData = yCategories.map(name => ({
    name: name,
    itemStyle: { color: dataRows.find(r => r.y === name)?.color || '#ccc' }
  }))

  return {
    title: {
      text: `${currentDeviceName.value} - 工序详情`,
      left: 10,
      top: 10,
      textStyle: { fontSize: 16, fontWeight: 'bold', color: '#000' }
    },
    backgroundColor: '#fafafa',
    legend: {
      type: 'plain',
      orient: 'vertical',
      right: 20,
      top: 60,
      selectedMode: false,
      data: legendData,
      textStyle: { fontSize: 12, color: '#333' },
      itemWidth: 20,
      itemHeight: 14,
      itemGap: 10
    },
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        const v = params.value
        if (!v) return ''
        const startDay = Math.floor(v[1]) + 1;
    const endDay = Math.floor(v[2]) + 1;
    const meta = v[4];
    let workersInfo = '';
    if (meta && meta.workers) {
      const workerList = [];
      Object.entries(meta.workers).forEach(([trade, names]) => {
        if (Array.isArray(names) && names.length) {
          workerList.push(`${trade}: ${names.join('、')}`);
        }
      });
      workersInfo = workerList.length ? `<br/>工人:<br/>${workerList.join('<br/>')}` : '';
    }
    return `工序: ${v[3]}<br/>开始: 第${startDay}天<br/>结束: 第${endDay}天${workersInfo}`;
  },
  backgroundColor: 'rgba(0,0,0,0.8)',
  borderColor: '#333',
  textStyle: { color: '#fff' }
    },
    grid: {
      left: 100,
      right: 160,
      top: 100,
      bottom: 60,
      containLabel: true
    },
    xAxis: {
      type: 'value',
      axisLabel: {
        formatter: (value) => {
          const day = Math.floor(value) + 1; // 将相对天数转为“第X天”，假设项目从第1天开始
    return `第${day}天`;
        },
        fontSize: 11,
        color: '#666'
      },
      splitLine: { show: true, lineStyle: { color: '#e5e5e5', type: 'dashed' } },
      axisLine: { lineStyle: { color: '#d0d0d0' } },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'category',
      data: yCategories,
      axisLabel: { fontSize: 13, fontWeight: '500', color: '#333' },
      axisLine: { lineStyle: { color: '#d0d0d0' } },
      axisTick: { show: false }
    },
    series: buildCustomSeries(dataRows, yCategories)
  }
}
onMounted(() => {
  fetchWorkOrders();
});
</script>

<style scoped>
/* 全局CSS变量定义 */
:root {
  --primary-color: #409EFF;
  --success-color: #67C23A;
  --warning-color: #E6A23C;
  --error-color: #F56C6C;
  --bg-color: #f8f9fa;
  --card-bg: #ffffff;
  --border-color: #e4e7ed;
  --text-primary: #303133;
  --text-secondary: #606266;
  --text-muted: #909399;
}

/* 全局平滑过渡 */
* {
  transition: color 0.3s ease, background-color 0.3s ease, border-color 0.3s ease, transform 0.3s ease, box-shadow 0.3s ease;
}

.home-container {
  min-height: 100vh;
  padding: 20px 24px;
  background-color: #ffffff;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
}

.top-bar {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  margin-bottom: 20px;
  background: #ffffff !important;
  color: #303133;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid #e4e7ed;
}

.brand .title {
  color: var(--text-primary);
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.025em;
}

.actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.button-group {
  display: flex;
  gap: 12px;
}

.button-group .schedule-btn,
.button-group .gantt-btn,
.button-group .save-btn {
  align-items: center;
  justify-content: center;
  width: 5vw;
}

.layout {
  display: grid;
  grid-template-columns: 320px 1fr 380px;
  gap: 20px;
  height: calc(100vh - 140px);
}

.left,
.center {

  min-width: 0;
  display: flex;
  flex-direction: column;
  height: 83vh;
  width: 20vw;
  margin-left: 50vw;
  overflow: auto;
}

.right {
  width: 60vw;

}

.panel-card {
  background: #ffffff !important;
  border: 1px solid #e4e7ed;
  border-radius: 16px;
  box-shadow:
    0 2px 8px rgba(0, 0, 0, 0.06),
    0 1px 4px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  overflow: auto;
  width: 85vw;
}

.panel-card:hover {
  box-shadow:
    0 8px 24px rgba(0, 0, 0, 0.12),
    0 4px 12px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.panel-header {
  background: linear-gradient(90deg, #fafbfc 0%, #f8f9fa 100%);
  border-radius: 16px 16px 0 0;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
  margin-bottom: 0;
}

.panel-header:hover {
  background: linear-gradient(90deg, #f8f9fa 0%, #f5f6f8 100%);
}

.panel-title {
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  font-size: 16px;
}

.panel-title .el-icon {
  color: var(--primary-color);
  font-size: 18px;
  margin-right: 8px;
}

.panel-tools {
  display: flex;
  gap: 8px;
  align-items: center;
}

.panel-body {
  padding: 20px;
}

/* 间距工具类 */
.mr6 {
  margin-right: 6px;
}

.mx8 {
  margin: 0 8px;
}

.mr4 {
  margin-right: 4px;
}

.ml4 {
  margin-left: 4px;
}

.mt8 {
  margin-top: 8px;
}

.mt12 {
  margin-top: 12px;
}

.mb8 {
  margin-bottom: 8px;
}

.w100 {
  width: 100%;
}

.map-card {
  height: 100%;
  border-radius: 16px;
  overflow: auto;
}

.map-placeholder {
  height: 100%;
  border-radius: 8px;
  background: repeating-linear-gradient(45deg, #f7f9fc, #f7f9fc 10px, #f2f5fb 10px, #f2f5fb 20px);
  border: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #606266;
  font-weight: 500;
  font-size: 16px;
  transition: all 0.3s ease;
}

.map-placeholder::before {
  content: "🗺️";
  font-size: 24px;
  margin-right: 8px;
}

.map-placeholder:hover {
  border-color: var(--primary-color);
  color: var(--text-secondary);
  background-color: rgba(22, 119, 255, 0.05);
}

.gantt-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(90deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 12px;
  padding: 12px 16px;
  margin-bottom: 16px;
  border: 1px solid var(--border-color);
}

.gantt-chart {
  height: 500px;
}

/* 工人筛选区域 */
.filter-worker {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  gap: 10px;
}

/* 课表样式 */
.schedule-table-container {
  width: 100%;
  overflow: auto;
  max-height: 70vh;
}

.schedule-table-wrapper {
  display: grid;
  grid-template-columns: 80px repeat(7, 1fr);
  grid-template-rows: 40px repeat(24, 40px);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  min-width: calc(80px + 7 * 150px);
}

.schedule-header {
  display: contents;
}

.schedule-content {
  display: contents;
}

.time-column-header,
.day-column-header {
  background-color: #f5f7fa;
  padding: 10px;
  text-align: center;
  font-weight: bold;
  border-right: 1px solid var(--border-color);
  border-bottom: 1px solid var(--border-color);
  min-height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.time-column {
  grid-column: 1;
  grid-row: 2 / -1;
  border-right: 1px solid var(--border-color);
}

.day-column {
  grid-row: 2 / -1;
  border-right: 1px solid var(--border-color);
  position: relative;
}

.time-slot-bg {
  height: 40px;
  border-bottom: 1px solid var(--border-color);
}

.time-slot {
  padding: 5px;
  border-bottom: 1px solid var(--border-color);
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 40px;
  box-sizing: border-box;
  transform: translateY(2px); /* 向下移动2px */
}

.task-item {
  position: absolute;
  left: 2px;
  right: 2px;
  background-color: #409EFF;
  color: white;
  border-radius: 4px;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2px;
  overflow: hidden;
  box-sizing: border-box;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  transform: translateY(20px); /* 向下移动20px */
}

.task-content {
  font-size: 12px;
  text-align: center;
  width: 100%;
  padding: 2px;
  box-sizing: border-box;
}

.task-name {
  font-weight: bold;
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.task-device,
.task-time {
  font-size: 11px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.pagination-controls {
  padding: 10px 0;
  text-align: center;
}

.dialog-footer {
  text-align: right;
}

.gantt-chart {
  border-radius: 12px;
  background: #fafafa;
  border: 1px solid var(--border-color);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.process-brief {
  margin-top: 12px;
  padding: 12px 16px;
  background: linear-gradient(90deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 8px;
  color: var(--text-secondary);
  font-size: 14px;
  border: 1px solid var(--border-color);
}

.worker-brief {
  margin-top: 12px;
  padding: 12px 16px;
  background: linear-gradient(90deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 8px;
  color: var(--text-secondary);
  font-size: 14px;
  display: flex;
  gap: 16px;
  border: 1px solid var(--border-color);
}

/* 任务管理模块样式 */
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;


  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
}

.section-actions {
  display: flex;
  gap: 8px;
}

.filter-toolbar {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
  padding: 16px;
  background: linear-gradient(90deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 12px;
  border: 1px solid var(--border-color);
}

.filter-toolbar .el-input,
.filter-toolbar .el-select {
  width: 100%;
}
/* 待分配任务行标红 */
:deep(.warning-row) {
  background-color: #fef0f0 !important;
}

:deep(.warning-row:hover > td) {
  background-color: #fde2e2 !important;
}
.mr8 {
  margin-right: 8px;
}

.text-danger {
  color: var(--error-color);
}

.task-detail {
  padding: 16px 0;
}

.detail-row {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-color);
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-row .label {
  font-weight: 600;
  color: var(--text-secondary);
  min-width: 100px;
  font-size: 14px;
}

.detail-row .value {
  color: var(--text-primary);
  flex: 1;
  font-size: 14px;
}

.section-title {
  font-weight: 600;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  font-size: 16px;
  color: var(--text-primary);
  flex: 1;
  text-align: center;
  margin: 0 8px;
}

.section-title .el-icon {
  font-size: 16px;
  color: var(--primary-color);
  margin-right: 8px;
}

/* 增强的表格和卡片样式 */
:deep(.el-card) {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

:deep(.el-card:hover) {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

:deep(.el-table) {
  border-radius: 12px;
  overflow: auto;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}

:deep(.el-table th) {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  color: var(--text-secondary);
  font-weight: 600;
  border-bottom: 2px solid #e2e8f0;
  font-size: 14px;
}

:deep(.el-table tr:hover) {
  background-color: #f8fafc;
}

:deep(.el-table--small .el-table__cell) {
  padding: 8px 12px;
  font-size: 13px;
}

:deep(.el-table__body td) {
  border-bottom: 1px solid var(--border-color);
}

/* 按钮样式现代化 */
:deep(.el-button) {
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
}

:deep(.el-button--primary) {
  background: var(--primary-color);
  border: 1px solid var(--primary-color);
  color: white;
  box-shadow: 0 2px 4px rgba(64, 158, 255, 0.2);
}

:deep(.el-button--primary:hover) {
  background: #66b1ff;
  border-color: #66b1ff;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.4);
}

:deep(.el-button--success) {
  background: var(--success-color);
  border: 1px solid var(--success-color);
  color: white;
  box-shadow: 0 2px 4px rgba(103, 194, 58, 0.2);
}

:deep(.el-button--success:hover) {
  background: #85ce61;
  border-color: #85ce61;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(103, 194, 58, 0.4);
}

:deep(.el-button.is-text) {
  color: var(--primary-color);
  padding: 4px 8px;
}

:deep(.el-button.is-text:hover) {
  background-color: rgba(64, 158, 255, 0.1);
}

:deep(.el-button--primary.is-plain) {
  background: white;
  border: 1px solid var(--primary-color);
  color: var(--primary-color);
}

:deep(.el-button--primary.is-plain:hover) {
  background: var(--primary-color);
  color: white;
}

/* 数据导入按钮样式 - 蓝色边框按钮 */
.import-btn {
  background: white !important;
  border: 1px solid #409EFF !important;
  color: #409EFF !important;
  font-weight: 500;
}

.import-btn:hover {
  background: #409EFF !important;
  color: white !important;
  border-color: #409EFF !important;
}

/* 保存方案按钮样式 - 绿色按钮 */
.save-btn {
  background: #67C23A !important;
  border: 1px solid #67C23A !important;
  color: white !important;
  font-weight: 500;
}

.save-btn:hover {
  background: #85ce61 !important;
  border-color: #85ce61 !important;
  color: white !important;
}

/* 发布工单按钮样式 - 橙色按钮 */
.publish-btn {
  background: #E6A23C !important;
  border: 1px solid #E6A23C !important;
  color: white !important;
  font-weight: 500;
}

.publish-btn:hover {
  background: #ebb563 !important;
  border-color: #ebb563 !important;
  color: white !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(230, 162, 60, 0.3);
}

.publish-btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 6px rgba(230, 162, 60, 0.2);
}

/* 标签状态颜色优化 */
:deep(.el-tag) {
  border-radius: 6px;
  font-weight: 500;
  border: none;
  font-size: 12px;
}

:deep(.el-tag--success) {
  background: linear-gradient(135deg, var(--success-color) 0%, #73d13d 100%);
  color: white;
}

:deep(.el-tag--warning) {
  background: linear-gradient(135deg, var(--warning-color) 0%, #ffc53d 100%);
  color: white;
}

:deep(.el-tag--danger) {
  background: linear-gradient(135deg, var(--error-color) 0%, #ff7875 100%);
  color: white;
}

:deep(.el-tag--info) {
  background: linear-gradient(135deg, #1890ff 0%, #40a9ff 100%);
  color: white;
}

/* 输入框和选择器样式 */
:deep(.el-input),
:deep(.el-select) {
  border-radius: 8px;
}

:deep(.el-input__wrapper) {
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  transition: all 0.3s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

:deep(.el-input__wrapper:hover) {
  border-color: var(--primary-color);
}

:deep(.el-input__wrapper.is-focus) {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(22, 119, 255, 0.1);
}

:deep(.el-select .el-select__wrapper) {
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  transition: all 0.3s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

:deep(.el-select .el-select__wrapper:hover) {
  border-color: var(--primary-color);
}

/* 加载状态美化 */
:deep(.el-loading-mask) {
  border-radius: 12px;
  background-color: rgba(255, 255, 255, 0.9);
}

:deep(.el-loading-spinner .circular) {
  background: linear-gradient(135deg, var(--primary-color) 0%, #4096ff 100%);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* 卡片展开收起动画 */
:deep(.el-collapse-transition) {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 响应式布局优化 */
@media (max-width: 1400px) {
  .home-container {
    padding: 16px 20px;
  }

  .layout {
    grid-template-columns: 280px 1fr 320px;
    gap: 16px;
  }
}

@media (max-width: 1200px) {
  .home-container {
    padding: 16px;
  }

  .layout {
    grid-template-columns: 1fr;
    gap: 16px;
    height: auto;
  }

  .left,
  .center {
    height: auto;
    min-height: 400px;

  }

  .map-placeholder {
    height: 300px;
  }

  .top-bar {
    height: 56px;
    padding: 0 16px;
  }

  .brand .title {
    font-size: 18px;
  }

  .actions {
    gap: 8px;
  }

  .panel-card {
    margin-bottom: 16px;
  }
}

@media (max-width: 768px) {
  .home-container {
    padding: 12px;
  }

  .top-bar {
    flex-direction: column;
    height: auto;
    padding: 16px;
    gap: 12px;
    border-radius: 12px;
  }

  .actions {
    width: 100%;
    justify-content: center;
    flex-wrap: wrap;
  }

  .brand .title {
    font-size: 16px;
  }

  .layout {
    gap: 12px;
  }

  .panel-header {
    padding: 12px 16px;
  }

  .panel-body {
    padding: 16px;
  }

  .filter-toolbar {
    padding: 12px;
  }

  .map-placeholder {
    height: 250px;
    font-size: 14px;
  }

  /* 移动端优化表格 */
  :deep(.el-table) {
    font-size: 12px;
  }

  :deep(.el-table__header-wrapper th) {
    padding: 8px 4px;
    font-size: 12px;
  }

  :deep(.el-table__body td) {
    padding: 8px 4px;
    font-size: 12px;
  }

  /* 移动端对话框优化 */
  :deep(.el-dialog) {
    width: 95% !important;
    margin: 10px auto;
  }

  .detail-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }

  .detail-row .label {
    min-width: auto;
  }

  .worker-brief {
    flex-direction: column;
    gap: 8px;
    text-align: center;
  }
}

@media (max-width: 480px) {
  .home-container {
    padding: 8px;
  }

  .top-bar {
    padding: 12px;
  }

  .brand .title {
    font-size: 14px;
  }

  .panel-header {
    padding: 8px 12px;
  }

  .panel-body {
    padding: 12px;
  }

  .filter-toolbar {
    padding: 8px;
  }

  .map-placeholder {
    height: 200px;
    font-size: 12px;
  }

  /* 超小屏幕表格 */
  :deep(.el-table__header-wrapper th) {
    padding: 6px 2px;
    font-size: 11px;
  }

  :deep(.el-table__body td) {
    padding: 6px 2px;
    font-size: 11px;
  }
}

/* 高分辨率屏幕优化 */
@media (min-width: 1600px) {
  .home-container {
    padding: 24px 32px;
  }

  .layout {
    grid-template-columns: 360px 1fr 420px;
    gap: 24px;
  }
}

/* 深色模式支持（可选） */
@media (prefers-color-scheme: white) {
  :root {
    --primary-color: #4096ff;
    --success-color: #73d13d;
    --warning-color: #ffc53d;
    --error-color: #ff7875;
    --bg-color: #141414;
    --card-bg: #1f1f1f;
    --border-color: #303030;
    --text-primary: #ffffff;
    --text-secondary: #d9d9d9;
    --text-muted: #8c8c8c;
  }

  .home-container {
    background: linear-gradient(135deg, #141414 0%, #1f1f1f 100%);
  }
}

/* 打印样式 */
@media print {
  .home-container {
    background: white;
    padding: 0;
  }

  .top-bar,
  .gantt-toolbar,
  .actions {
    display: none;
  }

  .panel-card,
  .map-card,
  .gantt-chart {
    box-shadow: none;
    border: 1px solid #ccc;

  }
}

/* 甘特图按钮样式 - 浅蓝色背景配蓝色文字 */
.gantt-btn {
  background-color: #e6f7ff !important;
  border: 1px solid #91d5ff !important;
  color: #1890ff !important;
  font-weight: 500;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.gantt-btn:hover {
  background-color: #bae7ff !important;
  border-color: #69c0ff !important;
  color: #0050b3 !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.15);
}

.gantt-btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 6px rgba(24, 144, 255, 0.2);
}

/* 任务管理布局优化 */
.filter-toolbar {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.search-input {
  width: 100%;
}

.status-select {
  width: 100%;
}

/* 查看按钮样式 - 蓝色 */
.view-btn {
  color: #1890ff !important;
  font-weight: 500;
  margin-right: 8px;
  transition: all 0.3s ease;
}

.view-btn:hover {
  color: #40a9ff !important;
  background-color: #e6f7ff !important;
  border-radius: 4px;
}

/* 编辑按钮样式 - 绿色实心按钮 */
.edit-btn {
  background-color: #52c41a !important;
  border-color: #52c41a !important;
  color: white !important;
  font-weight: 600;
  transition: all 0.3s ease;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(82, 196, 26, 0.2);
}

.edit-btn:hover {
  background-color: #73d13d !important;
  border-color: #73d13d !important;
  color: white !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(82, 196, 26, 0.3);
}

.edit-btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 6px rgba(82, 196, 26, 0.2);
}

/* 任务表格优化 */
:deep(.el-table .el-table__row) {
  transition: all 0.3s ease;
}

:deep(.el-table .el-table__row:hover) {
  background-color: #f8f9fa;
}

:deep(.el-table .el-table__header-wrapper th) {
  background: #fafbfc;
  color: #606266;
  font-weight: 600;
  border-bottom: 2px solid #e4e7ed;
}

:deep(.el-table .el-table__body-wrapper) {
  border-radius: 0 0 8px 8px;
}

/* 确定按钮样式优化 */
:deep(.el-button--primary) {
  background-color: #409EFF !important;
  border-color: #409EFF !important;
  color: white !important;
  font-weight: 600;
  box-shadow: 0 2px 4px rgba(64, 158, 255, 0.2);
  transition: all 0.3s ease;
}

:deep(.el-button--primary:hover) {
  background-color: #66b1ff !important;
  border-color: #66b1ff !important;
  color: white !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

:deep(.el-button--primary:active) {
  transform: translateY(0);
  box-shadow: 0 2px 6px rgba(64, 158, 255, 0.2);
}

/* 状态标签优化 */
:deep(.el-tag--small) {
  min-width: 60px;
  text-align: center;
  white-space: nowrap;
  padding: 4px 8px;
  font-size: 12px;
  line-height: 1.2;
}

/* 确保状态列有足够空间 */
:deep(.el-table .el-table__cell) {
  padding: 8px 12px;
}

/* 状态列特殊处理 */
:deep(.el-table .el-table__cell:nth-child(3)) {
  min-width: 100px;
  text-align: center;
}

/* 生成调度按钮样式 */
.schedule-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  border: none !important;
  color: white !important;
  font-weight: 600;
  border-radius: 8px;
  padding: 12px 24px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
  position: relative;
  overflow: hidden;
}

.schedule-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.schedule-btn:hover {
  background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%) !important;
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
}

.schedule-btn:hover::before {
  left: 100%;
}

.schedule-btn:active {
  transform: translateY(0);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.schedule-btn:focus {
  outline: none;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
}

.stat-section {
  margin-bottom: 20px;
}

.stat-section h4 {
  margin: 0 0 12px 0;
  font-weight: 600;
  color: #303133;
}

.total-hours-info {
  background-color: #f5f7fa;
  padding: 12px;
  border-radius: 8px;
}

.mt16 {
  margin-top: 16px;
}

.progress-wrapper {
  display: flex;
  align-items: center;
  height: 100%;
  padding: 8px 0;
}

.custom-progress {
  flex: 1;
  border-radius: 10px;
  overflow: hidden;
  position: relative;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.custom-progress:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.custom-progress :deep(.el-progress-bar__outer) {
  border-radius: 10px;
  background-color: #f0f2f5;
  overflow: hidden;
  position: relative;
}

.custom-progress :deep(.el-progress-bar__inner) {
  border-radius: 10px;
  position: relative;
  overflow: hidden;
  animation: progressAnimation 1s ease-out !important;
  /* 从0.5s改为0.3s，进一步加快加载速度 */
  background: var(--progress-bg, linear-gradient(90deg, #67c23a, #b3e19d)) !important;
}

.custom-progress :deep(.el-progress-bar__inner)::after {
  content: "";
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg,
      transparent,
      rgba(255, 255, 255, 0.3),
      transparent);

}

.custom-progress :deep(.el-progress__text) {
  font-weight: 600;
  font-size: 12px !important;
  color: #555;
  text-shadow: 0 1px 1px rgba(0, 0, 0, 0.1);
  min-width: 40px;
  text-align: right;
}

@keyframes progressAnimation {
  0% {
    width: 0;
  }

  100% {
    width: var(--progress-width, 0%);
  }
}

@keyframes shimmer {
  0% {
    left: -100%;
    opacity: 0.5;
  }

  50% {
    opacity: 1;
  }

  100% {
    left: 100%;
    opacity: 0.5;
  }
}

.stat-table :deep(.el-table__cell) {
  padding: 8px 0;
}

.stat-icon {
  margin-right: 8px;
  font-size: 18px;
  vertical-align: middle;
}

/* 添加导出按钮样式 */
.table-export-button {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}

/* 加载状态样式 */
.schedule-btn.is-loading {
  background: linear-gradient(135deg, #a8a8a8 0%, #888888 100%) !important;
  cursor: not-allowed;
}

.schedule-btn.is-loading:hover {
  transform: none;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

/* Icon Font 美化样式 */
/* 注意：需要在HTML头部引入icon font，例如：
<link rel="stylesheet" href="//at.alicdn.com/t/font_xxxxx_xxxxx.css">
或者使用其他icon font库如Font Awesome等
*/

.algorithm-target-selection {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.selection-item {
  flex: 1; /* 三个下拉框等宽 */
  min-width: 0;
}

.iconfont {
  font-size: 18px;
  color: #409EFF;
  transition: all 0.3s ease;
  display: inline-block;
}

/* 面板图标统一样式 */
.panel-icon {
  width: 24px;
  height: 24px;
  object-fit: contain;
  transition: all 0.3s ease;
  filter: brightness(1) saturate(1);
}

.panel-icon:hover {
  transform: scale(1.1);
  filter: brightness(1.1) saturate(1.2) drop-shadow(0 2px 8px rgba(0, 0, 0, 0.15));
}

/* 面板标题悬停效果 */
.panel-title:hover .panel-icon {
  transform: scale(1.1);
  filter: brightness(1.1) saturate(1.2) drop-shadow(0 2px 8px rgba(0, 0, 0, 0.15));
}

/* 算法选择图标特殊样式 */
.section-title .panel-icon {
  width: 22px;
  height: 22px;
  margin-right: 8px;
}

.iconfont:active {
  animation: iconPulse 0.3s ease;
}

.gantt-container {
  transform: scale(0.9);
  transform-origin: top left;
  width: 111.11%; /* 100% / 0.9 to maintain the same visual width */
  height:90vh;
}

/* 图标动画效果 */
@keyframes iconPulse {
  0% {
    transform: scale(1);
  }

  50% {
    transform: scale(1.05);
  }

  100% {
    transform: scale(1);
  }
}

.iconfont:active {
  animation: iconPulse 0.3s ease;
}
.conflict-option {
  color: #f56c6c !important;
}
</style>
>>>>>>> c589649ceb11edd98eb5b9fff54865511d861051
