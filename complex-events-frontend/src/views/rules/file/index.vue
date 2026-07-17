<template>
  <div class="file-manage">
    <!-- 上传卡片 -->
    <el-card shadow="hover" class="upload-card">
      <div class="upload-toolbar">
        <h2 class="upload-title">文件上传</h2>
        <el-button type="primary" class="upload-btn" @click="showUploadDialog = true">
          选择文件
        </el-button>
      </div>

      <div class="uploaded-files-section compact-module">
        <div class="section-header">
          <h3 class="section-title">待上传文件 ({{ pendingUploadFiles.length }})</h3>
          <el-button
            type="text"
            class="clear-btn"
            @click="clearPendingFiles"
            :disabled="!pendingUploadFiles.length || isUploading"
          >
            清空列表
          </el-button>
        </div>
        <div class="files-list">
          <div v-if="!pendingUploadFiles.length" class="empty-files">暂无待上传文件</div>
          <div
            v-else
            class="file-item-card"
            v-for="(file, index) in pendingUploadFiles"
            :key="index"
          >
            <div class="file-info">
              <div class="file-name-wrap">
                <span class="file-name">{{ file.name }}</span>
                <el-select
                  v-model="file.category"
                  class="file-category-select"
                  size="small"
                  :disabled="isUploading"
                >
                  <el-option label="定额" value="定额" />
                  <el-option label="规程" value="规程" />
                </el-select>
              </div>
              <el-button
                type="text"
                class="delete-btn"
                @click="removePendingFile(index)"
                :disabled="isUploading"
              >
                删除
              </el-button>
            </div>
            <div v-if="file.statusText" class="file-progress">
              <el-progress :percentage="file.percent" :stroke-width="6" size="small" />
              <span class="progress-text">{{ file.statusText }}</span>
            </div>
          </div>
        </div>

        <el-button
          type="primary"
          class="upload-all-btn"
          @click="uploadAll"
          :disabled="!pendingUploadFiles.length || isUploading"
          :loading="isUploading"
        >
          {{ isUploading ? '上传中...' : '上传' }}
        </el-button>
      </div>
    </el-card>

    <!-- 文件选择对话框 -->
    <el-dialog v-model="showUploadDialog" title="选择文件" width="560px">
      <div class="dialog-upload-body">
        <div class="drop-zone" @click="openFilePicker">
          <el-icon class="cloud-icon"><UploadFilled /></el-icon>
          <div class="drop-text">拖拽文件到此处，或点击选择</div>
        </div>
        <div class="file-types-section">
          <h3 class="section-title">支持文件类型</h3>
          <div class="file-types-grid">
            <div class="file-type-card pdf">PDF</div>
            <div class="file-type-card word">WORD</div>
            <div class="file-type-card excel">EXCEL</div>
            <div class="file-type-card jpg">JPG</div>
            <div class="file-type-card png">PNG</div>
            <div class="file-type-card txt">TXT</div>
          </div>
        </div>
      </div>
    </el-dialog>

    <input
      ref="uploadInputRef"
      class="hidden-input"
      type="file"
      multiple
      accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.txt"
      @change="handleFileChange"
    />

    <!-- 文件列表（带搜索和分页，布局调整为固定底部分页） -->
    <div class="list-section">
      <div class="list-header">
        <h2 class="list-title">文件管理</h2>
        <div class="filter-toolbar">
          <el-select v-model="selectedCategory" placeholder="选择分类" @change="handleFilterChange" style="width: 200px">
            <el-option label="全部" value="" />
            <el-option label="定额" value="定额" />
            <el-option label="规程" value="规程" />
          </el-select>
          <el-input
            v-model="searchKeyword"
            placeholder="输入文件名搜索"
            prefix-icon="Search"
            clearable
            @input="handleFilterChange"
            style="width: 250px; margin-left: 12px;"
          />
        </div>
      </div>

      <div class="table-wrapper">
        <el-table :data="paginatedFileList" v-loading="isRefreshingList" style="width: 100%" stripe>
          <el-table-column prop="original_name" label="文件名" show-overflow-tooltip />
          <el-table-column prop="category" label="分类" width="100">
            <template #default="{ row }">
              <el-tag :type="row.category === '定额' ? 'success' : 'warning'" size="small">
                {{ row.category }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="upload_time" label="上传时间" width="180" />
          <el-table-column label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.converted" type="success" size="small">已转换</el-tag>
              <el-tag v-else type="info" size="small">未转换</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="280" align="center">
            <template #default="{ row }">
              <el-button size="small" type="primary" text @click="openPreview(row)">预览</el-button>
              <el-button
                v-if="row.category === '定额' && !row.converted"
                size="small"
                type="warning"
                text
                :loading="convertingId === row.id"
                @click="convertToMd(row.id)"
              >
                {{ convertingId === row.id ? '转换中...' : '转换为MD' }}
              </el-button>
              <el-button size="small" type="danger" text @click="deleteFileFromList(row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 分页控件固定在底部 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="filePage"
          v-model:page-size="filePageSize"
          :total="filteredFileList.length"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          background
        />
      </div>
    </div>

    <!-- 预览对话框（保持不变） -->
    <el-dialog v-model="previewDialog" :title="previewTitle || '文件预览'" width="80%" :before-close="closePreview" top="8vh">
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
              v-model.number="jumpPageNum"
              size="small"
              style="width: 60px"
              @keyup.enter="jumpPage"
              :disabled="!pdfDoc"
            />
            <span class="page-info">页 / 共 {{ totalPages }} 页</span>
            <el-button size="small" @click="jumpPage" :disabled="!pdfDoc">跳转</el-button>
          </div>
          <div class="toolbar-right">
            <el-button size="small" @click="zoomOut" :disabled="!pdfDoc">
              <el-icon><ZoomOut /></el-icon>
            </el-button>
            <el-button size="small" @click="zoomIn" :disabled="!pdfDoc">
              <el-icon><ZoomIn /></el-icon>
            </el-button>
            <el-button size="small" @click="fullscreenPreview" :disabled="!pdfDoc">
              <el-icon><FullScreen /></el-icon>
            </el-button>
          </div>
        </div>

        <div class="pdf-view" ref="previewPdfContainer">
          <div
            class="pdf-scroll"
            @wheel="handleWheel"
            @mousedown="handleMouseDown"
            @mousemove="handleMouseMove"
            @mouseup="handleMouseUp"
            @mouseleave="handleMouseUp"
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
              id="preview-pdf-canvas"
              class="pdf-canvas"
              :style="canvasTransformStyle"
            ></canvas>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  UploadFilled,
  ArrowLeft,
  ArrowRight,
  ZoomOut,
  ZoomIn,
  FullScreen,
  Loading,
  Search
} from '@element-plus/icons-vue'
import * as pdfjsLib from 'pdfjs-dist'

pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdn.jsdelivr.net/npm/pdfjs-dist@${pdfjsLib.version}/build/pdf.worker.min.mjs`
const API_BASE = import.meta.env.MODE === 'production' ? 'http://localhost:8800/api' : '/api'

// ========== 分类、文件列表（搜索和分页） ==========
const selectedCategory = ref('')
const searchKeyword = ref('')
const fileList = ref([])
const filePage = ref(1)
const filePageSize = ref(10)

// 上传模块
const uploadInputRef = ref(null)
const pendingUploadFiles = ref([])   // 待上传文件列表
const showUploadDialog = ref(false)
const selectedFileType = ref('定额')
const isRefreshingList = ref(false)
const isUploading = ref(false)

// 转换模块
const convertingId = ref(null)       // 正在转换的文件 ID

// 预览相关
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

watch(currentPageNum, (val) => {
  jumpPageNum.value = val
})

// ========== 过滤和分页 ==========
const filteredFileList = computed(() => {
  let list = fileList.value
  if (selectedCategory.value) {
    list = list.filter(f => f.category === selectedCategory.value)
  }
  if (searchKeyword.value.trim()) {
    const keyword = searchKeyword.value.trim().toLowerCase()
    list = list.filter(f => f.original_name && f.original_name.toLowerCase().includes(keyword))
  }
  return list
})

const paginatedFileList = computed(() => {
  const start = (filePage.value - 1) * filePageSize.value
  const end = start + filePageSize.value
  return filteredFileList.value.slice(start, end)
})

watch([selectedCategory, searchKeyword], () => {
  filePage.value = 1
})

function handleFilterChange() {
  // 由 watch 自动处理
}

// 格式化上传时间：去掉 T，去掉小数秒
function formatUploadTime(timeStr) {
  if (!timeStr) return '-'
  // 将 ISO 格式 "2026-06-20T21:04:43.123456" 转为 "2026-06-20 21:04:43"
  const m = timeStr.match(/^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2}:\d{2})/)
  return m ? `${m[1]} ${m[2]}` : timeStr
}

// ========== 加载文件列表 ==========
const loadFiles = async () => {
  const url = `${API_BASE}/files`
  try {
    const res = await fetch(url)
    const data = await res.json()
    if (data.success && Array.isArray(data.data)) {
      fileList.value = data.data.map(file => ({
        ...file,
        id: file.id,
        original_name: file.original_name || file.filename || '未知文件',
        category: file.category || '未分类',
        upload_time: formatUploadTime(file.upload_time || file.created_at),
      }))
      filePage.value = 1
    } else {
      fileList.value = []
      ElMessage.error(data.message || '加载文件列表失败')
    }
  } catch (err) {
    fileList.value = []
    ElMessage.error('加载文件列表失败：' + err.message)
  }
}

// ========== 预览跳转 ==========
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

// ========== 拖拽 ==========
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
function handleMouseUp() {
  isDragging.value = false
}

// ========== 上传 ==========
function openFilePicker() {
  uploadInputRef.value.click()
}
// 选择文件后自动关闭对话框，直接加入待上传列表
function handleFileChange(e) {
  const files = e.target.files
  if (!files.length) return
  const newFiles = []
  for (let i = 0; i < files.length; i++) {
    newFiles.push({
      name: files[i].name,
      file: files[i],
      category: selectedFileType.value,
      percent: 0,
      statusText: ''
    })
  }
  pendingUploadFiles.value.push(...newFiles)
  uploadInputRef.value.value = ''
  showUploadDialog.value = false
  ElMessage.success(`已选择 ${newFiles.length} 个文件`)
}

// 统一上传所有待上传文件
async function uploadAll() {
  if (!pendingUploadFiles.value.length || isUploading.value) return
  isUploading.value = true
  let successCount = 0

  for (let i = 0; i < pendingUploadFiles.value.length; i++) {
    const fileItem = pendingUploadFiles.value[i]
    fileItem.percent = 0
    fileItem.statusText = '上传中...'
    const formData = new FormData()
    formData.append('file', fileItem.file)
    formData.append('category', fileItem.category)
    formData.append('original_name', fileItem.name)
    try {
      const resp = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData
      })
      const data = await resp.json()
      if (data.success) {
        fileItem.percent = 100
        fileItem.statusText = '已上传'
        successCount++
      } else if (data.conflict) {
        // 重名冲突：询问用户是否覆盖
        try {
          await ElMessageBox.confirm(
            `文件 "${fileItem.name}" 已存在，是否覆盖？`,
            '文件冲突',
            { confirmButtonText: '覆盖', cancelButtonText: '跳过', type: 'warning' }
          )
          // 用户确认覆盖，重新上传带 overwrite 标记
          fileItem.statusText = '覆盖中...'
          const retryForm = new FormData()
          retryForm.append('file', fileItem.file)
          retryForm.append('category', fileItem.category)
          retryForm.append('original_name', fileItem.name)
          retryForm.append('overwrite', 'true')
          const retryResp = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            body: retryForm
          })
          const retryData = await retryResp.json()
          if (retryData.success) {
            fileItem.percent = 100
            fileItem.statusText = '已上传'
            successCount++
          } else {
            fileItem.statusText = '上传失败'
            ElMessage.error(`${fileItem.name}：${retryData.message || '覆盖上传失败'}`)
          }
        } catch {
          // 用户点了取消/跳过
          fileItem.statusText = '已跳过'
        }
      } else {
        fileItem.statusText = '上传失败'
        ElMessage.error(`${fileItem.name}：${data.message || '上传失败'}`)
      }
    } catch (err) {
      fileItem.statusText = '上传失败'
      ElMessage.error(`上传 ${fileItem.name} 失败：${err.message}`)
    }
  }

  isUploading.value = false
  // 清除已上传成功的文件，保留失败的
  pendingUploadFiles.value = pendingUploadFiles.value.filter(f => f.statusText === '上传失败')
  if (successCount > 0) {
    isRefreshingList.value = true
    try {
      await loadFiles()
      ElMessage.success(`成功上传 ${successCount} 个文件`)
    } finally {
      isRefreshingList.value = false
    }
  }
}

function clearPendingFiles() {
  pendingUploadFiles.value = []
}
function removePendingFile(index) {
  pendingUploadFiles.value.splice(index, 1)
}

// ========== PDF 预览 ==========
async function loadPreviewPdf(fileId) {
  if (!fileId) return
  previewLoading.value = true
  currentPageNum.value = 1
  totalPages.value = 0
  scale.value = 1.0
  canvasOffsetX.value = 0
  canvasOffsetY.value = 0
  if (pdfDoc) {
    pdfDoc.destroy()
    pdfDoc = null
  }
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
  const viewport = page.getViewport({ scale: scale.value })
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
  const context = canvas.getContext('2d')
  canvas.width = viewport.width
  canvas.height = viewport.height
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
    // 非 PDF 文件无法用 PDF.js 预览
    previewLoading.value = false
  }
}

function closePreview(done) {
  if (pdfDoc) {
    pdfDoc.destroy()
    pdfDoc = null
  }
  previewDialog.value = false
  previewFileId.value = null
  currentPageNum.value = 1
  totalPages.value = 0
  scale.value = 1.0
  canvasOffsetX.value = 0
  canvasOffsetY.value = 0
  done()
}

function prevPage() {
  if (pdfDoc && currentPageNum.value > 1) {
    currentPageNum.value--
    renderPreviewPage(currentPageNum.value)
  }
}
function nextPage() {
  if (pdfDoc && currentPageNum.value < totalPages.value) {
    currentPageNum.value++
    renderPreviewPage(currentPageNum.value)
  }
}
function zoomIn() {
  if (pdfDoc) {
    scale.value = Math.min(scale.value + 0.25, 3.0)
    renderPreviewPage(currentPageNum.value)
  }
}
function zoomOut() {
  if (pdfDoc) {
    scale.value = Math.max(scale.value - 0.25, 0.5)
    renderPreviewPage(currentPageNum.value)
  }
}
function handlePdfClick(event) {
  if (isDragging.value || !pdfDoc) return
  const container = event.currentTarget
  const rect = container.getBoundingClientRect()
  const clickX = event.clientX - rect.left
  const halfWidth = rect.width / 2
  clickX < halfWidth ? prevPage() : nextPage()
}
function handleWheel(event) {
  if (!pdfDoc) return
  event.preventDefault()
  if (event.deltaY < 0) {
    scale.value = Math.min(scale.value + 0.25, 3.0)
  } else {
    scale.value = Math.max(scale.value - 0.25, 0.5)
  }
  renderPreviewPage(currentPageNum.value)
}
function fullscreenPreview() {
  const elem = document.querySelector('.preview-dialog-body')
  if (elem && elem.requestFullscreen) {
    elem.requestFullscreen()
  }
}

const viewFile = (id) => {
  window.open(`${API_BASE}/pdf/${id}`)
}

const deleteFileFromList = async (id) => {
  ElMessageBox.confirm('确定删除该文件吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await fetch(`${API_BASE}/files/${id}`, { method: 'DELETE' })
      const data = await res.json()
      if (data.success) {
        ElMessage.success('删除成功')
        await loadFiles()
      } else {
        ElMessage.error(data.message || '删除失败')
      }
    } catch (err) {
      ElMessage.error('删除失败：' + err.message)
    }
  }).catch(() => {})
}

const convertToMd = async (id) => {
  convertingId.value = id
  try {
    const res = await fetch(`${API_BASE}/files/${id}/convert`, { method: 'POST' })
    const data = await res.json()
    if (data.success) {
      ElMessage.success('转换完成')
      await loadFiles()
    } else if (data.conflict) {
      // 文件已存在，询问用户是否重新转换
      try {
        await ElMessageBox.confirm(
          data.message || '该文件已转换，是否重新转换？',
          '文件已存在',
          { confirmButtonText: '重新转换', cancelButtonText: '取消', type: 'warning' }
        )
        // 用户确认重新转换
        const formData = new FormData()
        formData.append('overwrite', 'true')
        const retryRes = await fetch(`${API_BASE}/files/${id}/convert`, {
          method: 'POST',
          body: formData
        })
        const retryData = await retryRes.json()
        if (retryData.success) {
          ElMessage.success('重新转换完成')
          await loadFiles()
        } else {
          ElMessage.error(retryData.message || '重新转换失败')
        }
      } catch {
        // 用户取消，不做操作
      }
    } else {
      ElMessage.error(data.message || '转换失败')
    }
  } catch (err) {
    ElMessage.error('转换失败：' + err.message)
  } finally {
    convertingId.value = null
  }
}

// ========== 生命周期 ==========
onMounted(loadFiles)
onUnmounted(() => {
  if (pdfDoc) {
    pdfDoc.destroy()
    pdfDoc = null
  }
})
</script>

<style scoped>
/* ========== 全局容器：占据视口高度，flex列布局 ========== */
.file-manage {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
  padding: 20px;
  box-sizing: border-box;
}

/* 上传卡片：自适应高度，不压缩 */
.upload-card {
  flex-shrink: 0;
  padding: 8px 12px !important;
  margin-bottom: 16px;
}

/* ========== 文件列表区域：占据剩余高度，内部flex列 ========== */
.list-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;          /* 防止flex溢出 */
  overflow: hidden;
}

/* 列表头部（标题+工具栏）：固定 */
.list-header {
  flex-shrink: 0;
  margin-bottom: 12px;
}

.list-title {
  font-size: 20px;
  font-weight: 700;
  margin: 0 0 8px 0;
  color: #1f2937;
}

.filter-toolbar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

/* 表格容器：可滚动 */
.table-wrapper {
  flex: 1;
  overflow: auto;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.table-wrapper .el-table {
  width: 100%;
}

/* 分页容器：固定底部 */
.pagination-wrapper {
  flex-shrink: 0;
  display: flex;
  justify-content: flex-end;
  padding: 12px 0 0 0;
  border-top: 1px solid #ebeef5;
  margin-top: 12px;
}

/* ========== 以下为原有样式（未改动） ========== */
.upload-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}
.upload-title {
  font-size: 20px;
  font-weight: 700;
  margin: 0;
  color: #1f2937;
}
.upload-btn {
  min-width: 96px;
}
.upload-all-btn {
  width: 100%;
  height: 40px;
  font-size: 15px;
  font-weight: 600;
  border-radius: 6px;
  margin-top: 12px;
}
.compact-module {
  margin-top: 4px;
}
.drop-zone {
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  padding: 10px 8px;
  text-align: center;
  cursor: pointer;
  background-color: #f8fafc;
  margin-bottom: 6px;
  transition: all 0.3s ease;
}
.drop-zone:hover {
  border-color: #3b82f6;
  background-color: #eff6ff;
}
.cloud-icon {
  font-size: 28px;
  color: #3b82f6;
  margin-bottom: 4px;
}
.drop-text {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}
.support-text {
  font-size: 12px;
  color: #64748b;
}
.file-types-section {
  margin-bottom: 6px;
}
.section-title {
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 6px 0;
  color: #1f2937;
}
.file-types-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}
.file-type-card {
  border-radius: 6px;
  padding: 8px 4px;
  text-align: center;
  color: white;
  font-weight: 600;
}
.pdf { background: linear-gradient(135deg, #f97316, #fb923c); }
.word { background: linear-gradient(135deg, #2563eb, #3b82f6); }
.excel { background: linear-gradient(135deg, #10b981, #34d399); }
.jpg { background: linear-gradient(135deg, #ef4444, #f87171); }
.png { background: linear-gradient(135deg, #8b5cf6, #a78bfa); }
.txt { background: linear-gradient(135deg, #64748b, #94a3b8); }

.uploaded-files-section {
  margin-bottom: 8px;
}
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.clear-btn {
  font-size: 12px;
  color: #64748b;
}
.files-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.empty-files {
  color: #94a3b8;
  font-size: 12px;
  text-align: center;
  padding: 8px 0;
}
.file-item-card {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 6px 10px;
}
.file-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}
.file-name-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex: 1;
}
.file-name {
  font-size: 15px;
  font-weight: 500;
  color: #1f2937;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 70%;
}
.file-category-select {
  width: 100px;
  flex-shrink: 0;
}
.delete-btn {
  color: #ef4444;
  font-size: 12px;
  padding: 0;
}
.file-progress {
  display: flex;
  align-items: center;
  gap: 10px;
}
.progress-text {
  font-size: 12px;
  color: #6b7280;
  min-width: 60px;
  text-align: right;
}
.hidden-input {
  display: none;
}
.preview-section {
  flex: 1;
  min-height: 0;
  display: flex;
}
.preview-card {
  height: 100%;
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 12px !important;
  box-sizing: border-box;
  overflow: hidden;
}
.preview-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: #1f2937;
}
.pdf-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 8px;
  background: #f5f7fa;
  border-radius: 6px 6px 0 0;
  border: 1px solid #ebeef5;
  border-bottom: none;
}
.toolbar-left, .toolbar-right {
  display: flex;
  align-items: center;
  gap: 4px;
}
.page-info {
  font-size: 12px;
  color: #606266;
}
.pdf-view {
  flex: 1;
  min-height: 800px;
  background: #555a64;
  border: 1px solid #ebeef5;
  border-top: none;
  border-bottom: none;
  overflow: hidden;
}
.pdf-scroll {
  width: 100%;
  height: 100%;
  min-height: 0;
  position: relative;
  cursor: grab;
}
.pdf-scroll.drag-cursor {
  cursor: grabbing;
}
.pdf-canvas {
  display: block;
  position: absolute;
  left: 50%;
  top: 50%;
  transform-origin: center center;
}
.empty-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 240px;
  color: #b0b3b8;
  text-align: center;
}
.loading-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 240px;
  gap: 8px;
  color: white;
}
.doc-icon {
  font-size: 56px;
  margin-bottom: 10px;
}
.empty-text {
  font-size: 15px;
}
.support-text-sm {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 4px;
}
.pdf-footer {
  padding: 6px 8px;
  background: #f5f7fa;
  border-radius: 0 0 6px 6px;
  border: 1px solid #ebeef5;
  border-top: none;
  text-align: center;
}
.highlight-info {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #606266;
}
.highlight-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #facc15;
}
.result-card {
  height: 100%;
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px !important;
  overflow: hidden;
  min-width: 0;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.title-group {
  display: flex;
  align-items: center;
  gap: 12px;
}
.main-title {
  font-size: 22px;
  font-weight: 600;
  margin: 0;
  color: #1f2937;
}
.count-tag {
  font-size: 14px;
  height: 26px;
  line-height: 24px;
}
.header-actions {
  display: flex;
  gap: 12px;
}
.result-table {
  flex: 1;
  margin-bottom: 16px;
  min-height: 0;
  width: 100%;
}
:deep(.el-card__body) {
  padding: 0 !important;
  height: 100%;
  display: flex;
  flex-direction: column;
}
.dialog-upload-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.result-table-container {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: auto;
  padding-right: 8px;
  min-width: 0;
}
</style>