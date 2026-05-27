<template>
  <div class="process-confirmation-container">
    <el-card class="panel-card" shadow="hover">
      <div class="panel-header">
        <div class="panel-title">
          <el-icon class="panel-icon"><Checked /></el-icon>
          流程确认
        </div>
        <div class="header-actions">
          <el-button type="primary" size="small" @click="handleBatchConfirm" :disabled="!hasCurrentProcesses">
            <el-icon><Checked /></el-icon> 批量确认
          </el-button>
        </div>
      </div>

      <!-- 设备筛选组件 - 三级联动 -->
      <div class="filter-section">
        <div class="filter-title">
          <el-icon><Filter /></el-icon>
          <span>设备筛选</span>
          <el-button
            v-if="selectedCategory || selectedType || selectedInstance"
            type="primary"
            link
            size="small"
            @click="clearFilters"
            class="clear-filter-btn"
          >
            清除筛选
          </el-button>
        </div>
        <el-row :gutter="16" class="filter-row">
          <!-- 第一级：设备种类 -->
          <el-col :xs="24" :sm="8" :md="6">
            <div class="filter-item">
              <div class="filter-label">
                <el-icon><Folder /></el-icon>
                <span>设备种类</span>
              </div>
              <el-select
                v-model="selectedCategory"
                placeholder="全部种类"
                clearable
                size="default"
                @change="handleCategoryChange"
                class="filter-select"
                :popper-append-to-body="false"
              >
                <el-option
                  v-for="item in categoryOptions"
                  :key="item.value"
                  :label="`${item.label} (${item.count})`"
                  :value="item.value"
                />
              </el-select>
            </div>
          </el-col>

          <!-- 第二级：设备类型 -->
          <el-col :xs="24" :sm="8" :md="6">
            <div class="filter-item">
              <div class="filter-label">
                <el-icon><Files /></el-icon>
                <span>设备类型</span>
              </div>
              <el-select
                v-model="selectedType"
                placeholder="全部类型"
                :disabled="!selectedCategory"
                clearable
                size="default"
                @change="handleTypeChange"
                class="filter-select"
                :popper-append-to-body="false"
              >
                <el-option
                  v-for="item in typeOptions"
                  :key="item.value"
                  :label="`${item.label} (${item.count})`"
                  :value="item.value"
                />
              </el-select>
            </div>
          </el-col>

          <!-- 第三级：设备实例 -->
          <el-col :xs="24" :sm="8" :md="6">
            <div class="filter-item">
              <div class="filter-label">
                <el-icon><Monitor /></el-icon>
                <span>设备实例</span>
              </div>
              <el-select
                v-model="selectedInstance"
                placeholder="全部实例"
                :disabled="!selectedType"
                clearable
                size="default"
                @change="handleInstanceChange"
                class="filter-select"
                :popper-append-to-body="false"
                filterable
              >
                <el-option
                  v-for="item in instanceOptions"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </div>
          </el-col>

          <!-- 统计信息 -->
          <el-col :xs="24" :sm="8" :md="6">
            <div class="filter-stats">
              <el-tag type="info" effect="plain" size="large">
                总计: {{ filteredProcesses.length }} 条工序
              </el-tag>
              <el-tag v-if="selectedInstance" type="success" effect="plain" size="large">
                设备: {{ getSelectedInstanceName }}
              </el-tag>
            </div>
          </el-col>
        </el-row>
        <el-row :gutter="16" class="filter-row" style="margin-top: 16px;">
  <!-- 状态筛选 -->
  <el-col :xs="24" :sm="12" :md="8">
    <div class="filter-item">
      <div class="filter-label">
        <el-icon><DataLine /></el-icon>
        <span>工单状态</span>
      </div>
      <el-select
        v-model="selectedStatus"
        placeholder="全部状态"
        clearable
        size="default"
        class="filter-select"
        :popper-append-to-body="false"
      >
        <el-option
          v-for="item in statusOptions"
          :key="item.value"
          :label="`${item.label} (${schedulePlan.filter(p => p.status === item.value).length})`"
          :value="item.value"
        />
      </el-select>
    </div>
  </el-col>

  <!-- 统计信息及清除按钮 -->
  <el-col :xs="24" :sm="12" :md="16" class="filter-stats-wrapper">
    <div class="filter-stats">
      <el-tag type="info" effect="plain" size="large">
        总计: {{ filteredProcesses.length }} 条工序
      </el-tag>
      <el-tag v-if="selectedInstance" type="success" effect="plain" size="large">
        设备: {{ getSelectedInstanceName }}
      </el-tag>
      <el-button
        v-if="selectedCategory || selectedType || selectedInstance || selectedStatus"
        type="primary"
        link
        size="small"
        @click="clearFilters"
        class="clear-all-btn"
      >
        清除所有筛选
      </el-button>
    </div>
  </el-col>
</el-row>
      </div>

      <!-- 表格展示流程数据 - 显示全部数据 -->
      <div class="table-container">
        <el-table
          :data="filteredProcesses"
          border
          size="small"
          height="62vh"
          style="width: 100%"
          @row-click="handleRowClick"
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
              <el-tag :type="getStatusTagType(row.status)" size="small" effect="light" class="status-tag">
                {{ getStatusText(row.status) }}
              </el-tag>
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

          <el-table-column label="操作" width="180" fixed="right" align="center">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button
                  type="primary"
                  size="small"
                  plain
                  @click.stop="openProcessDetail(row)"
                >
                  <el-icon><View /></el-icon> 详情
                </el-button>
                <el-button
                  type="success"
                  size="small"
                  plain
                  @click.stop="handleConfirm(row)"
                >
                  <el-icon><Checked /></el-icon> 确认
                </el-button>
                <el-button
                  type="danger"
                  size="small"
                  plain
                  @click.stop="handleReject(row)"
                >
                  <el-icon><Close /></el-icon> 驳回
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 流程详情弹窗 -->
      <el-dialog
        v-model="detailDialogVisible"
        :title="`流程详情 - ${currentProcess?.process_name || ''}`"
        width="600px"
        destroy-on-close
        class="process-detail-dialog"
      >
        <div v-if="currentProcess" class="process-detail">
          <!-- 设备信息 -->
          <div class="detail-section">
            <h4>设备信息</h4>
            <div class="info-grid">
              <div class="info-item">
                <span class="label">设备名称：</span>
                <span class="value">{{ currentProcess.equipment_name }}</span>
              </div>
              <div class="info-item">
                <span class="label">设备种类：</span>
                <span class="value">{{ currentProcess.equipment_category }}</span>
              </div>
              <div class="info-item">
                <span class="label">设备类型：</span>
                <span class="value">{{ currentProcess.equipment_type_name }}</span>
              </div>
            </div>
          </div>

          <!-- 工序信息 -->
          <div class="detail-section">
            <h4>工序信息</h4>
            <div class="info-grid">
              <div class="info-item">
                <span class="label">工序名称：</span>
                <span class="value">{{ currentProcess.process_name }}</span>
              </div>
              <div class="info-item">
                <span class="label">工序状态：</span>
                <el-tag :type="getStatusTagType(currentProcess.status)" size="small">
                  {{ getStatusText(currentProcess.status) }}
                </el-tag>
              </div>
              <div class="info-item">
                <span class="label">责任人：</span>
                <span class="value">{{ formatWorkers(currentProcess.workers) }}</span>
              </div>
              <div class="info-item">
                <span class="label">预计时长：</span>
                <span class="value">{{ currentProcess.estimated_hours || '--' }}h</span>
              </div>
              <div class="info-item">
                <span class="label">开始时间：</span>
                <span class="value">{{ formatTime(currentProcess.scheduled_start_time) }}</span>
              </div>
              <div class="info-item">
                <span class="label">结束时间：</span>
                <span class="value">{{ formatTime(currentProcess.scheduled_end_time) }}</span>
              </div>
            </div>
          </div>

          <!-- 工序描述 -->
          <div v-if="currentProcess.description" class="detail-section">
            <h4>工序描述</h4>
            <div class="description">{{ currentProcess.description }}</div>
          </div>
           <div v-if="currentProcess.attachment_path" class="detail-section">
            <h4>上传图片</h4>
            <div class="image-preview">
              <el-image
                :src="'http://localhost:5000' + currentProcess.attachment_path"
                fit="contain"
                :preview-src-list="['http://localhost:5000' + currentProcess.attachment_path]"
                class="preview-image"
              />
            </div>
          </div>
          <div v-else class="detail-section">
            <h4>上传图片</h4>
            <div class="no-image">暂无图片</div>
          </div>
          <!-- 物料需求 -->
          <div v-if="currentProcess.material_requirements && Object.keys(currentProcess.material_requirements).length > 0" class="detail-section">
            <h4>物料需求</h4>
            <div class="info-grid">
              <div v-for="(value, key) in currentProcess.material_requirements" :key="key" class="info-item">
                <span class="label">{{ key }}：</span>
                <span class="value">{{ value.quantity }} {{ value.unit }}</span>
              </div>
            </div>
          </div>

          <!-- 工具需求 -->
          <div v-if="currentProcess.tools_requirements && Object.keys(currentProcess.tools_requirements).length > 0" class="detail-section">
            <h4>工具需求</h4>
            <div class="info-grid">
              <div v-for="(value, key) in currentProcess.tools_requirements" :key="key" class="info-item">
                <span class="label">{{ key }}：</span>
                <span class="value">{{ value.quantity }} {{ value.unit }}</span>
              </div>
            </div>
          </div>

          <!-- 驳回原因 -->
          <div v-if="currentProcess.status === 'rejected' && currentProcess.approval_comments" class="detail-section reject">
            <h4>驳回原因</h4>
            <div class="reject-reason">{{ currentProcess.approval_comments }}</div>
          </div>

          <!-- 完成意见 -->
          <div v-if="currentProcess.status === 'completed' && currentProcess.approval_comments" class="detail-section">
            <h4>完成意见</h4>
            <div class="comment">{{ currentProcess.approval_comments }}</div>
          </div>

          <!-- 纵向流程节点图 -->
          <div class="detail-section">
            <h4>工序流程</h4>
            <div class="process-flow-mini">
              <div class="process-timeline-mini">
                <div
                  v-for="(node, index) in sortedProcessesByEquipment(currentProcess.equipment_id)"
                  :key="node.id"
                  class="timeline-mini-item"
                  :class="{
                    'current-node': node.id === currentProcess.id,
                    'completed-node': node.status === 'completed',
                    'rejected-node': node.status === 'rejected',
                  }"
                  @click="viewProcessNode(node)"
                >
                  <!-- 左侧连接线 -->
                  <div class="mini-left">
                    <div v-if="index < sortedProcessesByEquipment(currentProcess.equipment_id).length - 1"
                         class="mini-line"
                         :class="{ 'line-completed': node.status === 'completed' }">
                    </div>
                    <div class="mini-dot" :class="`dot-${node.status}`">
                      <el-icon v-if="node.status === 'completed'" size="10"><Select /></el-icon>
                      <span v-else class="dot-index">{{ index + 1 }}</span>
                    </div>
                  </div>

                  <!-- 节点内容 -->
                  <div class="mini-content">
                    <div class="mini-title">
                      <span>{{ node.process_name }}</span>
                      <el-tag v-if="node.is_milestone" size="small" type="warning" class="mini-milestone">里程碑</el-tag>
                    </div>
                    <div class="mini-status">
                      <el-tag :type="getStatusTagType(node.status)" size="small" effect="plain">
                        {{ getStatusText(node.status) }}
                      </el-tag>
                    </div>
                    <div v-if="node.status === 'rejected' && node.approval_comments" class="mini-reject">
                      驳回：{{ node.approval_comments }}
                    </div>
                    <div v-if="node.status === 'on_hold' && node.approval_comments" class="mini-on-hold">
                      挂起：{{ node.approval_comments }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 意见输入（仅当工序可操作时显示） -->
          <div v-if="canOperateProcess(currentProcess)" class="detail-section opinion">
            <h4>{{ currentProcess.status === 'rejected' ? '重新确认意见' : '确认意见' }}</h4>
            <el-input
              v-model="opinionText"
              type="textarea"
              :rows="3"
              :placeholder="getOpinionPlaceholder(currentProcess.status)"
              maxlength="200"
              show-word-limit
            />
          </div>
        </div>

        <template #footer>
          <span class="dialog-footer">
            <el-button @click="detailDialogVisible = false" size="small">关闭</el-button>
            <el-button
              v-if="currentProcess && canOperateProcess(currentProcess)"
              type="primary"
              size="small"
              :loading="confirmLoading"
              @click="handleDialogConfirm"
            >
              <el-icon><Checked /></el-icon> 确认
            </el-button>
            <el-button
              v-if="currentProcess"
              type="danger"
              size="small"
              :loading="rejectLoading"
              @click="handleDialogReject"
            >
              <el-icon><Close /></el-icon> 驳回
            </el-button>
          </span>
        </template>
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Checked, Select, Monitor, Close, View, Filter, Folder, Files
} from '@element-plus/icons-vue'
import axios from 'axios'

// 数据状态
const schedulePlan = ref([])
const detailDialogVisible = ref(false)
const currentProcess = ref(null)
const opinionText = ref('')
const confirmLoading = ref(false)
const rejectLoading = ref(false)
const loading = ref(false)

// 筛选状态
const selectedCategory = ref('')
const selectedType = ref('')
const selectedInstance = ref('')
const selectedStatus = ref('')
// 筛选选项数据
const categoryOptions = ref([])
const typeOptions = ref([])
const instanceOptions = ref([])

// 设备数据映射
const categoryMap = ref(new Map())
const typeMap = ref(new Map())
const instanceMap = ref(new Map())
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
  'pending':"-",
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
// 是否有可批量确认的工序
const hasCurrentProcesses = computed(() => {
  return schedulePlan.value.some(p => p.status === 'on_hold')
})

// 获取选中实例的名称
const getSelectedInstanceName = computed(() => {
  if (!selectedInstance.value) return ''
  const instance = instanceMap.value.get(selectedInstance.value)
  return instance ? instance.name : ''
})

// 过滤后的流程数据 - 显示全部，不分页
const filteredProcesses = computed(() => {
  let processes = [...schedulePlan.value]

  // 按设备实例筛选
  if (selectedInstance.value) {
    processes = processes.filter(p => p.equipment_id === selectedInstance.value)
  }
  // 按设备类型筛选
  else if (selectedType.value) {
    processes = processes.filter(p => p.equipment_type_name === selectedType.value)
  }
  // 按设备种类筛选
  else if (selectedCategory.value) {
    processes = processes.filter(p => p.equipment_category === selectedCategory.value)
  }
  

if (selectedStatus.value) {
    processes = processes.filter(p => p.status === selectedStatus.value)
  }
  // 按开始时间正序排序
  processes.sort((a, b) => {
    const aTime = parseTimeToMinutes(a.scheduled_start_time)
    const bTime = parseTimeToMinutes(b.scheduled_end_time)
    return aTime - bTime
  })

  return processes
})
const statusOptions = computed(() => {
  // 从当前数据中提取所有出现的状态（去重）
  const statusSet = new Set(schedulePlan.value.map(p => p.status))
  // 转为选项数组，使用 getStatusText 显示友好名称
  return Array.from(statusSet)
    .map(status => ({
      value: status,
      label: getStatusText(status)
    }))
    .sort((a, b) => a.label.localeCompare(b.label))
})
// 从schedule_plan中提取设备分类信息
function extractEquipmentInfo() {
  const categories = new Set()
  const typesByCategory = new Map()
  const instancesByType = new Map()

  // 清空映射
  categoryMap.value.clear()
  typeMap.value.clear()
  instanceMap.value.clear()

  schedulePlan.value.forEach(process => {
    const category = process.equipment_category || '未分类'
    const type = process.equipment_type_name || '未指定类型'
    const instanceId = process.equipment_id
    const instanceName = process.equipment_name

    // 收集种类
    categories.add(category)

    // 收集种类下的类型
    if (!typesByCategory.has(category)) {
      typesByCategory.set(category, new Set())
    }
    typesByCategory.get(category).add(type)

    // 收集类型下的实例
    const typeKey = `${category}|${type}`
    if (!instancesByType.has(typeKey)) {
      instancesByType.set(typeKey, new Map())
    }
    instancesByType.get(typeKey).set(instanceId, {
      id: instanceId,
      name: instanceName,
      type: type,
      category: category
    })

    // 更新映射
    categoryMap.value.set(category, {
      name: category,
      types: typesByCategory.get(category)
    })

    typeMap.value.set(type, {
      name: type,
      categories: [category]
    })

    instanceMap.value.set(instanceId, {
      id: instanceId,
      name: instanceName,
      type: type,
      category: category
    })
  })

  // 生成种类选项
  categoryOptions.value = Array.from(categories).map(category => ({
    value: category,
    label: category,
    count: schedulePlan.value.filter(p => p.equipment_category === category).length
  })).sort((a, b) => a.label.localeCompare(b.label))
}

// 处理种类变化
function handleCategoryChange() {
  selectedType.value = ''
  selectedInstance.value = ''

  if (selectedCategory.value) {
    // 获取该种类下的所有类型
    const types = new Set()
    schedulePlan.value
      .filter(p => p.equipment_category === selectedCategory.value)
      .forEach(p => {
        if (p.equipment_type_name) {
          types.add(p.equipment_type_name)
        }
      })

    typeOptions.value = Array.from(types).map(type => ({
      value: type,
      label: type,
      count: schedulePlan.value.filter(p =>
        p.equipment_category === selectedCategory.value &&
        p.equipment_type_name === type
      ).length
    })).sort((a, b) => a.label.localeCompare(b.label))
  } else {
    typeOptions.value = []
  }
}

// 处理类型变化
function handleTypeChange() {
  selectedInstance.value = ''

  if (selectedType.value && selectedCategory.value) {
    // 获取该种类和类型下的所有实例
    const instances = new Map()
    schedulePlan.value
      .filter(p =>
        p.equipment_category === selectedCategory.value &&
        p.equipment_type_name === selectedType.value
      )
      .forEach(p => {
        if (p.equipment_id && p.equipment_name) {
          instances.set(p.equipment_id, {
            id: p.equipment_id,
            name: p.equipment_name
          })
        }
      })

    instanceOptions.value = Array.from(instances.values()).map(instance => ({
      value: instance.id,
      label: instance.name
    })).sort((a, b) => a.label.localeCompare(b.label))
  } else {
    instanceOptions.value = []
  }
}

// 处理实例变化
function handleInstanceChange() {
  // 无需额外操作
}

// 清除所有筛选
function clearFilters() {
  selectedCategory.value = ''
  selectedType.value = ''
  selectedInstance.value = ''
  selectedStatus.value = ''
  typeOptions.value = []
  instanceOptions.value = []
}
// 判断是否可以操作工序
function canOperateProcess(process) {
  if (!process) return false
  // pending 和 in_progress 状态不允许操作
  if (process.status === 'pending' || process.status === 'in_progress') return false
  // on_hold 和 rejected 状态才能操作
  return process.status === 'on_hold' || process.status === 'rejected'
}



// 获取行样式类名
function getRowClassName({ row }) {
  if (row.status === 'completed') return 'status-completed-row'
  if (row.status === 'rejected') return 'status-rejected-row'
  if (row.status === 'current') return 'status-current-row'
  if (row.status === 'on_hold') return 'status-on-hold-row'
  if (row.status === 'in_progress') return 'status-in-progress-row'
  if (row.status === 'pending') return 'status-pending-row'
  return ''
}

// 获取单元格样式 - 用于设置背景色
function getCellStyle({ row }) {
  // 为第一列（序号列）也应用背景色
  if (row.status === 'current') {
    return {
      backgroundColor: '#e3f2fd',
      borderBottom: '1px solid #bbdefb'
    }
  }
  if (row.status === 'rejected') {
    return {
      backgroundColor: '#ffebee',
      borderBottom: '1px solid #ffcdd2'
    }
  }
  if (row.status === 'completed') {
    return {
      backgroundColor: '#e8f5e8',
      borderBottom: '1px solid #c8e6c9'
    }
  }
  if (row.status === 'on_hold') {
    return {
      backgroundColor: '#fff3e0',
      borderBottom: '1px solid #ffe0b2'
    }
  }
  if (row.status === 'in_progress') {
    return {
      backgroundColor: '#e3f2fd',
      borderBottom: '1px solid #bbdefb'
    }
  }
  if (row.status === 'pending') {
    return {
      backgroundColor: '#fafafa',
      borderBottom: '1px solid #e0e0e0'
    }
  }
  return {}
}

// 获取状态标签类型
function getStatusTagType(status) {
  const typeMap = {
    'completed': 'success',
    'current': 'primary',
    'pending': 'info',
    'rejected': 'danger',
    'on_hold': 'warning',
    'in_progress': 'primary'
  }
  return typeMap[status] || 'info'
}

// 获取状态文本
function getStatusText(status) {

  return STATUS_LABEL_MAP[status] || status
}

// 格式化时间
function formatTime(timeStr) {
  if (!timeStr) return '--'
  
  // 尝试分割日期和时间（支持空格或T分隔）
  let datePart = timeStr
  let timePart = ''
  
  if (timeStr.includes(' ')) {
    [datePart, timePart] = timeStr.split(' ')
  } else if (timeStr.includes('T')) {
    [datePart, timePart] = timeStr.split('T')
  }
  
  // 如果时间部分存在，截取前5位（HH:MM）
  if (timePart) {
    return `${datePart} ${timePart.substring(0, 5)}`
  }
  
  // 否则只返回日期部分
  return datePart
}

// 格式化工人信息
function formatWorkers(workers) {
  if (!workers) return '未分配'
  if (typeof workers === 'string') return workers
  if (Array.isArray(workers)) return workers.join(', ')
  if (typeof workers === 'object') {
    const workerNames = []
    Object.keys(workers).forEach(role => {
      const names = workers[role]
      if (Array.isArray(names) && names.length > 0) {
        workerNames.push(...names)
      } else if (typeof names === 'string' && names) {
        workerNames.push(names)
      }
    })
    return workerNames.length > 0 ? workerNames.join(', ') : '未分配'
  }
  return '未分配'
}

// 获取意见输入框占位文本
function getOpinionPlaceholder(status) {
  if (status === 'rejected') {
    return '请填写重新确认意见（可选）'
  }
  return '请填写你的审核意见（可选）'
}

// 解析时间字符串
function parseTimeToMinutes(timeStr) {
  if (!timeStr) return 0
  try {
    const dayMatch = timeStr.match(/第(\d+)天/)
    const timeMatch = timeStr.match(/(\d+):(\d+)/)

    let day = 0
    let hours = 0
    let minutes = 0

    if (dayMatch) {
      day = parseInt(dayMatch[1], 10) * 24 * 60
    }
    if (timeMatch) {
      hours = parseInt(timeMatch[1], 10)
      minutes = parseInt(timeMatch[2], 10)
    }

    return day + hours * 60 + minutes
  } catch {
    return 0
  }
}

// 获取指定设备的排序后工序
function getSortedProcessesByEquipment(equipmentId) {
  return schedulePlan.value
    .filter(p => p.equipment_id === equipmentId)
    .sort((a, b) => {
      const aTime = parseTimeToMinutes(a.scheduled_start_time)
      const bTime = parseTimeToMinutes(b.scheduled_start_time)
      return aTime - bTime
    })
}

// 排序后的工序（用于弹窗）
const sortedProcessesByEquipment = (equipmentId) => {
  return getSortedProcessesByEquipment(equipmentId)
}

// 打开流程详情弹窗
function openProcessDetail(process) {

  currentProcess.value = process
  opinionText.value = ''
  detailDialogVisible.value = true
}

// 查看流程节点
function viewProcessNode(node) {
    currentProcess.value = node
    opinionText.value = ''
}

// 行点击事件


// 保存工序状态 - 修改为调用后端审批接口
async function saveProcessStatus(processId, newStatus, rejectReason = '', comment = '') {
  try {
    const token = localStorage.getItem('token') || ''
    // 调用后端审批接口
    const response = await axios.put(`http://localhost:5000/api/work-order-tasks/${processId}/approve`, {
      approval_result: newStatus === 'completed' ? 'approved' : 'rejected',
      approval_comments: newStatus === 'completed' ? comment : rejectReason
    }, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (response.data.success) {
      // 更新本地状态
      const plans = [...schedulePlan.value]
      const index = plans.findIndex(p => p.id === processId)

      if (index !== -1) {
        plans[index] = {
          ...plans[index],
          status: newStatus,
          approval_comments: newStatus === 'rejected' ? rejectReason : (newStatus === 'completed' ? comment : plans[index].approval_comments)
        }
        schedulePlan.value = plans

        // 重新提取设备信息
        extractEquipmentInfo()

        // 显示成功消息
        ElMessage.success(response.data.message || '状态更新成功')
        return true
      }
    } else {
      ElMessage.error(response.data.message || '操作失败')
      return false
    }
  } catch (e) {
    console.error('保存工序状态失败:', e)
    if (e.response && e.response.data) {
      ElMessage.error(e.response.data.message || '操作失败')
    } else {
      ElMessage.error('网络错误，请检查后端服务是否正常')
    }
    return false
  }
}

// 激活下一个节点
function activateNextNode(equipmentId) {
  const processes = getSortedProcessesByEquipment(equipmentId)

  const nextNode = processes.find(p => p.status !== 'completed')
  if (nextNode) {
    saveProcessStatus(nextNode.id, 'current')
    ElMessage.info(`已激活下一工序: ${nextNode.process_name}`)
  } else {
    ElMessage.success('该设备所有工序已完成！')
  }
}

// 确认工序 - 直接使用审批接口
function handleConfirm(process) {
  const confirmText = '确认完成'

  ElMessageBox.prompt(
    `请输入确认意见（可选）`,
    `${confirmText} - ${process.process_name}`,
    {
      confirmButtonText: confirmText,
      cancelButtonText: '取消',
      type: 'info',
      inputPlaceholder: '请输入确认意见',
      inputType: 'textarea',
      inputValidator: () => true,
    }
  ).then(async ({ value }) => {
    confirmLoading.value = true
    try {
      const token = localStorage.getItem('token') || ''
      // 直接调用审批接口确认，状态变为 completed
      const response = await axios.put(`http://localhost:5000/api/work-order-tasks/${process.id}/update-status`, {
        action:'confirm',
        approval_result: 'approved',
        approval_comments: value || ''
      }, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.data.success) {
        ElMessage.success(`"${process.process_name}" 已确认完成`)
        // activateNextNode(process.equipment_id)
        detailDialogVisible.value = false

        // 更新本地数据，状态改为 completed
        const plans = [...schedulePlan.value]
        const index = plans.findIndex(p => p.id === process.id)
        if (index !== -1) {
          plans[index] = {
            ...plans[index],
            status: response.data.new_status,
            approval_comments: value || ''
          }
          schedulePlan.value = plans
          extractEquipmentInfo()
        }
      } else {
        throw new Error(response.data.message || '确认失败')
      }
    } catch (error) {
      console.error('确认工序失败:', error)
      if (error.response && error.response.data) {
        ElMessage.error(error.response.data.message || '确认失败')
      } else {
        ElMessage.error('网络错误，请检查后端服务是否正常')
      }
    } finally {
      confirmLoading.value = false
    }
  }).catch(() => {
    confirmLoading.value = false
  })
}

// 驳回工序 - 直接使用审批接口
function handleReject(process) {
  const rejectAction = process.status === 'rejected' ? '再次驳回' : '驳回'

  ElMessageBox.prompt('请输入驳回原因', `${rejectAction} - ${process.process_name}`, {
    confirmButtonText: `确定${rejectAction}`,
    cancelButtonText: '取消',
    type: 'warning',
    inputPlaceholder: '请填写驳回原因（必填）',
    inputType: 'textarea',
    inputPattern: /\S+/,
    inputErrorMessage: '驳回原因不能为空'
  }).then(async ({ value }) => {
    rejectLoading.value = true
    try {
      const token = localStorage.getItem('token') || ''
      // 直接调用审批接口驳回
      const response = await axios.put(`http://localhost:5000/api/work-order-tasks/${process.id}/update-status`, {
        action:"reject",
        approval_result: 'rejected',
        approval_comments: value
      }, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.data.success) {
        ElMessage.warning(`已${rejectAction} "${process.process_name}"，原因：${value}`)
        detailDialogVisible.value = false

        // 更新本地数据
        const plans = [...schedulePlan.value]
        const index = plans.findIndex(p => p.id === process.id)
        if (index !== -1) {
          plans[index] = {
            ...plans[index],
            status: 'rejected',
            approval_comments: value
          }
          schedulePlan.value = plans
          extractEquipmentInfo()
        }
      } else {
        throw new Error(response.data.message || '驳回失败')
      }
    } catch (error) {
      console.error('驳回工序失败:', error)
      if (error.response && error.response.data) {
        ElMessage.error(error.response.data.message || '驳回失败')
      } else {
        ElMessage.error('网络错误，请检查后端服务是否正常')
      }
    } finally {
      rejectLoading.value = false
    }
  }).catch(() => {
    rejectLoading.value = false
  })
}

// 弹窗内确认
function handleDialogConfirm() {
  if (currentProcess.value) {
    handleConfirm(currentProcess.value)
  }
}

// 弹窗内驳回
function handleDialogReject() {
  if (currentProcess.value) {
    handleReject(currentProcess.value)
  }
}

// 批量确认 - 修改筛选条件
function handleBatchConfirm() {
  // 筛选出状态为 on_hold 的任务
  const onHoldNodes = schedulePlan.value.filter(p => p.status === 'on_hold')

  if (onHoldNodes.length === 0) {
    ElMessage.warning('无可确认的待审批任务')
    return
  }

  ElMessageBox.confirm(
    `确认 ${onHoldNodes.length} 个待审批任务？`,
    '批量确认',
    {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'info',
      center: true,
      size: 'small'
    }
  ).then(async () => {
    try {
      let successCount = 0
      const equipmentGroups = {}
      const token = localStorage.getItem('token') || ''

      // 直接调用审批接口确认所有 on_hold 任务，状态变为 completed
      for (const node of onHoldNodes) {
        try {
          await axios.put(`http://localhost:5000/api/work-order-tasks/${node.id}/approve`, {
            approval_result: 'approved',
            approval_comments: '批量确认'
          }, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          })

          if (!equipmentGroups[node.equipment_id]) {
            equipmentGroups[node.equipment_id] = []
          }
          equipmentGroups[node.equipment_id].push(node)
          successCount++
        } catch (error) {
          console.error(`任务 ${node.id} 确认失败:`, error)
          // 继续处理其他任务
        }
      }

      // 更新本地数据，状态改为 completed
      const plans = [...schedulePlan.value]
      onHoldNodes.forEach(node => {
        const index = plans.findIndex(p => p.id === node.id)
        if (index !== -1) {
          plans[index] = {
            ...plans[index],
            status: 'completed',  // 批量确认后状态变为 completed
            approval_comments: '批量确认'
          }
        }
      })
      schedulePlan.value = plans
      extractEquipmentInfo()

      Object.keys(equipmentGroups).forEach(equipmentId => {
        activateNextNode(parseInt(equipmentId))
      })

      ElMessage.success(`已确认 ${successCount} 个任务`)
    } catch (error) {
      console.error('批量确认失败:', error)
      if (error.response && error.response.data) {
        ElMessage.error(error.response.data.message || '批量确认失败')
      } else {
        ElMessage.error('网络错误，请检查后端服务是否正常')
      }
    }
  }).catch(() => {})
}

// 加载 schedule_plan 数据
async function loadSchedulePlan() {
  loading.value = true
  try {
    const response = await axios.get('http://localhost:5000/api/work-order-tasks')

    if (response.data.success) {
      let plans = response.data.data
      console.log('Loaded work order tasks:', plans)

      // 添加设备种类和类型字段（如果API没有返回）
      plans = plans.map(p => ({
        ...p,
        equipment_category: p.equipment_category || '生产设备',
        equipment_type_name: p.equipment_type_name || '反应釜'
      }))

      const equipmentGroups = {}
      plans.forEach(p => {
        if (!equipmentGroups[p.equipment_id]) {
          equipmentGroups[p.equipment_id] = []
        }
        equipmentGroups[p.equipment_id].push(p)
      })

      Object.keys(equipmentGroups).forEach(equipmentId => {
        const group = equipmentGroups[equipmentId]
        group.sort((a, b) => {
          const aTime = parseTimeToMinutes(a.scheduled_start_time)
          const bTime = parseTimeToMinutes(b.scheduled_start_time)
          return aTime - bTime
        })

        // 移除自动设置on_hold状态的逻辑
        // 让后端或业务逻辑决定哪些工序应该是on_hold状态
      })

      schedulePlan.value = plans

      // 提取设备信息用于筛选
      extractEquipmentInfo()
    } else {
      ElMessage.error('加载数据失败：' + response.data.message)
    }
  } catch (e) {
    console.error('加载数据失败:', e)
    ElMessage.error('加载数据失败，请检查后端服务是否正常')
    schedulePlan.value = []
  } finally {
    loading.value = false
  }
}

// 页面加载
onMounted(() => {
  loadSchedulePlan()
})
</script>

<style scoped>
.process-confirmation-container {
  padding: 16px;
  height: 100%;
  box-sizing: border-box;
  background-color: #f5f8fa;
}

.panel-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.04);
}

.panel-header {
  padding: 12px 20px;
  border-bottom: 1px solid #eef2f6;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-title {
  font-size: 18px;
  font-weight: 600;
  color: #0b2c44;
  display: flex;
  align-items: center;
}

.panel-icon {
  margin-right: 8px;
  font-size: 20px;
  color: #1f6e9c;
}

.header-actions {
  display: flex;
  gap: 8px;
}

/* 筛选区域样式 */
.filter-section {
  padding: 16px 20px;
  border-bottom: 1px solid #eef2f6;
  background: #fafcfd;
}

.filter-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  font-size: 14px;
  font-weight: 600;
  color: #1f4e6a;
}

.filter-title .el-icon {
  font-size: 16px;
  color: #409eff;
}

.clear-filter-btn {
  margin-left: auto;
}

.filter-row {
  display: flex;
  align-items: flex-end;
}

.filter-item {
  background: white;
  border-radius: 8px;
  padding: 8px 12px;
  border: 1px solid #e4edf2;
  transition: all 0.3s;
}

.filter-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.filter-label {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 6px;
  font-size: 12px;
  color: #5a7e94;
}

.filter-label .el-icon {
  font-size: 14px;
  color: #409eff;
}

.filter-select {
  width: 100%;
}

.filter-select :deep(.el-input__wrapper) {
  background: transparent;
  box-shadow: none !important;
  padding-left: 0;
}

.filter-stats {
  display: flex;
  gap: 8px;
  align-items: center;
  height: 100%;
  padding: 8px 0;
}

.filter-stats .el-tag {
  font-size: 13px;
}

.table-container {
  flex: 1;
  padding: 0 20px 16px;
  overflow: auto;
}

/* 表格样式 - 使用自定义类名控制背景色，同时保留悬停效果 */
:deep(.el-table .status-current-row) {
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

:deep(.el-table .status-in-progress-row) {
  --el-table-tr-bg-color: #e3f2fd;
}

:deep(.el-table .status-pending-row) {
  --el-table-tr-bg-color: #fafafa;  /* 待完成使用灰色背景 */
}

/* 确保悬停时颜色变化 */
:deep(.el-table .el-table__row:hover) {
  --el-table-tr-bg-color: var(--el-table-row-hover-bg-color) !important;
}

:deep(.el-table .status-current-row:hover) {
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

:deep(.el-table .status-in-progress-row:hover) {
  --el-table-tr-bg-color: #bbdefb !important;
}

:deep(.el-table .status-pending-row:hover) {
  --el-table-tr-bg-color: #eeeeee !important;  /* 待完成悬停效果 */
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

/* 流程详情弹窗样式 */
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

.reject-section h4::before,
.reject h4::before {
  background: #f56c6c;
}

.reject-reason {
  background: #fff5f5;
  color: #c96b6b;
  border-left: 3px solid #f56c6c;
}

/* 迷你流程节点图 */
.process-flow-mini {
  background: #f8fbfd;
  border-radius: 8px;
  padding: 16px;
  max-height: 300px;
  overflow-y: auto;
}

.process-timeline-mini {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.timeline-mini-item {
  display: flex;
  position: relative;
  cursor: pointer;
  transition: all 0.2s;
  padding: 8px;
  border-radius: 6px;
}

.timeline-mini-item:hover {
  background: #eef2f6;
}

.timeline-mini-item.current-node {
  background: #e3f0fa;
  border: 1px solid #409eff;
}

.timeline-mini-item.completed-node {
  opacity: 0.8;
}

.timeline-mini-item.rejected-node {
  background: #fff5f5;
}

.timeline-mini-item.disabled-node {
  opacity: 0.5;
  cursor: not-allowed;
}

.mini-left {
  position: relative;
  width: 30px;
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
}

.mini-line {
  position: absolute;
  top: 22px;
  left: 50%;
  width: 1.5px;
  height: calc(100% + 12px);
  background: #cbd5e1;
  transform: translateX(-50%);
}

.mini-line.line-completed {
  background: #2c8e5c;
}

.mini-dot {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 600;
  color: white;
  z-index: 2;
}

.dot-completed {
  background: #2c8e5c;
}

.dot-current {
  background: #1f7a9c;
}

.dot-pending {
  background: #99aab9;
}

.dot-rejected {
  background: #c96b6b;
}

.dot-index {
  font-size: 10px;
}

.mini-content {
  flex: 1;
  margin-left: 8px;
}

.mini-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #1c3343;
  margin-bottom: 4px;
}

.mini-milestone {
  font-size: 8px;
  padding: 0 4px;
  height: 16px;
  line-height: 16px;
}

.mini-status {
  margin-bottom: 4px;
}

.mini-reject {
  font-size: 11px;
  color: #c96b6b;
  background: #fff5f5;
  padding: 2px 6px;
  border-radius: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
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

/* 迷你流程节点图中的进行中状态样式 */
.mini-dot.dot-in_progress {
  background: #1f7a9c;  /* 进行中使用蓝色 */
}

/* 迷你流程节点图中的待完成状态样式 */
.mini-dot.dot-pending {
  background: #99aab9;  /* 待完成使用灰色 */
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
