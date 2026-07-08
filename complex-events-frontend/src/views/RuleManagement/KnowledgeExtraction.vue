<template>
  <div class="knowledge-page">
    <!-- 主容器：左右35:65布局 -->
    <div class="main-container">
      <!-- 左列：上传区 + PDF预览 -->
      <div class="left-column">
        <!-- 上传区 -->
        <div class="upload-section">
          <el-card shadow="hover" class="upload-card">
            <div class="upload-toolbar">
              <h2 class="upload-title">上传区</h2>
              <el-button type="primary" class="upload-btn" @click="showUploadDialog = true">
                上传文件
              </el-button>
            </div>

            <div class="uploaded-files-section compact-module">
              <div class="section-header">
                <h3 class="section-title">已上传文件 ({{ uploadedFiles.length }})</h3>
                <el-button
                  type="text"
                  class="clear-btn"
                  @click="clearFiles"
                  :disabled="!uploadedFiles.length"
                >
                  清空列表
                </el-button>
              </div>
              <div class="files-list">
                <div v-if="!uploadedFiles.length" class="empty-files">暂无文件</div>
                <div
                  v-else
                  class="file-item-card"
                  v-for="(file, index) in uploadedFiles"
                  :key="index"
                >
                  <div class="file-info">
                    <span class="file-name">{{ file.name }}</span>
                    <el-button
                      type="text"
                      class="delete-btn"
                      @click="deleteFile(index)"
                      :disabled="file.loading"
                    >
                      删除
                    </el-button>
                  </div>
                  <div v-if="file.loading" class="file-progress">
                    <el-progress :percentage="file.percent" :stroke-width="6" size="small" />
                    <span class="progress-text">{{ file.statusText }}</span>
                  </div>
                </div>
              </div>

              <el-button
                type="primary"
                class="extract-btn"
                @click="startExtraction"
                :disabled="!uploadedFiles.length"
              >
                开始提取知识
              </el-button>
            </div>

            <el-dialog v-model="showUploadDialog" title="选择文件" width="560px">
              <div class="dialog-upload-body">
                <div class="drop-zone" @click="openFilePicker">
                  <el-icon class="cloud-icon"><UploadFilled /></el-icon>
                  <div class="drop-text">拖拽文件到此处，或点击上传</div>
                  <div class="support-text">支持 PDF 格式（仅PDF可预览）</div>
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
              accept=".pdf"
              @change="handleFileChange"
            />
          </el-card>
        </div>

        <!-- PDF预览区（使用 pdf.js 渲染） -->
        <div class="preview-section">
          <el-card shadow="hover" class="preview-card">
            <h2 class="preview-title">原始文档预览 (PDF)</h2>
            <div class="pdf-toolbar">
              <div class="toolbar-left">
                <el-button size="small" @click="prevPage" :disabled="!pdfDoc">
                  <el-icon><ArrowLeft /></el-icon>
                </el-button>
                <el-button size="small" @click="nextPage" :disabled="!pdfDoc">
                  <el-icon><ArrowRight /></el-icon>
                </el-button>
                <span class="page-info">{{ currentPageNum }} / {{ totalPages }}</span>
              </div>
              <div class="toolbar-right">
                <el-button size="small" @click="zoomOut" :disabled="!pdfDoc">
                  <el-icon><ZoomOut /></el-icon>
                </el-button>
                <el-button size="small" @click="zoomIn" :disabled="!pdfDoc">
                  <el-icon><ZoomIn /></el-icon>
                </el-button>
                <el-button size="small" @click="fullscreen">
                  <el-icon><FullScreen /></el-icon>
                </el-button>
              </div>
            </div>
            <div class="pdf-view" ref="pdfContainer">
              <div class="pdf-scroll">
                <div v-if="!pdfDoc && !pdfLoading" class="empty-preview">
                  <el-icon class="doc-icon"><Document /></el-icon>
                  <div class="empty-text">请上传 PDF 文件以预览</div>
                </div>
                <div v-else-if="pdfLoading" class="loading-preview">
                  <el-icon class="is-loading"><Loading /></el-icon>
                  <span>加载中...</span>
                </div>
                <canvas id="pdf-canvas" v-show="pdfDoc"></canvas>
              </div>
            </div>
            <div class="pdf-footer">
              <div class="highlight-info">
                <span class="highlight-dot"></span>
                <span>高亮：第{{ currentPageNum }}页</span>
              </div>
            </div>
          </el-card>
        </div>
      </div>

      <!-- 右列：知识提取结果 -->
      <div class="right-column">
        <el-card shadow="hover" class="result-card">
          <div class="card-header">
            <div class="title-group">
              <h2 class="main-title">知识提取结果</h2>
              <el-tag class="count-tag" type="info" effect="plain">{{ total }}条记录</el-tag>
            </div>
            <div class="header-actions">
              <el-button @click="exportTable">导出表格</el-button>
              <el-button @click="fieldSettings">字段设置</el-button>
            </div>
          </div>
          <div class="result-table-container">
          <el-table
            :data="paginatedData"
            v-loading="resultLoading"
            border
            stripe
            class="result-table"
            empty-text="暂无数据"
          >
<el-table-column type="index" label="#" width="50" align="center" />
<el-table-column prop="process" label="工序" min-width="150" />
<el-table-column prop="measurementDimension" label="计量维度" min-width="160" />
<el-table-column prop="measurementValue" label="计量值" min-width="120" align="center" />
<el-table-column prop="manHours" label="需要的人工时(工时)" min-width="160" align="center" />
<el-table-column prop="laborCost" label="工人费用(元)" min-width="140" align="center" />
<el-table-column prop="toolCost" label="机具费用(元)" min-width="140" align="center" />
<el-table-column label="操作" width="110" align="center">
  <template #default="{ row }">
    <el-button type="text" size="small" @click="openEdit(row)">编辑</el-button>
  </template>
</el-table-column>
          </el-table>
          </div>
          <div class="pagination-wrapper">
            <span class="total-text">共 {{ total }} 条</span>
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :total="total"
              :page-sizes="[10, 20, 50, 100]"
              layout="prev, pager, next, jumper, sizes"
              background
            />
          </div>
        </el-card>
      </div>
    </div>
    <el-dialog v-model="showEditDialog" title="编辑提取结果" width="560px">
      <div class="dialog-body">
        <el-form label-position="top" :model="editForm">
          <el-form-item label="计量维度">
            <el-input v-model="editForm.measurementDimension" />
          </el-form-item>
          <el-form-item label="计量值">
            <el-input v-model="editForm.measurementValue" />
          </el-form-item>
          <el-form-item label="需要的人工时(工时)">
            <el-input v-model="editForm.manHours" />
          </el-form-item>
          <el-form-item label="工人费用(元)">
            <el-input v-model="editForm.laborCost" />
          </el-form-item>
          <el-form-item label="机具费用(元)">
            <el-input v-model="editForm.toolCost" />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  UploadFilled,
  ArrowLeft,
  ArrowRight,
  ZoomOut,
  ZoomIn,
  FullScreen,
  Document,
  Loading
} from '@element-plus/icons-vue'
import * as pdfjsLib from 'pdfjs-dist'

// ✅ 修正为 .mjs 后缀（5.x 版本的正确 worker 文件）
pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdn.jsdelivr.net/npm/pdfjs-dist@${pdfjsLib.version}/build/pdf.worker.min.mjs`

// 后端接口地址（需根据实际部署调整）
const API_BASE = 'http://localhost:8800/api'

// ========== 上传相关 ==========
const uploadInputRef = ref(null)
const uploadedFiles = ref([])
const showUploadDialog = ref(false)

// 本地存储键名（方便未来版本升级）
const UPLOADED_FILES_KEY = 'knowledge_uploaded_files_v1'

// ========== PDF 预览相关 ==========
let pdfDoc = null
const pdfLoading = ref(false)
const currentPageNum = ref(1)
const totalPages = ref(0)
const scale = ref(1.0)

// ========== 表格数据 ==========
let allTableData = ref([])
const paginatedData = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const resultLoading = ref(false)

// 监听分页
watch([allTableData, currentPage, pageSize], () => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  paginatedData.value = allTableData.value.slice(start, end)
  total.value = allTableData.value.length
}, { immediate: true })

// ========== 辅助函数 ==========
function openFilePicker() {
  uploadInputRef.value.click()
}

function formatAmount(value) {
  if (value === null || value === undefined || value === '') return '-'
  const numericValue = Number(value)
  if (Number.isFinite(numericValue)) {
    return numericValue.toFixed(2)
  }
  return String(value)
}

function formatManHours(value) {
  if (value === null || value === undefined || value === '') return '-'
  const numericValue = Number(value)
  if (Number.isFinite(numericValue)) {
    return numericValue.toFixed(3)
  }
  return String(value)
}

function formatQuotaValue(value) {
  if (value === null || value === undefined || value === '') return '-'
  return String(value)
}

function normalizeQuotaRow(row) {
  return {
    process: row.processName || row.process || '未关联',
    processId: row.processId || row.processId || null,
    quotaId: row.quotaId || row.quota || null,
    measurementDimension: formatQuotaValue(row.measurementDimension),
    measurementValue: formatQuotaValue(row.measurementValue),
    manHours: formatManHours(row.manHours),
    laborCost: formatAmount(row.laborCost),
    toolCost: formatAmount(row.toolCost)
  }
}

async function loadQuotaData() {
  resultLoading.value = true
  try {
    const resp = await fetch(`${API_BASE}/quotas`)
    const data = await resp.json()
    if (!resp.ok || !data.ok) {
      throw new Error(data.error || '读取数据库失败')
    }

    allTableData.value = (data.data || []).map(normalizeQuotaRow)
    currentPage.value = 1
  } catch (err) {
    allTableData.value = []
    ElMessage.error(`加载结果失败：${err.message}`)
  } finally {
    resultLoading.value = false
  }
}

// ========== 编辑功能 ==========
const showEditDialog = ref(false)
const editForm = ref({})
function openEdit(row) {
  editForm.value = {
    process: row.process,
    processId: row.processId || null,
    quotaId: row.quotaId || null,
    measurementDimension: row.measurementDimension || '',
    measurementValue: row.measurementValue || '',
    manHours: row.manHours || '',
    laborCost: row.laborCost || '',
    toolCost: row.toolCost || ''
  }
  showEditDialog.value = true
}

async function saveEdit() {
  if (!editForm.value.quotaId) {
    ElMessage.error('缺少定额编号，无法保存')
    return
  }
  try {
    const resp = await fetch(`${API_BASE}/update_quota`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        quotaId: editForm.value.quotaId,
        processId: editForm.value.processId,
        measurementDimension: editForm.value.measurementDimension,
        measurementValue: editForm.value.measurementValue,
        manHours: editForm.value.manHours,
        laborCost: editForm.value.laborCost,
        toolCost: editForm.value.toolCost
      })
    })
    const data = await resp.json()
    if (!resp.ok || !data.ok) throw new Error(data.error || '保存失败')

    // 更新本地表格数据
    const idx = allTableData.value.findIndex(r => r.quotaId === editForm.value.quotaId)
    if (idx !== -1) {
      allTableData.value[idx] = normalizeQuotaRow(Object.assign({}, allTableData.value[idx], {
        processName: editForm.value.process,
        processId: editForm.value.processId,
        quotaId: editForm.value.quotaId,
        measurementDimension: editForm.value.measurementDimension,
        measurementValue: editForm.value.measurementValue,
        manHours: editForm.value.manHours,
        laborCost: editForm.value.laborCost,
        toolCost: editForm.value.toolCost
      }))
      // refresh pagination slice
      const start = (currentPage.value - 1) * pageSize.value
      const end = start + pageSize.value
      paginatedData.value = allTableData.value.slice(start, end)
    }

    showEditDialog.value = false
    ElMessage.success('保存成功')
  } catch (err) {
    ElMessage.error(`保存失败：${err.message}`)
  }
}

async function handleFileChange(e) {
  const files = e.target.files
  if (!files.length) return

  for (let i = 0; i < files.length; i++) {
    const file = files[i]
    if (file.type !== 'application/pdf') {
      ElMessage.warning(`文件 ${file.name} 不是 PDF，仅 PDF 可预览，但仍可上传用于知识提取`)
    }

    const uploadItem = {
      name: file.name,
      file: file,
      loading: true,
      percent: 0,
      statusText: '上传中...',
      file_id: null,
      pdfUrl: null
    }
    uploadedFiles.value.push(uploadItem)
    const idx = uploadedFiles.value.length - 1

    const formData = new FormData()
    formData.append('file', file)

    try {
      const resp = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
      })
      const data = await resp.json()
      if (data.success) {
        uploadedFiles.value[idx].percent = 100
        uploadedFiles.value[idx].loading = false
        uploadedFiles.value[idx].statusText = '已上传'
        uploadedFiles.value[idx].file_id = data.file_id
        uploadedFiles.value[idx].pdfUrl = data.url

        // 如果是 PDF 且尚无预览，自动加载第一个 PDF
        if (file.type === 'application/pdf' && !pdfDoc) {
          loadPdfForPreview(data.url)
        }
      } else {
        throw new Error(data.message)
      }
    } catch (err) {
      uploadedFiles.value[idx].loading = false
      uploadedFiles.value[idx].statusText = '上传失败'
      ElMessage.error(`上传 ${file.name} 失败：${err.message}`)
    }
  }
  uploadInputRef.value.value = ''
}

function clearFiles() {
  uploadedFiles.value = []
  if (pdfDoc) {
    pdfDoc.destroy()
    pdfDoc = null
  }
  currentPageNum.value = 0
  totalPages.value = 0
  const canvas = document.getElementById('pdf-canvas')
  if (canvas) {
    const ctx = canvas.getContext('2d')
    ctx.clearRect(0, 0, canvas.width, canvas.height)
  }
  // 同步清除持久化数据
  try { localStorage.removeItem(UPLOADED_FILES_KEY) } catch (e) { /* ignore */ }
}

function deleteFile(index) {
  const file = uploadedFiles.value[index]
  if (file.loading) {
    ElMessage.warning('文件正在处理，请稍后再试')
    return
  }
  uploadedFiles.value.splice(index, 1)
  // 如果当前预览的是被删除的文件，则尝试切换到下一个可预览的 PDF，否则清空预览
  if (pdfDoc && file.pdfUrl === pdfDoc.url) {
    const nextPdf = uploadedFiles.value.find(f => f.pdfUrl)
    if (nextPdf) {
      loadPdfForPreview(nextPdf.pdfUrl)
    } else {
      clearFiles()
    }
  }

  // 删除后持久化
  persistUploadedFiles()
}

async function loadPdfForPreview(url) {
  if (!url) return
  pdfLoading.value = true

  if (pdfDoc) {
    pdfDoc.destroy()
    pdfDoc = null
  }

  try {
    const response = await fetch(url)
    if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`)

    const arrayBuffer = await response.arrayBuffer()
    const loadingTask = pdfjsLib.getDocument({ data: arrayBuffer })
    pdfDoc = await loadingTask.promise
    pdfDoc.url = url
    totalPages.value = pdfDoc.numPages
    currentPageNum.value = 1
    await renderPage(1)
  } catch (err) {
    console.error('PDF 加载失败', err)
    if (err.message.includes('Failed to fetch') || err.name === 'TypeError') {
      ElMessage.error('PDF 加载失败：网络错误或跨域限制，请确认后端已开启 CORS 或部署同源')
    } else if (err.message.includes('Invalid PDF')) {
      ElMessage.error('PDF 文件无效或已损坏')
    } else {
      ElMessage.error('PDF 加载失败，请检查控制台')
    }
    pdfDoc = null
  } finally {
    pdfLoading.value = false
  }
}

async function renderPage(pageNumber) {
  if (!pdfDoc) return
  const page = await pdfDoc.getPage(pageNumber)
  const viewport = page.getViewport({ scale: scale.value })

  let canvas = document.getElementById('pdf-canvas')
  if (!canvas) {
    canvas = document.createElement('canvas')
    canvas.id = 'pdf-canvas'
    canvas.style.display = 'block'
    canvas.style.margin = '0 auto'
    const container = document.querySelector('.pdf-view .pdf-scroll')
    if (container) {
      container.innerHTML = ''
      container.appendChild(canvas)
    }
  }

  const context = canvas.getContext('2d')
  canvas.width = viewport.width
  canvas.height = viewport.height
  context.clearRect(0, 0, canvas.width, canvas.height)

  await page.render({ canvasContext: context, viewport: viewport }).promise
}

function prevPage() {
  if (pdfDoc && currentPageNum.value > 1) {
    currentPageNum.value--
    renderPage(currentPageNum.value)
  }
}
function nextPage() {
  if (pdfDoc && currentPageNum.value < totalPages.value) {
    currentPageNum.value++
    renderPage(currentPageNum.value)
  }
}
function zoomIn() {
  if (pdfDoc) {
    scale.value = Math.min(scale.value + 0.25, 3.0)
    renderPage(currentPageNum.value)
  }
}
function zoomOut() {
  if (pdfDoc) {
    scale.value = Math.max(scale.value - 0.25, 0.5)
    renderPage(currentPageNum.value)
  }
}
function fullscreen() {
  const elem = document.querySelector('.preview-card')
  if (elem.requestFullscreen) elem.requestFullscreen()
}

watch(scale, () => {
  if (pdfDoc && !pdfLoading.value) renderPage(currentPageNum.value)
})

async function startExtraction() {
  if (!uploadedFiles.value.length) {
    ElMessage.warning('请先上传文件')
    return
  }
  uploadedFiles.value.forEach(f => {
    f.loading = true
    f.statusText = '提取中...'
    f.percent = 0
  })
  try {
    for (const fileItem of uploadedFiles.value) {
      const formData = new FormData()
      formData.append('file', fileItem.file)

      // 第一步：调用 /api/parse 获取 markdown
      const resp = await fetch(`${API_BASE}/parse`, {
        method: 'POST',
        body: formData
      })
      const result = await resp.json()
      if (!resp.ok || !result.ok) {
        throw new Error(result.error || '解析失败')
      }

      const markdown = result.markdown
      if (!markdown) {
        throw new Error('未返回 markdown')
      }

      // 第二步：将 markdown 发送到后端入库接口
      const importResp = await fetch(`${API_BASE}/markdown_extract`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ markdown })
      })
      const importResult = await importResp.json()
      if (!importResp.ok || !importResult.ok) {
        throw new Error(importResult.error || '入库失败')
      }

      fileItem.percent = 100
      fileItem.statusText = '已入库'
      fileItem.loading = false
    }
    await loadQuotaData()
    ElMessage.success('知识提取并入库完成')
  } catch (err) {
    ElMessage.error(`提取失败：${err.message}`)
    uploadedFiles.value.forEach(f => {
      if (f.loading) {
        f.loading = false
        f.statusText = '提取失败'
      }
    })
  }
}

function exportTable() { ElMessage.info('导出功能待实现') }
function fieldSettings() { ElMessage.info('字段设置待实现') }

onMounted(() => {
  // 先恢复上传队列，再加载定额数据
  restoreUploadedFiles()
  loadQuotaData()
})

onUnmounted(() => {
  if (pdfDoc) {
    pdfDoc.destroy()
    pdfDoc = null
  }
})

// ========== 上传持久化相关 ==========
function persistUploadedFiles() {
  try {
    const serial = uploadedFiles.value.map(f => ({
      name: f.name || '',
      loading: !!f.loading,
      percent: f.percent || 0,
      statusText: f.statusText || '',
      file_id: f.file_id || null,
      pdfUrl: f.pdfUrl || null
    }))
    localStorage.setItem(UPLOADED_FILES_KEY, JSON.stringify(serial))
  } catch (e) {
    console.warn('保存上传列表到 localStorage 失败', e)
  }
}

function restoreUploadedFiles() {
  try {
    const raw = localStorage.getItem(UPLOADED_FILES_KEY)
    if (!raw) return
    const arr = JSON.parse(raw)
    if (!Array.isArray(arr) || !arr.length) return
    // 恢复为没有 File 对象的条目（file 字段置 null）
    uploadedFiles.value = arr.map(item => ({
      name: item.name || '未知文件',
      file: null,
      loading: false,
      percent: item.percent || 0,
      statusText: item.statusText || (item.file_id ? '已上传' : ''),
      file_id: item.file_id || null,
      pdfUrl: item.pdfUrl || null
    }))

    // 自动预览第一个可预览的 PDF
    const firstPdf = uploadedFiles.value.find(f => f.pdfUrl)
    if (firstPdf && !pdfDoc) {
      loadPdfForPreview(firstPdf.pdfUrl)
    }
  } catch (e) {
    console.warn('从 localStorage 恢复上传列表失败', e)
  }
}

// 监控 uploadedFiles 变化并持久化（节流可选，当前简单保存）
watch(uploadedFiles, () => {
  persistUploadedFiles()
}, { deep: true })
</script>

<style scoped>
/* ========== 完整样式保持不变 ========== */
.knowledge-page {
  padding: 20px;
  min-height: 100vh;
  box-sizing: border-box;
}
.main-container {
  display: flex;
  gap: 20px;
  width: 100%;
  align-items: stretch;
}
.left-column {
  flex: 0 0 35%;
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: calc(100vh - 40px);
  min-height: calc(100vh - 40px);
}
.right-column {
  flex: 0 0 65%;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 40px);
  min-height: calc(100vh - 40px);
}
.upload-section {
  flex-shrink: 0;
}
.upload-card {
  padding: 12px !important;
}
.upload-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}
.upload-title {
  font-size: 18px;
  font-weight: 700;
  margin: 0;
  color: #1f2937;
}
.upload-btn {
  min-width: 96px;
}
.compact-module {
  margin-top: 4px;
}
.drop-zone {
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  padding: 12px 10px;
  text-align: center;
  cursor: pointer;
  background-color: #f8fafc;
  margin-bottom: 8px;
  transition: all 0.3s ease;
}
.drop-zone:hover {
  border-color: #3b82f6;
  background-color: #eff6ff;
}
.cloud-icon {
  font-size: 28px;
  color: #3b82f6;
  margin-bottom: 6px;
}
.drop-text {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}
.support-text {
  font-size: 12px;
  color: #64748b;
}
.file-types-section {
  margin-bottom: 8px;
}
.section-title {
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 8px 0;
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
  margin-bottom: 12px;
}
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.clear-btn {
  font-size: 12px;
  color: #64748b;
}
.files-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.empty-files {
  color: #94a3b8;
  font-size: 12px;
  text-align: center;
  padding: 10px 0;
}
.file-item-card {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 10px 12px;
}
.file-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.file-name {
  font-size: 13px;
  color: #1f2937;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 75%;
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
.extract-btn {
  width: 100%;
  height: 36px;
  font-size: 14px;
  font-weight: 600;
  border-radius: 6px;
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
  min-height: 0;
  background: #555a64;
  display: flex;
  border: 1px solid #ebeef5;
  border-top: none;
  border-bottom: none;
  overflow: hidden;
}
.pdf-scroll {
  width: 100%;
  height: 100%;
  min-height: 0;
  overflow: auto;
  display: flex;
  align-items: flex-start;
  justify-content: center;
}
.pdf-scroll canvas {
  display: block;
  margin: 0 auto;
  max-width: 100%;
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
.pagination-wrapper {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 8px;
  border-top: 1px solid #ebeef5;
}
.total-text {
  color: #606266;
  font-size: 14px;
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
/* 可滚动的结果表容器 */
.result-table-container {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 8px;
}
</style>