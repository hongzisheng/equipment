<template>
  <el-card class="import-card" shadow="hover">
   <h2 class="title">工人台账</h2>

    <!-- 工人查询组件 -->
    <div class="worker-search-container">
      <h3 class="search-title">工人查询</h3>
      <el-form :model="searchForm" class="search-form" label-width="100px" size="default">
        <el-form-item label="工号">
          <el-input 
            v-model="searchForm.id" 
            placeholder="请输入工号" 
            clearable
            class="search-input"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input 
            v-model="searchForm.name" 
            placeholder="请输入姓名" 
            clearable
            class="search-input"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="工种">
          <el-select
            v-model="searchForm.worker_type"
            placeholder="请选择工种"
            clearable
            class="search-select"
            @change="handleSearch"
          >
            <el-option
              v-for="type in workerTypes"
              :key="type"
              :label="type"
              :value="type"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="是否持证">
          <el-select 
            v-model="searchForm.is_certified" 
            placeholder="请选择" 
            clearable
            class="search-select"
            @change="handleSearch"
          >
            <el-option label="是" value="是"></el-option>
            <el-option label="否" value="否"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="组织">
          <el-input 
            v-model="searchForm.organization" 
            placeholder="请输入组织" 
            clearable
            class="search-input"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item class="search-btn-group">
          <el-button type="primary" size="medium" @click="handleSearch">查询</el-button>
          <el-button size="default" @click="resetSearch">重置</el-button>
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
      title="工人数据编辑"
      :data="excelData"
      :columns="excelColumns"
      @confirm="confirmImport"
    />
    
    <!-- 工人数据表格 -->
    <div class="worker-table-section">
      <el-table 
        :data="searchForm.id || searchForm.name || searchForm.worker_type || searchForm.is_certified || searchForm.organization ? currentFilteredWorkers : currentPageWorkers" 
        v-loading="loadingWorkers"
        style="width: 100%"
        stripe
        height="670"
      >
        <!-- 动态生成列 -->
        <el-table-column
          v-for="column in workerColumns"
          :key="column.prop"
          :prop="column.prop"
          :label="column.label"
          :min-width="column.width || 120"
        >
          <template #default="scope">
            <!-- 特殊处理是否持证字段 -->
            <div v-if="column.prop === 'is_certified'">
              <span 
                v-if="scope.row[column.prop] === '是'" 
                class="certified-yes"
              >
                <el-icon><SuccessFilled /></el-icon> 是
              </span>
              <span 
                v-else-if="scope.row[column.prop] === '否'" 
                class="certified-no"
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
            <el-button size="small" @click="editWorker(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteWorker(scope.row)">删除</el-button>
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
          :total="searchForm.id || searchForm.name || searchForm.worker_type || searchForm.organization ? filteredWorkers.length : workers.length"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>

    <!-- 底部功能图标区 -->
    <div class="bottom-function-icons">
      <!-- 图标1：添加单个数据 -->
      <div class="icon-item" @click="showAddWorkerDialog" title="添加单个工人数据">
        <img src="@/assets/iconfont/添加.png" class="function-icon" alt="添加单个工人数据" />
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
    
    <!-- 编辑工人对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑工人" width="500">
      <el-form :model="currentWorker" label-width="100px">
        <el-form-item 
          v-for="column in workerColumns.filter(col => col.prop !== 'id' && col.prop !== 'created_time' && col.prop !== 'worker_type_id')" 
          :key="column.prop"
          :label="column.label"
        >
          <!-- 特殊处理是否持证字段 -->
          <el-select 
            v-if="column.prop === 'is_certified'" 
            v-model="currentWorker[column.prop]"
            style="width: 100%"
          >
            <el-option label="是" value="是"></el-option>
            <el-option label="否" value="否"></el-option>
          </el-select>
          <el-input 
            v-else
            v-model="currentWorker[column.prop]" 
            :placeholder="`请输入${column.label}`"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveWorker">保存</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 添加工人对话框 -->
    <el-dialog v-model="addDialogVisible" title="添加工人" width="500">
      <el-form :model="newWorker" label-width="100px">
        <el-form-item label="工种" prop="worker_type">
          <el-select 
            v-model="newWorker.worker_type" 
            placeholder="请选择工种"
            style="width: 100%"
          >
            <el-option
              v-for="type in workerTypes"
              :key="type"
              :label="type"
              :value="type"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="姓名" prop="name">
          <el-input 
            v-model="newWorker.name" 
            placeholder="请输入姓名"
          />
        </el-form-item>
        <el-form-item label="是否持证" prop="is_certified">
          <el-select 
            v-model="newWorker.is_certified" 
            placeholder="请选择是否持证"
            style="width: 100%"
          >
            <el-option label="是" value="是"></el-option>
            <el-option label="否" value="否"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="组织" prop="organization">
          <el-input 
            v-model="newWorker.organization" 
            placeholder="请输入组织"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="addDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="addWorker">确定</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 文件上传组件 -->
    <el-upload
      ref="uploadRef"
      class="upload-custom"
      :action="uploadUrl"
      :data="{ type: 'worker' }"
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

// 工人数据相关
const workers = ref([])
const workerColumns = ref([])
const loadingWorkers = ref(false)

// 工种列表
const workerTypes = ref([])

// 搜索相关
const searchForm = reactive({
  id: '',
  name: '',
  worker_type: '',
  is_certified: '',
  organization: ''
})

// 编辑工人相关
const editDialogVisible = ref(false)
const currentWorker = reactive({})

// 添加工人相关
const addDialogVisible = ref(false)
const newWorker = reactive({
  worker_type: '',
  name: '',
  is_certified: '是',
  organization: ''
})

// 分页相关
const currentPage = ref(1)
const pageSize = ref(10)

// 计算当前页显示的数据
const currentPageWorkers = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return workers.value.slice(start, end)
})

// 计算过滤后的数据
const filteredWorkers = computed(() => {
  return workers.value.filter(worker => {
    // 检查工号是否匹配
    const idMatch = searchForm.id ? 
      String(worker.id).includes(searchForm.id) : true
    
    // 检查姓名是否匹配
    const nameMatch = searchForm.name ? 
      worker.name && worker.name.includes(searchForm.name) : true
    
    // 检查工种是否匹配
    const workerTypeMatch = searchForm.worker_type ? 
      worker.worker_type && worker.worker_type.includes(searchForm.worker_type) : true
    
    // 检查是否持证字段是否匹配
    let certifiedMatch = true;
    if (searchForm.is_certified !== '') {
      if (searchForm.is_certified === '是') {
        certifiedMatch = worker.is_certified === '是';
      } else if (searchForm.is_certified === '否') {
        certifiedMatch = worker.is_certified === '否';
      }
    }
    
    // 检查组织是否匹配
    const organizationMatch = searchForm.organization ? 
      worker.organization && worker.organization.includes(searchForm.organization) : true
    
    return idMatch && nameMatch && workerTypeMatch && certifiedMatch && organizationMatch
  })
})

// 计算当前页显示的过滤数据
const currentFilteredWorkers = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredWorkers.value.slice(start, end)
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

// 页面加载时获取工人数据
onMounted(() => {
  fetchWorkers()
})

// 处理工人数据，将is_certified字段值映射为是/否
function processWorkerData(workersData) {
  return workersData.map(worker => {
    // 处理是否持证字段显示
    let processedWorker = { ...worker };
    
    if (worker.is_certified !== undefined) {
      processedWorker.is_certified = worker.is_certified === 1 ? '是' : (worker.is_certified === 0 ? '否' : worker.is_certified)
    }
    
    // 确保组织字段存在
    if (worker.organization === undefined) {
      processedWorker.organization = ''
    }
    
    return processedWorker
  })
}

// 获取工人数据
async function fetchWorkers() {
  try {
    loadingWorkers.value = true
    const response = await request({
      url: '/api/workers',
      method: 'get'
    })

    // Result 格式：{code: 20000, data: {workers: [...], total_count: N}}
    const processedWorkers = processWorkerData(response.data?.workers || [])
    workers.value = processedWorkers
    
    // 动态生成列定义
    if (processedWorkers.length > 0) {
      const firstRow = processedWorkers[0]
      // 定义字段映射，将英文字段名映射为中文标题
      const labelMap = {
        id: '工号',
        name: '姓名',
        worker_type: '工种',
        created_time: '创建时间',
        worker_type_id: '工种ID',
        is_certified: '是否持证',
        organization: '组织',
        compose: '班组'  // 新增班组列
      }
      
      // 生成列，排除 created_time
      let columns = Object.keys(firstRow)
        .filter(key => key !== 'created_time')
        .filter(key => key !== 'emp_id') 
        .filter(key => key !== 'compose')  // 隐藏创建时间
        .map(key => ({
          prop: key,
          label: labelMap[key] || key,
          width: key === 'compose' ? 180 : 150  // 班组列稍宽
        }))
      
      workerColumns.value = columns
      
      // 提取工种列表
      workerTypes.value = [...new Set(processedWorkers.map(worker => worker.worker_type))];
    } else {
      // 如果没有数据，设置默认列，包括班组字段
      workerColumns.value = [
        { prop: 'id', label: '工号', width: 100 },
        { prop: 'name', label: '姓名', width: 120 },
        { prop: 'worker_type', label: '工种', width: 150 },
        { prop: 'is_certified', label: '是否持证', width: 100 },
        { prop: 'organization', label: '组织', width: 150 },
      ]
    }
  } catch (error) {
    ElMessage.error('获取工人数据失败: ' + (error.message || '未知错误'))
    console.error('获取工人数据失败:', error)
  } finally {
    loadingWorkers.value = false
  }
}

// 编辑工人
function editWorker(row) {
  // 复制当前行数据到 currentWorker
  Object.keys(row).forEach(key => {
    currentWorker[key] = row[key]
  })
  editDialogVisible.value = true
}

// 保存工人修改
async function saveWorker() {
  try {
    await request({
      url: `/api/workers/${currentWorker.id}`,
      method: 'put',
      data: currentWorker
    })
    ElMessage.success('工人信息已更新')
    editDialogVisible.value = false
    // 重新获取数据以刷新表格
    await fetchWorkers()
  } catch (error) {
    ElMessage.error('更新工人信息失败: ' + (error.message || '未知错误'))
  }
}

// 删除工人
function deleteWorker(row) {
  ElMessageBox.confirm(
    `确定要删除工人 "${row.name}" 吗？此操作不可恢复。`,
    '确认删除',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',

    }
  ).then(async () => {
    try {
       await request({
        url: `/api/workers/${row.id}`,
        method: 'delete'
      })
      ElMessage.success('工人已删除')
      // 重新获取数据以刷新表格
      await fetchWorkers()
    } catch (error) {
      ElMessage.error('删除工人失败: ' + (error.message || '未知错误'))
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
  searchForm.worker_type = ''
  searchForm.is_certified = ''
  searchForm.organization = ''
  currentPage.value = 1
}

async function downloadTemplate() {
  try {
    downloading.value = true
    // 创建一个包含所有必要字段的工作表
    const worksheetData = [
      ['name', 'worker_type', 'is_certified', 'organization'],
      ['张三', '电工', '是', '电气车间'],
      ['李四', '钳工', '否', '机械车间']
    ];
    
    // 创建工作簿
    const worksheet = XLSX.utils.aoa_to_sheet(worksheetData);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, '工人数据模板');
    
    // 导出文件
    XLSX.writeFile(workbook, '工人表模版.xlsx');
    ElMessage.success('模板下载成功');
  } catch (error) {
    console.error('模板生成失败:', error);
    ElMessage.error('模板生成失败: ' + (error.message || '未知错误'));
  } finally {
    downloading.value = false;
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
      
      // 动态生成列定义，确保包含组织字段
      if (jsonData.length > 0) {
        const firstRow = jsonData[0]
        // 定义字段映射，将英文字段名映射为中文标题
        const labelMap = {
          id: '工号',
          worker_name: '姓名',
          worker_type: '工种',
          created_time: '创建时间',
          worker_type_id: '工种ID',
          is_certified: '是否持证',
          organization: '组织'
        }
        excelColumns.value = Object.keys(firstRow).map(key => ({
          prop: key,
          label: labelMap[key] || key,
          width: 150
        }))
      } else {
        // 如果没有数据，默认添加几列，包括组织字段
        excelColumns.value = [
          { prop: 'id', label: '工号', width: 100 },
          { prop: 'name', label: '姓名', width: 120 },
          { prop: 'worker_type', label: '工种', width: 150 },
          { prop: 'is_certified', label: '是否持证', width: 100 },
          { prop: 'organization', label: '组织', width: 150 }
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
    console.log(data)
    // 显示进度
    uploading.value = true
    progressVisible.value = true
    progressStatus.value = undefined
    progressPercent.value = 30 // 模拟处理中
    
    // 构造请求数据，以workers_list为键，值为Excel转换的JSON数组
    const requestData = {
      workers_list: data
    }
    
    // 发送POST请求到批量导入接口
    await request({
      url: '/api/batch-import-workers',
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
    
    // 重新获取工人数据
    await fetchWorkers()
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
  
  // 重新获取工人数据
  fetchWorkers()
}

function handleError() {
  uploading.value = false
  tipType.value = 'error'
  tipMessage.value = '导入失败，请检查文件或稍后重试'
  tipVisible.value = true
  progressStatus.value = 'exception'
  ElMessage.error('上传或导入失败')
}

// 显示添加工人对话框
function showAddWorkerDialog() {
  // 清空表单数据
  newWorker.worker_type = ''
  newWorker.name = ''
  newWorker.is_certified = '是'
  newWorker.organization = ''
  addDialogVisible.value = true
}

// 添加工人
async function addWorker() {
  if (!newWorker.worker_type || !newWorker.name) {
    ElMessage.warning('请填写完整的工人信息')
    return
  }
  
  try {
    await request({
      url: '/api/add-worker',
      method: 'post',
      data: {
        worker_type: newWorker.worker_type,
        worker_name: newWorker.name,
        is_certified: newWorker.is_certified === '是' ? 1 : 0,
        organization: newWorker.organization
      }
    })
    
    ElMessage.success('工人添加成功')
    addDialogVisible.value = false
    // 重新获取工人数据以刷新表格
    await fetchWorkers()
  } catch (error) {
    ElMessage.error('添加工人失败: ' + (error.message || '未知错误'))
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

/* 工人查询组件样式 */
.worker-search-container {
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

/* 工人数据表格部分样式 */
.worker-table-section {
  margin-top: 0;
  padding-top: 0;
  border-top: none;
}

.worker-table-section :deep(.el-table) {
  border-radius: 8px;
  border: 1px solid #f0f2f5;
  overflow: hidden;
}

.worker-table-section :deep(.el-table__inner-wrapper::before) {
  display: none;
}

.worker-table-section :deep(th.el-table__cell) {
  background-color: #f8fafc !important;
  color: #475569;
  font-weight: 600;
  height: 54px;
  border-bottom: 1px solid #e2e8f0 !important;
  border-right: none !important;
}

.worker-table-section :deep(td.el-table__cell) {
  padding: 16px 0;
  border-bottom: 1px solid #f1f5f9 !important;
  border-right: none !important;
  color: #334155;
}

.worker-table-section :deep(.el-table__row:hover > td) {
  background-color: #f8fafc !important;
}

/* 表格内按钮优化 */
.worker-table-section :deep(.el-button) {
  padding: 6px 12px;
  border-radius: 6px;
  font-weight: 500;
  border: none;
  background-color: transparent;
}

.worker-table-section :deep(.el-button:not(.el-button--danger)) {
  color: #3b82f6;
}
.worker-table-section :deep(.el-button:not(.el-button--danger):hover) {
  background-color: #eff6ff;
}

.worker-table-section :deep(.el-button--danger) {
  color: #ef4444;
}
.worker-table-section :deep(.el-button--danger:hover) {
  background-color: #fef2f2;
}

/* 分页样式 */
.pagination-container {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
}

.certified-yes {
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

.certified-no {
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