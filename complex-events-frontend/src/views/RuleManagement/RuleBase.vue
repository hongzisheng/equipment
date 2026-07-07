<template>
  <el-card class="import-card" shadow="hover">
    <h2 class="title">规则库</h2>

    <!-- 添加设备查询组件 -->
    <div class="equipment-search-container">
      <h3 class="search-title">规则查询</h3>
      <el-form :model="filterForm" class="search-form" label-width="120px" size="medium">
        <el-form-item label="设备种类">
          <el-input
            v-model="filterForm.equipmentType"
            placeholder="请输入设备种类"
            clearable
            class="search-input"
            @clear="resetFilter"
          />
        </el-form-item>
        <el-form-item class="search-btn-group">
          <el-button type="primary" size="medium" @click="fetchRuleData">查询</el-button>
          <el-button size="medium" @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

  

    <el-upload
      ref="uploadRef"
      class="upload-custom"
      :action="uploadUrl"
      :data="{ type: 'rule' }"
      :auto-upload="false"
      :show-file-list="false"
      :before-upload="handleBeforeUpload"
      :on-change="handleFileChange"
      :on-success="handleSuccess"
      :on-error="handleError"
      :on-progress="handleProgress"
      accept=".xlsx,.xls,.csv"
      style="display: none;"
    >
      <template #trigger>
        <el-button class="choose-btn" plain>选择文件</el-button>
      </template>
    </el-upload>

    <!-- 进度条显示上传进度与状态 -->
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
      title="规则数据编辑"
      :data="excelData"
      :columns="excelColumns"
      @confirm="confirmImport"
    />
    
    <!-- 第一层：规则数据表格 -->
    <div class="rule-table-section">
      <div class="section-header">
        <h3>工序规则数据列表</h3>
      </div>
      <el-table 
        :data="paginatedRuleData" 
        v-loading="loadingRules"
        style="width: 100%"
        stripe
        height="600"
      >
        <!-- 第一层列：显示对象键 -->
        
        <!-- 第一层列：显示name字段 -->
        <el-table-column
          prop="name"
          label="设备种类"
          min-width="150"
        />
        <!-- 操作列：查看工序 -->
        <el-table-column
          label="操作"
          width="120"
          fixed="right"
        >
          <template #default="scope">
            <el-button 
              type="primary" 
              link 
              size="small"
              @click="viewProcesses(scope.row)"
            >
              查看工序
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页组件 -->
      <div class="pagination">
        <el-pagination
          :current-page="currentPage"
          :page-size="pageSize"
          :page-sizes="[10]"
          :total="totalRuleData"
          layout="total, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>

    <!-- 新增：工种计费规则列表 -->
    <div class="worker-price-section">
      <div class="section-header">
        <h3>工种计费规则</h3>
        <el-button type="primary" size="small" @click="handleAddWorker">新增工种</el-button>
      </div>
      <el-table
        :data="paginatedWorkerTypes"
        v-loading="loadingWorkers"
        stripe
        height="400"
        style="width: 100%"
      >
        <el-table-column prop="id" label="工种ID" width="150" />
        <el-table-column prop="name" label="名称" min-width="120" />
        <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip />
        <el-table-column prop="price" label="价格（元）" width="120" />
        <el-table-column prop="requires_certification" label="需要认证" width="100">
          <template #default="scope">
            {{ scope.row.requires_certification ? '是' : '否' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="scope">
            <el-button type="primary" link @click="editWorker(scope.row)">编辑</el-button>
            <el-button type="danger" link @click="deleteWorker(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination">
        <el-pagination
          v-model:current-page="workerCurrentPage"
          :page-size="workerPageSize"
          :page-sizes="[10, 20, 50]"
          :total="workerTypes.length"
          layout="total, prev, pager, next"
          @size-change="handleWorkerSizeChange"
          @current-change="handleWorkerCurrentChange"
        />
      </div>
    </div>

    <!-- 第二层：工序表格弹窗 -->
    <el-dialog
      v-model="processDialogVisible"
      :title="`工序列表 - ${currentRuleName}`"
      width="90%"
      top="3vh"
    >
      <div style="margin-bottom: 15px; text-align: right;">
        <el-button 
          type="primary" 
          size="small" 
          @click="showAddProcessForm"
          style="float: left;"
        >
          新增工序
        </el-button>
        <el-input
          v-model="processFilterForm.description"
          placeholder="请输入工序代码、名称或描述"
          clearable
          style="width: 300px;"
          @clear="resetProcessFilter"
        >
          <template #append>
            <el-button @click="resetProcessFilter">重置</el-button>
          </template>
        </el-input>
      </div>
      
      <el-table 
        :data="paginatedProcesses" 
        stripe
        height="1000"
        :row-class-name="tableRowClassName"
      >
        <!-- 动态生成工序列 -->
        <el-table-column
          v-for="column in processColumns"
          :key="column.prop"
          :prop="column.prop"
          :label="column.label"
          :min-width="column.width || 120"
        >
          <template #default="scope" v-if="column.prop === 'is_major_process'">
            {{ scope.row[column.prop] ? '是' : '否' }}
          </template>
        </el-table-column>
        
        <!-- 工种信息列 -->
        <el-table-column
          label="需要工种"
          min-width="200"
        >
          <template #default="scope">
            <div v-if="scope.row.required_workers && Object.keys(scope.row.required_workers).length > 0">
              <div 
                v-for="(worker, index) in scope.row.required_workers" 
                :key="index"
                class="worker-item"
              >
                <span class="worker-type">{{ index }}</span>
                <span class="worker-count">({{ worker }}名)</span>
              </div>
            </div>
            <div v-else class="no-workers">
              无工种要求
            </div>
          </template>
        </el-table-column>
        
        <!-- 物料需求列 -->
        <el-table-column
          label="物料需求"
          min-width="200"
        >
          <template #default="scope">
            <div v-if="scope.row.material_requirements">
              <div 
                v-for="(material, index) in scope.row.material_requirements.split(/[、,]/)" 
                :key="index"
                class="material-item"
              >
                {{ formatMaterialRequirement(material.trim()) }}
              </div>
            </div>
            <div v-else class="no-materials">
              无物料需求
            </div>
          </template>
        </el-table-column>
        
        <!-- 工具需求列 -->
        <el-table-column
          label="工具需求"
          min-width="200"
        >
          <template #default="scope">
            <div v-if="scope.row.tools_requirements">
              <div 
                v-for="(tool, index) in scope.row.tools_requirements.split(/[、,]/)" 
                :key="index"
                class="tool-item"
              >
                {{ formatMaterialRequirement(tool.trim()) }}
              </div>
            </div>
            <div v-else class="no-tools">
              无工具需求
            </div>
          </template>
        </el-table-column>
        
        <!-- 操作列 -->
        <el-table-column
          label="操作"
          width="150"
          fixed="right"
        >
          <template #default="scope">
            <el-button 
              type="primary" 
              size="small"
              @click="editProcess(scope.row)"
            >
              编辑
            </el-button>
            <el-button 
              type="danger" 
              size="small"
              @click="deleteProcess(scope.row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 移除第二层分页 -->
      <!-- 
      <div class="pagination">
        <el-pagination
          :current-page="currentProcessPage"
          :page-size="1000"
          :page-sizes="[10]"
          :total="totalProcesses"
          layout="total, prev, pager, next"
          @size-change="handleProcessSizeChange"
          @current-change="handleProcessCurrentChange"
        />
      </div>
      -->
    </el-dialog>
    
    <!-- 新增工序对话框 -->
    <el-dialog
      v-model="addProcessDialogVisible"
      title="新增工序"
      width="50%"
      top="5vh"
    >
      <el-form :model="addProcessForm" label-width="120px">
        <el-form-item label="工序代码" required>
          <el-input v-model="addProcessForm.process_code" />
        </el-form-item>
        
        <el-form-item label="工序描述">
          <el-input v-model="addProcessForm.description" type="textarea" />
        </el-form-item>
        
        <el-form-item label="预计工时(小时)">
          <el-input-number 
            v-model="addProcessForm.estimated_hours" 
            :min="0" 
            :step="0.5"
            controls-position="right"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="前置工序代码">
          <el-input 
            v-model="addProcessForm.predecessor_codes" 
            placeholder="多个工序代码用逗号分隔"
          />
        </el-form-item>
        
        <el-form-item label="父工序代码">
          <el-input v-model="addProcessForm.parent_process_code" />
        </el-form-item>
        
        <el-form-item label="是否大工序">
          <el-switch v-model="addProcessForm.is_major_process" />
        </el-form-item>
        
        <el-form-item label="物料需求">
          <el-input 
            v-model="addProcessForm.material_requirements" 
            type="textarea"
            placeholder="例如: 氧气0.100m³、氮气0.200m³"
          />
        </el-form-item>
        
        <el-form-item label="物料费用">
          <el-input-number 
            v-model="addProcessForm.material_price" 
            :min="0"
            :step="0.1"
            controls-position="right"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="工具需求">
          <el-input 
            v-model="addProcessForm.tools_requirements" 
            type="textarea"
            placeholder="例如: 扳手、螺丝刀"
          />
        </el-form-item>
        
        <el-form-item label="工具费用">
          <el-input-number 
            v-model="addProcessForm.tools_price" 
            :min="0"
            :step="0.1"
            controls-position="right"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="需要工种">
          <div class="worker-types-container">
            <div 
              v-for="(count, workerType) in addProcessForm.required_workers" 
              :key="workerType"
              class="worker-type-item"
            >
              <span class="worker-type-name">{{ workerType }}</span>
              <el-input-number 
                v-model="addProcessForm.required_workers[workerType]" 
                :min="1"
                size="small"
                controls-position="right"
                style="width: 100px; margin: 0 10px;"
              />
              <el-button 
                type="danger" 
                size="small" 
                @click="removeWorkerTypeFromNew(workerType)"
              >
                删除
              </el-button>
            </div>
            <el-button 
              type="primary" 
              size="small" 
              @click="addWorkerTypeToNew"
              style="margin-top: 10px;"
            >
              添加工种
            </el-button>
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="addProcessDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitAddProcess">保存</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 编辑工序对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑工序"
      width="50%"
      top="5vh"
    >
      <el-form :model="editProcessForm" label-width="120px">
        <el-form-item label="工序代码">
          <el-input v-model="editProcessForm.process_code" disabled />
        </el-form-item>
        
        <el-form-item label="工序描述">
          <el-input v-model="editProcessForm.description" type="textarea" />
        </el-form-item>
        
        <el-form-item label="预计工时(小时)">
          <el-input-number 
            v-model="editProcessForm.estimated_hours" 
            :min="0" 
            :step="0.5"
            controls-position="right"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="前置工序代码">
          <el-input 
            v-model="editProcessForm.predecessor_codes" 
            placeholder="多个工序代码用逗号分隔"
          />
        </el-form-item>
        
        <el-form-item label="父工序代码">
          <el-input v-model="editProcessForm.parent_process_code" />
        </el-form-item>
        
        <el-form-item label="是否大工序">
          <el-switch v-model="editProcessForm.is_major_process" />
        </el-form-item>
        
        <el-form-item label="物料需求">
          <el-input 
            v-model="editProcessForm.material_requirements" 
            type="textarea"
            placeholder="例如: 氧气0.100m³、氮气0.200m³"
          />
        </el-form-item>
        
        <el-form-item label="物料费用">
          <el-input-number 
            v-model="editProcessForm.material_price" 
            :min="0"
            :step="0.1"
            controls-position="right"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="工具需求">
          <el-input 
            v-model="editProcessForm.tools_requirements" 
            type="textarea"
            placeholder="例如: 扳手、螺丝刀"
          />
        </el-form-item>
        
        <el-form-item label="工具费用">
          <el-input-number 
            v-model="editProcessForm.tools_price" 
            :min="0"
            :step="0.1"
            controls-position="right"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="需要工种">
          <div class="worker-types-container">
            <div 
              v-for="(count, workerType) in editProcessForm.required_workers" 
              :key="workerType"
              class="worker-type-item"
            >
              <span class="worker-type-name">{{ workerType }}</span>
              <el-input-number 
                v-model="editProcessForm.required_workers[workerType]" 
                :min="1"
                size="small"
                controls-position="right"
                style="width: 100px; margin: 0 10px;"
              />
              <el-button 
                type="danger" 
                size="small" 
                @click="removeWorkerType(workerType)"
              >
                删除
              </el-button>
            </div>
            <el-button 
              type="primary" 
              size="small" 
              @click="addWorkerType"
              style="margin-top: 10px;"
            >
              添加工种
            </el-button>
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="updateProcess">保存</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 新增/编辑工种对话框 -->
    <el-dialog
      v-model="workerDialogVisible"
      :title="editingWorker ? '编辑工种' : '新增工种'"
      width="500px"
      top="10vh"
    >
      <el-form :model="workerForm" label-width="100px">
        <el-form-item label="工种ID" required>
          <el-input v-model="workerForm.id" :disabled="!!editingWorker" />
        </el-form-item>
        <el-form-item label="名称" required>
          <el-input v-model="workerForm.name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="workerForm.description" type="textarea" />
        </el-form-item>
        <el-form-item label="价格">
          <el-input-number v-model="workerForm.price" :min="0" controls-position="right" style="width: 100%" />
        </el-form-item>
        <el-form-item label="需要认证">
          <el-switch v-model="workerForm.requires_certification" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="workerDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitWorker">保存</el-button>
      </template>
    </el-dialog>
    
      <!-- 底部功能图标区 -->
    <div class="bottom-function-icons">
      <!-- 图标1：下载模板 -->
      <div class="icon-item" @click="downloadTemplate" title="下载Excel模板">
        <img src="@/assets/iconfont/下载.png" class="function-icon" alt="下载Excel模板" />
      </div>
      <!-- 图标2：导入文件 -->
      <div class="icon-item" @click="triggerFileUpload" title="上传Excel文件">
        <img src="@/assets/iconfont/上传.png" class="function-icon" alt="上传Excel文件" />
      </div>
    </div>

  </el-card>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as XLSX from 'xlsx'
import ExcelEditor from './ExcelEditor.vue'
import request from '@/utils/request'

const uploading = ref(false)
const uploadRef = ref()
const selectedFile = ref(null)
const selectedFileName = ref('')
const columnMapping = {
  '设备类型ID': 'equipment_type_id',
  '工序代码': 'process_code',
  '工序描述': 'description',
  '预计工时(小时)': 'estimated_hours',
  '需要工种': 'required_workers',
  '前置工序代码': 'predecessor_codes',
  '父工序代码': 'parent_process_code',
  '是否大工序': 'is_major_process',
  '物料需求': 'material_requirements',
  '物料费用': 'material_price',
  '工具需求': 'tools_requirements',
  '工具费用': 'tools_price'
  // 可继续添加其他映射
}
// 筛选相关
const filterForm = reactive({
  equipmentType: ''  // 设备种类筛选
})

// Excel编辑器相关
const excelEditorVisible = ref(false)
const excelData = ref([])
const excelColumns = ref([])

// 规则数据相关 - 三层嵌套结构
const allRuleData = ref({})  // 存储原始的三层嵌套对象
const loadingRules = ref(false)

// 计算筛选后的规则数据
const filteredRuleData = computed(() => {
  if (!filterForm.equipmentType) {
    return allRuleData.value
  }
  
  const filtered = {}
  Object.entries(allRuleData.value).forEach(([key, value]) => {
    if (value.name && value.name.includes(filterForm.equipmentType)) {
      filtered[key] = value
    }
  })
  
  return filtered
})

// 第一层分页参数
const currentPage = ref(1)
const pageSize = ref(10)

// 第二层相关状态
const processDialogVisible = ref(false)
const currentRuleKey = ref('')
const currentRuleName = ref('')
const sortedProcesses = ref([]) // 存储排序后的工序

// 工序筛选相关
const processFilterForm = reactive({
  description: ''  // 工序描述筛选
})

// 计算筛选后的工序数据
const filteredProcesses = computed(() => {
  if (!processFilterForm.description) {
    return sortedProcesses.value
  }
  
  return sortedProcesses.value.filter(process => {
    // 检查工序描述是否匹配
    const descriptionMatch = process.description && 
      process.description.includes(processFilterForm.description)
    
    // 检查工序名称是否匹配
    const nameMatch = process.name && 
      process.name.includes(processFilterForm.description)
    
    // 检查工序代码是否匹配
    const codeMatch = process.process_code && 
      process.process_code.includes(processFilterForm.description)
    
    return descriptionMatch || nameMatch || codeMatch
  })
})

const processColumns = ref([])
const currentProcessPage = ref(1)

// 计算第一层分页数据
const paginatedRuleData = computed(() => {
  const startIndex = (currentPage.value - 1) * pageSize.value
  const endIndex = startIndex + pageSize.value
  return Object.entries(filteredRuleData.value)
    .slice(startIndex, endIndex)
    .map(([key, value]) => ({
      key,
      name: value.name || '未命名'
    }))
})

// 计算第二层分页数据
const paginatedProcesses = computed(() => {
  // 移除分页限制，显示所有数据
  return filteredProcesses.value
  // const startIndex = (currentProcessPage.value - 1) * processPageSize.value
  // const endIndex = startIndex + processPageSize.value
  // return filteredProcesses.value.slice(startIndex, endIndex)
})

const totalRuleData = computed(() => Object.keys(filteredRuleData.value).length)

// 工种计费规则相关状态
const workerTypes = ref([])
const loadingWorkers = ref(false)
const workerDialogVisible = ref(false)
const editingWorker = ref(null)
const workerForm = reactive({
  id: '',
  name: '',
  description: '',
  price: 0,
  requires_certification: false
})

// 工种分页
const workerCurrentPage = ref(1)
const workerPageSize = ref(10)

const paginatedWorkerTypes = computed(() => {
  const start = (workerCurrentPage.value - 1) * workerPageSize.value
  const end = start + workerPageSize.value
  return workerTypes.value.slice(start, end)
})

// 保留的后端接口地址
const uploadUrl = '/api/import'

const tipVisible = ref(false)
const tipMessage = ref('')
const tipType = ref('success')

// 进度状态
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

// 页面加载时获取规则数据和工种数据
onMounted(() => {
  fetchRuleData()
  fetchWorkerTypes()
})

// 获取规则数据
async function fetchRuleData() {
  try {
    loadingRules.value = true
    const response = await request({
      url: 'http://localhost:5000/api/all-process-templates',
      method: 'get'
    })
    
    // 存储原始的三层嵌套对象
    console.log(response)
    allRuleData.value = response.equipment_processes || {}
    
  } catch (error) {
    ElMessage.error('获取规则数据失败: ' + (error.message || '未知错误'))
    console.error('获取规则数据失败:', error)
  } finally {
    loadingRules.value = false
  }
}

// 获取工种数据
async function fetchWorkerTypes() {
  try {
    loadingWorkers.value = true
    const response = await request({
      url: 'http://localhost:5000/api/worker-types',
      method: 'get'
    })
    // 假设返回格式为 { success: true, data: [...] } 或直接数组
    if (Array.isArray(response)) {
      workerTypes.value = response
    } else if (response.data && Array.isArray(response.data)) {
      workerTypes.value = response.data
    } else {
      workerTypes.value = []
    }
  } catch (error) {
    ElMessage.error('获取工种数据失败: ' + (error.message || '未知错误'))
    console.error(error)
  } finally {
    loadingWorkers.value = false
  }
}

// 新增工种
function handleAddWorker() {
  editingWorker.value = null
  workerForm.id = ''
  workerForm.name = ''
  workerForm.description = ''
  workerForm.price = 0
  workerForm.requires_certification = false
  workerDialogVisible.value = true
}

// 编辑工种
function editWorker(row) {
  editingWorker.value = row
  workerForm.id = row.id
  workerForm.name = row.name
  workerForm.description = row.description || ''
  workerForm.price = row.price || 0
  workerForm.requires_certification = row.requires_certification || false
  workerDialogVisible.value = true
}

// 提交工种（新增/编辑）
async function submitWorker() {
  if (!workerForm.id || !workerForm.name) {
    ElMessage.error('工种ID和名称不能为空')
    return
  }
  try {
    const url = editingWorker.value 
      ? `http://localhost:5000/api/worker-types/${workerForm.id}`
      : 'http://localhost:5000/api/worker-types'
    const method = editingWorker.value ? 'put' : 'post'
    
    const response = await request({
      url,
      method,
      data: {
        id: workerForm.id,
        name: workerForm.name,
        description: workerForm.description,
        price: workerForm.price,
        requires_certification: workerForm.requires_certification
      }
    })
    
    if (response.success) {
      ElMessage.success(editingWorker.value ? '更新成功' : '创建成功')
      workerDialogVisible.value = false
      fetchWorkerTypes()
    } else {
      ElMessage.error(response.message || '操作失败')
    }
  } catch (error) {
    ElMessage.error('请求失败: ' + (error.message || '未知错误'))
  }
}

// 删除工种
function deleteWorker(row) {
  ElMessageBox.confirm(`确定删除工种 "${row.name}" (${row.id}) 吗？`, '删除确认', {
    type: 'warning'
  }).then(async () => {
    try {
      const response = await request({
        url: `http://localhost:5000/api/worker-types/${row.id}`,
        method: 'delete'
      })
      if (response.success) {
        ElMessage.success('删除成功')
        fetchWorkerTypes()
      } else {
        ElMessage.error(response.message || '删除失败')
      }
    } catch (error) {
      ElMessage.error('删除失败: ' + (error.message || '未知错误'))
    }
  }).catch(() => {})
}

// 工种分页事件
function handleWorkerSizeChange(val) {
  workerPageSize.value = val
  workerCurrentPage.value = 1
}
function handleWorkerCurrentChange(val) {
  workerCurrentPage.value = val
}

// 自然排序函数 - 更健壮的实现
function naturalSort(processes) {
  // 先按原始自然排序处理
  const naturallySorted = [...processes].sort((a, b) => {
    const codeA = a.process_code || ''
    const codeB = b.process_code || ''
    
    // 提取数字部分的正则表达式
    const numRegex = /(\d+)/g
    
    // 提取所有数字
    const numsA = codeA.match(numRegex) || []
    const numsB = codeB.match(numRegex) || []
    
    // 如果都有数字，比较第一个数字
    if (numsA.length > 0 && numsB.length > 0) {
      const numA = parseInt(numsA[0])
      const numB = parseInt(numsB[0])
      
      if (numA !== numB) {
        return numA - numB
      }
    }
    
    // 如果数字相同或没有数字，按字符串比较
    return codeA.localeCompare(codeB, 'zh-CN', { numeric: true })
  });
  
  // 按照M开头的大工序和P开头的小工序进行分组排序
  const mainProcesses = [];  // M开头的大工序
  const subProcesses = [];   // P开头的小工序
  
  // 分离大工序和小工序
  naturallySorted.forEach(process => {
    if (process.process_code && process.process_code.startsWith('M')) {
      mainProcesses.push(process);
    } else if (process.process_code && process.process_code.startsWith('P')) {
      subProcesses.push(process);
    }
  });
  
  // 构建最终排序结果
  const result = [];
  
  // 先处理大工序，再处理其对应的小工序
  mainProcesses.forEach(mainProcess => {
    // 添加大工序
    result.push(mainProcess);
    
    // 查找并添加对应的小工序
    const mainNumber = mainProcess.process_code.substring(1); // 去掉M前缀
    const relatedSubProcesses = subProcesses.filter(subProcess => {
      // 检查小工序的parent_process_code是否匹配大工序
      return subProcess.parent_process_code === mainProcess.process_code ||
             // 或者通过编号匹配（如M01对应P01开头的工序）
             (subProcess.process_code && subProcess.process_code.startsWith(`P${mainNumber}`));
    });
    
    // 对相关的小工序也进行自然排序
    const sortedSubProcesses = relatedSubProcesses.sort((a, b) => {
      const codeA = a.process_code || '';
      const codeB = b.process_code || '';
      
      const numRegex = /(\d+)/g;
      const numsA = codeA.match(numRegex) || [];
      const numsB = codeB.match(numRegex) || [];
      
      if (numsA.length > 0 && numsB.length > 0) {
        const numA = parseInt(numsA[0]);
        const numB = parseInt(numsB[0]);
        
        if (numA !== numB) {
          return numA - numB;
        }
      }
      
      return codeA.localeCompare(codeB, 'zh-CN', { numeric: true });
    });
    
    // 将排序后的小工序添加到结果中
    result.push(...sortedSubProcesses);
  });
  
  // 添加未匹配到大工序的其他工序（如果有）
  const remainingProcesses = naturallySorted.filter(process => {
    // 不是M开头的大工序，也不是已处理的小工序
    const isMainProcess = process.process_code && process.process_code.startsWith('M');
    const isProcessedSubProcess = result.includes(process);
    return !isMainProcess && !isProcessedSubProcess;
  });
  
  result.push(...remainingProcesses);
  
  return result;
}

// 查看工序（第二层）
function viewProcesses(row) {
  currentRuleKey.value = row.key
  currentRuleName.value = row.name
  
  // 获取工序数据
  const processes = allRuleData.value[row.key]?.processes || []
  
  // 使用自然排序
  sortedProcesses.value = naturalSort(processes)
  
  // 重置工序筛选
  resetProcessFilter()
  
  // 动态生成工序表格列
  if (sortedProcesses.value.length > 0) {
    const firstProcess = sortedProcesses.value[0]
    const allKeys = Object.keys(firstProcess).filter(key => 
      key !== 'required_workers' && key !== 'material_requirements' && key !== 'tools_requirements' && key !== 'id') // 排除required_workers、material_requirements、tools_requirements和id，单独显示
    
    // 设置中文列名
    const columnLabels = {
      'process_code': '工序代码',
      'name': '工序名称',
      'description': '工序描述',
      'duration': '持续时间',
      'equipment_type': '设备类型',
      'estimated_hours': '预计工时',
      'predecessor_codes': '前置工序代码',
      'material_price': '物料费用',
      'tools_price': '工具费用',
      'is_major_process': '是否大工序',
      'parent_process_code': '父工序代码',
      'equipment_type_name':'设备种类名称'
    }
    
    // 按指定顺序排列列
    const orderedKeys = []
    
    // 首先添加工序代码（如果存在）
    if (allKeys.includes('process_code')) {
      orderedKeys.push('process_code')
    }
    
    
    // 添加前置工序代码（如果存在）
    if (allKeys.includes('predecessor_codes')) {
      orderedKeys.push('predecessor_codes')
    }
    
      // 添加其他列（除了工序代码和前置工序代码）
    allKeys.forEach(key => {
      if (key !== 'process_code' && key !== 'predecessor_codes') {
        orderedKeys.push(key)
      }
    })
    
   
    processColumns.value = orderedKeys.map(key => ({
      prop: key,
      label: columnLabels[key] || key,
      width: getColumnWidth(key)
    }))
  } else {
    processColumns.value = [
      { prop: 'process_code', label: '工序代码', width: 120 },
      { prop: 'name', label: '工序名称', width: 150 },
      { prop: 'description', label: '工序描述', width: 200 },
      { prop: 'predecessor_codes', label: '前置工序代码', width: 150 },
      { prop: 'estimated_hours', label: '预计工时', width: 120 },
      { prop: 'material_price', label: '物料费用', width: 120 },
      { prop: 'tools_price', label: '工具费用', width: 120 }
    ]
  }
  
  currentProcessPage.value = 1
  processDialogVisible.value = true
}

// 根据字段类型设置列宽
function getColumnWidth(key) {
  const widthMap = {
    'process_code': 100,
    'name': 150,
    'description': 200,
    'duration': 100,
    'equipment_type': 120
  }
  return widthMap[key] || 120
}

// 格式化物料需求显示，为数字+单位格式的物料添加括号
function formatMaterialRequirement(material) {
  // 检查是否为数字+单位的格式（如"100kg"、"50L"等）
  const regex = /^(\d+\.?\d*)\s*([a-zA-Z\u4e00-\u9fa5]+)$/;
  if (regex.test(material)) {
    return `(${material})`;
  }
  
  // 检查是否为名称+数字+单位的格式（如"氧气0.100m³"）
  const nameWithQuantityRegex = /^([a-zA-Z\u4e00-\u9fa5]+)(\d+\.?\d*\s*[a-zA-Z\u4e00-\u9fa5]+)$/;
  const match = material.match(nameWithQuantityRegex);
  if (match) {
    const name = match[1]; // 物料名称，如"氧气"
    const quantity = match[2]; // 数量和单位，如"0.100m³"
    return `${name}(${quantity})`;
  }
  
  return material;
}


// 为el-table提供row-class-name
function tableRowClassName({ row }) {
  if (row.process_code && row.process_code.startsWith('M')) {
    return 'm-process';
  }
  return '';
}

// 触发文件上传
function triggerFileUpload() {
  // 触发el-upload的文件选择弹窗
  uploadRef.value?.$el.querySelector('input')?.click()
}

async function downloadTemplate() {
  try {
    downloading.value = true
    
    // 检查是否有数据
    if (!allRuleData.value || Object.keys(allRuleData.value).length === 0) {
      ElMessage.warning('暂无规则数据可下载')
      return
    }
    
    // 创建工作簿
    const workbook = XLSX.utils.book_new()
    
    // 遍历所有设备类型数据
    Object.entries(allRuleData.value).forEach(([equipmentTypeId, equipmentData]) => {
      const equipmentName = equipmentData.name || `设备_${equipmentTypeId}`
      const processes = equipmentData.processes || []
      
      // 如果有工序数据，则创建对应的sheet
      if (processes.length > 0) {
        // 准备数据：将工序数据转换为适合Excel的格式
        const sheetData = processes.map(process => {
          // 处理工种需求
          let requiredWorkersStr = ''
          if (process.required_workers && Object.keys(process.required_workers).length > 0) {
            requiredWorkersStr = Object.entries(process.required_workers)
              .map(([workerType, count]) => `${workerType}:${count}`)
              .join('; ')
          }
          
          // 处理前置工序代码
          let predecessorCodesStr = ''
          if (process.predecessor_codes) {
            if (Array.isArray(process.predecessor_codes)) {
              predecessorCodesStr = process.predecessor_codes.join(', ')
            } else if (typeof process.predecessor_codes === 'string') {
              predecessorCodesStr = process.predecessor_codes
            }
          }
          
          return {
            '工序代码': process.process_code || '',
            '工序名称': process.name || '',
            '工序描述': process.description || '',
            '预计工时(小时)': process.estimated_hours || 0,
            '前置工序代码': predecessorCodesStr,
            '父工序代码': process.parent_process_code || '',
            '是否大工序': process.is_major_process ? '是' : '否',
            '需要工种': requiredWorkersStr,
            '物料需求': process.material_requirements || '',
            '物料费用': process.material_price || 0,
            '工具需求': process.tools_requirements || '',
            '工具费用': process.tools_price || 0
          }
        })
        
        // 创建工作表
        const worksheet = XLSX.utils.json_to_sheet(sheetData)
        
        // 设置列宽
        const colWidths = [
          { wch: 15 }, // 工序代码
          { wch: 20 }, // 工序名称
          { wch: 30 }, // 工序描述
          { wch: 15 }, // 预计工时
          { wch: 25 }, // 前置工序代码
          { wch: 15 }, // 父工序代码
          { wch: 12 }, // 是否大工序
          { wch: 25 }, // 需要工种
          { wch: 25 }, // 物料需求
          { wch: 12 }, // 物料费用
          { wch: 25 }, // 工具需求
          { wch: 12 }  // 工具费用
        ]
        worksheet['!cols'] = colWidths
        
        // 将工作表添加到工作簿，使用设备名称作为sheet名
        XLSX.utils.book_append_sheet(workbook, worksheet, equipmentName)
      }
    })
    
    // 如果没有任何有效数据
    if (workbook.SheetNames.length === 0) {
      ElMessage.warning('没有找到有效的工序数据')
      return
    }
    
    // 导出文件
    const fileName = `规则数据_${new Date().getFullYear()}年${(new Date().getMonth() + 1).toString().padStart(2, '0')}月${new Date().getDate().toString().padStart(2, '0')}日.xlsx`
    XLSX.writeFile(workbook, fileName)
    
    ElMessage.success(`规则数据已导出，共${workbook.SheetNames.length}个设备类型`)
    
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败: ' + (error.message || '未知错误'))
  } finally {
    downloading.value = false
  }
}

function handleFileChange(file) {
  selectedFile.value = file?.raw || null
  selectedFileName.value = file?.name || ''
  
  // 自动预览数据
  if (selectedFile.value) {
    previewData()
  }
}

function previewData() {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择要导入的文件')
    return
  }
  
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const data = new Uint8Array(e.target.result)
      const workbook = XLSX.read(data, { type: 'array' });
      const firstSheetName = workbook.SheetNames[0];
      const worksheet = workbook.Sheets[firstSheetName];
      const jsonData = XLSX.utils.sheet_to_json(worksheet);
      
      // 动态生成列定义
      if (jsonData.length > 0) {
        const firstRow = jsonData[0];
        excelColumns.value = Object.keys(firstRow).map(key => ({
          prop: key,
          label: key,
          width: 150
        }));
      } else {
        excelColumns.value = [
          { prop: 'id', label: 'ID', width: 100 },
          { prop: 'name', label: '名称', width: 150 },
          { prop: 'description', label: '描述', width: 200 }
        ];
      }
      
      excelData.value = jsonData;
      excelEditorVisible.value = true;
    } catch (error) {
      ElMessage.error('文件解析失败: ' + error.message);
    }
  };
  reader.readAsArrayBuffer(selectedFile.value);
}

async function confirmImport(data) {
  const rawData = data || excelData.value
  if (!rawData || rawData.length === 0) {
    ElMessage.warning('没有数据可导入')
    return
  }
  const templatesList = []
  const errors = []

  rawData.forEach((row, index) => {
    try {
      // 构建模板对象
      const template = {}
      
      // 遍历当前行的所有键，根据映射填充
      Object.keys(row).forEach(key => {
        const backendKey = columnMapping[key] || key // 如果映射不存在，保留原键名（但后端可能不认识）
        let value = row[key]
        
        // 根据后端字段类型进行转换
        if (backendKey === 'equipment_type_id' || backendKey === 'process_code') {
          // 必填字段，如果为空则报错
          if (!value && value !== 0) {
            throw new Error(`第 ${index + 2} 行: ${key} 不能为空`)
          }
          template[backendKey] = String(value).trim()
        }
        else if (backendKey === 'estimated_hours' || backendKey === 'material_price' || backendKey === 'tools_price') {
          // 数字字段
          template[backendKey] = parseFloat(value) || 0
        }
        else {
          // 其他字符串字段直接赋值
          template[backendKey] = value !== undefined && value !== null ? String(value) : ''
        }
      })
       if (!template.equipment_type_id) {
        throw new Error(`第 ${index + 2} 行: 设备类型ID不能为空`)
      }
      if (!template.process_code) {
        throw new Error(`第 ${index + 2} 行: 工序代码不能为空`)
      }
      templatesList.push(template)
    } catch (e) {
      errors.push(e.message)
    }
  })
  try {
    const response = await request({
      url: '/api/batch-import-process-templates',
      method: 'post',
      data: { templates_list: templatesList }
    })

    if (response.success) {
      ElMessage.success(response.message || '批量导入成功')
      // 关闭编辑器弹窗
      excelEditorVisible.value = false
      // 刷新规则数据
      await fetchRuleData()
      // 清空选择的文件
      selectedFile.value = null
      selectedFileName.value = ''
    } else {
      ElMessage.error(response.message || '导入失败')
      // 如果有错误明细，可以显示
      if (response.errors && response.errors.length > 0) {
        console.error('导入错误明细:', response.errors)
        ElMessageBox.alert(response.errors.join('\n'), '导入错误', { type: 'error' })
      }
    }
  } catch (error) {
    ElMessage.error('批量导入请求失败: ' + (error.message || '未知错误'))
  }
}


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

  uploading.value = true
  tipVisible.value = false
  progressVisible.value = true
  progressStatus.value = undefined
  progressPercent.value = 0
  return true
}

function handleProgress(event) {
  const p = Math.floor(event?.percent ?? 0)
  progressPercent.value = Math.min(100, Math.max(0, p))
}

function handleSuccess() {
  uploading.value = false
  tipType.value = 'success'
  tipMessage.value = '导入成功'
  tipVisible.value = true
  progressPercent.value = 100
  progressStatus.value = 'success'
  ElMessage.success('上传并导入成功')
  
  fetchRuleData()
}

function handleError() {
  uploading.value = false
  tipType.value = 'error'
  tipMessage.value = '导入失败，请检查文件或稍后重试'
  tipVisible.value = true
  progressStatus.value = 'exception'
  ElMessage.error('上传或导入失败')
}

// 第一层分页事件
function handleSizeChange(val) {
  pageSize.value = val
  currentPage.value = 1
}

function handleCurrentChange(val) {
  currentPage.value = val
}

// 第二层分页事件

// 重置筛选
function resetFilter() {
  filterForm.equipmentType = ''
}

// 重置工序筛选
function resetProcessFilter() {
  processFilterForm.description = ''
}

// 添加编辑对话框相关状态
const editDialogVisible = ref(false)
const currentEditProcess = ref({})
const editProcessForm = reactive({
  process_code: '',
  description: '',
  estimated_hours: 0,
  required_workers: {},
  predecessor_codes: [],
  parent_process_code: '',
  is_major_process: false,
  material_requirements: '',
  material_price: 0,
  tools_requirements: '',
  tools_price: 0
})

// 编辑工序
function editProcess(row) {
  // 初始化表单数据
  editProcessForm.process_code = row.process_code || ''
  editProcessForm.description = row.description || ''
  editProcessForm.estimated_hours = row.estimated_hours || 0
  editProcessForm.required_workers = row.required_workers ? JSON.parse(JSON.stringify(row.required_workers)) : {}
  editProcessForm.predecessor_codes = Array.isArray(row.predecessor_codes) 
    ? [...row.predecessor_codes] 
    : (typeof row.predecessor_codes === 'string' 
       ? row.predecessor_codes.split(',').map(code => code.trim()).filter(code => code)
       : [])
  editProcessForm.parent_process_code = row.parent_process_code || ''
  editProcessForm.is_major_process = row.is_major_process || false
  editProcessForm.material_requirements = row.material_requirements || ''
  editProcessForm.material_price = row.material_price || 0
  editProcessForm.tools_requirements = row.tools_requirements || ''
  editProcessForm.tools_price = row.tools_price || 0
  
  currentEditProcess.value = { ...row }
  editDialogVisible.value = true
}

// 更新工序API调用
async function updateProcess() {
  try {
    const templateId = `${currentEditProcess.value.id}`
    
    // 格式化前置工序代码为数组
    let predecessorCodes = editProcessForm.predecessor_codes
    if (typeof predecessorCodes === 'string') {
      predecessorCodes = predecessorCodes.split(',').map(code => code.trim()).filter(code => code)
    }
    
    const response = await request({
      url: `http://localhost:5000/api/process-templates/${templateId}`,
      method: 'put',
      data: {
        description: editProcessForm.description,
        estimated_hours: parseFloat(editProcessForm.estimated_hours),
        required_workers: editProcessForm.required_workers,
        predecessor_codes: predecessorCodes,
        parent_process_code: editProcessForm.parent_process_code,
        is_major_process: editProcessForm.is_major_process,
        material_requirements: editProcessForm.material_requirements,
        material_price: parseFloat(editProcessForm.material_price),
        tools_requirements: editProcessForm.tools_requirements,
        tools_price: parseFloat(editProcessForm.tools_price)
      }
    })
    
    if (response.success) {
      ElMessage.success('工序更新成功')
      editDialogVisible.value = false
      // 重新获取数据
      await fetchRuleData()
      // 更新当前显示的工序列表
      refreshCurrentProcesses()
    } else {
      ElMessage.error(response.message || '更新失败')
    }
  } catch (error) {
    ElMessage.error('更新失败: ' + (error.message || '未知错误'))
  }
}

// 删除工序
function deleteProcess(row) {
  ElMessageBox.confirm(
    `确定要删除工序 "${row.process_code}" 吗?`,
    '删除确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      const templateId = `${currentRuleKey.value}-${row.process_code}`
      
      const response = await request({
        url: `http://localhost:5000/api/process-templates/${templateId}`,
        method: 'delete'
      })
      
      if (response.success) {
        ElMessage.success('工序删除成功')
        // 重新获取数据
        await fetchRuleData()
        // 更新当前显示的工序列表
        refreshCurrentProcesses()
      } else {
        ElMessage.error(response.message || '删除失败')
      }
    } catch (error) {
      ElMessage.error('删除失败: ' + (error.message || '未知错误'))
    }
  }).catch(() => {
    ElMessage.info('已取消删除')
  })
}

// 刷新当前工序列表
function refreshCurrentProcesses() {
  // 获取更新后的工序数据
  const processes = allRuleData.value[currentRuleKey.value]?.processes || []
  
  // 使用自然排序
  sortedProcesses.value = naturalSort(processes)
  
  // 重置工序筛选
  resetProcessFilter()
  
  // 重置分页到第一页
  currentProcessPage.value = 1
}

// 添加工种
function addWorkerType() {
  ElMessageBox.prompt('请输入工种名称:', '添加工种', {
    confirmButtonText: '确定',
    cancelButtonText: '取消'
  }).then(({ value }) => {
    if (value) {
      editProcessForm.required_workers[value] = 1
      ElMessage.success('工种添加成功')
    }
  }).catch(() => {
    // 取消操作
  })
}

// 删除工种
function removeWorkerType(workerType) {
  delete editProcessForm.required_workers[workerType]
  ElMessage.success('工种删除成功')
}

// 添加新增工序相关状态
const addProcessDialogVisible = ref(false)
const addProcessForm = reactive({
  process_code: '',
  description: '',
  estimated_hours: 0,
  required_workers: {},
  predecessor_codes: [],
  parent_process_code: '',
  is_major_process: false,
  material_requirements: '',
  material_price: 0,
  tools_requirements: '',
  tools_price: 0
})

// 显示新增工序表单
function showAddProcessForm() {
  // 初始化表单
  addProcessForm.process_code = ''
  addProcessForm.description = ''
  addProcessForm.estimated_hours = 0
  addProcessForm.required_workers = {}
  addProcessForm.predecessor_codes = []
  addProcessForm.parent_process_code = ''
  addProcessForm.is_major_process = false
  addProcessForm.material_requirements = ''
  addProcessForm.material_price = 0
  addProcessForm.tools_requirements = ''
  addProcessForm.tools_price = 0
  
  addProcessDialogVisible.value = true
}

// 添加工种到新增表单
function addWorkerTypeToNew() {
  ElMessageBox.prompt('请输入工种名称:', '添加工种', {
    confirmButtonText: '确定',
    cancelButtonText: '取消'
  }).then(({ value }) => {
    if (value) {
      addProcessForm.required_workers[value] = 1
      ElMessage.success('工种添加成功')
    }
  }).catch(() => {
    // 取消操作
  })
}

// 从新增表单中删除工种
function removeWorkerTypeFromNew(workerType) {
  delete addProcessForm.required_workers[workerType]
  ElMessage.success('工种删除成功')
}

// 提交新增工序
async function submitAddProcess() {
  try {
    // 验证必填字段
    if (!addProcessForm.process_code) {
      ElMessage.error('工序代码不能为空')
      return
    }
    
    if (!currentRuleKey.value) {
      ElMessage.error('设备类型ID缺失')
      return
    }
    
    // 格式化前置工序代码为数组
    let predecessorCodes = addProcessForm.predecessor_codes
    if (typeof predecessorCodes === 'string') {
      predecessorCodes = predecessorCodes.split(',').map(code => code.trim()).filter(code => code)
    }
    
    const response = await request({
      url: 'http://localhost:5000/api/process-templates',
      method: 'post',
      data: {
        equipment_type_id: currentRuleKey.value,
        process_code: addProcessForm.process_code,
        description: addProcessForm.description,
        estimated_hours: parseFloat(addProcessForm.estimated_hours),
        required_workers: addProcessForm.required_workers,
        predecessor_codes: predecessorCodes,
        parent_process_code: addProcessForm.parent_process_code,
        is_major_process: addProcessForm.is_major_process,
        material_requirements: addProcessForm.material_requirements,
        material_price: parseFloat(addProcessForm.material_price),
        tools_requirements: addProcessForm.tools_requirements,
        tools_price: parseFloat(addProcessForm.tools_price)
      }
    })
    
    if (response.success) {
      ElMessage.success('工序添加成功')
      addProcessDialogVisible.value = false
      // 重新获取数据
      await fetchRuleData()
      // 更新当前显示的工序列表
      refreshCurrentProcesses()
    } else {
      ElMessage.error(response.message || '添加失败')
    }
  } catch (error) {
    ElMessage.error('添加失败: ' + (error.message || '未知错误'))
  }
}

</script>

<style scoped>
.import-card {
  min-height: calc(100vh - 100px);
  border: none;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.06);
  border-radius: 14px;
  padding-bottom: 16px;
}

.title {
  margin: 8px 0 16px 0;
  font-weight: 600;
}

/* 设备查询组件样式 */
.equipment-search-container {
  margin: 20px 0;
  padding: 20px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  background: #fafafa;
}
.search-title {
  margin: 0 0 16px 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}
.search-form {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: center;
}
.search-input, .search-select, .search-date {
  width: 220px;
}
.search-btn-group {
  margin-left: auto;
  display: flex;
  gap: 8px;
}

/* 底部功能图标区样式 */
.bottom-function-icons {
  position: relative;
  gap:16px;
  display: flex;
  margin-top:20px;
  margin-left:10px;
}
.icon-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  transition: all 0.3s ease;
  padding: 8px;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  width: 40px;
  height: 40px;
  justify-content: center;
  position: relative;
}
.icon-item:hover {
  background: #e6f7ff; /* 浅蓝色背景 */
  color: #409eff;
  transform: scale(1.1);
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
}
.icon-item:hover .function-icon {
  color: #1890ff; /* 悬停时图标变为深蓝色 */
}
.icon-label {
  display: none;
}

/* 规则数据表格部分样式 */
.rule-table-section {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

/* 工种计费规则区块 */
.worker-price-section {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h3 {
  margin: 0;
  font-weight: 600;
  color: #303133;
}

/* 分页样式 */
.pagination {
  margin-top: 16px;
  text-align: right;
}

/* 增加表格行高 */
:deep(.el-table__row) {
  height: 50px;
}

/* 为M开头的工序行设置深色背景 */
/* 为M开头的工序行设置深色背景 */
:deep(.el-table__body tr.m-process > td) {
  background-color: #f0f8ff !important;
  font-weight: bold;
}

:deep(.el-table__body tr.m-process:hover > td) {
  background-color: #d1f0ff !important;
}

/* 工序筛选部分样式 */
.process-filter-section {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
}

.process-filter-section .el-input {
  width: 300px;
}

/* 工种信息样式 */
.worker-item {
  margin-bottom: 4px;
  padding: 2px 4px;
  border-radius: 3px;
  background-color: #f5f7fa;
}

.worker-item:last-child {
  margin-bottom: 0;
}

.worker-type {
  font-weight: 500;
  color: #303133;
}

.worker-count {
  color: #606266;
  margin-left: 4px;
}

.no-workers {
  color: #909399;
  font-style: italic;
}

/* 物料需求样式 */
.material-item {
  margin-bottom: 4px;
  padding: 2px 4px;
  border-radius: 3px;
  background-color: #f5f7fa;
}

.material-item:last-child {
  margin-bottom: 0;
}

.no-materials {
  color: #909399;
  font-style: italic;
}

/* 工具需求样式 */
.tool-item {
  margin-bottom: 4px;
  padding: 2px 4px;
  border-radius: 3px;
  background-color: #f5f7fa;
}

.tool-item:last-child {
  margin-bottom: 0;
}

.no-tools {
  color: #909399;
  font-style: italic;
}

/* 工种编辑样式 */
.worker-types-container {
  width: 100%;
}

.worker-type-item {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
  padding: 5px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.worker-type-name {
  font-weight: 500;
  flex: 1;
}

@media (max-width: 920px) {
  .import-card { width: 100%; }
  .two-col { grid-template-columns: 1fr; }
  .divider { display: none; }
  /* 响应式：查询组件换行 */
  .search-form { flex-direction: column; align-items: stretch; }
  .search-input, .search-select, .search-date { width: 100%; }
  .search-btn-group { margin-left: 0; justify-content: flex-end; }
  /* 响应式：底部图标区 */
  .bottom-function-icons { gap: 20px; }
  .function-icon { 
    font-size: 24px;
    width: 24px;
    height: 24px;
  }
}
</style>