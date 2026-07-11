<template>
  <el-card class="import-card" shadow="hover">
    <h2 class="title">维修机具台账</h2>

    <!-- 机具查询组件 -->
    <div class="tool-search-container">
      <h3 class="search-title">机具查询</h3>
      <el-form :model="searchForm" class="search-form" label-width="100px" size="medium">
        <el-form-item label="机具编号">
          <el-input 
            v-model="searchForm.id" 
            placeholder="请输入机具编号" 
            clearable
            class="search-input"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="机具名称">
          <el-input 
            v-model="searchForm.name" 
            placeholder="请输入机具名称" 
            clearable
            class="search-input"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="机具类型">
          <el-select
            v-model="searchForm.tool_type"
            placeholder="请选择机具类型"
            clearable
            class="search-select"
            @change="handleSearch"
          >
            <el-option
              v-for="type in toolTypes"
              :key="type"
              :label="type"
              :value="type"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="是否可用">
          <el-select 
            v-model="searchForm.is_available" 
            placeholder="请选择" 
            clearable
            class="search-select"
            @change="handleSearch"
          >
            <el-option label="是" value="是"></el-option>
            <el-option label="否" value="否"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item class="search-btn-group">
          <el-button type="primary" size="medium" @click="handleSearch">查询</el-button>
          <el-button size="medium" @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

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
      title="机具数据编辑"
      :data="excelData"
      :columns="excelColumns"
      @confirm="confirmImport"
    />
    
    <!-- 机具数据表格 -->
    <div class="tool-table-section">
      <el-table 
        :data="searchForm.id || searchForm.name || searchForm.tool_type || searchForm.is_available ? currentFilteredTools : currentPageTools" 
        v-loading="loadingTools"
        style="width: 100%"
        stripe
        height="670"
      >
        <!-- 动态生成列 -->
        <el-table-column
          v-for="column in toolColumns"
          :key="column.prop"
          :prop="column.prop"
          :label="column.label"
          :min-width="column.width || 120"
        >
          <template #default="scope">
            <!-- 特殊处理是否可用字段 -->
            <div v-if="column.prop === 'is_available'">
              <span 
                v-if="scope.row[column.prop] === 1 || scope.row[column.prop] === true" 
                class="available-yes"
              >
                <el-icon><SuccessFilled /></el-icon> 是
              </span>
              <span 
                v-else-if="scope.row[column.prop] === 0 || scope.row[column.prop] === false" 
                class="available-no"
              >
                <el-icon><CircleCloseFilled /></el-icon> 否
              </span>
              <span v-else>{{ scope.row[column.prop] }}</span>
            </div>
            <!-- 特殊处理重量字段 -->
            <div v-else-if="column.prop === 'capacity'">
              <span>{{ scope.row[column.prop] }} </span>
            </div>
            <!-- 特殊处理是否需要操作员字段 -->
            <div v-else-if="column.prop === 'requires_operator'">
              <span 
                v-if="scope.row[column.prop] === 1 || scope.row[column.prop] === true" 
                class="available-yes"
              >
                <el-icon><SuccessFilled /></el-icon> 是
              </span>
              <span 
                v-else-if="scope.row[column.prop] === 0 || scope.row[column.prop] === false" 
                class="available-no"
              >
                <el-icon><CircleCloseFilled /></el-icon> 否
              </span>
              <span v-else>{{ scope.row[column.prop] }}</span>
            </div>
            <!-- 其他字段使用默认显示 -->
            <span v-else>{{ scope.row[column.prop] }}</span>
          </template>
        </el-table-column>
        
        <!-- 操作列 -->
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button size="small" @click="editTool(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteTool(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页控件 -->
      <div class="pagination-container">
        <el-pagination
          :current-page="currentPage"
          :page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :small="false"
          :background="true"
          layout="total, sizes, prev, pager, next, jumper"
          :total="searchForm.id || searchForm.name || searchForm.tool_type ? filteredTools.length : tools.length"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>

    <!-- 底部功能图标区 -->
    <div class="bottom-function-icons">
      <!-- 图标1：添加单个数据 -->
      <div class="icon-item" @click="showAddToolDialog" title="添加单个机具数据">
        <img src="@/assets/iconfont/添加.png" class="function-icon" alt="添加单个机具数据" />
        <div class="icon-label">添加单个数据</div>
      </div>
      <!-- 图标2：下载模板 -->
      <div class="icon-item" @click="downloadTemplate" title="下载Excel模板">
        <img src="@/assets/iconfont/下载.png" class="function-icon" alt="下载Excel模板" />
        <div class="icon-label">下载模板</div>
      </div>
      <!-- 图标3：导入文件 -->
      <div class="icon-item" @click="triggerFileUpload" title="上传Excel文件">
        <img src="@/assets/iconfont/上传.png" class="function-icon" alt="上传Excel文件" />
        <div class="icon-label">导入文件</div>
      </div>
    </div>
    
    <!-- 编辑机具对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑机具" width="500">
      <el-form :model="currentTool" label-width="120px">
        <el-form-item 
          v-for="column in editableColumns" 
          :key="column.prop"
          :label="column.label"
        >
          <el-input 
            v-if="column.type === 'input'"
            v-model="currentTool[column.prop]" 
            :placeholder="`请输入${column.label}`"
          />
          <el-input-number
            v-else-if="column.type === 'number'"
            v-model="currentTool[column.prop]"
            :placeholder="`请输入${column.label}`"
            :min="0"
            controls-position="right"
            style="width: 100%"
          />
         
          <el-switch
            v-else-if="column.type === 'switch'"
            v-model="currentTool[column.prop]"
            active-text="是"
            inactive-text="否"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveTool">保存</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 添加机具对话框 -->
    <el-dialog v-model="addDialogVisible" title="添加机具" width="500">
      <el-form :model="newTool" label-width="120px">
        <el-form-item label="机具名称" prop="name" required>
          <el-input 
            v-model="newTool.name" 
            placeholder="请输入机具名称"
          />
        </el-form-item>
        <el-form-item label="机具类型" prop="tool_type" required>
          <el-input 
            v-model="newTool.tool_type" 
            placeholder="请输入机具类型"
          />
        </el-form-item>
        <el-form-item label="重量" prop="capacity">
          <el-input-number
            v-model="newTool.capacity"
            placeholder="请输入重量"
            :min="0"
            controls-position="right"
            style="width: 100%"
          />
          <span class="unit-label">kg</span>
        </el-form-item>
        <el-form-item label="日租金" prop="daily_rental_cost">
          <el-input-number
            v-model="newTool.daily_rental_cost"
            placeholder="请输入日租金"
            :min="0"
            controls-position="right"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="是否可用" prop="is_available">
          <el-switch
            v-model="newTool.is_available"
            active-text="是"
            inactive-text="否"
          />
        </el-form-item>
        <el-form-item label="是否需要操作员" prop="requires_operator">
          <el-switch
            v-model="newTool.requires_operator"
            active-text="是"
            inactive-text="否"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="addDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="addTool">确定</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 文件上传组件 -->
    <el-upload
      ref="uploadRef"
      class="upload-custom"
      :action="uploadUrl"
      :data="{ type: 'tool' }"
      :auto-upload="false"
      :show-file-list="false"
      :before-upload="handleBeforeUpload"
      :on-change="handleFileChange"
      :on-success="handleSuccess"
      :on-error="handleError"
      :on-progress="handleProgress"
      accept=".xlsx,.xls,.csv"
    >
    </el-upload>
  </el-card>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { SuccessFilled, CircleCloseFilled } from '@element-plus/icons-vue'
import * as XLSX from 'xlsx'
import ExcelEditor from './ExcelEditor.vue'
import request from '@/utils/request'

const uploading = ref(false)
const uploadRef = ref()
const selectedFile = ref(null)
const selectedFileName = ref('')

// Excel编辑器相关
const excelEditorVisible = ref(false)
const excelData = ref([])
const excelColumns = ref([])

// 机具数据相关
const tools = ref([])
const toolColumns = ref([])
const loadingTools = ref(false)

// 机具类型列表
const toolTypes = ref([])

// 搜索相关
const searchForm = reactive({
  id: '',
  name: '',
  tool_type: '',
  is_available: ''
})

// 编辑机具相关
const editDialogVisible = ref(false)
const currentTool = reactive({})

// 添加机具相关
const addDialogVisible = ref(false)
const newTool = reactive({
  name: '',
  tool_type: '',
  capacity: 0,
  daily_rental_cost: 0,
  is_available: true,
  requires_operator: false
})

// 分页相关
const currentPage = ref(1)
const pageSize = ref(10)

// 计算当前页显示的数据
const currentPageTools = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return tools.value.slice(start, end)
})

// 计算过滤后的数据
const filteredTools = computed(() => {
  return tools.value.filter(tool => {
    // 检查机具编号是否匹配
    const idMatch = searchForm.id ? 
      String(tool.id).includes(searchForm.id) : true
    
    // 检查机具名称是否匹配
    const nameMatch = searchForm.name ? 
      tool.name && tool.name.includes(searchForm.name) : true
    
    // 检查机具类型是否匹配
    const toolTypeMatch = searchForm.tool_type ? 
      tool.tool_type && tool.tool_type.includes(searchForm.tool_type) : true
    
    // 检查是否可用字段是否匹配
    let availableMatch = true;
    if (searchForm.is_available !== '') {
      if (searchForm.is_available === '是') {
        availableMatch = tool.is_available === '是';
      } else if (searchForm.is_available === '否') {
        availableMatch = tool.is_available === '否';
      }
    }
    
    return idMatch && nameMatch && toolTypeMatch && availableMatch
  })
})

// 计算当前页显示的过滤数据
const currentFilteredTools = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredTools.value.slice(start, end)
})

// 可编辑字段定义
const editableColumns = computed(() => {
  return [
    { prop: 'name', label: '机具名称', type: 'input' },
    { prop: 'tool_type', label: '机具类型', type: 'input' },
    { prop: 'capacity', label: '重量', type: 'number' },
    { prop: 'daily_rental_cost', label: '日租金', type: 'number' },
    { prop: 'is_available', label: '是否可用', type: 'switch' },
    { prop: 'requires_operator', label: '是否需要操作员', type: 'switch' }
  ]
})

// 保留的后端接口地址
const uploadUrl = '/api/import'

const tipVisible = ref(false)
const tipMessage = ref('')
const tipType = ref('success') // success | error | warning | info

// 进度状态
const progressPercent = ref(0)
const progressVisible = ref(false)
const progressStatus = ref(undefined) // success | exception | warning | undefined
const progressText = computed(() => {
  if (progressStatus.value === 'success') return '导入完成'
  if (progressStatus.value === 'exception') return '导入失败'
  if (uploading.value) return `正在导入… ${progressPercent.value}%`
  return ''
})

const downloading = ref(false)

// 页面加载时获取机具数据
onMounted(() => {
  fetchTools()
})

// 处理机具数据，将is_available字段值映射为是/否
function processToolData(toolsData) {
  return toolsData.map(tool => {
    return {
      ...tool,
      is_available: tool.is_available === 1 || tool.is_available === true ? '是' : '否',
      requires_operator: tool.requires_operator === 1 || tool.requires_operator === true ? '是' : '否'
    }
  })
}

// 获取机具数据
async function fetchTools() {
  try {
    loadingTools.value = true
    const response = await request({
      url: '/api/maintenance-tools',
      method: 'get'
    })
    
     const toolsData = response.data?.maintenance_tools || []
      if (toolsData.length > 0 || response.data?.total_count >= 0) {
        // 处理数据，将布尔值字段转换为是/否显示
        const processedTools = processToolData(toolsData)
        tools.value = processedTools
      
      // 动态生成列定义
      if (processedTools.length > 0) {
        const firstRow = processedTools[0]
        // 定义字段映射，将英文字段名映射为中文标题
        const labelMap = {
          id: '机具编号',
          name: '机具名称',
          tool_type: '机具类型',
          capacity: '重量',
          daily_rental_cost: '日租金',
          is_available: '是否可用',
          requires_operator: '是否需要操作员',
          created_at: '创建时间',
          updated_at: '更新时间'
        }
        
        // 按照指定顺序生成列定义
        const columnOrder = ['id', 'tool_type', 'name', 'is_available', 'requires_operator', 'capacity', 'daily_rental_cost', 'created_at', 'updated_at']
        toolColumns.value = columnOrder
          .filter(key => firstRow.hasOwnProperty(key))
          .map(key => ({
            prop: key,
            label: labelMap[key] || key,
            width: labelMap[key] ? 120 : 150
          }))
        
        // 提取机具类型列表
        toolTypes.value = [...new Set(processedTools.map(tool => tool.tool_type))];
      } else {
        // 如果没有数据，设置默认列（按指定顺序）
        toolColumns.value = [
          { prop: 'id', label: '机具编号', width: 100 },
          { prop: 'tool_type', label: '机具类型', width: 150 },
          { prop: 'name', label: '机具名称', width: 120 },
          { prop: 'is_available', label: '是否可用', width: 120 },
          { prop: 'requires_operator', label: '是否需要操作员', width: 150 }
        ]
      }
    } else {
      ElMessage.error('获取机具数据失败: ' + (response.message || '未知错误'))
      // 加载默认数据
      loadDefaultTools()
    }
  } catch (error) {
    ElMessage.error('获取机具数据失败: ' + (error.message || '未知错误'))
    console.error('获取机具数据失败:', error)
    
    // 加载默认数据
    loadDefaultTools()
  } finally {
    loadingTools.value = false
  }
}

// 加载默认机具数据
function loadDefaultTools() {
  const defaultTools = [
    {
      id: 1,
      name: '电焊机',
      tool_type: '焊接设备',
      capacity: 100,
      daily_rental_cost: 50.0,
      is_available: '是',
      requires_operator: '是'
    },
    {
      id: 2,
      name: '万用表',
      tool_type: '检测设备',
      capacity: 10,
      daily_rental_cost: 20.0,
      is_available: '否',
      requires_operator: '否'
    }
  ]
  
  tools.value = defaultTools
  
  // 设置默认列（按指定顺序）
  toolColumns.value = [
    { prop: 'id', label: '机具编号', width: 100 },
    { prop: 'tool_type', label: '机具类型', width: 150 },
    { prop: 'name', label: '机具名称', width: 120 },
    { prop: 'is_available', label: '是否可用', width: 120 },
    { prop: 'requires_operator', label: '是否需要操作员', width: 150 },
    { prop: 'capacity', label: '重量', width: 100 },
    { prop: 'daily_rental_cost', label: '日租金', width: 100 }
  ]
  
  // 提取机具类型列表
  toolTypes.value = [...new Set(defaultTools.map(tool => tool.tool_type))];
}

// 编辑机具
function editTool(row) {
  // 复制当前行数据到 currentTool
  Object.keys(row).forEach(key => {
    currentTool[key] = row[key]
  })
  // 转换布尔值字段
  currentTool.is_available = row.is_available === '是' || row.is_available === 1 || row.is_available === true
  currentTool.requires_operator = row.requires_operator === '是' || row.requires_operator === 1 || row.requires_operator === true
  editDialogVisible.value = true
}

// 保存机具修改
async function saveTool() {
  try {
    const toolData = {
      name: currentTool.name,
      tool_type: currentTool.tool_type,
      capacity: parseFloat(currentTool.capacity),
      daily_rental_cost: parseFloat(currentTool.daily_rental_cost),
      is_available: Boolean(currentTool.is_available),
      requires_operator: Boolean(currentTool.requires_operator)
    }
    
      await request({
        url: `/api/maintenance-tools/${currentTool.id}`,
        method: 'put',
        data: toolData
      })
      // Result 格式请求成功即 code===20000，拦截器已保证，无需额外判断
      ElMessage.success('机具信息已更新')
      editDialogVisible.value = false
      await fetchTools()
  } catch (error) {
    ElMessage.error('更新机具信息失败: ' + (error.message || '未知错误'))
  }
}

// 删除机具
function deleteTool(row) {
  ElMessageBox.confirm(
    `确定要删除机具 "${row.name}" 吗？此操作不可恢复。`,
    '确认删除',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',

    }
  ).then(async () => {
    try {
       await request({
          url: `/api/maintenance-tools/${row.id}`,
          method: 'delete'
        })
        // Result 格式：拦截器已保证 code===20000，直接视为成功
        ElMessage.success('机具已删除')
        await fetchTools()
    } catch (error) {
      ElMessage.error('删除机具失败: ' + (error.message || '未知错误'))
    }
  }).catch(() => {
    // 用户取消删除
  })
}

// 分页相关函数
function handleSizeChange(newSize) {
  pageSize.value = newSize
  currentPage.value = 1 // 重置到第一页
}

function handleCurrentChange(newPage) {
  currentPage.value = newPage
}

// 搜索功能
function handleSearch() {
  currentPage.value = 1 // 重置到第一页
}

// 重置搜索
function resetSearch() {
  searchForm.id = ''
  searchForm.name = ''
  searchForm.tool_type = ''
  searchForm.is_available = ''
  currentPage.value = 1
}

async function downloadTemplate() {
  try {
    downloading.value = true
    // 直接从public目录下载Excel模板文件
    const link = document.createElement('a')
    link.href = '/维修器具表模版.xlsx'
    link.download = '维修器具表模版.xlsx'
    link.click()
    ElMessage.success('模板开始下载')
  } catch {
    ElMessage.error('模板下载失败')
  } finally {
    downloading.value = false
  }
}

function handleFileChange(file) {
  selectedFile.value = file?.raw || null
  selectedFileName.value = file?.name || ''
  // 选择文件后直接预览数据
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
      const workbook = XLSX.read(data, { type: 'array' })
      const firstSheetName = workbook.SheetNames[0]
      const worksheet = workbook.Sheets[firstSheetName]
      // 将Excel转换为JSON，使用列标题作为对象字段
      const jsonData = XLSX.utils.sheet_to_json(worksheet)
      
      // 动态生成列定义
      if (jsonData.length > 0) {
        const firstRow = jsonData[0]
        // 定义字段映射，将英文字段名映射为中文标题
        const labelMap = {
          id: '机具编号',
          name: '机具名称',
          tool_type: '机具类型',
          capacity: '重量',
          daily_rental_cost: '日租金',
          is_available: '是否可用',
          requires_operator: '是否需要操作员',
          created_at: '创建时间',
          updated_at: '更新时间'
        }
        excelColumns.value = Object.keys(firstRow).map(key => ({
          prop: key,
          label: labelMap[key] || key,
          width: 150
        }))
      } else {
        // 如果没有数据，默认添加几列
        excelColumns.value = [
          { prop: 'name', label: '机具名称', width: 120 },
          { prop: 'tool_type', label: '机具类型', width: 150 },
          { prop: 'capacity', label: '重量', width: 100 },
          { prop: 'daily_rental_cost', label: '日租金', width: 100 },
          { prop: 'is_available', label: '是否可用', width: 120 },
          { prop: 'requires_operator', label: '是否需要操作员', width: 150 }
        ]
      }
      
      // 设置表格数据
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
    
    // 构造请求数据，以tools_list为键，值为Excel转换的JSON数组
    const requestData = {
      tools_list: data
    }
    
    // 发送POST请求到批量导入接口
   await request({
        url: '/api/batch-import-maintenance-tools',
        method: 'post',
        data: requestData
      })
    
    if (response.success) {
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
      
      // 重新获取机具数据
      await fetchTools()
    } else {
      throw new Error(response.message || '导入失败')
    }
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

function submitUpload() {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择要导入的文件')
    return
  }
  uploadRef.value?.submit()
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
  
  // 重新获取机具数据
  fetchTools()
}

function handleError() {
  uploading.value = false
  tipType.value = 'error'
  tipMessage.value = '导入失败，请检查文件或稍后重试'
  tipVisible.value = true
  progressStatus.value = 'exception'
  ElMessage.error('上传或导入失败')
}

// 显示添加机具对话框
function showAddToolDialog() {
  // 清空表单数据
  newTool.name = ''
  newTool.tool_type = ''
  newTool.capacity = 0
  newTool.daily_rental_cost = 0
  newTool.is_available = true
  newTool.requires_operator = false
  addDialogVisible.value = true
}

// 添加机具
async function addTool() {
  if (!newTool.name || !newTool.tool_type) {
    ElMessage.warning('请填写完整的机具信息')
    return
  }
  
  try {
    const toolData = {
      name: newTool.name,
      tool_type: newTool.tool_type,
      capacity: parseFloat(newTool.capacity),
      daily_rental_cost: parseFloat(newTool.daily_rental_cost),
      is_available: Boolean(newTool.is_available),
      requires_operator: Boolean(newTool.requires_operator)
    }
    
     await request({
        url: '/api/maintenance-tools',
        method: 'post',
        data: toolData
      })
    
    if (response.success) {
      ElMessage.success('机具添加成功')
      addDialogVisible.value = false
      // 重新获取机具数据以刷新表格
      await fetchTools()
    } else {
      ElMessage.error('添加机具失败: ' + (response.message || '未知错误'))
    }
  } catch (error) {
    ElMessage.error('添加机具失败: ' + (error.message || '未知错误'))
  }
}

// 触发文件上传
function triggerFileUpload() {
  // 触发el-upload的文件选择弹窗
  uploadRef.value?.$el.querySelector('input')?.click()
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

/* 机具查询组件样式 */
.tool-search-container {
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
  background-color: transparent;
  padding: 0;
}

.search-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.search-form :deep(.el-form-item__label) {
  font-weight: 500;
  color: #475569;
}

.search-input, .search-select {
  width: 220px;
}

.search-input :deep(.el-input__wrapper),
.search-select :deep(.el-input__wrapper) {
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

/* 机具数据表格部分样式 */
.tool-table-section {
  margin-top: 0;
  padding-top: 0;
  border-top: none;
}

.tool-table-section :deep(.el-table) {
  border-radius: 8px;
  border: 1px solid #f0f2f5;
  overflow: hidden;
}

.tool-table-section :deep(.el-table__inner-wrapper::before) {
  display: none;
}

.tool-table-section :deep(th.el-table__cell) {
  background-color: #f8fafc !important;
  color: #475569;
  font-weight: 600;
  height: 54px;
  border-bottom: 1px solid #e2e8f0 !important;
  border-right: none !important;
}

.tool-table-section :deep(td.el-table__cell) {
  padding: 16px 0;
  border-bottom: 1px solid #f1f5f9 !important;
  border-right: none !important;
  color: #334155;
}

.tool-table-section :deep(.el-table__row:hover > td) {
  background-color: #f8fafc !important;
}

/* 表格内按钮优化 */
.tool-table-section :deep(.el-button) {
  padding: 6px 12px;
  border-radius: 6px;
  font-weight: 500;
  border: none;
  background-color: transparent;
}

.tool-table-section :deep(.el-button:not(.el-button--danger)) {
  color: #3b82f6;
}
.tool-table-section :deep(.el-button:not(.el-button--danger):hover) {
  background-color: #eff6ff;
}

.tool-table-section :deep(.el-button--danger) {
  color: #ef4444;
}
.tool-table-section :deep(.el-button--danger:hover) {
  background-color: #fef2f2;
}

/* 分页样式 */
.pagination-container {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
}

.available-yes {
  color: #059669;
  background-color: #d1fae5;
  padding: 4px 12px;
  border-radius: 6px;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border: none;
}

.available-no {
  color: #dc2626;
  background-color: #fee2e2;
  padding: 4px 12px;
  border-radius: 6px;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border: none;
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
  /* 使用滤镜将图片变为深蓝色 */
  filter: brightness(0) saturate(100%) invert(25%) sepia(92%) saturate(2623%) hue-rotate(195deg) brightness(95%) contrast(90%);
}

.icon-label {
  display: none;
}

@media (max-width: 920px) {
  .import-card { width: 100%; }
  .two-col { grid-template-columns: 1fr; }
  .divider { display: none; }
  
  /* 响应式：查询组件换行 */
  .search-form { 
    flex-direction: column; 
    align-items: stretch; 
  }
  
  .search-input, 
  .search-select { 
    width: 100%; 
  }
  
  .search-btn-group { 
    margin-left: 0; 
    justify-content: flex-end; 
  }
  
  /* 响应式：底部图标区 */
  .bottom-function-icons { 
    gap: 20px; 
  }
  
  .function-icon { 
    font-size: 24px;
    width: 24px;
    height: 24px;
  }
  
}
</style>