<template>
  <el-card class="import-card" shadow="hover">
    <h2 class="title">设备台账</h2>

    <!-- 设备查询组件 -->
    <div class="equipment-search-container">
      <h3 class="search-title">设备查询</h3>
      <el-form :model="searchForm" class="search-form" label-width="120px" size="default">
        <el-form-item label="设备分类">
          <el-select 
            v-model="searchForm.category" 
            placeholder="全部分类" 
            clearable
            class="search-select"
          >
            <el-option label="全部分类" value="" />
            <el-option
              v-for="category in categoryOptions"
              :key="category.value"
              :label="category.label"
              :value="category.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="创建时间">
          <el-date-picker 
            v-model="searchForm.created_time" 
            type="date" 
            placeholder="年/月/日"
            value-format="YYYY-MM-DD"
            class="search-date"
          />
        </el-form-item>
        <el-form-item label="设备类型ID">
          <el-input 
            v-model="searchForm.equipment_type_id" 
            placeholder="请输入设备类型ID" 
            clearable
            class="search-input"
          />
        </el-form-item>
        <el-form-item label="设备类型名称">
          <el-select
            v-model="searchForm.equipment_type_name"
            placeholder="请选择设备类型"
            clearable
            class="search-select"
          >
            <el-option
              v-for="type in equipmentTypes"
              :key="type.value"
              :label="type.label"
              :value="type.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="设备名称">
          <el-input 
            v-model="searchForm.name" 
            placeholder="请输入设备名称" 
            clearable
            class="search-input"
          />
        </el-form-item>
        <el-form-item class="search-btn-group">
          <el-button type="primary" size="default" @click="handleSearch">查询</el-button>
          <el-button size="default" @click="handleResetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 隐藏的上传组件 -->
    <el-upload
      ref="uploadRef"
      class="upload-demo"
      :auto-upload="false"
      :show-file-list="false"
      :before-upload="handleBeforeUpload"
      :on-change="handleFileChange"
      accept=".xlsx,.xls,.csv"
      style="display: none;"
    >
      <template #trigger>
        <div></div>
      </template>
    </el-upload>

    <!-- 进度条与提示区域 -->
    <div v-if="progressVisible" class="progress-wrap">
      <el-progress :percentage="progressPercent" :status="progressStatus" :stroke-width="14" />
      <div class="progress-text">{{ progressText }}</div>
    </div>
    <el-alert
      v-if="tipVisible"
      :title="tipMessage"
      :type="tipType"
      show-icon
      class="result-tip"
      @close="tipVisible = false"
    />

    <!-- Excel编辑器弹窗 -->
    <excel-editor
      v-model="excelEditorVisible"
      title="设备数据编辑"
      :data="excelData"
      :columns="excelColumns"
      @confirm="confirmImport"
    />

    <!-- 添加设备对话框 -->
    <el-dialog v-model="addDialogVisible" title="添加设备" width="500px" destroy-on-close>
      <el-form :model="newEquipment" label-width="120px" style="padding: 20px 0;">
         <el-form-item label="设备分类" required>
          <el-select v-model="newEquipment.category" placeholder="请选择设备分类" style="width: 100%;">
            <el-option
              v-for="category in categoryOptions"
              :key="category.value"
              :label="category.label"
              :value="category.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="设备类型ID" required>
          <el-input v-model="newEquipment.type_id" placeholder="请输入设备类型ID" />
        </el-form-item>
        <el-form-item label="设备名称" required>
          <el-input v-model="newEquipment.name" placeholder="请输入设备名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="addDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="addEquipment">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 树状结构布局 -->
    <div class="tree-layout">
      <!-- 左侧树菜单 -->
      <div class="tree-panel">
        <div class="device-count-panel">
          当前共有 <span class="device-count-number">{{ totalInstances }}</span> 个设备实例
        </div>
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
      <!-- 右侧内容区 -->
      <div class="content-panel">
        <div v-if="currentNode && currentNode.type === 'instance'" class="equipment-detail">
          <h3>{{ currentNode.name }}</h3>
          <el-form label-width="120px" style="height:30vh">
            <el-form-item v-for="(value, key) in filteredEquipmentFields" :key="key" :label="getFieldLabel(key)">
              <el-input 
                v-if="isEditing" 
                v-model="currentNode[key]" 
              />
              <span v-else>{{ value }}</span>
            </el-form-item>
          </el-form>
          <div class="action-buttons">
            <el-button v-if="!isEditing" size="small" :icon="Edit" @click="editEquipment(currentNode)">编辑</el-button>
            <el-button v-else size="small" type="primary" :icon="CircleCheck" @click="saveEquipment">完成</el-button>
            <el-button size="small" type="danger" :icon="Delete" @click="deleteEquipment(currentNode)">删除</el-button>
            <el-button 
              size="small" 
              type="info" 
              :icon="Document" 
              @click="viewMaintenanceHistory(currentNode)"
            >
              查看历史维修记录
            </el-button>
          </div>
        </div>
        
        <div v-else-if="currentNode && currentNode.type === 'kind'" class="kind-info">
          
          <h3>{{ currentNode.label }} - 设备列表</h3>
          <p>该种类下共有 {{ currentNode.children?.length || 0 }} 个设备实例</p>
          <el-table 
            :data="currentNode.children" 
            border 
            style="width: 100%" 
            max-height="400"
            :fit="true"
            stripe
          >
            <template v-if="currentNode.label === '离心泵'">
              <el-table-column 
                prop="id" 
                label="设备ID" 
                width="100"
                align="center">
              </el-table-column>
              <el-table-column 
                prop="equipment_type_id" 
                label="设备类型ID" 
                width="200"
                align="center">
              </el-table-column>
              <el-table-column 
                prop="name" 
                label="设备名称" 
                min-width="150"
                show-overflow-tooltip
                align="center">
              </el-table-column>
              <el-table-column 
                prop="category" 
                label="设备分类" 
                width="120"
                align="center">
              </el-table-column>
              <el-table-column 
                prop="equipment_type_name" 
                label="设备类型名称" 
                min-width="150"
                show-overflow-tooltip
                align="center">
              </el-table-column>
            </template>
            <template v-else>
              <el-table-column 
                prop="name" 
                label="设备名称" 
                min-width="150"
                show-overflow-tooltip
                align="center">
              </el-table-column>
              <el-table-column 
                prop="id" 
                label="设备ID" 
                width="100"
                align="center">
              </el-table-column>
              <el-table-column 
                prop="category" 
                label="设备分类" 
                width="120"
                align="center">
              </el-table-column>
              <el-table-column 
                prop="equipment_type_name" 
                label="设备类型名称" 
                min-width="150"
                show-overflow-tooltip
                align="center">
              </el-table-column>
            </template>
          
            <el-table-column 
              label="操作" 
              width="100" 
              fixed="right"
              align="center">
              <template #default="{ row }">
                <el-button size="small" @click="selectEquipmentInstance(row)">查看</el-button>
              </template>
            </el-table-column>
          </el-table>
          
        </div>
        <div v-else-if="currentNode && currentNode.type === 'category'" class="category-info">
          <h3>{{ currentNode.label }}</h3>
          <p>该类别下共有 {{ currentNode.children?.length || 0 }} 个设备实例</p>
        </div>
        <div v-else class="placeholder">
          <p>请选择一个设备实例查看详情</p>
        </div>
      </div>
    </div>

    <!-- 查看历史维修记录弹窗 -->
    <el-dialog 
      v-model="maintenanceHistoryVisible" 
      title="历史维修记录" 
      width="60vw"
      destroy-on-close
    >
      <div v-if="maintenanceHistoryData.length === 0" style="text-align: center; padding: 40px;">
        <el-empty description="暂无维修记录" />
      </div>
      <div v-else class="maintenance-history-container">
        <!-- 第一层：按 equipment_id 分组后的工单列表 -->
        <el-collapse v-model="activeWorkOrders" accordion>
          <el-collapse-item 
            v-for="(workOrderGroup, workOrderId) in groupedMaintenanceData" 
            :key="workOrderId"
            :name="workOrderId"
          >
            <template #title>
              <div class="work-order-header">
                <el-tag type="primary" size="large">{{ workOrderGroup.work_order_no }}</el-tag>
                <span class="work-order-info">
                  <el-icon><Document /></el-icon>
                  工单任务：{{ workOrderGroup.task_count }} 项 | 
                  设备：{{ workOrderGroup.equipment_name }} |
                  最早开始：{{ workOrderGroup.earliest_start }} |
                  最晚结束：{{ workOrderGroup.latest_end }}
                </span>
              </div>
            </template>
            
            <!-- 第二层：工单下的具体任务 -->
            <el-table 
              :data="workOrderGroup.tasks" 
              border 
              stripe 
              max-height="500"
              size="small"
            >
              <el-table-column prop="task_code" label="任务编码" width="100" align="center" />
              <el-table-column prop="process_name" label="工序名称" min-width="150" show-overflow-tooltip />
              <el-table-column prop="description" label="任务描述" min-width="200" show-overflow-tooltip />
              <el-table-column prop="estimated_hours" label="预计工时 (h)" width="100" align="center" />
              <el-table-column prop="scheduled_start_time" label="计划开始" width="140" align="center" />
              <el-table-column prop="scheduled_end_time" label="计划结束" width="140" align="center" />
              <el-table-column prop="status" label="状态" width="100" align="center">
                <template #default="{ row }">
                  <el-tag :type="getStatusTagType(row.status)" size="small">
                    {{ getStatusText(row.status) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="物料需求" width="120" align="center">
                <template #default="{ row }">
                  <el-popover placement="top" trigger="hover" :width="200">
                    <template #reference>
                      <el-tag size="small" type="info" v-if="row.material_requirements">
                        {{ Object.keys(row.material_requirements).length }} 项
                      </el-tag>
                      <el-tag size="small" type="info" v-else>无</el-tag>
                    </template>
                    <div v-if="row.material_requirements">
                      <div v-for="(req, key) in row.material_requirements" :key="key" style="margin-bottom: 8px;">
                        <strong>{{ key }}:</strong> {{ req.quantity }} {{ req.unit }}
                      </div>
                    </div>
                    <div v-else>无物料需求</div>
                  </el-popover>
                </template>
              </el-table-column>
              <el-table-column label="工具需求" width="120" align="center">
                <template #default="{ row }">
                  <el-popover placement="top" trigger="hover" :width="200">
                    <template #reference>
                      <el-tag size="small" type="success" v-if="row.tools_requirements">
                        {{ Object.keys(row.tools_requirements).length }} 项
                      </el-tag>
                      <el-tag size="small" type="success" v-else>无</el-tag>
                    </template>
                    <div v-if="row.tools_requirements">
                      <div v-for="(req, key) in row.tools_requirements" :key="key" style="margin-bottom: 8px;">
                        <strong>{{ key }}:</strong> {{ req.quantity }} {{ req.unit }}
                      </div>
                    </div>
                    <div v-else>无工具需求</div>
                  </el-popover>
                </template>
              </el-table-column>
              <el-table-column label="人员安排" width="150" align="center">
                <template #default="{ row }">
                  <el-popover placement="top" trigger="hover" :width="300">
                    <template #reference>
                      <div class="worker-display">
                        <el-tag 
                          v-for="(workerList, role) in row.workers" 
                          :key="role"
                          size="small"
                          type="warning"
                          class="worker-tag"
                        >
                          {{ role }}: {{ workerList.join(' ') }}
                        </el-tag>
                      </div>
                    </template>
                    <div v-if="row.workers && Object.keys(row.workers).length > 0">
                      <div v-for="(workerList, role) in row.workers" :key="role" class="worker-detail-row">
                        <strong>{{ role }}:</strong>
                        <div class="worker-names">
                          <el-tag 
                            v-for="worker in workerList" 
                            :key="worker"
                            size="small"
                            effect="plain"
                            class="worker-name-tag"
                          >
                            {{ worker }}
                          </el-tag>
                        </div>
                      </div>
                    </div>
                    <div v-else class="no-workers">未安排人员</div>
                  </el-popover>
                </template>
              </el-table-column>
            </el-table>
          </el-collapse-item>
        </el-collapse>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="maintenanceHistoryVisible = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 底部功能图标区 -->
    <div class="bottom-function-icons">
      <!-- 添加单个数据 -->
      <div class="icon-item" @click="showAddEquipmentDialog" title="添加单个设备数据">
        <img src="@/assets/iconfont/添加.png" class="function-icon" alt="添加单个设备数据" />
      </div>
      <!-- 下载模板 -->
      <div class="icon-item" @click="downloadTemplate" title="下载Excel模板">
        <img src="@/assets/iconfont/下载.png" class="function-icon" alt="下载Excel模板" />
      </div>
      <!-- 导入文件 -->
      <div class="icon-item" @click="triggerFileUpload" title="上传Excel文件">
        <img src="@/assets/iconfont/上传.png" class="function-icon" alt="上传Excel文件" />
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { ref, computed, onMounted, reactive, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { OfficeBuilding, Box, Files, Monitor, Edit, CircleCheck, Delete, Document } from '@element-plus/icons-vue'
import * as XLSX from 'xlsx'
import ExcelEditor from './ExcelEditor.vue'
import request from '@/utils/request'

// 设备查询表单数据
const searchForm = reactive({
  category: '',        // 设备分类
  created_time: '',    // 创建时间
  equipment_type_id: '', // 设备类型ID
  equipment_type_name: '', // 设备类型名称
  name: ''             // 设备名称
})

// 设备类型选项
const equipmentTypes = computed(() => {
  const types = []
  const root = treeData.value[0]
  if (root && root.children) {
    root.children.forEach(category => {
      if (category.children) {
        category.children.forEach(kind => {
          types.push({
            value: kind.label,
            label: kind.label
          })
        })
      }
    })
  }
  return types
})

// 原有逻辑
const uploading = ref(false)
const uploadRef = ref()
const selectedFile = ref(null)
const selectedFileName = ref('')
// Excel编辑器相关
const excelEditorVisible = ref(false)
const excelData = ref([])
const excelColumns = ref([])
// 树形结构数据
const treeData = ref([
  {
    id: 1,
    label: '设备',
    type: 'root',
    children: []
  }
])
const defaultProps = { children: 'children', label: 'label' }
const currentNode = ref(null)
const isEditing = ref(false)
// 筛选相关
const categoryOptions = computed(() => {
  // 从设备数据中动态提取分类选项
  const categories = []
  const root = treeData.value[0]
  if (root && root.children) {
    root.children.forEach(category => {
      categories.push({
        value: category.label,
        label: category.label
      })
    })
  }
  return categories
})
// 设备字段标签映射
const fieldLabels = {
  id: '设备ID',
  name: '设备名称',
  category: '设备分类',
  created_time: '创建时间',
  equipment_type_id: '设备类型ID',
  equipment_type_name: '设备类型名称',
 
}
// 过滤不需要显示的字段
const filteredEquipmentFields = computed(() => {
  if (!currentNode.value || currentNode.value.type !== 'instance') return {}
  const filtered = {}
  Object.keys(currentNode.value).forEach(key => {
    if (!['id', 'type', 'label', 'children', 'type_id'].includes(key)) {
      filtered[key] = currentNode.value[key]
    }
  })
  return filtered
})
// 获取字段中文标签
function getFieldLabel(field) {
  return fieldLabels[field] || field
}
// 设备实例总数计算
const totalInstances = computed(() => {
  let count = 0
  const root = treeData.value[0]
  if (root && root.children) {
    root.children.forEach(category => {
      if (category.children) {
        category.children.forEach(kind => {
          if (kind.children) {
            count += kind.children.length
          }
        })
      }
    })
  }
  return count
})

const filteredTreeData = computed(() => {
  // 使用设备查询条件筛选树数据
  const filtered = JSON.parse(JSON.stringify(treeData.value))
  
  if (filtered.length > 0 && filtered[0].children) {
    // 按设备分类筛选
    if (searchForm.category) {
      const categoryNode = filtered[0].children.find(cat => cat.label === searchForm.category)
      filtered[0].children = categoryNode ? [categoryNode] : []
    }
    
    // 按设备类型名称筛选
    if (searchForm.equipment_type_name && filtered[0].children.length > 0) {
      filtered[0].children.forEach(category => {
        if (category.children) {
          category.children = category.children.filter(kind => 
            kind.label === searchForm.equipment_type_name
          )
        }
      })
    }
    
    // 按设备名称筛选
    if (searchForm.name && filtered[0].children.length > 0) {
      filtered[0].children.forEach(category => {
        if (category.children) {
          category.children.forEach(kind => {
            if (kind.children) {
              kind.children = kind.children.filter(instance => 
                instance.label.toLowerCase().includes(searchForm.name.toLowerCase())
              )
            }
          })
        }
      })
    }
  }
  
  return filtered
})
// 设备实例相关
const equipmentInstances = ref([])
const loadingInstances = ref(false)
// 编辑设备相关
const editDialogVisible = ref(false)
const currentEquipment = reactive({})
// 添加设备相关
const addDialogVisible = ref(false)
const newEquipment = reactive({ type_id: '', name: '', category: '' })
// 分页相关
const currentPage = ref(1)
const pageSize = ref(10)
// 当前页数据
const currentPageEquipmentInstances = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return equipmentInstances.value.slice(start, end)
})
// 提示相关
const tipVisible = ref(false)
const tipMessage = ref('')
const tipType = ref('success')
// 进度相关
const progressPercent = ref(0)
const progressVisible = ref(false)
const progressStatus = ref(undefined)
const progressText = computed(() => {
  if (progressStatus.value === 'success') return '导入完成'
  if (progressStatus.value === 'exception') return '导入失败'
  if (uploading.value) return `正在导入… ${progressPercent.value}%`
  return ''
})
const downloading = ref(false)

// 维修记录相关
const maintenanceHistoryVisible = ref(false)
const maintenanceHistoryData = ref([])
const currentEquipmentId = ref(null)
const activeWorkOrders = ref([]) // 当前展开的工单
const cachedWorkOrderTasks = ref([]) // 缓存所有工单任务数据

// 按 work_order_id 分组后的数据
const groupedMaintenanceData = computed(() => {
  if (!maintenanceHistoryData.value || maintenanceHistoryData.value.length === 0) {
    return {}
  }
  
  // 第一次分类：按 equipment_id 分组（已经在查询时过滤了）
  // 第二次分类：按 work_order_id 分组
  const groups = {}
  
  maintenanceHistoryData.value.forEach(task => {
    const workOrderId = task.work_order_id
    
    if (!groups[workOrderId]) {
      groups[workOrderId] = {
        work_order_no: task.work_order_id, // 实际使用时可能需要从其他地方获取工单号
        equipment_name: task.equipment_name,
        earliest_start: task.scheduled_start_time,
        latest_end: task.scheduled_end_time,
        tasks: []
      }
    }
    
    groups[workOrderId].tasks.push(task)
    
    // 更新最早开始和最晚结束时间
    if (task.scheduled_start_time < groups[workOrderId].earliest_start) {
      groups[workOrderId].earliest_start = task.scheduled_start_time
    }
    if (task.scheduled_end_time > groups[workOrderId].latest_end) {
      groups[workOrderId].latest_end = task.scheduled_end_time
    }
  })
  
  // 计算每个工单的任务数量
  Object.values(groups).forEach(group => {
    group.task_count = group.tasks.length
    // 格式化时间显示
    group.earliest_start = formatTimeDisplay(group.earliest_start)
    group.latest_end = formatTimeDisplay(group.latest_end)
  })
  
  return groups
})

// 格式化时间显示
function formatTimeDisplay(timeStr) {
  if (!timeStr) return '-'
  // 如果格式是 "第 1 天 08:00"，保持不变
  return timeStr
}

// 获取状态标签类型
function getStatusTagType(status) {
  const statusMap = {
    'pending': 'info',
    'in_progress': 'warning',
    'completed': 'success',
    'cancelled': 'danger'
  }
  return statusMap[status] || 'info'
}

// 获取状态文本
function getStatusText(status) {
  const statusMap = {
    'pending': '待处理',
    'in_progress': '进行中',
    'completed': '已完成',
    'cancelled': '已取消'
  }
  return statusMap[status] || status
}

// 获取人员数量
function getWorkerCount(workers) {
  if (!workers) return 0
  let count = 0
  Object.values(workers).forEach(workerList => {
    count += workerList.length
  })
  return count
}

// 设备查询相关方法
async function handleSearch() {
  ElMessage.info(`查询条件：${JSON.stringify(searchForm)}`)
  // 更新树数据以反映查询结果
  await fetchEquipmentInstances()
  
  // 查找匹配的设备实例并自动选中
  if (searchForm.name || searchForm.equipment_type_name || searchForm.category) {
    const root = treeData.value[0]
    if (root && root.children) {
      // 根据查询条件查找匹配的设备实例
      let matchedInstance = null
      
      // 如果有设备名称，直接查找该设备
      if (searchForm.name) {
        for (const category of root.children) {
          if (!category.children) continue
          for (const kind of category.children) {
            if (!kind.children) continue
            const instance = kind.children.find(child => 
              child.label.toLowerCase().includes(searchForm.name.toLowerCase())
            )
            if (instance) {
              matchedInstance = instance
              break
            }
          }
          if (matchedInstance) break
        }
      } 
      // 如果有设备类型名称，查找该类型下的第一个设备
      else if (searchForm.equipment_type_name) {
        for (const category of root.children) {
          if (!category.children) continue
          const kind = category.children.find(k => k.label === searchForm.equipment_type_name)
          if (kind && kind.children && kind.children.length > 0) {
            matchedInstance = kind.children[0]
            // 选中设备类型节点而不是具体设备实例
            currentNode.value = kind;
            isEditing.value = false;
            ElMessage.success(`已选中设备类型: ${kind.label}`)
            return;
          }
        }
      }
      // 如果只有设备分类，查找该分类下的第一个设备
      else if (searchForm.category) {
        const category = root.children.find(cat => cat.label === searchForm.category)
        if (category && category.children && category.children.length > 0) {
          const kind = category.children[0]
          if (kind && kind.children && kind.children.length > 0) {
            matchedInstance = kind.children[0]
          }
        }
      }
      
      // 如果找到匹配的设备实例，自动选中并显示其信息
      if (matchedInstance) {
        currentNode.value = matchedInstance
        isEditing.value = false
        ElMessage.success(`已选中设备: ${matchedInstance.label}`)
      } else {
        ElMessage.info('未找到匹配的设备')
      }
    }
  }
}

// 处理重置查询
function handleResetSearch() {
  Object.keys(searchForm).forEach(key => {
    searchForm[key] = ''
  })
  ElMessage.success('查询条件已重置')
}

// 底部图标触发文件上传
function triggerFileUpload() {
  // 触发el-upload的文件选择弹窗
  uploadRef.value?.$el.querySelector('input')?.click()
}

// 原有方法
// 页面加载获取设备实例
onMounted(async () => { 
  await fetchEquipmentInstances()
  await fetchWorkOrderTasks() // 页面加载时获取所有工单任务数据
})

// 获取工单任务数据并缓存
async function fetchWorkOrderTasks() {
  try {
    const response = await request({
      url: '/api/work-order-tasks',
      method: 'get'
    })

    // Result 格式：{code: 20000, data: [...]}
    cachedWorkOrderTasks.value = response.data || []
    console.log(`成功加载 ${cachedWorkOrderTasks.value.length} 条工单任务数据`)
  } catch (error) {
    console.error('获取工单任务失败:', error)
    ElMessage.error('获取工单任务失败：' + (error.message || '未知错误'))
  }
}

// 获取设备实例数据
async function fetchEquipmentInstances() {
  try {
    loadingInstances.value = true
    const response = await request({
      url: '/api/equipment-instances',
      method: 'get'
    })
    // 重置树结构
    treeData.value[0].children = []
    // Result 格式：{code: 20000, data: [...]}
    const instances = response.data || []
    
    // 从设备数据中提取所有分类
    const categories = [...new Set(instances.map(instance => instance.category || '其他'))]
    
    // 初始化分类节点
    const categoryMap = {}
    categories.forEach((category, index) => {
      const categoryId = index + 2 // 从2开始，因为根节点是1
      const categoryNode = {
        id: categoryId,
        label: category,
        type: 'category',
        children: []
      }
      treeData.value[0].children.push(categoryNode)
      categoryMap[category] = categoryId
    })
    
    // 按类型分组
    const typeGroups = {}
    instances.forEach(instance => {
      const categoryLabel = instance.category || '其他'
      const equipmentType = instance.equipment_type_name || '未分类'
      if (!typeGroups[categoryLabel]) typeGroups[categoryLabel] = {}
      if (!typeGroups[categoryLabel][equipmentType]) typeGroups[categoryLabel][equipmentType] = []
      typeGroups[categoryLabel][equipmentType].push(instance)
    })
    
    // 构建树节点
    Object.keys(typeGroups).forEach(categoryLabel => {
      const categoryId = categoryMap[categoryLabel]
      const categoryNode = treeData.value[0].children.find(node => node.id === categoryId)
      if (categoryNode) {
        Object.keys(typeGroups[categoryLabel]).forEach((equipmentType, typeIndex) => {
          const kindNode = {
            id: categoryId * 100 + typeIndex + 1,
            label: equipmentType,
            type: 'kind',
            children: []
          }
          // 添加实例节点
          typeGroups[categoryLabel][equipmentType].forEach(instance => {
            kindNode.children.push({
              id: instance.id,
              label: instance.name,
              type: 'instance',
              ...instance
            })
          })
          categoryNode.children.push(kindNode)
        })
      }
    })
  } catch (error) {
    ElMessage.error('获取设备实例数据失败: ' + (error.message || '未知错误'))
    console.error('获取设备实例数据失败:', error)
  } finally {
    loadingInstances.value = false
  }
}
// 节点点击事件
function handleNodeClick(node) {
  currentNode.value = node
  isEditing.value = false
}

// 选择设备实例（从表格中点击查看）
function selectEquipmentInstance(row) {
  currentNode.value = row;
}

// 查看历史维修记录
async function viewMaintenanceHistory(equipment) {
  currentEquipmentId.value = equipment.id
  maintenanceHistoryVisible.value = true
  
  // 使用缓存的数据，不再请求接口
  if (cachedWorkOrderTasks.value.length === 0) {
    ElMessage.warning('暂无工单任务数据')
    maintenanceHistoryData.value = []
    return
  }
  
  // 从缓存数据中按 equipment_id 过滤出当前设备的任务
  const equipmentTasks = cachedWorkOrderTasks.value.filter(task => 
    task.equipment_id === equipment.id
  )
  
  if (equipmentTasks.length === 0) {
    maintenanceHistoryData.value = []
    ElMessage.info('该设备暂无维修记录')
  } else {
    maintenanceHistoryData.value = equipmentTasks
    ElMessage.success(`加载了 ${equipmentTasks.length} 条维修任务`)
  }
}

// 生成模拟的维修记录数据
function generateMockMaintenanceData(equipmentId) {
  const maintenanceTypes = ['定期保养', '故障维修', '紧急抢修', '预防性维护', '大修']
  const faultDescriptions = [
    '设备运行异常，噪音过大',
    '轴承温度过高，需要更换',
    '密封件老化导致泄漏',
    '电机烧毁，需要重新绕制',
    '传动皮带磨损严重',
    '润滑系统故障',
    '控制系统信号异常',
    '液压系统压力不足',
    '过滤器堵塞',
    '传感器失灵'
  ]
  const maintenanceContents = [
    '更换轴承并添加润滑油',
    '更换密封件，清理结合面',
    '重新绕制电机线圈',
    '调整传动皮带张紧度',
    '清洗润滑系统，更换滤芯',
    '检查控制线路，更换继电器',
    '更换液压泵，补充液压油',
    '清洗或更换过滤器',
    '校准传感器，更换损坏线路',
    '全面检查设备，更换磨损件'
  ]
  const statuses = ['已完成', '已完成', '已完成', '进行中']
  
  // 工单任务类型
  const workOrderTasks = [
    '设备巡检与状态监测',
    '零部件更换与调试',
    '润滑系统维护保养',
    '电气系统检修',
    '机械传动系统维护',
    '液压系统故障排查',
    '控制系统程序更新',
    '安全装置检测与校准',
    '设备精度测试与调整',
    '预防性维护检查',
    '应急故障处理',
    '设备性能优化改造'
  ]
  
  // 生成 3-8 条模拟数据
  const recordCount = Math.floor(Math.random() * 6) + 3
  const records = []
  
  for (let i = 0; i < recordCount; i++) {
    const date = new Date()
    date.setDate(date.getDate() - Math.floor(Math.random() * 365))
    
    // 生成工单编号：WO + 年份 + 月份 + 流水号
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const serialNo = String(Math.floor(Math.random() * 9999) + 1).padStart(4, '0')
    const workOrderNo = `WO${year}${month}${serialNo}`
    
    records.push({
      record_id: `WX${equipmentId}-${String(i + 1).padStart(3, '0')}`,
      work_order_no: workOrderNo,
      work_order_task: workOrderTasks[Math.floor(Math.random() * workOrderTasks.length)],
      maintenance_date: date.toISOString().split('T')[0],
      maintenance_type: maintenanceTypes[Math.floor(Math.random() * maintenanceTypes.length)],
      fault_description: faultDescriptions[Math.floor(Math.random() * faultDescriptions.length)],
      maintenance_content: maintenanceContents[Math.floor(Math.random() * maintenanceContents.length)],
      maintainer: `维修人员${String.fromCharCode(65 + Math.floor(Math.random() * 26))}`,
      status: statuses[Math.floor(Math.random() * statuses.length)]
    })
  }
  
  // 按日期降序排序
  return records.sort((a, b) => new Date(b.maintenance_date) - new Date(a.maintenance_date))
}

// 获取维修类型标签颜色
function getMaintenanceTypeTag(type) {
  const typeMap = {
    '定期保养': 'success',
    '故障维修': 'danger',
    '紧急抢修': 'warning',
    '预防性维护': 'primary',
    '大修': 'info'
  }
  return typeMap[type] || ''
}

// 编辑设备
function editEquipment(row) {
  Object.keys(row).forEach(key => { currentEquipment[key] = row[key] })
  isEditing.value = true
}
// 保存设备修改
async function saveEquipment() {
  try {
    ElMessage.success('设备信息已更新')
    isEditing.value = false
    await fetchEquipmentInstances()
  } catch (error) {
    ElMessage.error('更新设备信息失败: ' + (error.message || '未知错误'))
  }
}
// 删除设备
function deleteEquipment(row) {
  ElMessageBox.confirm(
    `确定要删除设备 "${row.name}" 吗？此操作不可恢复。`,
    '确认删除',
    { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
  ).then(async () => {
    try {
      await request({
        url: `/api/equipment-instances/${row.id}`,
        method: 'delete'
      })
      ElMessage.success('设备已删除')
      await fetchEquipmentInstances()
    } catch (error) {
      ElMessage.error('删除设备失败: ' + (error.message || '未知错误'))
    }
  })
}
// 分页方法
function handleSizeChange(newSize) {
  pageSize.value = newSize
  currentPage.value = 1
}
function handleCurrentChange(newPage) {
  currentPage.value = newPage
}
// 下载模板
async function downloadTemplate() {
  try {
    downloading.value = true
    // 直接从public目录下载Excel模板文件
    const link = document.createElement('a')
    link.href = '/设备实例表模版.xlsx'
    link.download = '设备实例表模版.xlsx'
    link.click()
    ElMessage.success('模板开始下载')
  } catch {
    ElMessage.error('模板下载失败')
  } finally {
    downloading.value = false
  }
}
// 文件选择变化
function handleFileChange(file) {
  selectedFile.value = file?.raw || null
  selectedFileName.value = file?.name || ''
  // 选择文件后直接预览数据
  if (selectedFile.value) {
    previewData()
  }
}
// 预览数据
function previewData() {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择要导入的文件')
    return
  }
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const data = new Uint8Array(e.target.result)
      const workbook = XLSX.read(data, { type: 'array' })
      const firstSheetName = workbook.SheetNames[0]
      const worksheet = workbook.Sheets[firstSheetName]
      // 将Excel转换为JSON，使用列标题作为对象字段
      const jsonData = XLSX.utils.sheet_to_json(worksheet)
      // 生成列定义
      if (jsonData.length > 0) {
        // 定义字段映射，将英文字段名映射为中文标题
        const labelMap = {
          id: '设备ID',
          equipment_name: '设备名称',
          equipment_category: '设备分类',
          created_time: '创建时间',
          equipment_type_id: '设备类型ID',
          equipment_type_name: '设备类型名称',
        
        }
        excelColumns.value = Object.keys(jsonData[0]).map(key => ({
          prop: key, label: labelMap[key] || key, width: 150
        }))
      } else {
        excelColumns.value = [
          { prop: 'id', label: '设备ID', width: 100 },
          { prop: 'name', label: '设备名称', width: 150 },
          { prop: 'type', label: '设备类型', width: 120 }
        ]
      }
      excelData.value = jsonData
      excelEditorVisible.value = true
    } catch (error) {
      ElMessage.error('文件解析失败: ' + error.message)
    }
  }
  reader.readAsArrayBuffer(selectedFile.value)
}
// 确认导入 - 核心修改：添加自动消失的定时器
async function confirmImport(data) {
  try {
    // 显示进度
    uploading.value = true
    progressVisible.value = true
    progressStatus.value = undefined
    progressPercent.value = 30 // 模拟处理中
    
    // 构造请求数据，以equipment_list为键，值为Excel转换的JSON数组
    const requestData = {
      equipment_list: data
    }
    
    // 发送POST请求到批量导入接口
    await request({
      url: '/api/batch-import-equipment',
      method: 'post',
      data: requestData,
      // 监听请求进度
      onUploadProgress: (progressEvent) => {
        const percent = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 1))
        progressPercent.value = percent
      }
    })
    
    // 导入成功处理
    uploading.value = false
    tipType.value = 'success'
    tipMessage.value = '批量导入成功'
    tipVisible.value = true
    progressPercent.value = 100
    progressStatus.value = 'success'
    ElMessage.success('批量导入成功')
    
    // 3秒后自动隐藏成功提示
    setTimeout(() => {
      tipVisible.value = false
      progressVisible.value = false
    }, 1500)
    
    // 重置状态
    selectedFile.value = null
    selectedFileName.value = ''
    excelEditorVisible.value = false
    
    // 刷新数据
    await fetchEquipmentInstances()
  } catch (error) {
    // 导入失败处理
    uploading.value = false
    tipType.value = 'error'
    tipMessage.value = '批量导入失败: ' + (error.message || '未知错误')
    tipVisible.value = true
    progressStatus.value = 'exception'
    ElMessage.error('批量导入失败: ' + (error.message || '未知错误'))
  }
}
// 上传前校验
function handleBeforeUpload(file) {
  const isAllowedType =
    file.type === 'text/csv' ||
    file.type === 'application/vnd.ms-excel' ||
    file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isAllowedType) {
    ElMessage.error('仅支持 CSV 或 Excel 文件')
    return false
  }
  if (!isLt10M) {
    ElMessage.error('文件大小不能超过 10MB')
    return false
  }
  return true
}
// 显示添加设备对话框
function showAddEquipmentDialog() {
  newEquipment.type_id = ''
  newEquipment.name = ''
  newEquipment.category = ''
  addDialogVisible.value = true
}
// 添加设备
async function addEquipment() {
  if (!newEquipment.type_id || !newEquipment.name || !newEquipment.category) {
    ElMessage.warning('请填写完整的设备信息，包括设备类型ID、设备名称和设备分类')
    return
  }
  try {
    await request({
      url: '/api/add-equipment',
      method: 'post',
      data: {
        equipment_type_id: newEquipment.type_id,
        equipment_name: newEquipment.name,
        equipment_category: newEquipment.category
      }
    })
    ElMessage.success('设备添加成功')
    addDialogVisible.value = false
    await fetchEquipmentInstances()
  } catch (error) {
    ElMessage.error('添加设备失败: ' + (error.message || '未知错误'))
  }
}
</script>

<style scoped>
.import-card {
  min-height: calc(100vh - 100px);
  border: none;
  box-shadow: 0 4px 24px 0 rgba(0, 0, 0, 0.04);
  border-radius: 12px;
  padding-bottom: 16px;
  background: #ffffff;
}
.title {
  margin: 0 0 24px 0;
  font-weight: 600;
  font-size: 20px;
  color: #1a1a1a;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f2f5;
}
.two-col {
  display: grid;
  grid-template-columns: 1fr 1px 1fr;
  align-items: start;
  gap: 0;
  margin: 20px 0;
}
.col {
  min-height: 260px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 16px 12px;
}
.divider {
  width: 1px;
  background: #e5e7eb;
  height: 260px;
  margin: auto 0;
}
.step-title {
  color: #606266;
  margin-bottom: 10px;
}
.excel-icon {
  width: 100px;
  height: 100px;
  background: #1f9d55;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-weight: 800;
  font-size: 60px;
  line-height: 1;
  user-select: none;
  margin-bottom: 12px;
}
.choose-btn {
  margin-bottom: 8px;
}
.fileline {
  color: #606266;
  font-size: 13px;
  cursor: pointer;
  margin-bottom: 12px;
}
.paperclip {
  margin-right: 6px;
}
.import-btn {
  width: 120px;
}
.progress-wrap {
  margin-top: 16px;
  display: grid;
  gap: 6px;
}
.result-tip {
  margin-top: 16px;
}
.progress-text {
  text-align: center;
  font-size: 12px;
  color: #606266;
}
/* 树状结构布局 */
.tree-layout {
  display: flex;
  height: 600px;
  margin-top: 20px;
  border: 1px solid #f0f2f5;
  border-radius: 12px;
  overflow: hidden;
}
.tree-panel {
  width: 240px;
  background: #f8fafc;
  padding: 16px;
  border-right: 1px solid #f0f2f5;
}
.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.filter-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}
.filter-form {
  margin-bottom: 16px;
  padding: 12px;
  background: white;
  border-radius: 8px;
  border: 1px solid #f0f2f5;
}
.tree-panel h3 {
  margin: 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}
.tree-node {
  display: flex;
  align-items: center;
  font-size: 14px;
}
.tree-node-icon {
  margin-right: 8px;
  font-size: 16px;
  color: #3b82f6;
  width: 16px;
  height: 16px;
}
.custom-tree {
  width: 100%;
  max-height: 500px;
  overflow-y: auto;
  background: transparent;
}
.content-panel {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}
.equipment-detail {
  padding: 24px;
  border: none;
  border-radius: 12px;
  background: #f8fafc;
}
.equipment-detail h3 {
  margin: 0 0 20px 0;
  color: #1e293b;
  font-weight: 600;
}
.action-buttons {
  margin-top: 24px;
  display: flex;
  gap: 12px;
}
.category-info, .kind-info {
  padding: 24px;
  border: none;
  border-radius: 12px;
  background: #f8fafc;
  text-align: center;
}
.placeholder {
  text-align: center;
  color: #94a3b8;
  padding: 40px 0;
}

/* 设备实例计数组件样式 */
.device-count-panel {
  background-color: #f0fdf4;
  color: #166534;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  font-weight: 500;
  text-align: center;
  border: none;
}

.device-count-number {
  font-weight: 700;
  font-size: 18px;
}

/* 设备查询组件样式 */
.equipment-search-container {
  margin: 0 0 24px 0;
  padding: 24px;
  border: none;
  border-radius: 12px;
  background: #f8fafc;
}
.search-title {
  margin: 0 0 20px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}
.search-form {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  align-items: center;
}

.search-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.search-form :deep(.el-form-item__label) {
  font-weight: 500;
  color: #475569;
}

.search-input, .search-select, .search-date {
  width: 220px;
}

.search-input :deep(.el-input__wrapper),
.search-select :deep(.el-input__wrapper),
.search-date :deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
}

.search-btn-group {
  margin-left: auto;
  display: flex;
  gap: 12px;
}

.search-btn-group .el-button {
  border-radius: 8px;
  padding: 8px 24px;
  font-weight: 500;
}

/* 底部功能图标区样式 */
.bottom-function-icons {
  position: relative;
  gap: 16px;
  display: flex;
  margin-top: 24px;
  margin-left: 0;
  padding-top: 24px;
  border-top: 1px solid #f0f2f5;
}
.icon-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  transition: all 0.3s ease;
  padding: 12px;
  border-radius: 12px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  width: 48px;
  height: 48px;
  justify-content: center;
  position: relative;
}
.icon-item:hover {
  background: #eff6ff;
  border-color: #bfdbfe;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
}
.icon-item:hover::after {
  content: attr(title);
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  background: #333;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
  z-index: 1000;
  margin-bottom: 8px;
}
.icon-item:hover::before {
  content: "";
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 5px solid transparent;
  border-top-color: #333;
  margin-bottom: 3px;
}
.function-icon {
  font-size: 20px;
  color: #409eff;
  width: 24px;
  height: 24px;
  transition: filter 0.3s ease;
}
.icon-item:hover .function-icon {
  filter: brightness(0) saturate(100%) invert(41%) sepia(88%) saturate(746%) hue-rotate(190deg) brightness(101%) contrast(101%);
}
.icon-label {
  display: none;
}

/* 历史维修记录弹窗样式 */
.maintenance-history-container {
  padding: 10px;
}

.work-order-header {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.work-order-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #606266;
  font-size: 14px;
}

.work-order-info .el-icon {
  margin-right: 4px;
}

/* 工人信息显示样式 */
.worker-display {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  justify-content: center;
}

.worker-tag {
  margin: 2px;
}

.worker-detail-row {
  margin-bottom: 12px;
  padding: 8px;
  background: #f5f7fa;
  border-radius: 4px;
}

.worker-detail-row:last-child {
  margin-bottom: 0;
}

.worker-detail-row strong {
  display: block;
  margin-bottom: 6px;
  color: #606266;
  font-size: 13px;
}

.worker-names {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.worker-name-tag {
  font-size: 12px;
}

.no-workers {
  text-align: center;
  color: #999;
  padding: 12px 0;
}

/* 响应式调整 */
@media (max-width: 920px) {
  .import-card { width: 100%; }
  .two-col { grid-template-columns: 1fr; }
  .divider { display: none; }
  .tree-layout {
    flex-direction: column;
    height: auto;
  }
  .tree-panel {
    width: 100%;
    height: 150px;
  }
  .content-panel { height: auto; }
  .search-form { flex-direction: column; align-items: stretch; }
  .search-input, .search-select, .search-date { width: 100%; }
  .search-btn-group { margin-left: 0; justify-content: flex-end; }
  .bottom-function-icons { gap: 20px; }
  .function-icon { 
    font-size: 24px;
    width: 24px;
    height: 24px;
  }
}
</style>