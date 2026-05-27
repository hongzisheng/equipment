<template>
  <div class="search-container">
    <div class="left-panel">
      <!-- 检索词条 -->
      <div class="search-area">
        <h3 class="section-title">检索词条</h3>
        <el-form :model="form" label-width="140px" size="small" label-position="left">
          <el-form-item label="设备类型">
            <el-select
              v-model="form.category"
              placeholder="请选择设备类型"
              clearable
              filterable
              @change="onCategoryChange"
            >
              <el-option
                v-for="item in categoryOptions"
                :key="item.id"
                :label="item.name"
                :value="item.id"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="设备">
            <el-select
              v-model="form.device"
              placeholder="请输入或选择设备"
              clearable
              filterable
              :disabled="deviceLoading"
            >
              <el-option
                v-for="item in deviceOptions"
                :key="item.name"
                :label="item.name"
                :value="item.name"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="工序">
            <el-select v-model="form.process" placeholder="请输入或选择工序" clearable filterable>
              <el-option
                v-for="item in processOptions"
                :key="item"
                :label="item"
                :value="item"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="计量值">
            <el-input
              v-model="form.measureValue"
              placeholder="输入计量值（数字）"
              clearable
              type="number"
            />
          </el-form-item>

          <el-form-item class="button-group">
            <el-button @click="reset" class="reset-btn">重置</el-button>
            <el-button type="primary" @click="search" class="search-btn">检索</el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 检索结果 -->
      <div class="results-area">
        <div class="results-header">
          <h3 class="section-title">检索结果</h3>
          <span class="results-count">共 {{ displayResults.length }} 条</span>
        </div>
        <div class="results-content">
          <el-table
            v-loading="resultsLoading"
            :data="displayResults"
            stripe
            class="results-table"
            empty-text="暂无检索结果"
          >
            <el-table-column prop="equipment" label="设备" min-width="120" />
            <el-table-column prop="process" label="工序" min-width="140" />
            <el-table-column prop="measure_value" label="计量值" min-width="100" />
            <el-table-column prop="man_hours" label="需要的人工时" min-width="120" />
            <el-table-column prop="labor_cost" label="工人费用" min-width="120" />
            <el-table-column prop="equipment_cost" label="机具费用" min-width="120" />
          </el-table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

const apiBase = 'http://localhost:5000'

async function apiRequest(path, options = {}) {
  const url = `${apiBase}${path}`
  const defaultHeaders = { 'Content-Type': 'application/json' }
  const config = {
    ...options,
    headers: { ...defaultHeaders, ...(options.headers || {}) }
  }
  if (config.body && typeof config.body === 'object') {
    config.body = JSON.stringify(config.body)
  }
  const response = await fetch(url, config)
  if (!response.ok) throw new Error(`请求失败 ${response.status}`)
  return response.json()
}

// 表单数据
const form = ref({
  category: '',
  device: '',
  process: '',
  measureValue: ''
})

// 上次搜索条件（用于前端二次过滤）
const lastSearchForm = ref({
  category: '',
  device: '',
  process: '',
  measureValue: ''
})

// 缓存键
const SEARCH_RESULTS_KEY = 'search-area-results'
const SEARCH_HAS_SEARCHED_KEY = 'search-area-has-searched'
const SEARCH_LAST_FORM_KEY = 'search-area-last-form'

const safeSetStorage = (key, value) => {
  try { localStorage.setItem(key, value) } catch (e) { console.warn(e) }
}
const safeGetStorage = (key) => {
  try { return localStorage.getItem(key) } catch (e) { return null }
}
const safeParseJSON = (value, fallback) => {
  if (!value) return fallback
  try { return JSON.parse(value) } catch (e) { return fallback }
}

// 选项数据
const categoryOptions = ref([])
const deviceOptions = ref([])
const deviceLoading = ref(false)
const processOptions = ref([])

// 检索结果
const allResults = ref([])
const resultsLoading = ref(false)
const hasSearched = ref(false)

// 是否有筛选条件
const hasFilters = computed(() => {
  const v = lastSearchForm.value
  const filled = (input) => input !== null && input !== undefined && String(input).trim() !== ''
  return filled(v.category) || filled(v.device) || filled(v.process) || filled(v.measureValue)
})

// 前端二次过滤
const filteredResults = computed(() => {
  const value = lastSearchForm.value
  const device = (value.device || '').trim()
  const process = (value.process || '').trim()

  return allResults.value.filter(item => {
    if (device && !String(item.equipment || '').includes(device)) return false
    if (process && !String(item.process || '').includes(process)) return false
    return true
  })
})

// 最终展示结果
const displayResults = computed(() => {
  if (!hasSearched.value) return []
  return hasFilters.value ? filteredResults.value : allResults.value
})

// ---------- 加载选项 ----------
async function loadCategories() {
  try {
    const res = await apiRequest('/api/equipment-categories')
    categoryOptions.value = res.success ? (res.data || []) : []
  } catch (e) {
    categoryOptions.value = []
    ElMessage.error('加载设备类型失败')
  }
}

async function loadDevices(categoryId = '') {
  deviceLoading.value = true
  try {
    let url = '/api/equipment-types'
    if (categoryId) url += `?category=${encodeURIComponent(categoryId)}`
    const res = await apiRequest(url)
    if (res.success) {
      deviceOptions.value = (res.data || []).map(item => ({ name: item.name }))
    } else {
      deviceOptions.value = []
    }
  } catch (e) {
    deviceOptions.value = []
    ElMessage.error('加载设备列表失败')
  } finally {
    deviceLoading.value = false
  }
}

async function onCategoryChange(categoryId) {
  form.value.device = ''
  categoryId ? await loadDevices(categoryId) : await loadDevices()
}

async function loadProcessOptions() {
  try {
    const res = await apiRequest('/api/all-process-templates')
    if (res?.success) {
      const set = new Set()
      const equipmentProcesses = res.equipment_processes || {}
      Object.values(equipmentProcesses).forEach(group => {
        (group?.processes || []).forEach(proc => {
          if (proc?.description) set.add(proc.description)
        })
      })
      processOptions.value = Array.from(set)
    } else {
      processOptions.value = []
    }
  } catch (e) {
    processOptions.value = []
    ElMessage.error('加载工序选项失败')
  }
}

// ---------- 检索 ----------
async function fetchResultsByForm() {
  resultsLoading.value = true
  try {
    const payload = {
      category: form.value.category || '',
      device: form.value.device || '',
      process: form.value.process || '',
      measureValue: form.value.measureValue || ''
    }
    const response = await apiRequest('/api/search-processes', {
      method: 'POST',
      body: payload
    })
    if (response?.success) {
      allResults.value = response.data || []
      safeSetStorage(SEARCH_RESULTS_KEY, JSON.stringify(allResults.value))
    } else {
      allResults.value = []
      ElMessage.error(response?.message || '检索数据加载失败')
    }
  } catch (e) {
    allResults.value = []
    ElMessage.error('检索数据加载失败')
  } finally {
    resultsLoading.value = false
  }
}

function reset() {
  form.value = {
    category: '',
    device: '',
    process: '',
    measureValue: ''
  }
  hasSearched.value = false
  loadDevices() // 重置时重新加载全部设备
}

async function search() {
  try {
    hasSearched.value = true
    safeSetStorage(SEARCH_HAS_SEARCHED_KEY, '1')
    lastSearchForm.value = { ...form.value }
    safeSetStorage(SEARCH_LAST_FORM_KEY, JSON.stringify(lastSearchForm.value))
    await fetchResultsByForm()
  } catch (e) {
    ElMessage.error('检索失败')
  }
}

// ---------- 初始化 ----------
onMounted(() => {
  loadCategories()
  loadDevices()
  loadProcessOptions()

  // 恢复缓存结果
  const cachedResults = safeParseJSON(safeGetStorage(SEARCH_RESULTS_KEY), null)
  if (cachedResults) {
    allResults.value = cachedResults
    if (safeGetStorage(SEARCH_HAS_SEARCHED_KEY) === '1') {
      hasSearched.value = true
    }
  }

  // 恢复上次搜索条件
  const cachedLastForm = safeParseJSON(safeGetStorage(SEARCH_LAST_FORM_KEY), null)
  if (cachedLastForm) {
    lastSearchForm.value = cachedLastForm
  }
})
</script>

<style scoped>
.search-container {
  height: calc(100vh - 64px);
  min-height: 600px;
  padding: 24px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

.left-panel {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
  flex: 1 1 0;
  min-height: 0;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
  color: #1e293b;
}

.search-area {
  background: #fff;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04);
  flex: 0 0 auto;
}

.results-area {
  background: #fff;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04);
  display: flex;
  flex-direction: column;
  flex: 1 1 0;
  min-height: 0;
}

.results-content {
  overflow: auto;
  flex: 1 1 0;
}

.results-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.results-count {
  font-size: 13px;
  color: #64748b;
}

.results-table {
  width: 100%;
}

/* 表单样式 */
.search-area :deep(.el-form-item__label) {
  font-size: 14px !important;
  text-align: left !important;
  font-weight: 500;
  color: #475569;
}

.search-area :deep(.el-input__inner) {
  font-size: 14px !important;
}

.search-area :deep(.el-input__wrapper),
.search-area :deep(.el-select .el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
}

.search-area :deep(.el-select) {
  width: 100%;
}

.button-group {
  display: flex;
  gap: 20px;
  margin-top: 10px;
}

.reset-btn {
  flex: 1;
  font-size: 14px;
}

.search-btn {
  flex: 1;
  font-size: 14px;
}
</style>