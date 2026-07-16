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
              <el-button type="primary" class="upload-btn" @click="showFilePicker = true">
                选择文件
              </el-button>
            </div>

            <div class="uploaded-files-section compact-module">
              <div class="section-header">
                <h3 class="section-title">已选文件 ({{ selectedFiles.length }})</h3>
                <el-button
                  type="text"
                  class="clear-btn"
                  @click="clearFiles"
                  :disabled="!selectedFiles.length"
                >
                  清空列表
                </el-button>
              </div>
              <div class="files-list">
                <div v-if="!selectedFiles.length" class="empty-files">暂无文件</div>
                <div
                  v-else
                  class="file-item-card"
                  v-for="(file, index) in selectedFiles"
                  :key="index"
                >
                  <div class="file-info">
                    <span class="file-name">{{ file.original_name }}</span>
                    <el-button
                      type="text"
                      class="delete-btn"
                      @click="deleteFile(index)"
                    >
                      删除
                    </el-button>
                  </div>
                </div>
              </div>

              <el-button
                type="primary"
                class="extract-btn"
                @click="startExtraction"
                :disabled="!selectedFiles.length || extractLoading"
                :loading="extractLoading"
              >
                {{ extractLoading ? '提取中...' : '开始提取知识' }}
              </el-button>
            </div>

            <!-- 从文件管理选择对话框（两步式） -->
            <el-dialog v-model="showFilePicker" :title="dialogTitle" width="640px">
              <!-- 第一步：选择文件类型 -->
              <div v-if="step === 1" class="step-type-select">
                <div class="type-card type-card-quota" @click="selectCategory('定额')">
                  <el-icon class="type-icon"><PriceTag /></el-icon>
                  <div class="type-card-content">
                    <span class="type-name">定额文件</span>
                    <span class="type-desc">检修定额标准文件</span>
                  </div>
                </div>
                <div class="type-card type-card-procedure" @click="selectCategory('规程')">
                  <el-icon class="type-icon"><Document /></el-icon>
                  <div class="type-card-content">
                    <span class="type-name">规程文件</span>
                    <span class="type-desc">维护检修规程文件</span>
                  </div>
                </div>
              </div>
              <!-- 第二步：文件列表 -->
              <div v-else class="dialog-upload-body">
                <div class="back-bar">
                  <el-button text @click="goBack">
                    <el-icon><ArrowLeft /></el-icon> 返回选择类型
                  </el-button>
                  <el-tag :type="selectedCategory === '定额' ? 'success' : 'warning'" effect="dark" size="small">
                    {{ selectedCategory }}
                  </el-tag>
                </div>
                <div v-loading="loadingMgmt" class="mgmt-file-list">
                  <div v-if="!loadingMgmt && mgmtFiles.length === 0" class="empty-files">
                    暂无{{ selectedCategory }}文件
                  </div>
                  <el-table v-else :data="mgmtFiles" @selection-change="onMgmtSelectionChange" ref="mgmtTableRef">
                    <el-table-column type="selection" width="44" />
                    <el-table-column prop="original_name" label="文件名" show-overflow-tooltip />
                    <el-table-column prop="upload_time" label="上传时间" width="160" />
                  </el-table>
                  <div class="mgmt-footer">
                    <span class="mgmt-count">已选 {{ mgmtSelected.length }} 项</span>
                    <el-button type="primary" @click="confirmMgmtSelection" :disabled="!mgmtSelected.length">
                      确认选择
                    </el-button>
                  </div>
                </div>
              </div>
            </el-dialog>
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
import { ref, watch, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft,
  ArrowRight,
  ZoomOut,
  ZoomIn,
  FullScreen,
  Document,
  Loading,
  PriceTag
} from '@element-plus/icons-vue'
import * as pdfjsLib from 'pdfjs-dist'

// ✅ 修正为 .mjs 后缀（5.x 版本的正确 worker 文件）
pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdn.jsdelivr.net/npm/pdfjs-dist@${pdfjsLib.version}/build/pdf.worker.min.mjs`
// ✅ CMaps 参数传给 getDocument，避免全局设置报错
const pdfCmapOptions = {
  cMapUrl: `https://cdn.jsdelivr.net/npm/pdfjs-dist@${pdfjsLib.version}/cmaps/`,
  cMapPacked: true,
}

// 后端接口地址（需根据实际部署调整）
const API_BASE = '/api'

// ========== 文件选择相关 ==========
const selectedFiles = ref([])       // 从文件管理选中的文件
const showFilePicker = ref(false)   // 文件选择对话框
const mgmtFiles = ref([])           // 文件管理列表
const mgmtSelected = ref([])        // 对话框中勾选的文件
const mgmtTableRef = ref(null)
const loadingMgmt = ref(false)
const extractLoading = ref(false)

// --- 新增：两步文件选择状态 ---
const step = ref(1)              // 1=类型选择，2=文件列表
const selectedCategory = ref('') // '定额' 或 '规程'
const dialogTitle = computed(() => {
  if (step.value === 1) return '选择文件类型'
  return `选择${selectedCategory.value}文件`
})

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
// ========== 从文件管理选取 ==========
async function loadMgmtFiles(category) {
  loadingMgmt.value = true
  try {
    const url = category ? `${API_BASE}/files?category=${category}` : `${API_BASE}/files`
    const resp = await fetch(url)
    const data = await resp.json()
    mgmtFiles.value = (data.success && Array.isArray(data.data)) ? data.data : []
  } catch (e) {
    mgmtFiles.value = []
    ElMessage.error('加载文件列表失败')
  } finally {
    loadingMgmt.value = false
  }
}

function onMgmtSelectionChange(selection) {
  mgmtSelected.value = selection
}

function selectCategory(category) {
  selectedCategory.value = category
  step.value = 2
  loadMgmtFiles(category)
  mgmtTableRef.value?.clearSelection()
  mgmtSelected.value = []
}

function goBack() {
  step.value = 1
  selectedCategory.value = ''
  mgmtFiles.value = []
  mgmtSelected.value = []
}

function confirmMgmtSelection() {
  for (const item of mgmtSelected.value) {
    const exists = selectedFiles.value.some(f => f.file_id === item.id)
    if (!exists) {
      selectedFiles.value.push({
        file_id: item.id,
        original_name: item.original_name,
        category: item.category,
        upload_time: item.upload_time
      })
    }
  }
  showFilePicker.value = false
  // 自动预览第一个 PDF
  if (selectedFiles.value.length && !pdfDoc) {
    loadPdfForPreview(`${API_BASE}/pdf/${selectedFiles.value[0].file_id}`)
  }
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

function clearFiles() {
  selectedFiles.value = []
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
}

function deleteFile(index) {
  const file = selectedFiles.value[index]
  selectedFiles.value.splice(index, 1)
  if (pdfDoc) {
    pdfDoc.destroy()
    pdfDoc = null
  }
  currentPageNum.value = 0
  totalPages.value = 0
  if (selectedFiles.value.length) {
    loadPdfForPreview(`${API_BASE}/pdf/${selectedFiles.value[0].file_id}`)
  }
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
    const loadingTask = pdfjsLib.getDocument({ data: arrayBuffer, ...pdfCmapOptions })
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
  if (!selectedFiles.value.length) {
    ElMessage.warning('请先选择文件')
    return
  }
  extractLoading.value = true
  let successCount = 0
  try {
    for (const fileItem of selectedFiles.value) {
      const formData = new FormData()
      formData.append('file_id', fileItem.file_id)

      // 第一步：调用 /api/parse 获取 markdown（通过 file_id 读取）
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
      successCount++
    }
    await loadQuotaData()
    ElMessage.success(`知识提取完成，成功处理 ${successCount} 个文件`)
  } catch (err) {
    ElMessage.error(`提取失败：${err.message}`)
  } finally {
    extractLoading.value = false
  }
}

function exportTable() { ElMessage.info('导出功能待实现') }
function fieldSettings() { ElMessage.info('字段设置待实现') }

onMounted(() => {
  loadQuotaData()
})

// 对话框关闭时重置步骤
watch(showFilePicker, (val) => {
  if (!val) {
    step.value = 1
    selectedCategory.value = ''
    mgmtFiles.value = []
    mgmtSelected.value = []
    mgmtTableRef.value?.clearSelection()
  }
})

onUnmounted(() => {
  if (pdfDoc) {
    pdfDoc.destroy()
    pdfDoc = null
  }
})
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

/* ========== 两步文件选择样式 ========== */
.step-type-select {
  display: flex;
  gap: 20px;
  padding: 20px 0;
  justify-content: center;
}
.type-card {
  flex: 1;
  max-width: 220px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 32px 20px;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.25s ease;
  background: #fafafa;
}
.type-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}
.type-card-quota:hover {
  border-color: #67c23a;
  background: #f0f9eb;
}
.type-card-procedure:hover {
  border-color: #e6a23c;
  background: #fdf6ec;
}
.type-icon {
  font-size: 40px;
  color: #606266;
}
.type-card-quota:hover .type-icon {
  color: #67c23a;
}
.type-card-procedure:hover .type-icon {
  color: #e6a23c;
}
.type-card-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}
.type-name {
  font-size: 18px;
  font-weight: 700;
  color: #1f2937;
}
.type-desc {
  font-size: 13px;
  color: #909399;
}
.back-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
</style>