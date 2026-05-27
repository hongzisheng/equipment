<template>
  <el-card class="import-card" shadow="hover">
   <h2 class="title">物料台账</h2>

    <!-- 物料查询组件 -->
    <div class="material-search-container">
      <h3 class="search-title">物料查询</h3>
      <el-form :model="searchForm" class="search-form" label-width="100px" size="medium">
        <el-form-item label="物料ID">
          <el-input 
            v-model="searchForm.id" 
            placeholder="请输入物料ID" 
            clearable
            class="search-input"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="物料名称">
          <el-input 
            v-model="searchForm.name" 
            placeholder="请输入物料名称" 
            clearable
            class="search-input"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="单价区间">
          <div style="display: flex; align-items: center;">
            <el-input 
              v-model.number="searchForm.minPrice" 
              placeholder="最低价" 
              clearable
              class="search-input"
              type="number"
              style="width: 90px;"
            />
            <span style="margin: 0 5px;">-</span>
            <el-input 
              v-model.number="searchForm.maxPrice" 
              placeholder="最高价" 
              clearable
              class="search-input"
              type="number"
              style="width: 90px;"
            />
          </div>
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
      title="物料数据编辑"
      :data="excelData"
      :columns="excelColumns"
      @confirm="confirmImport"
    />
    
    <!-- 物料数据表格 -->
    <div class="material-table-section">
      <el-table 
        :data="searchForm.id || searchForm.name || searchForm.minPrice !== '' || searchForm.maxPrice !== '' ? currentFilteredMaterials : currentPageMaterials" 
        v-loading="loadingMaterials"
        style="width: 100%"
        stripe
        height="670"
      >
        <!-- 动态生成列 -->
        <el-table-column
          v-for="column in materialColumns"
          :key="column.prop"
          :prop="column.prop"
          :label="column.label"
          :min-width="column.width || 120"
        />
        
        <!-- 操作列 -->
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button size="small" @click="editMaterial(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteMaterial(scope.row)">删除</el-button>
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
          :total="searchForm.id || searchForm.name || searchForm.minPrice !== '' || searchForm.maxPrice !== '' ? filteredMaterials.length : materials.length"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>

    <!-- 底部功能图标区 -->
    <div class="bottom-function-icons">
      <!-- 图标1：添加单个数据 -->
      <div class="icon-item" @click="showAddMaterialDialog" title="添加单个物料数据">
        <img src="@/assets/iconfont/添加.png" class="function-icon" alt="添加单个物料数据" />
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
    
    <!-- 编辑物料对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑物料" width="500">
      <el-form :model="currentMaterial" label-width="100px">
        <el-form-item 
          v-for="column in materialColumns" 
          :key="column.prop"
          :label="column.label"
        >
          <el-input 
            v-model="currentMaterial[column.prop]" 
            :placeholder="`请输入${column.label}`"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveMaterial">保存</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 添加物料对话框 -->
    <el-dialog v-model="addDialogVisible" title="添加物料" width="500">
      <el-form :model="newMaterial" label-width="100px">
        <el-form-item label="物料名称" prop="name">
          <el-input 
            v-model="newMaterial.name" 
            placeholder="请输入物料名称"
          />
        </el-form-item>
        <el-form-item label="单价" prop="price">
          <el-input 
            v-model.number="newMaterial.price" 
            placeholder="请输入单价"
            type="number"
          />
        </el-form-item>
        <el-form-item label="库存数量" prop="stock_quantity">
          <el-input 
            v-model.number="newMaterial.stock_quantity" 
            placeholder="请输入库存数量"
            type="number"
          />
        </el-form-item>
        <el-form-item label="单位" prop="unit">
          <el-input 
            v-model="newMaterial.unit" 
            placeholder="请输入单位"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="addDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="addMaterial">确定</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 文件上传组件 -->
    <el-upload
      ref="uploadRef"
      class="upload-custom"
      :action="uploadUrl"
      :data="{ type: 'material' }"
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

// 物料数据相关
const materials = ref([])
const materialColumns = ref([
  { prop: 'id', label: 'ID', width: 100 },
  { prop: 'name', label: '物料名称', width: 150 },
  { prop: 'price', label: '单价', width: 100 },
  { prop: 'stock_quantity', label: '库存数量', width: 120 },
  { prop: 'unit', label: '单位', width: 100 },
  { prop: 'created_at', label: '创建时间', width: 180 }
])
const loadingMaterials = ref(false)

// 搜索相关
const searchForm = reactive({
  id: '',
  name: '',
  minPrice: '',
  maxPrice: ''
})

// 编辑物料相关
const editDialogVisible = ref(false)
const currentMaterial = reactive({})

// 添加物料相关
const addDialogVisible = ref(false)
const newMaterial = reactive({
  name: '',
  price: '',
  stock_quantity: '',
  unit: ''
})

// 分页相关
const currentPage = ref(1)
const pageSize = ref(10)

// 计算当前页显示的数据
const currentPageMaterials = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return materials.value.slice(start, end)
})

// 计算过滤后的数据
const filteredMaterials = computed(() => {
  return materials.value.filter(material => {
    // 检查ID是否匹配
    const idMatch = searchForm.id ? 
      String(material.id).includes(searchForm.id) : true
    
    // 检查物料名称是否匹配
    const nameMatch = searchForm.name ? 
      material.name && material.name.includes(searchForm.name) : true
    
    // 检查单价区间是否匹配
    let priceMatch = true;
    const price = parseFloat(material.price);
    
    if (searchForm.minPrice !== '' && !isNaN(searchForm.minPrice)) {
      priceMatch = priceMatch && price >= searchForm.minPrice;
    }
    
    if (searchForm.maxPrice !== '' && !isNaN(searchForm.maxPrice)) {
      priceMatch = priceMatch && price <= searchForm.maxPrice;
    }
    
    return idMatch && nameMatch && priceMatch
  })
})

// 计算当前页显示的过滤数据
const currentFilteredMaterials = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredMaterials.value.slice(start, end)
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

// 页面加载时获取物料数据
onMounted(() => {
  fetchMaterials()
})

// 获取物料数据
async function fetchMaterials() {
  try {
    loadingMaterials.value = true
    // TODO: 实际项目中需要替换为真实的API接口
    const response = await request({
      url: 'http://localhost:5000/api/materials',
      method: 'get'
    })
    // 设置表格数据
    materials.value = response.materials || []
  } catch (error) {
    ElMessage.error('获取物料数据失败: ' + (error.message || '未知错误'))
    console.error('获取物料数据失败:', error)
  } finally {
    loadingMaterials.value = false
  }
}

// 编辑物料
function editMaterial(row) {
  // 复制当前行数据到 currentMaterial
  Object.keys(row).forEach(key => {
    currentMaterial[key] = row[key]
  })
  editDialogVisible.value = true
}

// 保存物料修改
async function saveMaterial() {
  try {
    // 这里应该调用后端API保存修改
    ElMessage.success('物料信息已更新')
    editDialogVisible.value = false
    // 重新获取数据以刷新表格
    await fetchMaterials()
  } catch (error) {
    ElMessage.error('更新物料信息失败: ' + (error.message || '未知错误'))
  }
}

// 删除物料
function deleteMaterial(row) {
  ElMessageBox.confirm(
    `确定要删除物料 "${row.name}" 吗？此操作不可恢复。`,
    '确认删除',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      // 调用后端API删除物料
      await request({
        url: `http://localhost:5000/api/materials/${row.id}`,
        method: 'delete'
      })
      ElMessage.success('物料已删除')
      // 重新获取数据以刷新表格
      await fetchMaterials()
    } catch (error) {
      ElMessage.error('删除物料失败: ' + (error.message || '未知错误'))
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
  searchForm.minPrice = ''
  searchForm.maxPrice = ''
  currentPage.value = 1
}

async function downloadTemplate() {
  try {
    downloading.value = true
    // 直接从public目录下载Excel模板文件
    const link = document.createElement('a')
    link.href = '/物料表模版.xlsx'
    link.download = '物料表模版.xlsx'
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
          id: 'ID',
          name: '物料名称',
          price: '单价',
          stock_quantity: '库存数量',
          unit: '单位',
          created_at: '创建时间'
        }
        excelColumns.value = Object.keys(firstRow).map(key => ({
          prop: key,
          label: labelMap[key] || key,
          width: 150
        }))
      } else {
        // 如果没有数据，默认添加几列
        excelColumns.value = [
          { prop: 'id', label: 'ID', width: 100 },
          { prop: 'name', label: '物料名称', width: 150 },
          { prop: 'price', label: '单价', width: 100 }
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
    
    // 构造请求数据，以materials_list为键，值为Excel转换的JSON数组
    const requestData = {
      materials_list: data
    }
    
    // 发送POST请求到批量导入接口
    await request({
      url: 'http://localhost:5000/api/batch-import-materials',
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
    
    // 重新获取物料数据
    await fetchMaterials()
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
  
  // 重新获取物料数据
  fetchMaterials()
}

function handleError() {
  uploading.value = false
  tipType.value = 'error'
  tipMessage.value = '导入失败，请检查文件或稍后重试'
  tipVisible.value = true
  progressStatus.value = 'exception'
  ElMessage.error('上传或导入失败')
}

// 显示添加物料对话框
function showAddMaterialDialog() {
  // 清空表单数据
  newMaterial.name = ''
  newMaterial.price = ''
  newMaterial.stock_quantity = ''
  newMaterial.unit = ''
  addDialogVisible.value = true
}

// 添加物料
async function addMaterial() {
  if (!newMaterial.name) {
    ElMessage.warning('请填写完整的物料信息')
    return
  }
  
  try {
    // TODO: 实际项目中需要替换为真实的API接口
    const response = await request({
      url: 'http://localhost:5000/api/materials',
      method: 'post',
      data: {
        name: newMaterial.name,
        price: newMaterial.price,
        stock_quantity: newMaterial.stock_quantity,
        unit: newMaterial.unit
      }
    })
    
    ElMessage.success('物料添加成功')
    addDialogVisible.value = false
    // 重新获取物料数据以刷新表格
    await fetchMaterials()
  } catch (error) {
    ElMessage.error('添加物料失败: ' + (error.message || '未知错误'))
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

/* 物料查询组件样式 */
.material-search-container {
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

.search-input {
  width: 220px;
}

.search-input :deep(.el-input__wrapper) {
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

/* 物料数据表格部分样式 */
.material-table-section {
  margin-top: 0;
  padding-top: 0;
  border-top: none;
}

.material-table-section :deep(.el-table) {
  border-radius: 8px;
  border: 1px solid #f0f2f5;
  overflow: hidden;
}

.material-table-section :deep(.el-table__inner-wrapper::before) {
  display: none;
}

.material-table-section :deep(th.el-table__cell) {
  background-color: #f8fafc !important;
  color: #475569;
  font-weight: 600;
  height: 54px;
  border-bottom: 1px solid #e2e8f0 !important;
  border-right: none !important;
}

.material-table-section :deep(td.el-table__cell) {
  padding: 16px 0;
  border-bottom: 1px solid #f1f5f9 !important;
  border-right: none !important;
  color: #334155;
}

.material-table-section :deep(.el-table__row:hover > td) {
  background-color: #f8fafc !important;
}

/* 表格内按钮优化 */
.material-table-section :deep(.el-button) {
  padding: 6px 12px;
  border-radius: 6px;
  font-weight: 500;
  border: none;
  background-color: transparent;
}

.material-table-section :deep(.el-button:not(.el-button--danger)) {
  color: #3b82f6;
}
.material-table-section :deep(.el-button:not(.el-button--danger):hover) {
  background-color: #eff6ff;
}

.material-table-section :deep(.el-button--danger) {
  color: #ef4444;
}
.material-table-section :deep(.el-button--danger:hover) {
  background-color: #fef2f2;
}

/* 分页样式 */
.pagination-container {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
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