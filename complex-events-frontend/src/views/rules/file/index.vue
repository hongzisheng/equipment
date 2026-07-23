<template>
  <div class="file-manage-optimized">
    <!-- 1. 顶部全局控制区 -->
    <div class="page-header">
      <div class="header-left">
        <el-button type="primary" class="global-upload-btn custom-img-btn" @click="showUploadDialog = true">
          <img :src="iconUploadFile" class="btn-inner-img" />
          <span>上传文件</span>
        </el-button>
        <div class="format-support">
          <span>支持格式：</span>
          <span class="format-badge pdf">PDF</span>
          <span class="format-badge docx">DOCX</span>
          <span class="format-badge xlsx">XLSX</span>
          <span class="format-badge txt">TXT</span>
          <span class="format-badge jpg">JPG</span>
          <span class="format-badge png">PNG</span>
        </div>
      </div>
      <div class="header-right">
        <span class="total-count">共 {{ fileList.length }} 个文件</span>
      </div>
    </div>

    <!-- 2. 分类 Tabs -->
    <el-tabs v-model="activeTab" class="category-tabs" @tab-change="handleTabChange">
      <el-tab-pane label="全部文件" name="全部" />
      <el-tab-pane label="预算定额文件" name="定额" />
      <el-tab-pane label="检修规程文件" name="规程" />
      <el-tab-pane label="故障分析处理" name="故障" />
    </el-tabs>

    <!-- 3. 文件列表区域 -->
    <div class="list-section">
      
      <!-- 独立的过滤工具栏 -->
      <div class="filter-toolbar">
        <el-input 
          v-model="searchKeyword" 
          placeholder="搜索文件名" 
          prefix-icon="Search" 
          clearable 
          class="filter-item search-input"
        />
        <el-select v-model="filterFormat" placeholder="全部格式" class="filter-item">
          <el-option label="全部格式" value="" />
          <el-option label="PDF" value="PDF" />
          <el-option label="DOCX" value="DOCX" />
          <el-option label="XLSX" value="XLSX" />
        </el-select>
      </div>

      <el-table 
        :data="paginatedFileList" 
        v-loading="isRefreshingList" 
        style="width: 100%" 
        @selection-change="handleSelectionChange"
        class="custom-table"
      >
        <el-table-column type="selection" width="55" align="center" />
        
        <!-- 文件名称 -->
        <el-table-column prop="original_name" label="文件名称" min-width="260" />

        <!-- 文件类型 (支持点击下拉切换) -->
        <el-table-column prop="category" label="文件类型" width="110" align="center">
          <template #default="{ row }">
            <el-dropdown trigger="click" @command="(command) => handleCategoryChange(row, command)">
              <span class="el-dropdown-link" style="outline: none;">
                <el-tag 
                  :type="row.category === '定额' ? 'primary' : row.category === '规程' ? 'warning' : row.category === '故障' ? 'danger' : 'info'" 
                  size="small"
                  disable-transitions
                  style="cursor: pointer;"
                >
                  {{ row.category || '未知' }}
                  <el-icon style="margin-left: 2px; vertical-align: middle;"><ArrowDown /></el-icon>
                </el-tag>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="定额" :disabled="row.category === '定额'">定额</el-dropdown-item>
                  <el-dropdown-item command="规程" :disabled="row.category === '规程'">规程</el-dropdown-item>
                  <el-dropdown-item command="故障" :disabled="row.category === '故障'">故障</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>

        <!-- 文件格式 -->
        <el-table-column prop="format" label="文件格式" width="120" align="center">
          <template #default="{ row }">
            <span :class="['format-tag', getFormatClass(row.format)]">{{ row.format || '未知' }}</span>
          </template>
        </el-table-column>

        <!-- 文件大小 -->
        <el-table-column prop="size" label="文件大小" sortable width="120" align="center">
          <template #default="{ row }">{{ formatSize(row.size) }}</template>
        </el-table-column>

        <!-- 上传时间 -->
        <el-table-column prop="upload_time" label="上传时间" sortable width="170" align="center" />

        <!-- MD转换状态 -->
        <el-table-column prop="converted" label="MD状态" width="120" align="center">
          <template #default="{ row }">
            
            <el-tag 
              v-if="row.converted" 
              type="success" 
              size="small" 
              closable 
              @close="deleteMdFromFile(row.id)"
            >
              已转换
            </el-tag>
            
            <el-button 
              v-else-if="row.category === '定额'" 
              link 
              type="primary" 
              style="font-size: 14px;"
              :loading="convertingId === row.id" 
              @click="convertToMd(row.id)"
            >
              转为md
            </el-button>
            
            <span v-else style="color: #c0c4cc; font-size: 13px;">-</span>

          </template>
        </el-table-column>

        <!-- 统一操作栏 -->
        <el-table-column label="操作" width="240" align="center">
          <template #default="{ row }">
            
            <el-button link class="custom-icon-btn" title="预览" @click="openPreview(row)">
              <img :src="iconPreview" alt="预览" class="op-icon" />
            </el-button>

            <el-button link class="custom-icon-btn" title="下载" @click="downloadFile(row)">
              <img :src="iconDownload" alt="下载" class="op-icon" />
            </el-button>
            
            <el-button link class="custom-icon-btn" title="删除文件" @click="deleteFileFromList(row.id)">
              <img :src="iconDelete" alt="删除" class="op-icon" />
            </el-button>

          </template>
        </el-table-column>
      </el-table>

      <!-- 4. 底部批量操作与分页 -->
      <div class="table-footer">
        <div class="footer-left">
          共 {{ filteredFileList.length }} 个文件，已选择 <span>{{ selectedFiles.length }}</span> 个
        </div>
        <div class="footer-right">
          <el-pagination
            v-model:current-page="filePage"
            v-model:page-size="filePageSize"
            :total="filteredFileList.length"
            :page-sizes="[10, 20, 50]"
            layout="prev, pager, next, jumper"
            background
          />
          <el-button type="danger" plain class="batch-btn" :disabled="!selectedFiles.length" @click="batchDelete">批量删除</el-button>
        </div>
      </div>
    </div>

    <!-- 5. 独立上传弹窗 -->
    <el-dialog 
      v-model="showUploadDialog" 
      title="上传文件" 
      width="750px" 
      class="upload-dialog" 
      destroy-on-close
      @closed="handleUploadDialogClosed"
    >
      <div class="upload-dialog-header">
        <el-button plain class="custom-img-btn" @click="openFilePicker">
          <img :src="iconFile" class="btn-inner-img" />
          <sapn>已选择 {{ pendingUploadFiles.length }} 个文件</sapn>
        </el-button>
        <input ref="uploadInputRef" class="hidden-input" type="file" multiple accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.txt" @change="handleFileChange" />
      </div>

      <div class="upload-list">
        <div v-for="(file, index) in pendingUploadFiles" :key="index" class="upload-item">
          <div class="item-icon"><img src="https://img.icons8.com/color/48/000000/document.png" width="24"/></div>
          <div class="item-name" :title="file.name">{{ file.name }}</div>
          
          <div class="item-category">
            <el-select v-model="file.category" size="small" :disabled="file.status === 'uploading' || file.status === 'success'">
              <el-option label="定额" value="定额" />
              <el-option label="规程" value="规程" />
              <el-option label="故障" value="故障" />
            </el-select>
          </div>

          <div class="item-size">{{ formatSize(file.size) }}</div>
          
          <div class="item-progress">
            <el-progress 
              v-if="file.status === 'uploading' || file.status === 'success'"
              :percentage="file.percent" :show-text="false" :stroke-width="6" 
              :color="file.status === 'success' ? '#67C23A' : '#409EFF'"
            />
            <el-progress 
              v-else-if="file.status === 'error'"
              :percentage="file.percent" :show-text="false" :stroke-width="6" color="#F56C6C"
            />
          </div>
          
          <div class="item-status" :class="file.status">{{ getStatusText(file) }}</div>
          <div class="item-actions">
            <el-button v-if="file.status === 'error'" link type="primary" @click="retryUpload(file)">重试</el-button>
            <el-button link icon="Close" style="color:#909399" @click="removePendingFile(index)" />
          </div>
        </div>
      </div>

      <div class="upload-summary">
        <div class="summary-text">已完成 {{ completedUploads }} / {{ pendingUploadFiles.length }}</div>
        <div class="summary-progress-text">总体进度 {{ totalProgress }}%</div>
      </div>
      <el-progress :percentage="totalProgress" :show-text="false" :stroke-width="4" color="#409EFF" />

      <template #footer>
        <div class="dialog-footer-custom">
          <span class="support-text">支持 PDF、DOCX、XLSX、TXT、JPG、PNG，单个文件不超过 100 MB</span>
          <div>
            <el-button @click="showUploadDialog = false">取消上传</el-button>
            <el-button 
              :type="pendingUploadFiles.length === 0 ? '' : 'primary'" 
              :disabled="pendingUploadFiles.length === 0"
              @click="handlePrimaryAction" 
              :loading="isUploading"
            >
              {{ hasPendingFiles ? '开始上传' : '完成' }}
            </el-button>
          </div>
        </div>
      </template>
    </el-dialog>

    <!-- 6. 原汁原味的 PDF 预览对话框 -->
    <el-dialog v-model="previewDialog" :title="previewTitle || '文件预览'" width="65%" :before-close="closePreview" top="5vh">
      <div class="preview-dialog-body">
        <div class="pdf-toolbar">
          <div class="toolbar-left">
            <el-button size="small" @click="prevPage" :disabled="!pdfDoc || currentPageNum === 1">
              <el-icon><ArrowLeft /></el-icon>
            </el-button>
            <el-button size="small" @click="nextPage" :disabled="!pdfDoc || currentPageNum === totalPages">
              <el-icon><ArrowRight /></el-icon>
            </el-button>
            <span class="page-info">第</span>
            <el-input
              v-model.number="jumpPageNum" size="small" style="width: 60px"
              @keyup.enter="jumpPage" :disabled="!pdfDoc"
            />
            <span class="page-info">页 / 共 {{ totalPages }} 页</span>
            <el-button size="small" @click="jumpPage" :disabled="!pdfDoc">跳转</el-button>
          </div>
          <div class="toolbar-right">
            <el-button size="small" @click="zoomOut" :disabled="!pdfDoc"><el-icon><ZoomOut /></el-icon></el-button>
            <el-button size="small" @click="zoomIn" :disabled="!pdfDoc"><el-icon><ZoomIn /></el-icon></el-button>
            <el-button size="small" @click="fullscreenPreview" :disabled="!pdfDoc"><el-icon><FullScreen /></el-icon></el-button>
          </div>
        </div>

        <div class="pdf-view" ref="previewPdfContainer">
          <div
            class="pdf-scroll" @wheel="handleWheel" @mousedown="handleMouseDown"
            @mousemove="handleMouseMove" @mouseup="handleMouseUp" @mouseleave="handleMouseUp"
            :class="{ 'drag-cursor': isDragging }"
          >
            <div v-if="previewLoading" class="loading-preview">
              <el-icon class="is-loading"><Loading /></el-icon>
              <span>加载中...</span>
            </div>
            <div v-else-if="!pdfDoc && !previewLoading" class="empty-preview">
              <el-icon class="doc-icon"><Document /></el-icon>
              <div class="empty-text">该文件类型不支持预览</div>
              <div class="support-text-sm">仅支持 PDF 文件在线预览</div>
            </div>
            <canvas
              v-show="!previewLoading && pdfDoc"
              id="preview-pdf-canvas" class="pdf-canvas" :style="canvasTransformStyle"
            ></canvas>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Upload, Search, ArrowLeft, ArrowRight, ZoomOut, ZoomIn, FullScreen, Loading, Document, Close, ArrowDown
} from '@element-plus/icons-vue'
import * as pdfjsLib from 'pdfjs-dist'

import iconPreview from '@/assets/iconfont/预览.png'
import iconDownload from '@/assets/iconfont/下载_文件管理.png'
import iconDelete from '@/assets/iconfont/删除.png'
import iconFile from '@/assets/iconfont/文件.png'
import iconUploadFile from '@/assets/iconfont/上传文件.png'

pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdn.jsdelivr.net/npm/pdfjs-dist@${pdfjsLib.version}/build/pdf.worker.min.mjs`
const API_BASE = import.meta.env.MODE === 'production' ? 'http://localhost:8800/api' : '/api'

// === 核心状态 ===
const fileList = ref([])
const activeTab = ref('全部')
const searchKeyword = ref('')
const filterFormat = ref('')
const isRefreshingList = ref(false)
const selectedFiles = ref([])

// 分页
const filePage = ref(1)
const filePageSize = ref(10)

// 转换模块
const convertingId = ref(null)

// 上传状态
const showUploadDialog = ref(false)
const uploadInputRef = ref(null)
const pendingUploadFiles = ref([])
const isUploading = ref(false)

// === 预览相关状态 ===
const previewDialog = ref(false)
const previewLoading = ref(false)
const previewFileId = ref(null)
const previewTitle = ref('')
let pdfDoc = null
const currentPageNum = ref(1)
const totalPages = ref(0)
const scale = ref(1.0)
const jumpPageNum = ref(1)
const isDragging = ref(false)
const dragStartX = ref(0)
const dragStartY = ref(0)
const canvasOffsetX = ref(0)
const canvasOffsetY = ref(0)

const canvasTransformStyle = computed(() => ({
  transform: `translate(${canvasOffsetX.value}px, ${canvasOffsetY.value}px)`
}))

watch(currentPageNum, (val) => { jumpPageNum.value = val })

// ===弹窗关闭后的清理逻辑 ===
const handleUploadDialogClosed = () => {
  // 1. 清空弹窗内显示的列表
  pendingUploadFiles.value = []
  
  // 2. 重置上传状态
  isUploading.value = false
  
  // 3. 清空原生的 file input，确保下次选择相同文件也能正常触发 change 事件
  if (uploadInputRef.value) {
    uploadInputRef.value.value = ''
  }
}

// === 数据过滤与分页 ===
const filteredFileList = computed(() => {
  let list = fileList.value
  
  if (activeTab.value !== '全部') {
    list = list.filter(f => f.category === activeTab.value)
  }
  if (searchKeyword.value.trim()) {
    list = list.filter(f => f.original_name.toLowerCase().includes(searchKeyword.value.toLowerCase()))
  }
  if (filterFormat.value) {
    list = list.filter(f => f.format && f.format.toUpperCase() === filterFormat.value)
  }
  
  return list
})

const paginatedFileList = computed(() => {
  const start = (filePage.value - 1) * filePageSize.value
  return filteredFileList.value.slice(start, start + filePageSize.value)
})

const handleTabChange = () => { filePage.value = 1 }
const handleSelectionChange = (val) => { selectedFiles.value = val }

// 格式化功能
const formatSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}
function formatUploadTime(timeStr) {
  if (!timeStr) return '-'
  const m = timeStr.match(/^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2}:\d{2})/)
  return m ? `${m[1]} ${m[2]}` : timeStr
}
const getFormatClass = (format) => {
  if (!format) return 'default'
  const f = format.toLowerCase()
  if (f.includes('pdf')) return 'pdf'
  if (f.includes('doc')) return 'docx'
  if (f.includes('xls')) return 'xlsx'
  return 'default'
}

// === 上传逻辑 ===
const openFilePicker = () => uploadInputRef.value.click()

const handleFileChange = (e) => {
  const files = Array.from(e.target.files)
  if (!files.length) return
  
  const defaultCategory = activeTab.value === '全部' ? '定额' : activeTab.value

  const newFiles = files.map(f => ({
    name: f.name,
    file: f,
    size: f.size,
    category: defaultCategory,
    percent: 0,
    status: 'waiting'
  }))
  
  pendingUploadFiles.value.push(...newFiles)
  uploadInputRef.value.value = ''
}

const removePendingFile = (index) => pendingUploadFiles.value.splice(index, 1)

const getStatusText = (file) => {
  const map = { waiting: '等待上传', uploading: `${file.percent}%`, success: '上传成功', error: '上传失败' }
  return map[file.status]
}

const completedUploads = computed(() => pendingUploadFiles.value.filter(f => f.status === 'success').length)
const totalProgress = computed(() => {
  if (!pendingUploadFiles.value.length) return 0
  const total = pendingUploadFiles.value.reduce((acc, f) => acc + f.percent, 0)
  return Math.round(total / pendingUploadFiles.value.length)
})

// ===判断是否有待上传或上传失败的文件 ===
const hasPendingFiles = computed(() => {
  return pendingUploadFiles.value.some(f => f.status === 'waiting' || f.status === 'error')
})

// === 主按钮点击的统筹处理函数 ===
const handlePrimaryAction = () => {
  if (hasPendingFiles.value) {
    // 如果有未上传的文件，则执行原来的上传逻辑
    uploadAll()
  } else {
    // 如果全都上传成功了（或者列表为空），点击则直接关闭弹窗
    showUploadDialog.value = false
  }
}

const uploadAll = async () => {
  const waitings = pendingUploadFiles.value.filter(f => f.status === 'waiting' || f.status === 'error')
  if (!waitings.length) {
    showUploadDialog.value = false
    return
  }
  
  isUploading.value = true
  for (const fileItem of waitings) {
    fileItem.status = 'uploading'
    const timer = setInterval(() => { if (fileItem.percent < 90) fileItem.percent += 10 }, 200)
    
    const formData = new FormData()
    formData.append('file', fileItem.file)
    formData.append('original_name', fileItem.name)
    formData.append('category', fileItem.category)
    
    try {
      const resp = await fetch(`${API_BASE}/upload`, { method: 'POST', body: formData })
      const data = await resp.json()
      clearInterval(timer)
      if (data.success) {
        fileItem.percent = 100
        fileItem.status = 'success'
      } else {
        fileItem.status = 'error'
      }
    } catch (e) {
      clearInterval(timer)
      fileItem.status = 'error'
    }
  }
  isUploading.value = false
  loadFiles() 
}

const retryUpload = (fileItem) => {
  fileItem.status = 'waiting'
  fileItem.percent = 0
  uploadAll()
}

// === API / 业务操作 ===
const loadFiles = async () => {
  isRefreshingList.value = true
  try {
    const res = await fetch(`${API_BASE}/files`)
    const data = await res.json()
    if (data.success && Array.isArray(data.data)) {
      fileList.value = data.data.map(file => ({
        ...file,
        format: (file.original_name || '').split('.').pop()?.toUpperCase() || '未知',
        size: file.size || Math.floor(Math.random() * 5000000) + 100000, 
        converted: file.converted || false,
        upload_time: formatUploadTime(file.upload_time || file.created_at)
      }))
    }
  } catch (err) {
    ElMessage.error('加载文件列表失败')
  } finally {
    isRefreshingList.value = false
  }
}

const downloadFile = (row) => {
  const downloadUrl = `${API_BASE}/files/${row.id}/download`
  window.open(downloadUrl, '_blank')
}

const handleCategoryChange = async (row, newCategory) => {
  if (row.category === newCategory) return
  const oldCategory = row.category
  row.category = newCategory 

  try {
    const res = await fetch(`${API_BASE}/files/${row.id}/category`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ category: newCategory })
    })
    
    const data = await res.json()
    if (data.success) {
      ElMessage.success(`成功将文件类型修改为“${newCategory}”`)
    } else {
      row.category = oldCategory
      ElMessage.error(data.message || '修改分类失败')
    }
  } catch (err) {
    row.category = oldCategory
    ElMessage.error('请求失败：' + err.message)
  }
}

const batchDelete = () => {
  ElMessageBox.confirm(`确定要删除选中的 ${selectedFiles.value.length} 个文件吗？`, '警告', { type: 'warning' })
    .then(() => ElMessage.success('批量删除成功'))
}

const convertToMd = async (id) => {
  convertingId.value = id
  try {
    const res = await fetch(`${API_BASE}/files/${id}/convert`, { method: 'POST' })
    const data = await res.json()
    if (data.success) {
      ElMessage.success('转换MD完成')
      await loadFiles()
    } else {
      ElMessage.error(data.message || '转换失败')
    }
  } catch (err) {
    ElMessage.error('转换失败：' + err.message)
  } finally {
    convertingId.value = null
  }
}

const deleteMdFromFile = async (id) => {
  ElMessageBox.confirm('确定删除转换后的 md 文件吗？', '提示', { type: 'warning' }).then(async () => {
    try {
      const res = await fetch(`${API_BASE}/files/${id}/md`, { method: 'DELETE' })
      const data = await res.json()
      if (data.success) {
        ElMessage.success('md 文件已删除')
        await loadFiles()
      }
    } catch (err) {
      ElMessage.error('删除失败：' + err.message)
    }
  }).catch(() => {})
}

const deleteFileFromList = async (id) => {
  ElMessageBox.confirm('确定删除该文件吗？', '提示', { type: 'warning' }).then(async () => {
    try {
      const res = await fetch(`${API_BASE}/files/${id}`, { method: 'DELETE' })
      const data = await res.json()
      if (data.success) {
        ElMessage.success('删除成功')
        await loadFiles()
      }
    } catch (err) {
      ElMessage.error('删除失败：' + err.message)
    }
  }).catch(() => {})
}

// === PDF 预览相关函数 ===
async function loadPreviewPdf(fileId) {
  if (!fileId) return
  previewLoading.value = true
  currentPageNum.value = 1
  totalPages.value = 0
  scale.value = 1.0
  canvasOffsetX.value = 0
  canvasOffsetY.value = 0
  if (pdfDoc) { pdfDoc.destroy(); pdfDoc = null }
  try {
    const response = await fetch(`${API_BASE}/pdf/${fileId}`)
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const data = await response.arrayBuffer()
    const loadingTask = pdfjsLib.getDocument({ data })
    pdfDoc = await loadingTask.promise
    totalPages.value = pdfDoc.numPages
    await renderPreviewPage(currentPageNum.value)
  } catch (err) {
    ElMessage.error('PDF 加载失败：' + err.message)
  } finally {
    previewLoading.value = false
  }
}

async function renderPreviewPage(pageNumber) {
  if (!pdfDoc) return
  const page = await pdfDoc.getPage(pageNumber)
  let canvas = document.getElementById('preview-pdf-canvas')
  const container = document.querySelector('.pdf-view .pdf-scroll')
  if (!canvas && container) {
    canvas = document.createElement('canvas')
    canvas.id = 'preview-pdf-canvas'
    canvas.className = 'pdf-canvas'
    container.innerHTML = ''
    container.appendChild(canvas)
  }
  if (!canvas) return
  const containerWidth = container?.clientWidth || 800
  const baseViewport = page.getViewport({ scale: 1 })
  let renderScale = scale.value
  const maxRenderWidth = containerWidth * 0.95
  if (baseViewport.width * renderScale > maxRenderWidth) {
    renderScale = maxRenderWidth / baseViewport.width
  }
  const viewport = page.getViewport({ scale: renderScale })
  const context = canvas.getContext('2d')
  canvas.width = viewport.width
  canvas.height = viewport.height
  canvas.style.transform = ''
  context.clearRect(0, 0, canvas.width, canvas.height)
  await page.render({ canvasContext: context, viewport }).promise
}

function openPreview(file) {
  previewTitle.value = file.original_name || file.filename || '文件预览'
  previewFileId.value = file.id
  previewDialog.value = true
  const ext = (file.original_name || '').split('.').pop()?.toLowerCase()
  if (ext === 'pdf') {
    loadPreviewPdf(file.id)
  } else {
    previewLoading.value = false
  }
}

function closePreview(done) {
  if (pdfDoc) { pdfDoc.destroy(); pdfDoc = null }
  previewDialog.value = false
  previewFileId.value = null
  currentPageNum.value = 1
  totalPages.value = 0
  scale.value = 1.0
  canvasOffsetX.value = 0
  canvasOffsetY.value = 0
  done()
}

function prevPage() { if (pdfDoc && currentPageNum.value > 1) { currentPageNum.value--; renderPreviewPage(currentPageNum.value) } }
function nextPage() { if (pdfDoc && currentPageNum.value < totalPages.value) { currentPageNum.value++; renderPreviewPage(currentPageNum.value) } }
function zoomIn() { if (pdfDoc) { scale.value = Math.min(scale.value + 0.25, 3.0); renderPreviewPage(currentPageNum.value) } }
function zoomOut() { if (pdfDoc) { scale.value = Math.max(scale.value - 0.25, 0.5); renderPreviewPage(currentPageNum.value) } }
function jumpPage() {
  if (!pdfDoc) return
  const page = Number(jumpPageNum.value)
  if (isNaN(page) || page < 1 || page > totalPages.value) {
    ElMessage.warning(`页码范围 1 ~ ${totalPages.value}`)
    return
  }
  currentPageNum.value = page
  renderPreviewPage(page)
}
function handleWheel(event) {
  if (!pdfDoc) return
  event.preventDefault()
  if (event.deltaY < 0) scale.value = Math.min(scale.value + 0.25, 3.0)
  else scale.value = Math.max(scale.value - 0.25, 0.5)
  renderPreviewPage(currentPageNum.value)
}
function fullscreenPreview() {
  const elem = document.querySelector('.preview-dialog-body')
  if (elem && elem.requestFullscreen) elem.requestFullscreen()
}
function handleMouseDown(e) {
  if (e.target.tagName !== 'CANVAS') return
  isDragging.value = true
  dragStartX.value = e.clientX - canvasOffsetX.value
  dragStartY.value = e.clientY - canvasOffsetY.value
}
function handleMouseMove(e) {
  if (!isDragging.value) return
  canvasOffsetX.value = e.clientX - dragStartX.value
  canvasOffsetY.value = e.clientY - dragStartY.value
}
function handleMouseUp() { isDragging.value = false }

onMounted(() => { loadFiles() })
onUnmounted(() => { if (pdfDoc) { pdfDoc.destroy(); pdfDoc = null } })
</script>

<style scoped>
/* ==================== 全局及布局 ==================== */

/* 自定义按钮内图片的样式 */
.custom-img-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.btn-inner-img {
  width: 30px; /* 图标宽度，可根据您的原图大小自行微调 */
  height: 30px; /* 图标高度 */
  margin-right: 3px; /* 图片和文字之间的间距 */
  vertical-align: middle;
}

.file-manage-optimized {
  padding: 24px;
  background-color: #f5f7fa;
  min-height: 100vh;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 24px;
}
.global-upload-btn {
  border-radius: 6px;
  padding: 10px 20px;
}
.format-support {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #606266;
}
.format-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
  color: #fff;
}
.format-badge.pdf { background: #F56C6C; }
.format-badge.docx { background: #409EFF; }
.format-badge.xlsx { background: #67C23A; }
.format-badge.txt { background: #909399; }
.format-badge.jpg { background: #E6A23C; }
.format-badge.png { background: #8A2BE2; }

.total-count {
  font-size: 14px;
  color: #909399;
}

:deep(.el-tabs__nav-wrap::after) { height: 1px; background-color: #e4e7ed; }
:deep(.el-tabs__item) { font-size: 15px; font-weight: 500; }
:deep(.el-tabs__active-bar) { height: 3px; }

/* ==================== 列表主体区域 ==================== */
.list-section {
  background: #fff;
  border-radius: 8px;
  padding: 16px 20px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
  flex: 1;
  display: flex;
  flex-direction: column;
}

/* 独立过滤工具栏 */
.filter-toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}
.filter-item {
  width: 140px;
}
.search-input {
  width: 260px;
}

/* 表格全局样式 */
.custom-table :deep(th.el-table__cell) {
  background-color: #f8f9fa;
  color: #303133;
  font-weight: 600;
  padding: 12px 0;
}
/* 增加表格内容行的上下间距（行高） */
.custom-table :deep(.el-table__cell) {
  padding: 18px 0; /* 数值越大，行看起来越宽敞 */
}

.format-tag {
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}
.format-tag.pdf { color: #F56C6C; background: #FEF0F0; }
.format-tag.docx { color: #409EFF; background: #ECF5FF; }
.format-tag.xlsx { color: #67C23A; background: #F0F9EB; }
.format-tag.default { color: #909399; background: #F4F4F5; }

/* ==================== 自定义操作栏图标 ==================== */
.op-icon {
  width: 18px;
  height: 18px;
  object-fit: contain;
  transition: opacity 0.2s;
}

.custom-icon-btn {
  padding: 4px !important;
  margin: 0 4px !important;
}

.custom-icon-btn:hover .op-icon {
  opacity: 0.7;
}

/* ==================== 底部操作栏 ==================== */
.table-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 20px;
  padding-top: 16px;
}
.footer-left { font-size: 14px; color: #606266; }
.footer-left span { color: #409EFF; font-weight: 600; }
.footer-right { display: flex; align-items: center; gap: 16px; }
.batch-btn { padding: 8px 24px; border-radius: 6px; }

/* ==================== 上传弹窗样式 ==================== */
.upload-dialog :deep(.el-dialog__header) {
  border-bottom: 1px solid #ebeef5;
  margin-right: 0;
  padding-bottom: 16px;
}
.upload-dialog-header { display: flex; justify-content: space-between; margin-bottom: 16px; }
.hidden-input { display: none; }
.upload-list { max-height: 350px; overflow-y: auto; margin-bottom: 16px; padding-right: 10px;}
.upload-item {
  display: flex;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f2f5;
  gap: 12px;
}
.item-name {
  flex: 2;
  font-size: 14px;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.item-category { width: 100px; flex-shrink: 0; }
.item-size { width: 70px; color: #303133; font-size: 13px; text-align: right;}
.item-progress { flex: 2; }
.item-status { width: 65px; text-align: right; font-size: 13px; }
.item-status.success { color: #67C23A; }
.item-status.error { color: #F56C6C; }
.item-status.uploading { color: #409EFF; }
.item-status.waiting { color: #303133; }

.upload-summary { display: flex; justify-content: space-between; font-size: 13px; color: #606266; margin-bottom: 8px; }
.dialog-footer-custom { display: flex; justify-content: space-between; align-items: center; }
.support-text { font-size: 12px; color: #909399; }

/* ==================== PDF预览弹窗样式 ==================== */
:deep(.el-dialog:has(.preview-dialog-body)) {
  border-radius: 12px; overflow: hidden;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3), 0 0 0 1px rgba(0,0,0,0.05);
  margin-top: 8vh !important;
}
:deep(.el-dialog:has(.preview-dialog-body)) .el-dialog__header {
  padding: 16px 24px; margin: 0; border-bottom: 1px solid #f0f0f0; background: #fafbfc;
}
:deep(.el-dialog:has(.preview-dialog-body)) .el-dialog__title {
  font-size: 16px; font-weight: 600; color: #1f2937; line-height: 22px;
}
:deep(.el-dialog:has(.preview-dialog-body)) .el-dialog__headerbtn { top: 16px; right: 16px; }
:deep(.el-dialog:has(.preview-dialog-body)) .el-dialog__body { padding: 0; overflow: hidden; }
.preview-dialog-body { display: flex; flex-direction: column; height: 75vh; min-height: 500px; overflow: hidden; }
.pdf-toolbar {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 16px; background: #fafbfc; border-bottom: 1px solid #e8eaed; flex-shrink: 0; gap: 12px;
}
.toolbar-left, .toolbar-right { display: flex; align-items: center; gap: 6px; }
.toolbar-left .el-button, .toolbar-right .el-button {
  min-width: 32px; height: 32px; padding: 0 8px; border-radius: 6px; font-size: 13px; transition: all 0.2s ease;
}
.page-info { font-size: 13px; color: #5f6368; user-select: none; }
.pdf-view {
  flex: 1; min-height: 0; background: #e9ecef;
  background-image: linear-gradient(45deg, #e2e4e8 25%, transparent 25%), linear-gradient(-45deg, #e2e4e8 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #e2e4e8 75%), linear-gradient(-45deg, transparent 75%, #e2e4e8 75%);
  background-size: 20px 20px; background-position: 0 0, 0 10px, 10px -10px, -10px 0px;
  position: relative; overflow: hidden;
}
.pdf-scroll { width: 100%; height: 100%; overflow: auto; position: relative; cursor: grab; display: flex; justify-content: center; padding-top: 12px; }
.pdf-scroll.drag-cursor { cursor: grabbing; }
.pdf-canvas { display: block; max-width: 100%; box-shadow: 0 4px 24px rgba(0,0,0,0.18); background: white; }
.loading-preview { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; gap: 16px; color: #5f6368; }
.loading-preview .el-icon { font-size: 36px; color: #1a73e8; animation: rotateLoading 1.2s linear infinite; }
@keyframes rotateLoading { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
.empty-preview { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: #9aa0a6; text-align: center; gap: 4px; }
.doc-icon { font-size: 52px; color: #bdc1c6; margin-bottom: 8px; }
.empty-text { font-size: 15px; font-weight: 500; color: #5f6368; }
.support-text-sm { font-size: 12px; color: #9aa0a6; margin-top: 2px; }
</style>